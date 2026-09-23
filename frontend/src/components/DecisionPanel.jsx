import { useState } from 'react'

const DECISIONS = [
  { key: 'accepted', label: 'Accept preparation', hint: 'The prepared view and recommendation are sound.' },
  { key: 'amended', label: 'Accept with amendments', hint: 'Broadly right, but you changed something.' },
  { key: 'rejected', label: 'Reject preparation', hint: 'The preparation is wrong or unusable.' },
]

export default function DecisionPanel({ claim, onDecided }) {
  const [handler, setHandler] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const decided = claim.status && !['prepared', 'processing'].includes(claim.status)

  const submit = async (decision) => {
    if (!handler.trim()) { setError('Enter your name: decisions are never anonymous.'); return }
    setBusy(true); setError(null)
    try {
      const response = await fetch(`/api/claims/${claim.claim_id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, handler, note }),
      })
      if (!response.ok) throw new Error((await response.json()).detail || response.statusText)
      onDecided?.()
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  if (decided) {
    return (
      <section className="decision done">
        <h3>Handler decision</h3>
        <p>
          <strong className={`status status-${claim.status}`}>{claim.status}</strong>
          {' '}by {claim.handler} at {claim.decided_at}
        </p>
        {claim.handler_note && <p className="muted">“{claim.handler_note}”</p>}
      </section>
    )
  }

  return (
    <section className="decision">
      <h3>Handler decision</h3>
      <p className="muted">
        The workspace prepares and recommends. Approving, declining or paying a claim stays with
        authorised staff outside this tool.
      </p>
      <div className="row">
        <input
          placeholder="Your name"
          value={handler}
          onChange={(e) => setHandler(e.target.value)}
        />
      </div>
      <textarea
        placeholder="Note (what you checked, what you changed)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={3}
      />
      {error && <div className="banner error">{error}</div>}
      <div className="decision-buttons">
        {DECISIONS.map((d) => (
          <button
            key={d.key}
            disabled={busy}
            title={d.hint}
            className={d.key === 'rejected' ? 'danger' : ''}
            onClick={() => submit(d.key)}
          >
            {d.label}
          </button>
        ))}
      </div>
    </section>
  )
}
