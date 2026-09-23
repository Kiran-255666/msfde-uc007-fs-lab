const RECOMMENDATION_LABEL = {
  proceed: 'Proceed',
  request_information: 'Request info',
  refer: 'Refer',
}

export default function ClaimList({ claims, selected, onSelect, onProcess }) {
  return (
    <aside className="claim-list">
      <h2>Claims</h2>
      {claims.map((claim) => {
        const isSelected = claim.claim_id === selected
        const rec = claim.agent_recommendation
        return (
          <div
            key={claim.claim_id}
            className={`claim-card ${isSelected ? 'selected' : ''}`}
            onClick={() => onSelect(claim.claim_id)}
          >
            <div className="row">
              <strong>{claim.claim_id}</strong>
              {rec && <span className={`rec rec-${rec}`}>{RECOMMENDATION_LABEL[rec] || rec}</span>}
            </div>

            {claim.status === 'not_processed' && (
              <div className="row">
                <span className="muted">Not processed</span>
                <button
                  onClick={(e) => { e.stopPropagation(); onProcess(claim.claim_id) }}
                >
                  Process
                </button>
              </div>
            )}

            {claim.status === 'processing' && <div className="muted">Processing…</div>}

            {claim.finding_count != null && (
              <div className="muted">
                {claim.critical_count > 0 && (
                  <span className="critical-dot" title="critical findings" />
                )}
                {claim.finding_count} finding{claim.finding_count === 1 ? '' : 's'}
                {claim.status && !['prepared', 'processing', 'not_processed'].includes(claim.status)
                  && <> · <span className={`status status-${claim.status}`}>{claim.status}</span></>}
              </div>
            )}
          </div>
        )
      })}
      {claims.length === 0 && <p className="muted">No claims found.</p>}
    </aside>
  )
}
