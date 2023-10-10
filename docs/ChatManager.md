# ChatManager

This is a Python class designed to manage chat interactions using OpenAI's ChatGPT model. It provides methods to perform various tasks related to conversations, messages, and interactions with the model.

## Usage

To use the `ChatManager` class, follow these steps:

1. Import the required libraries:
   ```python
   import openai
   from tiktoken import *
   from _classes.Constants import *
   from _classes.DataClasses import *
   from _classes.Utility import *
   from _classes.StorageManager import StorageManager
   ```

2. Initialize an instance of `ChatManager`:
   ```python
   chat_manager = ChatManager()
   ```

3. Use the provided methods to interact with the chat system.

## Methods

### `execute_query(messages:list, temperature:float=0.2, model:str = defaultModel, isSystem=False, response_tokens:int=1000)`

Executes a query to the ChatGPT model.

- `messages`: A list of `ChatMessage` objects.
- `temperature`: The temperature parameter for randomness in the response. Default is `0.2`.
- `model`: The model to be used for the query. Default is `defaultModel`.
- `isSystem`: Indicates if the message is a system message. Default is `False`.
- `response_tokens`: Maximum number of tokens in the response. Default is `1000`.

Returns a tuple containing the generated content and the total token count.

### `get_token_count(text:str)`

Counts the tokens in the provided text.

- `text`: The input text.

Returns the token count.

### `chatbot_query(question, activity_mode, language_option, user_instructions="")`

Queries the chatbot with a question.

- `question`: The user's question.
- `activity_mode`: The mode of the chat activity.
- `language_option`: The selected language option.
- `user_instructions`: Additional instructions from the user.

Returns the generated content.

### `conversation_summarize()`

Summarizes the conversation.

### `conversation_make_title()`

Creates a title for the conversation.

### `generate_sample_prompts()`

Generates sample prompts.

### `get_chat_modes()`

Returns the available chat modes.

### `toggle_engine()`

Toggles between different models.

### `clear_conversation()`

Clears the conversation.

### `save_conversation()`

Saves the conversation.

### `load_conversation(conversationID)`

Loads a conversation.

- `conversationID`: The ID of the conversation to be loaded.

### `delete_conversation(conversationID)`

Deletes a conversation.

- `conversationID`: The ID of the conversation to be deleted.

### `delete_message(message)`

Deletes a message from the conversation.

- `message`: The message to be deleted.

### `append_conversation(content, token_count, is_response)`

Appends a message to the conversation.

- `content`: The content of the message.
- `token_count`: The token count of the message.
- `is_response`: Indicates if the message is a response from the assistant.

### `get_conversation_list()`

Gets a list of conversations.

## Note

Make sure to set up your OpenAI API key before using this class.