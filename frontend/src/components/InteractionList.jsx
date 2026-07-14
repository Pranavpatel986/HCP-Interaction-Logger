import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { fetchInteractions } from '../store/interactionsSlice'

export default function InteractionList() {
  const dispatch = useDispatch()
  const { list } = useSelector((state) => state.interactions)
  const hcps = useSelector((state) => state.hcps.list)

  useEffect(() => {
    dispatch(fetchInteractions())
  }, [dispatch])

  const hcpName = (id) => hcps.find((h) => h.id === id)?.name || id

  if (list.length === 0) {
    return <p style={{ color: '#888', fontSize: 14 }}>No interactions logged yet.</p>
  }

  return (
    <div>
      {list.map((i) => (
        <div key={i.id} className="interaction-item">
          <div className="meta">
            {new Date(i.interaction_date).toLocaleString()} · {hcpName(i.hcp_id)}
            <span className="badge">{i.source}</span>
          </div>
          <strong>{i.interaction_type}</strong> — {i.hcp_sentiment}
          <p style={{ margin: '6px 0', fontSize: 14 }}>{i.summary || i.notes}</p>
          {i.follow_up_needed && (
            <div style={{ fontSize: 12, color: '#4338ca' }}>
              Follow-up: {i.follow_up_date ? new Date(i.follow_up_date).toLocaleDateString() : 'TBD'}{' '}
              — {i.follow_up_notes}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
