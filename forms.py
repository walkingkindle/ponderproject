from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL,Email
from wtforms.validators import email
from flask_ckeditor import CKEditorField




class Write(FlaskForm):
    body = CKEditorField("Ponder Here:", validators=[DataRequired()])
    submit = SubmitField("Submit")