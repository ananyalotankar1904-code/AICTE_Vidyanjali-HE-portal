import React from 'react';

export const BpmnPage: React.FC = () => {
  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>BPMN Workflow Showcase &amp; Simulation</h1>
          <p>
            Process specification and interactive execution simulator illustrating state transitions and scenario execution.
          </p>
        </div>
        <a
          href="/bpmn-showcase.html"
          target="_blank"
          rel="noopener noreferrer"
          className="btn primary"
        >
          Open standalone showcase ↗
        </a>
      </div>

      <section className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line)', background: '#fffdf6' }}>
          <strong>Interactive Process Simulator View</strong>
          <p className="notice" style={{ margin: '4px 0 0' }}>
            Fully decoupled offline simulator running canonical scenarios (Direct Approval, Deficiency Loop, EVC Physical Inspection, Statutory Rejection).
          </p>
        </div>
        <iframe
          src="/bpmn-showcase.html"
          title="BPMN Showcase Simulator"
          style={{
            width: '100%',
            height: '750px',
            border: 'none',
            display: 'block',
          }}
        />
      </section>
    </div>
  );
};

