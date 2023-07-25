import os
import functools
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, UserEditForm, LoginForm, MessageForm, CSRFProtectForm
from models import db, connect_db, User, Message, Like

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# toolbar = DebugToolbarExtension(app)

connect_db(app)


# bug prevents functional login. This circumvents that issue but disables the
# CSRF auth. 
app.config['WTF_CSRF_ENABLED'] = False

### login decorator ###


def authenticate_login(f):
    """Decorator to check login before every view function"""

    @functools.wraps(f)
    def login_wrapper(*args, **kwargs):
        """ wrapper for login decorator"""

        if not g.user:
            flash("Access unauthorized.", "danger")
            return redirect("/")
        return f(*args, **kwargs)

    return login_wrapper

##############################################################################
# User signup/login/logout


@app.before_request
def apply_csrf_protect():
    """add a CSRF token before requests"""

    g.csrf_form = CSRFProtectForm()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Log out user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    do_logout()

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login and redirect to homepage on success."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data,
        )

        if user:

            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.post('/logout')
@authenticate_login
def logout():
    """Handle logout of user and redirect to homepage."""

    form = g.csrf_form

    if not form.validate_on_submit() or not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


##############################################################################
# General user routes:

@app.get('/users')
@authenticate_login
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """
    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.get('/users/<int:user_id>')
@authenticate_login
def show_user(user_id):
    """Show user profile."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user)


@app.get('/users/<int:user_id>/following')
@authenticate_login
def show_following(user_id):
    """Show list of people this user is following."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/following.html', user=user)


@app.get('/users/<int:user_id>/followers')
@authenticate_login
def show_followers(user_id):
    """Show list of followers of this user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/followers.html', user=user)


@app.post('/users/follow/<int:follow_id>')
@authenticate_login
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """
    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    if g.csrf_form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.append(followed_user)
        db.session.commit()
        return redirect(request.referrer)

    else:
        flash("Error processing request")
        return redirect("/")


@app.post('/users/stop-following/<int:follow_id>')
@authenticate_login
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """
    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    if g.csrf_form.validate_on_submit():
        followed_user = User.query.get_or_404(follow_id)
        g.user.following.remove(followed_user)
        db.session.commit()
        return redirect(request.referrer)

    else:
        flash("Error processing request")
        return redirect("/")


@app.route('/users/profile_edit', methods=["GET", "POST"])
def edit_profile():
    """Edit profile for current user."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():
        password = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(g.user.username, password)

        if user:
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            user.header_image_url = form.header_image_url.data
            user.bio = form.bio.data

            db.session.commit()

            flash(f"{user.username} updated")
            return redirect(f"/users/{user.id}")
        else:
            form.username.errors = ["Invalid password"]
    return render_template("users/edit.html", form=form)


@app.post('/users/delete')
@authenticate_login
def delete_user():
    """Delete user.

    Redirect to signup page.
    """

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    do_logout()

    if g.csrf_form.validate_on_submit():

        db.session.delete(g.user)
        db.session.commit()
        return redirect("/signup")

    else:
        flash("Error processing request")
        return redirect("/")

##############################################################################
# Messages routes:


@app.route('/messages/new', methods=["GET", "POST"])
@authenticate_login
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
@authenticate_login
def show_message(message_id):
    """Show a message."""

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    msg = Message.query.get_or_404(message_id)
    liked = Like.query.filter(Like.message_liked_id ==
                              message_id).one_or_none()

    return render_template('messages/show.html', message=msg, liked=liked)


@app.post('/messages/<int:message_id>/delete')
@authenticate_login
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    # if not g.user:
    #     flash("Access unauthorized.", "danger")
    #     return redirect("/")

    if g.csrf_form.validate_on_submit():
        msg = Message.query.get_or_404(message_id)

        if g.user.id != msg.user_id:
            flash("Access unauthorized.", "danger")
            return redirect("/")

        db.session.delete(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")

    else:
        flash("Error processing request")
        return redirect("/")


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        following_ids = [user.id for user in g.user.following] + [g.user.id]

        messages = (Message
                    .query
                    .filter((Message.user_id.in_(following_ids)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response


###############################################################
# Likes

@app.post('/<int:msg_id>/like')
@authenticate_login
def like_or_unlike(msg_id):
    """ Likes or unlikes messages"""

    like_message = Like.query.get((g.user.id, msg_id))
    msg = Message.query.get_or_404(msg_id)

    if msg.user_id == g.user.id:  # TODO: perform this logic in templates
        # TODO: maybe use request.url in template
        return redirect(request.referrer)

    if g.csrf_form.validate_on_submit():
        if like_message:
            db.session.delete(like_message)
            db.session.commit()

        else:
            new_like = Like(liked_by_user_id=g.user.id,
                            message_liked_id=msg_id)
            db.session.add(new_like)
            db.session.commit()

    return redirect(request.referrer)


@app.get('/users/<int:user_id>/liked-messages')
@authenticate_login
def show_liked_messages(user_id):
    """ Shows all messages liked by current user"""

    user = User.query.get_or_404(user_id)
    messages = user.liked_messages

    return render_template("/users/liked-messages.html", messages=messages, user=user)

# TODO: Fix the like aref buttons on the home and details page
# TODO: MAYBE: add a counter to each message to show how many likes it has ¯\_(ツ)_/¯
# TODO: Header photo looks like poopy
# QUESTION: How do we look at warbles from people we don't follow?
