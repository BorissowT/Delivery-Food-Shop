from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

meals_orders_association = db.Table(
    "meals_orders",
    db.Column("order_id", db.Integer, db.ForeignKey("orders.id")),
    db.Column("meal_id", db.Integer, db.ForeignKey("meals.id")),
)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    mail = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    orders = db.relationship("Order", back_populates="user")
    role = db.Column(db.String(32), default="user", nullable=False)

    def __repr__(self):
        return "id: {0} имя: {1}".format(self.id, self.name)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


class Order (db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(50), nullable=False)
    summ = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="orders")
    meals = db.relationship(
        "Meal", secondary=meals_orders_association, back_populates="orders"
    )


class Meal (db.Model):
    __tablename__ = "meals"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text(250), nullable=False)
    picture = db.Column(db.Text(500), nullable=False)
    category = db.relationship("Category", back_populates="meal")
    orders = db.relationship(
        "Order", secondary=meals_orders_association, back_populates="meals")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    def __repr__(self):
        return "{}".format(self.title)


class Category (db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    meal = db.relationship("Meal", back_populates="category")

    def __repr__(self):
        return "{}".format(self.title)


#db.create_all()
