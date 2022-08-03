from flask import Flask, flash, render_template, request, redirect, url_for, session
from apscheduler.scheduler import Scheduler
import sqlite3 as sql
import atexit


app = Flask(__name__)
app.secret_key = "random string"

#encapsulation
class SearchCriteria:  
    def __init__(searchcriteria, location, time):  
        searchcriteria.location = location  
        searchcriteria.time = time

    def getLocation(searchcriteria):
        return searchcriteria.location

    def getTime(searchcriteria):
        return searchcriteria.time

class DatabaseInfo:
    def __init__(databaseinfo, databasename, connection, cursor):
        databaseinfo.name = databasename
        databaseinfo.connection = connection
        databaseinfo.cursor = cursor

    def getDatabaseName(databaseinfo):
        return databaseinfo.name

    def getDatabaseCursor(databaseinfo):
        return databaseinfo.cursor

    def getDatabaseConnection(databaseinfo):
        return databaseinfo.connection

#inheritance
class CourtReservation(SearchCriteria):
    def __init__(courtreservation, location, time, name, court):
        super().__init__(location, time)
        courtreservation.name = name
        courtreservation.court = court


@app.route("/login")
def login():
    
    conn = sql.connect("database.db")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisreservations (username TEXT, name TEXT, location TEXT, court TEXT, times TEXT, booked_court_index INTEGER, booked_time_index INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisquestions (useremail TEXT, usermessage TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisreviews (username TEXT, name TEXT, userreview TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (name TEXT,username TEXT, useremail TEXT, password TEXT)"
    )
    conn.close()
    
    return render_template("login.html")

@app.route("/afterlogin", methods=["POST", "GET"])
def check_user_credentials():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = request.form['username']
        password = request.form['password']
        #get database connection
        databaseconn = getdatabaseconn('database.db', True)
        cur = databaseconn.getDatabaseCursor();
        #searching for data in the database
        cur.execute(" SELECT * FROM users WHERE username  = ? and password= ? ", [username, password])
        rows = cur.fetchall()
        if len(rows) == 0:
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route("/createaccount")
def createaccount():
    return render_template("createaccount.html")

@app.route("/saveaccount", methods=["POST"])
def saveaccount():
    name = request.form['name']
    username = request.form['username']
    emailaddress  = request.form['emailaddress']
    password = request.form['password']
    databaseconn = getdatabaseconn('database.db', True);
    cur = databaseconn.getDatabaseCursor();
    conn = databaseconn.getDatabaseConnection();
    cur.execute("select * from users where username= ? or useremail= ?",[username, emailaddress])
    rows = cur.fetchall()
    if len(rows) != 0:
        error = 'Sorry, this username or email is already in use. Please enter a different username.'
    else:
        cur.execute("INSERT INTO users (name, username, useremail, password) VALUES (?, ?, ? ,?)",(name, username, emailaddress, password,))
        conn.commit()
        return render_template("login.html")
    return render_template("createaccount.html", error=error)
    

@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   return redirect(url_for('login'))

@app.route("/cancel")
def cancel_reservation():
    return render_template("cancel.html")

@app.route("/aftercancelling", methods=["POST", "GET"])
def after_cancelling():
    cancel_time = request.form.get('Available Times')
    cancel_court = request.form.get('Courts')
    if 'username' in session:
      username = session['username']
    cancel_location = request.form.get('Location')
    #get the selected values that make up the user's reservation that they want to cancel
    databaseconn = getdatabaseconn('database.db', True)
    cur = databaseconn.getDatabaseCursor()
    conn = databaseconn.getDatabaseConnection()
    cur.execute(" SELECT * FROM tennisreservations WHERE username  = ? and court= ?  and times = ? and location =? ", [username, cancel_court, cancel_time, cancel_location])
    rows = cur.fetchall()
    if len(rows) == 0:
        flash("We did not find a matching reservation. Please check the values you have selected.")
    else:
        #delete data from a database 
        cur.execute("DELETE FROM tennisreservations WHERE username  = ? and court= ? and times = ? and location = ?", [username, cancel_court, cancel_time, cancel_location])
        conn.commit()
        flash("You have successfully cancelled your reservation. Come to again to play!")
    return render_template("cancel.html")
    

@app.route("/")
def home():
    conn = sql.connect("database.db")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisreservations (username TEXT, name TEXT, location TEXT, court TEXT, times TEXT, booked_court_index INTEGER, booked_time_index INTEGER)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisquestions (useremail TEXT, usermessage TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tennisreviews (username TEXT, name, TEXT, userreview TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (name TEXT,username TEXT, useremail TEXT, password TEXT)"
    )
    conn.close()
    if 'username' in session:
      username = session['username']
      msg = ("You are logged in as:" + username)
      return render_template("home.html", msg=msg)
    
    return render_template("login.html") 
    


@app.route("/enternew")
def new_reservation():
    return render_template("reservation.html")


@app.route("/createreview")
def create_review():
    return render_template("createreview.html")

@app.route("/viewreviews")
def view_reviews():
    databaseconn = getdatabaseconn('database.db', True);
    cur = databaseconn.getDatabaseCursor()
    cur.execute(
        "select name, userreview from tennisreviews"
    )
    rows = cur.fetchall()
    return render_template("viewreviews.html", rows=rows)

@app.route('/savereviews', methods = ["POST"])
def save_reviews():
    if request.method == "POST":
        if 'username' in session:
          username = session['username']
        user_review = request.form["theuserreview"]
        databaseconn = getdatabaseconn('database.db', True);
        conn = databaseconn.getDatabaseConnection()
        cur = databaseconn.getDatabaseCursor()
        cur.execute("select name from users where username= ?",[username])
        userrows = cur.fetchall()
        for userrow in userrows:
            name = userrow["name"]
        #insert data into the database 
        cur.execute(
            "INSERT INTO tennisreviews (username, name, userreview) VALUES (?, ?, ?)",
            (username, name, user_review,)
        )
        conn.commit()
        flash(
            "Thank you for submitting your review! Enjoy the app.")
        return render_template("createreview.html")



@app.route("/savequestions", methods=["POST"])
def save_questions():
    if request.method == "POST":
        emailaddr = request.form["email"]
        usermessage = request.form["message"]
        #polymorphism
        databaseconn = getdatabaseconn('database.db');
        conn = databaseconn.getDatabaseConnection()
        cur = databaseconn.getDatabaseCursor()
        cur.execute(
            "INSERT INTO tennisquestions (useremail,usermessage) VALUES (?,?)",
            (emailaddr, usermessage),
        )
        conn.commit()
        flash(
            "Thank you for submitting your question. We will get back to you shortly!"
        )
        return render_template("help.html")


@app.route("/register", methods=["POST", "GET"])
def addrec():
    if request.method == "POST":
        try:
            select = request.form.get("timeslist")
            selected_value_times = str(select)  # just to see what select is
            #lists
            times = ["9-11AM", "11-1PM", "1-3PM", "3-5PM", "5-7PM", "7-9PM"]
            locations = ["Dougherty Valley High School", "Central Park"]
            selected_location = str(request.form.get("locationlist"))
            time_index = str(times.index(selected_value_times))
            # now do the same but with the courts
            select_courts = request.form.get("courts")
            selected_value_courts = str(select_courts)  # just to see what select is
            courts = [
                "Court 1",
                "Court 2",
                "Court 3",
                "Court 4",
                "Court 5",
                "Court 6",
                "Court 7",
                "Court 8",
            ]
            court_index = str(courts.index(selected_value_courts))

            
            if 'username' in session:
                username = session['username']

            databaseconn = getdatabaseconn('database.db', True);
            con = databaseconn.getDatabaseConnection()
            cur = databaseconn.getDatabaseCursor()

            #check if the name already exists in the DB   
            cur.execute("select * from tennisreservations where username= ?",[username])
            rows = cur.fetchall()
                
            if len(rows) != 0:
                msg = ("Sorry, you already have a court reserved. You cannot reserve more than one court.")
            else:
                cur.execute("select name from users where username= ?",[username])
                userrows = cur.fetchall()
                for userrow in userrows:
                    name = userrow["name"]
                reservation = CourtReservation(selected_location, selected_value_times, name, selected_value_courts)
                cur.execute(
                    "INSERT INTO tennisreservations (username, name, location, court,times,booked_court_index, booked_time_index) VALUES (?, ?,?,?,?,?, ?)",
                    (
                    username,
                    reservation.name,
                    reservation.location,
                    reservation.court,
                    reservation.time,
                    court_index,
                    time_index,
                    ),)
                con.commit()
                    
                msg = (
                     "Hi "
                     + name
                     + "! You have successfully reserved "
                      + selected_value_courts
                      + " at time "
                      + selected_value_times
                      + "."
                )
        except:
           con.rollback()
           msg = "error in insert operation"
        finally:
            return render_template("result.html", msg=msg)
            con.close()


@app.route("/list")
def list():
    databaseconn = getdatabaseconn('database.db', True);
    conn = databaseconn.getDatabaseConnection()
    cur = databaseconn.getDatabaseCursor()
    cur.execute(
        "select name, location, court, times, booked_time_index, booked_court_index from tennisreservations"
    )
    rows = cur.fetchall()
    return render_template("list.html", rows=rows)


@app.route("/search", methods=["GET", "POST"])
def search():
    location = str(request.form.get("Location"))
    select = request.form.get("Available Times")
    # create the search criteria object
    selected_value_times = str(select)  # just to see what select is
    #encapsulation: created an object of SearchCriteria 
    courtSearchCriteria = SearchCriteria(location, selected_value_times)
    times = ["9-11AM", "11-1PM", "1-3PM", "3-5PM", "5-7PM", "7-9PM"]
    locations = ["Dougherty Valley High School", "Central Park"]
    time_index = str(times.index(selected_value_times))
    #polymorphism for getdatabaseconn method
    databaseconn = getdatabaseconn('database.db', True);
    conn = databaseconn.getDatabaseConnection()
    cur = databaseconn.getDatabaseCursor()
    cur.execute(
        "select booked_court_index from tennisreservations where booked_time_index=? and location=?",
        [time_index, location],
    )
    rows = cur.fetchall()

    times = ["9-11AM", "11-1PM", "1-3PM", "3-5PM", "5-7PM", "7-9PM"]
    courtForTime0list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    courtForTime1list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    courtForTime2list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    courtForTime3list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    courtForTime4list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    courtForTime5list = [
        "Court 1",
        "Court 2",
        "Court 3",
        "Court 4",
        "Court 5",
        "Court 6",
        "Court 7",
        "Court 8",
    ]
    #listoflists
    courtTimeMasterList = []
    courtTimeMasterList.append(courtForTime0list)
    courtTimeMasterList.append(courtForTime1list)
    courtTimeMasterList.append(courtForTime2list)
    courtTimeMasterList.append(courtForTime3list)
    courtTimeMasterList.append(courtForTime4list)
    courtTimeMasterList.append(courtForTime5list)

    list_courts_to_be_removed = []
    list_of_available_courts = []
    courtList = courtTimeMasterList[int(time_index)]

    updatedcourtlist = []

    #searching for data in a list of the court that has just been booked because this will be removed since it has already been reserved 
    for dbrow in rows:
        court_index = dbrow["booked_court_index"]
        list_courts_to_be_removed.append(court_index)

    for index in range(len(courtList)):
        if index in list_courts_to_be_removed:
            continue
        list_of_available_courts.append(courtList[index])
    if (len(list_of_available_courts)) == 0:
        return render_template("choosedifftime.html", state=selected_value_times)

    return render_template(
        "availablecourtsandname.html",
        courtSearchCriteria=courtSearchCriteria,
        courts=list_of_available_courts,
        #state=selected_value_times,
        #selected_location=location,
        timeslist=times,
        locationlist=locations,
    )

#polymorphism show this one 
def getdatabaseconn(dbname, isselect=False): 
        if isselect:
            con = sql.connect(dbname)
            con.row_factory = sql.Row
            cur = con.cursor()
            dbconnection = DatabaseInfo(dbname, con, cur)
        else:
            con = sql.connect("database.db")
            cur = con.cursor()
            dbconnection = DatabaseInfo(dbname, con, cur)
        return dbconnection 

#cron scheduler
cron = Scheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()

@cron.interval_schedule(hours=24)
def clear_database():
    conn = sql.connect("database.db")
    cur = conn.cursor()
    cur.execute(
            "DELETE FROM tennisreservations")
    conn.commit()
    print("Deleted reservations")

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: cron.shutdown(wait=False))


if __name__ == "__main__":
    app.run(debug=True)

