#Week 13 Assignment ­ Web Development with Flask (2/2)
#import required libraries:
from flask import Flask, g, redirect, render_template, request, session
import os
import sqlite3 as lite

#Part I ­ Database Setup and Initialization
DATABASE = './hw13.db' #connecting the database
DEBUG = False
SECRET_KEY = os.urandom(24)
message = ''

app = Flask(__name__)
app.config.from_object(__name__)

def connect_to_database():
    global message
    try:
        return lite.connect(app.config['DATABASE']) #here we try to return the object
    except:
        message = 'Error! Unable to connect to database'

#route connecting app to database
@app.before_request
def before_request():

    g.user = None #set the "g" user object to none

    if 'user' in session:
        g.user = session['user']

    # set Flask g db to database
    g.db = connect_to_database() #set flask "g.db" to database

#route to close db connection
@app.teardown_request
def teardown_request(exception):

    db = getattr(g, 'db', None)

    if db is not None:
        db.close()

#route to display index page and login box
@app.route('/')
def index():
    return render_template('index.html', message = message)

#Part II ­ Teacher Login

#route to manage user login when entering credentials
@app.route('/login', methods=['POST'])
def login():

    global message

    if 'user' in session:
        return redirect('/')

    else:
        # get credentials entered by user
        username = request.form['username']
        password = request.form['password']

        try:
            cur = g.db.execute("SELECT password FROM users WHERE username = '{}'".format(username))
            pwd = cur.fetchone()
        except:
            message = 'There was an issue retrieving the details from the database.'
            return redirect('/')

        try:
            if password == pwd[0]:
                session['user'] = username
                message = ''
                return redirect('/dashboard')  #should redirect to ‘/dashboard’ route, which we will develop later, if the username and password credentials are correct
            else:
                message = 'Incorrect Username and Pasword Combination.'
        except:
            message = 'Unable to login. Please try again.'
        
        return redirect('/') #should redirect back to the ‘/login’ route, with an error message, when the credentials are incorrect


#Part III Dashboard: View students and quizzes in the class

#route for dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    global message

    # if a session is already open
    if 'user' in session:
       #try to query database for students and quizzes and navigate to dashboard
        try:
            cur = g.db.execute("SELECT * FROM students")
            student_data = cur.fetchall()

            cur = g.db.execute("SELECT * FROM quizzes")
            quiz_data = cur.fetchall()

            return render_template('dashboard.html', student_data=student_data, quiz_data=quiz_data, message=message )
        except:
            message = 'There was an issue retrieving the details from the database.'
    
    else:
        message = 'No user logged in!'
        return redirect("/")

#route to show student creation page
@app.route('/student', methods=['GET','POST'])
def student_form():

    global message
    
    if 'user' in session:
        return render_template('add_student.html', message = message)
    else:
        return redirect('/')

#route to show quiz creation page
@app.route('/quiz', methods=['GET','POST'])
def quiz_form ():

    global message
    
    if 'user' in session:
        return render_template('add_quiz.html', message = message)
    else:
        return redirect('/')

#route to show results submission page
@app.route('/results', methods=['GET','POST'])
def results_form ():

    global message
    
    if 'user' in session:
        try:
            cur = g.db.execute("SELECT student_id, first_name, last_name FROM students ORDER BY first_name")
            students = cur.fetchall()

            cur = g.db.execute("SELECT quiz_id, subject FROM quizzes ORDER BY quiz_id")
            quizzes = cur.fetchall()
        except:
            message = 'There was an issue retrieving the data from the database.'

        return render_template('add_results.html', message = message, students=students, quizzes=quizzes)
    
    else:
        return redirect('/')

#Part IV ­ Add students to the class

