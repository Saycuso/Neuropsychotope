// src/katya_spy/background.js

function reportAllTabs() {
    // Query ALL tabs in ALL windows (God View)
    chrome.tabs.query({}, function(tabs) {
        if (tabs && tabs.length > 0) {
            
            // 1. Clean the data (Remove internal Chrome pages like settings/newtab)
            const cleanTabs = tabs
                .filter(tab => tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('about:') && !tab.url.startsWith('edge://'))
                .map(tab => ({
                    url: tab.url,
                    title: tab.title,
                    active: tab.active // We mark the one you are actually looking at
                }));

            // 2. Send the Batch to Python (New Endpoint: /track_batch)
            if (cleanTabs.length > 0) {
                fetch('http://127.0.0.1:5000/track_batch', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tabs: cleanTabs })
                }).catch(err => {
                    // Ignore errors if Katya is sleeping/offline
                });
            }
        }
    });
}

// LISTENERS (Triggers for tab switches, updates, closes)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') reportAllTabs();
});
chrome.tabs.onActivated.addListener(() => reportAllTabs());
chrome.tabs.onRemoved.addListener(() => reportAllTabs());

// HEARTBEAT (Every 2 seconds ensures we catch everything)
setInterval(reportAllTabs, 2000);