import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css'; // Ensure you have basic styles

const socket = io('http://localhost:5000');

function App() {
  const [view, setView] = useState("CONNECTING"); // CONNECTING, SETUP, DASHBOARD
  const [user, setUser] = useState(null);
  
  // Form State
  const [formData, setFormData] = useState({ name: "", profession: "", quest: "" });

  useEffect(() => {
    // 1. Listen for "Setup Needed"
    socket.on('trigger_setup', () => {
      setView("SETUP");
    });

    // 2. Listen for "Login Success"
    socket.on('auth_success', (userData) => {
      setUser(userData);
      setView("DASHBOARD");
    });

    return () => {
      socket.off('trigger_setup');
      socket.off('auth_success');
    };
  }, []);

  const handleSetupSubmit = () => {
    socket.emit('create_identity', formData);
  };

  // --- VIEW 1: CHARACTER CREATION (The Gamified Part) ---
  if (view === "SETUP") {
    return (
      <div className="setup-container" style={{
        height: "100vh",
        background: "#050505",
        color: "#00f3ff",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "'Courier New', monospace",
        border: "2px solid #00f3ff",
        boxShadow: "inset 0 0 50px rgba(0, 243, 255, 0.2)"
      }}>
        <h1 style={{textShadow: "0 0 10px #00f3ff"}}>NEUROPSYCHOTOPE v7.0</h1>
        <p className="blink">⚠️ NEURAL LINK UNRECOGNIZED ⚠️</p>
        
        <div style={{marginTop: "20px", width: "300px", display: "flex", flexDirection: "column", gap: "15px"}}>
          
          <div>
            <label style={{fontSize: "12px", opacity: 0.7}}>CODENAME</label>
            <input 
              type="text" 
              placeholder="e.g. Saycuso"
              style={inputStyle}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          </div>

          <div>
            <label style={{fontSize: "12px", opacity: 0.7}}>CLASS (PROFESSION)</label>
            <input 
              type="text" 
              placeholder="e.g. Full Stack Developer"
              style={inputStyle}
              onChange={(e) => setFormData({...formData, profession: e.target.value})}
            />
          </div>

          <div>
            <label style={{fontSize: "12px", opacity: 0.7}}>CURRENT QUEST (GOAL)</label>
            <input 
              type="text" 
              placeholder="e.g. Secure ₹10 LPA Job"
              style={inputStyle}
              onChange={(e) => setFormData({...formData, quest: e.target.value})}
            />
          </div>

          <button onClick={handleSetupSubmit} style={buttonStyle}>
            INITIALIZE UPLINK
          </button>
        </div>
      </div>
    );
  }

  // --- VIEW 2: THE HUD (Your Dashboard) ---
  if (view === "DASHBOARD" && user) {
    return (
      <div style={{
        height: "100vh",
        background: "rgba(13, 13, 13, 0.95)",
        border: "2px solid #00f3ff",
        padding: "20px",
        fontFamily: "'Courier New', monospace",
        color: "#00f3ff"
      }}>
        {/* Top Bar: Identity */}
        <div style={{borderBottom: "1px solid #333", paddingBottom: "10px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center"}}>
          <div>
            <div style={{fontSize: "10px", color: "#666"}}>OPERATIVE</div>
            <div style={{fontSize: "18px", fontWeight: "bold"}}>{user.name}</div>
          </div>
          <div style={{textAlign: "right"}}>
            <div style={{fontSize: "10px", color: "#666"}}>CLASS</div>
            <div style={{fontSize: "14px"}}>{user.profession}</div>
          </div>
        </div>

        {/* Main Quest Display */}
        <div style={{background: "rgba(0, 243, 255, 0.05)", padding: "15px", borderLeft: "4px solid #00f3ff", marginBottom: "20px"}}>
          <div style={{fontSize: "10px", letterSpacing: "2px", marginBottom: "5px"}}>CURRENT MAIN QUEST</div>
          <div style={{fontSize: "20px", textShadow: "0 0 10px rgba(0, 243, 255, 0.5)"}}>
            {user.main_quest}
          </div>
        </div>

        {/* The Stats (Sanity/Focus) go here... */}
        <div style={{opacity: 0.5, fontSize: "12px", textAlign: "center", marginTop: "50px"}}>
          SYSTEM: ONLINE | AWAITING INPUT
        </div>

      </div>
    );
  }

  return <div style={{background: "black", color: "white", height: "100vh", display: "grid", placeItems: "center"}}>CONNECTING TO KATYA CORE...</div>;
}

// Styles
const inputStyle = {
  width: "100%",
  background: "transparent",
  border: "none",
  borderBottom: "1px solid #00f3ff",
  color: "white",
  padding: "8px",
  fontFamily: "inherit",
  outline: "none"
};

const buttonStyle = {
  marginTop: "20px",
  background: "#00f3ff",
  color: "black",
  border: "none",
  padding: "10px",
  fontWeight: "bold",
  cursor: "pointer",
  clipPath: "polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)"
};

export default App;