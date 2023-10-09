import firebase_admin
from firebase_admin import credentials, auth, firestore
from _classes.Constants import *
from _classes.Utility import *
from _classes.DataClasses import *

class FirebaseManager:
	_instance = None
	is_initialized = False
	is_functional = True 
	device_id = "Webserver"
	android_id = "Webserver"
	user_id = firebase_user_ID
	root_id = ""
	usage_root_id = ""
	device_root_id = ""
	fs_database = None
	
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self):
		if not self.is_initialized:
			print("Initializing Firebase")
			self.initialize(True)
			self.is_initialized = True

	def initialize(self, use_google_auth):
		if use_google_auth:
			#val credential = GoogleAuthProvider.getCredential(idToken, null)
			#auth.signInWithCredential(credential)
			cred = credentials.Certificate(google_services)
			firebase_admin.initialize_app(cred)
			print(f"Firebase was authenticated automatically via Google")
		else:
			print("Firebase was not authenticated automatically...")
			print("Firebase: Logging anonymously...")
			firebase_admin.initialize_app()
			print(f"Firebase: Logged in anonymously")

		self.root_id = self.android_id
		self.device_root_id = f"{self.android_id}:{self.device_id}"
		self.usage_root_id = self.android_id
		if self.user_id !="":
			self.root_id = self.user_id
			self.usage_root_id += f":{self.user_id}"
		if self.is_functional:
			self.fs_database = firestore.client()
		self.is_initialized = self.is_functional
		
	#-------------------------------------------------- Firebase essential functions  --------------------------------------------------
	def generate_id(self, time_stamp=0, day_precision=False, base_id = ""):
		if base_id == "": base_id = self.root_id
		if time_stamp==0: time_stamp = get_current_timestamp()
		if day_precision: time_stamp = timestamp_trim_to_day(time_stamp)
		ts = str(time_stamp) 
		while len(ts) < 13:
			ts = "0" + ts
		return f"{base_id}:{ts}"

	def get_document_by_id(self, collection_name, document_id):
		document_ref = self.fs_database.collection(collection_name).document(document_id)
		try:
			return document_ref.get().to_dict()
		except Exception as e:
			return None

	def save_document(self, collection_name, document_id, data):
		document_ref = self.fs_database.collection(collection_name).document(document_id)
		document_ref.set(data)

	def get_document_items(self, document):
		result = []
		item_count = document.get("itemCount") or 0
		for i in range(item_count):
			x = document.get(f"item{i}") or ""
			if x != "":
				result.append(x)
		return result

	#-------------------------------------------------- device setup functions  --------------------------------------------------

	def update_device_status(self):
		device_model = "Webserver"  
		data = {
			"deviceModel": device_model,
			"userID": self.user_id,
			"timeStamp": get_current_timestamp()
		}
		document_ref = self.fs_database.collection(RegistrationTableName).document(self.device_root_id)
		document_ref.set(data)
		try:
			document_ref.get().to_dict()  # This doesn't return anything specific in Python, so it might need to be modified as per your needs.
		except Exception as e:
			print(f"Error updating device registration: {self.device_root_id}", e)

	def update_last_synced(self):
		try:
			document_ref = self.fs_database.collection(RegistrationTableName).document(self.device_root_id)
			document_ref.update({"lastSynced": get_current_timestamp()})
			document_ref.get().to_dict() 
		except Exception as e:
			print(f"Error updating last synced for device: {self.device_root_id}", e)

	def activate_trial_license(self, device_root_id):
		print(f"Activating trial license for device: {self.device_root_id}")
		data = {
			"subscriptionLevel": 1,
			"useGoogleAuth": False,
			"syncUsage": True,
			"timeStamp": get_current_timestamp()
		}
		document_ref = self.fs_database.collection(ActivatedDevicesTableName).document(self.device_root_id)
		document_ref.set(data)
		try:
			document_ref.get().to_dict()  # Similar to above, might need to be modified.
		except Exception as e:
			print("Error activating device", e)

	def get_device_settings(self):
		print(f"Reading device settings for {self.device_root_id}")
		result = DeviceSettings()
		document_ref = self.fs_database.collection(ActivatedDevicesTableName).document(self.device_root_id)
		try:
			document = document_ref.get().to_dict()
			if document:
				result = DeviceSettings(**document)
		except Exception as e:
			print(f"Unable to read device settings for {self.device_root_id}", e)
		update_device_status()
		if result.subscription_level == -100:
			activate_trial_license(self.device_root_id)
			result.subscription_level = 1
		return result


	#-------------------------------------------------- Firebase Sample Prompt Management  --------------------------------------------------

	def get_sample_prompts_last_updated(self):
		max_time_stamp = default_timestamp
		try:
			snap = self.fs_database.collection(SamplePromptTableName).order_by("timeStamp", direction=firestore.Query.DESCENDING).limit(1).get()
			if snap:
				if len(snap) > 0: max_time_stamp = snap[0].get("timeStamp")
		except Exception as e:
			print(f"Unable to read {SamplePromptTableName} collection", e)
		return max_time_stamp

	def get_sample_prompts(self, cutoff):
		result = []
		try:
			snap = self.fs_database.collection(SamplePromptTableName).order_by("timeStamp").where("timeStamp", ">", cutoff).get()
			if snap:
				if len(snap) > 0:
					for document in snap:
						time_stamp = document.get("timeStamp")
						items = self.get_document_items(document)
						for item in items:
							v = item.split("|")
							prompt = v[0]
							activity_type = "Conversation"
							if len(v) > 1:
								activity_type = v[1]
							result.append(SamplePrompt(activity_type, prompt, time_stamp))
		except Exception as e:
			print(f"Unable to read {SamplePromptTableName} collection", e)
		return result

	def save_sample_prompts(self, prompts):
		base_id = "System"
		update_count = 0
		time_stamp = get_current_timestamp()
		if prompts:
			last_updated = get_sample_prompts_last_updated()
			item_count = 0
			stop_id = self.generate_id(last_updated, True, base_id)
			print(f"Prompt sync {stop_id} {len(prompts)} stop at {last_updated}")
			current_id = self.generate_id(time_stamp, True, base_id)
			data = {}
			iterator = iter(prompts)
			while True:
				try:
					value = next(iterator)
					id = self.generate_id(time_stamp, True, base_id)
					if id != current_id:
						if item_count > 0:
							data["timeStamp"] = time_stamp
							data["itemCount"] = item_count
							self.save_document(SamplePromptTableName, current_id, data)
							data = {}
							item_count = 0
						current_id = id
					else:
						data[f"item{item_count}"] = f"{value.prompt}|{value.activity_name}"
						item_count += 1
					update_count += 1
				except StopIteration:
					break
			if item_count > 0:
				data["timeStamp"] = time_stamp
				data["itemCount"] = item_count
				self.save_document(SamplePromptTableName, current_id, data)
		return update_count

	#-------------------------------------------------- Firebase Conversation Management  --------------------------------------------------

	def get_deleted_conversations(self):
		result = []
		try:
			document = self.fs_database.collection(DeletionsTableName).document(self.user_id).get().to_dict()
			if document:
				items = self.get_document_items(document)
				result = [int(item) for item in items]
		except Exception as e:
			print(f"Unable to read {DeletionsTableName} collection, disabling Firebase")
			is_functional = False
		return result

	def save_deleted_conversations(self, ids):
		time_stamp = get_current_timestamp()
		data = {
			"timeStamp": time_stamp,
			"itemCount": len(ids),
			**{f"item{i}": id for i, id in enumerate(ids)}
		}
		self.save_document(DeletionsTableName, self.user_id, data)

	def save_conversation(self, conversation, messages):
		document_id = self.generate_id(conversation.conversationID, False)
		data = {
			"conversationID": conversation.conversationID,
			"dateAccessed": conversation.dateAccessed,
			"dateCreated": conversation.dateCreated,
			"dateModified": conversation.dateModified,
			"title": conversation.title,
			"summary": conversation.summary,
			**{f"item{i}": f"{m.timeStamp}|{m.role}|{m.content.replace('|', '')}" for i, m in enumerate(messages)},
			"itemCount": len(messages)
		}
		self.save_document(ConversationTableName, document_id, data)
		conversation.saved = True

	def get_conversation(self, conversationID):
		conversation = Conversation()
		messages = []
		document_id = self.generate_id(conversationID, False)
		try:
			document = self.fs_database.collection(ConversationTableName).document(document_id).get().to_dict()
			if document:
				conversation.conversationID = conversationID
				conversation.dateAccessed = document.get("dateAccessed")
				conversation.dateCreated = document.get("dateCreated")
				conversation.dateModified = document.get("dateModified")
				print(conversation.conversationID, conversation.dateModified)
				conversation.title = document.get("title", "")
				conversation.summary = document.get("summary")
				items = self.get_document_items(document)
				for item in items:
					v = item.split("|")
					if len(v) == 3:
						m = ChatMessageExtended(conversationID, v[1], v[2], int(v[0]))
						messages.append(m)
					else:
						print(f"Malformed message in {conversationID}: {item[:30]}")
		except Exception as e:
			print(f"Unable to read conversation conversationID: {conversationID}, disabling Firebase", e)
			is_functional = False
		return conversation, messages

	def make_conversation_toc(self, conversations):
		last_updated = default_timestamp
		for c in conversations:
			if timestamp_from_date(c.dateModified) > last_updated:
				last_updated = timestamp_from_date(c.dateModified)

		document_id = f"{self.root_id}:TOC"
		data = {
			"dateCreated": last_updated,
			"title": "TOC",
			"rootID": self.root_id
		}
		conversations.sort(key=lambda x: x.conversationID)
		item_count = 0
		for c in conversations:
			c.title = c.title.replace("|", "")
			c.summary = c.summary.replace("|", "")
			data[f"item{item_count}"] = f"{c.conversationID}|{timestamp_from_date(c.dateModified)}|{c.title[:25]}"
			item_count += 1
		data["itemCount"] = item_count
		self.save_document(ConversationTableName, document_id, data)

	def get_conversation_toc_last_updated(self):
		document_id = f"{self.root_id}:TOC"
		max_time_stamp = 0
		try:
			document = self.fs_database.collection(ConversationTableName).document(document_id).get().to_dict()
			if document:
				max_time_stamp = document.get("dateCreated")
		except Exception as e:
			print(f"Unable to read latest dateCreated from {ConversationTableName} TOC", e)
		return max_time_stamp

	def get_conversation_toc(self):
		document_id = f"{self.root_id}:TOC"
		conversations = []
		#try:
		document = self.fs_database.collection(ConversationTableName).document(document_id).get().to_dict()
		if document:
			items = self.get_document_items(document)
			for item in items:
				v = item.split("|")
				if len(v) == 3:
					conversationID = int(v[0])
					dateModified = int(v[1])
					dateModified = date_from_timestamp(dateModified)
					title_partial = v[2]
					c = Conversation(conversationID, title_partial, "", True, self.user_id, dateModified, dateModified,dateModified)
					conversations.append(c)
				else:
					print(f"Malformed conversation from TOC in {item[:30]}")
		#except Exception as e:
		#	print("Unable to read TOC", e)
		return conversations

	#-------------------------------------------------- Firebase ChatUsage Management  --------------------------------------------------
	async def get_usage_last_updated(self):
		max_time_stamp = default_timestamp
		try:
			snap = self.fs_database.collection(UsageTableName) \
				.where("id", ">=", f"{usage_root_id}") \
				.where("id", "<", f"{usage_root_id}Z") \
				.order_by("id", direction=firestore.Query.DESCENDING) \
				.limit(1) \
				.get()
			if snap:
				if len(snap) > 0:
					id = snap[0].id.replace(f"{usage_root_id}:", "")
					max_time_stamp = int(id)
			print(f"getUsageLastUpdated result {date_from_timestamp(max_time_stamp)}")
		except Exception as e:
			print(f"getUsageLastUpdated, unable to read {UsageTableName} collection, disabling Firebase", e)
			is_functional = False
		return max_time_stamp

	async def save_usage(self, usage):
		update_count = 0
		usage.sort(key=lambda x: x.time_stamp, reverse=True)
		if usage:
			last_updated = await get_usage_last_updated()
			item_count = 0
			stop_id = self.generate_id(last_updated, True, usage_root_id)
			print(f"Usage sync {stop_id} {len(usage)} stop at {date_from_timestamp(last_updated)}")
			current_id = self.generate_id(usage[0].time_stamp, True, usage_root_id)
			data = {}

			for c in usage:
				id = self.generate_id(c.time_stamp, True, usage_root_id)
				value = f"{c.prompt_tokens}:{c.completion_tokens}:{c.total_tokens}:{c.conversationID}:{c.time_stamp}"
				update_count += 1
				if id != current_id:
					if item_count > 0:
						data["id"] = current_id
						data["itemCount"] = item_count
						self.save_document(UsageTableName, current_id, data)
						data = {}
						item_count = 0

					current_id = id

				else:
					data[f"item{item_count}"] = value
					item_count += 1
			if item_count > 0:
				data["id"] = current_id
				data["itemCount"] = item_count
				self.save_document(UsageTableName, current_id, data)
		return update_count

	def delete_conversation(self, conversationID):
		document_id = self.generate_id(conversationID, False)
		doc_ref = self.fs_database.collection(ConversationTableName).document(document_id)
		doc_ref.delete().add_done_callback(
			lambda _: print(f"Conversation {conversationID} successfully deleted!")
		)

if __name__ == "__main__":
	fb = FirebaseManager()
	print("ID: ", fb.generate_id())
	conversations = fb.get_conversation_toc()
	for conversation in conversations:
		print("Conversation:", conversation)
		#messages = fb.get_conversation(conversation.conversationID)
		#for message in messages: print("Message:", message)
