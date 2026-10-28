import React from 'react';
import { usePortal } from '../context/PortalContext';

export const AuditPage: React.FC = () => {
  const { appId, auditLogs, canonicalData } = usePortal();

  const baselineEvents = [
    {
      action: 'Application entered scrutiny',
      time: '28 Oct 2026',
      actor: 'Scrutiny Officer',
      app: appId,
      detail: 'Validation → Scrutiny · Reason: Not available in supplied dataset.',
    },
    ...canonicalData.audit_events.slice(0, 10).map((evt: any) => ({
      action: evt.action_performed || evt.action || 'Workflow Stage Transition',
      time: evt.timestamp ? new Date(evt.timestamp).toLocaleDateString('en-IN') : '25 Oct 2026',
      actor: evt.actor_role || evt.actor || 'Intake Officer',
      app: evt.application_id || appId,
      detail: `${evt.stage_before || ''} → ${evt.stage_after || ''} · ${evt.transition_reason || 'Verified canonical action'}`,
    })),
  ];

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Audit history</h1>
          <p>Synthetic baseline events and local demo interactions are shown separately.</p>
        </div>
      </div>

      <section className="card">
        <h2>Current demo interactions</h2>
        <div className="timeline" style={{ marginTop: '16px' }}>
          {auditLogs.length > 0 ? (
            auditLogs.map((item) => (
              <div key={item.id} className="listrow">
                <div>
                  <strong>{item.action}</strong>
                  <small>
                    {item.time} · {item.role} · {item.app}
                  </small>
                  {item.detail && <small>Detail: {item.detail}</small>}
                  <small>Before / after: local demo state</small>
                </div>
              </div>
            ))
          ) : (
            <p className="muted" style={{ padding: '8px 0' }}>
              No interactions recorded in this session. Try scheduling a slot, replacing a document, or submitting a deficiency response!
            </p>
          )}
        </div>

        <hr className="divider" />

        <h2>Synthetic baseline</h2>
        <div className="timeline" style={{ marginTop: '16px' }}>
          {baselineEvents.map((evt, idx) => (
            <div key={idx} className="listrow">
              <div>
                <strong>{evt.action}</strong>
                <small>
                  {evt.time} · {evt.actor} · {evt.app}
                </small>
                <small>{evt.detail}</small>
              </div>
            </div>
          ))}
        </div>

        <p className="notice" style={{ marginTop: '20px' }}>
          Local mock logs are illustrative and are not immutable or tamper-proof.
        </p>
      </section>
    </div>
  );
};

