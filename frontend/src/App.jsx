import { useEffect, useState, useCallback } from 'react'
import ClaimList from './components/ClaimList.jsx'
import ClaimDetail from './components/ClaimDetail.jsx'

export default function App() {
  const [claims, setClaims] = useState([])
  const [selected, setSelected] = useState(null)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  const loadClaims = useCallback(async () => {
    try {
      const response = await fetch('/api/claims')
      if (!response.ok) throw new Error(`claims: ${response.status}`)
      const data = await response.json()
      setClaims(data.claims)
      setError(null)
      return data
    } catch (err) {
      setError(String(err))
      return null
    }
  }, [])

  useEffect(() => {
    fetch('/api/health').then(r => r.json()).then(setHealth).catch(() => {})
    loadClaims()
  }, [loadClaims])

  // While anything is processing, poll so the list updates on its own.
  useEffect(() => {
    const anyProcessing = claims.some(c => c.status === 'processing')
    if (!anyProcessing) return undefined
    const timer = setInterval(loadClaims, 4000)
    return () => clearInterval(timer)
  }, [claims, loadClaims])

  const processClaim = async (claimId) => {
    setClaims(cs => cs.map(c => (c.claim_id === claimId ? { ...c, status: 'processing' } : c)))
    await fetch(`/api/claims/${claimId}/process`, { method: 'POST' })
    setTimeout(loadClaims, 3000)
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Contoso Claims Workspace</h1>
          <p className="sub">
            Motor claim intake and review. Prepared automatically, decided by a handler.
          </p>
        </div>
        {health && (
          <div className="health">
            <span className="pill">{health.alias}</span>
            <span className="muted">{health.counts.prepared} prepared</span>
          </div>
        )}
      </header>

      {error && <div className="banner error">Cannot reach the API: {error}</div>}

      <div className="layout">
        <ClaimList
          claims={claims}
          selected={selected}
          onSelect={setSelected}
          onProcess={processClaim}
        />
        <ClaimDetail claimId={selected} onDecided={loadClaims} />
      </div>

      <footer>
        Training environment. Contoso Insurance is fictional. This workspace never approves,
        declines or pays a claim (CIP-CLM-200 section 5.2).
      </footer>
    </div>
  )
}
