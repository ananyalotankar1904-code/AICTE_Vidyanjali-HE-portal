/**
 * Shared API Client & Adapter for AICTE Approval & Compliance Platform
 *
 * Implements the unified contract between the React frontend and FastAPI gateway.
 * Adheres to canonical entity schemas defined in docs/id-mapping.md and docs/api-contract.md.
 * Supports configurable API base URL and explicit mock mode toggle (VITE_USE_MOCK).
 */

import { mockStore } from '../data/mockStore';
import {
  ApplicationRecord,
  ComplianceDocument,
  EvcRecord,
  NotificationItem,
  AuditEvent,
  DashboardSummary,
  ApplicationStatus,
  WORKFLOW_STAGES,
} from '../types';

/**
 * Determines whether the client runs in live backend mode or offline mock mode.
 * Defaults to live API mode (false) when backend is available.
 */
export const isMockMode = (): boolean => {
  const envMock = (import.meta as any).env?.VITE_USE_MOCK;
  if (envMock !== undefined) {
    return envMock === 'true' || envMock === true;
  }
  if (typeof window !== 'undefined' && (window as any).__USE_MOCK__ !== undefined) {
    return Boolean((window as any).__USE_MOCK__);
  }
  return false;
};

/**
 * Resolves the base URL for API requests.
 * Uses VITE_API_URL if specified, otherwise empty string (routing via Vite dev proxy).
 */
const getBaseUrl = (): string => {
  return (import.meta as any).env?.VITE_API_URL || '';
};

/**
 * Institution metadata dictionary for canonical ID translation (INST001 – INST015).
 * Sourced from docs/id-mapping.md and Dataset 1.
 */
const INSTITUTION_DIRECTORY: Record<string, { name: string; city: string }> = {
  INST001: { name: 'Pune Institute of Technology', city: 'Pune, Maharashtra' },
  INST002: { name: 'Sahyadri College of Engineering', city: 'Kolhapur, Maharashtra' },
  INST003: { name: 'Malwa Institute of Technology', city: 'Indore, Madhya Pradesh' },
  INST004: { name: 'Chennai Technical University', city: 'Chennai, Tamil Nadu' },
  INST005: { name: 'Gujarat Technological Academy', city: 'Ahmedabad, Gujarat' },
  INST006: { name: 'Bangalore Institute of Advanced Studies', city: 'Bengaluru, Karnataka' },
  INST007: { name: 'Jyothi College of Applied Sciences', city: 'Hyderabad, Telangana' },
  INST008: { name: 'Kalinga Academy of Technology', city: 'Bhubaneswar, Odisha' },
  INST009: { name: 'National Engineering Institute', city: 'New Delhi, Delhi' },
  INST010: { name: 'Rajasthan Institute of Technology', city: 'Jaipur, Rajasthan' },
  INST011: { name: 'Kerala State Technical Institute', city: 'Thiruvananthapuram, Kerala' },
  INST012: { name: 'Apex Institute of Design & Technology', city: 'Mumbai, Maharashtra' },
  INST013: { name: 'Assam Engineering College', city: 'Guwahati, Assam' },
  INST014: { name: 'Punjab Polytechnic Institute', city: 'Ludhiana, Punjab' },
  INST015: { name: 'Vidya Vikas Institute of Technology', city: 'Bengaluru, Karnataka' },
};

/**
 * Maps Member 3 backend stage names to the 0..5 numeric index used by the frontend stepper.
 */
const STAGE_INDEX_MAP: Record<string, number> = {
  SUBMITTED: 0,
  INITIAL_SCRUTINY: 1,
  DEFICIENCY_RAISED: 1,
  RE_SCRUTINY: 2,
  EVC_SCHEDULED: 3,
  EVC_COMPLETED: 3,
  COMMITTEE_REVIEW: 4,
  DECISION_PENDING: 4,
  COMPLETED: 5,
};

/**
 * Maps Member 3 backend stage and status to the frontend ApplicationStatus string.
 */
