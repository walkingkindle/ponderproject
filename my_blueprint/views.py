from urllib.parse import urlencode

from flask import Blueprint, render_template, request, redirect, url_for
from flask_mail import Message, Mail

my_blueprint = Blueprint('my_blueprint', __name__,template_folder='templates',static_url_path='/static', static_folder='static')


@my_blueprint.route('/',methods=["POST","GET"])
def coming_soon():
    if request.method == 'POST':
        email = request.form.get('email')
        print(email)
        name = request.form.get('name')
        print(name)
        params = urlencode({'email': email, 'name': name})
        return redirect(url_for('notifications') + '?' + params)
    return render_template('coming-soon.html')
