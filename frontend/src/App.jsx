import React, { useState } from 'react';
import { Shield, Send } from 'lucide-react';
import ChatContainer from './components/ChatContainer';
import DocumentMasker from './components/DocumentMasker';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [retrainState, setRetrainState] = useState({ active: false, progress: 0, status: 'idle', msg: '' });

  const handleFlagMessage = async (text) => {
    setRetrainState({ active: true, progress: 0, status: 'training', msg: '' });

    const interval = setInterval(() => {
      setRetrainState(prev => {
        if (prev.progress >= 95) return prev;
        return { ...prev, progress: prev.progress + 1.5 };
      });
    }, 150);

    try {
      const response = await fetch('http://localhost:8000/report_bad_masking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await response.json();

      clearInterval(interval);
      if (data.status === 'success') {
        setRetrainState({ active: true, progress: 100, status: 'success', msg: '' });
        setTimeout(() => setRetrainState({ active: false, progress: 0, status: 'idle', msg: '' }), 6000);
      } else {
        setRetrainState({ active: true, progress: 100, status: 'error', msg: data.message });
        setTimeout(() => setRetrainState({ active: false, progress: 0, status: 'idle', msg: '' }), 5000);
      }
    } catch (err) {
      clearInterval(interval);
      setRetrainState({ active: true, progress: 100, status: 'error', msg: 'Network error during retraining.' });
      setTimeout(() => setRetrainState({ active: false, progress: 0, status: 'idle', msg: '' }), 5000);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessageText = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    const tempUserMsg = {
      sender: 'user',
      original: userMessageText,
      masked: userMessageText,
      entities: []
    };

    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userMessageText })
      });

      const data = await response.json();

      const verifiedUserMsg = {
        sender: 'user',
        original: data.original,
        masked: data.masked_input,
        entities: data.input_entities
      };

      const geminiMsg = {
        sender: 'gemini',
        original: data.gemini_response,
        masked: data.masked_response,
        entities: data.output_entities
      };

      setMessages(prev => {
        const newArr = [...prev];
        newArr[newArr.length - 1] = verifiedUserMsg;
        return [...newArr, geminiMsg];
      });

    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = {
        sender: 'gemini',
        original: 'Connection error. Ensure backend is running.',
        masked: 'Connection error. Ensure backend is running.',
        entities: []
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-title-container">
          <Shield className="shield-icon" size={22} />
          <div>
            <h1 className="header-title">PII DATA MASKER</h1>
          </div>
        </div>
        
        <div className="tabs-container">
          <button 
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat Interface
          </button>
          <button 
            className={`tab-btn ${activeTab === 'document' ? 'active' : ''}`}
            onClick={() => setActiveTab('document')}
          >
            Document OCR
          </button>
        </div>
      </header>

      {retrainState.active && (
        <div className="active-learning-bar">
          <div className="progress-container">
            <div
              className="progress-fill"
              style={{
                width: `${retrainState.progress}%`,
                backgroundColor:
                  retrainState.status === 'error' ? '#ff4d6a'
                  : retrainState.status === 'success' ? '#00e5a0'
                  : '#00d4ff'
              }}
            />
          </div>
          <div className="progress-text">
            {retrainState.status === 'training' && `retraining neural network... ${Math.round(retrainState.progress)}%`}
            {retrainState.status === 'success' && `deep learning core updated — please resend your input`}
            {retrainState.status === 'error' && `training failed: ${retrainState.msg}`}
          </div>
        </div>
      )}

      {activeTab === 'chat' ? (
        <>

          <ChatContainer messages={messages} onFlag={handleFlagMessage} isLoading={isLoading} />

          <div className="input-container">
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div className="input-wrapper">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Type a message"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  disabled={isLoading}
                />
              </div>
            </div>
            <button
              className="send-button"
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
            >
              {isLoading ? <div className="loader" /> : <Send size={15} />}
            </button>
          </div>
        </>
      ) : (
        <DocumentMasker onFlag={handleFlagMessage} />
      )}
    </div>
  );
}

export default App;