#route to add a new student
@app.route('/student/add', methods=['POST'])
def student_add():
    
    global message

    if 'user' in session:
        #Accepts the HTML form and attempts to add a new student to the database with the given form information.
        first = request.form['first']
        last = request.form['last']

        #verify that student details were entered
        if first != '' and last != '':
            try:              
                cur = g.db.execute("SELECT * FROM students WHERE first_name = '{}' and last_name = '{}'".format(first, last))
                count = len(cur.fetchall())
                #if count is more than 0, they exist
                if count > 0:
                    message = 'Student "{} {}" Already Exists!'.format(first, last)
                    return redirect('/student')
                else:
                    cur = g.db.execute("INSERT INTO students (first_name, last_name) VALUES (?, ?)", (first, last))
                    g.db.commit()
                    message = 'Student Added Successfully'
                    return redirect('/dashboard') #Upon success, redirect back to the ‘/dashboard’ route
            except:
                #update message
                message = 'There was an issue retrieving the data from the database.'
                return redirect('/dashboard') #If there is a failure, return the same HTML form with an error message.

        else:
            message = 'One or more fields were left blank. Please check and try again.'
            return redirect('/student')

#Part V ­ Add Quizzes to the Class

#route to add a new quiz
@app.route('/quiz/add', methods=['POST'])
def quiz_add():
    
    global message

    if 'user' in session:

        #get input from the HTML form
        subject = request.form['subject']
        questions = request.form['questions']
        date = request.form['date']

        #verify to check information is entered
        if subject != '' and questions != '' and date != '':

            try: 
                cur = g.db.execute("SELECT * FROM quizzes WHERE subject = '{}' and num_of_questions = '{}' and quiz_date = '{}'".format(subject, questions, date))
                count = len(cur.fetchall())

                #if count is more than 0, quiz exist so redirect back to quiz creation
                if count > 0:
                    message = 'Quiz Details Already Exist!'
                    return redirect('/quiz')
                else:
                    cur = g.db.execute("INSERT INTO quizzes (subject, num_of_questions, quiz_date) VALUES (?, ?, ?)", (subject, questions, date))
                    g.db.commit()
                    message = 'Quiz Added Successfully'
                    return redirect('/dashboard')
            except:
                message = 'There was an issue updating the database.'
                return redirect('/dashboard')
        else:
            message = 'One or more fields were left blank. Please check and try again.'
            return redirect('/quiz')

#Part VII ­ Add a Student’s Quiz Result

#route to add a quiz result
@app.route('/results/add', methods=['GET','POST'])
def results_add():
    
    global message

    if 'user' in session:
    
        #verify to check information is entered
        student = request.form['student']
        quiz = request.form['quiz']
        score = request.form['score']

        # verify that check details were entered on form
        if student != 'Select Student' and quiz != 'Select Quiz' and score != '':

            try:
                g.db.execute("INSERT INTO results (student_id, quiz_id, score) VALUES (?, ?, ?)", (student, quiz, score))
                g.db.commit()
                message = 'Quiz Result Added Successfully'
                return redirect('/dashboard')
            except:
                message = 'There was an issue updating the database.'
                return redirect('/dashboard')
        
        # if details were blank
        else:
            message = 'One or more fields were left blank. Please check and try again.'
            return redirect('/add_quiz')

#Part VI ­ View Quiz Results

@app.route('/student/<id>')
def get_students(id):

    global message

    if 'user' in session:
    
        #query database to look for password for username
        try:
            cur = g.db.execute("SELECT students.first_name, students.last_name,\
                quizzes.quiz_id, quizzes.subject, quizzes.quiz_date, results.score\
                FROM students\
                LEFT JOIN results\
                ON results.student_id  = students.student_id\
                LEFT JOIN quizzes\
                ON results.quiz_id = quizzes.quiz_id\
                WHERE students.student_id = {};".format(id))         
                
            results_data = cur.fetchall()

            count = len(results_data)
            # if more than 1 row
            if count > 0:
                message = ''
                return render_template('results.html', message=message, results_data=results_data)
            else:
                message = 'No quiz results found for Student Id {}'. format(id)
                return render_template('results.html', message=message, results_data=results_data)
        except:
            message = 'There was an issue retrieving the details from the database.'
            return redirect('/dashboard')
    else:
        message = 'No user logged in!'
        return redirect("/")

#route to log out user from session
@app.route('/logout')
def logout():

    global message

    session.pop('user', None)
    message = 'Logout Successful.'
    return redirect("/")

if __name__ == '__main__':
    app.run()

#end of the code!