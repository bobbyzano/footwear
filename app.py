from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_uploads import UploadSet, configure_uploads, IMAGES
import timeit
import datetime
from flask_mail import Mail, Message
import os
from wtforms.fields.html5 import EmailField


app = Flask(__name__)
app.secret_key = "secret123"


# Config MySQL
mysql = MySQL()
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "Bobby"
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'codemartdb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


# Initialize the app for use with this MySQL class
mysql.init_app(app)




@app.route("/")
def index():

    return render_template('index1.html')


@app.route("/about")
def about():
    return render_template('about.html')


def is_logged_in(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized access, Please login", "danger")
            return redirect(url_for("login"))

    return wrapped


@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for("login"))


def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('admin_login'))

    return wrap


def not_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return redirect(url_for('admin'))
        else:
            return f(*args, *kwargs)

    return wrap


# user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    form = MyForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users (name, email, username,password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # commit to database
        mysql.connection.commit()

        # close connecction
        cur.close()

        # flash message
        flash("you have successfully registered", "success")
        return redirect("/login")

    # if request.method == "GET":
    return render_template("register.html", form=form)


# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # get form fields

        username = request.form["username"]
        password_candidate = request.form["password"]

        # create cursor
        cur = mysql.connection.cursor()

        # get user by name
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            #     get the hash
            data = cur.fetchone()
            password = data["password"]

            #  compare password
            if sha256_crypt.verify(password_candidate, password):
                app.logger.info("Password matched")
                session["logged_in"] = True
                session["username"] = username
                flash("you are succesfully logged in", "success")

                return redirect(url_for("index"))

            else:
                error = "Invalid login credentials"

                return render_template("login.html", error=error)

        else:
            error = "User not found"
            return render_template("login.html", error=error)

    return render_template("login.html", name="login")



@app.route("/business_account", methods=["GET", "POST"])
def bizreg():
    form = BizForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.legal_business_name.data
        email = form.legal_business_email.data
        phone = form.phone.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO business_acct (legal_business_name, legal_business_email, phone,password) VALUES(%s, "
                    "%s, %s, %s)",
                    (name, email, phone, password))

        # commit to database
        mysql.connection.commit()

        # close connecction
        cur.close()

        # flash message
        flash("you have successfully registered", "success")
        return redirect("/login")

    # if request.method == "GET":
    return render_template("business_account.html", form=form)


@app.route('/admin_login', methods=['GET', 'POST'])
@not_admin_logged_in
def admin_login():
    if request.method == 'POST':
        # GEt user form
        username = request.form['email']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM admin WHERE email=%s", [username])

        if result > 0:
            # Get stored value
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['firstName']

            # Compare password
            if(password_candidate, password):
                # passed
                session['admin_logged_in'] = True
                session['admin_uid'] = uid
                session['admin_name'] = name

                return redirect(url_for('admin'))

            else:
                flash('Incorrect password', 'danger')
                return render_template('pages/login.html')

        else:
            flash('Username not found', 'danger')
            # Close connection
            cur.close()
            return render_template('pages/login.html')
    return render_template('pages/login.html')


@app.route("/men", methods=['GET', 'POST'])
def men():
    return render_template("men.html")


@app.route("/women", methods=['GET', 'POST'])
def women():
    return render_template("women.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    return render_template("contact.html")


@app.route("/cart", methods=['GET', 'POST'])
def cart():
    return render_template("cart.html")



class MyForm(Form):
    name = StringField(u'Name', validators=
    [validators.input_required(), validators.Length(min=3, max=50)])

    email = StringField(u'Email', validators=
    [validators.input_required(), validators.Length(min=3, max=50)])

    username = StringField(u'Username', validators=
    [validators.input_required(), validators.length(min=3, max=50)])

    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


class BizForm(Form):
    legal_business_name = StringField(u'Legal business name', validators=
    [validators.input_required(), validators.Length(min=3, max=50)])

    legal_business_email = StringField(u'Legal business email', validators=
    [validators.input_required(), validators.Length(min=3, max=50)])

    phone = StringField(u'Phone', validators=
    [validators.input_required(), validators.length(min=3, max=50)])

    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


