from functools import wraps
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
from flask_oauthlib.client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid
from _classes.DataClasses import *
from _classes.ChatManager import *

app = Flask(__name__)
app.secret_key = google_api_key
chat_managers = {}	#dictionary of ChatManagers for each user session
max_question_length = 1000

# ------------------------------------------------------- Google OAuth  ---------------------------------------------------------
oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=google_client_id, 
    consumer_secret=google_client_secret,
    request_token_params={'scope': 'email', },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

# ------------------------------------------------ User Session Management and login authorization  -------------------------------------------------
def get_chat_manager():
	result = None
	if 'session_id' in session.keys():
		session_id = session['session_id']
		if not session_id in chat_managers.keys(): set_chat_manager()
		if session_id in chat_managers.keys():
			result = chat_managers[session_id]
	return result

def set_chat_manager():
	session_id = session['session_id']
	if not session_id in chat_managers.keys(): 
		chat_managers[session_id] = ChatManager()
		print(f"Created ChatManager instance for session: {session_id}")

def remove_chat_manager():
	session_id = session['session_id']
	if session_id in chat_managers.keys(): 
		cm  = chat_managers[session_id] 
		cm.shut_down()
		del chat_managers[session_id] 
		print(f"REmoved ChatManager instance for session: {session_id}")

def verify_session():
	global chat_managers
	#verify user has logged in and the session is setup
	result = False
	if 'google_token' in session:
		user_info = google.get('userinfo')
		user_id = google.get('sub')
		if 'email' in user_info.data.keys(): session['email'] = user_info.data['email']
		if 'session_id' not in session:
			session['session_id'] = str(uuid.uuid4())
			set_chat_manager()
			print(f"Key count on verification: {len(chat_managers)}")
			print(f"Session initialized: {session['session_id']}")
			print(f"Email: {session['email']}")
		result = ('session_id' in session)
	return result

@google.tokengetter
def get_google_oauth_token():
	return session.get('google_token')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'google_token' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return decorated_function

@app.route('/login')
def login():
	print("Route: login")
	return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/login/authorized')
def authorized():
	print("Route: login/authorized")
	response = google.authorized_response()
	if response is None or response.get('access_token') is None:
		return 'Access denied: reason={} error={}'.format(
			request.args['error_reason'],
			request.args['error_description']
		)
	session['google_token'] = (response['access_token'], '')
	user_info = google.get('userinfo')
	result = 'Logged in as: ' + user_info.data['email']
	result +="<script> setTimeout(function() {window.location.href = '/';  }, 3000);     </script>"
	return result

@app.route('/logout')
def logout():
	print("Route: logout")
	remove_chat_manager()
	session.clear()
	session.pop('google_token', None)
	return "You have been logged out."
	

# ------------------------------------------------------- Conversation Handling ------------------------------------------------------
@app.route('/')
@login_required
def index():
	print("Route: default")
	if verify_session():
		return render_template('conversation.html', username=session['email'] )
	else:
		return 'You are not logged in.'

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
	print("Route: clear_chat")
	if verify_session():
		cm = get_chat_manager()
		cm.clear_conversation()
	return redirect('/')

@app.route('/chat_query', methods=['POST'])
@login_required
def chat_query():
	print("Route: chat_query")
	if verify_session():
		question = request.form['user_input'][:max_question_length].strip()
		response = ""
		if question !='':
			x = request.form['temperature']
			temperature = float(x)/10		
			user_instructions = request.form['user_instructions'][:max_question_length].strip()
			language_option = "English"
			activity_mode = ChatActivityType("Conversation", "Start a conversation about the given text, be informative in your responses", True, False, False, temperature=temperature)
			cm = get_chat_manager()
			response = cm.chatbot_query(question, activity_mode, language_option, user_instructions)
			#chatBox.innerHTML += `<div class="bot-message">${response.response}</div>`; response is appended via javascript function
		return jsonify({'response': response})
	else:
		return redirect('/')

@app.route('/conversations')
def display_conversations():
	print("Route: conversations")
	if verify_session():
		session_id = session['session_id']
		print(session_id)
		for key in chat_managers.keys():
			print(f"key: {key}")
		cm = get_chat_manager()
		conversations = cm.get_conversation_list()
		return render_template('conversation_list.html', conversations=conversations)
	else:
		return redirect('/')
 
@app.route('/load/<int:conversation_id>')
def load_conversation(conversation_id):
	print(f"Route: load/{conversation_id}")
	if verify_session():
		print(f"Received request to load {conversation_id}")
		cm = get_chat_manager()
		cm.load_conversation(conversation_id)
		messages = cm.messages_extended
		return render_template('conversation.html', username=session['email'], messages=messages )
	else:
		return redirect('/')


@app.route('/update/<int:conversation_id>', methods=['POST'])
def update_conversation(conversation_id):
	print(f"Route: update/{conversation_id}")
	if verify_session():
		cm = get_chat_manager()
		title = request.form.get('title')
		summary = request.form.get('summary')
		print(f"Received request to save updates to {conversation_id}")
		# Update the database
		#cursor.execute('UPDATE conversation SET title=?, summary=? WHERE conversationID=?', (title, summary, conversation_id))
		#conn.commit()
		return redirect(url_for('display_conversations'))
	else:
		return redirect('/')

@app.errorhandler(404)
def page_not_found(e):
	result = "Page not found. Redirecting to home page..."
	result +="<script> setTimeout(function() {window.location.href = '/';  }, 3000);     </script>"
	return result

if __name__ == '__main__':
	app.run(debug=True)