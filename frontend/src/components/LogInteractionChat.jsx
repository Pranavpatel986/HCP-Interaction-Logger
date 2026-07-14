import React, { useState, useRef, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { sendChatMessage } from '../store/chatSlice'
import { fetchInteractions } from '../store/interactionsSlice'

// Lightweight markdown renderer for agent replies: supports **bold**,
// dash-bulleted lists, and line breaks. Avoids pulling in a full markdown
// library for a handful of formatting cases.
function renderFormatted(text) {
  const renderInline = (line, key) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean)
    return (
      <span key={key}>
        {parts.map((part, i) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={i}>{part.slice(2, -2)}</strong>
          ) : (
            <React.Fragment key={i}>{part}</React.Fragment>
          )
        )}
      </span>
    )
  }

  const lines = text.split('\n')
  const elements = []
  let listBuffer = []

  const flushList = (key) => {
    if (listBuffer.length) {
      elements.push(
        <ul key={`ul-${key}`} style={{ margin: '4px 0', paddingLeft: 18 }}>
          {listBuffer.map((item, i) => (
            <li key={i}>{renderInline(item, i)}</li>
          ))}
        </ul>
      )
      listBuffer = []
    }
  }

  lines.forEach((line, idx) => {
    const trimmed = line.trim()
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      listBuffer.push(trimmed.slice(2))
    } else {
      flushList(idx)
      if (trimmed.length > 0) {
        elements.push(<div key={idx}>{renderInline(trimmed, idx)}</div>)
      }
    }
  })
  flushList('end')

  return elements
}

export default function LogInteractionChat() {
  const dispatch = useDispatch()
  const { messages, status } = useSelector((state) => state.chat)
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    const text = input
    setInput('')
    await dispatch(sendChatMessage(text))
    // refresh the interaction list in case the agent logged/edited something
    dispatch(fetchInteractions())
  }

  return (
    <div>
      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-bubble agent">
            Hi! Tell me about a visit — e.g. "I met Dr. Sarah Chen today, discussed Drug A,
            she was positive and wants follow-up data next week."
          </div>
        )}
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.role === 'user' ? 'user' : 'agent'}`}>
            {m.role === 'agent' ? renderFormatted(m.text) : m.text}
            {m.tool && <div className="tool-tag">🛠 tool used: {m.tool}</div>}
          </div>
        ))}
        {status === 'loading' && <div className="chat-bubble agent">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe the interaction, or ask to edit a previous one..."
        />
        <button className="btn-primary" type="submit">
          Send
        </button>
      </form>
    </div>
  )
}
