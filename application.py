import os

from flask import Flask, render_template, url_for, request, session, logging, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from flask_login import login_required, current_user, logout_user
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

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

@app.route("/hello")
def hello():
    result = db.execute("SELECT * FROM users WHERE email = :e", {"e": session['user']}).fetchone()
    return render_template('hello.html', name=result.name)


@app.route('/login', methods=["GET", "POST"])
def login():
    if 'user' in session:
        return redirect(url_for('hello'))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password").encode('utf-8')
        result = db.execute("SELECT * FROM users WHERE email = :e", {"e": email}).fetchone()

        if result is not None:
            if check_password_hash(result.password, password):
                session['user'] = email
                session['logged_in'] = True
                return redirect(url_for('hello'))

        flash('Please check your login details and try again.')
    return render_template('login.html')

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if 'user' in session:
        return redirect(url_for('hello'))

    message = None

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
                return redirect(url_for('hello'))

        except exc.IntegrityError:
            message = "Username already exists."
            db.execute("ROLLBACK")
            db.commit()
            flash('Email address already exists! Please use another e-mail.')
            return render_template("signup.html")

    return render_template("signup.html", message=message)


@app.route('/logout')
#@login_required
def logout():
    #logout_user()
    if 'user' in session:
        session.pop('user', None)
        session['logged_in'] = False
        flash('You logged out')
    return redirect(url_for('login'))
