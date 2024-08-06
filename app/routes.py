from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    Blueprint,
    render_template_string,
    json,
    url_for,
    session,
)
import requests
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    login_required,
    current_user,
)
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db, logger, mail
from app.models import User, Book, CartItem, Checkout
from app.controller import signin_controller
from app.controller import signup_controller
from app.controller import send_email
from app import login_manager

home = Blueprint("main", __name__)
login_manager.login_view = "main.signin"


# Routes
@home.route("/signin", methods=["GET", "POST"])
def signin():
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            return signin_controller(email, password)

        return render_template("signin.html")
    except Exception as err:
        logger.exception(f"Something went wrong in signin_controller() {err}")
        return render_template_string("<b>Something went wrong!<b>")


@home.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        return signup_controller(username, email, password)

    return render_template("signup.html")


@home.route("/search", methods=["GET", "POST"])
@login_required
def search():
    books = []
    if request.method == "POST":
        search_term = request.form["search_term"]
        response = requests.get(
            f"https://www.googleapis.com/books/v1/volumes?q={search_term}&key={os.getenv('GOOGLE_BOOKS_API_KEY')}"
        )
        books = response.json().get("items", [])
    return render_template("search.html", books=books)


@app.route("/add_to_cart/<book_id>", methods=["GET", "POST"])
@login_required
def add_to_cart(book_id):
    try:
        response = requests.get(
            f"https://www.googleapis.com/books/v1/volumes/{book_id}?key={os.getenv('GOOGLE_BOOKS_API_KEY')}"
        )
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        book = response.json()

        volume_info = book.get("volumeInfo", {})
        id = book_id
        title = volume_info.get("title", "No Title")
        authors = ", ".join(volume_info.get("authors", ["No Authors"]))
        description = volume_info.get("description", "No Description")
        image = volume_info.get("imageLinks", {}).get("thumbnail")
        print("Image", image)
        # Save book information to the database
        new_book = Book(
            google_id=id,
            title=title,
            authors=authors,
            description=description,
            image=image,
        )
        db.session.add(new_book)
        db.session.commit()
        print("new book:", new_book)
        # Check if the book is already in the cart
        book = Book.query.filter_by(google_id=id).first()

        if book:
            # Check if the book is already in the user's cart
            existing_cart_item = CartItem.query.filter_by(
                user_id=current_user.id, book_id=book.id
            ).first()

            if not existing_cart_item:
                # Add the book to the cart
                new_cart_item = CartItem(user_id=current_user.id, book_id=book.id)
                db.session.add(new_cart_item)
                db.session.commit()
                print("Book added to cart")
            else:
                print("The book is already in the user's cart")
        else:
            print("Book not found")

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return redirect(url_for("cart"))


@app.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    print("cart items0", cart_items)

    found_books = []

    for books in cart_items:
        book = Book.query.filter_by(id=books.book_id).first()
        print(book)
        found_books.append(book)

    return render_template("cart.html", cart_item=found_books)


@home.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "POST":
        student_name = request.form.get("student_name")
        email = request.form.get("email")
        print("EMAIL RECEIVED", email)
        
        # Validate the email address
        if not email or "@" not in email or "." not in email:
            flash("Invalid email address", "error")
            return redirect(url_for('main.checkout'))
        
        # Save checkout information to the database
        checkout = Checkout(student_name=student_name, email=email)
        db.session.add(checkout)
        db.session.commit()
        
        # Retrieve user's cart items and corresponding book links
        get_user_cart = CartItem.query.filter_by(user_id=current_user.id).all()
        book_links = []
        for cart in get_user_cart:
            book = Book.query.filter_by(id=cart.book_id).first()
            book_links.append({
                "title": book.title,  # Assuming the Book model has a title attribute
                "url": f"https://books.google.com/books?id={book.google_id}"
            })
        
        # Send email with the book links
        send_email(student_name, email, book_links)
         # Flash a success message and redirect
        flash("Checkout completed and email sent successfully!", "success")
        return redirect(url_for('main.checkout'))
    
    # Render the checkout page for GET request
    return render_template("checkout.html")

@home.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@home.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    book_list = []
    print(book_list)
    count = len(cart_items)
    print(count)
    for books in cart_items:
        book = Book.query.filter_by(id=books.book_id).first()
        book_list.append(book)
    return render_template(
        "dashboard.html", current_user=current_user, items=book_list, count=count
    )
