import pyodbc
from _classes.DataClasses import *
from _classes.Constants import *

class SQLManager:
	_instance = None
	is_initialized = False
	conn = None
	cursor = None
	
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		DatabaseServer = "localhost"
		DatabaseName = "ChatDatabase"
		if self.conn == None: self.is_initialized = False
		if not self.is_initialized:
			print("Initializing SQL")
			conn_str = 'DRIVER={SQL Server Native Client 11.0};SERVER=' + DatabaseServer + ';DATABASE=' + DatabaseName
			conn_str += ';Trusted_Connection=yes;' #';Integrated Security=true;'
			self.conn = pyodbc.connect(conn_str)
			self.cursor = self.conn.cursor()
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
		self.cursor.execute(CREATE_CONVERSATION_TABLE)
		self.cursor.execute(CREATE_CONVERSATION_DELETED_TABLE)
		self.cursor.execute(CREATE_MESSAGES_TABLE)
		self.cursor.execute(CREATE_USAGE_TABLE)
		self.cursor.execute(CREATE_SAMPLEPROMPTS_TABLE)
		self.conn.commit()

	def recreate_database(self):
		self.cursor.execute(f"DROP TABLE IF EXISTS {ConversationTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {DeletionsTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {MessageTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {UsageTableName}")
		self.cursor.execute(f"DROP TABLE IF EXISTS {SamplePromptTableName}")
		self.create_tables()

	def apply_updates(self):
		self.cursor.execute(f"DROP TABLE IF EXISTS {SamplePromptTableName}")
		self.cursor.execute(self.CREATE_SAMPLEPROMPTS_TABLE)
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
		self.cursor.execute(f"SELECT MAX(dateModified) AS maxTimeStamp FROM {ConversationTableName} WHERE userID='{user_id}'")
		row = self.cursor.fetchone()
		max_time_stamp = row.maxTimeStamp if row.maxTimeStamp else 0
		return max_time_stamp

	def update_conversation_dates(self, conversation):
		sql = f"UPDATE {ConversationTableName} SET dateCreated = {timestamp_from_date(conversation.dateCreated)}, dateAccessed = {timestamp_from_date(conversation.dateAccessed)}, dateModified = {timestamp_from_date(conversation.dateModified)} WHERE conversationID = {conversation.conversationID}" 
		self.cursor.execute(sql)
		self.conn.commit()

	def save_conversation(self, conversation):
		sql = f"INSERT INTO {ConversationTableName} (conversationID, title, summary, saved, userID) VALUES (?,?,?,?,?)"
		values = (conversation.conversationID, conversation.title, conversation.summary, 1 if conversation.saved else 0, conversation.userID)
		print(sql, values)
		self.cursor.execute(sql, values)
		self.update_conversation_dates(conversation)

	def delete_conversation(self, conversation_id):
		self.cursor.execute(f"DELETE FROM {ConversationTableName} WHERE conversationID={conversation_id}")
		self.cursor.execute(f"DELETE FROM {MessageTableName} WHERE conversationID={conversation_id}")
		self.cursor.execute(f"INSERT INTO {DeletionsTableName} (conversationID) VALUES ({conversation_id})")
		self.conn.commit()

	def get_deleted_conversations(self, user_id):
		result = []
		try:
			self.cursor.execute(f"SELECT conversationID FROM {DeletionsTableName} WHERE userID='{user_id}'")
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
		try:
			self.cursor.execute(f"SELECT * FROM {ConversationTableName} WHERE userID='{user_id}' ORDER BY dateModified DESC")
			rows = self.cursor.fetchall()
			for row in rows:
				conversation = self.cursor_to_conversation(row)
				conversations.append(conversation)
		except pyodbc.Error as e:
			print(f"Error: {e}")
		return conversations

	def get_conversation(self, conversation_id, user_id):
		conversation = None
		try:
			self.cursor.execute(f"SELECT * FROM {ConversationTableName} WHERE conversationID={conversation_id} AND userID='{user_id}'")
			row = self.cursor.fetchone()
			if row:
				conversation = self.cursor_to_conversation(row)
				conversation.saved = True
				time_stamp = get_current_timestamp()
				sql = f"UPDATE {ConversationTableName} SET dateAccessed={time_stamp} WHERE conversationID={conversation.conversationID}"
				self.cursor.execute(sql)
				self.conn.commit()
		except pyodbc.Error as e:
			print(f"Error: {e}")
		return conversation

	def update_conversation_modified(self, conversation):
		conversation.dateModified = get_current_date()
		self.update_conversation_dates(conversation)

	def cursor_to_chat_message(self, cursor):
		conversation_id = cursor.conversationID
		role = cursor.role
		content = cursor.content.strip()
		timestamp = cursor.timeStamp
		return ChatMessageExtended(conversation_id, role, content, timestamp)

	def append_message(self, conversation, chat_message):
		try:
			self.cursor.execute(f"INSERT INTO {MessageTableName} (conversationID, role, content, timeStamp) VALUES (?, ?, ?, ?)",
				(chat_message.conversationID, chat_message.role, chat_message.content, chat_message.timeStamp))
			self.conn.commit()
			#self.update_conversation_dates(conversation) #handle in storage manager
		except pyodbc.Error as e:
			print(f"Error: {e}")

	def delete_message(self, message):
		try:
			self.cursor.execute(f"DELETE FROM {MessageTableName} WHERE conversationID=? AND timeStamp=?",  (message.conversationID, message.timeStamp))
			self.conn.commit()
			print("Message deletion succeeded")
		except pyodbc.Error as e:
			print(f"Message deletion failed: {e}")

	def get_messages(self, conversation_id):
		chat_messages = []
		try:
			self.cursor.execute(f"SELECT * FROM {MessageTableName} WHERE conversationID=? ORDER BY timeStamp", (conversation_id,))
			rows = self.cursor.fetchall()
			for row in rows:
				chat_message = self.cursor_to_chat_message(row)
				chat_messages.append(chat_message)
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
		try:
			self.cursor.execute(f"SELECT MAX(timeStamp) AS maxTimeStamp FROM {UsageTableName} WHERE userID=? AND androidID=?", (user_id, android_id))
			row = self.cursor.fetchone()
			max_time_stamp = row.maxTimeStamp if row.maxTimeStamp else 0
			return max_time_stamp 
		except pyodbc.Error as e:
			print(f"Error: {e}")
			return 0

	def append_usage(self, usage):
		try:
			self.cursor.execute(f"""
				INSERT INTO {UsageTableName} 
				(conversationID, promptTokens, completionTokens, totalTokens, androidID, userID, timeStamp) 
				VALUES (?, ?, ?, ?, ?, ?, ?)
			""", (usage.conversationID, usage.promptTokens, usage.completionTokens, usage.totalTokens, usage.androidID, usage.userID, usage.timeStamp))
			self.conn.commit()
		except pyodbc.Error as e:
			print(f"Error: {e}")

	def get_sample_prompt(self, activity_name, unused=False):
		result = SamplePrompt()
		sql = f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE activityName='{activity_name}' ORDER BY NEWID() OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY"
		if unused:
			sql = f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE activityName='{activity_name}' and used=0 ORDER BY NEWID() OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY"
		try:
			self.cursor.execute(sql)
			row = self.cursor.fetchone()
			if row:
				activity_name = row.activityName
				prompt = row.prompt
				result = SamplePrompt(activity_name, prompt)
				self.cursor.execute(f"UPDATE {SamplePromptTableName} SET used=1 WHERE activityName='{activity_name}' and prompt='{prompt}'")
				self.conn.commit()
		except pyodbc.Error as e:
			print(f"Error: {e}")
			print("Error getting sample prompts, regenerating table...")
			# Assuming dbHelper.applyUpdates(database) performs necessary updates

		return result

	def reuse_sample_prompts(self):
		try:
			self.cursor.execute(f"UPDATE {SamplePromptTableName} SET used=0")
			self.conn.commit()
		except pyodbc.Error as e:
			print(f"Error: {e}")

	def get_sample_prompts(self, cutoff, unused=False):
		result = []
		sql = f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE timeStamp>{cutoff} ORDER BY timeStamp"
		if unused:
			sql = f"SELECT activityName, prompt FROM {SamplePromptTableName} WHERE timeStamp>{cutoff} and used=0 ORDER BY timeStamp"
		try:
			self.cursor.execute(sql)
			rows = self.cursor.fetchall()
			for row in rows:
				activity_name = row.activityName
				prompt = row.prompt
				result.append(SamplePrompt(activity_name, prompt))
		except pyodbc.Error as e:
			print(f"Error: {e}")
		return result

	def clean_sample_prompts(self):
		self.cursor.execute(f"SELECT prompt, timeStamp FROM {SamplePromptTableName} ORDER BY prompt, timeStamp DESC")
		p1 = ""
		p2 = ""
		ts = 0
		rows = self.cursor.fetchall()
		for row in rows:
			p2 = row.prompt
			ts = row.timeStamp
			if p1 == p2:
				p2 = p2.replace("'", "''")
				sql = f"DELETE FROM {SamplePromptTableName} WHERE prompt='{p2}' AND timeStamp={ts}"
				self.cursor.execute(sql)
				self.conn.commit()
			p1 = p2

	def append_sample_prompt(self, time_stamp, prompt):
		try:
			self.cursor.execute(f"""
				INSERT INTO {SamplePromptTableName} (activityName, prompt, used, timeStamp) 
				VALUES (?, ?, ?, ?)
			""", (prompt.activityName, prompt.prompt, 0, time_stamp))
			self.conn.commit()
			print(f"Added sample prompt to SQL: {prompt.prompt}")
		except pyodbc.Error as e:
			print(f"Error: {e}")
			print(f"Error writing prompt to SQL: {e}")

	def get_sample_prompts_last_updated(self):
		try:
			self.cursor.execute(f"SELECT MAX(timeStamp) AS maxTimeStamp FROM {SamplePromptTableName}")
			row = self.cursor.fetchone()
			max_time_stamp = row.maxTimeStamp if row.maxTimeStamp else 0
			return max_time_stamp
		except pyodbc.Error as e:
			print(f"Error: {e}")
			return 0

	def get_sample_prompts_count(self, unused=False):
		sql = f"SELECT COUNT(prompt) AS promptCount FROM {SamplePromptTableName}"
		if unused:
			sql = f"SELECT COUNT(prompt) AS promptCount FROM {SamplePromptTableName} WHERE used=0"
		try:
			self.cursor.execute(sql)
			row = self.cursor.fetchone()
			result = row.promptCount if row.promptCount else 0
			return result
		except pyodbc.Error as e:
			print(f"Error: {e}")
			return 0

	def apply_fixes(self, user_id, android_id):
		print("Applying database fixes...")
		self.cursor.execute(f"UPDATE {ConversationTableName} SET userID=? WHERE userID=''", user_id)
		self.cursor.execute(f"UPDATE {UsageTableName} SET userID=? WHERE userID=''", user_id)		
		self.clean_sample_prompts()
		try:
			self.cursor.execute(f"SELECT * FROM {MessageTableName}")
			rows = cursor.fetchall()
			for row in rows:
				conversation_id = row.conversationID
				timestamp = row.timeStamp
				content = row.content
				q2 = format_prompt_pretty_like(content)
				if q2 != content:
					self.cursor.execute(f"UPDATE {MessageTableName} SET content=? WHERE conversationID=? AND timeStamp=?", q2, conversation_id, timestamp)
					self.cursor.execute(f"UPDATE {ConversationTableName} SET dateModified=? WHERE conversationID=?", get_current_timestamp(), conversation_id)
			self.cursor.execute(f"SELECT * FROM {MessageTableName} WHERE role=?", 'user')
			rows = cursor.fetchall()
			for row in rows:
				conversation_id = row.conversationID
				timestamp = row.timeStamp
				content = row.content
				q2 = format_prompt_pretty_like(content)
				if q2 != content:
					self.cursor.execute(f"UPDATE {MessageTableName} SET content=? WHERE conversationID=? AND timeStamp=?",  q2, conversation_id, timestamp)
					self.cursor.execute(f"UPDATE {ConversationTableName} SET dateModified=? WHERE conversationID=?",  get_current_timestamp(), conversation_id)

			if android_id:
				self.cursor.execute(f"UPDATE {UsageTableName} SET androidID=? WHERE androidID=''", android_id)

			print("Applying database fixes complete")
		except pyodbc.Error as e:
			print(f"Error: {e}")

