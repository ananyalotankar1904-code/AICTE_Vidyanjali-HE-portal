import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const EvcPage: React.FC = () => {
  const navigate = useNavigate();
  const { appId, institutionName, canonicalData, showToast } = usePortal();
  const [activeTab, setActiveTab] = useState<'agenda' | 'calendar'>('agenda');

  const evcRecords = canonicalData.evcs || [];

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>EVC management</h1>
          <p>Inspection and committee activities apply only to configured routes.</p>
        </div>
        <button className="btn" onClick={() => navigate('/case')}>
          Open case
        </button>
      </div>

      <div className="tabs">
        <button
          className={`btn ${activeTab === 'agenda' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('agenda');
            showToast('Agenda view selected');
          }}
        >
          Agenda
        </button>
        <button
          className={`btn ${activeTab === 'calendar' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('calendar');
            showToast('Calendar view selected');
          }}
        >
          Calendar
        </button>
      </div>

      <section className="card">
        <div className="cardhead">
          <h2>Applicable inspection</h2>
        </div>

        <div className="listrow">
          <div>
            <strong>Illustrative EVC inspection</strong>
            <small>
              {institutionName} · {appId}
            </small>
            <small>Committee, date, mode and evidence: Not available in supplied dataset.</small>
          </div>
          <span className="badge amber">Scheduling required</span>
        </div>

        {evcRecords.map((evc: any) => (
          <div key={evc.evc_id || evc.id} className="listrow">
            <div>
              <strong>
                {evc.evc_id}: {evc.committee_lead || 'Expert Inspection Team'}
              </strong>
              <small>
                Target Application: {evc.application_id} · Scheduled:{' '}
                {evc.scheduled_date || 'November 2026'} · Mode: {evc.visit_mode || 'On-site'}
              </small>
              <small>
                Evidence Upload: {evc.evidence_status || 'Pending'} · Outcome:{' '}
                {evc.review_outcome || 'Awaiting visit'}
              </small>
            </div>
            <span
              className={`badge ${
                evc.status === 'Completed'
                  ? 'green'
                  : evc.status === 'Scheduled'
                  ? 'blue'
                  : 'amber'
              }`}
            >
              {evc.status || 'Scheduled'}
            </span>
          </div>
        ))}
      </section>

      <p className="notice" style={{ marginTop: '16px' }}>
        This example is conditional; EVC is not mandatory for every application. It is only required for high-risk or specific infrastructure expansions.
      </p>
    </div>
  );
};

