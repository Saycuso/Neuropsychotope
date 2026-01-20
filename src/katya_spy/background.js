// Function to get the current tab and send it to Katya
function reportActiveTab() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        if (tabs && tabs.length > 0) {
            let tab = tabs[0];
            
            // Filter out internal Chrome pages
            if (tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('about:blank')) {
                
                // Send "Heartbeat" to Python Server
                fetch('http://127.0.0.1:5000/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: tab.url })
                }).catch(err => {
                    // Ignore errors if Katya is offline
                });
            }
        }
    });
}

// 1. LISTEN FOR CLICKS/UPDATES (Instant Reaction)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') {
        reportActiveTab();
    }
});

chrome.tabs.onActivated.addListener(() => {
    reportActiveTab();
});

// 2. THE HEARTBEAT (Check every 1 second)
// This fixes the "Stuck at 13s" bug
setInterval(reportActiveTab, 1000);