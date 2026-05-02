//buttons
const clearButton = document.getElementById('clear-button');
const conversationsButton = document.getElementById('conversations-button');
const copyButton = document.getElementById('copy-button');
const logoutButton = document.getElementById('logout-button');
const sendButton = document.getElementById('send-button');

//Options
const conversationMode = document.getElementById('conversation-mode');
const responseSize = document.getElementById('response-size');
const temperature = document.getElementById('temperature');
const chatActivityMode = document.getElementById('chat-activity-mode');
const languageOption = document.getElementById('language-option');
const customInstructions = document.getElementById('user-instructions');

//other
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');

function formatMarkdown(text) {
    let result = text;
    const ticks = "\n```";
    while (result.includes(ticks)) {
        result = result.replace(ticks, "<pre><div class='markdowncode'>");
        result = result.replace(ticks, "</div></pre>");
    }
    return result;
}

function addUserMessage(message) { chatBox.innerHTML += `<div class="user-message">${message}</div>`; }
function addResponseMessage(message) { 	chatBox.innerHTML += `<div class="bot-message">${formatMarkdown(message)}</div>`; }

sendButton.addEventListener('click', async () => {
    const userMessage = userInput.value;
    addUserMessage(userMessage);
	userInput.value = '';
    const formData = new URLSearchParams({user_input: userMessage, conversation_mode: conversationMode.checked, response_size: responseSize.value, chat_activity_mode: chatActivityMode.value, temperature: temperature.value, user_instructions: customInstructions.value, language_option: languageOption.value});
    const response = await fetch('/chat_query', {method: 'POST', body: formData,}).then(response => response.json());
	addResponseMessage(response.response);
    chatBox.scrollTop = chatBox.scrollHeight;
});
	
userInput.addEventListener('keydown', event => {
	if (event.key === 'Enter') {
		event.preventDefault(); 
		sendButton.click(); 
	}
});

conversationsButton.addEventListener('click', function() {
	window.location.href = '/conversations';
});

document.getElementById('notes-button').addEventListener('click', function() {
	window.location.href = '/notes';
});

const saveAsNoteButton = document.getElementById('save-as-note-button');
const saveNotePanel = document.getElementById('save-note-panel');
const saveNoteTitle = document.getElementById('save-note-title');
const saveNoteCategory = document.getElementById('save-note-category');

saveAsNoteButton.addEventListener('click', () => {
	saveNoteTitle.value = '';
	saveAsNoteButton.classList.add('hidden');
	saveNotePanel.classList.remove('hidden');
	saveNotePanel.classList.add('visible');
	saveNoteTitle.focus();
});

document.getElementById('cancel-save-note').addEventListener('click', () => {
	saveNotePanel.classList.add('hidden');
	saveAsNoteButton.classList.remove('hidden');
});

const confirmSaveNote = document.getElementById('confirm-save-note');
confirmSaveNote.addEventListener('click', async () => {
	confirmSaveNote.disabled = true;
	confirmSaveNote.textContent = 'Saving...';
	const title = saveNoteTitle.value.trim();
	const categoryId = saveNoteCategory.value;
	const formData = new URLSearchParams({ title, category_id: categoryId });
	const response = await fetch('/save_as_note', { method: 'POST', body: formData });
	const result = await response.json();
	confirmSaveNote.disabled = false;
	confirmSaveNote.textContent = 'Save';
	saveNotePanel.classList.add('hidden');
	if (result.success) {
		window.location.href = '/note/' + result.note_id;
	}
});

clearButton.addEventListener('click', () => { 	window.location.href = '/';});

// copyButton.addEventListener('click', () => {
    // const botMessages = document.querySelectorAll('.bot-message');
    // const textToCopy = Array.from(botMessages).map(message => message.textContent).join('\n');   
    // const tempTextarea = document.createElement('textarea');
    // tempTextarea.value = textToCopy;
    // document.body.appendChild(tempTextarea);
    // tempTextarea.select();
    // document.execCommand('copy');
    // document.body.removeChild(tempTextarea);
// });

logoutButton.addEventListener('click', function() {
	window.location.href = '/logout';
});

