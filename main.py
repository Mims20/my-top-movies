import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my-top-movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

TMDB_API = "https://api.themoviedb.org/3/search/movie?"
TMDB_MOVIE_DETAILS = "https://api.themoviedb.org/3/movie/"
API_KEY = os.environ["API_KEY"]


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)


# Create database and add a record
db.create_all()

# new_movie = Movie( title="Phone Booth", year=2002, description="Publicist Stuart Shepard finds himself trapped in a
# phone booth, pinned down by an extortionist's " "sniper rifle. Unable to leave or receive outside help,
# Stuart's negotiation with the caller leads to " "a jaw-dropping climax.", rating=7.3, ranking=10, review="My
# favourite character was the caller.", img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg" )
#
# db.session.add(new_movie)
# db.session.commit()

class RateMovieForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g 8.9", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    # retrieve all movies from database sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # Update ranking for each movie
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


# Update a movie's rating and review
@app.route("/edit", methods=["GET", "POST"])
def edit():
    # create instance of movie form class and use it to generate bootstrap quick form
    form = RateMovieForm()

    movie_id = request.args.get('id')
    movie_to_update = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie_to_update.rating = request.form["rating"]
        movie_to_update.review = request.form["review"]

        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit.html", movie=movie_to_update, form=form)


# Delete a movie record
@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(movie_id)

    db.session.delete(movie_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    # an instance of addmovieform to be used for wtf quick form
    form = AddMovieForm()

    # Grab movie title on submit, use it to search tmdb and return results
    if form.validate_on_submit():
        params = {
            "api_key": API_KEY,
            "query": request.form["title"],
        }

        response = requests.get(TMDB_API, params=params)
        data = response.json()["results"]

        return render_template('select.html', movies=data)

    return render_template("add.html", form=form)


# Search details of movie using its id from initial results.
# Add selected movie to database, then redirect to edit page to provide rating and review
@app.route("/select")
def select_movie():
    selected_movie_id = request.args.get("movie_id")

    response = requests.get(f"{TMDB_MOVIE_DETAILS}{selected_movie_id}?api_key={API_KEY}")
    movie_details = response.json()

    new_movie = Movie(title=movie_details["title"],
                      year=datetime.strptime(movie_details["release_date"], "%Y-%m-%d").year,
                      description=movie_details["overview"],
                      img_url=f"http://image.tmdb.org/t/p/w500{movie_details['poster_path']}")

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
