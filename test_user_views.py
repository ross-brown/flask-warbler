"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, Message, User, Like

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewBaseCase(TestCase):
    """Base case for user views"""

    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


class UserAuthenticationTestCase(UserViewBaseCase):
    """Tests for signup, login, logout."""

    def test_signup(self):
        """Testing successful signup route for new user."""
        with self.client as c:
            #Testing Get for Signup Route
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today', html)


            test_data = {
                            'username': "signed_up_user",
                            'password': 'password',
                            'email': 'signup@gmail.com',
                            'image_url': None
                          }

            #Testing Post Route
            resp = c.post('/signup',
                          data=test_data,
                          follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('id="home-aside"', html)
            self.assertIn('@signed_up_user', html)


    def test_invalid_signup(self):
        """Testing unsuccesful route when trying to create an invalid user"""

        with self.client as c:
            resp = c.post('/signup',
                        data={
                        'username': "u1",
                        'password': 'password',
                        'email': 'u1@email.com',
                        'image_url': None
                        },
                        follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken', html)

