import React, { useState } from 'react';
import { Shield, Send } from 'lucide-react';
import ChatContainer from './components/ChatContainer';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [retrainState, setRetrainState] = useState({ active: false, progress: 0, status: 'idle', msg: '' });

  const handleFlagMessage = async (text) => {
    setRetrainState({ active: true, progress: 0, status: 'training', msg: '' });
    
    // Smooth progress simulation over typical 10s window (BiLSTM epochs)
    const interval = setInterval(() => {
      setRetrainState(prev => {
        if(prev.progress >= 95) return prev;
        return { ...prev, progress: prev.progress + 1.5 };
      });
    }, 150);

    try {
      const response = await fetch('http://localhost:8080/report_bad_masking', {
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
    } catch(err) {
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
      const response = await fetch('http://localhost:8080/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
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
        original: "Connection error. Ensure backend is running.",
        masked: "Connection error. Ensure backend is running.",
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
          <Shield className="shield-icon" size={28} />
          <h1 className="header-title">Privacy Guard</h1>
        </div>
      </header>

      {retrainState.active && (
        <div className="active-learning-bar">
          <div className="progress-container">
            <div 
              className="progress-fill" 
              style={{ 
                width: `${retrainState.progress}%`, 
                backgroundColor: retrainState.status === 'error' ? '#ff6b6b' : (retrainState.status === 'success' ? '#00e676' : '#4cc9f0')
              }} 
            />
          </div>
          <div className="progress-text">
            {retrainState.status === 'training' && `Neural Network Retraining... (${Math.round(retrainState.progress)}%)`}
            {retrainState.status === 'success' && `Deep Learning Core successfully updated! Please SEND your exact input again.`}
            {retrainState.status === 'error' && `Training failed: ${retrainState.msg}`}
          </div>
        </div>
      )}

      <ChatContainer messages={messages} onFlag={handleFlagMessage} />

      <div className="input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="Type a message (e.g. Call John at 555-1234)..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={isLoading}
        />
        <button 
          className="send-button" 
          onClick={handleSend} 
          disabled={isLoading || !inputValue.trim()}
        >
          {isLoading ? <div className="loader" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}

export default App;
