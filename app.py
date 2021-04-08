import sqlite3
from flask import session, Flask, render_template, url_for, request, g, redirect, escape

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
    if 'userid' in session and 'usertype' in session:
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
        db.close()
    else:
        db.close()
        return render_template("signin.html", value=0)

    # check which type of user
    if user is not None:
        session['usertype'] = user['usertype']
        if session['usertype'] == 'instructor':
            session['value'] = 2
        else:
            session['value'] = 1
        return redirect(url_for('home'))
    else:
        session.clear()
        return render_template("signin.html", value=0, error="Wrong User ID or password.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/studentFeedback", methods=['GET', 'POST'])
def studentFeedback():
    db = get_db()
    db.row_factory = make_dicts
    cursor = db.cursor()

    prof = query_db("select * from Instructor")
    
    if request.method == "POST":
        feedback = request.form
        prof = query_db("select * from Instructor where username=?", [feedback['professor']], one=True) 

        question_num = 1
        for question in feedback:
            cursor.execute("insert into Feedback (questionNum, professorID, studentID, answer) values (?, ?, ?, ?)", 
            [question_num, prof['userid'], session['userid'], question])
            question_num += 1
        
        db.commit()
        db.close()
        cursor.close()
    
    return render_template("student-feedback.html", value=session['value'], professors=prof)

@app.route("/marks")
def marks():
    db = get_db()
    db.row_factory = make_dicts
    student_id = session['userid']

    # List of dictionaries
    marks = query_db("select * from Marks where studentID=?", [student_id])
    
    print(marks)

    db.close()
    return render_template("marks.html", marks=marks, value=session['value'])


### INSTRUCTORS ###
@app.route("/assessments")
def assessments():
    db = get_db()
    db.row_factory = make_dicts

    # fetch data from database
    tests = query_db('SELECT * FROM Assessment') # list of dictionaries
    db.close()

    return render_template("assessments.html", tests = tests)

@app.route("/classMarks/<testID>")
def classMarks(testID):
    db = get_db()
    db.row_factory = make_dicts

    #fetch grades for testID = test['testID']
    marks = query_db('SELECT testID, studentID, username, mark\
                        FROM Marks\
                        INNER JOIN Student ON studentID = userid\
                        WHERE testID = ?', testID) 
    test = query_db('SELECT * FROM Assessment WHERE testID = ?', testID, one = True)
    db.close()

    return render_template("classMarks.html", marks = marks, test = test)

@app.route("/editMark")
def editMark():
    db = get_db()
    db.row_factory = make_dicts
    db.close()

    return None


@app.route('/remark')
def remark():
    db = get_db()
    db.row_factory = make_dicts

    #fetch regrade requests for instructor = current instructor in session
    #instructorID = session['userid']
    requests = query_db("SELECT studentID, username, testName, message \
            FROM Remark \
            INNER JOIN Assessment ON Remark.testID = Assessment.testID\
            INNER JOIN Student ON studentID = userid\
            WHERE instructorID = ?", (session['userid'],)) 
    db.close()

    return render_template("remark.html", requests = requests)

@app.route('/feedback')
def feedback():
    return None

if __name__ == '_main_':
    app.run(debug=True)