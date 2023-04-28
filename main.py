# ----------------------------------------------------------------------IMPORTS------------------------------------------
# FLASK
import config
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, url_for, flash, session, abort, redirect, request
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_mail import Mail, Message
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from sqlalchemy.exc import IntegrityError
from my_blueprint.views import my_blueprint
# WERZEUG
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# MISCELLANIOUS
import random
import pprint
from bs4 import BeautifulSoup
import datetime

#email verification
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import SignatureExpired
from config import urlsafe_secret



# SQL
from sqlalchemy.orm import relationship
from forms import Write, Register
from sqlalchemy import or_

# GOOGLE AUTH
import google.auth.transport.requests
from authlib.integrations.flask_client import OAuth
import os
import pathlib
from dotenv import load_dotenv
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

# wikiquotes
import wikiquotes
from wikiquotes.managers.custom_exceptions import TitleNotFound

# -----------------------------------------------------------FLASK APP----------------------------------------





# Initiating Flask APP
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('flask_secret_key')
app.config['MAX_CONTENT_PATH'] = 1000000
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MY_EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('MY_PASSWORD')
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = 'static/files'
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
                                     redirect_uri="http://127.0.0.1:5000/callback")

# ------------------------------------------------------------ SMTP ----------------------------------------------------
# Flask DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
users = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# Configure Tables
class User(users.Model, UserMixin):
    __tablename__ = "users"
    id = users.Column(users.Integer, primary_key=True)
    email = users.Column(users.String(250), nullable=False, unique=True)
    username = users.Column(users.String(250), nullable=True, unique=True)
    confirmed = users.Column(users.String(10),nullable=True)
    password = users.Column(users.String(1000), nullable=True)
    first_name = users.Column(users.String(250), nullable=True)
    last_name = users.Column(users.String(250), nullable=True)
    continent = users.Column(users.String(250), nullable=True)
    posts = relationship("Posts", back_populates="user")


class Posts(users.Model):
    __tablename__ = "posts"
    id = users.Column(users.Integer, primary_key=True, nullable=True)
    author_id = users.Column(users.String, users.ForeignKey('users.id'), nullable=True)
    clippings_filename = users.Column(users.String(250), nullable=True)
    user = relationship("User", back_populates="posts")
    body = users.Column(users.Text, nullable=True)
    quote = users.Column(users.String(250))
    date = users.Column(users.String(250), nullable=True)
    user_quote = users.Column(users.String(250), nullable=False)
    photo = users.Column(users.String(500), nullable=True)


# connect databases to each other.
# Creating Tables
#
with app.app_context():
    users.create_all()
    users.session.commit()


