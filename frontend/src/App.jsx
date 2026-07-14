import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchHCPs } from './store/hcpsSlice'
import LogInteractionForm from './components/LogInteractionForm'
import LogInteractionChat from './components/LogInteractionChat'
import InteractionList from './components/InteractionList'

export default function App() {
  const dispatch = useDispatch()
  const [mode, setMode] = useState('form') // 'form' | 'chat'

  useEffect(() => {
    dispatch(fetchHCPs())
  }, [dispatch])

  return (
    <div className="app-shell">
      <div className="app-header">
        <h1>Log HCP Interaction</h1>
      </div>

      <div className="tab-switch">
        <button className={mode === 'form' ? 'active' : ''} onClick={() => setMode('form')}>
          Structured Form
        </button>
        <button className={mode === 'chat' ? 'active' : ''} onClick={() => setMode('chat')}>
          Chat with AI Agent
        </button>
      </div>

      <div className="card">
        {mode === 'form' ? <LogInteractionForm /> : <LogInteractionChat />}
      </div>

      <div className="interaction-list">
        <h2 style={{ fontSize: 16 }}>Recent Interactions</h2>
        <InteractionList />
      </div>
    </div>
  )
}
