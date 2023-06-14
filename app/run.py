# ----------------------------------------------------------------------IMPORTS------------------------------------------
# FLASK
import json

import config
import forms
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, session, abort, redirect, request,session,g
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_mail import Mail, Message
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import IntegrityError

import engine
from my_blueprint.views import my_blueprint
# WERZEUG
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# MISCELLANIOUS
import random
import pprint

import datetime

import pyshorteners as ps
#email verification
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import SignatureExpired


#PIL for small images
from PIL import Image

from models import User,Posts
from database import users,initialize_app
# SQL
from sqlalchemy.orm import relationship
from forms import Write, Register,ForgotPassword,ResetPassword
from sqlalchemy import or_

# GOOGLE AUTH
import google.auth.transport.requests
from authlib.integrations.flask_client import OAuth
import os
import pathlib
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import uuid
# wikiquotes
import wikiquotes
from wikiquotes.managers.custom_exceptions import TitleNotFound
# -----------------------------------------------------------FLASK APP----------------------------------------





# Initiating Flask APP
app = initialize_app('sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = config.urlsafe_secret
app.config['MAX_CONTENT_PATH'] = 1000000
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = config.email
app.config['MAIL_PASSWORD'] = config.password
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAIL_SENDER'] = config.email
app.config['MAIL_DEFAULT_ADDRESS'] = config.email
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
with app.app_context():
    users.create_all()








ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = 'static/files'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)
mail = Mail(app)
app.register_blueprint(my_blueprint, url_prefix='/pages')

s = URLSafeTimedSerializer(config.urlsafe_secret)
# OATH GOOGLE
oauth = OAuth(app)
oauth.init_app(app)


client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client-secret.json")
flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile",
                                             "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                     redirect_uri="https://www.ponder.ink/callback")


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"




def allowed_file(filename):
    """Verifies the file for file upload to make sure the file is valid"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




# -------------------------------------- FLASK ROUTES -----------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Loads the user id"""
    return User.query.get(user_id)


@app.route("/")
def home():
    """Main index route"""
    sent = request.args.get("sent")
    profile_photo_updated = request.args.get('profile_photo_updated')
    email_sent = request.args.get('email_sent')
    expired = request.args.get('expired')
    has_account = request.args.get('has_account')
    if expired:
        email = request.args.get('email')
        user = users.session.query(User).filter_by(email=email).first()
        if user:
            users.session.delete(user)
            users.session.commit()
    how_many = User.query.count()
    if sent:
        print(sent)
    return render_template("Index.html", quote=engine.get_random_quote(), sent=sent, current_user=current_user,
                           how_many=how_many,email_sent=email_sent,expired=expired,has_account=has_account,profile_photo_updated=profile_photo_updated)


@app.route("/dashboard",methods=["POST","GET"])
@login_required
def dashboard():
    random_quote = request.args.get('quote')
    try:
        clippings_filename = "My_Clippings.txt" + str(current_user.id)
        quote_list = engine.extract_quotes_with_writers(clippings_path=app.config['UPLOAD_FOLDER'], filename=clippings_filename)
        quote_pair = random.choice(quote_list)
        real_quote = quote_pair[1]
        print(real_quote)
        real_writer = quote_pair[0]
        print(real_writer)
        if real_quote == real_writer:
            new_pair = random.choice(quote_list)
            real_quote = new_pair[0]
            real_writer = new_pair[1]
        all_posts = Posts.query.all()
        if request.method == 'POST':
            return redirect(url_for('write-from-kindle',quote=real_quote,writer=real_writer,redirect_from='dashboard'))
    except FileNotFoundError:
            return redirect(url_for('upload',not_uploaded=True))
    return render_template("Dashboard.html", quote=real_quote, writer=real_writer, all_posts=all_posts)

@app.route("/select",methods=["POST","GET"])
def select():
    clippings_filename = "My_Clippings.txt" + str(current_user.id)
    book_list = engine.get_all_writers(clippings_path=app.config['UPLOAD_FOLDER'],filename=clippings_filename)
    if request.method == 'POST':
        selected_items = request.form.get('selected_items')

    return render_template('select.html',book_list=book_list)


@app.route('/notification')
def notifications():
    """The 'feature in progress' page. Using this whenever I haven't built a feature yet."""
    name = request.args.get('name')
    email = request.args.get('email')
    print(name)
    print(email)
    msg = Message(subject=f"Hi {name}",
                  body=f'Thanks for subscribing. You will receive a notification once we get'
                       f' the feature up and running. \n',
                  sender='ponder.contactus@gmail.com', recipients=[email])
    mail.send(msg)
    return redirect(url_for('home', sent=True))


