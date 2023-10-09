# chatbot_web_application
Chatbox web application
## 📚 Description
Demonstrates:
  -Web-based Chat interface using OpenAI chat completions API
  
  -ChatManager: handles the active conversation and interaction with the completions API
  
  -SQLManager: provides local SQL storage for conversation and token usage history
  
  -FirebaseManager: provides efficient Firebase cloud storage of conversation and token usage history, allowing these to be synchronized with my companion Chat-T (chatty) Android application
  
  -StorageManager: front-ends SQLManager and FirebaseManager and handles synchronization between the two
  
  -Authentication to the website and Firebase is done via Google OAuth
  
## ✅ Requirements:
  -pip install flask, flask-OAuthlib, google-auth, flask, openai, tiktoken, uuid
  
  -get an API token from OpenAI, setup a local SQL server, and register your application with Google Firebase
  
If this is too much then use the simpler chatbox_website project

This supports both the GPT 3.5 Turbo and GPT 4.0 models.  Turbo works pretty well and 4.0 is 20x the price so for this it really isn't worth it. 

Have fun and keep programming!

-Tim
