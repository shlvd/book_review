from flask import Flask, render_template, request
from models import *
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgres://vdztiunknbwcth:2bd54b025103d5f8683970cd5c73b3993d841c54ae3a92aa7c9ea143fa613a6c@ec2-46-137-177-160.eu-west-1.compute.amazonaws.com:5432/deu3hil9n7nd71'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

def main():
    usrs = Users.query.all()
    for user in usrs:
        print(f" {user.email}  {user.password}   {user.name}")


if __name__ == "__main__":
    with app.app_context():
        main()
