import React, { useState } from 'react';
import {
  Plus,
  Clock,
  AlertTriangle,
  CheckCircle2,
  FileCheck2,
  RefreshCw,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { EmptyState } from '../components/common/EmptyState';
import { toast } from '../components/common/Toast';
import { useStore } from '../hooks/useStore';
import { ComplianceDocument } from '../types';

export const CompliancePage: React.FC = () => {
  const { documents, applications, store } = useStore();

  const [urgencyFilter, setUrgencyFilter] = useState<string>('All');
  const [typeFilter, setTypeFilter] = useState<string>('All');
  const [instFilter, setInstFilter] = useState<string>('All');

  // Modal states
  const [isUndertakingModalOpen, setIsUndertakingModalOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<ComplianceDocument | null>(null);
  const [modalMode, setModalMode] = useState<'renew' | 'verify' | null>(null);

  // Form states
  const [inputInstitution, setInputInstitution] = useState('');
  const [inputTitle, setInputTitle] = useState('');
  const [inputDate, setInputDate] = useState('');
  const [inputFile, setInputFile] = useState('');
  const [inputNote, setInputNote] = useState('');
  const [formError, setFormError] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  // Filtering
  const filteredDocs = documents.filter((doc) => {
    if (urgencyFilter !== 'All' && doc.status !== urgencyFilter) return false;
    if (typeFilter !== 'All' && doc.type !== typeFilter) return false;
    if (instFilter !== 'All' && doc.institution !== instFilter) return false;
    return true;
  });

  const validCount = documents.filter((d) => d.status === 'Valid' || d.status === 'Verified').length;
  const expiringCount = documents.filter((d) => d.status === 'Expiring soon').length;
  const urgentCount = documents.filter((d) => ['Expired', 'Missing'].includes(d.status)).length;

  const formatDate = (dateStr: string) => {
    if (dateStr === '—') return '—';
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

  const handleOpenUndertakingModal = () => {
    setInputInstitution(applications[0]?.name || '');
    setInputTitle('');
    setInputDate('2027-06-30');
    setInputFile('');
    setFormError('');
    setIsUndertakingModalOpen(true);
  };

  const handleOpenDocAction = (doc: ComplianceDocument) => {
    setSelectedDoc(doc);
    setInputDate(doc.expiry !== '—' ? doc.expiry : '2027-12-31');
    setInputFile('');
    setInputNote('');
    setFormError('');
    setModalMode(doc.status === 'Pending verification' ? 'verify' : 'renew');
  };

  const handleCloseModal = () => {
    setIsUndertakingModalOpen(false);
    setSelectedDoc(null);
    setModalMode(null);
    setFormError('');
    setIsBusy(false);
  };

  const handleSubmitUndertaking = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputInstitution || !inputTitle.trim()) {
      setFormError('Please complete all required fields.');
      return;
    }

    setIsBusy(true);
    setTimeout(() => {
      store.submitUndertaking(
        inputInstitution,
        inputTitle.trim(),
        inputDate,
        inputFile || `${inputTitle.trim().replace(/\s+/g, '_')}_Signed.pdf`
      );
      toast.show('Undertaking submitted for compliance verification.', 'success');
      handleCloseModal();
    }, 350);
  };

  const handleSubmitDocAction = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;

    setIsBusy(true);
    setTimeout(() => {
      try {
        if (modalMode === 'verify') {
          store.verifyUndertaking(
            selectedDoc.id,
            inputNote || 'Institutional undertaking reviewed and validated against AICTE norms.'
          );
          toast.show(`Undertaking verified for ${selectedDoc.institution}.`, 'success');
        } else {
          store.renewDocument(
            selectedDoc.id,
            inputDate,
            inputFile || `Renewal_${selectedDoc.name.replace(/\s+/g, '_')}_v${(selectedDoc.version || 1) + 1}.pdf`
          );
          toast.show(
            `Document renewed successfully. Prior version retained in audit history.`,
            'success'
          );
        }
        handleCloseModal();
      } catch (err: any) {
        setFormError(err?.message || 'Operation failed');
        setIsBusy(false);
      }
    }, 350);
  };

  const distinctInstitutions = Array.from(new Set(documents.map((d) => d.institution)));

  return (
    <div>
      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Evidence & Regulatory Validity</div>
          <h1 className="page-title">Compliance & Documents</h1>
          <p className="page-subtitle">
            Track certificate expirations, institutional undertakings, and statutory infrastructure
            evidence. Past document versions remain retained in compliance archives.
          </p>
        </div>

        <div className="head-actions">
          <Button
            variant="primary"
            onClick={handleOpenUndertakingModal}
            icon={<Plus size={16} />}
          >
            Submit Undertaking
          </Button>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="metric-grid">
        <div className="metric-card green">
          <div className="metric-top">
            <span className="metric-label">Valid Evidence</span>
            <span className="metric-icon-wrap">
              <CheckCircle2 size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{validCount}</div>
            <div className="metric-footer">Current and active certificates</div>
          </div>
        </div>

        <div className="metric-card warn">
          <div className="metric-top">
            <span className="metric-label">Expiring Soon</span>
            <span className="metric-icon-wrap">
              <Clock size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{expiringCount}</div>
            <div className="metric-footer">Renewal recommended within 30 days</div>
          </div>
        </div>

        <div className="metric-card danger">
          <div className="metric-top">
            <span className="metric-label">Expired / Missing</span>
            <span className="metric-icon-wrap">
              <AlertTriangle size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{urgentCount}</div>
            <div className="metric-footer">Notice issued; correction required</div>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="toolbar">
        <div className="form-field">
          <label htmlFor="urgency-filter">Urgency / State</label>
          <select
            id="urgency-filter"
            value={urgencyFilter}
            onChange={(e) => setUrgencyFilter(e.target.value)}
          >
            <option value="All">All states</option>
            <option value="Valid">Valid</option>
            <option value="Expiring soon">Expiring soon</option>
            <option value="Expired">Expired</option>
            <option value="Missing">Missing</option>
            <option value="Pending verification">Pending verification</option>
            <option value="Verified">Verified</option>
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="type-filter">Category</label>
          <select
            id="type-filter"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="All">All categories</option>
            <option value="Safety">Safety & NOC</option>
            <option value="Infrastructure">Infrastructure</option>
            <option value="Faculty">Faculty & Appointments</option>
            <option value="Undertaking">Compliance Undertaking</option>
          </select>
        </div>

        <div className="form-field" style={{ minWidth: '240px' }}>
          <label htmlFor="inst-filter">Institution</label>
          <select
            id="inst-filter"
            value={instFilter}
            onChange={(e) => setInstFilter(e.target.value)}
          >
            <option value="All">All institutions</option>
            {distinctInstitutions.map((inst) => (
              <option key={inst} value={inst}>
                {inst}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Data Table */}
      <Card padded={false}>
        {filteredDocs.length === 0 ? (
          <EmptyState
            title="No compliance records match filters"
            description="Adjust your urgency, category, or institution filter selection."
            actionText="Clear Filters"
            onAction={() => {
              setUrgencyFilter('All');
              setTypeFilter('All');
              setInstFilter('All');
            }}
          />
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Document Name / Code</th>
                  <th>Institution</th>
                  <th>Category</th>
                  <th>Expiry Date</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <span className="table-institution" style={{ cursor: 'default' }}>
                        {doc.name}
                      </span>
                      <span className="table-sub">
                        {doc.id} · {doc.filename || 'Evidence_Archive.pdf'}
                      </span>
                    </td>
                    <td>{doc.institution}</td>
                    <td>{doc.type}</td>
                    <td>{formatDate(doc.expiry)}</td>
                    <td>
                      <span
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '11px',
                          background: 'var(--surface)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                        }}
                      >
                        v{doc.version || 1}
                      </span>
                    </td>
                    <td>
                      <Badge statusText={doc.status}>{doc.status}</Badge>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenDocAction(doc)}
                        icon={doc.status === 'Pending verification' ? <FileCheck2 size={14} /> : <RefreshCw size={13} />}
                      >
                        {doc.status === 'Pending verification' ? 'Verify' : 'Renew / Update'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* --- Modals --- */}

      {/* 1. Submit Undertaking Modal */}
      <Modal
        isOpen={isUndertakingModalOpen}
        onClose={handleCloseModal}
        title="Submit Compliance Undertaking"
        subtitle="Record institutional commitment or compliance obligation for verification."
        footer={
          <>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSubmitUndertaking} isLoading={isBusy}>
              Submit for Verification
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmitUndertaking}>
          <div className="form-field" style={{ marginBottom: '14px' }}>
            <label htmlFor="modal-inst">Institution</label>
            <select
              id="modal-inst"
              value={inputInstitution}
              onChange={(e) => setInputInstitution(e.target.value)}
              required
            >
              {applications.map((a) => (
                <option key={a.id} value={a.name}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field" style={{ marginBottom: '14px' }}>
            <label htmlFor="modal-title">Undertaking Title</label>
            <input
              id="modal-title"
              type="text"
              placeholder="e.g. Undertaking for Cadre Ratio Compliance"
              value={inputTitle}
              onChange={(e) => setInputTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-field" style={{ marginBottom: '14px' }}>
            <label htmlFor="modal-expiry">Obligation Fulfillment Target Date</label>
            <input
              id="modal-expiry"
              type="date"
              value={inputDate}
              min="2026-10-25"
              onChange={(e) => setInputDate(e.target.value)}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="modal-upload">Signed Affidavit / Letter (PDF)</label>
            <input
              id="modal-upload"
              type="file"
              accept=".pdf,.png,.jpg"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) setInputFile(f.name);
              }}
            />
            <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
              The prototype retains filename and revision audit metadata.
            </p>
          </div>

          {formError && <p className="field-error">{formError}</p>}
        </form>
      </Modal>

      {/* 2. Renew or Verify Document Modal */}
      {selectedDoc && (
        <Modal
          isOpen={modalMode !== null}
          onClose={handleCloseModal}
          title={modalMode === 'verify' ? 'Verify Institutional Undertaking' : 'Renew or Replace Document'}
          subtitle={`${selectedDoc.name} · ${selectedDoc.institution}`}
          footer={
            <>
              <Button variant="secondary" onClick={handleCloseModal}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSubmitDocAction} isLoading={isBusy}>
                {modalMode === 'verify' ? 'Confirm Verification' : 'Save Renewal & Increment Version'}
              </Button>
            </>
          }
        >
          <form onSubmit={handleSubmitDocAction}>
            {modalMode === 'verify' ? (
              <div className="form-field">
                <label htmlFor="verify-note">Verification Findings Note</label>
                <textarea
                  id="verify-note"
                  rows={3}
                  value={inputNote}
                  onChange={(e) => setInputNote(e.target.value)}
                  placeholder="Record basis of verification according to AICTE Approval Process Handbook guidelines."
                  required
                />
              </div>
            ) : (
              <>
                <div className="form-field" style={{ marginBottom: '14px' }}>
                  <label htmlFor="renew-date">New Validity Expiration Date</label>
                  <input
                    id="renew-date"
                    type="date"
                    value={inputDate}
                    min="2026-10-25"
                    onChange={(e) => setInputDate(e.target.value)}
                    required
                  />
                </div>

                <div className="form-field">
                  <label htmlFor="renew-file">Replacement Evidence Document</label>
                  <input
                    id="renew-file"
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) setInputFile(f.name);
                    }}
                  />
                  <p style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '4px' }}>
                    Note: Replacing this file will archive version v{selectedDoc.version || 1} and record
                    the transition in the append-only audit trail.
                  </p>
                </div>
              </>
            )}

            {formError && <p className="field-error">{formError}</p>}
          </form>
        </Modal>
      )}
    </div>
  );
};
