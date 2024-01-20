# app.py
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key
login_manager = LoginManager(app)

# Data structure to store messages and users
messages = []
users = {}

# User class for authentication
class User(UserMixin):
    def __init__(self, user_id, username, password):
        self.id = user_id
        self.username = username
        self.password = password

class Message:
    def __init__(self, username, message):
        self.username = username
        self.message = message
        self.likes = 0 
        

prohibited_words = ['hate', 'offensive', 'inappropriate']  # Add more words as needed

def contains_prohibited_word(message):
    for word in prohibited_words:
        if word.lower() in message.lower():
            return True
    return False

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash('You need to be logged in to access this page', 'error')
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html', messages=messages, warning_message=None, current_user=current_user)

@app.route('/post_message', methods=['POST'])
@login_required
def post_message():
    username = current_user.username
    message_text = request.form['message']

    # Check if the message contains prohibited words
    if contains_prohibited_word(message_text):
        flash("Your message contains prohibited words. Please be respectful.", 'error')
    else:
        # Find the existing message with the same content
        existing_message = next((msg for msg in messages if msg.username == username and msg.message == message_text), None)

        if existing_message:
            # If the message already exists, increment its like count
            existing_message.likes += 1
        else:
            # If the message does not exist, add a new message with an initial likes count of 0
            new_message = Message(username, message_text)
            messages.append(new_message)

    # Redirect to the home page
    return redirect(url_for('index'))

@app.route('/like/<int:message_index>')
@login_required
def like(message_index):
    # Increase the likes count for the specified message index
    messages[message_index]['likes'] += 1

    # Redirect to the home page
    return redirect(url_for('index'))

@app.route('/get_likes/<int:message_index>')
def get_likes(message_index):
    # Return the likes count for the specified message index as JSON
    return jsonify({'likes': messages[message_index]['likes']})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((user for user in users.values() if user.username == username and user.password == password), None)
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the username is already taken
        if username in [user.username for user in users.values()]:
            flash('Username already taken. Please choose a different username.', 'error')
        else:
            # Create a new user and add it to the users dictionary
            user_id = len(users) + 1
            new_user = User(user_id, username, password)
            users[user_id] = new_user
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
