import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const NewApplicationPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = usePortal();

  const [institutionName, setInstitutionName] = useState('');
  const [appType, setAppType] = useState('Extension of approval');
  const [location, setLocation] = useState('');

  const handleSaveDraft = () => {
    showToast('Demo draft only; no application was submitted.');
    setTimeout(() => {
      navigate('/applications');
    }, 1200);
  };

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>New application intake</h1>
          <p>Enter basic details for an illustrative application.</p>
        </div>
      </div>

      <section className="card">
        <div style={{ display: 'grid', gap: '14px' }}>
          <div>
            <label htmlFor="inst" style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '5px' }}>
              Institution name
            </label>
            <input
              id="inst"
              value={institutionName}
              placeholder="Enter institution name"
              style={{ width: '100%' }}
              onChange={(e) => setInstitutionName(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="type" style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '5px' }}>
              Application type
            </label>
            <select
              id="type"
              value={appType}
              style={{ width: '100%' }}
              onChange={(e) => setAppType(e.target.value)}
            >
              <option>Extension of approval</option>
              <option>New application</option>
              <option>Increase in Intake</option>
              <option>New Course</option>
            </select>
          </div>

          <div>
            <label htmlFor="location" style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '5px' }}>
              Location
            </label>
            <input
              id="location"
              value={location}
              placeholder="Enter location (e.g. Pune, Maharashtra)"
              style={{ width: '100%' }}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>

        <hr className="divider" />

        <button className="btn primary" onClick={handleSaveDraft}>
          Save demo draft
        </button>
      </section>
    </div>
  );
};

