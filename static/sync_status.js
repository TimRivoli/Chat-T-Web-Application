// Polls /sync_status and shows a banner while sync is in progress.
(function() {
    const banner = document.getElementById('sync-banner');
    const message = document.getElementById('sync-message');
    if (!banner || !message) return;

    let pollInterval = null;
    let wasInProgress = false;

    async function checkSync() {
        try {
            const resp = await fetch('/sync_status');
            if (!resp.ok) return;
            const data = await resp.json();
            if (data.in_progress) {
                wasInProgress = true;
                message.textContent = '↻ ' + data.status;
                banner.classList.remove('hidden');
                banner.classList.add('visible');
            } else {
                if (wasInProgress) {
                    message.textContent = '✓ Sync complete';
                    banner.classList.remove('hidden');
                    banner.classList.add('visible');
                    setTimeout(() => banner.classList.add('hidden'), 3000);
                    wasInProgress = false;
                }
                clearInterval(pollInterval);
                pollInterval = setInterval(checkSync, 15000);
            }
        } catch (e) { /* server not ready yet */ }
    }

    // Poll quickly while sync might be running, slow down once idle
    pollInterval = setInterval(checkSync, 2000);
    checkSync();
})();
