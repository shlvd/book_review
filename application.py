import os

from flask import Flask, render_template, url_for, request, session, logging, redirect, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from flask_login import login_required, current_user, logout_user
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

from models import *


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/profile")
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('profile'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password").encode('utf-8')
        result = db.execute("SELECT * FROM users WHERE email = :e", {"e": email}).fetchone()

        if result is not None:
            if check_password_hash(result.password, password):
                session['user'] = email
                session['logged_in'] = True
                return redirect(url_for('profile'))

        flash('Please check your login details and try again.')
    return render_template('login.html')

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if 'user' in session:
        return redirect(url_for('profile'))

    if request.method == "POST":
        try:
            email = request.form.get("email")
            name = request.form.get("name")
            password = request.form.get("password")

            result = db.execute("INSERT INTO Users (email, password, name) VALUES (:e, :p, :n)", {"e": email, "p": generate_password_hash(password, method='sha256'), "n":name})
            db.commit()

            if result.rowcount > 0:
                session['user'] = email
                session['logged_in'] = True
                return redirect(url_for('profile'))

        except exc.IntegrityError:
            message = "Username already exists."
            db.execute("ROLLBACK")
            db.commit()
            flash('Email address already exists! Please use another e-mail.')
            return render_template("signup.html")

    return render_template("signup.html")


@app.route('/logout')
#@login_required
def logout():
    #logout_user()
    if 'user' in session:
        session.pop('user', None)
        session['logged_in'] = False
        flash('You logged out')
    return redirect(url_for('login'))

@app.route('/profile/search', methods=["GET", "POST"])
def search():
    if 'user' not in session:
        return redirect(url_for('login'))
    query = request.form.get("searchbox")
    query = '%' + query.lower() + '%'
    results = db.execute("SELECT * FROM books WHERE lower(title) LIKE :q OR isbn LIKE :q OR lower(author) LIKE :q", {"q": query}).fetchall()
    if results == []:
        flash('Can"t find anything that match your query. Please, back to search and try again.')
    return render_template("search.html", results=results)

@app.route("/books_info/<string:isbn>", methods=["GET", "POST"])
def books_info(isbn):
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        comment = request.form.get("comment")
        my_rating = request.form.get("rating", None)
        username = db.execute("SELECT * FROM users WHERE email = :q", {"q": session['user']}).fetchone()
        book = db.execute("INSERT INTO reviews (name, isbn, comment, rating) VALUES (:a, :b, :c, :r)", {"a": username.name, "b": isbn, "c": comment, "r": my_rating})
        db.commit()

    book = db.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()
    reviews = db.execute("SELECT DATE_TRUNC('second', date::timestamp) as date, name, comment, rating  FROM reviews WHERE isbn = :q1", {"q1": isbn}).fetchall()

    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "YOUR_KEY", "isbns": isbn})
    data = response.json()
    gr_rating = (data['books'][0]['average_rating'])
    rev_count = (data['books'][0]['reviews_count'])

    return render_template("books_info.html", book_info=book, reviews=reviews, rating=gr_rating, count=rev_count)

@app.route("/api/<string:isbn>")
def api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :q", {"q": isbn}).fetchone()

    if book is None:
        return jsonify({"error": "Invalid ISBN"}), 404

    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :q1", {"q1": book.isbn}).fetchall()
    response = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "YOUR_KEY", "isbns": isbn})
    data = response.json()['books'][0]

    return jsonify({
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "review_count": data['reviews_count'],
        "average_rating": data['average_rating']
    })
