from flask import Flask, request, render_template
from database import DatabaseConnection
import email_service
import hashlib
import random
import string
import bcrypt
import time
import json
import re
from email.utils import parseaddr
from validate_email import validate_email

app = Flask(__name__)
DB = DatabaseConnection()
HOST = "localhost"
EMAIL_SERVICE = email_service.get_email_service()


def is_email_valid(email):
    regex = "^[\w\.]+@([\w-]+\.)+[\w-]{2,4}$"
    return re.search(regex, email)


def hasNumbers(inputString):
    return bool(re.search(r'\d', inputString))


def validate_password(password):
    return len(password) > 8 and len(password) < 50 and hasNumbers(password)


def generate_link():
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    length = 200
    return ''.join(random.choice(chars) for _ in range(length))


def send_email(user_email, link):
    link_to_send = f"http://{HOST}:3000/validation/user?validate={link}"
    subject = "Application email validation"
    text = "Follow the link in order to validate your account. " + link_to_send
    message = 'Subject: {}\n\n{}'.format(subject, text)
    EMAIL_SERVICE.sendmail("application@gmail.com", user_email, message)


def is_link_valid(user):
    return user["link_expires"] > time.time()


def get_hashed_password(plain_text_password):
    return bcrypt.hashpw(plain_text_password.encode("utf-8"), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(plain_text_password, hashed_password)


@app.route('/', methods=["GET"])
def main():
    return render_template('signup.html')


@app.route('/validation/user', methods=["GET"])
def verify_email():
    link = request.args.get("validate")
    query = {"verification_link": link, "verified": False}
    user = DB.get_user(query)

    if not user:
        return json.dumps({"msg": "Invalid link"}), 400

    new_user = {
        "username": user["username"],
        "password": user["password"],
        "email": user["email"],
        "history": user["history"],
    }

    if is_link_valid(user):
        new_user["verified"] = True
        DB.update_user(user, new_user)
        return "Success", 200


    else:
        link = generate_link()
        send_email(user["email"], link)
        new_user["verified"] = False
        new_user["verification_link"] = link
        new_user["link_expires"] = time.time() + 15

        DB.update_user(user, new_user)

        return "The link expired. We resent a new one.", 200


@app.route('/user', methods=["POST"])
def sign_up():
    try:
        user = request.get_json()
        user_db = DB.get_user({"username": user["username"]})
        if user_db:
            return json.dumps({"msg": "User already exists"}), 400

        if not is_email_valid(user["email"]):
            return json.dumps({"msg": "Email not valid"}), 400

        if len(user["username"]) < 5 or not validate_password(user["password"]):
            return json.dumps({"msg": "Invalid credentials"}), 400

        hashed = get_hashed_password(user["password"])
        user["password"] = hashed
        email_verification_link = generate_link()
        send_email(user["email"], email_verification_link)

        user["verified"] = False
        user["verification_link"] = email_verification_link
        user["link_expires"] = time.time() + 15
        user["history"] = []
        DB.create_user(user)

        return json.dumps({
                              "msg": "An email was sent to your email. Please validate your account in order to continue. The link expires in 15 seconds."}), 201
    except Exception as e:
        return json.dumps({"msg": "Something went wrong."}), 400


@app.route('/auth', methods=["POST"])
def auth():
    req = request.get_json()
    username = req["username"]
    password = req["password"]
    user = DB.get_user({"username": username})

    if not user:
        return json.dumps({"msg": "No such user"}), 400
    elif not user["verified"]:
        return json.dumps({"msg": "User not verified"}), 400
    elif not check_password(req["password"], user["password"].encode("utf-8")):
        return json.dumps({"msg": "Incorrect credentials"}), 400
    else:
        return json.dumps({"msg": "Succes"}), 200


if __name__ == '__main__':
    app.run(port=3000)
