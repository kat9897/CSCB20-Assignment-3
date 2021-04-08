import sqlite3
from flask import session, Flask, render_template, url_for, request, g, redirect, escape, current_app, send_file

DATABASE = "./assignment3.db"

# To run: python -m flask run

app = Flask(__name__)
app.secret_key = b'Assignment'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# one=True: dictionary
# one=False: list of dictionaries


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/')
def home():
    if 'userid' in session:
        return render_template("index.html", value=session['value'], usertype=session['usertype'])
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
        if session['usertype'] is not None:
            if session['usertype'] == "instructor":
                session['value'] = 2
            else:
                session['value'] = 1
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
                session['value'] = 1
                db.commit()
                cursor.close()
                db.close()
            else:
                cursor = db.cursor()
                cursor.execute("INSERT INTO Instructor('userid', 'username', 'email') VALUES (?,?,?)",
                               (session['userid'], session['username'], email))
                session['value'] = 2
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
        session['usertype'] = user['usertype']
        if session['usertype'] == 'instructor':
            session['username'] = query_db('select username from Instructor where userid=?', [
                                           session['userid']], one=True)['username']
            session['value'] = 2
        else:
            session['username'] = query_db('select username from Student where userid=?', [
                                           session['userid']], one=True)['username']
            session['value'] = 1
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
    session['value'] = 0
    session['usertype'] = ''
    return redirect(url_for('home'))


@app.route("/studentFeedback", methods=['GET', 'POST'])
def studentFeedback():
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()

    prof = query_db("select * from Instructor")

    if request.method == "POST":
        feedback = request.form
        question_num = 1

        prof = query_db("select * from Instructor where username=?",
                        [request.form['prof-person']], one=True)
        q1 = feedback['question1']
        q2 = feedback['question2']
        q3 = feedback['question3']
        q4 = feedback['question4']
        questions = [q1, q2, q3, q4]

        for i in range(4):
            cur.execute("insert into Feedback (questionNum, professorID, studentID, answer) values (?, ?, ?, ?)", [
                question_num,
                prof['userid'],
                session['userid'],
                questions[i]])
            question_num += 1
        cur.close()

    prof = query_db("select * from Instructor")
    db.commit()
    db.close()

    return render_template("student-feedback.html", value=session['value'], professors=prof)


@app.route("/marks", methods=["POST", "GET"])
def marks():
    db = get_db()
    db.row_factory = make_dicts
    student_id = session['userid']

    # List of dictionaries
    marks = query_db("select * from Marks where studentID=?", [student_id])

    for mark in marks:
        professor = query_db("select username from Instructor where userid=?", [
                             mark['professorID']], one=True)
        mark['username'] = professor['username']

    if request.form == "POST":
        cur = db.cursor()
        

    db.close()
    return render_template("marks.html", marks=marks, value=session['value'])


@app.route("/studentRemark", methods=["POST", "GET"])
def studentRemark():
    db = get_db()
    db.row_factory = make_dicts
    cur = db.cursor()
    feedback = request.form

    assignments = query_db("select * from Marks where studentID=?", [session['userid']])
    print(assignments)

    if (request.form == "POST"):
        prof = query_db("select * from Instructor where username=?",
            [request.form['prof-person']], one=True)

        for i in range(4):
        #cur.execute("insert into Feedback (questionNum, professorID, studentID, answer) values (?, ?, ?, ?)", [
        #    ,
        #    prof['userid'],
        #    session['userid'],
        #    questions[i]])
            cur.close()

    db.commit()
    db.close()

    return render_template("student-remark.html", marks=marks, value=session['value'])

# Links

@app.route("/assignments")
def assignments():
    return render_template("assignments.html", value=session['value'], usertype=session['usertype'])

@app.route("/calendar")
def calendar():
    return render_template("calendar.html", value=session['value'], usertype=session['usertype'])

@app.route("/syllabus")
def syllabus():
    return render_template("syllabus.html", value=session['value'], usertype=session['usertype'])

@app.route("/lectures")
def lectures():
    return render_template("lectures.html", value=session['value'], usertype=session['usertype'])

@app.route("/labs")
def labs():
    return render_template("labs.html", value=session['value'], usertype=session['usertype'])

@app.route("/tests")
def tests():
    return render_template("tests.html", value=session['value'], usertype=session['usertype'])

@app.route("/courseTeam")
def courseTeam():
    return render_template("courseTeam.html", value=session['value'], usertype=session['usertype'])

@app.route("/news")
def news():
    return render_template("news.html", value=session['value'], usertype=session['usertype'])

@app.route("/externalLinks")
def externalLinks():
    return render_template("externalLinks.html", value=session['value'], usertype=session['usertype'])

if __name__ == '__main__':
    app.run(debug=True)
