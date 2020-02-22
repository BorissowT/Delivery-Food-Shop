import flask_wtf
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, ValidationError

from models import User, db

class ORDER(flask_wtf.FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    mail = EmailField('Mail', validators=[DataRequired(), Email()])
    number = StringField('Number', validators=[DataRequired()])

    def validate_number(self, field):
        #print(db.session.query(User).filter(User.mail == self.mail.data).first())
        if self.number.data[0] != "+":
            self.name.errors.append('Number has to start with "+"')
        if len(self.number.data) < 12:
            self.name.errors.append('Number must be less than 12 characters')

class USER(flask_wtf.FlaskForm):
    mail = EmailField('Mail', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])