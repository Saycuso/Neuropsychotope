import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css'; 

const socket = io('http://localhost:5000');

function App() {
  const [view, setView] = useState("CONNECTING"); 
  const [user, setUser] = useState(null);
  const [formData, setFormData] = useState({ name: "", profession: "", quest: "" });

  // --- NEW ECONOMY STATE ---
  const [economy, setEconomy] = useState({
    balance: 0,
    change: 0,
    status: "IDLE", 
    locked: false,
    domain: "SYSTEM READY"
  });

  useEffect(() => {
    // 1. Identity Handlers
    socket.on('trigger_setup', () => setView("SETUP"));
    socket.on('auth_success', (userData) => {
      setUser(userData);
      setView("DASHBOARD");
    });

    // 2. ECONOMY HANDLER (The Money Stream)
    socket.on('status_update', (data) => {
      setEconomy({
        balance: data.balance,
        change: data.change,
        status: data.status,
        locked: data.locked,
        domain: data.domain
      });
    });

    return () => {
      socket.off('trigger_setup');
      socket.off('auth_success');
      socket.off('status_update');
    };
  }, []);

  const handleSetupSubmit = () => {
    socket.emit('create_identity', formData);
  };

  // --- VIEW 1: SETUP (Unchanged) ---
  if (view === "SETUP") {
    return (
      <div style={setupContainerStyle}>
        <h1 style={{textShadow: "0 0 10px #00f3ff"}}>NEUROPSYCHOTOPE v7.0</h1>
        <p className="blink">⚠️ NEURAL LINK UNRECOGNIZED ⚠️</p>
        
        <div style={{marginTop: "20px", width: "300px", display: "flex", flexDirection: "column", gap: "15px"}}>
          <input type="text" placeholder="CODENAME" style={inputStyle} onChange={(e) => setFormData({...formData, name: e.target.value})} />
          <input type="text" placeholder="CLASS (e.g. Dev)" style={inputStyle} onChange={(e) => setFormData({...formData, profession: e.target.value})} />
          <input type="text" placeholder="MAIN QUEST" style={inputStyle} onChange={(e) => setFormData({...formData, quest: e.target.value})} />
          <button onClick={handleSetupSubmit} style={buttonStyle}>INITIALIZE</button>
        </div>
      </div>
    );
  }

  // --- VIEW 2: DASHBOARD (The Upgrade) ---
  if (view === "DASHBOARD" && user) {
    // Dynamic Styles based on State
    const isLocked = economy.locked;
    const isSpending = economy.change < 0;
    const themeColor = isLocked ? "#ff0000" : (isSpending ? "#ffaa00" : "#00f3ff");

    return (
      <div style={{
        height: "100vh",
        background: `radial-gradient(circle, rgba(10,10,10,1) 0%, rgba(0,0,0,1) 100%)`,
        border: `2px solid ${themeColor}`,
        padding: "20px",
        fontFamily: "'Courier New', monospace",
        color: themeColor,
        boxShadow: `inset 0 0 20px ${themeColor}20`,
        transition: "all 0.5s ease"
      }}>
        
        {/* TOP BAR: Player Info + BALANCE */}
        <div style={{display: "flex", justifyContent: "space-between", borderBottom: `1px solid ${themeColor}50`, paddingBottom: "10px"}}>
          <div>
            <div style={{fontSize: "10px", opacity: 0.7}}>OPERATIVE</div>
            <div style={{fontWeight: "bold"}}>{user.name}</div>
          </div>
          
          {/* THE WALLET */}
          <div style={{textAlign: "right"}}>
            <div style={{fontSize: "10px", opacity: 0.7}}>CREDITS</div>
            <div style={{fontSize: "24px", fontWeight: "bold", textShadow: `0 0 10px ${themeColor}`}}>
              ${economy.balance}
            </div>
          </div>
        </div>

        {/* CENTER: Main Quest */}
        <div style={{margin: "40px 0", textAlign: "center"}}>
           <div style={{fontSize: "10px", letterSpacing: "2px", opacity: 0.7}}>CURRENT OBJECTIVE</div>
           <div style={{fontSize: "22px", marginTop: "5px"}}>{user.main_quest}</div>
        </div>

        {/* ACTIVE STATUS (The Ticker) */}
        <div style={{
          background: `${themeColor}10`, 
          border: `1px solid ${themeColor}`, 
          padding: "20px", 
          borderRadius: "4px",
          textAlign: "center"
        }}>
          <div style={{fontSize: "12px", opacity: 0.8}}>{economy.domain.toUpperCase()}</div>
          
          <div style={{fontSize: "30px", fontWeight: "bold", margin: "10px 0"}}>
            {economy.status}
          </div>

          <div style={{fontSize: "14px", fontWeight: "bold"}}>
             {economy.change > 0 ? "+" : ""}{economy.change} Credits / Tick
          </div>
        </div>

        {/* LOCKED WARNING */}
        {isLocked && (
          <div className="blink" style={{
            marginTop: "20px", 
            color: "red", 
            textAlign: "center", 
            fontSize: "20px", 
            fontWeight: "bold", 
            background: "black", 
            padding: "10px"
          }}>
            ⛔ RECOVERY MODE ACTIVE ⛔<br/>
            EARN 100 CREDITS TO UNLOCK
          </div>
        )}

      </div>
    );
  }

  return <div style={{background: "black", color: "white", height: "100vh", display: "grid", placeItems: "center"}}>CONNECTING...</div>;
}

// STYLES
const setupContainerStyle = {
  height: "100vh", background: "#050505", color: "#00f3ff", display: "flex", 
  flexDirection: "column", justifyContent: "center", alignItems: "center", 
  fontFamily: "'Courier New', monospace"
};
const inputStyle = {
  width: "100%", background: "transparent", border: "none", borderBottom: "1px solid #00f3ff", 
  color: "white", padding: "8px", fontFamily: "inherit", outline: "none"
};
const buttonStyle = {
  marginTop: "20px", background: "#00f3ff", color: "black", border: "none", 
  padding: "10px", fontWeight: "bold", cursor: "pointer"
};

export default App;