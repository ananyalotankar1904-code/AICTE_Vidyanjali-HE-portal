import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const DocumentsPage: React.FC<{ complianceMode?: boolean }> = ({
  complianceMode = false,
}) => {
  const navigate = useNavigate();
  const {
    institutionName,
    documents,
    simulateDocumentReplace,
    openDialog,
    showToast,
  } = usePortal();

  const [urgencyFilter, setUrgencyFilter] = useState('All states');
  const [categoryFilter, setCategoryFilter] = useState('All categories');

  const complianceDocs = [
    { name: 'Safety certificate', status: 'Verified', category: 'Safety', required: 'Required' },
    { name: 'Infrastructure evidence', status: 'Missing', category: 'Infrastructure', required: 'Required' },
    { name: 'Land records', status: 'Pending Review', category: 'Land', required: 'Required' },
    { name: 'Faculty information', status: 'Verified', category: 'Faculty', required: 'Conditional' },
    { name: 'Undertakings', status: 'Pending Review', category: 'Undertaking', required: 'Required' },
    { name: 'Renewal evidence', status: 'Missing', category: 'Renewal', required: 'Conditional' },
  ];

  const scrutinyDocKeys = Object.keys(documents);

  const handleReplace = (docName: string) => {
    openDialog({
      title: `Replace ${docName}`,
      children: (
        <div>
          <p>Select a file to demonstrate replacement. No file is uploaded.</p>
          <label htmlFor="replace-file">Replacement file</label>
          <input id="replace-file" type="file" />
        </div>
      ),
      confirmLabel: 'Simulate replacement',
      notice: 'This action changes local demo state only.',
      onConfirm: () => {
        simulateDocumentReplace(docName);
      },
    });
  };

  const getStatusBadgeColor = (status: string) => {
    if (status === 'Verified' || status === 'Valid') return 'green';
    if (status === 'Missing' || status === 'Expired') return 'red';
    if (status === 'Pending Review' || status === 'Pending verification') return 'amber';
    return 'blue';
  };

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>{complianceMode ? 'Compliance & undertakings' : 'Documents & readiness'}</h1>
          <p>
            {complianceMode
              ? 'Track validity, renewal and ongoing compliance evidence.'
              : 'Prepare the evidence required for the scrutiny meeting.'}
          </p>
        </div>
      </div>

      {/* 4 Metric cards matching sih_final.html */}
      <div className="grid metrics">
        <div className="card metric">
          <div className="label">Valid evidence</div>
          <strong>{complianceMode ? '2' : '1'}</strong>
          <small>Verified in demo</small>
        </div>
        <div className="card metric">
          <div className="label">Expiring soon</div>
          <strong>0</strong>
          <small>Within 30 days</small>
        </div>
        <div className="card metric">
          <div className="label">Expired / missing</div>
          <strong>{complianceMode ? '2' : '1'}</strong>
          <small>Action required</small>
        </div>
        <div className="card metric">
          <div className="label">Pending review</div>
          <strong>2</strong>
          <small>Awaiting review</small>
        </div>
      </div>

      <section className="card">
        <div className="cardhead">
          <div>
            <h2>{complianceMode ? 'Compliance inventory' : 'Scrutiny meeting documents'}</h2>
            <p>Document records are illustrative; absent source values are identified.</p>
          </div>
          {complianceMode ? (
            <button className="btn text" onClick={() => navigate('/documents')}>
              Meeting documents →
            </button>
          ) : (
            <button className="btn text" onClick={() => navigate('/compliance')}>
              Compliance inventory →
            </button>
          )}
        </div>

        {/* Filters toolbar matching sih_final.html */}
        <div className="filters">
          <select
            value={urgencyFilter}
            aria-label="Filter urgency"
            onChange={(e) => setUrgencyFilter(e.target.value)}
          >
            <option>All states</option>
            <option>Missing</option>
            <option>Verified</option>
            <option>Pending Review</option>
          </select>
          <select
            value={categoryFilter}
            aria-label="Filter category"
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option>All categories</option>
            <option>Evidence</option>
            <option>Safety</option>
            <option>Infrastructure</option>
          </select>
          <select aria-label="Filter institution">
            <option>All institutions</option>
            <option>{institutionName}</option>
          </select>
        </div>

        {/* List of Documents */}
        {complianceMode ? (
          <div>
            {complianceDocs
              .filter(
                (d) =>
                  urgencyFilter === 'All states' ||
                  d.status.toLowerCase().includes(urgencyFilter.toLowerCase())
              )
              .map((d) => (
                <div key={d.name} className="listrow">
                  <div>
                    <strong>{d.name}</strong>
                    <small>
                      {d.required} · Category: {d.category} · Version / expiry: Not available in supplied dataset.
                    </small>
                    <small>Reviewer note: Not available in supplied dataset.</small>
                  </div>
                  <div className="buttonrow">
                    <span className={`badge ${getStatusBadgeColor(d.status)}`}>{d.status}</span>
                    <button
                      className="btn"
                      onClick={() => showToast('No supplied previous versions available.')}
                    >
                      Previous versions
                    </button>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div>
            {scrutinyDocKeys
              .filter(
                (k) =>
                  urgencyFilter === 'All states' ||
                  documents[k].toLowerCase().includes(urgencyFilter.toLowerCase())
              )
              .map((d, i) => {
                const status = documents[d];
                return (
                  <div key={d} className="listrow">
                    <div>
                      <strong>{d}</strong>
                      <small>
                        {i === 3 ? 'Conditional' : 'Required'} · Version / expiry: Not available in supplied dataset.
                      </small>
                      <small>Reviewer note: Not available in supplied dataset.</small>
                    </div>
                    <div className="buttonrow">
                      <span className={`badge ${getStatusBadgeColor(status)}`}>{status}</span>
                      <button className="btn" onClick={() => handleReplace(d)}>
                        Replace
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </section>
    </div>
  );
};

