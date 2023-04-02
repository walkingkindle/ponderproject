#----------------------------------------------------------------------IMPORTS------------------------------------------

import random
import requests
from bs4 import BeautifulSoup
import itertools
from flask import Flask, render_template, redirect, url_for, flash,request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask import Flask, render_template
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user,login_manager
from wtforms import StringField, SubmitField,SelectField
from wtforms.validators import DataRequired,url
import csv
import uuid
import os
from forms import Write
import smtplib
from flask_mail import Mail,Message
from config import MY_EMAIL,MY_PASSWORD




#-----------------------------------------------------------FLASK APP---------------------------------------------------
#Initiating FLask APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['MAX_CONTENT_PATH'] = 1000000
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = MY_EMAIL
app.config['MAIL_PASSWORD'] = MY_PASSWORD
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = 'static/files'
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)
mail = Mail(app)


# ------------------------------------------------------------ SMTP ----------------------------------------------------




#Flask DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

users = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#Configure Tables
class User(users.Model,UserMixin):
        __tablename__ = "users"
        id = users.Column(users.String(36), primary_key=True, default=str(uuid.uuid4()))
        email = users.Column(users.String(250),nullable=False,unique=True)
        username = users.Column(users.String(250),nullable=False,unique=True)
        password = users.Column(users.String(1000),nullable=False,unique=True)
        first_name = users.Column(users.String(250),nullable=True)
        last_name = users.Column(users.String(250),nullable=True)
        continent = users.Column(users.String(250),nullable=True)
        clippings_filename = users.Column(users.String(250),nullable=True)


# Creating Tables

with app.app_context():
    users.create_all()
    users.session.commit()

#-----------------------------------------------------------ENGINE------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_random_quote_from_kindle(my_clippings):
    check_letter = '-'
    quote_list = [idx for idx in my_clippings if idx[0] != check_letter and idx[0] != '=']
    formatted_quotes = []
    for i in range(len(quote_list)):
        if quote_list[i].startswith('\n'):
            continue
        if quote_list[i].endswith('\n'):
            quote = quote_list[i].strip()
            author = quote_list[i - 1].strip()
            formatted_quote = f"{author}: {quote}"
            formatted_quotes.append(formatted_quote)
        random_kindle_quote = random.choice(formatted_quotes)
        print(random_kindle_quote)
        return random_kindle_quote
def get_random_quote():
    request = requests.get(url="https://www.litquotes.com/random-words-of-wisdom.php").content
    soup = BeautifulSoup(request, 'html.parser')
    find_quote = soup.find('span')
    print(find_quote.text)
    return find_quote.text

def also_get_random_quote():
        response = requests.get('https://api.quotable.io/random')
        r = response.json()
        quote = f"{r['content']}, {r['author']}"
        print(quote)
        return quote

def get_current_username():
    if current_user.is_authenticated:
        return current_user.username
    else:
        return None

def get_current_email():
    if current_user.is_authenticated:
        return current_user.email
    else:
        return None
def get_current_password():
    if current_user.is_authenticated:
        return current_user.password
    else:
        return None
def get_current_id():
    if current_user.is_authenticated:
        return current_user.id
    else:
        return None
#-------------------------------------- FLASK ROUTES -----------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
@app.route("/")
def home():
    sent = request.args.get("sent")
    if sent:
        print(sent)
    return render_template("Index.html",quote=get_random_quote(),sent=sent,current_user=current_user)


@app.route("/dashboard")
@login_required
def dashboard():
    # FIX THIS AND MAKE IT SO THAT IT CAN READ THE FILE
    already_uploaded_file = current_user.clippings_filename
    if already_uploaded_file:
        print("file already uploaded")
        with open(os.path.join(app.config['UPLOAD_FOLDER'], already_uploaded_file), 'r', encoding='UTF-8') as ponder_quotes:
            my_clippings = ponder_quotes.readlines()
            quote = get_random_quote_from_kindle(my_clippings=my_clippings)
        return render_template("Dashboard.html", quote=quote, redirect_from="home",current_user=current_user,has_file=True)
    else:
        ponder_text = request.args.get("file")
        if ponder_text == None:
            return render_template("Dashboard.html",redirect_from="home")
        else:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], ponder_text), 'r',encoding='UTF-8') as ponder_quotes:
                my_clippings = ponder_quotes.readlines()
                quote = get_random_quote_from_kindle(my_clippings=my_clippings)
                redirect_from = request.args.get("redirect_from")
    return redirect(url_for('write', redirect_from='dashboard', quote=quote))


