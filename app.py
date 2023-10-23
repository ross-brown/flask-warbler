import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, flash, redirect, session, g
from werkzeug.exceptions import Unauthorized
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, CSRFForm, UserEditForm
from models import db, connect_db, User, Message, Like

load_dotenv()

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


@app.before_request
def add_csrf_form():
    """Instantiate CSRF for logout function before each request."""

    g.csrf_form = CSRFForm()


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

#TODO: if you GET to this route while logged in, IT WORKS, IT SHOULDN'T
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
def logout():
    """Handle logout of user and redirect to homepage."""

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()
    flash('Logged out successfully!', 'success')

    return redirect('/login')


##############################################################################
# General user routes:

@app.get('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users, form=g.csrf_form)


@app.get('/users/<int:user_id>')
def show_user(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    return render_template('users/show.html', user=user, form=g.csrf_form)


@app.get('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user, form=g.csrf_form)


@app.get('/users/<int:user_id>/followers')
def show_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user, form=g.csrf_form)


@app.post('/users/follow/<int:follow_id>')
def start_following(follow_id):
    """Add a follow for the currently-logged-in user.

    Redirect to following page for the current for the current user.
    """

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.user.id == follow_id:
        flash("You can't follow yourself!", 'danger')
        return redirect('/users')

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.post('/users/stop-following/<int:follow_id>')
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user.

    Redirect to following page for the current for the current user.
    """

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.get('/users/<int:user_id>/likes')
def show_likes(user_id):
    """Show list of likes of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/likes.html', user=user, form=g.csrf_form)


@app.post('/users/like/<int:message_id>')
def like_message(message_id):
    """Like a specific message and redirect."""

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    if message.user_id != g.user.id:
        g.user.liked_messages.add(message)
        db.session.commit()
    else:
        flash('You cannot like your own Warble!', 'danger')

    return redirect(request.args['next'])


@app.post("/users/unlike/<int:message_id>")
def unlike_message(message_id):
    """Unlike a specific message and redirect."""

    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    message = Message.query.get_or_404(message_id)

    g.user.liked_messages.remove(message)
    db.session.commit()

    return redirect(request.args['next'])


@app.route('/users/profile', methods=["GET", "POST"])
def update_profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():

        form_fields = {"username": form.username.data,
                       "email": form.email.data,
                       "image_url": form.image_url.data,
                       "header_image_url": form.header_image_url.data,
                       "bio": form.bio.data}

        if User.authenticate(g.user.username, form.password.data):
            g.user.username = form_fields["username"]
            g.user.email = form_fields["email"]
            g.user.image_url = form_fields["image_url"]
            g.user.header_image_url = form_fields["header_image_url"]
            g.user.bio = form_fields["bio"]

            db.session.commit()

            flash('Profile updated successfully!', 'success')
            return redirect(F"/users/{g.user.id}")
        else:
            form = UserEditForm(obj=form_fields)

            flash('Password incorrect!', 'danger')
            return render_template('/users/edit.html', form=form, user=g.user)

    return render_template('/users/edit.html', form=form, user=g.user)


@app.post('/users/delete')
def delete_user():
    """Delete user.

    Redirect to signup page.
    """
    if not g.user or not g.csrf_form.validate_on_submit():
        flash("Access unauthorized.", "danger")
        return redirect("/")

    Message.query.filter_by(user_id=g.user.id).delete()
    db.session.delete(g.user)
    db.session.commit()

    do_logout()

    flash("Account deleted successfully!", "success")
    return redirect("/signup")


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def add_message():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/create.html', form=form)


@app.get('/messages/<int:message_id>')
def show_message(message_id):
    """Show a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg, form=g.csrf_form)


@app.post('/messages/<int:message_id>/delete')
def delete_message(message_id):
    """Delete a message.

    Check that this message was written by the current user.
    Redirect to user page on success.
    """

    if not g.user or not g.csrf_form.validate_on_submit() or \
         message_id not in [m.id for m in g.user.messages]:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.get('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of self & followed_users
    """

    if g.user:
        following_ids = [f.id for f in g.user.following] + [g.user.id]

        messages = (Message
                    .query
                    .filter((Message.user_id.in_(following_ids)))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages, form=g.csrf_form)

    return render_template('home-anon.html', form=g.csrf_form)



@app.errorhandler(404)
def page_not_found(error):
    """Display custom error page on 404 status codes."""

    return render_template("404.html", form=g.csrf_form), 404


@app.after_request
def add_header(response):
    """Add non-caching headers on every request."""

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control
    response.cache_control.no_store = True
    return response
