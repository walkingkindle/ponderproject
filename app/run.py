# ----------------------------------------------------------------------IMPORTS------------------------------------------
# FLASK
import json

from oauthlib.oauth2 import MismatchingStateError

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
from flask_dance.contrib.twitter import make_twitter_blueprint,twitter
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

from models import User, Posts, Books
from database import users,initialize_app
# SQL
from sqlalchemy.orm import relationship
from forms import Write, Register,ForgotPassword,ResetPassword
from sqlalchemy import or_, func

# GOOGLE AUTH
import google.auth.transport.requests
from authlib.integrations.flask_client import OAuth,OAuthError
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
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
Session(app)
with app.app_context():
    users.create_all()


def create_sample_post(current_user):
    """Just creating a sample post to show the user what posts, or quote comments really are, so to speak."""
    sample_post = Posts(
        quote="“It is important to expect nothing, to take every experience,"
              " including the negative ones, as merely steps on the path, and to proceed.”",
        body="Here goes something you can write about the quote, for example: This quote means... Or Ram Dass was...",
        id=engine.generate_custom_id(),
        user=current_user,
        date= None,
        user_quote="Sample Post",
        quote_author="Ram Dass",
        author_id=current_user.id
    )
    users.session.add(sample_post)
    users.session.commit()
    return "Sucess!"





ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = 'static/files'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "log_in"
bootstrap = Bootstrap(app)
ckeditor = CKEditor(app)
mail = Mail(app)
app.register_blueprint(my_blueprint, url_prefix='/pages')

s = URLSafeTimedSerializer(config.urlsafe_secret)
# OATH GOOGLE
oauth = OAuth(app)
oauth.init_app(app)
TWITTER_CLIENT_ID = config.TWITTER_CLIENT_ID
TWITTER_CLIENT_SECRET = config.TWITTER_CLIENT_SECRET
twitter_blueprint = make_twitter_blueprint(
    api_key= config.TWITTER_API_KEY,api_secret=config.TWITTER_API_SECRET_KEY,redirect_url="http://127.0.0.1:5000/"
                                                                                          "twitter_login"
)
app.register_blueprint(twitter_blueprint,url_prefix="/twitter_login")



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





@app.route("/my-ponder", methods=["GET", "POST"])
@login_required
def my_ponder_selections():
    book_list = users.session.query(Books.writer_quote).filter(Books.highlight_id == current_user.id).all()
    book_list = [engine.format_string(book[0]) for book in book_list]
    book_list = list(set(book_list))
    if request.method == "POST":
        selected_items = request.form.get('selected-books')
        book_list = selected_items.split("||")
        print(book_list)
        for writer in book_list:
            writer_query = users.session.query(Books).filter_by(writer_quote=writer)
            print(writer_query)
            for book in writer_query:
                users.session.delete(book)
            users.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("select.html", is_edit=True, current_user=current_user, book_list=book_list)








@login_manager.user_loader
def load_user(user_id):
    """Loads the user id"""
    return User.query.get(user_id)


@app.route("/")
def home():
    """Main index route"""
    real_quote = engine.get_random_quote()
    quote = real_quote[0]
    writer = real_quote[1]
    sent = request.args.get("sent")
    profile_photo_updated = request.args.get('profile_photo_updated')
    email_sent = request.args.get('email_sent')
    expired = request.args.get('expired')
    has_account = request.args.get('has_account')
    if has_account:
        return redirect(url_for('log_in',has_account=has_account))
    if expired:
        email = request.args.get('email')
        user = users.session.query(User).filter_by(email=email).first()
        if user:
            users.session.delete(user)
            users.session.commit()
    how_many = User.query.count()
    if sent:
        print(sent)
    return render_template("Index.html", quote=quote, writer=writer, sent=sent, current_user=current_user,
                           how_many=how_many,email_sent=email_sent,expired=expired,has_account=has_account,
                           profile_photo_updated=profile_photo_updated)




