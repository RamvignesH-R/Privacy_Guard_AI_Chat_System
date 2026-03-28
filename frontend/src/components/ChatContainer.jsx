import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import { ShieldCheck } from 'lucide-react';

export default function ChatContainer({ messages, onFlag }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      {messages.length === 0 ? (
        <div className="empty-state">
          <ShieldCheck className="empty-state-icon" />
          <h2>Privacy Guard AI</h2>
          <p>Your messages are masked locally before reaching the cloud.</p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble key={index} message={msg} onFlag={onFlag} />
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
