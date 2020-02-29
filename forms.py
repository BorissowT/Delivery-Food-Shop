import flask_wtf
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo

from models import User, db
from views import redirect


class ORDER(flask_wtf.FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    mail = EmailField('Mail', validators=[DataRequired(), Email()])
    number = StringField('Number', validators=[DataRequired()])

    def validate_number(self, number):
        if self.number.data[0] != "+":
            raise ValidationError('Number has to start with "+"')
        if len(self.number.data) < 12:
            raise ValidationError('Number must be less than 12 characters')

    def validate_mail(self, mail):
        if db.session.query(User).filter(User.mail == self.mail.data).first() == None:
            return True


class USER(flask_wtf.FlaskForm):
    mail = EmailField('Mail', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegistrationForm(flask_wtf.FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    mail = EmailField('Mail', validators=[DataRequired(), Email()])
    password1 = PasswordField("Password1", validators=[DataRequired()])
    confirm_password = PasswordField("Password2", validators=[DataRequired(), EqualTo("password1",
                                                                               message="Пароли не совпадают")])
    address = StringField('Address', validators=[DataRequired()])

    def validate_mail(self, mail):
        if db.session.query(User).filter(User.mail == self.mail.data).first() != None:
            raise ValidationError('Пользователь с такой почтой уже существует')
