from flask import render_template
import random

from app import app
from models import Meal,Category, db


@app.route("/")
def index():
    diction = {}
    randomlist = []
    counter = 0
    min = 10
    categories = db.session.query(Category).all()
    for category in categories:
        if len(db.session.query(Category).filter(Category.title == category.title).first().meal) < min:
            min = len(db.session.query(Category).filter(Category.title == category.title).first().meal)
        diction[category.title] = db.session.query(Category).filter(Category.title == category.title).first().meal
    while counter < 3:
        rand = random.randrange(1, min)
        if rand not in randomlist:
            randomlist.append(rand)
            counter += 1
    return render_template("main.html", diction=diction, categories=categories, randomlist=randomlist)


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
