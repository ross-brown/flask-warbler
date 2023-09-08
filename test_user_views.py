"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, Message, User

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
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)
        db.session.flush()

        u1.following.append(u2)
        u2.following.append(u1)

        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


class UserAuthenticationTestCase(UserViewBaseCase):
    """Tests for signup, login, logout."""

    def test_signup(self):
        """Testing successful signup route for new user."""
        with self.client as c:
            #TODO: have one just for getting sign up page
            # Testing Get for Signup Route
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today', html)

            # Testing Post Route
            resp = c.post('/signup',
                          data={
                            'username': "signed_up_user",
                            'password': 'password',
                            'email': 'signup@gmail.com',
                            'image_url': None
            },
                          follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('id="home-aside"', html)
            self.assertIn('@signed_up_user', html)

    def test_invalid_signup(self):
        """Testing unsuccessful route when trying to create an invalid user"""

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

    def test_login(self):
        """Testing successful login routes."""

        with self.client as c:
            # Testing Get for Login Route
            #TODO: split get into separate test
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome back.', html)

            # Testing Post Route
            resp = c.post('/login',
                          data={"username": "u1",
                                "password": "password"},
                          follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Hello, u1!', html)
            self.assertIn('id="home-aside"', html)

    def test_invalid_login(self):
        """Testing unsuccesful route when trying to login."""

        with self.client as c:
            resp = c.post('/login',
                          data={
                              'username': "u321",
                              'password': 'password'
                          },
                          follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Invalid credentials.', html)

    def test_logout(self):
        """Testing successful route when logging out."""
        with self.client as c:
            # Need to login first to be able to logout
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/logout', follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Logged out successfully', html)

    def test_invalid_logout(self):
        """Testing unsuccessful route when trying to logout."""
        with self.client as c:

            resp = c.post('/logout', follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


class UserPagesTestCase(UserViewBaseCase):
    """Testing for viewing different pages for a user."""

    def test_homepage(self):
        """Test route to view the homepage."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/")

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', html)
            self.assertIn('id="home-aside"', html)

    def test_invalid_homepage(self):
        """Test route to homepage without being logged in."""
        with self.client as c:

            resp = c.get("/")

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('New to Warbler?', html)

    def test_user_list(self):
        """Test route to get list of users."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('class="card-bio"', html)

    def test_invalid_user_list(self):
        """Test route to get list of users without being logged in."""
        with self.client as c:

            resp = c.get("/users", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_search_list(self):
        """Test route whenever using search bar."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users?q=u2", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('class="card-bio"', html)
            self.assertIn('@u2', html)

    def test_user_search_list_none(self):
        """Test route whenever using search bar with no users found."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users?q=hfjdksahjfk", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sorry, no users found', html)

    def test_user_profile(self):
        """Test route to view a user's profile."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', html)
            self.assertIn('id="warbler-hero"', html)

    def test_invalid_user_profile(self):
        """Test route to get list of users without being logged in."""
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_following(self):
        """Test route to view a user's following list."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/following",
                         follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', html)
            self.assertIn('@u2', html)

    def test_invalid_user_following(self):
        """Test route to get list of following without being logged in."""
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}/following",
                         follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_followers(self):
        """Test route to view a user's followers list."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/followers",
                         follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u1', html)
            self.assertIn('@u2', html)

    def test_invalid_user_followers(self):
        """Test route to get list of followers without being logged in."""
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}/followers",
                         follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_likes(self):
        """Test route to view a user's likes."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Creating a liked message to check for
            m1 = Message(text="test-message", user_id=self.u2_id)
            db.session.commit()
            u1 = User.query.get(self.u1_id)
            u1.liked_messages.add(m1)

            resp = c.get(f"/users/{self.u1_id}/likes")

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('test-message', html)
            self.assertIn('@u2', html)

    def test_invalid_user_likes(self):
        """Test route to get list of liked messages without being logged in."""
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}/likes", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


class UserFunctionalityTestCase(UserViewBaseCase):
    """Testing functionality that a user can do."""

    def test_user_follow(self):
        """Test route to follow a user."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/follow/{self.u3_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('@u3', html)
            self.assertIn('@u2', html)

    def test_invalid_user_follow(self):
        """Test route to follow someone without being logged in."""
        with self.client as c:

            resp = c.post(f"/users/follow/{self.u3_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_unfollow(self):
        """Test route to unfollow a user."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/users/stop-following/{self.u2_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@u2', html)

    def test_invalid_user_unfollow(self):
        """Test route to unfollow someone without being logged in."""
        with self.client as c:

            resp = c.post(f"/users/stop-following/{self.u3_id}", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_edit_page(self):
        """Test route to view edit page."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/profile")

            #TODO: could check that initial profile data is there.
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Your Profile.', html)
            self.assertIn('Edit this user!', html)

    def test_invalid_user_edit_page(self):
        """Test route to edit profile without being logged in."""
        with self.client as c:

            resp = c.post(f"/users/profile", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_edit(self):
        """Test route to edit a user."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/profile", data={"username": "new-name",
                                                   "email": "new@gmail.com",
                                                   "image_url": None,
                                                   "header_image_url": None,
                                                   "bio": None,
                                                   "password": "password"
                                                   },
                          follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('new-name', html)
            self.assertIn('id="warbler-hero"', html)

    def test_invalid_user_edit(self):
        """Test route to edit profile without being logged in."""
        with self.client as c:

            resp = c.post(f"/users/profile", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_edit_invalid_password(self):
        """Test route to edit a user with incorrect password."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/profile", data={"username": "new-name",
                                                   "email": "new@gmail.com",
                                                   "image_url": None,
                                                   "header_image_url": None,
                                                   "bio": None,
                                                   "password": "fdsafgfdsgf"
                                                   })

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('new-name', html)
            self.assertIn('Password incorrect', html)

    def test_user_delete(self):
        """Test route to delete a user."""
        with self.client as c:
            # Logging in first
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Account deleted successfully', html)
            self.assertIn('Join Warbler today.', html)

    def test_invalid_user_delete(self):
        """Test route to delete user without being logged in."""
        with self.client as c:

            resp = c.post(f"/users/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)
