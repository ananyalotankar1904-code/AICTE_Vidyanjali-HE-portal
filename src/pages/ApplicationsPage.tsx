import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const ApplicationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { appId, institutionName, canonicalData, deficiencyStatus, setAppId } = usePortal();

  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  const [attentionFilter, setAttentionFilter] = useState('');

  // Combine canonical applications from Dataset 2 with the active demo case
  const allApps = [
    {
      id: appId,
      institution: institutionName,
      location: 'Pune, Maharashtra',
      type: 'Extension of approval',
      stage: 'Scrutiny',
      owner: 'Scrutiny Officer',
      readiness: '1 of 4 verified',
      readinessState:
        deficiencyStatus === 'RESPONSE_SUBMITTED'
          ? 'Response submitted'
          : deficiencyStatus === 'REVIEWED'
          ? 'Reviewed'
          : 'Deficiency open',
      deadline: '12 Nov 2026',
      meeting: 'Meeting 05 Nov',
      actionNeeded: true,
    },
    ...canonicalData.applications.map((a: any) => {
      const inst = (canonicalData.institutions as Record<string, any>)[a.institution_id] || {};
      const stageName =
        a.current_stage === 'INITIAL_SCRUTINY' || a.current_stage === 'RE_SCRUTINY'
          ? 'Scrutiny'
          : a.current_stage === 'DECISION_PENDING' || a.current_stage === 'COMPLETED'
          ? 'Decision'
          : a.current_stage === 'EVC_SCHEDULED' || a.current_stage === 'EVC_COMPLETED'
          ? 'EVC'
          : a.current_stage === 'DRAFT'
          ? 'Draft'
          : 'Submitted';

      return {
        id: a.application_id,
        institution: inst.name || `Institution ${a.institution_id}`,
        location: `${inst.district || 'District'}, ${inst.state || 'State'}`,
        type: a.application_type || 'Standard Approval',
        stage: stageName,
        owner: a.assigned_role || 'Intake Officer',
        readiness: a.deficiency_flag === 'Yes' ? 'Deficient' : 'Documents Submitted',
        readinessState: a.deficiency_flag === 'Yes' ? 'Deficiency open' : 'Verified',
        deadline: '15 Nov 2026',
        meeting: 'Scheduled',
        actionNeeded: a.application_status === 'ACTION_REQUIRED' || a.deficiency_flag === 'Yes',
      };
    }),
  ];

  // Filtering logic
  const filteredApps = allApps.filter((app) => {
    const textMatch =
      !search ||
      `${app.id} ${app.institution} ${app.location}`
        .toLowerCase()
        .includes(search.toLowerCase());

    const stageMatch = !stageFilter || app.stage.toLowerCase() === stageFilter.toLowerCase();
    const attentionMatch = !attentionFilter || (attentionFilter === 'Action needed' && app.actionNeeded);

    return textMatch && stageMatch && attentionMatch;
  });

  const handleOpenCase = (id: string) => {
    setAppId(id);
    navigate(`/applications/${id}`);
  };

  const handleReset = () => {
    setSearch('');
    setStageFilter('');
    setAttentionFilter('');
  };

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Application registry</h1>
          <p>Search and manage applications across the illustrative cycle.</p>
        </div>
        <button className="btn primary" onClick={() => navigate('/applications/new')}>
          New application
        </button>
      </div>

      <section className="card">
        {/* Filters bar matching sih_final.html */}
        <div className="filters">
          <input
            id="search"
            value={search}
            placeholder="Search ID, institution or location"
            aria-label="Search applications"
            onChange={(e) => setSearch(e.target.value)}
          />
          <select
            id="stage"
            value={stageFilter}
            aria-label="Filter stage"
            onChange={(e) => setStageFilter(e.target.value)}
          >
            <option value="">All stages</option>
            <option value="Scrutiny">Scrutiny</option>
            <option value="Decision">Decision</option>
            <option value="EVC">EVC</option>
            <option value="Submitted">Submitted</option>
          </select>
          <select
            id="attention"
            value={attentionFilter}
            aria-label="Filter attention"
            onChange={(e) => setAttentionFilter(e.target.value)}
          >
            <option value="">All attention states</option>
            <option value="Action needed">Action needed</option>
          </select>
          <button className="btn" onClick={handleReset}>
            Reset filters
          </button>
        </div>

        <p className="notice" id="count">
          {filteredApps.length} {filteredApps.length === 1 ? 'result' : 'results'} · Synthetic demo data
        </p>

        {filteredApps.length === 0 ? (
          <div className="empty">
            <strong>No matching applications</strong>
            <p>Try a different search or reset filters.</p>
          </div>
        ) : (
          <div className="tablewrap">
            <table>
              <thead>
                <tr>
                  <th>Application / institution</th>
                  <th>Stage &amp; owner</th>
                  <th>Readiness</th>
                  <th>Deadline / slot</th>
                  <th>Next action</th>
                </tr>
              </thead>
              <tbody>
                {filteredApps.map((row) => (
                  <tr key={row.id}>
                    <td data-label="Application">
                      <strong>{row.id}</strong>
                      <small>{row.institution}</small>
                    </td>
                    <td data-label="Stage">
                      {row.stage}
                      <small>{row.owner}</small>
                    </td>
                    <td data-label="Documents">
                      <span className={`badge ${row.readiness.includes('verified') ? 'amber' : ''}`}>
                        {row.readiness}
                      </span>
                      <small>{row.readinessState}</small>
                    </td>
                    <td data-label="Deadline">
                      {row.deadline}
                      <small>{row.meeting}</small>
                    </td>
                    <td data-label="Action">
                      <button className="btn text" onClick={() => handleOpenCase(row.id)}>
                        Open case →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="listrow" style={{ marginTop: '16px' }}>
          <span className="notice">Page 1 of 1</span>
          <button className="btn" disabled>
            Next
          </button>
        </div>
      </section>
    </div>
  );
};

