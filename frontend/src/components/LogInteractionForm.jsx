import React, { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { createInteraction } from '../store/interactionsSlice'

const INTERACTION_TYPES = ['In-person visit', 'Call', 'Email', 'Conference']
const SENTIMENTS = ['Positive', 'Neutral', 'Negative']

export default function LogInteractionForm() {
  const dispatch = useDispatch()
  const hcps = useSelector((state) => state.hcps.list)

  const [form, setForm] = useState({
    hcp_id: '',
    interaction_type: 'In-person visit',
    products_discussed: '',
    samples_provided: '',
    hcp_sentiment: 'Neutral',
    notes: '',
    follow_up_needed: false,
    follow_up_date: '',
  })

  const update = (key) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [key]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.hcp_id) return
    await dispatch(
      createInteraction({
        ...form,
        follow_up_date: form.follow_up_date ? new Date(form.follow_up_date).toISOString() : null,
        source: 'form',
      })
    )
    setForm((f) => ({ ...f, notes: '', products_discussed: '', samples_provided: '' }))
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label>Healthcare Professional</label>
        <select value={form.hcp_id} onChange={update('hcp_id')} required>
          <option value="">Select HCP...</option>
          {hcps.map((h) => (
            <option key={h.id} value={h.id}>
              {h.name} — {h.specialty}
            </option>
          ))}
        </select>
      </div>

      <div className="row">
        <div className="field">
          <label>Interaction Type</label>
          <select value={form.interaction_type} onChange={update('interaction_type')}>
            {INTERACTION_TYPES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>HCP Sentiment</label>
          <select value={form.hcp_sentiment} onChange={update('hcp_sentiment')}>
            {SENTIMENTS.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="row">
        <div className="field">
          <label>Products Discussed</label>
          <input value={form.products_discussed} onChange={update('products_discussed')} placeholder="e.g. Drug A, Drug B" />
        </div>
        <div className="field">
          <label>Samples Provided</label>
          <input value={form.samples_provided} onChange={update('samples_provided')} placeholder="e.g. 2x Drug A samples" />
        </div>
      </div>

      <div className="field">
        <label>Notes</label>
        <textarea value={form.notes} onChange={update('notes')} placeholder="Additional notes about the visit..." />
      </div>

      <div className="row">
        <div className="field" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" checked={form.follow_up_needed} onChange={update('follow_up_needed')} style={{ width: 'auto' }} />
          <label style={{ margin: 0 }}>Follow-up needed</label>
        </div>
        {form.follow_up_needed && (
          <div className="field">
            <label>Follow-up Date</label>
            <input type="date" value={form.follow_up_date} onChange={update('follow_up_date')} />
          </div>
        )}
      </div>

      <button className="btn-primary" type="submit">
        Save Interaction
      </button>
    </form>
  )
}
