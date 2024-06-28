import os
from os.path import join, dirname
from dotenv import load_dotenv

from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from flask import (
    Flask, 
    render_template, 
    jsonify, 
    request, 
    redirect, 
    url_for,
)
from werkzeug.utils import secure_filename

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("mongodb+srv://amelia045:mongomell@cluster0.pjx2hyv.mongodb.net/")
DB_NAME =  os.environ.get("TUGAS10")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"

SECRET_KEY = "AMEL"

MONGODB_CONNECTION_STRING = "mongodb+srv://amelia045:mongomell@cluster0.pjx2hyv.mongodb.net/"

client = MongoClient(MONGODB_CONNECTION_STRING)

db = client.dbsparta_plus_week4

TOKEN_KEY = "mytoken"

@app.route("/", methods=["GET"])
def home():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        msg="Your token has expired"
        return redirect(url_for("login", msg=msg))
    except jwt.exceptions.DecodeError:
        msg="There was problem logging you in"
        return redirect(url_for("login", msg=msg))

@app.route("/login", methods=['GET'])
def login():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg)

@app.route("/user/<username>", methods=['GET'])
def user(username):
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        print('username',username)
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        status = username == payload.get["id"]  
        user_info = db.users.find_one(
            {"username": username}, 
            {"_id": False}
        )
        print('user_info',users_info)
        return render_template(
            "user.html", 
            user_info=user_info, 
            status=status
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/sign_in", methods=["POST"])
def sign_in():
    return jsonify({"result": "success"})

@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    return jsonify({"result": "success"})

@app.route("/sign_up/check_dup", methods=["POST"])
def check_dup():
    username_receive = request.form.get('username_give')
    user = db.users.find_one({'username' : username_receive})
    exists = bool (db.user.find_one({'username' : username_receive}))
    return jsonify({"result": "success", 'exists' : exists})

@app.route("/update_profile", methods=["POST"])
def save_img():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {"profile_name": name_receive, "profile_info": about_receive}
        if "file_give" in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/" + file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path

        db.users.update_one({"username": payload["id"]}, {"$set": new_doc})
        return jsonify({"result": "success", "msg": "Profile updated!"})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
    
@app.route("/posting", methods=["POST"])
def posting():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"]
        )
        return jsonify({
            "result": "success", 
            "msg": "Posting successfull"
        })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/get_posts", methods=["GET"])
def get_posts():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])

        username_receive = request.args.get("username_give")
        if username_receive == "":
            posts = list(db.posts.find({}).sort("date", -1).limit(20))
        else:
            posts = list(
                db.posts.find({"username": username_receive}).sort("date", -1).limit(20)
            )

        for post in posts:
            post["_id"] = str(post["_id"])
            post["count_heart"] = db.likes.count_documents(
                {"post_id": post["_id"], "type": "heart"}
            )
            post["heart_by_me"] = bool(
                db.likes.find_one(
                    {"post_id": post["_id"], "type": "heart", "username": payload["id"]}
                )
            )
            post["count_star"] = db.likes.count_documents(
                {"post_id": post["_id"], "type": "star"}
            )
            post['count_thumbsup'] = db.likes.count_documents({
                'post_id': post['_id'],
                'type' :'thumbsup',
            })
            post["star_by_me"] = bool(
                db.likes.find_one(
                    {"post_id": post["_id"], "type": "star", "username": payload["id"]}
                )
            )
            post["count_like"] = db.likes.count_documents(
                {"post_id": post["_id"], "type": "like"}
            )
            post["like_by_me"] = bool(
                db.likes.find_one(
                    {"post_id": post["_id"], "type": "like", "username": payload["id"]}
                )
            )
            post["thumbsup_by_me"] = bool(
                db.likes.find_one(
                    {"post_id": post["_id"], "type": "star", "username": payload["id"]}
                )
            )
        return jsonify(
            {
                "result": "success",
                "msg": "Successful fetched all posts",
                "posts": posts,
            }
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/update_like", methods=["POST"])
def update_like():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"
        ])
        user_info = db.users.find_one({"username": payload.get["id"]})
        post_id_receive = request.form.get["post_id_give"]
        comment_receive = request.form.get["type_give"]
        date_receive = request.form.get["action_give"]
        doc = {
            'post_id': post_id_receive,
            'username' : user_info.get('username'),
            'type' : type_receive,
        }
        if action_receive == 'like':
            db.likes.insert_one(doc)
        else:
            db.like.delete_one(doc)
        count = db.likes.count_documents({
            'post_id': post_id_receive,
            'type': type_receive
        })

        return jsonify({
            "result": "success", 
            "msg": "updated!",
            'count': 'count',
        })
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/about", methods=['GET'])
def about():
    return render_template("about.html")

@app.route("/secret")
def secret():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(
            token_receive, 
            SECRET_KEY, 
            algorithms=["HS256"])
        user_info = db.user.find_one({'username':payload.get('id')})
        return render_template("secret.html",user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

if __name__ == "__main__":
 app.run("0.0.0.0", port=5000, debug=True)

