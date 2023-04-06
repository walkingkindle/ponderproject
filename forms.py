from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length, ValidationError, Regexp
from wtforms.validators import email
from email_validator import validate_email, EmailNotValidError
from flask_ckeditor import CKEditorField




class Write(FlaskForm):
    body = CKEditorField("Ponder Here:", validators=[DataRequired()])
    submit = SubmitField("Submit")

def my_length_check(form, field):
    if any(c.isdigit() for c in field.data):
        raise ValidationError('Username must not contain any numbers.')

def my_password_length_checker(form, field):
    if len(field.data) < 6:
        raise ValidationError('Your password must have at least 6 characters.')
    if not any(x.isupper() for x in field.data):
        raise ValidationError('Your password must have at least one uppercase letter.')

class Register(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Email("Please enter a valid e-mail adress")],render_kw={"placeholder": "E-mail"})
    password = PasswordField('Password', [
        DataRequired(),
        Length(min=6),
        Regexp(
            '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{6,}$',
            message="Your password must contain at least one lowercase letter, one uppercase letter, one digit, and one special character"
        )
    ])
    username = StringField("Username",validators=[DataRequired(),my_length_check,Length(min=6,max=16)],render_kw={"placeholder": "Username"})
    submit = SubmitField("Register")


    #fix the email validator so that it works.