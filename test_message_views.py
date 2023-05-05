"""Message View tests."""
from models import Message, User
from unittest import TestCase
from app import app, CURR_USER_KEY, db
import os

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database


# Now we can import app


app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
FLASK_DEBUG = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.m1_id = m1.id

        self.client = app.test_client()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_valid_add_message(self):
        """Test successfully add messages"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "message_test"},
                          follow_redirects=True)
            html = resp.get_data(as_text=True)

            m2 = Message.query.filter_by(text="message_test").one()

            self.assertEqual(resp.status_code, 200)
            self.assertIn("message_test", html)
            self.assertIn("<!-- User's Profile Page -->", html)
            self.assertIsInstance(m2, Message)

    def test_invalid_add_message(self):
        """Test unable to submit a message without text"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": ""})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!-- Message Create Page -->", html)

    def test_valid_show_message(self):
        """Test successfully showing messages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("m1-text", html)
            self.assertIn("<!-- Show Message Page -->", html)

    def test_invalid_show_message(self):
        """Test failing to show a message that doesn't exist"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/100")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 404)
            self.assertIn("requested URL was not found", html)

    def test_valid_delete_message(self):
        """Test successfully deleting messages"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("m1-text", html)
            self.assertIn("<!-- User's Profile Page -->", html)

    def test_invalid_delete_message(self):
        """Test invalid user deleting someone else's message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            m1 = Message.query.get(self.m1_id)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            self.assertIn("<!-- Homepage for logged in -->", html)
            self.assertEqual(m1.text, "m1-text")

    def test_like_message(self):
        """Test for functional and successful like button """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f"/{self.m1_id}/like",
                          headers={"Referer": f"/messages/{self.m1_id}"}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("-fill", html)
