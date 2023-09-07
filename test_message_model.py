"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        m1 = Message(text='test_text1')
        u1.messages.append(m1)

        m2 = Message(text='test_text2')
        u2.messages.append(m2)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id
        self.m2_id = m2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


    def test_message_user_relationship(self):
        """Test relationship between user and message tables."""
        m1 = Message.query.get(self.m1_id)
        u1 = User.query.get(self.u1_id)

        #Confirm that message is properly related to user
        self.assertIn(m1, u1.messages)
        self.assertEqual(m1.user_id, u1.id)

        m2 = Message.query.get(self.m2_id)

        #Confirm that users do not have a relation to a message that is not theirs
        self.assertNotIn(m2, u1.messages)
        self.assertNotEqual(m2.user_id, u1.id)


    def test_(self):
        """Test relationship between messages/users and likes."""

        m1 = Message.query.get(self.m1_id)
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u1.liked_messages.add(m1)

        self.assertIn(m1, u1.liked_messages)
        self.assertNotIn(m1, u2.liked_messages)

        self.assertIn(u1, m1.users_who_liked)
        self.assertNotIn(u2, m1.users_who_liked)
