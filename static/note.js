document.getElementById('notelist-button').addEventListener('click', () => {
    window.location.href = '/notes';
});

const deleteButton = document.getElementById('delete-button');
if (deleteButton) {
    deleteButton.addEventListener('click', async function() {
        const noteID = this.getAttribute('data-id');
        if (!confirm('Delete this note?')) return;
        const response = await fetch('/note/' + noteID + '/delete', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/notes';
        }
    });
}

// Auto-resize textarea
const textarea = document.getElementById('note-content');
function resizeTextarea() {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}
textarea.addEventListener('input', resizeTextarea);
resizeTextarea();