@app.route("/dashboard", methods=["POST", "GET"])
@login_required
def dashboard():
    post_images = ["/static/europe-street-1.jpg", "/static/europe-street-2.jpg", "/static/europe-street-3.jpg"]
    username = current_user.username
    current_index = session.get('quote_index', 0)
    try:
        all_quotes = users.session.query(Books).filter_by(highlight_id=current_user.id).all()
        try:
            random_quote = all_quotes[current_index]
            id = random_quote.id

            quote = random_quote.original_quote
            writer = random_quote.writer_quote
        except IndexError:              #There is only one book or one quote in the database.
            random_quote = users.session.query(Books).filter_by(highlight_id=current_user.id).first()
            id = random_quote.id
            quote = random_quote.original_quote
            writer = random_quote.writer_quote

    except AttributeError:
        return redirect(url_for('upload', not_uploaded=True))
    all_posts = users.session.query(Posts).filter_by(author_id=current_user.id).all()
    post_count = len(all_posts)
    if request.method == "POST":
      return redirect(url_for('write_from_kindle', quote_id=id))
    session['quote_index'] = current_index
    return render_template("Dashboard.html", quote_id=random_quote.id, quote=quote, writer=writer,
                           username=username, post_images=random.choice(post_images),
                           all_posts=all_posts, post_count=post_count)

@app.route("/dashboard/previous", methods=["POST","GET"])
@login_required
def dashboard_previous():
    all_quotes = users.session.query(Books).filter_by(highlight_id=current_user.id).all()
    current_index = session.get('quote_index', 0)
    current_index = (current_index - 1) % len(all_quotes)
    session['quote_index'] = current_index

    return redirect(url_for('dashboard'))

@app.route("/dashboard/next", methods=["POST","GET"])
@login_required
def dashboard_next():
    all_quotes = users.session.query(Books).filter_by(highlight_id=current_user.id).all()
    current_index = session.get('quote_index', 0)
    current_index = (current_index + 1) % len(all_quotes)
    session['quote_index'] = current_index

    return redirect(url_for('dashboard'))

@app.route("/select",methods=["POST","GET"])
@login_required
def select():
    clippings_filename = "My_Clippings.txt" + str(current_user.id)
    nothing_selected = request.args.get("nothing_selected")
    book_list = engine.get_all_writers(clippings_path=app.config['UPLOAD_FOLDER'],filename=clippings_filename)
    highlights = engine.format_kindle_clippings(clippings_path=app.config['UPLOAD_FOLDER'],filename=clippings_filename)
    if request.method == 'POST':
        selected_items = request.form.get('selected-books')
        real_book_list = selected_items.split("||")
        real_selected_highlights = []
        for highlight in highlights:
            parts = highlight.split("\n")
            for book in real_book_list:
                if book.strip() in highlight:
                 try:
                    writer = parts[0]
                    quote = parts[3]
                    date = parts[1]
                    real_selected_highlights.append({
                        "writer": writer,
                        "quote": quote,
                        "date": date
                    })
                 except IndexError:
                    pass # an exception raised after noticing that sometimes, there are highlights saved with a writer,
                    # date added, but no actual highlights. In this case, skip these highlights and continue onto the
                   # other hihglights that the book might have had
        for highlight in real_selected_highlights:
            new_highlight = Books(
                id=engine.generate_custom_id(),
                highlight_owner=current_user,
                original_quote= highlight["quote"],
                writer_quote=highlight["writer"],
                date_added=highlight["date"],
                paper=False
                )
            users.session.add(new_highlight)
            users.session.commit()
        posts = users.session.query(Posts).filter_by(author_id=current_user.id).first()
        if posts == None:
            create_sample_post(current_user=current_user)
        return redirect(url_for('dashboard'))
    return render_template('select.html',book_list=book_list,nothing_selected=nothing_selected)
    # except IndexError:
    #     return redirect(url_for('select',nothing_selected=True))


@app.route('/notification')
def notifications():
    """The 'feature in progress' page. Using this whenever I haven't built a feature yet."""
    name = request.args.get('name')
    email = request.args.get('email')
    msg = Message(subject=f"Hi {name}",
                  body=f'Thanks for subscribing. You will receive a notification once we get'
                       f' the feature up and running. \n',
                  sender='ponder.contactus@gmail.com', recipients=[email])
    mail.send(msg)
    return redirect(url_for('home', sent=True))


@app.route('/choose-your-path')
@login_required
def choose_path():
    user_id = session.get('id')
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
    return render_template("see-post.html", post=requested_post)


@app.route('/nothing-here')
def nothing_selected():
    return render_template("file-not-selected.html")



