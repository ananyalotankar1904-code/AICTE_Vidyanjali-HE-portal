import {
  ApplicationRecord,
  ComplianceDocument,
  EvcRecord,
  NotificationItem,
  AuditEvent,
  UserProfile,
  WORKFLOW_STAGES,
} from '../types';
import { seedApplications } from './mockApplications';
import { seedDocs } from './mockDocuments';
import { seedEvcs } from './mockEvcs';
import { seedNotes } from './mockNotifications';
import { seedAudit } from './mockAudit';

export const DEMO_USERS: UserProfile[] = [
  {
    id: 'user-1',
    name: 'Ananya Rao',
    role: 'Scrutiny Officer',
    designation: 'Approval Bureau, AICTE HQ',
    avatar: 'AR',
  },
  {
    id: 'user-2',
    name: 'Dr. Suresh Patil',
    role: 'Competent Authority',
    designation: 'Member Secretary / Authorised Official',
    avatar: 'SP',
  },
  {
    id: 'user-3',
    name: 'Dr. Meera Shah',
    role: 'EVC Committee Lead',
    designation: 'Expert Visiting Committee Inspector',
    avatar: 'MS',
  },
  {
    id: 'user-4',
    name: 'Prof. Ramesh Kulkarni',
    role: 'Institution Applicant',
    designation: 'Director, Sahyadri College of Eng.',
    avatar: 'RK',
  },
];

interface AppState {
  applications: ApplicationRecord[];
  documents: ComplianceDocument[];
  evcs: EvcRecord[];
  notifications: NotificationItem[];
  auditLogs: AuditEvent[];
  currentUser: UserProfile;
  notificationPreferences: {
    deadlines: boolean;
    deficiencies: boolean;
    evcs: boolean;
    escalations: boolean;
  };
}

class MockStore {
  private state: AppState;
  private listeners: Set<() => void> = new Set();

