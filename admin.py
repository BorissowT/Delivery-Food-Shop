from flask_admin import AdminIndexView, expose, BaseView, Admin
from flask_admin.contrib.sqla import ModelView

from app import app
from models import User, Order, Meal, Category, db
admin = Admin(app)


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Order, db.session))
admin.add_view(ModelView(Meal, db.session))
admin.add_view(ModelView(Category, db.session))