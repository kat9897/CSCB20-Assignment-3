import sqlite3
from flask import session, Flask, render_template, url_for, request, g, redirect, escape

DATABASE = "./assignment3.db"

# To run: python -m flask run

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
    if 'userid' in session:
        if session['usertype'] == 'instructor':
            return render_template("index.html", value=2, usertype=session['usertype'])
        else:
            return render_template("index.html", value=1, usertype=session['usertype'])
    else:
        return render_template("index.html", value=0)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    db = get_db()
    db.row_factory = make_dicts
    if request.method == 'POST':
        session['userid'] = request.form.get('userid', type=int)
        session['password'] = request.form['password']
        session['usertype'] = request.form['usertype']
        session['username'] = request.form['username']
        user = query_db('select * from User where userid=?',
                        (session['userid'],), one=True)

        correct_userid_length = False
        if session['userid'] is not None:
            if session['userid'] >= 1000000000 and session['userid'] <= 9999999999:
                correct_userid_length = True

        correct_password_length = False
        if len(session['password']) == 8:
            correct_password_length = True

        correct_type = False
        if session['usertype'] == "student" or session['usertype'] == "instructor":
            correct_type = True

        if user is None and correct_type and correct_password_length and correct_userid_length:
            email = ""+str(session['userid'])+"@mail.utoronto.ca"
            cursor = db.cursor()
            cursor.execute("INSERT INTO User ('userid', 'usertype', 'password') VALUES (?,?,?)",
                           (session['userid'], session['usertype'], session['password']))
            db.commit()
            cursor.close()
            if session['usertype'] == "student":
                cursor = db.cursor()
                cursor.execute("INSERT INTO Student ('userid', 'username', 'email') VALUES (?,?,?)",
                               (session['userid'], session['username'], email))
                db.commit()
                cursor.close()
                db.close()
            else:
                cursor = db.cursor()
                cursor.execute("INSERT INTO Instructor('userid', 'username', 'email') VALUES (?,?,?)",
                               (session['userid'], session['username'], email))
                db.commit()
                cursor.close()
                db.close()
            return redirect(url_for('home'))
        else:
            session.clear()
            db.close()
            errorMessage = ""
            if user is not None:
                errorMessage = errorMessage+"Account already exists.\n"
            elif 'userid' not in session:
                errorMessage = errorMessage+"UserID should be a 10 digit number.\n"
            if not correct_password_length:
                errorMessage = errorMessage + \
                    "Invalid password length. The password length should be 8.\n"
            if not correct_type:
                errorMessage = errorMessage+"Invalid user type. Please enter student or instructor\n"

            return render_template("signup.html", value=0,
                                   error=errorMessage)
    else:
        db.close()
        return render_template("signup.html", value=0, error="")


@app.route("/signin", methods=['GET', 'POST'])
def signin():
    db = get_db()
    db.row_factory = make_dicts
    user = None
    if request.method == 'POST':
        session['userid'] = request.form['userid']
        session['password'] = request.form['password']
        user = query_db('select * from User where userid=? AND password=?',
                        (session['userid'], session['password']), one=True)
        session['usertype'] = user[1]
        db.close()
    else:
        db.close()
        return render_template("signin.html", value=0)
    if user is not None:
        db.close()
        return redirect(url_for('home'))
    else:
        session.clear()
        return render_template("signin.html", value=0, error="Wrong User ID or password.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '_main_':
    app.run(debug=True)