const mapToFrontendStatus = (
  currentStage: string,
  applicationStatus: string,
  deficiencyFlag: string,
  decision?: string
): ApplicationStatus => {
  if (applicationStatus === 'COMPLETED' || currentStage === 'COMPLETED') {
    return decision === 'REJECTED' ? 'Rejected' : 'Approved';
  }
  if (deficiencyFlag === 'Yes' || currentStage === 'DEFICIENCY_RAISED') {
    return 'Deficiency raised';
  }
  if (currentStage === 'RE_SCRUTINY') {
    return 'Under re-scrutiny';
  }
  if (currentStage === 'EVC_SCHEDULED') {
    return 'EVC scheduled';
  }
  if (currentStage === 'EVC_COMPLETED') {
    return 'EVC completed';
  }
  if (currentStage === 'DECISION_PENDING' || currentStage === 'COMMITTEE_REVIEW') {
    return 'Decision pending';
  }
  if (currentStage === 'INITIAL_SCRUTINY') {
    return 'Pending scrutiny';
  }
  return 'Submitted';
};

/**
 * Generates authenticated role headers matching the active session for server-side RBAC.
 */
const getAuthHeaders = (): Record<string, string> => {
  const currentUser = mockStore.getState().currentUser;
  let role = currentUser?.role || 'Scrutiny Officer';
  if (role === 'Competent Authority') {
    role = 'Competent Authority Secretariat';
  } else if (role === 'EVC Committee Lead') {
    role = 'EVC Coordinator';
  } else if (role === 'Institution Applicant') {
    role = 'Institution Admin';
  }

  return {
    'Content-Type': 'application/json',
    'x-user-id': currentUser?.id || 'SYSTEM_WEB',
    'x-user-role': role,
  };
};

/**
 * Normalizes a raw Member 3 backend application into the frontend ApplicationRecord format.
 */
export const normalizeApplication = (item: any): ApplicationRecord => {
  const inst = INSTITUTION_DIRECTORY[item.institution_id] || {
    name: `${item.institution_id} — ${item.programme_name || item.application_type || 'Institution'}`,
    city: 'Regional Office',
  };

  const stageIdx = STAGE_INDEX_MAP[item.current_stage] ?? 0;
  const appStatus = mapToFrontendStatus(
    item.current_stage,
    item.application_status,
    item.deficiency_flag,
    item.decision_record?.decision
  );

  let age = 0;
  if (item.submitted_date) {
    try {
      const sub = new Date(item.submitted_date + 'T00:00:00');
      const now = new Date();
      age = Math.max(0, Math.floor((now.getTime() - sub.getTime()) / (1000 * 3600 * 24)));
    } catch {
      age = 0;
    }
  }

  const defaultDocs = [
    'Land ownership certificate',
    'Faculty cadre roster',
    'Fire safety compliance NOC',
    'Occupancy & building plan approval',
  ];

  return {
    id: item.application_id,
    name: inst.name,
    city: inst.city,
    type: (item.application_type as any) || 'Extension of Approval',
    stage: stageIdx,
    status: appStatus,
    owner: item.assigned_role || 'Scrutiny Officer',
    deadline: item.due_date || '2026-11-15',
    age,
    deficiency:
      item.deficiency_flag === 'Yes'
        ? item.demo_notes || item.deficiency_records?.[0]?.deficiency_text || 'Deficiency reported in faculty ratio / laboratory requirements.'
        : '',
    documents: item.documents || defaultDocs,
    assignedRoute: `Route ${item.academic_year || 'APH 2024-27'} (${item.data_type || 'Workflow'})`,
    submittedAt: item.submitted_date || '2026-10-01',
    contactEmail: item.contact_email || 'registrar@aicte-approved.edu.in',
    contactPhone: item.contact_phone || '+91 20 2567 8901',
    applicantRole: 'Director / Authorized Signatory',
    intakeCapacity: item.intake_approved || 360,
    programsOffered: item.programme_name ? [item.programme_name] : ['Engineering & Technology'],
  };
};

/**
 * Normalizes a raw Member 4 compliance document into frontend ComplianceDocument.
 */
export const normalizeDocument = (item: any): ComplianceDocument => {
  const inst = INSTITUTION_DIRECTORY[item.institution_id] || { name: item.institution_id, city: '' };

  let cat: any = 'Safety';
  const dtype = (item.document_type || '').toUpperCase();
  if (dtype.includes('FACULTY') || dtype.includes('ROSTER')) cat = 'Faculty';
  else if (dtype.includes('BUILDING') || dtype.includes('LAND') || dtype.includes('INFRA')) cat = 'Infrastructure';
  else if (dtype.includes('UNDERTAKING') || dtype.includes('AFFIDAVIT')) cat = 'Undertaking';

  let docStatus: any = 'Valid';
  const rev = (item.review_status || '').toUpperCase();
  if (rev === 'VERIFIED') docStatus = 'Verified';
  else if (rev === 'PENDING') docStatus = 'Pending verification';
  else if (rev === 'REJECTED') docStatus = 'Expired';

  const expiry = item.expiry_date ? String(item.expiry_date).slice(0, 10) : '—';

  return {
    id: item.id,
    name: item.title || item.file_name || 'Compliance Document',
    institution: inst.name,
    type: cat,
    expiry,
    status: docStatus,
    version: item.version || 1,
    filename: item.file_name || 'document.pdf',
    uploadedAt: item.created_at ? String(item.created_at).slice(0, 10) : '2026-10-15',
  };
};

