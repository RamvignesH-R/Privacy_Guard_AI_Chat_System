import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { ShieldCheck } from 'lucide-react';

export default function ChatContainer({ messages, onFlag, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <div className="empty-state">
          <ShieldCheck className="empty-state-icon" size={40} />
          <h2>DATA MASKER</h2>
          <h3>PII (Personally identifiable information)</h3>
          <p>Your messages are masked locally before reaching the cloud</p>
          <p> PII never leaves your device</p>
    
        </div>
      ) : (
        <>
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} onFlag={onFlag} />
          ))}
          {isLoading && (
            <div className="typing-bubble">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}