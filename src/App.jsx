import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './index.css';

const socket = io('http://127.0.0.1:5000', { transports: ['websocket', 'polling'] });

function App() {
  const [status, setStatus] = useState('OFFLINE');
  const [transcriptions, setTranscriptions] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [activeCore, setActiveCore] = useState('AI ORCHESTRATOR');
  
  useEffect(() => {
    socket.connect(); // Ensure it connects if it was disconnected
    
    const onConnect = () => {
      console.log('Socket connected successfully!');
      setStatus('FRIDAY ONLINE');
    };
    const onDisconnect = () => {
      console.log('Socket disconnected!');
      setStatus('OFFLINE');
    };
    const onConnectError = (error) => {
      console.error('Socket connection error:', error);
      setStatus(`ERROR: ${error.message}`);
    };
    const onStatus = (data) => setStatus(data.msg);
    const onTranscription = (data) => {
      setTranscriptions(prev => [...prev, data]);
    };
    const onPong = () => console.log('Pong received');

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('connect_error', onConnectError);
    socket.on('status', onStatus);
    socket.on('transcription', onTranscription);
    socket.on('pong', onPong);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('connect_error', onConnectError);
      socket.off('status', onStatus);
      socket.off('transcription', onTranscription);
      socket.off('pong', onPong);
    };
  }, []);

  const toggleJarvis = () => {
    if (!isListening) {
      socket.emit('start_audio');
      setIsListening(true);
    } else {
      socket.emit('stop_audio');
      setIsListening(false);
    }
  };

  return (
    <div className="app-container">
      <header className="glass-panel header">
        <div className="logo">FRIDAY JARVIS</div>
        <div className="status-indicator">{status}</div>
      </header>

      <aside className="glass-panel sidebar">
        <div className="sidebar-header">SYSTEM CORES</div>
        <div className="core-list">
          {['AI ORCHESTRATOR', 'VISION ENGINE', 'TWILIO HUB', 'CAD ENGINE'].map((core) => (
            <div 
              key={core} 
              className={`core-item ${activeCore === core ? 'active' : ''}`}
              onClick={() => setActiveCore(core)}
              style={{ cursor: 'pointer' }}
            >
              {core}
            </div>
          ))}
        </div>
      </aside>

      <main className="main-view">
        {activeCore === 'AI ORCHESTRATOR' && (
          <div className="glass-panel chat-view">
            <h3>Communication Log</h3>
            {transcriptions.map((t, i) => (
              <div key={i} className={`chat-bubble ${t.sender}`}>
                <strong>{t.sender}:</strong> {t.text}
              </div>
            ))}
          </div>
        )}
        {activeCore === 'VISION ENGINE' && (
          <div className="glass-panel module-view">
            <h3>Vision Engine</h3>
            <div className="status-indicator">Camera Feed Standby</div>
            <p>Computer Vision sub-system is awaiting initialization...</p>
          </div>
        )}
        {activeCore === 'TWILIO HUB' && (
          <div className="glass-panel module-view">
            <h3>Twilio Hub</h3>
            <div className="status-indicator">Comm Link Active</div>
            <p>Ready to dispatch SMS and phone calls via Twilio API...</p>
          </div>
        )}
        {activeCore === 'CAD ENGINE' && (
          <div className="glass-panel module-view">
            <h3>CAD Engine</h3>
            <div className="status-indicator">Engine Ready</div>
            <p>Awaiting 3D rendering parameters...</p>
          </div>
        )}
      </main>

      <aside className="glass-panel stats-panel">
        <div className="sidebar-header">DIAGNOSTICS</div>
        <div className="stats-list">
          <div>CPU: 12%</div>
          <div>MEM: 4.2GB</div>
          <div>LATENCY: 45ms</div>
        </div>
      </aside>

      <footer className="glass-panel control-bar">
        <div className="voice-visualizer">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="bar" style={{ animationDelay: `${i * 0.05}s` }}></div>
          ))}
        </div>
        <div className="jarvis-orb" onClick={toggleJarvis}></div>
        <div className="voice-visualizer">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="bar" style={{ animationDelay: `${i * 0.05}s` }}></div>
          ))}
        </div>
      </footer>
    </div>
  );
}

export default App;
