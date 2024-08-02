from flask import flash, redirect, render_template_string
from flask_login import login_user
from app import db, logger
from app.models import User


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


def signup_controller(username, email, password):
    # Check if the email is already registered
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email address already exists. Please use a different email.", "danger")
        return redirect("/signup")

    # Create new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    flash("Account created successfully. Please log in.", "success")
    return redirect("/signin")
