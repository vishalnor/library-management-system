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
    jsonify,
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
from werkzeug.utils import secure_filename
from app import app, db, logger, mail
from app.models import User, Book, CartItem, Checkout
from app.controller import signin_controller
from app.controller import signup_controller
from app.controller import send_email
from app import login_manager
from app import cloudinary

home = Blueprint("main", __name__)

login_manager.login_view = "main.signin"
# Define the directory where uploaded files will be saved



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

    urls = [
        "https://api.dicebear.com/9.x/adventurer/svg?seed=Molly",
        "https://api.dicebear.com/9.x/adventurer/svg?seed=George",
        "https://api.dicebear.com/9.x/adventurer/svg?seed=Bubba",
        "https://api.dicebear.com/9.x/adventurer/svg?seed=Sassy",
        "https://api.dicebear.com/9.x/adventurer/svg?seed=Mittens",
        "https://api.dicebear.com/9.x/adventurer/svg?seed=Callie",
    ]

    print("URLS", urls)
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        avatar_url = request.form.get("avatar_url")
        if avatar_url == "":
            flash("Please select your avatar", 'danger')
            return redirect("/signup")
        else:
           signup_controller(username, email, password, avatar_url)
        #    return redirect("/signin")

    return render_template("signup.html", urls=urls)


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


@app.route("/add_to_cart/<book_id>", methods=["POST", "GET"])
@login_required
def add_to_cart(book_id):
    try:
        # Fetch book details from Google Books API
        response = requests.get(
            f"https://www.googleapis.com/books/v1/volumes/{book_id}?key={os.getenv('GOOGLE_BOOKS_API_KEY')}"
        )
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        book_data = response.json()

        volume_info = book_data.get("volumeInfo", {})
        title = volume_info.get("title", "No Title")
        authors = ", ".join(volume_info.get("authors", ["No Authors"]))
        description = volume_info.get("description", "No Description")
        image = volume_info.get("imageLinks", {}).get("thumbnail")
        print("Image", image)

        # Check if the book already exists in the database
        book = Book.query.filter_by(google_id=book_id).first()

        if not book:
            # If the book does not exist, create a new one
            book = Book(
                google_id=book_id,
                title=title,
                authors=authors,
                description=description,
                image=image,
            )
            db.session.add(book)
            db.session.commit()
            print("New book added to database:", book)
        else:
            print("Book already exists in the database:", book)

        # Check if the book is already in the user's cart
        existing_cart_item = CartItem.query.filter_by(
            user_id=current_user.id, book_id=book.id
        ).first()

        if not existing_cart_item:
            # If the book is not in the cart, add it
            new_cart_item = CartItem(user_id=current_user.id, book_id=book.id)
            db.session.add(new_cart_item)
            db.session.commit()
            flash("Book added to cart.", "success")
            print("Book added to cart")
        else:
            flash("The book is already in your cart.", "info")
            print("The book is already in the user's cart")

    except requests.exceptions.RequestException as e:
        flash(f"HTTP Request failed: {e}", "error")
        print(f"HTTP Request failed: {e}")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "error")
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
            return redirect(url_for("main.checkout"))

        # Save checkout information to the database
        checkout = Checkout(student_name=student_name, email=email)
        db.session.add(checkout)
        db.session.commit()

        # Retrieve user's cart items and corresponding book links
        get_user_cart = CartItem.query.filter_by(user_id=current_user.id).all()
        book_links = []
        for cart in get_user_cart:
            book = Book.query.filter_by(id=cart.book_id).first()
            book_links.append(
                {
                    "title": book.title,  # Assuming the Book model has a title attribute
                    "url": f"https://books.google.com/books?id={book.google_id}",
                }
            )

        # Send email with the book links
        send_email(student_name, email, book_links)
        # Flash a success message and redirect
        flash("Checkout completed and email sent successfully!", "success")
        return redirect(url_for("main.checkout"))

    # Render the checkout page for GET request
    return render_template("checkout.html")


@home.route("/remove_book/<book_id>", methods=["GET", "POST"])
@login_required
def remove_book(book_id):
    book = CartItem.query.filter_by(book_id=book_id).first()

    print(book)
    db.session.delete(book)
    db.session.commit()
    flash("Book Removed", "success")
    return redirect(url_for("cart"))


@home.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
        
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            file = request.files.get("avatar-input")
            upload_result = cloudinary.uploader.upload(file)
            url = upload_result.get("url")

            # Debugging: Print the form data to ensure it’s being captured
            print(f"Name: {name}, Email: {email}, Password: {password}, File: {url}")

            user = User.query.filter_by(id=current_user.id).first()

            if user:
                # Update user details
                user.username = name
                user.email = email

                if password:
                    user.password_hash = generate_password_hash(password)

                if file:
                    user.avatar = url
                    try:
                        result = cloudinary.uploader.upload(file)
                        print(result)
                    except Exception as e:
                        print(f"Cloudinary error: {e}")

                db.session.commit()  # Save the changes to the database
                flash("Profile updated successfully!", "success")
            else:
                flash("User not found!", "danger")

            return redirect(url_for("main.profile"))
    

        return render_template("profile.html", user=current_user)


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
