```markdown
# Chat Application

This application is a Flask-based web application for managing chat conversations. It includes Google OAuth for user authentication and utilizes various classes for conversation handling.

## Prerequisites

- Python 3.x
- Flask
- Flask-OAuthlib

## Setup

1. Install the required packages:
   ```
   pip install flask flask-oauthlib
   ```

2. Set up your Google OAuth credentials. Replace `google_client_id`, `google_client_secret`, and `google_api_key` with your own credentials.

3. Run the application:
   ```
   python app.py
   ```

4. Access the application at [http://localhost:5000](http://localhost:5000).

## Overview

### Classes

- `ChatManager`: Manages chat sessions and interactions.

### Google OAuth

- Uses OAuth to authenticate users through Google.

### Session Management

- Manages user sessions and ChatManager instances for each session.

### Routes

- `/login`: Initiates the Google OAuth login process.
- `/login/authorized`: Callback route after successful login.
- `/logout`: Logs out the user and removes associated ChatManager instance.
- `/clear_chat`: Clears the conversation in the current session.
- `/chat_query`: Handles chat queries.
- `/conversations`: Displays a list of conversations.
- `/load/<int:conversation_id>`: Loads a specific conversation.
- `/update/<int:conversation_id>`: Updates conversation details.

### Templates

- `conversation.html`: Template for the main chat interface.
- `conversation_list.html`: Template for displaying conversation lists.

## Usage

1. Access the application at [http://localhost:5000](http://localhost:5000).
2. Log in with your Google account.
3. Start or join a conversation and interact with the chatbot.

## Notes

- Conversations are stored in memory for the duration of the session.
- This application serves as a basic framework and can be extended for more advanced functionality.

---

```
