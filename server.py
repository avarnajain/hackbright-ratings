"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, 
                    flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie

from sqlalchemy import asc


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template('homepage.html')

@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by('title').all()
    return render_template("movie_list.html", movies=movies)

@app.route('/new-user')
def new_user():
    """Add new user info"""

    return render_template('registration_form.html')

@app.route('/check-user', methods=['POST'])
def check_user():
    """check if user exists or add new user"""

    new_email = request.form.get('email')
    new_password = request.form.get('password')
    check_password = request.form.get('password2')


    email_list = []

    for user in User.query.all():
        email_list.append(user.email)

    if new_email in email_list:
        #check if given password matches db password
        #if yes, redirect to /logged-in
        db_user = User.query.filter(User.email==new_email).first()
        if (db_user.password == new_password):
            session['user_id'] = db_user.user_id
            flash('Succesfully loggged in!')
            return_url = '/users/{}'.format(session['user_id'])
            return redirect(return_url)
        #if not
        else: #option to reset password
            return render_template('user_error.html')
    else:
        if (new_password != check_password):
            return render_template('registration_form.html')
        #add user to db
        session['new_email'] = new_email
        session['new_password'] = new_password

       
        return render_template('new_user_info.html', user=user)

@app.route('/new-user-info', methods=['POST'])
def new_user_info():
    """Add extra info for new user"""
    age = request.form.get('age')
    zipcode = request.form.get('zipcode')
    
    user = User(email=session['new_email'], 
                password=session['new_password'],
                age=age, zipcode=zipcode)
    
    db.session.add(user)
    db.session.commit()

    session['email'] = user.email
    session['user_id'] = user.user_id
    return redirect('/logged-in')

@app.route('/login')
def user_login():
    """user login page"""
    return render_template('login_form.html')

@app.route('/logged-in')
def logged_in():
    """Successfully Logged in page"""
    user = User.query.filter(User.user_id==session['user_id']).first()
    user_email = user.email

    return render_template('logged_in.html')

@app.route('/logout')
def logout_user():
    """Log out route to clear entire session"""
    session.clear()
    flash("Successfully logged out")
    return redirect('/')


@app.route('/users/<user_id>')
def user_info(user_id):
    """Info for specific users"""
    user = User.query.get(user_id)
    list_of_Rating = Rating.query.filter(Rating.user_id==user_id).all()
    movies =[]

    for rating in list_of_Rating:
        movie = Movie.query.get(rating.movie_id).title
        score = rating.score
        movie_rating = (movie, score)
        movies.append(movie_rating)

    return render_template('user_info.html',
                                user=user,
                                movies=movies)

@app.route('/movies/<movie_id>')
def movie_info(movie_id):
    """Info for specific movie"""
    movie = Movie.query.get(movie_id)
    list_of_Rating = Rating.query.filter(Rating.movie_id==movie_id).all()
    user_ratings = []

    for rating in list_of_Rating:
        user = User.query.get(rating.user_id).email
        score = rating.score
        user_rating = (user, score)
        user_ratings.append(user_rating)

    return render_template('movie_info.html',
                                movie=movie,
                                user_ratings=user_ratings)

@app.route('/rate-movie/<movie_id>', methods=['POST'])
def rate_movie(movie_id):
    """Pos method for adding user rating"""
    score = request.form.get('rating')

    rating = Rating(movie_id=movie_id, 
                user_id=session['user_id'],
                score=score)
    
    db.session.add(rating)
    db.session.commit()
   
    redirect_url = '/movies/{}'.format(movie_id)
    return redirect(redirect_url)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
