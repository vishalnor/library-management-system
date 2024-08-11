from app import db, app, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    UserMixin,
)


# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    avatar = db.Column(db.String(512), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        print(check_password_hash(self.password_hash, password))
        return check_password_hash(self.password_hash, password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200), unique=True)
    google_id = db.Column(db.String(200), unique=True)
    title = db.Column(db.String(200), nullable=False)
    authors = db.Column(db.String(200))
    description = db.Column(db.Text)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    book = db.relationship("Book")
    user = db.relationship("User")


class Checkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_name = db.Column(db.String(200), nullable=False)


# Callback to load user object from ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create all tables
with app.app_context():
    db.create_all()
