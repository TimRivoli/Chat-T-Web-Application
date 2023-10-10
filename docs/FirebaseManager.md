Sure, here's a `readme.md` file with the provided Python code:

```markdown
# FirebaseManager Class

This Python class manages interactions with Firebase, providing functions for authentication, data retrieval, and storage.

## Prerequisites

- Make sure you have the required Python modules installed:
  - `firebase_admin`
  - `flask`
  
## Usage

1. Import the necessary modules:
```python
import firebase_admin
from flask import session 
from firebase_admin import credentials, auth, firestore, initialize_app
from _classes.Constants import *
from _classes.Utility import *
from _classes.DataClasses import *
```

2. Create an instance of `FirebaseManager`:
```python
fb = FirebaseManager()
```

3. Use the available functions to interact with Firebase. For example:
```python
conversations = fb.get_conversation_toc()
for conversation in conversations:
    print("Conversation:", conversation)
```

## Functions

- `initialize(use_google_auth)`: Initializes the Firebase app with the provided credentials. If `use_google_auth` is `True`, it uses Google authentication.

- `generate_id(time_stamp=0, day_precision=False, base_id = "")`: Generates a unique ID.

- `get_document_by_id(collection_name, document_id)`: Retrieves a document from a collection by its ID.

- `save_document(collection_name, document_id, data)`: Saves a document in a collection.

- `get_document_items(document)`: Retrieves items from a document.

- ... (and more, see the code for additional functions)

## Example

```python
if __name__ == "__main__":
    fb = FirebaseManager()
    print("ID: ", fb.generate_id())
    conversations = fb.get_conversation_toc()
    for conversation in conversations:
        print("Conversation:", conversation)
```

## Important Notes

- Make sure to set up Firebase and obtain the necessary credentials before using this class.

- Modify the class and functions as per your specific use case.

- This code is a sample and may require adjustments based on your application's requirements.

---

Feel free to modify this `readme.md` file according to your project's specific needs and requirements.