  constructor() {
    this.state = {
      applications: JSON.parse(JSON.stringify(seedApplications)),
      documents: JSON.parse(JSON.stringify(seedDocs)),
      evcs: JSON.parse(JSON.stringify(seedEvcs)),
      notifications: JSON.parse(JSON.stringify(seedNotes)),
      auditLogs: JSON.parse(JSON.stringify(seedAudit)),
      currentUser: DEMO_USERS[0],
      notificationPreferences: {
        deadlines: true,
        deficiencies: true,
        evcs: true,
        escalations: true,
      },
    };
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify() {
    this.listeners.forEach((listener) => listener());
  }

  public getState(): AppState {
    return this.state;
  }

  public setCurrentUser(user: UserProfile) {
    this.state.currentUser = user;
    this.notify();
  }

  public getApplications(): ApplicationRecord[] {
    return this.state.applications;
  }

  public getApplicationById(id: string): ApplicationRecord | undefined {
    return this.state.applications.find((a) => a.id === id);
  }

  public getDocuments(): ComplianceDocument[] {
    return this.state.documents;
  }

  public getEvcs(): EvcRecord[] {
    return this.state.evcs;
  }

  public getNotifications(): NotificationItem[] {
    return this.state.notifications;
  }

  public getAuditLogs(): AuditEvent[] {
    return this.state.auditLogs;
  }

  public addAuditLog(
    action: string,
    appId: string,
    before: string,
    after: string,
    reason: string,
    actorOverride?: string
  ) {
    const actor = actorOverride || this.state.currentUser.name;
    const now = new Date();
    const timestamp = now.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    const newEvent: AuditEvent = {
      id: Date.now(),
      at: timestamp,
      actor,
      action,
      app: appId,
      before,
      after,
      reason,
    };

    this.state.auditLogs.unshift(newEvent);
    this.notify();
  }

  public addApplication(newApp: Omit<ApplicationRecord, 'id' | 'stage' | 'status' | 'age' | 'submittedAt'>): ApplicationRecord {
    const generatedId = `AI-2026-${Math.floor(1850 + Math.random() * 850)}`;
    const now = new Date();
    const submittedAt = now.toISOString().split('T')[0];

    const application: ApplicationRecord = {
      ...newApp,
      id: generatedId,
      stage: 0,
      status: 'Submitted',
      age: 0,
      submittedAt,
      owner: 'Scrutiny desk',
    };

    this.state.applications.unshift(application);

    this.addAuditLog(
      'Registered application',
      generatedId,
      'None',
      'Submitted',
      'Initial application intake registered by institution applicant.'
    );

    this.state.notifications.unshift({
      id: `N-${Date.now()}`,
      kind: 'Deadline reminder',
      title: 'New application registered',
      body: `${application.name} submitted ${application.type}. Assigned route: ${application.assignedRoute}.`,
      time: 'Just now',
      read: false,
      app: generatedId,
    });

    this.notify();
    return application;
  }

  public recordDeficiency(appId: string, deficiencyReason: string): boolean {
    const app = this.state.applications.find((a) => a.id === appId);
    if (!app) return false;

    const beforeStatus = app.status;
    app.deficiency = deficiencyReason;
    app.status = 'Deficiency raised';
    app.owner = 'Institution';

    this.addAuditLog(
      'Raised deficiency',
      app.id,
      beforeStatus,
      app.status,
      deficiencyReason
    );

    this.state.notifications.unshift({
      id: `N-${Date.now()}`,
      kind: 'Deficiency alert',
      title: 'Deficiency raised',
      body: `${app.name} returned for document/data correction: ${deficiencyReason}`,
      time: 'Just now',
      read: false,
      app: app.id,
    });

    this.notify();
    return true;
  }

  public advanceStage(appId: string, rationale: string): boolean {
    const app = this.state.applications.find((a) => a.id === appId);
    if (!app || app.stage >= WORKFLOW_STAGES.length - 1) return false;

    const beforeStage = WORKFLOW_STAGES[app.stage];
    const newStageIndex = app.stage + 1;
    app.stage = newStageIndex;
    app.deficiency = ''; // Clear deficiency on advancement

    const stageStatusMap: Record<number, ApplicationRecord['status']> = {
      0: 'Submitted',
      1: 'Pending scrutiny',
      2: 'Under re-scrutiny',
      3: 'EVC scheduled',
      4: 'Decision pending',
      5: 'Approved',
    };

    const stageOwnerMap: Record<number, string> = {
      0: 'Scrutiny desk',
      1: 'Ananya Rao',
      2: 'Scrutiny officer',
      3: 'EVC committee',
      4: 'Executive committee',
      5: 'Institution',
    };

    app.status = stageStatusMap[newStageIndex] || 'Decision pending';
    app.owner = stageOwnerMap[newStageIndex] || 'Assigned officer';

    this.addAuditLog(
      'Moved to next stage',
      app.id,
      beforeStage,
      WORKFLOW_STAGES[newStageIndex],
      rationale
    );

    this.notify();
    return true;
  }

  public recordOfficialDecision(
    appId: string,
    outcome: 'Approved' | 'Rejected',
    rationale: string
  ): boolean {
    const app = this.state.applications.find((a) => a.id === appId);
    if (!app) return false;

    const beforeStatus = app.status;
    app.stage = 5;
    app.status = outcome;
    app.owner = 'Institution';

    this.addAuditLog(
      `Recorded official decision: ${outcome}`,
      app.id,
      beforeStatus,
      outcome,
      rationale
    );

    this.state.notifications.unshift({
      id: `N-${Date.now()}`,
      kind: 'Escalation',
      title: `Official decision recorded: ${outcome}`,
      body: `Competent Authority recorded final decision for ${app.name}: ${outcome}. Rationale: ${rationale}`,
      time: 'Just now',
      read: false,
      app: app.id,
    });

    this.notify();
    return true;
  }

  public sendReminder(appId: string): boolean {
    const app = this.state.applications.find((a) => a.id === appId);
    if (!app) return false;

    const note: NotificationItem = {
      id: `N-${Date.now()}`,
      kind: 'Deadline reminder',
      title: 'Reminder sent',
      body: `${app.name}: Target deadline ${app.deadline} reminder sent to ${app.owner}.`,
      time: 'Just now',
      read: true,
      app: app.id,
    };

    this.state.notifications.unshift(note);

    this.addAuditLog(
      'Sent deadline reminder',
      app.id,
      'Not sent',
      'Sent',
      `Manual deadline reminder dispatched to ${app.owner}.`
    );

    this.notify();
    return true;
  }

  public rescheduleEvc(evcId: string, newDate: string): boolean {
    const evc = this.state.evcs.find((e) => e.id === evcId);
    if (!evc) return false;

    const oldDate = evc.date;
    evc.date = newDate;
    evc.status = 'Scheduled';

    this.addAuditLog(
      'Rescheduled EVC',
      evc.app,
      oldDate,
      newDate,
      'Inspection date updated by EVC coordinator.'
    );

    this.notify();
    return true;
  }

  public assignEvc(evcId: string, members: string): boolean {
    const evc = this.state.evcs.find((e) => e.id === evcId);
    if (!evc) return false;

    const oldMembers = evc.members;
    evc.members = members;
    evc.status = 'Scheduled';

    this.addAuditLog(
      'Assigned EVC committee',
      evc.app,
      oldMembers,
      members,
      'Committee assignment updated by coordinator.'
    );

    this.notify();
    return true;
  }

  public uploadEvcEvidence(evcId: string, filename: string): boolean {
    const evc = this.state.evcs.find((e) => e.id === evcId);
    if (!evc) return false;

    const oldEvidence = evc.evidence;
    evc.evidence = filename;

    this.addAuditLog(
      'Attached EVC evidence',
      evc.app,
      oldEvidence,
      filename,
      'Inspection evidence filename recorded in prototype.'
    );

    this.notify();
    return true;
  }

  public completeEvc(evcId: string, note: string): boolean {
    const evc = this.state.evcs.find((e) => e.id === evcId);
    if (!evc) return false;

    evc.status = 'Completed';
    evc.reportNotes = note;

    const linkedApp = this.state.applications.find((a) => a.id === evc.app);
    if (linkedApp && linkedApp.status === 'EVC scheduled') {
      linkedApp.status = 'EVC completed';
    }

    this.addAuditLog(
      'Completed EVC',
      evc.app,
      'Scheduled',
      'Completed',
      note || 'Inspection verified and completed by visiting committee.'
    );

    this.notify();
    return true;
  }

  public verifyUndertaking(docId: string, note: string): boolean {
    const doc = this.state.documents.find((d) => d.id === docId);
    if (!doc) return false;

    const oldStatus = doc.status;
    doc.status = 'Verified';

    const linkedApp = this.state.applications.find((a) => a.name === doc.institution);

    this.addAuditLog(
      'Verified undertaking',
      linkedApp?.id || 'GLOBAL',
      oldStatus,
      'Verified',
      note || 'Undertaking compliance checked against AICTE guidelines.'
    );

    this.notify();
    return true;
  }

  public renewDocument(docId: string, newExpiry: string, filename: string): boolean {
    const doc = this.state.documents.find((d) => d.id === docId);
    if (!doc) return false;

    const oldStatus = doc.status;
    doc.expiry = newExpiry;
    doc.status = 'Valid';
    doc.version = (doc.version || 1) + 1;
    doc.filename = filename;

    const linkedApp = this.state.applications.find((a) => a.name === doc.institution);

    this.addAuditLog(
      'Renewed document',
      linkedApp?.id || 'GLOBAL',
      oldStatus,
      'Valid',
      `${doc.name} renewed with expiry ${newExpiry}; version ${doc.version} attached.`
    );

    this.notify();
    return true;
  }

  public submitUndertaking(
    institution: string,
    name: string,
    expiry: string,
    filename: string
  ): boolean {
    const newDoc: ComplianceDocument = {
      id: `D-${Date.now()}`,
      name,
      institution,
      type: 'Undertaking',
      expiry,
      status: 'Pending verification',
      version: 1,
      filename,
      uploadedAt: new Date().toISOString().split('T')[0],
    };

    this.state.documents.unshift(newDoc);

    const linkedApp = this.state.applications.find((a) => a.name === institution);

    this.addAuditLog(
      'Submitted undertaking',
      linkedApp?.id || 'GLOBAL',
      'None',
      'Pending verification',
      `${name} submitted for institutional verification.`
    );

    this.notify();
    return true;
  }

  public toggleNotificationRead(noteId: string) {
    const note = this.state.notifications.find((n) => n.id === noteId);
    if (note) {
      note.read = !note.read;
      this.notify();
    }
  }

  public markAllNotificationsRead() {
    this.state.notifications.forEach((n) => {
      n.read = true;
    });
    this.notify();
  }

  public setNotificationPreference(key: keyof AppState['notificationPreferences'], value: boolean) {
    this.state.notificationPreferences[key] = value;
    this.notify();
  }
}

export const mockStore = new MockStore();
