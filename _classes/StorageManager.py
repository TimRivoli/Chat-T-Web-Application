from _classes.Constants import firebase_user_ID
from _classes.DataClasses import *
from _classes.SQLManager import SQLManager
from _classes.FirebaseManager import FirebaseManager
import threading

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
	webClientID = ""
	sync_cooldown = 83333  # milliseconds = 5 min
	sync_status = "Idle"
	sql_mgr = None
	fb_mgr = None

	def __init__(self):
		print("Initializing StorageManager")
		if not self.sql_mgr or not self.fb_mgr:
			print("Initializing SQL and Firebase Managers...")
			self.sql_mgr = SQLManager()
			self.fb_mgr = FirebaseManager()
			#self.fb_mgr.initialize(self.use_google_auth)
			#self.download_registered_device_settings()
			if self.subscription_level > 0:
				thread = threading.Thread(target=self.sync_databases, daemon=True)
				thread.start()

	def shut_down(self):
		self.sql_mgr.shut_down()
		self.sql_mgr = None

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
		if conversation:
			conversation.dateAccessed = get_current_date()
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
		self.sql_mgr.touch_conversation(message.conversationID)

#---------------------------------------------------------------- Notes ------------------------------------------------------

	def get_notes(self, categoryID=-1, search_string=""):
		return self.sql_mgr.get_notes(categoryID, search_string)

	def get_note(self, noteID):
		note = self.sql_mgr.get_note(noteID)
		note.dateAccessed =  get_current_date() # Update here rather than sqLiteManager to differentiate admin operations (sync) from user operations
		self.sql_mgr.update_note_dates(note)
		return note

	def save_note(self, note):
		print("Saving note:", note.noteID)
		sync_needed = True
		note.dateModified = get_current_date()
		note.dateAccessed = get_current_date()
		self.sql_mgr.save_note(note)

	def delete_note(self, noteID):
		sync_needed = True
		self.sql_mgr.delete_note(noteID)

	def get_note_category_id(self, category_name=""):
		return self.sql_mgr.get_note_category_id(category_name)

	def get_note_category_name(self, category_id):
		return self.sql_mgr.get_note_category_name(category_id)

	def get_note_categories(self):
		return self.sql_mgr.get_note_categories()

	def get_note_category_objects(self):
		return self.sql_mgr.get_note_category_objects()

	def create_note_category(self, categoryName):
		sync_needed = True
		self.sql_mgr.create_note_category(categoryName)

	def delete_note_category(self, categoryID):
		sync_needed = True
		self.sql_mgr.delete_note_category(categoryID)

#---------------------------------------------------------------- Prices Working Set ------------------------------------------------------

	def get_prices_working_set(self):
		return self.sql_mgr.get_prices_working_set()

	def get_price_working_set_entry(self, ticker):
		return self.sql_mgr.get_price_working_set_entry(ticker)

	def save_price_working_set_entry(self, entry):
		self.sync_needed = True
		self.sql_mgr.save_price_working_set_entry(entry)

#---------------------------------------------------------------- Usage ------------------------------------------------------
	def append_usage(self, usage):
		usage.userID = self.user_id
		usage.androidID = self.android_id
		self.sql_mgr.append_usage(usage)

	def get_sample_prompt(self, activityName):
		return self.sql_mgr.get_sample_prompt(activityName)

	def append_sample_prompt(self, prompt):
		self.sql_mgr.append_sample_prompt(prompt)

