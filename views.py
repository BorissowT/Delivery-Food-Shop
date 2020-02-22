from flask import render_template, request, session, flash
import random
from flask_wtf.csrf import CSRFProtect
import datetime

from app import app
from models import Meal, Category, User, Order, db
from forms import ORDER, USER


app.secret_key = 'my-super-secret-phrase-I-do-not-tell-this-to-nobody'
csrf = CSRFProtect(app)

def total():
    cart_list = []
    total_cost = 0
    cart = session.get("cart", [])
    ######getting ids from session and finding in db elemnts with ids###
    for id in cart:
        newmeal = db.session.query(Meal).filter(Meal.id == id).first()
        cart_list.append(newmeal)
        total_cost += int(newmeal.price)
        session["total"] = total_cost
    return total_cost


@app.route("/", methods=["POST", "GET"])
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
    cart = session.get("cart", [])
    total_cost = total()
    return render_template("main.html", diction=diction, categories=categories, randomlist=randomlist,
                           amount=len(cart), total_cost=total_cost)


@app.route("/cart/", methods=["POST", "GET"])
def cart():
    form = ORDER()
    ######добавление элемента ##########################
    if request.method == "POST" and request.form.get('cart'):
        cart = session.get("cart", [])
        meal = request.form.get('cart')
        cart.append(meal)
        session['cart'] = cart
    ######удаление из сессии выбранного элемента########
    elif request.method == "POST" and request.form.get('delete'):
        delete = request.form.get('delete')
        cart = session.get("cart", [])
        if delete in session["cart"]:
            cart.pop(session["cart"].index(delete))
            flash("Блюдо удалено из корзины")
        session["cart"] = cart
    elif request.method == "POST" and request.form.get('submit'):
        if form.validate_on_submit():
            if db.session.query(User).filter(User.mail == form.mail.data).first() == None:
                return ("Please register")########################################################## send User to registration
            else:
                user = db.session.query(User).filter(User.mail == form.mail.data).first()
                now = datetime.datetime.now()
                cart_list = []
                total_cost = 0
                cart = session.get("cart", [])
                for id in cart:
                    newmeal = db.session.query(Meal).filter(Meal.id == id).first()
                    cart_list.append(newmeal)
                    total_cost += int(newmeal.price)
                    session["total"] = total_cost
                order = Order(data=now.strftime("%Y-%m-%d %H:%M"), summ=total_cost, status="выполняется",
                              user_id=user.id, user=user, meals=cart_list)
                db.session.add(order)
                db.session.commit()
                session.pop("cart")
                session.pop("total")
                return render_template("ordered.html")
    cart_list = []
    cart = session.get("cart", [])
    for id in cart:
        newmeal = db.session.query(Meal).filter(Meal.id == id).first()
        cart_list.append(newmeal)
    total_cost = total()
    return render_template("cart.html", cart=cart_list, total_cost=total_cost, form=form, amount=len(cart))


@app.route("/account/")
def acc():
    return render_template("account.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    form = USER()

    if request.method == "POST":
        if form.validate_on_submit():
            print(form.mail)
            print(form.password)
    return render_template("auth.html", form=form)


@app.route("/logout")
def logout():
    pass
