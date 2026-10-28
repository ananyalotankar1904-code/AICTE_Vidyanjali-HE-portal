import React from 'react';

export const GuidePage: React.FC = () => {
  const steps = ['Submitted', 'Validation', 'Scrutiny', 'Review', 'Decision'];

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Process guide</h1>
          <p>Understand the approval journey and the actions required at each stage.</p>
        </div>
      </div>

      <section className="card">
        <div className="progress">
          {steps.map((s, i) => (
            <div key={s} className={`step ${i < 2 ? 'done' : i === 2 ? 'current' : ''}`}>
              <i>{i < 2 ? '✓' : i + 1}</i>
              {s}
            </div>
          ))}
        </div>
        <p className="notice" style={{ marginBottom: '24px' }}>
          EVC and committee review are applicable only when required by the configured route.
        </p>

        <div className="listrow">
          <div>
            <strong>1. Submit and validate</strong>
            <small>Provide institutional details, upload mandatory compliance files, and complete basic validation checks.</small>
          </div>
        </div>

        <div className="listrow">
          <div>
            <strong>2. Scrutiny and corrections</strong>
            <small>Prepare meeting documents, participate in online scrutiny hearings, and submit timely deficiency responses if notices are raised.</small>
          </div>
        </div>

        <div className="listrow">
          <div>
            <strong>3. Conditional reviews</strong>
            <small>Expert Visiting Committee (EVC) physical inspections and Standing Appellate Committee (SAC) reviews apply solely to designated institutional routes.</small>
          </div>
        </div>

        <div className="listrow">
          <div>
            <strong>4. Decision</strong>
            <small>Formal statutory decisions (Approved, Approved with Conditions, Rejected) are issued strictly by the authorised Competent Authority Secretariat.</small>
          </div>
        </div>
      </section>
    </div>
  );
};

