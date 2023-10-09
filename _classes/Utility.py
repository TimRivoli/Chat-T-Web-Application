from datetime import datetime

#Note on time: Python supports date from seconds, Kotlin supports time from millis, so the firebase timestamps are saved in millis which need to be translated for Python losing <1 sec precision
#This is going to present an issue whenever timestamps are converted to dates and back
#To simply all date and timestamp conversions go through here

default_timestamp = 946684800000  #1/1/2000 in millis
def get_current_date(): return datetime.now()
def get_current_timestamp(): return int(datetime.now().timestamp()) * 1000
def date_from_timestamp(timestamp_in_millis): return datetime.fromtimestamp(int(timestamp_in_millis/1000))
def timestamp_from_date(date): return int(date.timestamp()) * 1000
def timestamp_trim_to_day(timestamp_in_millis):
	d = datetime.fromtimestamp(int(timestamp_in_millis/1000))
	d.replace(hour=0, minute=0, second=0, microsecond=0)
	return d.timestamp() * 1000
def date_string_from_timestamp(timestamp_in_millis):
	date_format = "%Y-%m-%d %H:%M:%S"
	return datetime.fromtimestamp(int(timestamp_in_millis/1000)).strftime(date_format)

def formatPromptPrettyLike(s1):
	formattedString = s1.strip().capitalize()
	if "what" in formattedString or "who" in formattedString or "why" in formattedString or "where" in formattedString:
		if not formattedString.endswith("?"):
			formattedString += "?"
	return formattedString
	
def formatHTMLMarkup(text):
	HTMLStartTag = "<!DOCTYPE html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>\n" + \
				   "<style> body {font-size: 8px; font-family: sans-serif;  } div { background-color: black; color: white;} </style>\n</head><body>"
	HTMLEndTag = "</body> </html>"
	ticks = "```"
	result = text.replace("\n", "<BR>")
	while ticks in result:
		result = result.replace(ticks, "<pre><div>", 1)
		result = result.replace(ticks, "</div></pre>", 1)
	return result 
