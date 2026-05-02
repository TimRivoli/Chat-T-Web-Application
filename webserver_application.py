from functools import wraps
from flask import Flask, redirect, render_template, request, jsonify, session, url_for
from flask_oauthlib.client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid, threading, time, os
from _classes.DataClasses import *
from _classes.ChatManager import *
from _classes.StorageManager import StorageManager

app = Flask(__name__)
app.secret_key = google_api_key
chat_managers = {}
_chat_managers_lock = threading.RLock()
_last_access = {}
_SESSION_TTL = 7200  # seconds before an idle session is evicted
max_question_length = 1000
chat_activity_modes = []
language_options = [o.value for o in ChatLanguageOption]

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
def _evict_stale_sessions():
	now = time.time()
	stale = [sid for sid, t in list(_last_access.items()) if now - t > _SESSION_TTL]
	for sid in stale:
		cm = chat_managers.pop(sid, None)
		_last_access.pop(sid, None)
		if cm:
			try:
				cm.shut_down()
			except Exception:
				pass
		print(f"Evicted stale session: {sid}")

def get_chat_manager():
	with _chat_managers_lock:
		if 'session_id' not in session:
			return None
		session_id = session['session_id']
		if session_id not in chat_managers:
			set_chat_manager()
		_last_access[session_id] = time.time()
		_evict_stale_sessions()
		return chat_managers.get(session_id)

def set_chat_manager():
	session_id = session['session_id']
	if session_id not in chat_managers:
		cm = ChatManager()
		if not chat_activity_modes:
			for m in cm.get_chat_modes():
				chat_activity_modes.append(m.activityName)
		chat_managers[session_id] = cm
		_last_access[session_id] = time.time()
		print(f"Created ChatManager instance for session: {session_id}")

def remove_chat_manager():
	with _chat_managers_lock:
		session_id = session.get('session_id')
		if session_id and session_id in chat_managers:
			cm = chat_managers.pop(session_id)
			_last_access.pop(session_id, None)
			cm.shut_down()
			print(f"Removed ChatManager instance for session: {session_id}")

def verify_session():
	global chat_managers
	#verify user has logged in and the session is setup
	result = False
	if 'google_token' in session:
		user_info = google.get('userinfo')
		user_id = google.get('sub')
		if 'email' in user_info.data.keys(): 
			session['email'] = user_info.data['email']
		else:
			session['email'] = ""
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
	id_token = response.get('id_token')
	print(f"id_token: {id_token}")
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
		cm = get_chat_manager()
		categories = cm.sm.get_note_category_objects()
		return render_template('conversation.html', username=session['email'], chatActivityModes=chat_activity_modes, categories=categories, language_options=language_options)
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
		chat_activity_name = request.form['chat_activity_mode'] if request.form['chat_activity_mode'] is not None and request.form['chat_activity_mode'] != '' else 'Conversation'
		x = request.form['response_size']
		response_tokens = 1000
		if x =='small':	response_tokens = 350
		if x =='large':	response_tokens = 2000
		if x =='verylarge':	response_tokens = 3500
		x = request.form['temperature']
		temperature = float(x)/10		
		response = ""
		if question !='':
			x = request.form['temperature']
			temperature = float(x)/10		
			user_instructions = request.form['user_instructions'][:max_question_length].strip()
			language_option = request.form.get('language_option', 'English')
			chat_activity_mode = None
			cm = get_chat_manager()
			for m in cm.get_chat_modes(): 
				if m.activityName == chat_activity_name: chat_activity_mode = m
			chat_activity_mode.temperature = temperature
			response = cm.chatbot_query(question=question, activity_mode=chat_activity_mode, language_option=language_option, response_tokens=response_tokens, user_instructions=user_instructions)
			cm.auto_save()
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
 
def format_markdown(text):
	result = text
	ticks = "\n```"
	while ticks in result:
		result = result.replace(ticks, "<pre><div class='markdowncode'>", 1)
		result = result.replace(ticks, "</div></pre>", 1)
	return result