# -----------------------------------------------------------ENGINE------------------------------------------------------
def allowed_file(filename):
    """Verifies the file for file upload to make sure the file is valid"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def configure():
    """Protected info configuration"""
    load_dotenv()


def extract_quotes_with_writers(filename, clippings_path):
    """Takes My Clippings.txt and extracts it to a formatted string"""
    with open(rf"{clippings_path}/{filename}", "r", encoding="utf-8") as text_file:
        text = text_file.read()
        print(text)
        lines = text.splitlines()
        # Initialize an empty list to store the quotes and writers
        quotes_with_writers = []
        # Loop through the lines and extract the quotes and writers
        for line in lines:
            # Check if the line starts with a quotation mark
            if line.startswith('“') or line.startswith("- Your"):
                lines.remove(line)
            else:
                quotes_with_writers.append(line)
            quotes_formatted = []
            [quotes_formatted.append(x) for x in quotes_with_writers if x != '==========']
            if len(quotes_formatted) % 2 == 0:
                pair_list = [[quotes_formatted[i], quotes_formatted[i + 1]] for i in range(0, len(quotes_formatted), 2)]
            else:
                pair_list = [[quotes_formatted[i], quotes_formatted[i + 1]] for i in
                             range(0, len(quotes_formatted) - 1, 2)]
        return pair_list


def get_random_quote():
    """Scrapes the random quote of the internet when sometimes one of them does not work."""
    the_request = requests.get(url="https://www.litquotes.com/random-words-of-wisdom.php").content
    soup = BeautifulSoup(the_request, 'html.parser')
    find_quote = soup.find('span')
    print(find_quote.text)
    return find_quote.text


def also_get_random_quote():
    """Scrapes the random quote of the internet."""
    response = requests.get('https://api.quotable.io/random')
    r = response.json()
    quote = f"{r['content']}, {r['author']}"
    print(quote)
    return quote


def generate_custom_id():
    """Random ID for the database"""
    d_id = random.randint(0, 100)
    return d_id


# -------------------------------------- FLASK ROUTES -----------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    """Loads the user id"""
    return User.query.get(user_id)


@app.route("/")
def home():
    """Main index route"""
    sent = request.args.get("sent")
    email_sent = request.args.get('email_sent')
    expired = request.args.get('expired')
    if expired:
        email = request.args.get('email')
        user = users.session.query(User).filter_by(email=email).first()
        if user:
            users.session.delete(user)
            users.session.commit()
    how_many = User.query.count()
    if sent:
        print(sent)
    return render_template("Index.html", quote=get_random_quote(), sent=sent, current_user=current_user,
                           how_many=how_many,email_sent=email_sent,expired=expired)


@app.route("/dashboard")
@login_required
def dashboard():
    clippings_filename = "My_Clippings.txt"
    quote_list = extract_quotes_with_writers(clippings_path=app.config['UPLOAD_FOLDER'], filename=clippings_filename)
    quote = random.choice(quote_list)
    real_quote = quote[0]
    real_writer = quote[1]
    all_posts = Posts.query.all()
    if real_quote == real_writer:
        new_quote, new_writer = quote
        while new_quote == new_writer:
            new_quote, new_writer = random.choice(quote_list)
    else:
        pass

    if len(real_quote) < 20:
        new_quote, new_writer = quote
        while len(new_quote) < 20:
            new_quote, new_writer = random.choice(quote_list)

    if len(real_quote) > len(real_writer):
        real_quote, real_writer = real_writer, real_quote
    return render_template("Dashboard.html", quote=real_quote, writer=real_writer, all_posts=all_posts)


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
    return render_template("Upload File.html", current_user=current_user)


@app.route("/upload", methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            file = request.files.get('My Clippings')
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                   secure_filename(file.filename)))
            if file:
                return redirect(url_for("dashboard", redirect_from="upload", current_user=current_user))
            else:
                return redirect(url_for("nothing_selected", current_user=current_user))
        except FileNotFoundError:
            return redirect(url_for('nothing_selected'))
    return render_template("Kindle Upload.html", current_user=current_user)


@app.route("/see-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def see_post(post_id):
    requested_post = Posts.query.get(post_id)
    return render_template("see-post.html", post=requested_post)


@app.route('/nothing-here')
def nothing_selected():
    return render_template("file-not-selected.html")


@app.route("/search-page", methods=['POST', 'GET'])
def search_page():
    """A feature which gives the user a choice to search the books and authors in case he/she does not own a Kindle."""
    books = []
    authors = []
    quotes_list = []
    if request.method == 'POST':
        for i in range(1, 6):
            title = request.form.get('title')
            author = request.form.get('author')
            books.append(f"{title} by {author}")
            authors.append(author)
        print(authors)
        for author in authors:
            try:
                quote = wikiquotes.get_quotes(author=author, raw_language='en')
                print(quote)
                quotes_list.append(f"{quote}")
            except TitleNotFound:
                quote = None
        print(quotes_list)
        if len(quotes_list) > 0:
            quote = str(random.choice(quotes_list))
            final_quote = quote.replace("[", " ")
            final_final_quote = final_quote.replace("]", " ")
            return redirect(url_for('paper_reader', redirect_from='search', quote=final_final_quote))
    return render_template("Search.html")

@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token,salt='email-confirm',max_age=7200)
        user = users.session.query(User).filter_by(email=email).first()
        user.confirmed = True
        login_user(user)
        return redirect(url_for("choose_path", current_user=current_user))
    except SignatureExpired:
        email = request.args.get('email')
        return redirect(url_for('home',expired=True,email=email))




@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    if request.method == 'POST':
        e_mail = request.form.get("email")
        password = form.password.data
        username = form.username.data
        hashed_password = generate_password_hash(password=password, method="pbkdf2:sha256", salt_length=8)
        user_id = generate_custom_id()
        check_and_find = users.session.query(User).filter(or_(User.email == e_mail, User.username == username)).first()
        if check_and_find:
            flash("Your account already exist. Please log in.")
            return render_template("sign-in.html", redirect_from='register')
        else:
            token = s.dumps(e_mail,salt='email-confirm')
            link = url_for('confirm_email',token=token,_external=True,email=e_mail)
            msg = Message(' Confirm Email ', sender=app.config['MAIL_USERNAME'], recipients=[e_mail],body=f'Please confirm your e-mail with this link:{link}')
            mail.send(msg)
            email_sent= True
            new_user = User(
                email=e_mail,
                password=hashed_password,
                username=username,
                id=user_id
            )
            users.session.add(new_user)
            users.session.commit()
        return redirect(url_for('home',email_sent=email_sent,email=e_mail))
    return render_template("sign up.html", current_user=current_user, form=form)


@app.route('/login-with-google')
def login_with_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/log_in", methods=["POST", "GET"])
def log_in():
    if request.method == 'POST':
        entered_email = request.form.get('email')
        entered_password = request.form.get('password')
        user = users.session.query(User).filter_by(email=entered_email).first()
        if user:
            if check_password_hash(pwhash=user.password, password=entered_password) and user.confirmed == True:
                login_user(user)
                return redirect(url_for("choose_path", current_user=current_user))
            else:
                wrong_password = True
                return render_template("sign-in.html", wrong_password=wrong_password, email_doesnt_exist=False)
        else:
            email_doesnt_exist = True
            return render_template("sign-in.html", email_doesnt_exist=email_doesnt_exist)
    else:
        entered_email = request.args.get('email', '')
        return render_template("sign-in.html", email=entered_email)


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
        audience=os.getenv('GOOGLE_CLIENT_ID')
    )
    pprint.pprint(id_info)
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
                id=generate_custom_id(),
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
                id=generate_custom_id(),
                confirmed=True
            )
        return redirect(url_for('home', current_user=current_user))



@app.route("/about")
def about():
    return render_template("About us.html")

@app.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    """Based on the redirect, write page will show different quotes."""
    form = Write()
    new_quote = get_random_quote()
    redirect_from = request.args.get("redirect_from")
    if redirect_from == 'home':
        print(redirect_from)
        body = form.body.data
        quote2 = form.quote.data
        post_id = generate_custom_id()
        current_date = datetime.datetime.now()
        formatted_datetime = current_date.strftime("%d/%m/%Y")
        if form.validate_on_submit():
            new_post = Posts(
                quote=new_quote,
                body=body,
                id=post_id,
                user=current_user,
                date=formatted_datetime,
                user_quote=quote2
            )
            users.session.add(new_post)
            users.session.commit()
            return redirect(url_for("see_post", quote=new_quote, form=form, current_user=current_user, post_id=post_id,
                                    redirect_from=redirect_from))
    elif redirect_from == 'dashboard':
        print(redirect_from)
        dashboard_quote = request.args.get("quote")
        writer = request.args.get("writer")
        body = form.body.data
        quote2 = form.quote.data
        post_id = generate_custom_id()
        current_date = datetime.datetime.now()
        formatted_datetime = current_date.strftime("%d/%m/%Y")
        if form.validate_on_submit():
            new_post = Posts(
                quote=f"{dashboard_quote}, {writer}",
                body=body,
                id=post_id,
                user=current_user,
                date=formatted_datetime,
                user_quote=quote2
            )
            users.session.add(new_post)
            users.session.commit()
            return redirect(url_for("see_post", quote=dashboard_quote, form=form, current_user=current_user,
                                    post_id=post_id,
                                    redirect_from=redirect_from))
        return render_template("Write.html", form=form, quote=dashboard_quote, current_user=current_user,
                               redirect_from=redirect_from)
    return render_template("Write.html", form=form, current_user=current_user, quote=new_quote,
                           redirect_from=redirect_from)


@app.route('/paper-reader', methods=["POST", "GET"])
def paper_reader():
    """A feature that searches books from an API and gets famous quotes from them. Used in case the user does not own a
     Kindle"""
    form = Write()
    quote = str(request.args.get('quote'))
    body = form.body.data
    quote2 = form.quote.data
    post_id = generate_custom_id()
    current_date = datetime.datetime.now()
    formatted_datetime = current_date.strftime("%d/%m/%Y")
    if form.validate_on_submit():
        new_post = Posts(
            quote=f"{quote}",
            body=body,
            post_id=post_id,
            user=current_user,
            date=formatted_datetime,
            user_quote=quote2
        )
        users.session.add(new_post)
        users.session.commit()
        return redirect(url_for("see_post", quote=str(quote), form=form, current_user=current_user, post_id=id))
    return render_template("Write.html", form=form, current_user=current_user, quote=str(quote))


@app.route("/edit-post/<int:post_id>", methods=['GET', 'POST'])
def edit_post(post_id):
    post = Posts.query.get(post_id)
    quote = post.quote
    edit_form = Write(
        quote=post.user_quote,
        body=post.body,
    )
    if edit_form.validate_on_submit():
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


@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        return redirect(url_for("edit_user", current_user=current_user))
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
