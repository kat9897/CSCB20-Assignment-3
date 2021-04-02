import sqlite3
from flask import session, Flask, render_template, url_for, request, g, redirect, escape

DATABASE = "./assignment3.db"


app = Flask(__name__)
app.secret_key = b'Assignment'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g.database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/')
def home():
    return render_template("index.html")


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    db = get_db()
    db.row_factory = make_dicts
    users = []
    for user in query_db('select * from User'):
        users.append(user)
    user = None
    if request.method == 'POST':
        session['userid'] = request.form['userid']
        session['password'] = request.form['password']
        user = query_db('select * from User where userid=? AND password=?',
                        (session['userid'], session['password']), one=True)
        db.close()
    else:
        db.close()
        return render_template("signin.html")
    if user is not None:
        return redirect(url_for('home'))
    else:
        session.clear()
        return render_template("signin.html")


if __name__ == '_main_':
    app.run(debug=True)
