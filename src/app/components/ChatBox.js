'use client';
import { useState } from 'react';
import axios from 'axios';

export default function ChatBox() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const sendQuestion = async () => {
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { type: 'user', text: question }]);
    setLoading(true);

    try {
      const res = await axios.post('http://127.0.0.1:8000/ask', {
        question,
      });

      if (res.data.result) {
        setMessages((prev) => [
          ...prev,
          { type: 'bot', text: JSON.stringify(res.data.result, null, 2) }
        ]);
      } else {
        setMessages((prev) => [...prev, { type: 'bot', text: res.data.error || 'No response' }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { type: 'bot', text: 'Eroare API' }]);
    }

    setQuestion('');
    setLoading(false);
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          backgroundColor: '#2563eb',
          color: 'white',
          border: 'none',
          fontSize: '24px',
          cursor: 'pointer',
          zIndex: 1001,
        }}
        title="Deschide chat"
      >
        💬
      </button>

      {open && (
        <div style={{
          position: 'fixed',
          bottom: '90px',
          right: '20px',
          width: '300px',
          height: '400px',
          backgroundColor: 'white',
          border: '1px solid #ccc',
          borderRadius: '10px',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        }}>
          <div style={{ flex: 1, padding: '10px', overflowY: 'auto', fontSize: '14px' }}>
            {messages.map((msg, i) => (
              <div key={i} style={{
                textAlign: msg.type === 'user' ? 'right' : 'left',
                marginBottom: '10px',
                whiteSpace: 'pre-wrap',
                color: msg.type === 'user' ? '#1d4ed8' : '#000'
              }}>
                {msg.text}
              </div>
            ))}
            {loading && <div style={{ fontStyle: 'italic' }}>AI răspunde...</div>}
          </div>
          <div style={{ padding: '10px', borderTop: '1px solid #eee' }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Întrebare..."
              style={{ width: '80%', padding: '5px' }}
            />
            <button onClick={sendQuestion} style={{ padding: '5px 10px', marginLeft: '5px' }}>
              Trimite
            </button>
          </div>
        </div>
      )}
    </>
  );
}
