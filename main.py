from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello():
    context = {
        "posts" : [
            {
            "title" : "Первый пост!",
            "content" : "text posta",
            "date" : "2024-11-20"
            },
            {
                "title": "Школа!",
                "content": "бим=бам=бом",
                "date": "2024-11-21"
            },
            {
            "title" : "Выходные",
            "content" : "Белка",
            "date": "2024-11-25"
            },
        ]
    }
    return render_template("blog112.html", **context)

@app.route("/bye/")
def greet():
    return "BYE BYE!"

@app.route("/alla/")
def alla_greet():
    return "HELLO ALLA"

@app.route("/andria/")
def tazo_greet():
    return "Hi Andria, shen yle xar"

@app.route("/<name>/")
def name_greet(name):
    return f"Hi, {name.title()}"


if __name__ == "__main__":
    app.run()