import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal, ROLES } from '../context/PortalContext';

export const DeficienciesPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    role,
    appId,
    deficiencyStatus,
    deficiencyResponse,
    deficiencyOutcome,
    submitDeficiencyResponse,
    reviewDeficiencyResponse,
    openDialog,
    showToast,
  } = usePortal();

  const isApplicant = role === ROLES[0];

  const handleRespond = () => {
    let responseText = '';

    openDialog({
      title: 'Respond to deficiency',
      children: (
        <div>
          <p>Describe the correction and replace the requested evidence before submitting.</p>
          <label htmlFor="deficiency-response-text">Applicant response</label>
          <textarea
            id="deficiency-response-text"
            placeholder="Describe the correction"
            onChange={(e) => {
              responseText = e.target.value;
            }}
          />
        </div>
      ),
      confirmLabel: 'Submit mock response',
      notice: 'This action changes local demo state only.',
      onConfirm: () => {
        if (!responseText.trim()) {
          showToast('Add a response before submitting.');
          return;
        }
        submitDeficiencyResponse(responseText);
      },
    });
  };

  const handleReview = () => {
    let outcome: 'Resolved' | 'Retained / reopen' = 'Resolved';
    let reviewReason = '';

    openDialog({
      title: 'Review response',
      children: (
        <div>
          <p>Review the institution response and record a mock outcome.</p>
          <label htmlFor="outcome-select">Outcome</label>
          <select
            id="outcome-select"
            defaultValue="Resolved"
            onChange={(e) => {
              outcome = e.target.value as any;
            }}
          >
            <option value="Resolved">Resolve</option>
            <option value="Retained / reopen">Retain / reopen</option>
          </select>
          <label htmlFor="review-reason">Reason</label>
          <textarea
            id="review-reason"
            placeholder="Enter review rationale"
            onChange={(e) => {
              reviewReason = e.target.value;
            }}
          />
        </div>
      ),
      confirmLabel: 'Record mock review',
      notice: 'This action changes local demo state only.',
      onConfirm: () => {
        if (!reviewReason.trim()) {
          showToast('Provide a reason for the review outcome.');
          return;
        }
        reviewDeficiencyResponse(outcome, reviewReason);
      },
    });
  };

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Deficiencies &amp; responses</h1>
          <p>Track corrections and evidence without confusing a deficiency with a rejection.</p>
        </div>
      </div>

      <div className="grid columns">
        {/* Left Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>Deficiency DEMO-DEF-01</h2>
            </div>

            <div className="meta">
              <span
                className={`badge ${
                  deficiencyStatus === 'REVIEWED'
                    ? 'green'
                    : deficiencyStatus === 'RESPONSE_SUBMITTED'
                    ? 'blue'
                    : 'amber'
                }`}
              >
                {deficiencyStatus === 'REVIEWED'
                  ? 'Reviewed'
                  : deficiencyStatus === 'RESPONSE_SUBMITTED'
                  ? 'Response submitted'
                  : 'Open'}
              </span>
              <span>{appId} · Issued by Scrutiny Officer</span>
            </div>

            <p style={{ marginTop: '12px' }}>
              <strong>Response deadline:</strong> 12 November 2026
            </p>

            <div className="banner">
              <div>
                <strong>Correction required</strong>
                <p>
                  Provide the registrar identification and updated authorisation evidence for review.
                </p>
              </div>
            </div>

            <p>
              <strong>Required evidence:</strong> Registrar ID and management authorization letter.
            </p>

            <div className="buttonrow" style={{ marginTop: '16px' }}>
              <button className="btn" onClick={() => navigate('/documents')}>
                Replace evidence
              </button>
              {isApplicant ? (
                <button className="btn primary" onClick={handleRespond}>
                  Add and submit response
                </button>
              ) : (
                <button className="btn primary" onClick={handleReview}>
                  Review response
                </button>
              )}
            </div>
          </section>

          {/* Response History Card */}
          <section className="card">
            <div className="cardhead">
              <h2>Response history</h2>
            </div>
            {deficiencyStatus !== 'OPEN' ? (
              <div>
                <div className="listrow">
                  <div>
                    <strong>Mock response submitted</strong>
                    <small>
                      {deficiencyResponse
                        ? `Response: "${deficiencyResponse}"`
                        : 'Demo interaction · awaiting review'}
                    </small>
                  </div>
                  <span
                    className={`badge ${
                      deficiencyStatus === 'REVIEWED' ? 'green' : 'blue'
                    }`}
                  >
                    {deficiencyStatus === 'REVIEWED'
                      ? `Reviewed (${deficiencyOutcome || 'Resolved'})`
                      : 'Pending review'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="muted">
                No response submitted yet. Add a response after addressing the listed issues.
              </p>
            )}
          </section>
        </div>

        {/* Right Stack */}
        <div className="stack">
          <section className="card">
            <div className="cardhead">
              <h2>What happens next</h2>
            </div>
            <p>
              The officer reviews the response and records whether each issue is resolved or retained.
            </p>
            <p className="notice">
              This notice is a request for correction, not a formal rejection. An overdue deadline does not automatically reject an application.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

