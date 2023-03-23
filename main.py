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
from forms import Write





#-----------------------------------------------------------FLASK APP---------------------------------------------------
#Initiating FLask APP
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['MAX_CONTENT_PATH'] = 1000000
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = r"C:\Users\Aleksa Hadzic\PycharmProjects\Ponderproject\documents"
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)

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


# Creating Tables

# with app.app_context():
#     users.create_all()
#     users.session.commit()

#-----------------------------------------------------------ENGINE------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_random_quote_from_kindle():
    check_letter = '-'
    with open('documents/My Clippings.txt','r',encoding='utf-8') as quotes:
        kindle_quotes = quotes.readlines()
        quote_list = [idx for idx in kindle_quotes if idx[0] != check_letter and idx[0] != '=']
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


#-------------------------------------- FLASK ROUTES -----------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
@app.route("/")
def home():
    return render_template("Index.html",quote=get_random_quote())


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("Dashboard.html")


@app.route('/choose-your-path')
def choose_path():
    return render_template("Upload File.html")


# @app.route("/upload",methods=['GET','POST'])
# def upload():
#     if request.method['POST']:
#         if 'My Clippings' not in request.files:
#             flash("No file part")
#             return redirect(url_for("upload"))
#         file = request.files['My Clippings']
#         if file.filename == ''
#             flash("No selected file")
#     return render_template("Kindle Upload.html")

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
        users.session.add(new_user)
        users.session.commit()
        login_user(new_user)
        return redirect(url_for("choose_path"),current_user=current_user)
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
                flash("Invalid Password")
                return redirect(url_for("login",current_user=current_user))
        else:
            flash("This E-mail doesn't exist. Please create your account.")
            return redirect(url_for("login",current_user=current_user))
    return render_template("sign-in.html")

@app.route('/write',methods=['GET','POST'])
@login_required
def write():
    form = Write()
    redirect_from = request.args.get('redirect_from','')
    return render_template("Write.html",quote=get_random_quote(),redirect_from=redirect_from,form=form)


@app.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect(url_for('home'))





if __name__ == '__main__':
    app.run(debug=True)