# LAGGING WITH THE LATEST DATABASE UPDATES, UPDATE AS NECESSARY
@app.route("/search-page", methods=['POST', 'GET'])
@login_required
def search_page():
    """A feature which gives the user a choice to
     search the books and authors in case he/she does not own a Kindle."""
    not_given= request.args.get('not_given')
    selected_highlights = []
    authors = []
    current_date = datetime.datetime.now()
    formatted_datetime = current_date.strftime("%d/%m/%Y")
    if request.method == 'POST':
        for i in range(1, 6):
            author = request.form.get('author')
            authors.append(author)
        real_authors = set(authors)
        for author in real_authors:
            try:
                try:
                    quote = wikiquotes.get_quotes(author=author, raw_language='en')
                    real_quotes = set(quote)
                    for q in real_quotes:
                        selected_highlights.append({
                            "author" : author,
                            "quote" : q,
                            "date" : formatted_datetime
                        })
                except KeyError:
                    #an exception for user not searching anything in the page.
                    return redirect(url_for('search_page',not_given=True))
            except TitleNotFound:
                #an exception when the API cannot find books with the designated name.
                quote = "If you're seeing this, it means that we couldn't find any quotes on this author/book." \
                        "Click on the link below to contribute to the quote API with more quotes."
                contribute = True
            for higlight in selected_highlights:
                new_highlight = Books(
                    id = engine.generate_custom_id(),
                    highlight_owner = current_user,
                    original_quote = str(higlight['quote']),
                    writer_quote = higlight['author'],
                    date_added = higlight['date'],
                    paper = True
                )
                users.session.add(new_highlight)
                users.session.commit()
        return redirect(url_for('paper_reader'))
    return render_template("Search.html",redirect_from='search',not_given=not_given)

@app.route("/contribute")
@login_required
def contribute():
    """Add a quote to the wikiquotes.org api"""
    contribute = True
    form = forms.ContributeForm()
    if form.validate_on_submit():
        page_title = "Wikiquote:Quote of the day"
        section_title = "May 12, 2023"
        quote_text = form.quote.data
        quote_author = current_user.username

        api_url = "https://en.wikiquote.org/w/api.php"

        params = {
            "action": "edit",
            "format": "json",
            "title": page_title,
            "section": "new",
            "sectiontitle": section_title,
            "text": f"'''{quote_author}:''' {quote_text}"
        }

        headers = {
            "User-Agent": "MyWikiquoteBot/1.0"
        }

        response = requests.post(api_url, params=params, headers=headers)

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
        return redirect(url_for('log_in',expired=True,email=email))



@app.route("/twitter_login")
def twitter_login():
    print(request.url)
    if not twitter.authorized:
        return redirect(url_for('twitter.login'))
    account_info = twitter.get('account/settings.json')
    if twitter.authorized:
        print("true")
    if account_info.ok:
        account_info_json = account_info.json()
        return f"sucess, {account_info_json['screen_name']}"
    return "request_failed"


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    googlep = request.args.get("google_log_in_problem")
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
            msg = Message(' Confirm Email ', sender=app.config['MAIL_SENDER'],
                          recipients=[e_mail],body=engine.confirmation_email(link))
            mail.send(msg)
            email_sent= True
        return redirect(url_for('home',email_sent=email_sent,email=e_mail))
    return render_template("auth/sign up.html", current_user=current_user, form=form,googlep=googlep)


@app.route('/login-with-google')
def login_with_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/log_in", methods=["POST", "GET"])
def log_in():
    has_account = request.args.get('has_account')
    expired = request.args.get("expired")
    reset = request.args.get("reset")
    print(expired)
    if request.method == 'POST':
        entered_email = request.form.get('email')
        entered_password = request.form.get('password')
        user = users.session.query(User).filter_by(email=entered_email).first()
        print(f"{user} is")
        if user:
            if check_password_hash(pwhash=user.password, password=entered_password) and user.confirmed:
                login_user(user)
                if users.session.query(Books).filter_by(highlight_id=current_user.id).first():
                    return redirect(url_for('dashboard',current_user=current_user))
                else:
                    return redirect(url_for("choose_path", current_user=current_user))
            else:
                wrong_password = True
                return render_template("auth/sign-in.html", wrong_password=wrong_password, email_doesnt_exist=False)
        else:
            email_doesnt_exist = True
            return render_template("auth/sign-in.html", email_doesnt_exist=email_doesnt_exist)
    else:
        entered_email = request.args.get('email', '')
        return render_template("auth/sign-in.html", email=entered_email,has_account=has_account,
                               expired=expired,reset=reset)



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
        return redirect(url_for('log_in',reset=True))
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
    try:
        flow.fetch_token(authorization_response=request.url)
    except MismatchingStateError:
        return redirect(url_for('register',google_log_in_problem=True))

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
    """This route will redirect the user to a random quote,
     which will then become a part of his library, after the post comment."""
    new_quote = engine.get_random_quote()
    quote = new_quote[0]
    print(quote)
    writer = new_quote[1]
    body = request.form.get("content")
    post_title = request.form.get("post-title")
    post_id = engine.generate_custom_id()
    current_date = datetime.datetime.now()
    formatted_datetime = current_date.strftime("%d/%m/%Y")
    if request.method == "POST":
        new_post = Posts(
            quote=quote,
            body=body,
            id=post_id,
            user=current_user,
            date=formatted_datetime,
            user_quote=post_title,
            quote_author=writer,
            author_id=current_user.id
            )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", current_user=current_user, post_id=post_id))
    return render_template("Write.html", current_user=current_user, quote=new_quote, writer=writer,redirect_from="home")

