/**
 * Shared Type Definitions for AICTE_Vidyanjali-HE-portal Approval Platform
 * Aligned with SIH26262 README specification and Member 1 responsibilities.
 */

export type WorkflowStage =
  | 'Submitted'
  | 'Scrutiny'
  | 'Re-scrutiny'
  | 'EVC'
  | 'Executive Decision'
  | 'Appeal/Post-approval';

export const WORKFLOW_STAGES: readonly WorkflowStage[] = [
  'Submitted',
  'Scrutiny',
  'Re-scrutiny',
  'EVC',
  'Executive Decision',
  'Appeal/Post-approval',
] as const;

export type ApplicationStatus =
  | 'Submitted'
  | 'Pending scrutiny'
  | 'Deficiency raised'
  | 'EVC scheduled'
  | 'EVC completed'
  | 'Decision pending'
  | 'Approved'
  | 'Rejected'
  | 'Under re-scrutiny';

export type ApplicationCategory =
  | 'Extension of Approval'
  | 'Increase in Intake'
  | 'New Course'
  | 'New Institution';

export interface ApplicationRecord {
  id: string;
  name: string;
  city: string;
  type: ApplicationCategory;
  stage: number; // 0 to 5 index in WORKFLOW_STAGES
  status: ApplicationStatus;
  owner: string;
  deadline: string; // YYYY-MM-DD
  age: number; // Days since submission
  deficiency: string;
  documents: string[];
  assignedRoute: string;
  submittedAt: string;
  contactEmail?: string;
  contactPhone?: string;
  applicantRole?: string;
  intakeCapacity?: number;
  programsOffered?: string[];
}

export type DocumentCategory = 'Safety' | 'Infrastructure' | 'Faculty' | 'Undertaking';

export type DocumentStatus =
  | 'Valid'
  | 'Expiring soon'
  | 'Expired'
  | 'Missing'
  | 'Pending verification'
  | 'Verified';

export interface ComplianceDocument {
  id: string;
  name: string;
  institution: string;
  type: DocumentCategory;
  expiry: string; // YYYY-MM-DD or '—'
  status: DocumentStatus;
  version?: number;
  filename?: string;
  uploadedAt?: string;
}

export type EvcStatus = 'Scheduled' | 'Completed' | 'Awaiting assignment' | 'Delayed';
export type EvcMode = 'On-site' | 'Virtual';

export interface EvcRecord {
  id: string;
  app: string;
  date: string; // YYYY-MM-DD
  mode: EvcMode;
  members: string;
  status: EvcStatus;
  evidence: string;
  scheduledTime?: string;
  reportNotes?: string;
}

export type NotificationKind =
  | 'Deficiency alert'
  | 'Deadline reminder'
  | 'EVC reminder'
  | 'Escalation';

export interface NotificationItem {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  time: string;
  read: boolean;
  app: string;
}

export interface AuditEvent {
  id: number | string;
  at: string;
  actor: string;
  action: string;
  app: string;
  before: string;
  after: string;
  reason: string;
}

export interface UserProfile {
  id: string;
  name: string;
  role: string;
  designation: string;
  avatar: string;
}

export interface DashboardSummary {
  totalApplications: number;
  pendingScrutiny: number;
  deficiencyCases: number;
  evcsScheduled: number;
  expiringDocuments: number;
  upcomingDeadlines: number;
  stageDistribution: { stage: WorkflowStage; count: number }[];
  ageingBuckets: { bucket: string; count: number }[];
  status?: string;
  degraded?: boolean;
  subsystem_status?: {
    workflow_engine: string;
    compliance_engine: string;
  };
}

export type FilterView = 'All applications' | 'My queue' | 'At risk' | 'EVC pipeline';