@app.route('/choose-your-path')
def choose_path():
    user_id = session.get('id')
    print(user_id)
    return render_template("Upload-File.html", current_user=current_user,user_id=user_id)


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    not_uploaded = request.args.get("not_uploaded")
    if request.method == 'POST':
        try:
            file = request.files.get('My Clippings')
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                   secure_filename(file.filename + str(current_user.id))))
            current_user.clippings_filename = file.filename + str(current_user.id)
            users.session.commit()
            if file:
                return redirect(url_for("select", redirect_from="upload", current_user=current_user))
            else:
                return redirect(url_for("nothing_selected", current_user=current_user))
        except FileNotFoundError:
            return redirect(url_for('nothing_selected'))
    return render_template("Kindle-Upload.html", current_user=current_user,not_uploaded=not_uploaded)


@app.route("/see-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def see_post(post_id):
    requested_post = Posts.query.get(post_id)
    if int(current_user.id) == int(requested_post.author_id):
        can_edit = True
    else:
        can_edit = False
    # share_link_twitter = engine.link_shortener("https://twitter.com/intent/tweet?text=http://ponder.ink/{{url_for('see_post',post_id=post.id)}}")
    # share_link_linkedin = engine.link_shortener("https://www.linkedin.com/shareArticle?mini=true&url=http://ponder.ink/{{url_for('see_post',post_id=post.id)}}")
    # share_link_facebook = engine.link_shortener("https://www.facebook.com/sharer/sharer.php?u=http%3A//ponder.ink/%7B%7Burl_for('see_post',post_id=post.id)%7D%7D")
    return render_template("see-post.html", post=requested_post,can_edit=can_edit)


@app.route('/nothing-here')
def nothing_selected():
    return render_template("file-not-selected.html")


@app.route("/search-page", methods=['POST', 'GET'])
@login_required
def search_page():
    """A feature which gives the user a choice to search the books and authors in case he/she does not own a Kindle."""
    contribute = request.args.get('contribute')
    not_given= request.args.get('not_given')
    print(contribute)
    books = []
    authors = []
    quotes_list = []
    if request.method == 'POST':
        for i in range(1, 6):
            author = request.form.get('author')
            authors.append(author)
        print(authors)
        for author in authors:
            try:
                try:
                    quote = wikiquotes.get_quotes(author=author, raw_language='en')
                except KeyError:
                    return redirect(url_for('search_page',not_given=True))
                print(quote)
                quotes_list.append(quote)
            except TitleNotFound:
                quote = "If you're seeing this, it means that we couldn't find any quotes on this author/book." \
                        "Click on the link below to contribute to the quote API with more quotes."
                contribute = True
                return redirect(url_for('paper_reader',quote=quote,contribute=contribute))
        print(quotes_list)
        if len(quotes_list) > 0:
            quote = random.choice(quotes_list)
            print(quotes_list[0])
            return redirect(url_for('paper_reader', redirect_from='search', quote=quote))
    return render_template("Search.html",contribute=contribute,redirect_from='search',not_given=not_given)

@app.route("/contribute")
@login_required
def contribute():
    """Add a quote to the wikiquotes.org api"""
    contribute = True
    form = forms.ContributeForm()
    if form.validate_on_submit():
        # Set the parameters for the new quote
        page_title = "Wikiquote:Quote of the day"
        section_title = "May 12, 2023"
        quote_text = form.quote.data
        quote_author = current_user.username

        # Set the API endpoint for creating a new section
        api_url = "https://en.wikiquote.org/w/api.php"

        # Set the parameters for the API request
        params = {
            "action": "edit",
            "format": "json",
            "title": page_title,
            "section": "new",
            "sectiontitle": section_title,
            "text": f"'''{quote_author}:''' {quote_text}"
        }

        # Set the headers for the API request (including the user agent)
        headers = {
            "User-Agent": "MyWikiquoteBot/1.0"
        }

        # Send the API request
        response = requests.post(api_url, params=params, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            print("New quote added successfully!")
        else:
            print("Error adding new quote:", response.text)
        return redirect(url_for('home'))
    return render_template("Write.html",contribute = contribute,form = form,current_user=current_user)



@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token,salt='email-confirm',max_age=7200)
        user = users.session.query(User).filter_by(email=email).first()
        user.confirmed = True
        users.session.commit()
        login_user(user)
        return redirect(url_for("choose_path", current_user=current_user,user_id=current_user.id))
    except SignatureExpired:
        email = request.args.get('email')
        return redirect(url_for('choose_path',expired=True,email=email))



@app.route('/login_with_twitter')
def login_with_twitter():
    pass
    #needs website link

@app.route("/twitter-authorized")
def twitter():
    pass
    #needs website link


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    if request.method == 'POST':
        e_mail = request.form.get("email")
        password = form.password.data
        username = form.username.data
        hashed_password = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
        user_id = engine.generate_custom_id()
        check_and_find = users.session.query(User).filter(or_(User.email == e_mail, User.username == username)).first()
        if check_and_find:
            has_account = True
            return render_template("auth/sign-in.html", has_account=has_account)
        else:
            new_user = User(
                email=e_mail,
                password=hashed_password,
                username=username,
                id=user_id
            )
            users.session.add(new_user)
            users.session.commit()
            token = s.dumps(e_mail,salt='email-confirm')
            link = url_for('confirm_email',token=token,_external=True,email=e_mail,user_id=new_user.id)
            session['id'] = new_user.id
            msg = Message(' Confirm Email ', sender=app.config['MAIL_SENDER'], recipients=[e_mail],body=engine.confirmation_email(link))
            mail.send(msg)
            email_sent= True
        return redirect(url_for('home',email_sent=email_sent,email=e_mail))
    return render_template("auth/sign up.html", current_user=current_user, form=form)


@app.route('/login-with-google')
def login_with_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/log_in", methods=["POST", "GET"])
def log_in():
    has_account = request.args.get('has_account')
    if request.method == 'POST':
        entered_email = request.form.get('email')
        entered_password = request.form.get('password')
        user = users.session.query(User).filter_by(email=entered_email).first()
        print(f"{user} is")
        if user:
            if check_password_hash(pwhash=user.password, password=entered_password) and user.confirmed:
                login_user(user)
                return redirect(url_for("choose_path", current_user=current_user))
            else:
                wrong_password = True
                return render_template("auth/sign-in.html", wrong_password=wrong_password, email_doesnt_exist=False)
        else:
            email_doesnt_exist = True
            return render_template("auth/sign-in.html", email_doesnt_exist=email_doesnt_exist)
    else:
        entered_email = request.args.get('email', '')
        return render_template("auth/sign-in.html", email=entered_email,has_account=has_account)



@app.route("/new-password/<token>",methods=["POST","GET"])
def new_password(token):
    form = ResetPassword()
    if form.validate_on_submit():
        email = s.loads(token,salt='password-reset',max_age=600)
        password = form.new_password.data
        user = users.session.query(User).filter_by(email=email).first()
        hashed_password = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
        user.password = hashed_password
        users.session.commit()
        return redirect(url_for('home'))
    return render_template('reset-password.html',form=form)






@app.route("/reset-password",methods=["POST", "GET"])
def reset_password():
    email_form = ForgotPassword()
    if email_form.validate_on_submit():
        e_mail = email_form.email.data
        user = users.session.query(User).filter_by(email=e_mail).first()
        if user:
            user_id = user.id
            token = s.dumps(e_mail, salt='password-reset')
            link = url_for('new_password', token=token, _external=True, email=e_mail,user_id=user_id)
            msg = Message(' Reset Password Request ', sender=app.config['MAIL_USERNAME'], recipients=[e_mail],
                  body=f'Please reset your password with this link:{link}')
            mail.send(msg)
            email_sent = True
            return redirect(url_for('home', user_id=user_id,email_sent=email_sent))
        else:
            return abort(404)
    return render_template('reset-password.html',email=True,form=email_form)


@app.route("/callback")
def callback():
    """Google auth callback"""
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args['state']:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)
    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=config.GOOGLE_CLIENT_ID
    )
    pprint.pprint(id_info)
    user = users.session.query(User).filter_by(email=id_info['email']).first()
    if user:
        return redirect(url_for('home',has_account=True))
    username = id_info['name']
    email = id_info['email']
    first_name = id_info['given_name']
    last_name = id_info['family_name']
    user = users.session.query(User).filter_by(email=email).first()
    if user:
        login_user(user)
        return redirect(url_for('home', current_user=current_user))
    else:
        try:
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                id=engine.generate_custom_id(),
                confirmed=True
            )
            login_user(new_user)
            users.session.add(new_user)
            users.session.commit()
        except IntegrityError:
            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                id=engine.generate_custom_id(),
                confirmed=True
            )
        return redirect(url_for('choose_path', current_user=current_user))



