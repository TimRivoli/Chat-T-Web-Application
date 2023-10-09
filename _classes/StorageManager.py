from _classes.DataClasses import *
from _classes.SQLManager import SQLManager
from _classes.FirebaseManager import FirebaseManager

class StorageManager:
	TAG = "StorageManager"
	use_google_auth = True
	user_id = firebase_user_ID
	android_id = "Webserver"
	device_id = "Webserver"
	subscription_level = 1
	sync_conversations = True
	sync_usage = False
	sync_in_progress = False
	sync_needed = True
	last_synced = 0
	sync_cooldown = 83333  # milliseconds = 5 min
	sql_mgr = None
	fb_mgr = None

	# def __new__(self, *args, **kwargs):
		# if not self._instance:
			# self._instance = super().__new__(self, *args, **kwargs)
		# return self._instance

	def __init__(self):
		print("Initializing StorageManager")
		if not self.sql_mgr or not self.fb_mgr:
			print("Initializing SQL and Firebase Managers...")
			self.sql_mgr = SQLManager()
			self.fb_mgr = FirebaseManager()
			#self.fb_mgr.initialize(self.use_google_auth)
			#self.download_registered_device_settings()
			if self.subscription_level > 0:
				self.sync_databases()	

	# def download_registered_device_settings(self):
		# s = self.fb_mgr.get_device_settings()
		# self.subscription_level = s.subscription_level
		# self.use_google_auth = s.use_google_auth
		# self.sync_conversations = s.sync_conversations and self.use_google_auth
		# self.sync_usage = s.sync_usage

	def shut_down(self):
		self.sql_mgr.shut_down()
		self.sql_mgr = None
		#self.fb_mgr.shut_down()
		#self.fb_mgr = None

#----------------------------------------------------------------------- Utility ------------------------------------------------------

	def get_chat_modes(self):
		result = []
		# Define the ChatActivityType objects
		conversation = ChatActivityType("Conversation", "Start a conversation about the given text, be informative in your responses", True, False, False, temperature=0.2)
		translation = ChatActivityType("Translation", "Translate the given text to ", True, True, True, temperature=0.2)
		tutor = ChatActivityType("Tutor", "You are a Socratic tutor. Use the following principles in responding to students:\n" +
			"- Ask thought-provoking, open-ended questions that challenge students' preconceptions and encourage them to engage in deeper reflection and critical thinking.\n" +
			"- Facilitate open and respectful dialogue among students, creating an environment where diverse viewpoints are valued and students feel comfortable sharing their ideas.\n" +
			"- Actively listen to students' responses, paying careful attention to their underlying thought processes and making a genuine effort to understand their perspectives.\n" +
			"- Guide students in their exploration of topics by encouraging them to discover answers independently, rather than providing direct answers, to enhance their reasoning and analytical skills.\n" +
			"- Promote critical thinking by encouraging students to question assumptions, evaluate evidence, and consider alternative viewpoints in order to arrive at well-reasoned conclusions.\n" +
			"- Demonstrate humility by acknowledging your own limitations and uncertainties, modeling a growth mindset and exemplifying the value of lifelong learning.\n ", True, True, False, temperature=0.2)
		joke = ChatActivityType("Joke", "Tell a joke or make a funny comment about the following prompt", True, True, False, temperature=0.5)
		story = ChatActivityType("Story", "Tell me a story inspired by the following prompt", True, True, False, temperature=0.5)
		result.extend([conversation, translation, tutor, joke, story])
		return result

	def save_language_pref(self, language):
		# Implementation for saving language preference goes here
		pass

	def get_language_ref(self):
		# Implementation for retrieving language preference goes here
		pass

#---------------------------------------------------------------- Conversations ------------------------------------------------------
	def get_conversation_list(self):
		return list(self.sql_mgr.get_all_conversations(self.user_id))

	def get_conversation(self, conversationID):
		conversation = self.sql_mgr.get_conversation(conversationID, self.user_id)
		conversation.dateAccessed = get_current_date()  # Update here rather than sqLiteManager to differentiate admin operations (sync) from user operations
		self.sql_mgr.update_conversation_dates(conversation)
		return conversation

	def get_conversation_usage(self, conversationID):
		return self.sql_mgr.get_conversation_usage(conversationID)

	def save_conversation(self, conversation, messages):
		if len(messages) > 0:
			print(f"Saving conversation: {conversation.conversationID}")
			self.sync_needed = True
			conversation.dateModified = get_current_date()
			conversation.dateAccessed = get_current_date()
			conversation.userID = self.user_id
			conversation.saved = True
			self.sql_mgr.save_conversation(conversation)
			for m in messages:
				self.sql_mgr.append_message(conversation, m)

	
	def delete_conversation(self, conversationID):
		self.sync_needed = True
		self.sql_mgr.delete_conversation(conversationID)

	def get_messages(self, conversationID):
		return list(self.sql_mgr.get_messages(conversationID))

	def append_message(self, conversation, message):
		print(f"Appending message: {conversation.conversationID}:{message.timeStamp}")
		self.sync_needed = True
		conversation.dateModified = get_current_date()
		self.sql_mgr.append_message(conversation, message)
		self.sql_mgr.update_conversation_modified(conversation)

	def delete_message(self, message):
		self.sync_needed = True
		self.sql_mgr.delete_message(message)
		self.sql_mgr.update_conversation_modified(ChatManager.conversation)