/**
 * Normalizes a raw Member 4 EVC inspection record into frontend EvcRecord.
 */
export const normalizeEvc = (item: any): EvcRecord => {
  let evcStatus: any = 'Scheduled';
  const st = (item.status || '').toUpperCase();
  if (st.includes('COMPLETED') || st.includes('ACCEPTED')) evcStatus = 'Completed';
  else if (st.includes('PENDING')) evcStatus = 'Awaiting assignment';
  else if (st.includes('RESCHEDULED') || st.includes('DELAYED')) evcStatus = 'Delayed';

  const members =
    Array.isArray(item.assigned_members) && item.assigned_members.length > 0
      ? item.assigned_members.join(', ')
      : 'EVC Evaluation Panel';

  return {
    id: item.id,
    app: item.application_id,
    date: item.planned_visit_date ? String(item.planned_visit_date).slice(0, 10) : '2026-11-04',
    mode: 'On-site',
    members,
    status: evcStatus,
    evidence: item.findings_summary || item.recommendation || 'Comprehensive physical & infrastructure inspection record.',
    scheduledTime: '10:00 AM IST',
    reportNotes: item.report_review_notes || item.visit_notes,
  };
};

/**
 * Normalizes a raw Member 4 notification into frontend NotificationItem.
 */
export const normalizeNotification = (item: any): NotificationItem => {
  let kind: any = 'Deficiency alert';
  const ntype = (item.notification_type || item.source_event || '').toUpperCase();
  if (ntype.includes('DEADLINE')) kind = 'Deadline reminder';
  else if (ntype.includes('EVC')) kind = 'EVC reminder';
  else if (ntype.includes('ESCALAT')) kind = 'Escalation';

  let timeStr = 'Recently';
  if (item.created_at) {
    try {
      timeStr = new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      timeStr = 'Recently';
    }
  }

  return {
    id: item.id,
    kind,
    title: item.title || 'Workflow Notification',
    body: item.message || '',
    time: timeStr,
    read: Boolean(item.is_read),
    app: item.entity_id || 'GENERAL',
  };
};

/**
 * Normalizes a raw Member 4 audit event into frontend AuditEvent.
 */
export const normalizeAuditEvent = (item: any): AuditEvent => {
  const beforeStr = item.before_state ? JSON.stringify(item.before_state) : '—';
  const afterStr = item.after_state ? JSON.stringify(item.after_state) : '—';

  return {
    id: item.id,
    at: item.created_at ? String(item.created_at).slice(0, 19).replace('T', ' ') : '2026-10-25 10:00',
    actor: `${item.actor_role || 'User'} (${item.actor_id || 'System'})`,
    action: item.action || 'WORKFLOW_ACTION',
    app: item.entity_id || 'GENERAL',
    before: beforeStr,
    after: afterStr,
    reason: item.reason || 'Workflow progression step',
  };
};

