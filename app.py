import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# The secret_key is essential for session['user'] to work and keep users logged in
app.secret_key = "alstandesign_secure_key_2026"

# --- DATABASE LOGIC ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'alstandesign.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates necessary tables if they don't exist."""
    print("--- STEP 1: INITIALIZING DATABASE ---")
    try:
        conn = get_db_connection()
        # Table for registered clients
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        # Table for contact form inquiries
        conn.execute('''
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING'
            )
        ''')
        conn.commit()
        conn.close()
        print(f"SUCCESS: Database synchronized at {DB_PATH}")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")

# Run database initialization on startup
init_db()

# --- ROUTES ---

@app.route('/')
def index():
    """Main landing page. Passes the logged-in user's name to the navbar."""
    user_name = session.get('user') 
    return render_template('index.html', name=user_name)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new identity enrollment."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        try:
            # Inserts new user into the database
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, password))
            conn.commit()
            print(f"NEW ENROLLMENT: {username}")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Email already exists. <a href='/register'>Try again</a>"
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles secure access to the client portal."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        # Matches email and password against the database
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?',
                            (email, password)).fetchone()
        conn.close()
        
        if user:
            # Stores the username in the session so they stay logged in
            session['user'] = user['username']
            return redirect(url_for('index'))
        return "Invalid Credentials. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Clears the session and returns to the terminal."""
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/submit', methods=['POST'])
def submit():
    """Processes inquiries from the 'Start a Project' form."""
    email = request.form.get('email')
    message = request.form.get('message')
    
    if email and message:
        conn = get_db_connection()
        conn.execute('INSERT INTO inquiries (email, message) VALUES (?, ?)', 
                     (email, message))
        conn.commit()
        conn.close()
        return "Inquiry Deployed Successfully. <a href='/'>Return to Main Terminal</a>"
    return "Missing information. <a href='/'>Go back</a>"

@app.route('/admin')
def admin_panel():
    """Fetches records for the themed terminal."""
    conn = get_db_connection()
    
    # Fetching: [0]=id, [1]=username, [2]=email
    users = conn.execute('SELECT id, username, email FROM users').fetchall()
    
    # Fetching: [0]=id, [1]=email, [2]=message, [3]=status
    inquiries = conn.execute('SELECT id, email, message, status FROM inquiries').fetchall()
    
    conn.close()
    return render_template('admin.html', users=users, inquiries=inquiries)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    """Deletes user by ID to avoid build errors."""
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

# IMPORTANT: Add this at the bottom to keep the server running
if __name__ == '__main__':
    app.run(debug=True)