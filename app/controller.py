from flask import flash, redirect, render_template_string, render_template
from flask_login import login_user
from app import db, logger, mail
from app.models import User
from flask_mail import Message


def signin_controller(email, password):
    try:
        user = User.query.filter_by(email=email).first()
        print(user)
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return redirect("/signin")
    except Exception as err:
        logger.exception(f"Something went wrong in signin_controller() {err}")
        return render_template_string("<b>Something went wrong!<b>")


def signup_controller(username, email, password, avatar_url):
    # Check if the email is already registered

    existing_username = User.query.filter_by(username=username).first()
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        flash("Email address already exists. Please use a different email.", "danger")
        return redirect("/signup")
    elif existing_username:
        flash("Username already exists. Please use a different name.", "danger")
        return redirect("/signup")
    else:
        # Create new user
        new_user = User(username=username, email=email, avatar=avatar_url)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

    flash("Account created successfully. Please log in.", "success")
    return redirect("/signin")


def send_email(student_name, email, book_links):
    msg = Message(
        "Your E-Books Are Ready - Norens Library",
        recipients=[email],  # Use the collected email address
    )

    msg.body = "Thank you for the purchased please find below all the links"
    msg.html = render_template(
        "email_template.html", student_name=student_name, links=book_links
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        return f"Failed to send email: {e}"
