from typing import List, Tuple, Optional

from bcrypt import hashpw, checkpw, gensalt
from flask import Flask, render_template, request, session, url_for, redirect

app = Flask(__name__)
app.secret_key = "0i9asdufzvßy9s8dzfßüa089sfß9a8"

user_id_field: str = "userId"

users: List[Tuple[str, str]] = [("test", "$2b$12$MN/nWaRWwHUsFxrA4lMGzO2mCxDvSZarO2.x6tth8IChiNlbs39IG")]


@app.route("/")
def route_index():
    if user_id_field not in session:
        return redirect(url_for("route_login"))

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def route_register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username: Optional[str] = request.form.get("username")
        password: Optional[str] = request.form.get("password")
        password_repeat: Optional[str] = request.form.get("passwordRepeat")

        if username is None or password is None or password != password_repeat:
            return render_template(
                "register.html",
                username=username,
                password=password,
                password_repeat=password_repeat,
            )

        pw_hash: str = hashpw(password.encode(), gensalt()).decode()

        users.append((username, pw_hash))

        return redirect(url_for("route_login"))


@app.route("/login", methods=["GET", "POST"])
def route_login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username: Optional[str] = request.form.get("username")
        password: Optional[str] = request.form.get("password")

        if username is None or password is None:
            return render_template("login.html", username=username, password=password)

        pw_hash: Optional[str] = next(u[1] for u in users if u[0] == username)

        if pw_hash is None or not checkpw(password.encode(), pw_hash.encode()):
            return render_template("login.html", username=username, password=password)

        session[user_id_field] = username
        return redirect(url_for("route_index"))


@app.route("/logout")
def route_logout():
    session.clear()
    return redirect(url_for("route_login"))


if __name__ == "__main__":
    app.debug = True
    app.run()
