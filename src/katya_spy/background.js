// Generate a unique ID for this specific Chrome profile
const CLIENT_ID = "agent_" + Math.floor(Math.random() * 1000000);

function reportAllTabs() {
    chrome.tabs.query({}, function(tabs) {
        if (tabs && tabs.length > 0) {
            // Filter internal pages
            const cleanTabs = tabs
                .filter(tab => tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('edge://'))
                .map(tab => ({
                    url: tab.url,
                    title: tab.title,
                    active: tab.active 
                }));

            // SEND TO BATCH ENDPOINT
            if (cleanTabs.length > 0) {
                fetch('http://127.0.0.1:5000/track_batch', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        tabs: cleanTabs,
                        client_id: CLIENT_ID // <--- NEW: Send the unique profile ID
                    })
                }).catch(err => console.log("Katya Offline"));
            }
        }
    });
}

// LISTENERS
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') reportAllTabs();
});
chrome.tabs.onActivated.addListener(() => reportAllTabs());
chrome.tabs.onRemoved.addListener(() => reportAllTabs());

// HEARTBEAT
setInterval(reportAllTabs, 2000);