# SQLManager

The `SQLManager` class provides functionalities for managing SQL database connections and performing operations on the database. This class assumes the presence of a SQL Server database named `ChatDatabase` running on `localhost`.

## Usage

To use the `SQLManager` class, follow these steps:

1. Import the required libraries:
   ```python
   import pyodbc
   from _classes.DataClasses import *
   from _classes.Constants import *
   ```

2. Initialize an instance of `SQLManager`:
   ```python
   sql_manager = SQLManager()
   ```

3. Use the provided methods to interact with the database.

## Methods

### `create_tables()`

Creates necessary tables if they do not exist.

### `recreate_database()`

Drops existing tables and creates new ones.

### `apply_updates()`

Applies updates to the database.

### `cursor_to_conversation(cursor)`

Converts a database cursor to a `Conversation` object.

### `get_conversations_last_updated(user_id)`

Retrieves the timestamp of the last updated conversation for a specific user.

### `update_conversation_dates(conversation)`

Updates the date-related fields of a conversation.

### `save_conversation(conversation)`

Saves a conversation to the database.

### `delete_conversation(conversation_id)`

Deletes a conversation from the database.

### `get_deleted_conversations(user_id)`

Retrieves a list of conversation IDs that have been marked as deleted by a user.

### `get_all_conversations(user_id)`

Retrieves all conversations for a specific user.

### `get_conversation(conversation_id, user_id)`

Retrieves a specific conversation by ID for a user.

### `update_conversation_modified(conversation)`

Updates the modification date of a conversation.

### `cursor_to_chat_message(cursor)`

Converts a database cursor to a `ChatMessageExtended` object.

### `append_message(conversation, chat_message)`

Appends a message to a conversation.

### `delete_message(message)`

Deletes a message from a conversation.

### `get_messages(conversation_id)`

Retrieves all messages for a specific conversation.

### `cursor_to_usage(cursor)`

Converts a database cursor to a `ChatUsage` object.

### `get_conversation_usage(conversation_id)`

Retrieves the total token count for a conversation.

### `get_usage(user_id, android_id)`

Retrieves a list of usage data for a specific user and Android device.

### `get_usage_last_updated(user_id, android_id)`

Retrieves the timestamp of the last updated usage data for a specific user and Android device.

### `append_usage(usage)`

Appends usage data to the database.

### `get_sample_prompt(activity_name, unused=False)`

Retrieves a sample prompt.

### `reuse_sample_prompts()`

Resets the usage status of sample prompts.

### `get_sample_prompts(cutoff, unused=False)`

Retrieves a list of sample prompts.

### `clean_sample_prompts()`

Removes duplicate sample prompts.

### `append_sample_prompt(time_stamp, prompt)`

Appends a sample prompt to the database.

### `get_sample_prompts_last_updated()`

Retrieves the timestamp of the last updated sample prompts.

### `get_sample_prompts_count(unused=False)`

Retrieves the count of sample prompts.

### `apply_fixes(user_id, android_id)`

Applies database fixes, such as updating empty user IDs and cleaning sample prompts.

## Note

Make sure to initialize the `SQLManager` instance and establish a connection to the database before using any of the methods.