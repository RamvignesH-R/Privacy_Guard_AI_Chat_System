import React, { useState } from 'react';
import { ShieldAlert, Eye, EyeOff, Flag } from 'lucide-react';

export default function MessageBubble({ message, onFlag }) {
  const isUser = message.sender === 'user';
  const [showOriginal, setShowOriginal] = useState(false);

  const hasPII = message.entities && message.entities.length > 0;
  
  const renderText = (text, isOriginal) => {
    if (isOriginal || !hasPII) return text;
    
    const parts = [];
    const regex = /\[(.*?)\]/g;
    
    let lastIndex = 0;
    let match;
    
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: 'text', content: text.substring(lastIndex, match.index) });
      }
      
      const label = match[1];
      const entity = message.entities.find(e => e.label === label);
      
      parts.push({ 
        type: 'token', 
        label, 
        score: entity ? entity.score : null, 
        source: entity ? entity.source : 'Unknown' 
      });
      lastIndex = regex.lastIndex;
    }
    
    if (lastIndex < text.length) {
      parts.push({ type: 'text', content: text.substring(lastIndex) });
    }
    
    if (parts.length === 0) return <span>{text}</span>;
    
    return parts.map((part, idx) => {
      if (part.type === 'text') {
        return <span key={idx}>{part.content}</span>;
      }
      return (
        <span key={idx} className="pii-token">
          [{part.label}]
          {part.score !== null && (
            <div className="tooltip">
              {(part.score * 100).toFixed(1)}% Conf | {part.source}
            </div>
          )}
        </span>
      );
    });
  };

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'gemini'}`}>
      {hasPII && (
        <div className="pii-warning">
          <ShieldAlert size={16} />
          Sensitive data detected and masked
        </div>
      )}
      
      <div className="message-header">
        <div className="sender-name">
          {isUser ? 'You' : 'Gemini'}
          {isUser && (
            <span className="flag-icon-btn" onClick={() => onFlag && onFlag(message.original)} title="Flag Bad Masking & Retrain AI">
              <Flag size={14} color="#ff3333" fill="#ff3333" />
            </span>
          )}
        </div>
        
        {hasPII && (
          <div className="toggle-container" onClick={() => setShowOriginal(!showOriginal)}>
            {showOriginal ? <EyeOff size={14} /> : <Eye size={14} />}
            {showOriginal ? 'Hide Original' : 'Show Original'}
          </div>
        )}
      </div>
      
      <div className="message-bubble">
        {renderText(showOriginal ? message.original : message.masked, showOriginal)}
      </div>
    </div>
  );
}
