from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)

class Books(db.Model):
    __tablename__ = "books"
    #id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class Reviews(db.Model):
    __tablename__ = "reviews"
    #id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.Integer, primary_key=True, nullable=False)
    review = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
