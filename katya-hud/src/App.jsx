// src/App.jsx
import { useState, useEffect } from 'react';
import io from 'socket.io-client';

// Connect to Python Brain
const socket = io('http://localhost:5000');

function App() {
  const [status, setStatus] = useState("IDLE");
  const [domain, setDomain] = useState("AWAITING INPUT");
  const [sanity, setSanity] = useState(100);

  useEffect(() => {
    socket.on('status_update', (data) => {
      setStatus(data.status);
      setDomain(data.domain || "SYSTEM READY");
    });

    socket.on('sanity_update', (data) => {
      setSanity(data.level);
    });

    return () => {
      socket.off('status_update');
      socket.off('sanity_update');
    };
  }, []);

  // Cyberpunk Logic
  const isDanger = status === "DISTRACTION";
  const mainColor = isDanger ? "#ff2a2a" : "#00f3ff"; // Red vs Cyan
  
  return (
    <div style={{
      background: "rgba(13, 13, 13, 0.9)",
      border: `2px solid ${mainColor}`,
      borderRadius: "12px",
      padding: "16px",
      color: mainColor,
      fontFamily: "'Courier New', monospace",
      height: "100vh",
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-between",
      boxShadow: `0 0 15px ${mainColor}40`, // Glow effect
      overflow: "hidden"
    }}>
      
      {/* Header */}
      <div style={{display: "flex", justifyContent: "space-between", fontSize: "10px", opacity: 0.8}}>
        <span>KATYA OS v7.0</span>
        <span>[{status}]</span>
      </div>

      {/* Main Target Display */}
      <div style={{textAlign: "center", margin: "10px 0"}}>
        <h2 style={{
          margin: 0, 
          fontSize: "20px", 
          textTransform: "uppercase", 
          textShadow: `0 0 8px ${mainColor}`
        }}>
          {domain}
        </h2>
      </div>

      {/* Sanity Bar */}
      <div>
        <div style={{display: "flex", justifyContent: "space-between", fontSize: "10px", marginBottom: "4px"}}>
          <span>SANITY INTEGRITY</span>
          <span>{sanity}%</span>
        </div>
        <div style={{
          width: "100%", 
          height: "8px", 
          background: "#333", 
          borderRadius: "4px",
          overflow: "hidden"
        }}>
          <div style={{
            width: `${sanity}%`,
            height: "100%",
            background: sanity < 30 ? "#ff0000" : mainColor,
            transition: "width 0.3s ease-out",
            boxShadow: `0 0 10px ${mainColor}`
          }}></div>
        </div>
      </div>

    </div>
  );
}

export default App;