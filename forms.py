from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL,Email,Length,ValidationError
from wtforms.validators import email
from email_validator import validate_email, EmailNotValidError
from flask_ckeditor import CKEditorField




class Write(FlaskForm):
    body = CKEditorField("Ponder Here:", validators=[DataRequired()])
    submit = SubmitField("Submit")

def my_length_check(form, field):
    if int in field.data:
        raise ValidationError('Username contain at least one number.')
def my_password_length_checker(form,field):
    rules = [lambda field: any(x.isupper() for x in field),  # must have at least one uppercase
             ]
    if all(rule(field) for rule in rules):
        pass
    else:
        raise ValidationError('Your password must have at least one uppercase letter.')
class Register(FlaskForm):
    email = StringField("Email",validators=[DataRequired(),Email()],render_kw={"placeholder": "E-mail"})
    password = PasswordField("Password",validators=[DataRequired(),Length(min=6,max=50),my_password_length_checker],render_kw={"placeholder": "Password"})
    username = StringField("Username",validators=[DataRequired(),my_length_check],render_kw={"placeholder": "Username"})
    submit = SubmitField("Register")


    #fix the email validator so that it works.