import configparser, os

_config = configparser.ConfigParser()
_config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.ini'))

openai_api_key    = _config['openai']['api_key']
google_api_key    = _config['google']['api_key']
google_client_id  = _config['google']['client_id']
google_client_secret = _config['google']['client_secret']
firebase_user_ID  = _config['firebase']['user_id']
google_services   = "static/google-services.json"

DatabaseServer = "localhost"
DatabaseName   = "ChatDatabase"

ConversationTableName    = "conversations"
DeletionsTableName       = "conversations_deleted"
MessageTableName         = "messages"
UsageTableName           = "usage"
ActivatedDevicesTableName = "devices_activated"
RegistrationTableName    = "devices_registration"
SamplePromptTableName    = "sample_prompts"
NotesTableName           = "notes"
NotesCategoryTableName   = "notes_categories"
NotesDeletionsTableName  = "notes_deleted"
PricesWorkingSetTableName = "prices_working_set"

defaultModel  = "gpt-4o-mini"
enhancedModel = "gpt-4.1"
enhancedModel2 = "gpt-4o"
enhancedModel3 = "gpt-4.1-mini"
