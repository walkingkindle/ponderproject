from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired, URL, Email, Length, ValidationError, Regexp,url
from wtforms.validators import email
from email_validator import validate_email, EmailNotValidError
from flask_ckeditor import CKEditorField




class Write(FlaskForm):
    quote = StringField("Quote of the Day:", render_kw={"class": "form-control", "placeholder": "Write a short version of the quote here."})
    author = StringField("Who is the Author of the quote?",validators=[DataRequired()])
    body = CKEditorField("Ponder Here:", render_kw={"class": "ckeditor", "data-ckeditor-skin": "moono-lisa", "data-ckeditor-fontSize_defaultLabel": "16px", "data-ckeditor-colorButton_colors": "000000,ffffff", "data-ckeditor-toolbar": "['Bold', 'Italic', 'Underline', '-', 'Link', 'Unlink', '-', 'Image']", "data-ckeditor-customConfig": """
                config.extraPlugins = 'image,link';
                config.removePlugins = 'flash';
                config.toolbarGroups = [                    { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
                    { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
                    { name: 'editing', groups: [ 'find', 'selection', 'spellchecker' ] },
                    { name: 'forms', groups: [ 'forms' ] },
                    { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
                    { name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
                    { name: 'links', groups: [ 'links' ] },
                    { name: 'insert', groups: [ 'insert' ] },
                    { name: 'styles', groups: [ 'styles' ] },
                    { name: 'colors', groups: [ 'colors' ] },
                    { name: 'tools', groups: [ 'tools' ] },
                    { name: 'others', groups: [ 'others' ] },
                    { name: 'about', groups: [ 'about' ] }
                ];
                """})

    submit = SubmitField("Submit")

class ContributeForm(FlaskForm):
    quote = StringField("Enter your quote here:",validators=[DataRequired()])



class Write_Edit(FlaskForm):
    real_quote = CKEditorField("Edit the author quote")
    quote = StringField("Quote of the Day:", render_kw={"class": "form-control", "placeholder": "Write a short version of the quote here."})
    author = StringField("Who is the Author of the quote?",validators=[DataRequired()])
    body = CKEditorField("Ponder Here:", render_kw={"class": "ckeditor", "data-ckeditor-skin": "moono-lisa", "data-ckeditor-fontSize_defaultLabel": "16px", "data-ckeditor-colorButton_colors": "000000,ffffff", "data-ckeditor-toolbar": "['Bold', 'Italic', 'Underline', '-', 'Link', 'Unlink', '-', 'Image']", "data-ckeditor-customConfig": """
                config.extraPlugins = 'image,link';
                config.removePlugins = 'flash';
                config.toolbarGroups = [                    { name: 'document', groups: [ 'mode', 'document', 'doctools' ] },
                    { name: 'clipboard', groups: [ 'clipboard', 'undo' ] },
                    { name: 'editing', groups: [ 'find', 'selection', 'spellchecker' ] },
                    { name: 'forms', groups: [ 'forms' ] },
                    { name: 'basicstyles', groups: [ 'basicstyles', 'cleanup' ] },
                    { name: 'paragraph', groups: [ 'list', 'indent', 'blocks', 'align', 'bidi' ] },
                    { name: 'links', groups: [ 'links' ] },
                    { name: 'insert', groups: [ 'insert' ] },
                    { name: 'styles', groups: [ 'styles' ] },
                    { name: 'colors', groups: [ 'colors' ] },
                    { name: 'tools', groups: [ 'tools' ] },
                    { name: 'others', groups: [ 'others' ] },
                    { name: 'about', groups: [ 'about' ] }
                ];
                """})

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

class ResetPassword(FlaskForm):
    new_password = PasswordField("Enter a new password",validators=[DataRequired()],render_kw={"placeholder": "Password"})
    submit = SubmitField("Change Password")


class ForgotPassword(FlaskForm):
    email = StringField("Please enter your E-mail",validators=[DataRequired()],render_kw={"placeholder":"email"})
    submit = SubmitField("Submit")