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
              {(part.score * 100).toFixed(1)}% conf · {part.source}
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
          <ShieldAlert size={13} />
          sensitive data masked
        </div>
      )}

      <div className="message-header">
        <div className="sender-name">
          <div className={`sender-avatar ${isUser ? 'user-av' : 'ai-av'}`}>
            {isUser ? 'U' : 'AI'}
          </div>
          {isUser ? 'You' : 'Gemini'}
          {isUser && (
            <span
              className="flag-icon-btn"
              onClick={() => onFlag && onFlag(message.original)}
              title="Flag bad masking & retrain"
            >
              <Flag size={12} color="#ff4d6a" fill="#ff4d6a" />
            </span>
          )}
        </div>

        {hasPII && (
          <div className="toggle-container" onClick={() => setShowOriginal(!showOriginal)}>
            {showOriginal ? <EyeOff size={12} /> : <Eye size={12} />}
            {showOriginal ? 'hide original' : 'show original'}
          </div>
        )}
      </div>

      <div className="message-bubble">
        {renderText(showOriginal ? message.original : message.masked, showOriginal)}
      </div>
    </div>
  );
}