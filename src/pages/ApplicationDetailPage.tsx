import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  AlertTriangle,
  ChevronRight,
  Send,
  FileCheck2,
  Calendar,
  Gavel,
  History,
  Building,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Stepper } from '../components/common/Stepper';
import { Modal } from '../components/common/Modal';
import { Skeleton } from '../components/common/Skeleton';
import { toast } from '../components/common/Toast';
import { apiClient } from '../api/client';
import { WORKFLOW_STAGES, ApplicationRecord, ComplianceDocument, AuditEvent } from '../types';

export const ApplicationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [app, setApp] = useState<ApplicationRecord | null>(null);
  const [documents, setDocuments] = useState<ComplianceDocument[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Modal dialog states
  const [modalType, setModalType] = useState<
    'deficiency' | 'advance' | 'decision' | 'reminder' | null
  >(null);
  const [modalReason, setModalReason] = useState('');
  const [decisionOutcome, setDecisionOutcome] = useState<'Approved' | 'Rejected'>('Approved');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const loadApplication = async () => {
    if (!id) return;
    setIsLoading(true);
    setFetchError(null);
    try {
      const [appData, docsData, auditData] = await Promise.all([
        apiClient.getApplicationById(id),
        apiClient.getDocuments().catch(() => []),
        apiClient.getAuditLogs().catch(() => []),
      ]);

      if (!appData) {
        setFetchError(`Application ${id} does not exist in the approval registry.`);
        setApp(null);
      } else {
        setApp(appData);
        setDocuments(docsData);
        setAuditLogs(auditData);
      }
    } catch (err: any) {
      setFetchError(err?.message || `Failed to fetch application ${id} from server.`);
      setApp(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadApplication();
  }, [id]);

  const handleOpenModal = (type: 'deficiency' | 'advance' | 'decision' | 'reminder') => {
    setModalType(type);
    setModalReason('');
    setFormError('');
  };

  const handleCloseModal = () => {
    setModalType(null);
    setModalReason('');
    setFormError('');
    setIsSubmitting(false);
  };

  const handleSubmitModal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (modalType !== 'reminder' && !modalReason.trim()) {
      setFormError('Please enter a clear justification or reason before confirming.');
      return;
    }

    if (!app) return;

    setIsSubmitting(true);
    setFormError('');

    try {
      let actionKey = 'ADVANCE_STAGE';
      if (modalType === 'deficiency') actionKey = 'ISSUE_DEFICIENCY';
      else if (modalType === 'decision') actionKey = 'RECORD_OFFICIAL_DECISION';
      else if (modalType === 'reminder') actionKey = 'SEND_REMINDER';

      const result = await apiClient.requestTransition(
        app.id,
        actionKey,
        modalReason.trim(),
        decisionOutcome,
        app.status
      );

      toast.show(result.message, decisionOutcome === 'Approved' || modalType !== 'decision' ? 'success' : 'error');
      handleCloseModal();
      await loadApplication();
    } catch (err: any) {
      setFormError(err?.message || 'Server rejected transition request.');
      toast.show(err?.message || 'Action rejected by server', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/applications')}
          icon={<ArrowLeft size={15} />}
          style={{ marginBottom: '16px' }}
        >
          Back to Applications
        </Button>
        <Card style={{ padding: '24px' }}>
          <Skeleton lines={6} />
        </Card>
      </div>
    );
  }

  if (fetchError || !app) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center' }}>
        <AlertCircle size={44} color="#dc2626" style={{ margin: '0 auto 12px' }} />
        <h2 style={{ color: '#C53030' }}>Application Not Found</h2>
        <p style={{ color: 'var(--muted)', marginTop: '8px', maxWidth: '500px', margin: '8px auto 20px' }}>
          {fetchError || `Application ${id} could not be found in the registry.`}
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <Button variant="secondary" onClick={loadApplication} icon={<RefreshCw size={14} />}>
            Retry Request
          </Button>
          <Button onClick={() => navigate('/applications')}>
            Return to Applications List
          </Button>
        </div>
      </div>
    );
  }

  const linkedDocs = app.documents.map((docName) => {
    const item = documents.find(
      (d) => d.institution === app.name && d.name === docName
    );
    return {
      name: docName,
      status: item ? item.status : 'Valid',
      expiry: item ? item.expiry : '—',
      filename: item?.filename || 'Document_Uploaded.pdf',
    };
  });

  const appAudit = auditLogs.filter((log) => log.app === app.id);

  const getNextActionDescription = () => {
    if (app.deficiency) return 'Institution to submit corrected evidence & documentation';
    if (app.stage === 5) return 'Process concluded · Institutional compliance record active';
    if (app.stage === 4) return 'Competent Authority human decision required to conclude outcome';
    if (app.stage === 3) return 'Visiting EVC committee to conduct inspection and file report';
    if (app.stage === 2) return 'Scrutiny officer to verify resubmitted deficiency corrections';
    if (app.stage === 1) return 'Assigned scrutiny desk officer to verify statutory documentation';
    return 'Application awaiting initial desk assignment';
  };

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

  return (
    <div>
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate('/applications')}
        icon={<ArrowLeft size={15} />}
        style={{ marginBottom: '16px' }}
      >
        Back to Applications
      </Button>

      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">{app.id} · Case File</div>
          <h1 className="page-title">{app.name}</h1>
          <p className="page-subtitle">
            <MapPin size={13} style={{ display: 'inline', marginRight: 4 }} />
            {app.city} · <Building size={13} style={{ display: 'inline', margin: '0 4px 0 8px' }} />
            {app.type}
          </p>
        </div>

        <div className="head-actions">
          {/* Deficiency Button */}
          <Button
            variant="outline-danger"
            onClick={() => handleOpenModal('deficiency')}
            disabled={app.stage === 5}
            icon={<AlertTriangle size={15} />}
          >
            Issue Deficiency
          </Button>

          {/* Move Stage / Official Decision Button */}
          {app.stage === 4 ? (
            <Button
              variant="primary"
              onClick={() => handleOpenModal('decision')}
              icon={<Gavel size={15} />}
            >
              Record Official Decision
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={() => handleOpenModal('advance')}
              disabled={Boolean(app.deficiency) || app.stage === 5}
              icon={<ChevronRight size={15} />}
              iconPosition="right"
            >
              Move to Next Stage
            </Button>
          )}
        </div>
      </div>

      {/* Main Detail Grid Layout */}
      <div className="dashboard-grid">
        {/* Left Column: Progress, Next Action, Deficiency, Documents */}
        <div style={{ display: 'grid', gap: '18px' }}>
          {/* Approval Progress Stepper Card */}
          <Card>
            <CardHeader
              title="Approval Progress"
              subtitle={`Current stage: ${WORKFLOW_STAGES[app.stage]}`}
              action={<Badge statusText={app.status}>{app.status}</Badge>}
            />
            <Stepper currentStageIndex={app.stage} />
          </Card>

          {/* What Happens Next Card */}
          <Card>
            <CardHeader
              title="What Happens Next"
              subtitle="Current operational queue responsibility"
            />
            <div className="flow-callout">
              <div>
                <strong>{getNextActionDescription()}</strong>
                <p>
                  Current Assignee: <b>{app.owner}</b> · Target Deadline: <b>{formatDate(app.deadline)}</b>
                </p>
              </div>
              <ChevronRight size={18} color="var(--accent-active)" />
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '16px',
                marginTop: '18px',
                paddingTop: '16px',
                borderTop: '1px solid var(--border-soft)',
              }}
            >
              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Application ID
                </span>
                <b style={{ display: 'block', fontSize: '13px', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                  {app.id}
                </b>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Intake Category
                </span>
                <b style={{ display: 'block', fontSize: '13px', marginTop: 2 }}>{app.type}</b>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Assigned Route
                </span>
                <b style={{ display: 'block', fontSize: '13px', color: 'var(--accent-active)', marginTop: 2 }}>
                  {app.assignedRoute}
                </b>
              </div>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Ageing
                </span>
                <b style={{ display: 'block', fontSize: '13px', marginTop: 2 }}>{app.age} days</b>
              </div>
            </div>
          </Card>

          {/* Deficiency Status Card */}
          <Card>
            <CardHeader
              title="Deficiency Review"
              subtitle="Scrutiny findings that require applicant response"
            />
            {app.deficiency ? (
              <div className="attention-box urgent">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <AlertTriangle size={18} color="#dc2626" />
                  <h3 style={{ color: '#991b1b' }}>Deficiency Notice Issued</h3>
                </div>
                <p>{app.deficiency}</p>
                <div style={{ marginTop: '12px', fontSize: '12px', color: '#7f1d1d' }}>
                  Applicant institution must submit corrected documentation before stage advancement.
                </div>
              </div>
            ) : (
              <div className="attention-box">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <CheckCircle2 size={18} color="#059669" />
                  <h3 style={{ color: '#065f46' }}>No Open Scrutiny Deficiencies</h3>
                </div>
                <p>The current case file has no unresolved deficiency notices on record.</p>
              </div>
            )}
          </Card>

          {/* Document Checklist Card */}
          <Card>
            <CardHeader
              title="Statutory Evidence & Document Checklist"
              subtitle="Uploaded verification files for this institutional category"
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/compliance')}
                  icon={<FileCheck2 size={14} />}
                >
                  Document Inventory
                </Button>
              }
            />

            <div style={{ display: 'grid', gap: '0' }}>
              {linkedDocs.map((doc, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                    padding: '12px 0',
                    borderTop: idx === 0 ? 'none' : '1px solid var(--border-soft)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span
                      style={{
                        width: '22px',
                        height: '22px',
                        borderRadius: '50%',
                        background: doc.status === 'Missing' || doc.status === 'Expired' ? 'var(--red-bg)' : 'var(--green-bg)',
                        color: doc.status === 'Missing' || doc.status === 'Expired' ? 'var(--red-ink)' : 'var(--green-ink)',
                        display: 'grid',
                        placeItems: 'center',
                        fontSize: '12px',
                        fontWeight: 700,
                      }}
                    >
                      {doc.status === 'Missing' || doc.status === 'Expired' ? '!' : '✓'}
                    </span>
                    <div>
                      <span style={{ fontWeight: 650, fontSize: '13px', color: 'var(--ink)' }}>
                        {doc.name}
                      </span>
                      <span
                        style={{
                          display: 'block',
                          fontSize: '11px',
                          color: 'var(--muted)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {doc.filename} · Valid until: {formatDate(doc.expiry)}
                      </span>
                    </div>
                  </div>

                  <Badge statusText={doc.status}>{doc.status}</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Deadlines, Quick Reminders, Audit Timeline */}
        <div style={{ display: 'grid', gap: '18px', alignContent: 'start' }}>
          {/* Deadline Card */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Target Deadline
                </span>
                <div style={{ fontSize: '26px', fontWeight: 800, color: 'var(--ink)', margin: '4px 0' }}>
                  {formatDate(app.deadline)}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                  Assigned owner: <b>{app.owner}</b>
                </div>
              </div>
              <Clock size={22} color="var(--accent)" />
            </div>

            <p style={{ fontSize: '12px', color: 'var(--fg-2)', marginTop: '14px', lineHeight: 1.5 }}>
              Deadlines serve as monitoring alerts. In accordance with SIH26262 guidelines, an overdue
              date triggers escalation notices rather than automated statutory rejection.
            </p>

            <Button
              variant="secondary"
              onClick={() => handleOpenModal('reminder')}
              style={{ width: '100%', marginTop: '16px' }}
              icon={<Send size={14} />}
            >
              Send Deadline Reminder
            </Button>
          </Card>

          {/* Activity & Audit Trail Card */}
          <Card>
            <CardHeader
              title="Case Audit Trail"
              subtitle="Append-only lifecycle events"
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/audit')}
                  icon={<History size={14} />}
                >
                  Full History
                </Button>
              }
            />

            <div className="audit-timeline">
              {appAudit.length === 0 ? (
                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>No audit events logged yet.</p>
              ) : (
                appAudit.map((log) => (
                  <div
                    key={log.id}
                    style={{
                      position: 'relative',
                      padding: '0 0 16px 20px',
                      borderLeft: '1px solid var(--border)',
                      marginLeft: '7px',
                    }}
                  >
                    <div
                      style={{
                        position: 'absolute',
                        left: '-5px',
                        top: '4px',
                        width: '9px',
                        height: '9px',
                        background: 'var(--accent-active)',
                        border: '2px solid white',
                        borderRadius: '50%',
                        boxShadow: '0 0 0 1px var(--border)',
                      }}
                    />
                    <strong style={{ display: 'block', fontSize: '13px', lineHeight: 1.35 }}>
                      {log.action}
                    </strong>
                    <div style={{ fontSize: '12px', color: 'var(--fg-2)', marginTop: '2px' }}>
                      {log.reason}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '3px' }}>
                      {log.actor} · {log.at}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* --- Action Modals --- */}

      {/* 1. Issue Deficiency Modal */}
      <Modal
        isOpen={modalType === 'deficiency'}
        onClose={handleCloseModal}
        title="Return Case for Deficiency Correction"
        subtitle={`Specify the documentation or compliance defect that ${app.name} must resolve.`}
        footer={
          <>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleSubmitModal}
              isLoading={isSubmitting}
            >
              Record Deficiency Notice
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmitModal}>
          <div className="form-field">
            <label htmlFor="deficiency-reason">
              Deficiency Details & Required Corrections <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <textarea
              id="deficiency-reason"
              rows={4}
              value={modalReason}
              onChange={(e) => setModalReason(e.target.value)}
              placeholder="e.g. Valid Fire Safety NOC is expired; updated appointment letters required for 3 faculty members."
              required
            />
          </div>
          {formError && <p className="field-error">{formError}</p>}
        </form>
      </Modal>

      {/* 2. Advance Stage Modal */}
      <Modal
        isOpen={modalType === 'advance'}
        onClose={handleCloseModal}
        title="Move Application to Next Stage"
        subtitle={`Advance ${app.name} from "${WORKFLOW_STAGES[app.stage]}" to "${
          WORKFLOW_STAGES[Math.min(5, app.stage + 1)]
        }".`}
        footer={
          <>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmitModal}
              isLoading={isSubmitting}
            >
              Confirm Stage Progression
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmitModal}>
          <div className="form-field">
            <label htmlFor="advance-rationale">
              Review Summary & Transition Justification <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <textarea
              id="advance-rationale"
              rows={3}
              value={modalReason}
              onChange={(e) => setModalReason(e.target.value)}
              placeholder="e.g. Scrutiny requirements met. Recommending on-site EVC inspection for lab and infrastructure verification."
              required
            />
          </div>
          {formError && <p className="field-error">{formError}</p>}
        </form>
      </Modal>

      {/* 3. Official Human Decision Modal (Competent Authority) */}
      <Modal
        isOpen={modalType === 'decision'}
        onClose={handleCloseModal}
        title="Record Official Statutory Decision"
        subtitle="In accordance with regulatory rules, official decisions require explicit authorized human action."
        footer={
          <>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant={decisionOutcome === 'Approved' ? 'primary' : 'danger'}
              onClick={handleSubmitModal}
              isLoading={isSubmitting}
            >
              Record {decisionOutcome}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmitModal}>
          <div style={{ marginBottom: '14px' }}>
            <label style={{ fontSize: '12px', fontWeight: 700, display: 'block', marginBottom: '6px' }}>
              Statutory Outcome
            </label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className={`button ${decisionOutcome === 'Approved' ? 'primary' : 'secondary'}`}
                style={{ flex: 1 }}
                onClick={() => setDecisionOutcome('Approved')}
              >
                <CheckCircle2 size={16} /> Grant Approval
              </button>
              <button
                type="button"
                className={`button ${decisionOutcome === 'Rejected' ? 'danger' : 'secondary'}`}
                style={{ flex: 1 }}
                onClick={() => setDecisionOutcome('Rejected')}
              >
                <XCircle size={16} /> Formal Rejection
              </button>
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="decision-rationale">
              Decision Rationale & Recorded Conditions <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <textarea
              id="decision-rationale"
              rows={4}
              value={modalReason}
              onChange={(e) => setModalReason(e.target.value)}
              placeholder="Record the official rationale, executive committee meeting minute reference, and any conditional undertakings."
              required
            />
          </div>
          {formError && <p className="field-error">{formError}</p>}
        </form>
      </Modal>

      {/* 4. Send Reminder Modal */}
      <Modal
        isOpen={modalType === 'reminder'}
        onClose={handleCloseModal}
        title="Send Deadline Reminder"
        subtitle={`Notify ${app.owner} regarding target deadline of ${formatDate(app.deadline)} for ${app.name}.`}
        footer={
          <>
            <Button variant="secondary" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSubmitModal}
              isLoading={isSubmitting}
              icon={<Send size={14} />}
            >
              Dispatch Reminder
            </Button>
          </>
        }
      >
        <div className="flow-callout">
          <Calendar size={18} color="var(--accent-active)" />
          <div>
            <strong>Automated Notification Dispatch</strong>
            <p>
              An in-app deadline alert will be created in the Notifications inbox and logged in the
              permanent audit history.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
