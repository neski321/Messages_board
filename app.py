# app.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pyrebase
from dotenv import load_dotenv
import os



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
login_manager = LoginManager(app)

# Load environment variables from the .env file
load_dotenv()

# Firebase configuration
firebase_config = {
  'apiKey': os.getenv('FIREBASE_API_KEY'),
  'authDomain':os.getenv('FIREBASE_AUTH_DOMAIN'),
  'projectId':os.getenv('FIREBASE_PROJECT_ID'),
  'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
  'databaseURL':os.getenv('FIREBASE_DATABASE_URL'),
  'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
  'appId': os.getenv('FIREBASE_APP_ID'),
}

firebase = pyrebase.initialize_app(firebase_config)

auth = firebase.auth()
db = firebase.database()

# User class for authentication
class User(UserMixin):
    def __init__(self, user_id, email=None):
        self.id = user_id
        self.email = email 

# Data structure to store messages
class Message:
    def __init__(self, username, message, likes=0, key=None):
        self.username = username
        self.message = message
        self.likes = likes
        self.key = key

prohibited_words = ['hate', 'offensive', 'inappropriate']  # Add more words as needed

def contains_prohibited_word(message):
    for word in prohibited_words:
        if word.lower() in message.lower():
            return True
    return False

@login_manager.user_loader
def load_user(user_id):
    user_data = db.child('users').child(user_id).get().val()
    if user_data:
        email = user_data.get('email')  # Get email from user_data
        return User(user_id, email)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('You need to be logged in to access this page', 'error')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Retrieve messages from the database
    messages_data = db.child('messages').get().val() or {}

    # Convert messages_data to a list of Message objects
    messages = [Message(message_data['username'], message_data['message'], message_data['likes'], key) for key, message_data in messages_data.items()]

    return render_template('index.html', messages=messages, warning_message=None, current_user=current_user)

@app.route('/post_message', methods=['POST'])
@login_required
def post_message():
    username = current_user.email.split('@')[0]
    message_text = request.form['message']

    # Check if the message contains prohibited words
    if contains_prohibited_word(message_text):
        flash("Your message contains prohibited words. Please be respectful.", 'error')
    else:
        # Add the message to the database
        new_message_ref = db.child('messages').push({
            'username': username,
            'message': message_text,
            'likes': 0  # Initialize likes count to 0
        })

    # Redirect to the home page
    return redirect(url_for('index'))

@app.route('/like/<string:message_key>')
@login_required
def like(message_key):
    # Update the likes count for the specified message key in the database
    db.child('messages').child(message_key).child('likes').transaction(lambda current_likes: (current_likes or 0) + 1)

    # Redirect to the home page
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Check if the user exists in Firebase Authentication
            user = auth.sign_in_with_email_and_password(email, password)
            user_id = user['localId']

            # Check if the user exists in the database
            user_data = db.child('users').child(user_id).get().val()

            if user_data:
                login_user(User(user_id))
                return redirect(url_for('index'))
            else:
                flash('User does not exist. Redirecting to registration page.', 'error')
                return redirect(url_for('register'))
        except Exception as e:
            print(e)
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Create user in Pyrebase authentication
            user = auth.create_user_with_email_and_password(email, password)
            user_id = user['localId']

            # Add user data to the database
            db.child('users').child(user_id).set({'email': email})

            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(e)
            flash('Registration failed. Please try again later.', 'error')

    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
