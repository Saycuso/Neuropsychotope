// Function to get ALL tabs and send them to Katya
function reportAllTabs() {
    // Query ALL tabs in ALL windows
    chrome.tabs.query({}, function(tabs) {
        if (tabs && tabs.length > 0) {
            
            // 1. Clean the data (Remove chrome:// internals)
            const cleanTabs = tabs
                .filter(tab => tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('about:'))
                .map(tab => ({
                    url: tab.url,
                    title: tab.title,
                    active: tab.active // We flag which one you are actually looking at
                }));

            // 2. Send the Batch to Python
            if (cleanTabs.length > 0) {
                fetch('http://127.0.0.1:5000/track_batch', { // <--- NEW ENDPOINT
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tabs: cleanTabs })
                }).catch(err => {
                    // Ignore offline errors
                });
            }
        }
    });
}

// LISTENERS
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') reportAllTabs();
});

chrome.tabs.onActivated.addListener(() => {
    reportAllTabs();
});

chrome.tabs.onRemoved.addListener(() => {
    reportAllTabs();
});

// Heartbeat (Every 2 seconds is enough for batch processing)
setInterval(reportAllTabs, 2000);