@app.route("/write-from-kindle/<int:quote_id>",methods=["POST","GET"])
@login_required
def write_from_kindle(quote_id):
    quote_row = Books.query.get(quote_id)
    if request.method == "POST":
        user_quote = quote_row.original_quote
        quote_author = quote_row.writer_quote
        current_date = datetime.datetime.now()
        formatted_datetime = current_date.strftime("%d/%m/%Y")
        post_id = engine.generate_custom_id()
        body = request.form.get("content")
        print(f"{body} is the body")
        post_title = request.form.get("post-title")
        print(f"{post_title} is the title of the post")
        new_post = Posts(
            quote=f"{quote_row.original_quote}, {quote_row.writer_quote}",
            body=body,
            id=post_id,
            user=current_user,
            date=formatted_datetime,
            user_quote=post_title,
            quote_author=quote_author,
            author_id=current_user.id
        )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", quote=quote_row.original_quote, current_user=current_user,
                                post_id=post_id))
    return render_template("Write.html", quote=quote_row.original_quote, writer=quote_row.writer_quote,
                           current_user=current_user,quote_id=quote_row.id)


@app.route('/paper-reader/', methods=["POST", "GET"])
def paper_reader():
    """A feature that searches books from an API and gets famous quotes from them. Used in case the user does not own a
     Kindle"""
    quote_row = users.session.query(Books).filter_by(paper=True).order_by(func.random()).first()
    quote = quote_row.original_quote
    print(f"quote is{quote}")
    writer = quote_row.writer_quote
    body = request.form.get("content")
    post_title = request.form.get("post-title")
    current_datetime = datetime.datetime.now()
    formatted_datetime = current_datetime.strftime("%d/%m/%Y")
    if request.method == "POST":
        new_post = Posts(
            quote=f"{quote}",
            body=body,
            id=engine.generate_custom_id(),
            quote_author = writer,
            user=current_user,
            date=formatted_datetime,
            user_quote=post_title
        )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", current_user=current_user, post_id=new_post.id))
    return render_template("Write.html", current_user=current_user,contribute=contribute,
                           quote=quote,writer=writer,quote_id=quote_row.id)

@app.route("/reset/<int:user_id>")
def reset_photo(user_id):
    user = users.session.query(User).filter_by(id=user_id).first()
    user.user_photo = None
    users.session.commit()
    return redirect(url_for('account',user_id=user_id))





@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    is_edit = request.args.get("is_edit")
    quote_row = users.session.query(Posts).filter_by(id=post_id).first()
    quote = quote_row.quote
    quote_author = quote_row.quote_author
    if request.method == "POST":
        print("YEEEEA")
        body = request.form.get("content")
        post_title = request.form.get("post-title")
        quote_row.body = body
        quote_row.user_quote = post_title
        users.session.commit()
        return redirect(url_for('see_post',post_id=quote_row.id))
    return render_template("Write.html",is_edit=is_edit,quote=quote,writer=quote_author,post_id=post_id,post=quote_row)

@app.route("/delete-post/<int:post_id>")
@login_required
def delete_post(post_id):
    post = users.session.query(Posts).filter_by(id=post_id).first()
    users.session.delete(post)
    users.session.commit()
    return redirect(url_for('dashboard'))



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