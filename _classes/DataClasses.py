from enum import Enum
from _classes.Utility import *

class ChatActivityType:
	def __init__(self, activityName="", prompt="", conversational=False, clearConversationOnChange=True, showLanguageOptions=False, temperature=0.2):
		self.activityName = activityName
		self.prompt = prompt
		self.conversational = conversational
		self.clearConversationOnChange = clearConversationOnChange
		self.showLanguageOptions = showLanguageOptions
		self.temperature = temperature

class ChatLanguageOption(Enum):
	English = "English"
	French = "French"
	German = "German"
	Spanish = "Spanish"
	Italian = "Italian"
	Chinese = "Chinese"
	Japanese = "Japanese"
	Python = "Python"
	Java = "Java"
	Kotlin = "Kotlin"
	def __str__(self): 	return self.value
	
	@staticmethod
	def from_string(value):
		for option in ChatLanguageOption:
			if option.value == value:
				return option
		return None

class ChatUsage:
	def __init__(self, conversationID=0, promptTokens=0, completionTokens=0, totalTokens=0, userID="", androidID="", timeStamp=None):
		self.conversationID = conversationID
		self.promptTokens = promptTokens
		self.completionTokens = completionTokens
		self.totalTokens = totalTokens
		self.userID = userID
		self.androidID = androidID
		self.timeStamp = timeStamp or get_current_timestamp()
	def __str__(self):
		return f"Conversation ID: {self.conversationID}, Prompt Tokens: {self.promptTokens}, Completion Tokens: {self.completionTokens}, Total Tokens: {self.totalTokens}, User ID: {self.userID}, Android ID: {self.androidID}, Timestamp: {self.timeStamp}"
		
class ChatMessage:
	def __init__(self, role, content):
		self.role = role
		self.content = content
	def __str__(self):	return f"Role: {self.role}, Content: {self.content}"   
	def __repr__(self): return f"ChatMessage({self.role}, {self.content})"
	def __dict__(self): return {'role': self.role,'content': self.content}

class ChatMessageExtended:
	def __init__(self, conversationID=0, role="", content="", timeStamp=None):
		self.conversationID = conversationID
		self.role = role
		self.content = content
		self.timeStamp = timeStamp or get_current_timestamp()
	def __str__(self):	return f"Conversation ID: {self.conversationID}, Role: {self.role}, Content: {self.content[:35]}, Timestamp: {self.timeStamp}"
	def __repr__(self): return f"ChatMessage({self.role}, {self.content})"
	def __dict__(self): return {'role': self.role,'content': self.content}

class ChatCompletion:
	def __init__(self, id="", object="", created=0, model="", choices=None, usage=None):
		self.id = id
		self.object = object
		self.created = created
		self.model = model
		self.choices = choices or []
		self.usage = usage
	def __str__(self):
		return f"ID: {self.id}, Object: {self.object}, Created: {self.created}, Model: {self.model}, Choices: {self.choices}, Usage: {self.usage}"


class Choice:
	def __init__(self, index, message, finish_reason):
		self.index = index
		self.message = message
		self.finish_reason = finish_reason
	def __str__(self):
		return f"Index: {self.index}, Message: {self.message[:35]}, Finish Reason: {self.finish_reason}"

class Conversation:
	def __init__(self, conversationID=None, title="", summary="", saved=False, userID="", dateCreated=None, dateAccessed=None, dateModified=None):
		self.conversationID = conversationID or get_current_timestamp()
		self.title = title
		self.summary = summary
		self.saved = saved
		self.userID = userID
		self.dateCreated = dateCreated or get_current_date()
		self.dateAccessed = dateAccessed or get_current_date()
		self.dateModified = dateModified or get_current_date()
	def __str__(self):
		return f"Conversation ID: {self.conversationID}, Title: {self.title[:35]}, Summary: {self.summary[:35]}, Saved: {self.saved}, User ID: {self.userID}, Date Created: {self.dateCreated}, Date Accessed: {self.dateAccessed}, Date Modified: {self.dateModified}"

class DeviceSettings:
	def __init__(self, deviceModel="", subscriptionLevel=-100, useGoogleAuth=False, syncConversations=False, syncUsage=True):
		self.deviceModel = deviceModel
		self.subscriptionLevel = subscriptionLevel
		self.useGoogleAuth = useGoogleAuth
		self.syncConversations = syncConversations
		self.syncUsage = syncUsage
	def __str__(self):
		return f"Device Model: {self.deviceModel}, Subscription Level: {self.subscriptionLevel}, Use Google Auth: {self.useGoogleAuth}, Sync Conversations: {self.syncConversations}, Sync Usage: {self.syncUsage}"

class SamplePrompt:
	def __init__(self, activityName="Conversation", prompt="", timeStamp=0):
		self.activityName = activityName
		self.prompt = prompt
		self.timeStamp = timeStamp
	def __str__(self):
		return f"Activity Name: {self.activityName}, Prompt: {self.prompt}, Timestamp: {self.timeStamp}"
