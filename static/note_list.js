document.getElementById('new-note-button').addEventListener('click', () => {
    window.location.href = '/note/new';
});

document.getElementById('chat-button').addEventListener('click', () => {
    window.location.href = '/';
});

// Expand/collapse note content on title click
document.querySelectorAll('.note-title').forEach(title => {
    title.addEventListener('click', function() {
        const noteID = this.getAttribute('data-id');
        const content = document.getElementById('content-' + noteID);
        content.classList.toggle('hidden');
        content.classList.toggle('visible');
    });
});

// Edit button
document.querySelectorAll('.edit-button').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        window.location.href = '/note/' + this.getAttribute('data-id');
    });
});

// Delete button
document.querySelectorAll('.delete-button').forEach(btn => {
    btn.addEventListener('click', async function(e) {
        e.stopPropagation();
        const noteID = this.getAttribute('data-id');
        if (!confirm('Delete this note?')) return;
        const response = await fetch('/note/' + noteID + '/delete', { method: 'POST' });
        if (response.ok) {
            this.closest('.note-container').remove();
        }
    });
});

// Category filter
document.getElementById('category-filter').addEventListener('change', filterNotes);
document.getElementById('search-box').addEventListener('input', filterNotes);

function filterNotes() {
    const categoryID = document.getElementById('category-filter').value;
    const search = document.getElementById('search-box').value.toLowerCase();
    document.querySelectorAll('.note-container').forEach(note => {
        const matchCat = !categoryID || note.getAttribute('data-category') === categoryID;
        const matchSearch = !search || note.getAttribute('data-title').includes(search);
        note.style.display = (matchCat && matchSearch) ? '' : 'none';
    });
}
