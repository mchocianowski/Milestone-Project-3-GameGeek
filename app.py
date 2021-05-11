import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/get_games")
def get_games():
    games = list(mongo.db.games.find())
    return render_template("games.html", games=games)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash(
                "Sorry this Username already exists please try using a different Username.")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Thankyou for registering with GameGeek!")
        return redirect(url_for("profiles", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profiles", username=session["user"]))
            else:
                flash(
                    "It seems that the Username or Password entered are incorrect, please try again.")
                return redirect(url_for("login"))

        else:
            flash(
                "It seems that the Username or Password entered are incorrect, please try again.")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profiles/<username>", methods=["GET", "POST"])
def profiles(username):
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    games = list(mongo.db.games.find())
    if session["user"]:
        return render_template("profiles.html", games=games, username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_review", methods=["GET", "POST"])
def add_review():
    if request.method == "POST":
        review = {
            "game_name": request.form.get("game_name"),
            "age_restriction": request.form.get("age_restriction"),
            "genre_name": request.form.get("genre_name"),
            "single_or_multiplayer": request.form.get("single_or_multiplayer"),
            "extra_comments": request.form.get("extra_comments"),
            "created_by": session["user"]
        }
        mongo.db.games.insert_one(review)
        flash("Review Successfully Submitted")
        return redirect(url_for("get_games"))

    ages = mongo.db.ages.find().sort("age_restriction", 1)
    genres = mongo.db.genres.find().sort("genre_name", 1)
    players = mongo.db.players.find().sort("single_or_multiplayer", 1)
    return render_template("add_review.html", genres=genres, ages=ages,
                           players=players)


@app.route("/edit_review/<game_id>", methods=["GET", "POST"])
def edit_review(game_id):
    if request.method == "POST":
        submit_review = {
            "game_name": request.form.get("game_name"),
            "age_restriction": request.form.get("age_restriction"),
            "genre_name": request.form.get("genre_name"),
            "single_or_multiplayer": request.form.get("single_or_multiplayer"),
            "extra_comments": request.form.get("extra_comments"),
            "created_by": session["user"]
        }
        mongo.db.games.update({"_id": ObjectId(game_id)}, submit_review)
        flash("Review Successfully Updated")

    game = mongo.db.games.find_one({"_id": ObjectId(game_id)})
    ages = mongo.db.ages.find().sort("age_restriction", 1)
    genres = mongo.db.genres.find().sort("genre_name", 1)
    players = mongo.db.players.find().sort("single_or_multiplayer", 1)
    return render_template("edit_review.html", game=game, genres=genres,
                           ages=ages, players=players)


@app.route("/delete_review/<game_id>")
def delete_review(game_id):
    mongo.db.games.remove({"_id": ObjectId(game_id)})
    flash("Your post has been removed.")
    return redirect(url_for("profiles", username=session["user"]))


@app.route("/all_user_reviews", methods=["GET", "POST"])
def all_user_reviews():
    games = list(mongo.db.games.find())
    return render_template("all_user_reviews.html", games=games)


@app.route("/delete_user_review/<game_id>")
def delete_user_review(game_id):
    mongo.db.games.remove({"_id": ObjectId(game_id)})
    flash("This review has been removed.")
    return redirect(url_for("all_user_reviews"))


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    games = list(mongo.db.games.find({"$text": {"$search": query}}))
    return render_template("games.html", games=games)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
