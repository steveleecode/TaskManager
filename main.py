from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import sqlite3
import random
import string
from redis import Redis
import hashlib

app = Flask(__name__)

app.secret_key = hashlib.sha256(''.join(random.choices(string.ascii_letters + string.digits, k=8)).encode()).hexdigest()

length = 8
random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to initialize the database and create the tasks table if it doesn't exist
def init_db():
    conn = sqlite3.connect("tasks.db")  # Connect to the SQLite database
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER, 
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
        SELECT id, user_id, task, priority 
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
    if not session.get("logged_in"):
        return redirect("/login")
    return render_template("index.html", tasks=tasks, random_string = random_string)  # Render the HTML page with tasks


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/login_user", methods=["POST"])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    password_hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect("tasks.db")  # Connect to the database
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users where username = ? and password = ?", (username, password_hashed))
    output = cursor.fetchone()
    
    if output == None:
        print("User password combination not found")
        return redirect("/login")

    user = output[1]
    password = output[2]
    user_id = output[0]
    conn.commit()  # Save changes
    conn.close()  # Close connection



    if user == None or password == None:
        print("User not found")
        return redirect("/login")
    elif password == password_hashed:
        session["user_id"] = user_id
        session["logged_in"] = True
        session["username"] = user
        tasks = get_tasks()
        return render_template("index.html", tasks=tasks, random_string = random_string)  # Render the HTML page with tasks

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    password_hashed = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users where username = ? and password = ?", (username, password_hashed))

    if cursor.fetchone() is not None:
        return redirect("/register")
    cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password_hashed, email))
    conn.commit()
    conn.close()
    return redirect("/login")

# Route to handle task submissions
@app.route("/add_task", methods=["POST"])
def add_task_route():
    task = request.form.get(f"task-{random_string}")  # Get task input from the form
    priority = request.form.get("priority")
    user_id = session.get("user_id")
    if task:  # Ensure the task is not empty
        add_task(user_id, task, priority)  # Add task to the database
    else:
        print("ERROR: TASK IS EMPTY")
    return redirect("/")  # Redirect back to homepage after adding the task

# Function to add a task to the database
def add_task(user_id, task, priority):
    conn = sqlite3.connect("tasks.db")  # Connect to the database
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user_id, task, priority) VALUES (?, ?, ?)", (user_id, task, priority))  # Insert task into table
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
