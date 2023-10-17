import firebase_admin
from flask import session 
from firebase_admin import credentials, auth, firestore, initialize_app
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

from _classes.Constants import *
from _classes.Utility import *
from _classes.DataClasses import *
from _classes.Cryptography import *

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
	encrypt_content = True
	encryption_pending = False
	content_encryption_key = ""
	encryption_test_content = "Today is a good day!"
	fs_database = None
	
	# def __new__(cls, *args, **kwargs):
		# if not cls._instance:
			# cls._instance = super().__new__(cls, *args, **kwargs)
		# return cls._instance

	def __init__(self):
		if not self.is_initialized:
			print("Initializing Firebase")
			self.initialize(True)
			self.is_initialized = True

	def initialize(self, use_google_auth):
		if use_google_auth:
			cred = credentials.Certificate(google_services)
			firebase_admin.initialize_app(cred)
			#print(f"Initializing with token: {id_token}")
			#user = auth.verify_id_token(id_token)
			#return f"Firebase UserID: {user['uid']}"
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
		
#-------------------------------------------------- Device Management functions --------------------------------------------------
	def distribute_api_keys():
		cred = credentials.Certificate(google_services)
		firebase_admin.initialize_app(cred)
		db = firestore.client()
		collection_a = db.collection(RegistrationTableName)
		collection_b = db.collection(ActivatedDevicesTableName)
		docs_a = collection_a.stream()
		for doc_a in docs_a:
			device_id = doc_a.id
			public_key = doc_a.to_dict().get('publicKey', None)
			if public_key:
				encrypted_api_key = encrypt_string_rsa(openai_api_key, public_key)
				#print(encrypted_api_key)
				doc_b = collection_b.document(device_id).get().to_dict()
				doc_b['apiKey'] = encrypted_api_key
				collection_b.document(device_id).set(doc_b, merge=True)
	
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
			self.is_functional = False
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
				if self.encrypt_content:
					conversation.title = decrypt_string_aes(conversation.title, self.content_encryption_key)
					conversation.summary = decrypt_string_aes(conversation.summary, self.content_encryption_key)               
				items = self.get_document_items(document)
				for item in items:
					v = item.split("|")
					if self.encrypt_content: v = decrypt_string_aes(item, self.content_encryption_key).split("|")
					if len(v) == 3:
						m = ChatMessageExtended(conversationID, v[1], v[2], int(v[0]))
						messages.append(m)
					else:
						print(f"Malformed message in {conversationID}: {item[:50]}")
		except Exception as e:
			print(f"Unable to read conversation conversationID: {conversationID}, disabling Firebase", e)
			self.is_functional = False
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
		if (self.encrypt_content):
			data["key"] = encrypt_string_aes(self.encryption_test_content, self.content_encryption_key)        
		conversations.sort(key=lambda x: x.conversationID)
		item_count = 0
		for c in conversations:
			c.title = c.title.replace("|", "")
			if self.encrypt_content: c.title = encrypt_string_aes(c.title, self.content_encryption_key)
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
		encryption_state_is_good = not self.encrypt_content
		document_data = None
		try:
			document_data = self.fs_database.collection(ConversationTableName).document(document_id).get().to_dict()
		except Exception as ex:
			print(f"Unable to read TOC: {ex}")
			# If the TOC fails to read, this will cause an upload of the full conversation list and re-creation of the TOC, due to the structure of the IDs items won't be duplicated
		if document_data:
			encryption_test = document_data.get("key", "")
			if self.encrypt_content:
				self.content_encryption_key = get_aes_certificate()	#This generates and saves if it doesnt' exist
				print("Encryption is enabled.  Checking status...")
				if encryption_test == "":
					print("Content not yet encrypted. Setting encryptionPending.")
					self.encryption_pending = True
				else:
					if self.content_encryption_key != "":
						print("Content is encrypted.  Testing if my key matches.")
						test = decrypt_string_aes(encryption_test, self.content_encryption_key)
						if test == self.encryption_test_content:
							print("Encryption state is good.  Clear to proceed.")
							encryption_state_is_good = True
						else:
							print(f"Encryption test failed: {test}")
						
					key_transfer_requested_certificate = document_data.get("transferRequest", "")
					if not encryption_state_is_good:
						key_transfer_response = document_data.get("transferResponse", "")
						if key_transfer_response != "" and key_transfer_requested_certificate == get_public_key_as_string():
							print("Content is encrypted, checking the status of my key request.")
							test_key = decrypt_string_rsa(key_transfer_response)
							test = decrypt_string_aes(encryption_test, test_key)
							if test == self.encryption_test_content:
								print("Encryption state is good.  Clear to proceed.")
								self.content_encryption_key = test_key
								save_aes_certificate(test_key)
								encryption_state_is_good = True
							else:
								print("Encryption test failed on received key.")
								self.is_functional = False
						else:
							print("Content is encrypted and I don't have a valid key.  Requesting key transfer.")
							document_data["transferRequest"] = get_public_key_as_string()
							self.save_document(ConversationTableName, document_id, document_data)
							self.is_functional = False   # If the encryption key doesn't match then we aren't functional
							print("getConversationTOC, requested key transfer.")
					else:
						print("My encryption state is good.  Checking for transfer requests...")
						if key_transfer_requested_certificate != "":
							print(f"Sending response to: {key_transfer_requested_certificate}")
							key_transfer_response = encrypt_string_rsa(self.content_encryption_key, key_transfer_requested_certificate)
							print(f"My response: {key_transfer_response}")
							document_data["transferResponse"] = key_transfer_response
							self.save_document(ConversationTableName, document_id, document_data)
							print("getConversationTOC, sent key.")
			else:	#!self.encrypt_content
				if encryption_test !="":
					self.encryption_pending = False
					self.encryption_state_is_good = False
			if encryption_state_is_good:
				items = self.get_document_items(document_data)
				for item in items:
					v = item.split("|")
					if len(v) == 3 or (len(v) ==4 and self.encrypt_content):
						conversationID = int(v[0])
						dateModified = int(v[1])
						dateModified = date_from_timestamp(dateModified)
						title_partial = v[2]
						if self.encrypt_content:
							title_partial = v[2] + "|" + v[3]
						c = Conversation(conversationID, title_partial, "", True, self.user_id, dateModified, dateModified,dateModified)
						conversations.append(c)
					else:
						print(f"Malformed conversation from TOC in {item[:30]}")
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
			self.is_functional = False
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