#------------------------------------------------------------------- Sync ------------------------------------------------------
	def sync_note_categories(self):
		fb_categories = self.fb_mgr.get_note_categories()
		sql_categories = self.sql_mgr.get_note_category_objects()
		sql_ids = {c.categoryID for c in sql_categories}
		fb_ids = {c.categoryID for c in fb_categories}
		changed = False
		for c in fb_categories:
			if c.categoryID not in sql_ids:
				print(f"Adding category from Firebase to SQL: {c.categoryID} {c.categoryName}")
				self.sql_mgr.create_note_category(c.categoryName, c.categoryID)
				self.sql_mgr.note_categories = []
				changed = True
		for c in sql_categories:
			if c.categoryID not in fb_ids:
				changed = True
		if changed or len(fb_categories) == 0:
			sql_categories = self.sql_mgr.get_note_category_objects()
			print(f"Updating Firebase note categories: {len(sql_categories)}")
			self.fb_mgr.save_note_categories(sql_categories)

	def sync_notes(self):
		self.sync_note_categories()
		updates = 0
		deletions = 0
		additions = 0
		fb_note_last_updated = self.fb_mgr.get_notes_toc_last_updated()
		sql_notes_last_updated = self.sql_mgr.get_notes_last_updated()
		print(f"Comparing notes table dates local {sql_notes_last_updated} , remote {fb_note_last_updated}")
		print(f"Comparing notes table dates local {sql_notes_last_updated} ({date_from_timestamp(sql_notes_last_updated)}), remote {fb_note_last_updated} ({date_from_timestamp(fb_note_last_updated)})")
		fb_notes = self.fb_mgr.get_notes_toc()
		if sql_notes_last_updated != fb_note_last_updated:
			print("Notes sync needed")
			sql_notes = self.sql_mgr.get_notes()
			print("Firebase notes: ", len(fb_notes))
			print("SQL notes", len(sql_notes))

			#if len(sql_notes) < 10: assert(False)
			# Sync deletions
			print(" Deleting SQL notes... found in deletions collection...")
			deleted_items = self.fb_mgr.get_deleted_notes()
			for n in sql_notes:
				if n.noteID in deleted_items:
					self.sql_mgr.delete_note(n.noteID)
					print(f"Deleting {n.noteID}")
					n.noteID = -1
					deletions += 1

			print(" Deleting firebase notes... found in deletions collection...")
			deleted_items = self.sql_mgr.get_deleted_notes()
			for n in fb_notes:
				if n.noteID in deleted_items:
					self.fb_mgr.delete_note(n.noteID)
					print(f"Deleting {n.noteID}")
					n.noteID = -1
					deletions += 1
			self.fb_mgr.save_deleted_notes(deleted_items)

			# Sync matches
			print(" Synchronizing matched items")
			note_ids = [n.noteID for n in fb_notes]
			for n in sql_notes:
				if n.noteID > 0 and n.noteID in note_ids:
					for nn in fb_notes:
						if n.noteID == nn.noteID:
							print(f"FB: {nn.dateModified} vs SQL: {n.dateModified}")
							if nn.dateModified > n.dateModified:
								found_note = self.fb_mgr.get_note(n.noteID)
								print(f" Firebase is newer, save to SQL {n.noteID}: {n.title}")
								print(f"{found_note.dateModified}")
								self.sql_mgr.save_note(found_note)
								updates += 1
							elif nn.dateModified < n.dateModified:
								print(f" SQL is newer, save to Firebase {n.noteID}: {n.title}")
								self.fb_mgr.save_note(n)
								updates += 1

			# Sync missing up
			print(" Synchronizing missing notes up to Firebase")
			for n in sql_notes:
				if n.noteID > 0 and n.noteID not in note_ids:
					print(f" Saving to Firebase {n.noteID}: {n.title}")
					self.fb_mgr.save_note(n)
					additions += 1

			# Sync missing down
			print(" Synchronizing missing notes down to SQL")
			note_ids = [n.noteID for n in sql_notes]
			for n in fb_notes:
				if n.noteID > 0 and n.noteID not in note_ids:
					found_note = self.fb_mgr.get_note(n.noteID)
					print(f" Saving to SQL {found_note.noteID}: {found_note.title}")
					if found_note.noteID != n.noteID: assert(False)
						
					self.sql_mgr.save_note(found_note)
					additions += 1

			if additions + updates > 0 and self.fb_mgr.is_functional:
				sql_notes = self.sql_mgr.get_notes()
				print("Updating Firebase Notes TOC")
				self.fb_mgr.make_notes_toc(sql_notes)

		print(f"Sync Notes Completed. Additions: {additions} Updates: {updates}  Deletions: {deletions}")

	def sync_prices_working_set(self):
		updates = 0
		additions = 0
		fb_last_updated = self.fb_mgr.get_prices_working_set_toc_last_updated()
		sql_last_updated = self.sql_mgr.get_prices_working_set_last_updated()
		print(f"Comparing prices_working_set dates local {sql_last_updated}, remote {fb_last_updated}")
		fb_entries = self.fb_mgr.get_prices_working_set_toc()
		if sql_last_updated != fb_last_updated:
			print("Prices working set sync needed")
			sql_entries = self.sql_mgr.get_prices_working_set()
			print(f"Firebase entries: {len(fb_entries)}")
			print(f"SQL entries: {len(sql_entries)}")

			# Sync matches
			print(" Synchronizing matched items")
			fb_tickers = [e.Ticker for e in fb_entries]
			for e in sql_entries:
				if e.Ticker and e.Ticker in fb_tickers:
					for fe in fb_entries:
						if e.Ticker == fe.Ticker:
							sql_ts = timestamp_from_date(e.LatestEntry)
							fb_ts = timestamp_from_date(fe.LatestEntry)
							if fb_ts > sql_ts:
								found_entry = self.fb_mgr.get_price_working_set_entry(e.Ticker)
								print(f" Firebase is newer, save to SQL: {e.Ticker}")
								self.sql_mgr.save_price_working_set_entry(found_entry)
								updates += 1
							elif fb_ts < sql_ts:
								print(f" SQL is newer, save to Firebase: {e.Ticker}")
								self.fb_mgr.save_price_working_set_entry(e)
								updates += 1
							break

			# Sync missing up
			print(" Synchronizing missing entries up to Firebase")
			for e in sql_entries:
				if e.Ticker and e.Ticker not in fb_tickers:
					print(f" Saving to Firebase: {e.Ticker}")
					self.fb_mgr.save_price_working_set_entry(e)
					additions += 1

			# Sync missing down
			print(" Synchronizing missing entries down to SQL")
			sql_tickers = [e.Ticker for e in sql_entries]
			for fe in fb_entries:
				if fe.Ticker and fe.Ticker not in sql_tickers:
					found_entry = self.fb_mgr.get_price_working_set_entry(fe.Ticker)
					print(f" Saving to SQL: {found_entry.Ticker}")
					self.sql_mgr.save_price_working_set_entry(found_entry)
					additions += 1

			if additions + updates > 0 and self.fb_mgr.is_functional:
				sql_entries = self.sql_mgr.get_prices_working_set()
				print("Updating Firebase Prices Working Set TOC")
				self.fb_mgr.make_prices_working_set_toc(sql_entries)

		print(f"Sync Prices Working Set Completed. Additions: {additions} Updates: {updates}")

	def sync_databases(self):
		sync_conversations_down = self.sync_conversations
		sync_conversations_up = self.sync_conversations
		TOCRefreshNeeded = False		
		timeSinceLastSync = get_current_timestamp() - self.last_synced
		print(" Checking if sync needed...")
		#self.sql_mgr.apply_updates()
		if self.fb_mgr.is_functional and not self.sync_in_progress:
			if not self.sync_needed or timeSinceLastSync <= self.sync_cooldown:
				print(f"Sync is not needed or on cooldown. Needed: {self.sync_needed} Cooldown: {timeSinceLastSync}")
			else:
				print(" Running database sync...")
				self.sync_in_progress = True
				self.sync_status = "Syncing..."
				conversationUpdates = 0
				messageUpdates = 0
				usageUpdates = 0

				# ------------------------------ Usage update -----------------------------------------
				if self.sync_usage:
					print("Uploading usage to Firebase...")
					usages = self.sql_mgr.getUsage(self.user_id, self.android_id)
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
				self.sync_status = "Syncing conversations..."
				d2 = self.fb_mgr.get_conversation_toc_last_updated()
				if self.sync_conversations and self.fb_mgr.is_functional:
					d1 = self.sql_mgr.get_conversations_last_updated(self.user_id)
					print(f"Comparing conversation table dates local {d1} ({date_from_timestamp(d1)}), remote {d2} ({date_from_timestamp(d2)})")
					fbConversations = self.fb_mgr.get_conversation_toc()
					if d1 != d2 and self.fb_mgr.is_functional:
						if (self.fb_mgr.encrypt_content and self.fb_mgr.encryption_pending):
								Print("Encryption is pending.  Setting fbConversations to empty list to trigger re-write.")
								fbConversations = []
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
						
				self.sync_status = "Syncing notes..."
				self.sync_notes()

				self.sync_status = "Syncing prices working set..."
				self.sync_prices_working_set()

				print("Database sync completed")
				self.last_synced = get_current_date()
				self.sync_needed = False
				self.sync_in_progress = False
				self.sync_status = "Idle"
