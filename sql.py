from webbrowser import register

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

from edit_database import cursor, connection

app = Flask(__name__)

app.config['SECRET_KEY'] = 'ddvfcb34g1234565gthy9867698j6980kihbgfc'

login_manager = LoginManager(app)
login_manager.login_view = 'register'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        print(password)
        print(self.password_hash)
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    user = cursor.execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None


@app.route("/")
def index():
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    # cursor.execute('SELECT * from post')
    cursor.execute('''SELECT post.id, post.title, post.CONTENT, post.author_id, user.username, 
                    COUNT(like.id) AS likes
                   FROM post
                   JOIN user ON post.author_id = user.id
                   LEFT JOIN like ON post.id = like.post_id
                   GROUP BY
                        post.id, post.title, post.CONTENT, post.author_id, user.username'''
                   )
    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        posts.append(
            {'id' : post[0],
             'title': post[1],
             'content' : post[2],
             'author_id' : post[3],
             'username' : post[4],
             'likes' : post[5]}
        )
        if current_user.is_authenticated:
            cursor.execute('SELECT post_id FROM like WHERE user_id = ?', (current_user.id,))
            likes_result = cursor.fetchall()
            liked_posts = []
            for like in likes_result:
                liked_posts.append(like[0])
            posts[-1]['liked_posts'] = liked_posts

    print(posts)
    context = {'posts' : posts}
    return render_template("blog112.html", **context)

def close_db(connection=None):
    if connection is not None:
        connection.close()

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        gmail = request.form['gmail']
        username = request.form['username']
        password = request.form['password']
        try:
            connection = sqlite3.connect('sqlite.db')
            cursor = connection.cursor()
            cursor.execute('INSERT INTO user (gmail, username, password_hash) VALUES (?, ?, ?)',
                           (gmail, username,  generate_password_hash(password))
            )
            connection.commit()
            print("Successful registration")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html',
                                   message='Account already exists')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print(1)
        username = request.form['username']
        gmail = request.form['gmail']
        password = request.form['password']
        print(username)
        connection = sqlite3.connect('sqlite.db')
        cursor = connection.cursor()
        user = cursor.execute(
            f'SELECT * FROM user WHERE username = "{username}"'
        ).fetchone()
        print(user)
        if user and User(user[0], user[1], user[3]).check_password(password):
            print(3)
            login_user(User(user[0], user[1], user[3]))
            print(4)
            return redirect(url_for('index'))
        else:
            print(5)
            return render_template('login.html', message='invalid username or password')
    return render_template('login.html')

@app.teardown_appcontext
def close_connection(exception):
    close_db()

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/delete/<int:post_id>", methods=['POST'])
@login_required
def delete_post(post_id):
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    post = cursor.execute('SELECT * FROM post WHERE id = ?',
                          (post_id,)).fetchone()
    print(current_user.id)
    if post and post[3] == current_user.id:
        cursor.execute('DELETE FROM post WHERE id = ?', (post_id,))
        connection.commit()
        return redirect(url_for('index'))
    else:
        print(1)
        return redirect(url_for('index'))


def user_is_liking(user_id, post_id):
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    like = cursor.execute(
        'SELECT * FROM like WHERE user_id=? AND post_id=?',
        (user_id, post_id)).fetchone()
    return bool(like)

@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    post = cursor.execute('SELECT * FROM post WHERE id = ?',
                          (post_id,)).fetchone()
    if post:
        if user_is_liking(current_user.id, post_id):
            cursor.execute(
                'DELETE FROM like WHERE user_id = ? AND post_id = ?',
                (current_user.id, post_id))
            connection.commit()
            print('Unliked post')
        else:
            cursor.execute(
                'INSERT INTO like (user_id, post_id) VALUES (?, ?)',
                (current_user.id, post_id))
            connection.commit()
            print('liked post')
        return redirect(url_for('index'))
    return "post not found", 404

@app.route("/add", methods=['GET', 'POST'])
@login_required
def add_post():
    print(request.method)
    if request.method == 'POST':
        print(request.form)
        title = request.form['title']
        content = request.form['content']
        connection = sqlite3.connect('sqlite.db')
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO post (title,content, author_id) VALUES (?, ?, ?)',
            (title, content, current_user.id)
        )
        connection.commit()
        return redirect(url_for('index'))
    return render_template('add_new.html')

@app.route('/post/<post_id>')
def post(post_id):
    connection = sqlite3.connect('sqlite.db')
    cursor = connection.cursor()
    print(post_id)
    result = cursor.execute(
        'select * FROM post WHERE id = ?', (post_id,)
    ).fetchone()
    print(result)
    post_dict = {"id": result[0], 'title': result[1], 'content': result[2]}
    return render_template('post.html', post=post_dict)

@app.route("/bye/")
def greet():
    return "BYE BYE!"

@app.route("/<name>/")
def name_greet(name):
    return f"Hi, {name.title()}"


if __name__ == "__main__":
    app.run()