@app.route("/about")
def about():
    return render_template("about-us.html")

@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    """Based on the redirect, write page will show different quotes."""
    form = Write()
    new_quote = engine.get_random_quote()
    redirect_from = request.args.get("redirect_from")
    if redirect_from == 'home':
        print(redirect_from)
        body = form.body.data
        quote2 = form.quote.data
        post_id = engine.generate_custom_id()
        quote_author = form.author.data
        current_date = datetime.datetime.now()
        print(current_date)
        formatted_datetime = current_date.strftime("%d/%m/%Y")
        if form.validate_on_submit():
            print("submitted")
            new_post = Posts(
                quote=new_quote,
                body=body,
                id=post_id,
                user=current_user,
                date=formatted_datetime,
                user_quote=quote2,
                quote_author=quote_author
            )
            users.session.add(new_post)
            users.session.commit()
            print("new post entered into the database.")
            return redirect(url_for("see_post", form=form, current_user=current_user, post_id=post_id,
                                    redirect_from=redirect_from))
    return render_template("Write.html", form=form, current_user=current_user, quote=new_quote,
                           redirect_from=redirect_from)

@app.route("/write-from-kindle",methods=["POST","GET"])
def write_from_kindle():
    redirect_from = "dashboard"
    quote = request.args.get('quote')
    writer = request.args.get("writer")
    print(writer)
    real_writer = engine.get_writer_only(writer)
    form = forms.Write(
        author= real_writer
    )
    body = form.body.data
    quote2 = form.quote.data
    quote_author = form.author.data
    post_id = engine.generate_custom_id()
    current_date = datetime.datetime.now()
    formatted_datetime = current_date.strftime("%d/%m/%Y")
    if form.validate_on_submit():
        new_post = Posts(
            quote=f"{quote}, {writer}",
            body=body,
            id=post_id,
            user=current_user,
            date=formatted_datetime,
            user_quote=quote2,
            quote_author=quote_author
        )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", quote=quote, form=form, current_user=current_user,
                                post_id=post_id,
                                redirect_from=redirect_from))
    return render_template("Write.html", form=form, quote=quote, writer=writer, current_user=current_user,
                           redirect_from=redirect_from)
