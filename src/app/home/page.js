'use client'

import { useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

export default function Home() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])

    try {
      const res = await axios.post('http://127.0.0.1:8000/ask', { question: input })

      if (res.data.answer) {
        const aiResponse = res.data.answer
        const botMessage = { role: 'assistant', content: aiResponse }
        setMessages((prev) => [...prev, botMessage])
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: res.data.error || '⚠️ No answer returned from backend' }
        ])
      }

    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ Backend error: ' + err.message }
      ])
    }

    setInput('')
  }

  return (
    <main style={{ maxWidth: '600px', margin: 'auto', padding: '20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '16px' }}>Sakila Chat Assistant</h1>

      <div style={{
        minHeight: '400px',
        padding: '10px',
        border: '1px solid #ccc',
        borderRadius: '8px',
        marginBottom: '16px',
        overflowY: 'auto'
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            textAlign: msg.role === 'user' ? 'right' : 'left',
            margin: '8px 0'
          }}>
            <div style={{
              display: 'inline-block',
              background: msg.role === 'user' ? '#0070f3' : '#f4f4f4',
              color: msg.role === 'user' ? '#fff' : '#000',
              padding: '8px 12px',
              borderRadius: '12px',
              maxWidth: '90%',
              wordWrap: 'break-word'
            }}>
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something about Sakila DB..."
          style={{
            flex: 1,
            padding: '10px',
            borderRadius: '8px 0 0 8px',
            border: '1px solid #ccc'
          }}
        />
        <button type="submit" style={{
          padding: '10px 20px',
          borderRadius: '0 8px 8px 0',
          backgroundColor: '#0070f3',
          color: '#fff',
          border: 'none'
        }}>
          Send
        </button>
      </form>
    </main>
  )
}
