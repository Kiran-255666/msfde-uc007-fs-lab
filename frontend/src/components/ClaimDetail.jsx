import { useEffect, useState } from 'react'
import DecisionPanel from './DecisionPanel.jsx'

const SEVERITY_ORDER = { critical: 0, warning: 1, info: 2 }

export default function ClaimDetail({ claimId, onDecided }) {
  const [claim, setClaim] = useState(null)
  const [evidence, setEvidence] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    if (!claimId) return
    setLoading(true)
    try {
      const [claimRes, evidenceRes] = await Promise.all([
        fetch(`/api/claims/${claimId}`),
        fetch(`/api/claims/${claimId}/evidence`),
      ])
      setClaim(claimRes.ok ? await claimRes.json() : null)
      setEvidence(evidenceRes.ok ? (await evidenceRes.json()).files : [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [claimId])

  if (!claimId) return <main className="detail empty">Select a claim to review.</main>
  if (loading && !claim) return <main className="detail empty">Loading…</main>
  if (!claim) {
    return (
      <main className="detail empty">
        {claimId} has not been processed yet. Use Process in the list.
      </main>
    )
  }

  const review = claim.review || {}
  const findings = [...(claim.findings || [])].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3),
  )

  return (
    <main className="detail">
      <div className="detail-head">
        <h2>{claim.claim_id}</h2>
        <span className={`rec rec-${review.recommendation}`}>{review.recommendation}</span>
      </div>

      <section>
        <h3>Claim summary</h3>
        <p className="summary">{review.summary || '—'}</p>
      </section>

      <section>
        <h3>Findings ({findings.length})</h3>
        {findings.length === 0 && <p className="muted">No findings. The evidence is complete and consistent.</p>}
        {findings.map((finding, index) => (
          <div key={index} className={`finding sev-${finding.severity}`}>
            <div className="row">
              <strong>{finding.code}</strong>
              <span className="sev">{finding.severity}</span>
            </div>
            <p>{finding.message}</p>
            {finding.evidence?.length > 0 && (
              <div className="evidence-chips">
                {finding.evidence.map((e, i) => (
                  <span key={i} className="chip" title={`${e.document}.${e.field}`}>
                    {e.document}: {String(e.value)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </section>

      {review.findings_explained?.length > 0 && (
        <section>
          <h3>Why these matter</h3>
          {review.findings_explained.map((item, index) => (
            <div key={index} className="explained">
              <div className="row">
                <strong>{item.code}</strong>
                <span className="muted">{item.policy_reference}</span>
              </div>
              <p>{item.explanation}</p>
            </div>
          ))}
        </section>
      )}

      {review.outstanding_items?.length > 0 && (
        <section>
          <h3>Outstanding</h3>
          <ul>{review.outstanding_items.map((item, i) => <li key={i}>{item}</li>)}</ul>
        </section>
      )}

      {review.recommended_next_steps?.length > 0 && (
        <section>
          <h3>Recommended next steps</h3>
          <ol>{review.recommended_next_steps.map((item, i) => <li key={i}>{item}</li>)}</ol>
        </section>
      )}

      <section>
        <h3>Extracted data</h3>
        {Object.entries(claim.extracted || {}).map(([docType, fields]) => (
          <details key={docType}>
            <summary>{docType.replace(/_/g, ' ')}</summary>
            <table className="fields">
              <tbody>
                {Object.entries(fields).map(([name, field]) => (
                  <tr key={name}>
                    <td className="label">{name.replace(/_/g, ' ')}</td>
                    <td>{field.value == null || field.value === '' ? '—' : String(field.value)}</td>
                    <td className={`conf ${field.confidence != null && field.confidence < 0.6 ? 'low' : ''}`}>
                      {field.confidence != null ? field.confidence.toFixed(2) : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        ))}
      </section>

      {claim.photo_assessments?.length > 0 && (
        <section>
          <h3>Photograph assessment</h3>
          <div className="photos">
            {claim.photo_assessments.map((photo) => (
              <figure key={photo.file}>
                <img src={`/api/claims/${claim.claim_id}/file/photos/${photo.file}`} alt={photo.file} />
                <figcaption>
                  <strong>{photo.damage_area}</strong> · {photo.severity}
                  <br />{photo.visible_damage}
                  <br /><span className="muted">indicative {photo.indicative_repair_band}</span>
                </figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3>Evidence on file</h3>
        <ul className="evidence">
          {evidence.map((file) => (
            <li key={file.name}>
              <a href={`/api/claims/${claim.claim_id}/file/${file.name}`} target="_blank" rel="noreferrer">
                {file.name}
              </a>
              <span className="muted"> · {file.type.replace(/_/g, ' ')} · {file.size_kb} KB</span>
            </li>
          ))}
        </ul>
      </section>

      {review.policy_citations?.length > 0 && (
        <section>
          <h3>Policy sources</h3>
          <ul className="citations">
            {review.policy_citations.map((c, i) => (
              <li key={i}>{c.document} — section {c.section}</li>
            ))}
          </ul>
        </section>
      )}

      <DecisionPanel claim={claim} onDecided={() => { load(); onDecided?.() }} />
    </main>
  )
}
