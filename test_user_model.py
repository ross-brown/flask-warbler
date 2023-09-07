"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User

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


class UserModelTestCase(TestCase):
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
        u1 = User.query.get(self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_user_follow(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))

        u1.following.append(u2)
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

    def test_user_signup(self):
        test_user = User.signup("u3", "u3@gmail.com", "password", None)
        db.session.commit()

        self.assertEqual(test_user, User.query.get(test_user.id))

        User.signup("u1", "u3@gmail.com", "password", None)

        with self.assertRaises(IntegrityError):
            User.signup("u3", "u3@gmail.com", "password", None)
            db.session.commit()


    def test_user_authenticate(self):
        """Test that authenticate method works as expected."""

        # Authenticate returns user when correct credentials input.
        user = User.authenticate("u1", "password")
        self.assertEqual(user, User.query.get(user.id))

        #Returns False when incorrect username or password
        self.assertFalse(User.authenticate('tuckerdiane', 'ewrghetheat'))
        self.assertFalse(User.authenticate('rwthejnmhraet', 'password'))
