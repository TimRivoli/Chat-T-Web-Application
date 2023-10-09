import openai, tiktoken
from _classes.Constants import *
from _classes.DataClasses import *
from _classes.Utility import *
from _classes.StorageManager import StorageManager

class ChatManager:
	TAG = "ChatManager"
	currentModel = defaultModel
	conversation_token_count = 0
	chatModes = []
	conversation = Conversation()
	messages_extended = []
	chatUsage = []
	sm = None

	def __init__(self):
		print("Initializing ChatManager")
		openai.api_key = openai_api_key
		self.sm = StorageManager()
		self.chatModes = self.sm.get_chat_modes()

	def shut_down(self):
		self.sm.shut_down()

# ------------------------------------------------------- API Calls ---------------------------------------------------------
	# @staticmethod
	# async def execute_query(self, messages, temperature=0.2, model=defaultModel, isSystem=False):
		# result = ""
		# total_tokens = 0
		# chatCompletion = WebManager.callChatCompletionAPI(messages, temperature, model)
		# message = chatCompletion.choices[0].message
		# if chatCompletion.choices[0].finish_reason == "Error":
			# result = message.content
			# if result.startswith("Socket timeout", True): result = "Request timed out."
		# else:
			# usage = chatCompletion.usage
			# u = ChatUsage(self.conversation.conversationID, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)
			# if isSystem: u.conversationID = -100
			# self.chatUsage.append(u)
			# self.sm.appendUsage(u)
			# result = message.content
			# total_tokens = usage.total_tokens
		#print(chatCompletion)
		# return result, total_tokens

	def execute_query(self, messages:list, temperature:float=0.2, model:str = defaultModel, isSystem=False, response_tokens:int=1000):
		result = ""
		token_count = 0
		m2 = []
		for m in messages:	m2.append(m.__dict__())
		try: 
			model_result = openai.ChatCompletion.create(model=model, messages=m2, temperature=temperature, max_tokens=response_tokens)
			success = True
		except Exception as e:
			print("ChatGPT query failed:", e)
			success = False
			result = "API Call Failed. " + str(e)
			#Incorrect API key provided
			#The model `gpt-4` does not exist or you do not have access to it. Learn more: https://help.openai.com/en/articles/7102672-how-can-i-access-gpt-4.
		if success: 
			token_limit = 0
			usage_summary = f"Usage Summary (Prompt: {model_result.usage.prompt_tokens}, Response: {model_result.usage.completion_tokens}, Total Tokens: {model_result.usage.total_tokens}, Response Limit: {response_tokens}, Specified Model Limit: {token_limit})"
			print(usage_summary)
			result = model_result.choices[0].message.content
			token_count = model_result.usage.total_tokens
			self.append_conversation(content=result, token_count=token_count, is_response=True)
			#result = result.replace("\n", "<BR>") 
			#$result = result.replace("<BR><BR>", "<BR>") 
			#result = result.replace("<BR><BR>", "<BR>") 
		return result, token_count
		
	def get_token_count(self, text:str):
		token_count = 0
		if text:
			encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
			token_count = len(encoding.encode(text))
			print(f" The text contains {token_count} tokens.")
		return token_count

	def chatbot_query(self, question, activity_mode, language_option, user_instructions=""):
		result = ""
		if question:
			messages = []
			system_message = activity_mode.prompt
			if activity_mode.showLanguageOptions:
				system_message += " " + language_option
			user_tokens = self.get_token_count(user_instructions + ". " + question)
			if user_instructions:
				system_message = user_instructions + ". " + system_message
			messages.append(ChatMessage("system", system_message))

			if activity_mode.conversational:
				if self.conversation_token_count > 750 and len(self.messages_extended) > 2:
					self.conversationSummarize()
				if self.conversation.summary:
					messages.append(ChatMessage("system", "Conversation summary: " + self.conversation.summary))
				for m in self.messages_extended:
					if m.role == "user":
						messages.append(ChatMessage(m.role, m.content))
					else:
						messages.append(ChatMessage(m.role, m.content[:100]))
			messages.append(ChatMessage("user", question))
			self.append_conversation(question, user_tokens, False)
			content, total_tokens = self.execute_query(messages, activity_mode.temperature, self.currentModel, False)
			self.append_conversation(content=content, token_count=total_tokens, is_response=True)
		return content

	def conversation_summarize(self):
		print("Summarizing conversation...")
		messages = []
		messages.append(ChatMessage("system", "You will be given a conversation, your task is to summarize it making sure to include information provided by the user"))
		if self.conversation.summary:
			messages.append(ChatMessage("user", "Please generate a concise summary of this conversation. Make sure to include information provided by the user: " + self.conversation.summary))

		for m in self.messages_extended:
			messages.append(ChatMessage(m.role, m.content))

		self.conversation_token_count -= self.get_token_count(self.conversation.summary)
		content, total_tokens = self.execute_query(messages, 0.0, defaultModel, True)
		self.conversation.summary = result
		self.conversation_token_count += total_tokens

	def conversation_make_title(self):
		print("Making conversation title...")
		if not self.conversation.summary:
			self.conversationSummarize()
		messages = []
		messages.append(ChatMessage("user", "Provide a concise 5 word topic for this conversation: " + self.conversation.summary))
		content, total_tokens = self.execute_query(messages, 0.2, defaultModel, True)
		self.conversation.title = content

	def generate_sample_prompts(self):
		print("Generating sample prompts...")
		for i in range(10):
			messages = []
			messages.append(ChatMessage("user", "Sample prompt."))
			content, total_tokens = self.execute_query(messages, 0.2, defaultModel, True)
			self.sm.appendSamplePrompt(SamplePrompt("Conversation", content))


