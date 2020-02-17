from flask import render_template
import random

from app import app
from models import Meal,Category, db

@app.route("/")
def index():
    diction = {}

    categories = db.session.query(Category).all()
    for category in categories:
        diction[category.title] = db.session.query(Category).filter(Category.title == category.title).first().meal

    return render_template("main.html", diction=diction, categories=categories)


@app.route("/cart/")
def cart():
    return render_template("cart.html")


@app.route("/account/")
def acc():
    return render_template("account.html")


@app.route("/login")
def login():
    return render_template("auth.html")


@app.route("/logout")
def logout():
    pass