#---------------------------------------------------------------- Usage ------------------------------------------------------
	def append_usage(self, usage):
		usage.userID = self.user_id
		usage.androidID = self.androidID
		self.sql_mgr.append_usage(usage)

	def get_sample_prompt(self, activityName):
		return self.sql_mgr.get_sample_prompt(activityName)

	def append_sample_prompt(self, prompt):
		self.sql_mgr.append_sample_prompt(prompt)

#------------------------------------------------------------------- Sync ------------------------------------------------------
	def sync_databases(self):
		sync_conversations_down = self.sync_conversations
		sync_conversations_up = self.sync_conversations
		TOCRefreshNeeded = False
		timeSinceLastSync = get_current_timestamp() - self.last_synced
		# self.sql_mgr.applyFixes(self.user_id, self.androidID)
		if self.fb_mgr.is_functional and not self.sync_in_progress:
			if not self.sync_needed or timeSinceLastSync <= self.sync_cooldown:
				print(f"Sync is not needed or on cooldown. Needed: {self.sync_needed} Cooldown: {timeSinceLastSync}")
			else:
				self.sync_in_progress = True   # Prevent concurrent syncs
				conversationUpdates = 0
				messageUpdates = 0
				usageUpdates = 0

				# ------------------------------ Usage update -----------------------------------------
				if self.sync_usage:
					print("Uploading usage to Firebase...")
					usages = self.sql_mgr.getUsage(self.user_id, self.androidID)
					usageUpdates = self.fb_mgr.saveUsage(usages)
					print(f"SyncUp usage updates: {usageUpdates}")

				# ------------------------------ Sample prompts update -----------------------------------------
				# generateSamplePrompts()
				# uploadSamplePrompts()
				if self.sql_mgr.get_sample_prompts_count(True) < 5 or True:
					t1 = self.sql_mgr.get_sample_prompts_last_updated()
					t2 = self.fb_mgr.get_sample_prompts_last_updated()
					print(f"Checking sample prompts local {t1} ({date_from_timestamp(t1)}) vs remote {t2} ({date_from_timestamp(t2)})")
					if t2 > t1:
						prompts = self.fb_mgr.get_sample_prompts(t1)
						print(f"Checking prompts.... found {len(prompts)}")
						for p in prompts:
							self.sql_mgr.append_sample_prompt(t2, p)
						self.sql_mgr.clean_sample_prompts()

				# ------------------------------ Conversation updates  -----------------------------------------
				d2 = self.fb_mgr.get_conversation_toc_last_updated()
				if self.sync_conversations and self.fb_mgr.is_functional:
					d1 = self.sql_mgr.get_conversations_last_updated(self.user_id)
					print(f"Comparing conversation table dates local {d1} ({date_from_timestamp(d1)}), remote {d2} ({date_from_timestamp(d2)})")
					if d1 != d2:
						fbConversations = self.fb_mgr.get_conversation_toc()
						sqlConversations = list(self.sql_mgr.get_all_conversations(self.user_id))
						messagesFB = []
						messagesSQL = []
						found = False
						print(f"Firebase conversations: {len(fbConversations)}")
						print(f"SQL conversations: {len(sqlConversations)}")

						# ------------------------------ Part I deletions  -----------------------------------------
						if self.fb_mgr.is_functional:
							fbDeletedConversations = self.fb_mgr.get_deleted_conversations()
							sqlDeletedConversations = self.sql_mgr.get_deleted_conversations(self.user_id)
							print(f"Begin clearing deleted conversations from Firebase...{len(sqlDeletedConversations)}")
							conversationUpdates = 0
							for c in fbConversations: 
								if c.conversationID in sqlDeletedConversations:
									print(f"Deleting {c.conversationID} from Firebase")
									self.fb_mgr.delete_conversation(c.conversationID)
									fbConversations.remove(c)
									conversationUpdates += 1
							if conversationUpdates > 0:
								self.fb_mgr.save_deleted_conversations(sqlDeletedConversations)
								print(f"Deleted {conversationUpdates} FireBase conversations")

							print("Begin clearing deleted conversations from SQL...")
							conversationUpdates = 0
							for c in sqlConversations:
								if c.conversationID in fbDeletedConversations:
									print(f"Deleting {c.conversationID} from SQL")
									self.fb_mgr.delete_conversation(c.conversationID)
									sqlConversations.remove(c)
									conversationUpdates += 1
							if conversationUpdates > 0:
								print(f"Deleted {conversationUpdates} SQL conversations")

						# ------------------------------ Part II Sync changes up to Firebase  -----------------------------------------
						if sync_conversations_up and self.fb_mgr.is_functional:
							print("Begin conversation sync up to Firebase...")
							conversationUpdates = 0
							for c in sqlConversations:
								found = False
								for cc in fbConversations:
									if c.conversationID == cc.conversationID:
										found = True
										if c.dateModified != cc.dateModified:
											fbConv, messagesFB = self.fb_mgr.get_conversation(c.conversationID)  # More complete conversation than the TOC provides, use instead of cc
											if len(messagesFB) == 0:
												print("Zero messages returned from getMessagesFirebase")  # retrieval may have just failed so don't do anything
											else:
												messagesSQL = list(self.sql_mgr.get_messages(c.conversationID))
												messagesSQL.sort(key=lambda x: x.timeStamp)
												messagesFB.sort(key=lambda x: x.timeStamp)
												sqlSet = set(map(lambda x: x.timeStamp, messagesSQL))
												fbSet = set(map(lambda x: x.timeStamp, messagesFB))
												if c.dateModified > cc.dateModified:
													print("Conversation found but SQL is newer, update Firebase version...")
													self.fb_mgr.save_conversation(c, messagesSQL)
													conversationUpdates += 1
												else:
													print("Conversation found but Firebase is newer, update SQL version...")
													for message in messagesSQL:
														if message.timeStamp not in fbSet:
															self.sql_mgr.delete_message(message)
															messagesSQL.remove(message)
															messageUpdates += 1
													for message in messagesFB:
														if message.timeStamp not in sqlSet:
															self.sql_mgr.append_message(fbConv, message)
															messagesSQL.append(message)
															messageUpdates += 1
													self.sql_mgr.update_conversation_dates(fbConv)
													conversationUpdates += 1
										break  # Conversation already found, no need to continue searching

								if not found:
									conversationUpdates += 1
									messagesSQL = list(self.sql_mgr.get_messages(c.conversationID))
									if len(messagesSQL) == 0:
										print(f"Deleting empty conversation from SQL... {c.conversationID}")
										self.sql_mgr.delete_conversation(c.conversationID)
									else:
										print(f"Appending missing conversation {c.conversationID} to Firebase...")
										c.saved = True
										c.userID = self.user_id
										self.fb_mgr.save_conversation(c, messagesSQL)

							print(f"SyncUp updates: {conversationUpdates}: {messageUpdates}")
							if conversationUpdates > 0:
								TOCRefreshNeeded = True

						# ------------------------------ Part III Sync changes down from Firebase  -----------------------------------------
						if sync_conversations_down and self.fb_mgr.is_functional:
							print("Begin database sync down from Firebase...")
							conversationUpdates = 0
							messageUpdates = 0
							for c in fbConversations:
								found = False
								for cc in sqlConversations:
									if c.conversationID == cc.conversationID:
										found = True
										break  # Conversation already found, no need to continue searching

								if not found:
									conversationUpdates += 1
									fbConv, messagesFB = self.fb_mgr.get_conversation(c.conversationID) # More complete conversation than the TOC provides, use instead of c
									if len(messagesFB) == 0:
										print(f"Empty conversation found in Firebase... {c.conversationID}")
									else:
										print(f"Appending missing conversation {c.conversationID} aka {fbConv.conversationID} to SQL...")
										fbConv.saved = True
										fbConv.userID = self.user_id
										sqlConversations.append(fbConv)
										self.sql_mgr.save_conversation(fbConv)
										for m in messagesFB:
											self.sql_mgr.append_message(fbConv, m)

							print(f"SyncDown updates: {conversationUpdates}: {messageUpdates}")
							if conversationUpdates > 0:
								TOCRefreshNeeded = True

						if TOCRefreshNeeded and self.fb_mgr.is_functional:
							sqlConversations = list(self.sql_mgr.get_all_conversations(self.user_id))
							print("Updating Firebase TOC")
							self.fb_mgr.make_conversation_toc(sqlConversations)

				print("Database sync completed")
				self.last_synced = datetime.now().timestamp() * 1000
				#self.fb_mgr.update_last_synced()
				self.sync_needed = False
				self.sync_in_progress = False