# ------------------------------------------------------- Chat management ---------------------------------------------------------
	def toggle_engine(self):
		if self.currentModel == self.defaultModel:
			self.currentModel = self.enhancedModel
		else:
			self.currentModel = self.defaultModel

	def clear_conversation(self):
		self.conversation.conversationID = get_current_timestamp()
		self.conversation.title = ""
		self.conversation.summary = ""
		self.conversation.dateCreated = get_current_date()
		self.conversation.dateModified = get_current_date()
		self.conversation.dateAccessed = get_current_date()
		self.conversation.saved = False
		self.messages_extended.clear()
		self.conversation_token_count = 0
		print("Chat conversation cleared.")

	def save_conversation(self):
		self.conversation_make_title()  # This only gets called once so title should be empty
		self.sm.save_conversation(self.conversation, self.messages_extended)

	def load_conversation(self, conversationID):
		print("Asked to load conversation:", conversationID)
		self.conversation = self.sm.get_conversation(conversationID)
		if self.conversation.conversationID != conversationID:
			print("Could not locate:", conversationID)
			self.clear_conversation()
		else:
			print("Found:", self.conversation.conversationID)
			print("Title:", self.conversation.title)
			self.messages_extended.clear()
			x = self.sm.get_messages(self.conversation.conversationID)
			for m in x:
				self.messages_extended.append(m)
			self.conversation_token_count = self.sm.get_conversation_usage(conversationID)
			print("Messages:", len(self.messages_extended))
		print("Chat conversation load completed.")

	def delete_conversation(self, conversationID):
		self.sm.deleteConversation(conversationID)

	def delete_message(self, message):
		self.messages_extended.remove(message)
		self.sm.deleteMessage(message)

	def append_conversation(self, content, token_count, is_response):
		if content:
			m = ChatMessageExtended(self.conversation.conversationID, "", content)
			if is_response:
				m.role = "assistant"
			else:
				m.role = "user"
			self.messages_extended.append(m)
			if self.conversation.saved:
				self.sm.append_message(self.conversation, m)

	def get_conversation_list(self):
		return self.sm.get_conversation_list()
	
