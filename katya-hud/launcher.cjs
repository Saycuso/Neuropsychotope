const { app, BrowserWindow } = require('electron');

app.disableHardwareAcceleration();

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 600,
    height: 400,
    frame: true,        // Borders ON
    transparent: false, // Background ON
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // 1. Force Open the "Inspect Element" Console
  win.webContents.openDevTools();

  // 2. Try the IP address (More reliable than localhost)
  const targetUrl = 'http://localhost:5173/';
  console.log(`Attempting to load: ${targetUrl}`);
  win.loadURL(targetUrl);

  // 3. Log errors to your Terminal if it fails
  win.webContents.on('did-fail-load', (event, code, desc) => {
    console.log(`\nCRITICAL ERROR: Failed to load. Code: ${code}, Description: ${desc}\n`);
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});