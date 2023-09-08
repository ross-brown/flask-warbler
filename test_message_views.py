"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

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


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        m2 = Message(text="m2_text", user_id=u2.id)

        u1.following.append(u2)

        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id
        self.m1_text = m1.text
        self.m2_id = m2.id
        self.m2_text = m2.text

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()


class MessagePageTestCase(MessageBaseViewTestCase):
    def test_show_message(self):
        """Test that the message page loads"""

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/messages/{self.m1_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.m1_text, html)
            self.assertIn('class="message-area"', html)

    def test_invalid_show_message(self):
        """Test to ensure you cannot see a message when logged out."""

        with self.client as c:


            resp = c.get(f'/messages/{self.m1_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        """Test adding a message while logged in."""
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Testing a GET request to view the add message page
            #TODO: split GET into sep request
            resp = c.get("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("happening?", html)
            self.assertIn("Add my message!", html)

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()

            resp = c.post("/messages/new",
                          data={"text": "World"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertIn("World", html)
            self.assertIn("@u1", html)
            self.assertIn('id="warbler-hero"', html)

    def test_invalid_add_message(self):
        """Test adding a message while logged out."""
        with self.client as c:

            resp = c.post("/messages/new",
                          data={"text": "World"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_delete_message(self):
        """Test deleteing a message while logged in."""
        with self.client as c:

            # testing deleting while logged in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertNotIn(self.m1_text, html)
            self.assertIn("@u1", html)
            self.assertIn('id="warbler-hero"', html)

            # Confirm you cannot delete someone else's message
            #TODO: split into separate test as well
            resp = c.post(
                f"/messages/{self.m2_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized', html)

    def test_invalid_delete_message(self):
        """Test deleting a message while logged out."""
        with self.client as c:

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)



class MessageLikeTestCase(MessageBaseViewTestCase):
    def test_like_message(self):
        """Test liking a message while logged in."""
        with self.client as c:

            # testing liking own message while logged in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #Ensuring a user can't like their own warble.
            resp = c.post(f"/users/like/{self.m1_id}?next=/", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('You cannot like your own Warble!', html)

            # testing liking someone else's messsage while logged in
            resp = c.post(f"/users/like/{self.m2_id}?next=/", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('<i class="bi bi-heart-fill">', html)

    def test_invalid_like_message(self):
        """Test liking a message while logged out."""
        with self.client as c:

            resp = c.post(
                f"/users/like/{self.m1_id}?next=/", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)



    def test_unlike_message(self):
        """Test unliking a message while logged in."""
        with self.client as c:

            # testing unliking someone else's messsage while logged in
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            c.post(f"/users/like/{self.m2_id}?next=/", follow_redirects=True)

            resp = c.post(f"/users/unlike/{self.m2_id}?next=/", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('<i class="bi bi-heart">', html)

    def test_invalid_unlike_message(self):
        """Test unliking a message while logged out."""
        with self.client as c:

            resp = c.post(
                f"/users/unlike/{self.m1_id}?next=/", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)
