import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar as CalendarIcon,
  List,
  Upload,
  UserPlus,
  CheckCircle,
  Clock,
  MoreVertical,
  FileCheck,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { toast } from '../components/common/Toast';
import { useStore } from '../hooks/useStore';
import { EvcRecord } from '../types';

export const EvcManagementPage: React.FC = () => {
  const navigate = useNavigate();
  const { evcs, applications, store } = useStore();

  const [viewMode, setViewMode] = useState<'List' | 'Calendar'>('List');
  const [selectedEvc, setSelectedEvc] = useState<EvcRecord | null>(null);
  const [modalType, setModalType] = useState<
    'reschedule' | 'assign' | 'evidence' | 'complete' | 'actions' | null
  >(null);

  // Form input states for modals
  const [inputDate, setInputDate] = useState('');
  const [inputMembers, setInputMembers] = useState('');
  const [inputEvidenceFile, setInputEvidenceFile] = useState('');
  const [inputNotes, setInputNotes] = useState('');
  const [formError, setFormError] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const getAppName = (appId: string) => {
    return applications.find((a) => a.id === appId)?.name || appId;
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const openModal = (
    type: 'reschedule' | 'assign' | 'evidence' | 'complete' | 'actions',
    evc: EvcRecord
  ) => {
    setSelectedEvc(evc);
    setModalType(type);
    setInputDate(evc.date);
    setInputMembers(evc.members === 'Assignment pending' ? '' : evc.members);
    setInputEvidenceFile('');
    setInputNotes('');
    setFormError('');
  };

  const closeModal = () => {
    setModalType(null);
    setSelectedEvc(null);
    setFormError('');
    setIsBusy(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc) return;

    setIsBusy(true);

    setTimeout(() => {
      try {
        if (modalType === 'reschedule') {
          if (!inputDate) throw new Error('Choose a valid inspection date');
          store.rescheduleEvc(selectedEvc.id, inputDate);
          toast.show(`Inspection for ${getAppName(selectedEvc.app)} rescheduled to ${formatDate(inputDate)}.`, 'info');
        } else if (modalType === 'assign') {
          if (!inputMembers.trim()) throw new Error('Enter committee member names');
          store.assignEvc(selectedEvc.id, inputMembers.trim());
          toast.show('EVC committee assignment saved.', 'success');
        } else if (modalType === 'evidence') {
          const filename = inputEvidenceFile || 'Inspection_Report_Verified.pdf';
          store.uploadEvcEvidence(selectedEvc.id, filename);
          toast.show(`Evidence file attached: ${filename}`, 'success');
        } else if (modalType === 'complete') {
          if (selectedEvc.evidence === 'Not uploaded' && !inputEvidenceFile) {
            throw new Error('Please upload an inspection evidence report before completing the EVC.');
          }
          store.completeEvc(selectedEvc.id, inputNotes || 'Inspection concluded and report filed.');
          toast.show(`Inspection marked complete for ${getAppName(selectedEvc.app)}.`, 'success');
        }

        closeModal();
      } catch (err: any) {
        setFormError(err?.message || 'Operation failed');
        setIsBusy(false);
      }
    }, 350);
  };

  const completedCount = evcs.filter((e) => e.status === 'Completed').length;

  return (
    <div>
      {/* Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Inspection Coordination</div>
          <h1 className="page-title">Expert Visiting Committee (EVC)</h1>
          <p className="page-subtitle">
            Plan physical and virtual inspection visits, assign academic committee members, track
            geo-tagged evidence reports, and verify infrastructure readiness.
          </p>
        </div>

        <div className="head-actions">
          <div
            style={{
              display: 'inline-flex',
              background: 'var(--surface)',
              padding: '3px',
              borderRadius: 'var(--radius-sm)',
              gap: '2px',
            }}
          >
            <button
              type="button"
              className={`button ${viewMode === 'List' ? 'primary' : 'ghost'}`}
              style={{ minHeight: '34px', padding: '4px 12px', fontSize: '12px' }}
              onClick={() => setViewMode('List')}
            >
              <List size={14} /> List View
            </button>
            <button
              type="button"
              className={`button ${viewMode === 'Calendar' ? 'primary' : 'ghost'}`}
              style={{ minHeight: '34px', padding: '4px 12px', fontSize: '12px' }}
              onClick={() => setViewMode('Calendar')}
            >
              <CalendarIcon size={14} /> Calendar View
            </button>
          </div>
        </div>
      </div>

      {/* Main View Area */}
      {viewMode === 'List' ? (
        <Card padded={false}>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>EVC Code</th>
                  <th>Institution Name</th>
                  <th>Committee Members</th>
                  <th>Scheduled Date</th>
                  <th>Visit Mode</th>
                  <th>Status</th>
                  <th>Evidence Report</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {evcs.map((evc) => (
                  <tr key={evc.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 650 }}>{evc.id}</td>
                    <td>
                      <button
                        type="button"
                        className="table-institution"
                        onClick={() => navigate(`/applications/${evc.app}`)}
                      >
                        {getAppName(evc.app)}
                      </button>
                      <span className="table-sub">{evc.app}</span>
                    </td>
                    <td>{evc.members}</td>
                    <td>{formatDate(evc.date)}</td>
                    <td>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: evc.mode === 'Virtual' ? '#f0fdf4' : 'var(--surface-ivory)',
                          color: evc.mode === 'Virtual' ? '#166534' : 'var(--accent-active)',
                          border: evc.mode === 'Virtual' ? '1px solid #bbf7d0' : '1px solid var(--accent-border)',
                          fontSize: '11px',
                          fontWeight: 650,
                        }}
                      >
                        {evc.mode}
                      </span>
                    </td>
                    <td>
                      <Badge statusText={evc.status}>{evc.status}</Badge>
                    </td>
                    <td>
                      {evc.evidence === 'Not uploaded' ? (
                        <span style={{ color: 'var(--muted)', fontSize: '12px' }}>Not uploaded</span>
                      ) : (
                        <button
                          type="button"
                          className="button ghost"
                          style={{ minHeight: '28px', padding: '0 8px', fontSize: '12px' }}
                          onClick={() => openModal('evidence', evc)}
                        >
                          <FileCheck size={13} /> {evc.evidence}
                        </button>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        type="button"
                        className="icon-btn"
                        onClick={() => openModal('actions', evc)}
                        aria-label={`Actions for ${evc.id}`}
                      >
                        <MoreVertical size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card>
          <CardHeader
            title="November 2026 Inspection Schedule"
            subtitle="Click any scheduled event to inspect committee assignments or modify dates"
          />
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, 1fr)',
              gap: '6px',
              marginTop: '12px',
            }}
          >
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
              <div
                key={d}
                style={{
                  textAlign: 'center',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: 'var(--muted)',
                  padding: '6px',
                }}
              >
                {d}
              </div>
            ))}
            {Array.from({ length: 35 }, (_, i) => {
              const day = i + 1;
              const dateKey = `2026-11-${String(day).padStart(2, '0')}`;
              const dayEvcs = evcs.filter((e) => e.date === dateKey);
              if (day > 30) {
                return (
                  <div
                    key={i}
                    style={{
                      minHeight: '76px',
                      background: 'transparent',
                      borderRadius: '6px',
                    }}
                  />
                );
              }
              return (
                <div
                  key={i}
                  style={{
                    minHeight: '76px',
                    background: '#ffffff',
                    border: '1px solid var(--border-soft)',
                    borderRadius: '8px',
                    padding: '8px',
                    fontSize: '11px',
                  }}
                >
                  <b style={{ color: 'var(--ink)' }}>{day}</b>
                  {dayEvcs.map((e) => (
                    <button
                      key={e.id}
                      type="button"
                      onClick={() => openModal('actions', e)}
                      style={{
                        display: 'block',
                        width: '100%',
                        textAlign: 'left',
                        background: 'var(--surface-ivory)',
                        color: 'var(--ink)',
                        border: '1px solid var(--accent-border)',
                        borderRadius: '5px',
                        fontSize: '10px',
                        lineHeight: 1.3,
                        padding: '4px 6px',
                        marginTop: '4px',
                        cursor: 'pointer',
                        fontWeight: 650,
                      }}
                    >
                      {getAppName(e.app)}
                    </button>
                  ))}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Summary KPI Cards */}
      <div className="split-lower" style={{ marginTop: '22px' }}>
        <Card>
          <CardHeader
            title="Upcoming Inspection"
            subtitle="Next scheduled committee visit"
          />
          <p style={{ fontWeight: 700, fontSize: '15px', color: 'var(--ink)' }}>
            Chennai Technical University (AI-2026-1794)
          </p>
          <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '4px 0 16px' }}>
            07 Nov 2026 · On-site Inspection · Dr Meera Shah, Prof. S. Iyer
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              const item = evcs.find((e) => e.id === 'EVC-301');
              if (item) openModal('actions', item);
            }}
          >
            Manage Inspection EVC-301
          </Button>
        </Card>

        <Card>
          <CardHeader
            title="Completion Status"
            subtitle="Cycle progress across registered committee visits"
          />
          <p style={{ fontWeight: 700, fontSize: '20px', color: 'var(--ink)' }}>
            {completedCount} of {evcs.length} inspections completed
          </p>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            Reports and photo evidence remain permanently attached to each application case file.
          </p>
        </Card>
      </div>

      {/* --- Action Modals --- */}

      {/* 1. EVC Quick Actions Menu Modal */}
      {selectedEvc && (
        <Modal
          isOpen={modalType === 'actions'}
          onClose={closeModal}
          title={`Inspection Management: ${selectedEvc.id}`}
          subtitle={`${getAppName(selectedEvc.app)} · ${formatDate(selectedEvc.date)} · ${selectedEvc.status}`}
          footer={
            <Button variant="secondary" onClick={closeModal}>
              Close
            </Button>
          }
        >
          <div style={{ display: 'grid', gap: '10px' }}>
            <Button
              variant="secondary"
              onClick={() => openModal('reschedule', selectedEvc)}
              icon={<Clock size={15} />}
              style={{ justifyContent: 'flex-start' }}
            >
              Reschedule Inspection Date
            </Button>
            <Button
              variant="secondary"
              onClick={() => openModal('assign', selectedEvc)}
              icon={<UserPlus size={15} />}
              style={{ justifyContent: 'flex-start' }}
            >
              Assign / Update Committee Members
            </Button>
            <Button
              variant="secondary"
              onClick={() => openModal('evidence', selectedEvc)}
              icon={<Upload size={15} />}
              style={{ justifyContent: 'flex-start' }}
            >
              {selectedEvc.evidence === 'Not uploaded' ? 'Attach Inspection Report' : 'Inspect Attached Report'}
            </Button>
            <Button
              variant="primary"
              onClick={() => openModal('complete', selectedEvc)}
              disabled={selectedEvc.status === 'Completed'}
              icon={<CheckCircle size={15} />}
              style={{ justifyContent: 'flex-start' }}
            >
              Mark Inspection as Completed
            </Button>
          </div>
        </Modal>
      )}

      {/* 2. Reschedule Modal */}
      {selectedEvc && (
        <Modal
          isOpen={modalType === 'reschedule'}
          onClose={closeModal}
          title="Reschedule Inspection Date"
          subtitle={`Update committee inspection schedule for ${getAppName(selectedEvc.app)}.`}
          footer={
            <>
              <Button variant="secondary" onClick={closeModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSubmit} isLoading={isBusy}>
                Save Schedule
              </Button>
            </>
          }
        >
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="reschedule-date">New Inspection Date</label>
              <input
                id="reschedule-date"
                type="date"
                value={inputDate}
                min="2026-10-25"
                onChange={(e) => setInputDate(e.target.value)}
                required
              />
            </div>
            {formError && <p className="field-error">{formError}</p>}
          </form>
        </Modal>
      )}

      {/* 3. Assign Committee Modal */}
      {selectedEvc && (
        <Modal
          isOpen={modalType === 'assign'}
          onClose={closeModal}
          title="Assign Visiting Committee"
          subtitle={`Nominate evaluators for ${getAppName(selectedEvc.app)}.`}
          footer={
            <>
              <Button variant="secondary" onClick={closeModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSubmit} isLoading={isBusy}>
                Save Committee
              </Button>
            </>
          }
        >
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="assign-members">Committee Evaluator Names (Comma separated)</label>
              <input
                id="assign-members"
                type="text"
                placeholder="e.g. Dr. A. Sharma, Prof. K. Venkatesh"
                value={inputMembers}
                onChange={(e) => setInputMembers(e.target.value)}
                required
              />
            </div>
            {formError && <p className="field-error">{formError}</p>}
          </form>
        </Modal>
      )}

      {/* 4. Evidence Modal */}
      {selectedEvc && (
        <Modal
          isOpen={modalType === 'evidence'}
          onClose={closeModal}
          title="Inspection Report & Evidence"
          subtitle={`${getAppName(selectedEvc.app)} · Current file: ${selectedEvc.evidence}`}
          footer={
            <>
              <Button variant="secondary" onClick={closeModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSubmit} isLoading={isBusy}>
                Attach Report
              </Button>
            </>
          }
        >
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="evidence-file">Select Inspection Report (PDF / Image)</label>
              <input
                id="evidence-file"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) setInputEvidenceFile(file.name);
                }}
              />
              <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
                Note: In this local demonstration, the filename reference is attached to the audit trail.
              </p>
            </div>
            {formError && <p className="field-error">{formError}</p>}
          </form>
        </Modal>
      )}

      {/* 5. Complete Inspection Modal */}
      {selectedEvc && (
        <Modal
          isOpen={modalType === 'complete'}
          onClose={closeModal}
          title="Confirm Inspection Completion"
          subtitle={`Finalize findings for ${getAppName(selectedEvc.app)}.`}
          footer={
            <>
              <Button variant="secondary" onClick={closeModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSubmit} isLoading={isBusy}>
                Mark Completed
              </Button>
            </>
          }
        >
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="complete-notes">Inspection Summary & Committee Recommendations</label>
              <textarea
                id="complete-notes"
                rows={3}
                placeholder="Summarize physical laboratory checks, library verification, and faculty roster examination."
                value={inputNotes}
                onChange={(e) => setInputNotes(e.target.value)}
                required
              />
            </div>
            {formError && <p className="field-error">{formError}</p>}
          </form>
        </Modal>
      )}
    </div>
  );
};