@app.route('/load/<int:conversation_id>')
def load_conversation(conversation_id):
	print(f"Route: load/{conversation_id}")
	if verify_session():
		print(f"Received request to load {conversation_id}")
		cm = get_chat_manager()
		cm.load_conversation(conversation_id)
		messages = cm.messages_extended
		for m in messages:
			if m.role=="assistant":
				m.content = format_markdown(m.content)
		categories = cm.sm.get_note_category_objects()
		return render_template('conversation.html', username=session['email'], messages=messages, chatActivityModes=chat_activity_modes, categories=categories, language_options=language_options)
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


@app.route('/notes')
def display_notes():
	print("Route: notes")
	if verify_session():
		cm = get_chat_manager()
		notes = cm.sm.get_notes(-1, '')
		categories = cm.sm.get_note_category_objects()
		return render_template('note_list.html', notes=notes, categories=categories)
	else:
		return redirect('/')

@app.route('/note/new')
@login_required
def new_note():
	print("Route: note/new")
	if verify_session():
		cm = get_chat_manager()
		categories = cm.sm.get_note_category_objects()
		return render_template('note.html', username=session['email'], note=NoteEntry(), categories=categories)
	else:
		return redirect('/')

@app.route('/note/<int:note_id>')
def load_note(note_id):
	print(f"Route: note/{note_id}")
	if verify_session():
		cm = get_chat_manager()
		n = cm.sm.get_note(note_id)
		categories = cm.sm.get_note_category_objects()
		return render_template('note.html', username=session['email'], note=n, categories=categories)
	else:
		return redirect('/')

@app.route('/note/save', methods=['POST'])
@login_required
def save_note():
	print("Route: note/save")
	if verify_session():
		cm = get_chat_manager()
		note_id = int(request.form.get('note_id', 0))
		if note_id == 0:
			note_id = get_current_timestamp()
		n = NoteEntry()
		n.noteID = note_id
		n.title = request.form.get('title', '').strip()
		n.content = request.form.get('content', '').strip()
		n.categoryID = int(request.form.get('category_id', 0))
		cm.sm.save_note(n)
		return redirect('/notes')
	else:
		return redirect('/')

@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
	print(f"Route: note/{note_id}/delete")
	if verify_session():
		cm = get_chat_manager()
		cm.sm.delete_note(note_id)
		return jsonify({'success': True})
	else:
		return jsonify({'success': False}), 401


@app.route('/save_as_note', methods=['POST'])
@login_required
def save_as_note():
	print("Route: save_as_note")
	if verify_session():
		cm = get_chat_manager()
		if not cm.messages_extended:
			return jsonify({'success': False, 'error': 'No conversation to save'})
		title = request.form.get('title', '').strip()
		category_id = int(request.form.get('category_id', 0))
		if not title:
			title = f"Conversation {get_current_date().strftime('%Y-%m-%d')}"
		lines = [m.content for m in cm.messages_extended if m.role == 'assistant']
		n = NoteEntry()
		n.noteID = get_current_timestamp()
		n.title = title
		n.content = "\n\n".join(lines)
		n.categoryID = category_id
		cm.sm.save_note(n)
		return jsonify({'success': True, 'note_id': n.noteID})
	return jsonify({'success': False}), 401

@app.route('/sync_status')
@login_required
def sync_status():
	cm = get_chat_manager()
	if cm:
		return jsonify({'in_progress': cm.sm.sync_in_progress, 'status': cm.sm.sync_status})
	return jsonify({'in_progress': False, 'status': 'Idle'})

@app.errorhandler(404)
def page_not_found(e):
	result = "Page not found. Redirecting to home page..."
	result +="<script> setTimeout(function() {window.location.href = '/';  }, 3000);     </script>"
	return result

if __name__ == '__main__':
	app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')