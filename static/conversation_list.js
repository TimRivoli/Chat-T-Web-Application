	var editableInputs = document.querySelectorAll('.editable');
	var detailsButtons = document.querySelectorAll('.details-button');
	var loadButtons = document.querySelectorAll('.load-button');
	var editButtons = document.querySelectorAll('.edit-button');
	var saveButtons = document.querySelectorAll('.save-button');
	var cancelButtons = document.querySelectorAll('.cancel-button');

	function loadConversation(conversationID) {
		window.location.href = '/load/' + conversationID;
	}

	function saveConversation(conversationID) {
		var titleInput = document.querySelector('.title[data-id="' + conversationID + '"] input[name="title"]');
		var summaryTextarea = document.querySelector('.summary[data-id="' + conversationID + '"] textarea[name="summary"]');
		var title = titleInput.value;
		var summary = summaryTextarea.value;
		var data = { title: title, summary: summary };

		// Send data to server using AJAX
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/update/' + conversationID, true);
		xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');

		xhr.onload = function () {
			if (xhr.status >= 200 && xhr.status < 400) {
				// Request was successful, handle the response if needed
				console.log(xhr.responseText);
			} else {
				// Error handling
				console.error('Error saving conversation:', xhr.status, xhr.statusText);
			}
		};

		xhr.onerror = function () {
			console.error('Network error');
		};

		xhr.send(JSON.stringify(data));
	}

	function cancelEdit(conversationID) {
		// Implement any actions needed when the user cancels the edit
		// For example, you might want to reset the input fields
	}
	function showItem(item){
		item.classList.remove('hidden');
		item.classList.add('visible');		
	}
	function hideItem(item) {
		item.classList.remove('visible');
		item.classList.add('hidden');				
	}
	function toggleDetails(conversationID) {
		var summaryElem =     document.getElementById('summary-' + conversationID);
		var editContainer =   document.getElementById('edit-container-' + conversationID);
		var editButton =    document.querySelector('.edit-button[data-id="' + conversationID + '"]');
		visible = !summaryElem.classList.contains('hidden');
		if (visible) {
			hideItem(summaryElem);
			hideItem(editButton);
		} else {
			showItem(summaryElem);
			showItem(editButton);
		}
		hideItem(editContainer);
	}

	function enableEdit(conversationID) {
		var summaryElem = document.getElementById('summary-' + conversationID);
		var editContainer =   document.getElementById('edit-container-' + conversationID);
		var editButton = document.querySelector('.edit-button[data-id="' + conversationID + '"]');
		hideItem(summaryElem);
		hideItem(editButton);
		showItem(editContainer);
	}

	function adjustTextareaHeight(textareaElement) {
        textareaElement.style.height = 'auto'; 
        textareaElement.style.height = (textareaElement.scrollHeight) + 'px'; 
    }
	function adjustInputHeight(inputElement) {
		inputElement.style.height = 'auto'; 
		inputElement.style.height = (inputElement.scrollHeight) + 'px'; 
	} 

document.addEventListener('DOMContentLoaded', function() {
	detailsButtons.forEach(function(button) {
		button.addEventListener('click', function() {
			var conversationID = this.getAttribute('data-id');
			toggleDetails(conversationID);
		});
	});

	loadButtons.forEach(function(button) {
		button.addEventListener('click', function() {
			var conversationID = this.getAttribute('data-id');
			loadConversation(conversationID);
		});
	});

	editButtons.forEach(function(button) {
		button.addEventListener('click', function() {
			var conversationID = this.getAttribute('data-id');
			enableEdit(conversationID);
		});
	});

	editableInputs.forEach(function(input) {
		if (input.classList.contains('title')) {
			adjustInputHeight(input);
		} else if (input.classList.contains('summary')) {
			adjustTextareaHeight(input);
		}
		input.addEventListener('input', function() {
			if (this.classList.contains('title')) {
				adjustInputHeight(this);
			} else if (this.classList.contains('summary')) {
				adjustTextareaHeight(this);
			}
		});
	});
});