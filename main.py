from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import sqlite3
import random
import string
from redis import Redis
import hashlib

app = Flask(__name__)

SESSION_TYPE = 'redis'
SESSION_REDIS = Redis(host='localhost', port=6379)
app.config.from_object(__name__)
Session(app)

length = 8
random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to initialize the database and create the tasks table if it doesn't exist
def init_db():
    conn = sqlite3.connect("tasks.db")  # Connect to the SQLite database
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        task TEXT,
                        priority TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT, 
                    password TEXT,
                    email TEXT)''')
    conn.commit()  # Save changes
    conn.close()  # Close database connection

# Function to retrieve all tasks from the database
def get_tasks():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, task, priority 
        FROM tasks
        ORDER BY 
            CASE 
                WHEN priority = 'High' THEN 1
                WHEN priority = 'Medium' THEN 2
                WHEN priority = 'Low' THEN 3
                ELSE 4
            END
    """)  # Order tasks by priority: High -> Medium -> Low
    tasks = cursor.fetchall()  # Fetch tasks with priority
    conn.close()
    return tasks

@app.route("/complete_task", methods=["POST"])
def complete_task():
    task_id = request.form.get("task_id")  # Get the task ID from the form
    if task_id:
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))  # Delete the task by ID
        conn.commit()
        conn.close()
    return redirect("/")  # Redirect back to the homepage


# Route for displaying the homepage with all stored tasks
@app.route("/", methods=["GET"])
def index():
    tasks = get_tasks()  # Fetch all tasks from the database
    return render_template("index.html", tasks=tasks, random_string = random_string)  # Render the HTML page with tasks

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login_user", methods=["POST"])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    password_hashed = password
    #hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect("tasks.db")  # Connect to the database
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users where username = ? and password = ?", (username, password_hashed))
    output = cursor.fetchone()
    
    if output == None:
        print("User password combination not found")
        return redirect("/login")

    user = output[1]
    password = output[2]
    conn.commit()  # Save changes
    conn.close()  # Close connection



    if user == None or password == None:
        print("User not found")
        return redirect("/login")
    elif password == password_hashed:
        #session["logged_in"] = True
        return redirect("/")

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form.get("username")
    password = request.form.get("password")

    password_hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users where username = ? and password = ?", (username, password_hashed))

    if cursor.fetchone() is not None:
        return redirect("/register")
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hashed))
    conn.commit()
    conn.close()
    return redirect("/login")

# Route to handle task submissions
@app.route("/add_task", methods=["POST"])
def add_task_route():
    task = request.form.get("task")  # Get task input from the form
    priority = request.form.get("priority")
    if task:  # Ensure the task is not empty
        add_task(task, priority)  # Add task to the database
    else:
        print("ERROR: TASK IS EMPTY")
    return redirect("/")  # Redirect back to homepage after adding the task

# Function to add a task to the database
def add_task(task, priority):
    print("Locking in")
    print(task)
    conn = sqlite3.connect("tasks.db")  # Connect to the database
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task, priority) VALUES (?, ?)", (task, priority))  # Insert task into table
    conn.commit()  # Save changes
    conn.close()  # Close connection

@app.route("/delete_all_tasks", methods=["POST"])
def delete_all_tasks():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()
    return redirect("/")

# Main function to initialize the database and run the Flask app
if __name__ == "__main__":
    init_db()  # Initialize database (creates the table if not already created)
    app.run(debug=True)  # Start the Flask application in debug mode
