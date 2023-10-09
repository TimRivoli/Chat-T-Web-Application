openai_api_key = "<enter your key here>"
google_api_key = "<enter your key here>"
google_client_id = "<enter your key here>"
google_client_secret = "<enter your key here>"
google_services = "static\google-services.json" #You will need to setup a Google API account and register your application
firebase_user_ID = "" #This should be loaded through OAuth/Firebase, haven't gotten there yet.

ConversationTableName = "conversations"
DeletionsTableName = "conversations_deleted"
MessageTableName = "messages"
UsageTableName = "usage"
ActivatedDevicesTableName = "devices_activated"
RegistrationTableName = "devices_registration"
SamplePromptTableName = "sample_prompts"

defaultModel = "gpt-3.5-turbo"
enhancedModel = "gpt-4"
