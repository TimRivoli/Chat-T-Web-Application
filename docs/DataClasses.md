Certainly! Here's the `readme.md` file for the provided Python code:

```markdown
# Chat Classes

This module contains various classes related to chat activities and usage tracking.

## ChatActivityType

- This class defines different types of chat activities.

### Properties:

- `activityName`: Name of the activity.
- `prompt`: A prompt related to the activity.
- `conversational`: Specifies if the activity is conversational.
- `clearConversationOnChange`: Determines if the conversation should be cleared when activity changes.
- `showLanguageOptions`: Indicates if language options should be displayed.
- `temperature`: A parameter related to the activity.

## ChatLanguageOption

- This class is an enumeration of different language options.

### Options:

- English
- French
- German
- Spanish
- Italian
- Chinese
- Japanese
- Python
- Java
- Kotlin

## ChatUsage

- Represents usage information related to a conversation.

### Properties:

- `conversationID`: ID of the conversation.
- `promptTokens`: Number of tokens in the prompt.
- `completionTokens`: Number of tokens in the completion.
- `totalTokens`: Total number of tokens.
- `userID`: User ID.
- `androidID`: Android ID.
- `timeStamp`: Timestamp of the usage.

## ChatMessage

- Represents a message in a chat.

### Properties:

- `role`: Role of the message.
- `content`: Content of the message.

## ChatMessageExtended

- Represents an extended message in a chat.

### Properties:

- `conversationID`: ID of the conversation.
- `role`: Role of the message.
- `content`: Content of the message.
- `timeStamp`: Timestamp of the message.

## ChatCompletion

- Represents completion information.

### Properties:

- `id`: ID of the completion.
- `object`: Object related to the completion.
- `created`: Timestamp of creation.
- `model`: Model associated with the completion.
- `choices`: List of choices.
- `usage`: Usage information.

## Choice

- Represents a choice in a completion.

### Properties:

- `index`: Index of the choice.
- `message`: Message related to the choice.
- `finish_reason`: Finish reason for the choice.

## Conversation

- Represents a conversation.

### Properties:

- `conversationID`: ID of the conversation.
- `title`: Title of the conversation.
- `summary`: Summary of the conversation.
- `saved`: Indicates if the conversation is saved.
- `userID`: User ID associated with the conversation.
- `dateCreated`: Timestamp of creation.
- `dateAccessed`: Timestamp of last access.
- `dateModified`: Timestamp of last modification.

## DeviceSettings

- Represents device settings.

### Properties:

- `deviceModel`: Model of the device.
- `subscriptionLevel`: Subscription level.
- `useGoogleAuth`: Indicates if Google authentication is used.
- `syncConversations`: Indicates if conversations are synced.
- `syncUsage`: Indicates if usage is synced.

## SamplePrompt

- Represents a sample prompt.

### Properties:

- `activityName`: Name of the activity.
- `prompt`: Prompt related to the activity.
- `timeStamp`: Timestamp associated with the prompt.

---

Feel free to modify this `readme.md` file according to your project's specific needs and requirements.
```

This `readme.md` provides an overview of each class along with their properties and functionalities. You can customize it further based on your project's specific requirements.