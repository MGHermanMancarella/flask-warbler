"""User model tests."""

import os

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# run these tests like:
#
#    python -m unittest test_user_model.py

from app import app, db
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import User, Message, Follow, DEFAULT_IMAGE_URL, DEFAULT_HEADER_IMAGE_URL

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
app.config['TESTING'] = True
FLASK_DEBUG = False
# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Test of User class and Follow class/ join table"""

    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Test to se if users have been properly instantiated"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)
        self.assertEqual(len(u2.messages), 0)
        self.assertEqual(len(u2.followers), 0)
        self.assertEqual(u1.image_url, DEFAULT_IMAGE_URL)
        self.assertEqual(u1.header_image_url, DEFAULT_HEADER_IMAGE_URL)

    def test_valid_follow(self):
        """ Test to see if u1 can follow u2
        and user instance methods is_followed_by & is_following """

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        new_follow = Follow(user_being_followed_id=self.u1_id,
                            user_following_id=self.u2_id)
        db.session.add(new_follow)
        db.session.commit()

        self.assertTrue(u1.is_followed_by(u2))
        self.assertTrue(u2.is_following(u1))


    def test_invalid_follow(self):
        """ Test to see if u1 is not following u2
        and user instance methods is_followed_by & is_following """

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        new_follow = Follow(user_being_followed_id=self.u1_id,
                            user_following_id=self.u2_id)
        db.session.add(new_follow)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))

        #test for repeated follow of same users
        with self.assertRaises(IntegrityError):
            repeat_follow = Follow(user_being_followed_id=self.u1_id,
                            user_following_id=self.u2_id)
            db.session.add(repeat_follow)
            db.session.commit()


    def test_valid_authenticate(self):
        """Testing class method authenticate() success"""

        self.assertIsInstance(User.authenticate(
            username="u1", password="password"), User)

    def test_invalid_authenticate(self):
        """Testing class method authenticate() failer"""

        # Wrong username
        self.assertFalse(User.authenticate(
            username="wrong", password="password"))

        # Wrong password
        self.assertFalse(User.authenticate(username="u1", password="wrong"))

    def test_valid_signup(self):
        """Check for successful new user signup"""

        good_test = User.signup(
            "good_test", "good_test@email.com", "password", None)

        # Test successful registration
        self.assertIsInstance(good_test, User)
        self.assertEqual(good_test.username,"good_test")
        self.assertEqual(good_test.email,"good_test@email.com")
        self.assertNotEqual(good_test.password,"password")


    def test_invalid_signup(self):
        """Check for failed new user signup"""

        # Same email fail register
        with self.assertRaises(IntegrityError):
            User.signup("bad_test", "u1@email.com", "password", None)
            db.session.commit()
        db.session.rollback()

        # Same username fail register
        with self.assertRaises(IntegrityError):
            User.signup("u1", "bad_test@email.com", "password", None)
            db.session.commit()

    def test_valid_messages_relationship(self):
        """Test for the messages relationship"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        message = Message(text="test", user_id=self.u1_id)
        db.session.add(message)
        db.session.commit()

        self.assertIsInstance(u1.messages, list)
        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(len(u2.messages), 0)

    def test_valid_followers_relationship(self):
        """Test for the followers relationship"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)
        new_follow = Follow(user_being_followed_id=self.u1_id,
                            user_following_id=self.u2_id)
        db.session.add(new_follow)
        db.session.commit()


        self.assertIsInstance(u1.followers, list)
        self.assertEqual(len(u1.followers), 1)
        self.assertEqual(u1.followers[0], u2)
        self.assertEqual(len(u2.followers), 0)
