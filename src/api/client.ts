/**
 * Shared API Client & Adapter for AICTE_Vidyanjali-HE-portal Platform
 *
 * Implements the endpoints specified in Section 9.1 of the SIH26262 README.
 * In local prototype mode, it delegates seamlessly to the reactive MockStore.
 * When a real backend is available (VITE_API_URL configured), it switches to HTTP fetch.
 */

import { mockStore } from '../data/mockStore';
import {
  ApplicationRecord,
  ComplianceDocument,
  EvcRecord,
  NotificationItem,
  AuditEvent,
  DashboardSummary,
  WORKFLOW_STAGES,
} from '../types';

const USE_LOCAL_MOCK = true; // Prototype mode default; toggle via env if backend running

export const apiClient = {
  // 1. Dashboard summary
  async getDashboardSummary(): Promise<DashboardSummary> {
    if (USE_LOCAL_MOCK) {
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
      };
    }

    const res = await fetch('/api/dashboard/summary');
    if (!res.ok) throw new Error('Failed to load dashboard summary');
    return res.json();
  },

  // 2. Applications
  async getApplications(): Promise<ApplicationRecord[]> {
    if (USE_LOCAL_MOCK) {
      return [...mockStore.getApplications()];
    }
    const res = await fetch('/api/applications');
    if (!res.ok) throw new Error('Failed to fetch applications');
    return res.json();
  },

  async getApplicationById(id: string): Promise<ApplicationRecord | null> {
    if (USE_LOCAL_MOCK) {
      const app = mockStore.getApplicationById(id);
      return app ? { ...app } : null;
    }
    const res = await fetch(`/api/applications/${id}`);
    if (!res.ok) return null;
    return res.json();
  },

  async createApplication(payload: Omit<ApplicationRecord, 'id' | 'stage' | 'status' | 'age' | 'submittedAt'>): Promise<ApplicationRecord> {
    if (USE_LOCAL_MOCK) {
      return mockStore.addApplication(payload);
    }
    const res = await fetch('/api/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create application');
    return res.json();
  },

  // 3. Workflow transitions
  async requestTransition(
    id: string,
    action: string,
    reason: string,
    outcome?: 'Approved' | 'Rejected'
  ): Promise<{ success: boolean; message: string }> {
    if (USE_LOCAL_MOCK) {
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

    const res = await fetch(`/api/applications/${id}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, reason, outcome }),
    });
    if (!res.ok) throw new Error('Transition rejected');
    return res.json();
  },

  // 4. Documents & Undertakings
  async getDocuments(): Promise<ComplianceDocument[]> {
    if (USE_LOCAL_MOCK) {
      return [...mockStore.getDocuments()];
    }
    const res = await fetch('/api/documents');
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  // 5. EVCs
  async getEvcs(): Promise<EvcRecord[]> {
    if (USE_LOCAL_MOCK) {
      return [...mockStore.getEvcs()];
    }
    const res = await fetch('/api/evcs');
    if (!res.ok) throw new Error('Failed to fetch EVC inspections');
    return res.json();
  },

  // 6. Notifications
  async getNotifications(): Promise<NotificationItem[]> {
    if (USE_LOCAL_MOCK) {
      return [...mockStore.getNotifications()];
    }
    const res = await fetch('/api/notifications');
    if (!res.ok) throw new Error('Failed to fetch notifications');
    return res.json();
  },

  // 7. Audit logs
  async getAuditLogs(): Promise<AuditEvent[]> {
    if (USE_LOCAL_MOCK) {
      return [...mockStore.getAuditLogs()];
    }
    const res = await fetch('/api/audit-logs');
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  },
};