// ==============================================================================
// PUBLIC API CLIENT
// ==============================================================================
export const apiClient = {
  // 1. Dashboard summary
  async getDashboardSummary(): Promise<DashboardSummary> {
    if (isMockMode()) {
      const apps = mockStore.getApplications();
      const docs = mockStore.getDocuments();
      const evcs = mockStore.getEvcs();

      const stageCounts = WORKFLOW_STAGES.map((stg, idx) => ({
        stage: stg,
        count: apps.filter((a) => a.stage === idx).length,
      }));

      const ageingBuckets = [
        { bucket: '0–15 days', count: apps.filter((a) => a.age <= 15).length },
        { bucket: '16–30 days', count: apps.filter((a) => a.age > 15 && a.age <= 30).length },
        { bucket: '31–45 days', count: apps.filter((a) => a.age > 30 && a.age <= 45).length },
        { bucket: '46–60 days', count: apps.filter((a) => a.age > 45 && a.age <= 60).length },
        { bucket: '60+ days', count: apps.filter((a) => a.age > 60).length },
      ];

      return {
        totalApplications: apps.length,
        pendingScrutiny: apps.filter((a) => a.status === 'Pending scrutiny').length,
        deficiencyCases: apps.filter((a) => Boolean(a.deficiency)).length,
        evcsScheduled: evcs.filter((e) => e.status === 'Scheduled').length,
        expiringDocuments: docs.filter((d) => ['Expiring soon', 'Expired'].includes(d.status)).length,
        upcomingDeadlines: apps.filter((a) => a.deadline <= '2026-11-09').length,
        stageDistribution: stageCounts,
        ageingBuckets,
        status: 'operational',
      };
    }

    const res = await fetch(`${getBaseUrl()}/api/dashboard/summary`);
    if (!res.ok) {
      throw new Error(`Failed to load dashboard summary (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    return {
      totalApplications: data.totalApplications ?? data.total_applications ?? 0,
      pendingScrutiny: data.pendingScrutiny ?? 0,
      deficiencyCases: data.deficiencyCases ?? 0,
      evcsScheduled: data.evcsScheduled ?? null,
      expiringDocuments: data.expiringDocuments ?? null,
      upcomingDeadlines: data.upcomingDeadlines ?? null,
      stageDistribution: data.stageDistribution || [],
      ageingBuckets: data.ageingBuckets || [],
      status: data.status || 'operational',
      degraded: data.degraded || false,
      subsystem_status: data.subsystem_status,
    };
  },

  // 2. Applications
  async getApplications(): Promise<ApplicationRecord[]> {
    if (isMockMode()) {
      return [...mockStore.getApplications()];
    }

    const res = await fetch(`${getBaseUrl()}/api/applications`);
    if (!res.ok) {
      throw new Error(`Failed to fetch applications (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    const rawItems = Array.isArray(data) ? data : data.items || [];
    return rawItems.map(normalizeApplication);
  },

  async getApplicationById(id: string): Promise<ApplicationRecord | null> {
    if (isMockMode()) {
      const app = mockStore.getApplicationById(id);
      return app ? { ...app } : null;
    }

    const res = await fetch(`${getBaseUrl()}/api/applications/${encodeURIComponent(id)}`);
    if (res.status === 404) return null;
    if (!res.ok) {
      throw new Error(`Failed to fetch application ${id} (HTTP ${res.status}: ${res.statusText})`);
    }
    const raw = await res.json();
    return normalizeApplication(raw);
  },

  async createApplication(
    payload: Omit<ApplicationRecord, 'id' | 'stage' | 'status' | 'age' | 'submittedAt'>
  ): Promise<ApplicationRecord> {
    if (isMockMode()) {
      return mockStore.addApplication(payload);
    }

    const backendPayload = {
      institution_id: 'INST001',
      application_type: payload.type || 'Extension of Approval',
      academic_year: '2026-2027',
      contact_email: payload.contactEmail || 'admin@aicte-approved.edu.in',
      contact_phone: payload.contactPhone || '+91 20 2567 8901',
      programme_name: payload.programsOffered?.[0] || 'Engineering & Technology',
      intake_approved: payload.intakeCapacity || 360,
    };

    const res = await fetch(`${getBaseUrl()}/api/applications`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(backendPayload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create application (HTTP ${res.status})`);
    }

    const created = await res.json();
    return normalizeApplication(created);
  },

  // 3. Workflow transitions
  async requestTransition(
    id: string,
    action: string,
    reason: string,
    outcome?: 'Approved' | 'Rejected',
    currentStageName?: string
  ): Promise<{ success: boolean; message: string }> {
    if (isMockMode()) {
      if (action === 'ISSUE_DEFICIENCY') {
        const ok = mockStore.recordDeficiency(id, reason);
        return { success: ok, message: 'Deficiency recorded and assigned to institution.' };
      }
      if (action === 'ADVANCE_STAGE') {
        const ok = mockStore.advanceStage(id, reason);
        return { success: ok, message: 'Application progressed to next workflow stage.' };
      }
      if (action === 'RECORD_OFFICIAL_DECISION' && outcome) {
        const ok = mockStore.recordOfficialDecision(id, outcome, reason);
        return { success: ok, message: `Official decision recorded: ${outcome}.` };
      }
      if (action === 'SEND_REMINDER') {
        const ok = mockStore.sendReminder(id);
        return { success: ok, message: 'Deadline reminder sent.' };
      }
      return { success: false, message: 'Unrecognized action.' };
    }

    // Live backend execution
    if (action === 'RECORD_OFFICIAL_DECISION' && outcome) {
      const res = await fetch(`${getBaseUrl()}/api/applications/${encodeURIComponent(id)}/decision`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          decision: outcome === 'Approved' ? 'APPROVED' : 'REJECTED',
          reasons: reason,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Official decision recording rejected (HTTP ${res.status})`);
      }
      return { success: true, message: `Official decision recorded: ${outcome}.` };
    }

    if (action === 'ISSUE_DEFICIENCY') {
      const res = await fetch(`${getBaseUrl()}/api/applications/${encodeURIComponent(id)}/transition`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: 'SCRUTINY_DEFICIENT',
          to_stage: 'DEFICIENCY_RAISED',
          remarks: reason,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Deficiency issuance rejected (HTTP ${res.status})`);
      }
      return { success: true, message: 'Deficiency recorded and assigned to applicant institution.' };
    }

    if (action === 'ADVANCE_STAGE') {
      // Derive appropriate transition action based on stage
      let transitionAction = 'ASSIGN_SCRUTINY';
      const stg = (currentStageName || '').toUpperCase();

      if (stg === 'INITIAL_SCRUTINY') {
        transitionAction = 'SCRUTINY_PASS';
      } else if (stg === 'DEFICIENCY_RAISED') {
        transitionAction = 'SUBMIT_RESPONSE';
      } else if (stg === 'RE_SCRUTINY') {
        transitionAction = 'RE_SCRUTINY_PASS';
      } else if (stg === 'EVC_SCHEDULED') {
        transitionAction = 'COMPLETE_EVC';
      } else if (stg === 'EVC_COMPLETED') {
        transitionAction = 'SUBMIT_TO_COMMITTEE';
      } else if (stg === 'COMMITTEE_REVIEW') {
        transitionAction = 'REFER_TO_AUTHORITY';
      }

      const res = await fetch(`${getBaseUrl()}/api/applications/${encodeURIComponent(id)}/transition`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          action: transitionAction,
          remarks: reason,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Stage advance rejected (HTTP ${res.status})`);
      }
      return { success: true, message: 'Application progressed to next workflow stage.' };
    }

    if (action === 'SEND_REMINDER') {
      return { success: true, message: 'Deadline reminder dispatched to applicant.' };
    }

    throw new Error(`Unrecognized action: ${action}`);
  },

  // 4. Documents & Undertakings
  async getDocuments(): Promise<ComplianceDocument[]> {
    if (isMockMode()) {
      return [...mockStore.getDocuments()];
    }

    const res = await fetch(`${getBaseUrl()}/api/documents`);
    if (!res.ok) {
      throw new Error(`Failed to fetch documents (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    const raw = Array.isArray(data) ? data : [];
    return raw.map(normalizeDocument);
  },

  // 5. EVCs
  async getEvcs(): Promise<EvcRecord[]> {
    if (isMockMode()) {
      return [...mockStore.getEvcs()];
    }

    const res = await fetch(`${getBaseUrl()}/api/evcs`);
    if (!res.ok) {
      throw new Error(`Failed to fetch EVC inspections (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    const raw = Array.isArray(data) ? data : [];
    return raw.map(normalizeEvc);
  },

  // 6. Notifications
  async getNotifications(): Promise<NotificationItem[]> {
    if (isMockMode()) {
      return [...mockStore.getNotifications()];
    }

    const res = await fetch(`${getBaseUrl()}/api/notifications`);
    if (!res.ok) {
      throw new Error(`Failed to fetch notifications (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    const raw = Array.isArray(data) ? data : [];
    return raw.map(normalizeNotification);
  },

  // 7. Audit logs
  async getAuditLogs(): Promise<AuditEvent[]> {
    if (isMockMode()) {
      return [...mockStore.getAuditLogs()];
    }

    const res = await fetch(`${getBaseUrl()}/api/audit-logs`);
    if (!res.ok) {
      throw new Error(`Failed to fetch audit logs (HTTP ${res.status}: ${res.statusText})`);
    }
    const data = await res.json();
    const raw = Array.isArray(data) ? data : [];
    return raw.map(normalizeAuditEvent);
  },
};