@app.route('/choose-your-path')
def choose_path():
    return render_template("Upload File.html",current_user=current_user)


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('My Clippings')
        if file:
            filename = secure_filename(file.filename)
            current_user.clippings_filename = filename
            users.session.commit()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for("dashboard",file=filename,redirect_from='upload',current_user=current_user))
        else:
            return redirect(url_for("nothing_selected",current_user=current_user))
    return render_template("Kindle Upload.html",current_user=current_user)


@app.route('/nothing-here')
def nothing_selected():
    return render_template("file-not-selected.html")

@app.route("/search-page")
def search_page():
    return render_template("Search.html")

@app.route("/register",methods=['GET','POST'])
def register():
    if request.method == 'POST':
        e_mail = request.form.get('e-mail')
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password=password,method="pbkdf2:sha256",salt_length=8)
        new_user = User(
            email=e_mail,
            password=hashed_password,
            username=username
        )
        check_and_find = users.session.query(User).filter_by(email=e_mail).first()
        if check_and_find:
            flash("Your account already exist. Please log in.")
            return render_template("sign-in.html",redirect_from='register')
        users.session.add(new_user)
        users.session.commit()
        login_user(new_user)
        return redirect(url_for("choose_path",current_user=current_user))
    return render_template("sign up.html",current_user=current_user)

@app.route("/log_in",methods=["POST","GET"])
def log_in():
    if request.method == 'POST':
        entered_email = request.form.get('email')
        entered_pasword = request.form.get('password')
        user = users.session.query(User).filter_by(email=entered_email).first()
        if user:
            if check_password_hash(pwhash=user.password,password=entered_pasword):
                login_user(user)
                return redirect(url_for("choose_path",current_user=current_user))
            else:
                wrong_password = True
                if wrong_password:
                    print("true")
                return render_template("sign-in.html",wrong_password=wrong_password)
        else:
            email_doesnt_exist = True
            return redirect(url_for("log_in",current_user=current_user,email_doesnt_exist=email_doesnt_exist))
    return render_template("sign-in.html")

@app.route('/write',methods=['GET','POST'])
@login_required
def write():
    form = Write()
    redirect_from = request.args.get("redirect_from")
    quote = request.args.get("quote")
    print(quote)
    return render_template("Write.html",form=form,current_user=current_user,quote=quote)

@app.route("/contact-me",methods = ["GET","POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        subject = request.form.get("subject")
        sender_email = request.form.get("email")
        body = request.form.get("message")
        msg = Message(subject=subject, body=f' From: {sender_email}\n {body}', sender=sender_email, recipients=[app.config['MAIL_USERNAME']])
        mail.send(msg)
        sent = True
        return redirect(url_for("home",sent=sent,current_user=current_user))
    sent = False
    return render_template("contact-me.html",sent=sent,current_user=current_user)


@app.route("/edit_user", methods=["GET", "POST"])
@login_required
def edit_user():
    """Searches the existing logs inside SQLite database and changes them accordingly"""
    if request.method == "POST":
        new_username = request.form.get("username")
        new_email = request.form.get("email")
        new_password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        continent = request.form.get("continent")

        if new_username and new_username != get_current_username():
            current_user.username = new_username

        if new_email and new_email != get_current_email():
            current_user.email = new_email

        if new_password and new_password != get_current_password():
            new_password_hashed = generate_password_hash(password=new_password, method="pbkdf2:sha256", salt_length=8)
            current_user.password = new_password_hashed

        if first_name and first_name != current_user.first_name:
            current_user.first_name = first_name

        if last_name and last_name != current_user.last_name:
            current_user.last_name = last_name

        if continent and continent != current_user.continent:
            current_user.continent = continent

        users.session.commit()
        return redirect(url_for("dashboard", current_user=current_user))
    return render_template("Edit-User.html", current_user=current_user)

@app.route("/account",methods=["GET","POST"])
def account():
    if request.method == "POST":
        return redirect(url_for("edit_user",current_user=current_user))
    return render_template("account-info.html")



@app.route("/delete_user", methods=["GET", "POST"])
@login_required
def delete_user():
    if request.method == "POST":
        print("yes")
        user = User.query.get(current_user.id)
        if user:
            users.session.delete(user)
            users.session.commit()
            logout_user()
            return redirect(url_for("home"))
    return render_template("delete-user.html")
@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect(url_for('home'))






if __name__ == '__main__':
    app.run(debug=True)
