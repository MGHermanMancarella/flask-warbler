"""Message model tests."""
import os

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

# run these tests like:
#
#    python -m unittest test_message_model.py

from models import User, Message, Follow, Like
from unittest import TestCase
from app import app, db





# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

FLASK_DEBUG = False
# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

        msg1 = Message(text="test", user_id=self.u1_id)
        db.session.add(msg1)
        db.session.commit()

        self.msg1_id = msg1.id

    def tearDown(self):
        db.session.rollback()

    def test_valid_messages_model(self):
        """Check that messages were create for user 1"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        # User1 should have 1 message, user2 none.
        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(len(u2.messages), 0)

    def test_valid_datatypes(self):
        """check that message data types are correct"""

        msg = Message.query.get(self.msg1_id)

        self.assertIsInstance(msg.id, int)
        self.assertIsInstance(msg.user_id, int)
        self.assertEqual(len(msg.likes), 0)

    def test_valid_user_relationship(self):
        """check that message has a valid user owner"""

        u1 = User.query.get(self.u1_id)
        msg = Message.query.get(self.msg1_id)

        self.assertEqual(msg.user, u1)

    def test_valid_likes_relationship(self):
        """check that message has a valid user owner"""

        u2 = User.query.get(self.u2_id)
        msg = Message.query.get(self.msg1_id)
        new_like = Like(liked_by_user_id=u2.id,
                            message_liked_id=msg.id)
        db.session.add(new_like)
        db.session.commit()

        self.assertIsInstance(msg.likes, list)
        self.assertEqual(len(msg.likes), 1)

    def test_valid_liked_by_user_relationship(self):
        """check that message has a valid user owner"""

        u2 = User.query.get(self.u2_id)
        msg = Message.query.get(self.msg1_id)
        new_like = Like(liked_by_user_id=u2.id,
                            message_liked_id=msg.id)
        db.session.add(new_like)
        db.session.commit()

        self.assertIsInstance(msg.liked_by_users, list)
        self.assertEqual(msg.liked_by_users[0], u2)
        self.assertEqual(len(msg.likes), 1)


