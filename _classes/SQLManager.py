import pyodbc, threading
from _classes.DataClasses import *
from _classes.Constants import *

class SQLManager:
	_instance = None
	is_initialized = False
	conn = None
	cursor = None
	note_categories = []
	_lock = None

	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		if self.conn is None: self.is_initialized = False
		if not self.is_initialized:
			print("Initializing SQL")
			conn_str = (
				f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={DatabaseServer};DATABASE={DatabaseName}'
				';Trusted_Connection=yes;TrustServerCertificate=yes;'
			)
			self.conn = pyodbc.connect(conn_str)
			self.cursor = self.conn.cursor()
			self._lock = threading.RLock()
			self.is_initialized = True

	def shut_down(self):
		self.cursor.close()
		self.conn.close()
		self.cursor = None
		self.conn = None
		self.is_initialized = False

	def create_tables(self):
		CREATE_CONVERSATION_TABLE = f"""
			IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{ConversationTableName}')
			BEGIN
				CREATE TABLE {ConversationTableName} (
					conversationID BIGINT PRIMARY KEY,
					dateCreated BIGINT,
					dateAccessed BIGINT,
					dateModified BIGINT,
					saved BIT,
					title NVARCHAR(300),
					summary NVARCHAR(3000),
					userID NVARCHAR(255),
					firebaseID NVARCHAR(255)
				);
			END;
		"""

		CREATE_CONVERSATION_DELETED_TABLE = f"""
			IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{DeletionsTableName}')
			BEGIN
				CREATE TABLE {DeletionsTableName} (
					conversationID BIGINT PRIMARY KEY,
					userID NVARCHAR(255)
				);
			END;
		"""

		CREATE_MESSAGES_TABLE = f"""
			IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{MessageTableName}')
			BEGIN
				CREATE TABLE {MessageTableName} (
					conversationID BIGINT,
					timeStamp BIGINT,
					role NVARCHAR(50),
					content NVARCHAR(MAX)
				);
			END;
		"""

		CREATE_USAGE_TABLE = f"""
		IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{UsageTableName}')
		BEGIN
			CREATE TABLE {UsageTableName} (
				conversationID BIGINT,
				timeStamp BIGINT,
				promptTokens INT,
				completionTokens INT,
				totalTokens INT,
				userID NVARCHAR(255),
				androidID NVARCHAR(255)
			);
		END;
		"""

		CREATE_SAMPLEPROMPTS_TABLE = f"""
		IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{SamplePromptTableName}')
		BEGIN
			CREATE TABLE {SamplePromptTableName} (
				activityName NVARCHAR(50),
				prompt NVARCHAR(500),
				used BIT,
				timeStamp BIGINT
			);
		END;
		"""
		
		CREATE_NOTES_TABLE = f"""
		IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{NotesTableName}')
		BEGIN
			CREATE TABLE notes (
				noteID BIGINT,
				categoryID INT,
				title NVARCHAR(255),
				content NVARCHAR(MAX),
				dateCreated BIGINT,
				dateModified BIGINT,
				dateAccessed BIGINT
			)
		END
		"""

		CREATE_NOTESCATEGORIES_TABLE = f"""
		IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{NotesCategoryTableName}')
		BEGIN
			CREATE TABLE {NotesCategoryTableName} (
				categoryID INT,
				categoryName TEXT
			)
		END
		"""

		CREATE_DEFAULT_NOTESCATEGORIES = f"""
			INSERT INTO {NotesCategoryTableName} (categoryID, categoryName)
			SELECT 0, 'General'
			WHERE NOT EXISTS (SELECT 1 FROM {NotesCategoryTableName} WHERE categoryID = 0)
		"""

		CREATE_NOTES_DELETED_TABLE = f"""
		IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{NotesDeletionsTableName}')
		BEGIN
			CREATE TABLE {NotesDeletionsTableName} (
				noteID INTEGER,
				timeStamp BIGINT
			)
		END
		"""

		for stmt in [
			CREATE_CONVERSATION_TABLE,
			CREATE_CONVERSATION_DELETED_TABLE,
			CREATE_MESSAGES_TABLE,
			CREATE_USAGE_TABLE,
			CREATE_SAMPLEPROMPTS_TABLE,
			CREATE_NOTES_TABLE,
			CREATE_NOTESCATEGORIES_TABLE,
			CREATE_DEFAULT_NOTESCATEGORIES,
			CREATE_NOTES_DELETED_TABLE,
		]:
			self.cursor.execute(stmt)
			self.conn.commit()

	def recreate_database(self):
		self.cursor.execute(f"DROP TABLE IF EXISTS {ConversationTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {DeletionsTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {MessageTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {UsageTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {SamplePromptTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {CREATE_NOTESCATEGORIES_TABLE}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {CREATE_NOTES_DELETED_TABLE}")
		self.create_tables()

	def apply_updates(self):
		self.create_tables()
		#self.cursor.execute(f"DROP TABLE IF EXISTS {SamplePromptTableName}")
		#self.cursor.execute(self.CREATE_SAMPLEPROMPTS_TABLE)
		self.conn.commit()
	
	def cursor_to_conversation(self, cursor):
		conversation_id = cursor.conversationID
		title = cursor.title.strip()
		summary = cursor.summary.strip()
		saved = cursor.saved == 1
		user_id = cursor.userID
		date_created = date_from_timestamp(cursor.dateCreated)
		date_accessed = date_from_timestamp(cursor.dateAccessed)
		date_modified = date_from_timestamp(cursor.dateModified)
		return Conversation(conversation_id, title, summary, saved, user_id, date_created, date_accessed, date_modified)

	def get_conversations_last_updated(self, user_id):
		with self._lock:
			self.cursor.execute(f"SELECT MAX(dateModified) AS maxTimeStamp FROM {ConversationTableName} WHERE userID=?", (user_id,))
			row = self.cursor.fetchone()
		return row.maxTimeStamp if row.maxTimeStamp else 0

	def update_conversation_dates(self, conversation):
		with self._lock:
			self.cursor.execute(
				f"UPDATE {ConversationTableName} SET dateCreated=?, dateAccessed=?, dateModified=? WHERE conversationID=?",
				(timestamp_from_date(conversation.dateCreated), timestamp_from_date(conversation.dateAccessed),
				 timestamp_from_date(conversation.dateModified), conversation.conversationID)
			)
			self.conn.commit()

	def save_conversation(self, conversation):
		with self._lock:
			sql = f"INSERT INTO {ConversationTableName} (conversationID, title, summary, saved, userID) VALUES (?,?,?,?,?)"
			values = (conversation.conversationID, conversation.title, conversation.summary, 1 if conversation.saved else 0, conversation.userID)
			print(sql, values)
			self.cursor.execute(sql, values)
		self.update_conversation_dates(conversation)

	def delete_conversation(self, conversation_id):
		with self._lock:
			self.cursor.execute(f"DELETE FROM {ConversationTableName} WHERE conversationID=?", (conversation_id,))
			self.cursor.execute(f"DELETE FROM {MessageTableName} WHERE conversationID=?", (conversation_id,))
			self.cursor.execute(f"INSERT INTO {DeletionsTableName} (conversationID) VALUES (?)", (conversation_id,))
			self.conn.commit()

	def get_deleted_conversations(self, user_id):
		result = []
		with self._lock:
			try:
				self.cursor.execute(f"SELECT conversationID FROM {DeletionsTableName} WHERE userID=?", (user_id,))
				rows = self.cursor.fetchall()
				for row in rows:
					result.append(row.conversationID)
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return result

	def cursor_to_conversation(self, cursor):
		# Assuming cursor is already positioned on the correct row
		conversation_id = cursor.conversationID
		title = cursor.title
		summary = cursor.summary
		saved = cursor.saved == 1
		user_id = cursor.userID
		date_created = date_from_timestamp(cursor.dateCreated)
		date_accessed = date_from_timestamp(cursor.dateAccessed)
		date_modified = date_from_timestamp(cursor.dateModified)
		return Conversation(conversation_id, title, summary, saved, user_id, date_created, date_accessed, date_modified)

	def get_all_conversations(self, user_id):
		conversations = []
		with self._lock:
			try:
				self.cursor.execute(f"SELECT * FROM {ConversationTableName} WHERE userID=? ORDER BY dateModified DESC", (user_id,))
				rows = self.cursor.fetchall()
				for row in rows:
					conversations.append(self.cursor_to_conversation(row))
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return conversations

	def get_conversation(self, conversation_id, user_id):
		conversation = None
		with self._lock:
			try:
				self.cursor.execute(
					f"SELECT * FROM {ConversationTableName} WHERE conversationID=? AND userID=?",
					(conversation_id, user_id)
				)
				row = self.cursor.fetchone()
				if row:
					conversation = self.cursor_to_conversation(row)
					conversation.saved = True
					self.cursor.execute(
						f"UPDATE {ConversationTableName} SET dateAccessed=? WHERE conversationID=?",
						(get_current_timestamp(), conversation.conversationID)
					)
					self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return conversation

	def update_conversation_modified(self, conversation):
		conversation.dateModified = get_current_date()
		self.update_conversation_dates(conversation)

	def touch_conversation(self, conversation_id):
		with self._lock:
			try:
				self.cursor.execute(
					f"UPDATE {ConversationTableName} SET dateModified=? WHERE conversationID=?",
					(get_current_timestamp(), conversation_id)
				)
				self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")

	def cursor_to_chat_message(self, cursor):
		conversation_id = cursor.conversationID
		role = cursor.role
		content = cursor.content.strip()
		timestamp = cursor.timeStamp
		return ChatMessageExtended(conversation_id, role, content, timestamp)

	def append_message(self, conversation, chat_message):
		with self._lock:
			try:
				self.cursor.execute(
					f"INSERT INTO {MessageTableName} (conversationID, role, content, timeStamp) VALUES (?, ?, ?, ?)",
					(chat_message.conversationID, chat_message.role, chat_message.content, chat_message.timeStamp)
				)
				self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")

	def delete_message(self, message):
		with self._lock:
			try:
				self.cursor.execute(
					f"DELETE FROM {MessageTableName} WHERE conversationID=? AND timeStamp=?",
					(message.conversationID, message.timeStamp)
				)
				self.conn.commit()
				print("Message deletion succeeded")
			except pyodbc.Error as e:
				print(f"Message deletion failed: {e}")

	def get_messages(self, conversation_id):
		chat_messages = []
		with self._lock:
			try:
				self.cursor.execute(f"SELECT * FROM {MessageTableName} WHERE conversationID=? ORDER BY timeStamp", (conversation_id,))
				rows = self.cursor.fetchall()
				for row in rows:
					chat_messages.append(self.cursor_to_chat_message(row))
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return chat_messages


	def cursor_to_usage(self, cursor):
		conversation_id = cursor.conversationID
		prompt_tokens = cursor.promptTokens
		completion_tokens = cursor.completionTokens
		total_tokens = cursor.totalTokens
		user_id = cursor.userID
		android_id = cursor.androidID
		time_stamp = cursor.timeStamp
		return ChatUsage(conversation_id, prompt_tokens, completion_tokens, total_tokens, user_id, android_id, time_stamp)

	def get_conversation_usage(self, conversation_id):
		result = 0
		with self._lock:
			try:
				self.cursor.execute(f"SELECT totalTokens FROM {UsageTableName} WHERE conversationID=?", (conversation_id,))
				rows = self.cursor.fetchall()
				for row in rows:
					result += row.totalTokens
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return result

	def get_usage(self, user_id, android_id):
		usage_list = []
		try:
			self.cursor.execute(f"SELECT * FROM {UsageTableName} WHERE userID=? AND androidID=?", (user_id, android_id))
			rows = self.cursor.fetchall()
			for row in rows:
				usage = self.cursor_to_usage(row)
				usage_list.append(usage)
		except pyodbc.Error as e:
			print(f"Error: {e}")
		return usage_list

	def get_usage_last_updated(self, user_id, android_id):
		with self._lock:
			try:
				self.cursor.execute(f"SELECT MAX(timeStamp) AS maxTimeStamp FROM {UsageTableName} WHERE userID=? AND androidID=?", (user_id, android_id))
				row = self.cursor.fetchone()
				return row.maxTimeStamp if row.maxTimeStamp else 0
			except pyodbc.Error as e:
				print(f"Error: {e}")
				return 0

	def append_usage(self, usage):
		with self._lock:
			try:
				self.cursor.execute(
					f"INSERT INTO {UsageTableName} (conversationID, promptTokens, completionTokens, totalTokens, androidID, userID, timeStamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
					(usage.conversationID, usage.promptTokens, usage.completionTokens, usage.totalTokens, usage.androidID, usage.userID, usage.timeStamp)
				)
				self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")

	def get_sample_prompt(self, activity_name, unused=False):
		result = SamplePrompt()
		with self._lock:
			try:
				if unused:
					self.cursor.execute(f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE activityName=? AND used=0 ORDER BY NEWID() OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY", (activity_name,))
				else:
					self.cursor.execute(f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE activityName=? ORDER BY NEWID() OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY", (activity_name,))
				row = self.cursor.fetchone()
				if row:
					result = SamplePrompt(row.activityName, row.prompt)
					self.cursor.execute(f"UPDATE {SamplePromptTableName} SET used=1 WHERE activityName=? AND prompt=?", (row.activityName, row.prompt))
					self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return result

	def reuse_sample_prompts(self):
		with self._lock:
			try:
				self.cursor.execute(f"UPDATE {SamplePromptTableName} SET used=0")
				self.conn.commit()
			except pyodbc.Error as e:
				print(f"Error: {e}")

	def get_sample_prompts(self, cutoff, unused=False):
		result = []
		with self._lock:
			try:
				if unused:
					self.cursor.execute(f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE timeStamp>? AND used=0 ORDER BY timeStamp", (cutoff,))
				else:
					self.cursor.execute(f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE timeStamp>? ORDER BY timeStamp", (cutoff,))
				rows = self.cursor.fetchall()
				for row in rows:
					result.append(SamplePrompt(row.activityName, row.prompt))
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return result

	def clean_sample_prompts(self):
		with self._lock:
			self.cursor.execute(f"SELECT prompt, timeStamp FROM {SamplePromptTableName} ORDER BY prompt, timeStamp DESC")
			rows = self.cursor.fetchall()
			p1 = ""
			for row in rows:
				p2 = row.prompt
				if p1 == p2:
					self.cursor.execute(f"DELETE FROM {SamplePromptTableName} WHERE prompt=? AND timeStamp=?", (p2, row.timeStamp))
					self.conn.commit()
				p1 = p2

	def append_sample_prompt(self, time_stamp, prompt):
		with self._lock:
			try:
				self.cursor.execute(
					f"INSERT INTO {SamplePromptTableName} (activityName, prompt, used, timeStamp) VALUES (?, ?, ?, ?)",
					(prompt.activityName, prompt.prompt, 0, time_stamp)
				)
				self.conn.commit()
				print(f"Added sample prompt to SQL: {prompt.prompt}")
			except pyodbc.Error as e:
				print(f"Error writing prompt to SQL: {e}")

	def get_sample_prompts_last_updated(self):
		with self._lock:
			try:
				self.cursor.execute(f"SELECT MAX(timeStamp) AS maxTimeStamp FROM {SamplePromptTableName}")
				row = self.cursor.fetchone()
				return row.maxTimeStamp if row.maxTimeStamp else 0
			except pyodbc.Error as e:
				print(f"Error: {e}")
				return 0

	def get_sample_prompts_count(self, unused=False):
		with self._lock:
			try:
				if unused:
					self.cursor.execute(f"SELECT COUNT(prompt) AS promptCount FROM {SamplePromptTableName} WHERE used=0")
				else:
					self.cursor.execute(f"SELECT COUNT(prompt) AS promptCount FROM {SamplePromptTableName}")
				row = self.cursor.fetchone()
				return row.promptCount if row.promptCount else 0
			except pyodbc.Error as e:
				print(f"Error: {e}")
				return 0
			
#--------------------------------------------------------------- Notes -------------------------------------------------------

	def cursor_to_note_entry(self,cursor):
		note_id = cursor.noteID
		category_id = cursor.categoryID
		category_name = self.get_note_category_name(category_id)
		title = cursor.title
		content = cursor.content
		date_created = date_from_timestamp(cursor.dateCreated)
		date_accessed = date_from_timestamp(cursor.dateAccessed)
		date_modified = date_from_timestamp(cursor.dateModified)
		return NoteEntry(note_id, category_id, category_name, title, content, date_created, date_accessed, date_modified)

	def cursor_to_note_category(self,cursor):
		category_id = cursor.categoryID
		category_name = cursor.categoryName
		return NoteCategory(category_id, category_name)

	def cache_note_categories(self):
		with self._lock:
			self.note_categories = []
			try:
				self.cursor.execute(f"SELECT categoryID, categoryName FROM {NotesCategoryTableName} ORDER BY categoryID")
				for row in self.cursor.fetchall():
					self.note_categories.append(self.cursor_to_note_category(row))
			except pyodbc.Error as e:
				print(f"Error: {e}")
		if len(self.note_categories) == 0:
			for c in [NoteCategory(0, 'General')]:
				self.create_note_category(c.categoryName, c.categoryID)

	def get_note_category_max_id(self):
		result = 0
		if len(self.note_categories) == 0:
			self.cache_note_categories()
		for c in self.note_categories:
			if c.categoryID > result:
				result = c.categoryID
		return result

	def get_note_category_id(self,category_name=""):
		result = -1
		if len(self.note_categories) == 0:
			self.cache_note_categories()
		for c in note_categories:
			if c.categoryName == category_name:
				result = c.categoryID
		return result

	def get_note_category_name(self, category_id):
		#print(f"searching for category_id {category_id}")
		result = ""
		if len(self.note_categories) == 0:
			self.cache_note_categories()
		for c in self.note_categories:
			if c.categoryID == category_id:
				result = c.categoryName
		#print(f"result {result}")
		return result
		
	def get_note_categories(self,include_any_option=False):
		if len(self.note_categories) == 0:
			self.cache_note_categories()
		result = []
		if include_any_option:
			result.append("Any")
		for c in self.note_categories:
			result.append(c.categoryName)
		return result

	def get_note_category_objects(self):
		if len(self.note_categories) == 0:
			self.cache_note_categories()
		return list(self.note_categories)

	def create_note_category(self, category_name, category_id=-1):
		new_category_id = category_id if category_id >= 0 else self.get_note_category_max_id() + 1
		with self._lock:
			try:
				self.cursor.execute(
					f"INSERT INTO {NotesCategoryTableName} (categoryID, categoryName) SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM {NotesCategoryTableName} WHERE categoryName=?)",
					(new_category_id, category_name, category_name)
				)
				self.conn.commit()
				print(f"Note category {category_name} created")
			except Exception as e:
				print(f"Note category {category_name} creation failed: {str(e)}")

	def delete_note_category(self, category_id, replacement_category_id=0):
		with self._lock:
			try:
				self.cursor.execute(f"UPDATE {NotesTableName} SET CategoryID=? WHERE categoryID=?", (replacement_category_id, category_id))
				self.cursor.execute(f"DELETE FROM {NotesCategoryTableName} WHERE categoryID=?", (category_id,))
				self.conn.commit()
				print(f"Note category {category_id} deletion succeeded")
			except Exception as e:
				print(f"Note category {category_id} deletion failed: {str(e)}")
	
	def get_notes(self, category_id=-1, searchString=""):
		notes = []
		conditions = []
		params = []
		if category_id >= 0:
			conditions.append("categoryID = ?")
			params.append(category_id)
		if searchString:
			conditions.append("(title LIKE ? OR content LIKE ?)")
			params.append(f'%{searchString}%')
			params.append(f'%{searchString}%')
		sql = f"SELECT noteID, categoryID, title, content, dateCreated, dateModified, dateAccessed FROM {NotesTableName}"
		if conditions:
			sql += " WHERE " + " AND ".join(conditions)
		sql += " ORDER BY dateModified DESC"
		print(f"SQL: {sql}")
		with self._lock:
			try:
				self.cursor.execute(sql, params)
				rows = self.cursor.fetchall()
				for row in rows:
					note = self.cursor_to_note_entry(row)
					notes.append(note)
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return notes


	def get_note(self, note_id):
		result = NoteEntry()
		with self._lock:
			try:
				self.cursor.execute(
					f"SELECT noteID, categoryID, title, content, dateCreated, dateModified, dateAccessed FROM {NotesTableName} WHERE noteID=?",
					(note_id,)
				)
				row = self.cursor.fetchone()
				if row:
					result = self.cursor_to_note_entry(row)
			except pyodbc.Error as e:
				print(e)
		if result.noteID == 0:
			result.noteID = get_current_timestamp()
		return result

	def save_note(self, note):
		print(f"Saving note to SQL {note.noteID}")
		if note.categoryName == "General":
			note.categoryID = 0
		with self._lock:
			self.cursor.execute(f"SELECT noteID FROM {NotesTableName} WHERE noteID=?", (note.noteID,))
			row = self.cursor.fetchone()
			if row:
				self.cursor.execute(
					f"UPDATE {NotesTableName} SET categoryid=?, title=?, content=? WHERE noteID=?",
					(note.categoryID, note.title, note.content, note.noteID)
				)
				print("SQL: Note updated successfully")
			else:
				self.cursor.execute(
					f"INSERT INTO {NotesTableName} (noteID, categoryid, title, content) VALUES (?, ?, ?, ?)",
					(note.noteID, note.categoryID, note.title, note.content)
				)
				print("SQL: Adding new note")
		self.update_note_dates(note)

	def update_note_dates(self, note):
		with self._lock:
			self.cursor.execute(
				f"UPDATE {NotesTableName} SET dateCreated=?, dateAccessed=?, dateModified=? WHERE noteID=?",
				(timestamp_from_date(note.dateCreated), timestamp_from_date(note.dateAccessed),
				 timestamp_from_date(note.dateModified), note.noteID)
			)
			self.conn.commit()

	def delete_note(self, noteID):
		with self._lock:
			try:
				self.cursor.execute(f"DELETE FROM {NotesTableName} WHERE noteID=?", (noteID,))
				self.cursor.execute(f"INSERT INTO {NotesDeletionsTableName} (noteID, timeStamp) VALUES (?, ?)", (noteID, get_current_timestamp()))
				self.conn.commit()
				print("Note deletion succeeded")
			except pyodbc.Error as e:
				print("Note deletion failed:", e)

	def get_deleted_notes(self):
		result = []
		with self._lock:
			try:
				self.cursor.execute(f"SELECT noteID FROM {NotesDeletionsTableName}")
				for row in self.cursor.fetchall():
					result.append(row.noteID)
			except pyodbc.Error as e:
				print(e)
		return result

	def get_notes_last_updated(self):
		with self._lock:
			self.cursor.execute(f"SELECT MAX(dateModified) AS maxTimeStamp FROM {NotesTableName}")
			ts1 = self.cursor.fetchone().maxTimeStamp or 0
			self.cursor.execute(f"SELECT MAX(timeStamp) AS maxTimeStamp FROM {NotesDeletionsTableName}")
			ts2 = self.cursor.fetchone().maxTimeStamp or 0
		return max(ts1, ts2)

#--------------------------------------------------------------- Prices Working Set -------------------------------------------------------

	def cursor_to_price_working_set_entry(self, cursor):
		entry = PriceWorkingSetEntry()
		entry.CompanyName = cursor.CompanyName or ""
		entry.Ticker = cursor.Ticker or ""
		entry.Sector = cursor.Sector or ""
		entry.SP500Listed = bool(cursor.SP500Listed)
		entry.CurrentPrice = float(cursor.CurrentPrice or 0.0)
		entry.Average_5Day = float(cursor.Average_5Day or 0.0)
		entry.Average_2Day = float(cursor.Average_2Day or 0.0)
		entry.PC_2Year = float(cursor.PC_2Year or 0.0)
		entry.PC_1Year = float(cursor.PC_1Year or 0.0)
		entry.PC_6Month = float(cursor.PC_6Month or 0.0)
		entry.PC_3Month = float(cursor.PC_3Month or 0.0)
		entry.PC_2Month = float(cursor.PC_2Month or 0.0)
		entry.PC_1Month = float(cursor.PC_1Month or 0.0)
		entry.PC_1Day = float(cursor.PC_1Day or 0.0)
		entry.Gain_Monthly = float(cursor.Gain_Monthly or 0.0)
		entry.LossStd_1Year = float(cursor.LossStd_1Year or 0.0)
		entry.Point_Value = int(cursor.Point_Value or 0)
		entry.TargetHoldings = float(cursor.TargetHoldings or 0.0)
		entry.Revenue = float(cursor.Revenue or 0.0)
		entry.NetIncome = float(cursor.NetIncome or 0.0)
		entry.CompanySize = int(cursor.CompanySize or 0)
		entry.MarketCap = float(cursor.MarketCap or 0.0)
		entry.OperatingExpense = float(cursor.OperatingExpense or 0.0)
		entry.NetProfitMargin = float(cursor.NetProfitMargin or 0.0)
		entry.EarningsPerShare = float(cursor.EarningsPerShare or 0.0)
		entry.CashShortTermInvestments = float(cursor.CashShortTermInvestments or 0.0)
		entry.TotalAssets = float(cursor.TotalAssets or 0.0)
		entry.TotalLiabilities = float(cursor.TotalLiabilities or 0.0)
		entry.NetWorth = float(cursor.NetWorth or 0.0)
		entry.TotalEquity = float(cursor.TotalEquity or 0.0)
		entry.SharesOutstanding = float(cursor.SharesOutstanding or 0.0)
		entry.PriceToBook = float(cursor.PriceToBook or 0.0)
		entry.ReturnOnAssetts = float(cursor.ReturnOnAssetts or 0.0)
		entry.ReturnOnCapital = float(cursor.ReturnOnCapital or 0.0)
		entry.CashFromOperations = float(cursor.CashFromOperations or 0.0)
		entry.CashFromInvesting = float(cursor.CashFromInvesting or 0.0)
		entry.CashFromFinancing = float(cursor.CashFromFinancing or 0.0)
		entry.NetChangeInCash = float(cursor.NetChangeInCash or 0.0)
		entry.FreeCashFlow = float(cursor.FreeCashFlow or 0.0)
		entry.Comments = cursor.Comments or ""
		entry.LatestEntry = cursor.latestEntry or get_current_date()
		return entry

	def get_prices_working_set(self):
		entries = []
		with self._lock:
			try:
				self.cursor.execute(f"SELECT * FROM {PricesWorkingSetTableName} ORDER BY Ticker")
				for row in self.cursor.fetchall():
					entries.append(self.cursor_to_price_working_set_entry(row))
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return entries

	def get_price_working_set_entry(self, ticker):
		result = PriceWorkingSetEntry()
		with self._lock:
			try:
				self.cursor.execute(f"SELECT * FROM {PricesWorkingSetTableName} WHERE Ticker=?", (ticker,))
				row = self.cursor.fetchone()
				if row:
					result = self.cursor_to_price_working_set_entry(row)
			except pyodbc.Error as e:
				print(f"Error: {e}")
		return result

	def save_price_working_set_entry(self, entry):
		print(f"Saving price working set entry to SQL: {entry.Ticker}")
		with self._lock:
			self.cursor.execute(f"SELECT Ticker FROM {PricesWorkingSetTableName} WHERE Ticker=?", (entry.Ticker,))
			row = self.cursor.fetchone()
			if row:
				self.cursor.execute(
					f"""UPDATE {PricesWorkingSetTableName} SET
						CompanyName=?, Sector=?, SP500Listed=?, CurrentPrice=?,
						Average_5Day=?, Average_2Day=?, PC_2Year=?, PC_1Year=?, PC_6Month=?,
						PC_3Month=?, PC_2Month=?, PC_1Month=?, PC_1Day=?,
						Gain_Monthly=?, LossStd_1Year=?, Point_Value=?, TargetHoldings=?,
						Revenue=?, NetIncome=?, CompanySize=?, MarketCap=?, OperatingExpense=?,
						NetProfitMargin=?, EarningsPerShare=?, CashShortTermInvestments=?,
						TotalAssets=?, TotalLiabilities=?, NetWorth=?, TotalEquity=?,
						SharesOutstanding=?, PriceToBook=?, ReturnOnAssetts=?, ReturnOnCapital=?,
						CashFromOperations=?, CashFromInvesting=?, CashFromFinancing=?,
						NetChangeInCash=?, FreeCashFlow=?, Comments=?, latestEntry=?
						WHERE Ticker=?""",
					(entry.CompanyName, entry.Sector, entry.SP500Listed, entry.CurrentPrice,
					 entry.Average_5Day, entry.Average_2Day, entry.PC_2Year, entry.PC_1Year, entry.PC_6Month,
					 entry.PC_3Month, entry.PC_2Month, entry.PC_1Month, entry.PC_1Day,
					 entry.Gain_Monthly, entry.LossStd_1Year, entry.Point_Value, entry.TargetHoldings,
					 entry.Revenue, entry.NetIncome, entry.CompanySize, entry.MarketCap, entry.OperatingExpense,
					 entry.NetProfitMargin, entry.EarningsPerShare, entry.CashShortTermInvestments,
					 entry.TotalAssets, entry.TotalLiabilities, entry.NetWorth, entry.TotalEquity,
					 entry.SharesOutstanding, entry.PriceToBook, entry.ReturnOnAssetts, entry.ReturnOnCapital,
					 entry.CashFromOperations, entry.CashFromInvesting, entry.CashFromFinancing,
					 entry.NetChangeInCash, entry.FreeCashFlow, entry.Comments, entry.LatestEntry,
					 entry.Ticker)
				)
				print("SQL: Price working set entry updated")
			else:
				self.cursor.execute(
					f"""INSERT INTO {PricesWorkingSetTableName}
						(CompanyName, Ticker, Sector, SP500Listed, CurrentPrice,
						Average_5Day, Average_2Day, PC_2Year, PC_1Year, PC_6Month,
						PC_3Month, PC_2Month, PC_1Month, PC_1Day,
						Gain_Monthly, LossStd_1Year, Point_Value, TargetHoldings,
						Revenue, NetIncome, CompanySize, MarketCap, OperatingExpense,
						NetProfitMargin, EarningsPerShare, CashShortTermInvestments,
						TotalAssets, TotalLiabilities, NetWorth, TotalEquity,
						SharesOutstanding, PriceToBook, ReturnOnAssetts, ReturnOnCapital,
						CashFromOperations, CashFromInvesting, CashFromFinancing,
						NetChangeInCash, FreeCashFlow, Comments, latestEntry)
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
					(entry.CompanyName, entry.Ticker, entry.Sector, entry.SP500Listed, entry.CurrentPrice,
					 entry.Average_5Day, entry.Average_2Day, entry.PC_2Year, entry.PC_1Year, entry.PC_6Month,
					 entry.PC_3Month, entry.PC_2Month, entry.PC_1Month, entry.PC_1Day,
					 entry.Gain_Monthly, entry.LossStd_1Year, entry.Point_Value, entry.TargetHoldings,
					 entry.Revenue, entry.NetIncome, entry.CompanySize, entry.MarketCap, entry.OperatingExpense,
					 entry.NetProfitMargin, entry.EarningsPerShare, entry.CashShortTermInvestments,
					 entry.TotalAssets, entry.TotalLiabilities, entry.NetWorth, entry.TotalEquity,
					 entry.SharesOutstanding, entry.PriceToBook, entry.ReturnOnAssetts, entry.ReturnOnCapital,
					 entry.CashFromOperations, entry.CashFromInvesting, entry.CashFromFinancing,
					 entry.NetChangeInCash, entry.FreeCashFlow, entry.Comments, entry.LatestEntry)
				)
				print("SQL: Added new price working set entry")
			self.conn.commit()

	def get_prices_working_set_last_updated(self):
		with self._lock:
			self.cursor.execute(f"SELECT MAX(latestEntry) AS maxEntry FROM {PricesWorkingSetTableName}")
			row = self.cursor.fetchone()
			return timestamp_from_date(row.maxEntry) if row.maxEntry else 0

#--------------------------------------------------------------- Database Maint -------------------------------------------------------

	def apply_fixes(self, user_id, android_id):
		print("Applying database fixes...")
		self.cursor.execute(f"UPDATE {ConversationTableName} SET userID=? WHERE userID=''", user_id)
		self.cursor.execute(f"UPDATE {UsageTableName} SET userID=? WHERE userID=''", user_id)		
		# self.clean_sample_prompts()
		# try:
			# self.cursor.execute(f"SELECT * FROM {MessageTableName}")
			# rows = cursor.fetchall()
			# for row in rows:
				# conversation_id = row.conversationID
				# timestamp = row.timeStamp
				# content = row.content
				# q2 = format_prompt_pretty_like(content)
				# if q2 != content:
					# self.cursor.execute(f"UPDATE {MessageTableName} SET content=? WHERE conversationID=? AND timeStamp=?", q2, conversation_id, timestamp)
					# self.cursor.execute(f"UPDATE {ConversationTableName} SET dateModified=? WHERE conversationID=?", get_current_timestamp(), conversation_id)
			# self.cursor.execute(f"SELECT * FROM {MessageTableName} WHERE role=?", 'user')
			# rows = cursor.fetchall()
			# for row in rows:
				# conversation_id = row.conversationID
				# timestamp = row.timeStamp
				# content = row.content
				# q2 = format_prompt_pretty_like(content)
				# if q2 != content:
					# self.cursor.execute(f"UPDATE {MessageTableName} SET content=? WHERE conversationID=? AND timeStamp=?",  q2, conversation_id, timestamp)
					# self.cursor.execute(f"UPDATE {ConversationTableName} SET dateModified=? WHERE conversationID=?",  get_current_timestamp(), conversation_id)

			# if android_id:
				# self.cursor.execute(f"UPDATE {UsageTableName} SET androidID=? WHERE androidID=''", android_id)

			# print("Applying database fixes complete")
		# except pyodbc.Error as e:
			# print(f"Error: {e}")