@app.route('/paper-reader', methods=["POST", "GET"])
def paper_reader():
    """A feature that searches books from an API and gets famous quotes from them. Used in case the user does not own a
     Kindle"""
    contribute = request.args.get('contribute')
    form = Write()
    quote = str(request.args.get('quote'))
    body = form.body.data
    quote2 = form.quote.data
    author = form.author.data
    post_id = engine.generate_custom_id()
    current_date = datetime.datetime.now()
    formatted_datetime = current_date.strftime("%d/%m/%Y")
    if form.validate_on_submit():
        new_post = Posts(
            quote=f"{quote}",
            body=body,
            id=post_id,
            quote_author = author,
            user=current_user,
            date=formatted_datetime,
            user_quote=quote2
        )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", quote=str(quote), form=form, current_user=current_user, post_id=new_post.id))
    return render_template("Write.html", form=form, current_user=current_user, quote=str(quote),contribute=contribute)

@app.route("/reset/<int:user_id>")
def reset_photo(user_id):
    user = users.session.query(User).filter_by(id=user_id).first()
    user.user_photo = None
    users.session.commit()
    return redirect(url_for('account',user_id=user_id))





@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
def edit_post(post_id):
    post = Posts.query.get(post_id)
    quote = post.quote
    edit_form = forms.Write_Edit(
        quote=post.user_quote,
        body=post.body,
        author = post.quote_author,
        real_quote = post.quote
    )
    if edit_form.validate_on_submit():
        post.quote = edit_form.real_quote.data
        post.quote_author = edit_form.author.data
        post.user_quote = edit_form.quote.data
        post.body = edit_form.body.data
        post.author = current_user
        users.session.commit()
        return redirect(url_for('see_post', post_id=post.id))
    return render_template('Write.html', form=edit_form, is_edit=True, current_user=current_user, quote=quote)


@app.route("/contact-me", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        subject = request.form.get("subject")
        sender_email = request.form.get("email")
        body = request.form.get("message")
        msg = Message(subject=subject, body=f' From:{name}, {sender_email}\n {body}', sender=sender_email,
                      recipients=[app.config['MAIL_USERNAME']])
        mail.send(msg)
        sent = True
        return redirect(url_for("home", sent=sent, current_user=current_user))
    sent = False
    return render_template("contact-me.html", sent=sent, current_user=current_user)


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

        if new_username and new_username != current_user.username:
            current_user.username = new_username

        if new_email and new_email != current_user.email:
            current_user.email = new_email

        if new_password and new_password != current_user.password:
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


@app.route("/account/<int:user_id>", methods=["GET", "POST"])
@login_required
def account(user_id):
    user = users.session.query(User).filter_by(id=user_id).first()

    if request.method == "POST":
        photo = request.files['photo']
        username = request.form.get('username')
        name = request.form.get('name')
        continent = request.form.get('continent')
        if photo:
            img = Image.open(photo)
            max_size = (315,315)
            img.thumbnail(max_size)
            filename,ext = os.path.splitext(photo.filename)
            filename = secure_filename(str(user.id) + 'profile' + ext)
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img.save(img_path)
            user.user_photo = filename
        user.username = username
        user.first_name = name
        user.continent = continent
        users.session.commit()
        return redirect(url_for('home',profile_photo_updated=True))
    if user.user_photo:
        img_path = '/static/files/' + user.user_photo
        return render_template("account-info.html",user=user,img_path=img_path)
    else:
        pass
        return render_template("account-info.html",user=user)

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


if __name__ == "__main__":
    app.run(debug=True)