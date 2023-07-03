from flask import Flask, redirect, url_for, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, current_user, login_required, login_user, logout_user
import os

app = Flask(__name__)

# DB configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "llave_secreta"

db = SQLAlchemy(app)

# Login config
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(db.Model, UserMixin):
	# __tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50))
	password = db.Column(db.String(50))
	email = db.Column(db.String(100))
	contacts = db.relationship("Contact", backref="user")

	def __init__(self, username, password, email):
		self.username = username
		self.password = password
		self.email = email

class Contact(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(50))
	email = db.Column(db.String(50)) 
	phone = db.Column(db.String(50))
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

	def __init__(self, name, email, phone, user_id):
		self.name = name
		self.email = email
		self.phone = phone
		self.user_id = user_id


@app.route("/")
def index():
	if current_user.is_authenticated:
		return redirect(url_for("home"))
	return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		email = request.form["email"]
		
		# Search for the user
		user = User.query.filter_by(username=username).first()

		# Check the user
		if user:
			if user.email == email:
				if user.password == password:
					login_user(user)
					return redirect(url_for("home"))
				else:
					flash("Wrong password")
					return redirect(url_for("login"))
			else:
				flash("Wrong email")
				return redirect(url_for("login"))
		else:
			flash("Wrong username")
			return redirect(url_for("login"))
		
	return render_template("auth/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		password2 = request.form["password2"]
		email = request.form["email"]

		# Check if the user does not exists
		user_username= User.query.filter_by(username=username).first()
		user_email = User.query.filter_by(email=email).first()
		if not user_username:
			if password == password2:
				if not user_email:
					# Add the user to the database
					user = User(username, password, email)
					db.session.add(user)
					db.session.commit()
					login_user(user)
					return redirect(url_for("home"))
				else:
					flash("The email is already in use")
					return redirect(url_for("register"))
			else:
				flash("The passwords do not coincide")
				return redirect(url_for("register"))
		else:
			flash("The username already exists")
			return redirect(url_for("register"))
	return render_template("auth/register.html")

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))

@app.route("/home")
@login_required
def home():
	return render_template("home.html")

@app.route("/add_contact", methods=["POST"])
@login_required
def add():
	if request.method == "POST":
		name = request.form["name"]
		email = request.form["email"]
		phone = request.form["phone"]
		if name and email and phone:
			# Add the contact
			contact = Contact(name, email, phone, current_user.id)
			db.session.add(contact)
			db.session.commit()
			flash("Contact added successfully")
			return redirect(url_for("home"))
		else:
			flash("All the fields are required")
			return redirect(url_for("home"))
	return render_template("auth/edit.html", mode="add")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
	contact = Contact.query.get_or_404(id)
	if request.method == "POST":
		contact.name = request.form["name"]
		contact.email = request.form["email"]
		contact.phone = request.form["phone"]
		
		db.session.commit()
		flash("Contact edited successfully")

		return redirect(url_for("home"))
	return render_template("auth/edit.html", contact=contact)

@app.route("/delete/<int:id>")
@login_required
def delete(id):
	contact = Contact.query.get_or_404(id)
	db.session.delete(contact)
	db.session.commit()
	flash("Contact removed successfully")
	return redirect(url_for("home"))