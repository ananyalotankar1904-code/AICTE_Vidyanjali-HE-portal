import React, { createContext, useContext, useState, useEffect } from 'react';
import canonicalJson from '../data/canonicalData.json';
import { Language, getTranslation } from '../utils/translations';

export const ROLES = [
  'Institution Applicant / Institution Admin',
  'Intake Officer',
  'Scrutiny Officer',
  'EVC Coordinator',
  'Committee Secretariat',
  'Competent Authority Secretariat',
] as const;

export type PortalRole = typeof ROLES[number];

export interface PortalAuditLog {
  id: string;
  action: string;
  time: string;
  role: string;
  app: string;
  detail?: string;
}

export interface PortalDialogState {
  isOpen: boolean;
  title: string;
  children: React.ReactNode;
  confirmLabel?: string;
  onConfirm?: () => void;
  notice?: string;
}

interface PortalContextType {
  role: PortalRole;
  setRole: (r: PortalRole) => void;
  language: Language;
  setLanguage: (l: Language) => void;
  toggleLanguage: () => void;
  t: (key: string) => string;
  appId: string;
  setAppId: (id: string) => void;
  institutionName: string;
  slotRescheduled: boolean;
  rescheduleRequested: boolean;
  rescheduleReason: string;
  reschedulePreferred: string;
  deficiencyStatus: 'OPEN' | 'RESPONSE_SUBMITTED' | 'REVIEWED';
  deficiencyResponse: string;
  deficiencyOutcome: 'Resolved' | 'Retained / reopen' | '';
  deficiencyReviewReason: string;
  documents: Record<string, string>;
  notificationsRead: boolean;
  auditLogs: PortalAuditLog[];
  canonicalData: typeof canonicalJson;
  // UI helpers
  toastMessage: string | null;
  showToast: (msg: string) => void;
  dialog: PortalDialogState | null;
  openDialog: (d: Omit<PortalDialogState, 'isOpen'>) => void;
  closeDialog: () => void;
  // Demo Actions
  submitRescheduleRequest: (reason: string, preferred: string) => void;
  assignScrutinySlot: (slot: 'booked' | 'available', duration: string) => boolean;
  submitDeficiencyResponse: (response: string) => void;
  reviewDeficiencyResponse: (outcome: 'Resolved' | 'Retained / reopen', reason: string) => void;
  simulateDocumentReplace: (docName: string) => void;
  markAllNotificationsRead: () => void;
  resetDemoState: () => void;
}

const PortalContext = createContext<PortalContextType | undefined>(undefined);

export const PortalProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRoleState] = useState<PortalRole>(ROLES[0]);
  const [language, setLanguageState] = useState<Language>('en');
  const [appId, setAppId] = useState<string>('DEMO-2026-0042');
  const [institutionName] = useState<string>('Sample Institute of Technology');

  // Interactive Demo States matching sih_final.html
  const [slotRescheduled, setSlotRescheduled] = useState<boolean>(false);
  const [rescheduleRequested, setRescheduleRequested] = useState<boolean>(false);
  const [rescheduleReason, setRescheduleReason] = useState<string>('');
  const [reschedulePreferred, setReschedulePreferred] = useState<string>('');

  const [deficiencyStatus, setDeficiencyStatus] = useState<'OPEN' | 'RESPONSE_SUBMITTED' | 'REVIEWED'>('OPEN');
  const [deficiencyResponse, setDeficiencyResponse] = useState<string>('');
  const [deficiencyOutcome, setDeficiencyOutcome] = useState<'Resolved' | 'Retained / reopen' | ''>('');
  const [deficiencyReviewReason, setDeficiencyReviewReason] = useState<string>('');

  const [documents, setDocuments] = useState<Record<string, string>>({
    'Principal ID': 'Verified',
    'Registrar ID': 'Missing',
    'Management authorization letter': 'Pending Review',
    'Case-specific evidence': 'Uploaded',
  });

  const [notificationsRead, setNotificationsRead] = useState<boolean>(false);
  const [auditLogs, setAuditLogs] = useState<PortalAuditLog[]>([]);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [dialog, setDialog] = useState<PortalDialogState | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
  };

  const toggleLanguage = () => {
    const next = language === 'en' ? 'hi' : 'en';
    setLanguageState(next);
    showToast(next === 'hi' ? 'भाषा हिन्दी में बदली गई' : 'Language switched to English');
  };

  const setLanguage = (l: Language) => {
    setLanguageState(l);
  };

  const t = (key: string): string => {
    return getTranslation(key, language);
  };

  useEffect(() => {
    if (!toastMessage) return;
    const timer = setTimeout(() => {
      setToastMessage(null);
    }, 3500);
    return () => clearTimeout(timer);
  }, [toastMessage]);

  const openDialog = (d: Omit<PortalDialogState, 'isOpen'>) => {
    setDialog({ ...d, isOpen: true });
  };

  const closeDialog = () => {
    setDialog(null);
  };

  const logAudit = (action: string, detail?: string) => {
    const time = new Date().toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
    setAuditLogs((prev) => [
      {
        id: `LOG-${Date.now()}`,
        action,
        time,
        role,
        app: appId,
        detail,
      },
      ...prev,
    ]);
  };

  const setRole = (newRole: PortalRole) => {
    setRoleState(newRole);
    showToast(`Switched simulated role to ${newRole}`);
  };

  const submitRescheduleRequest = (reason: string, preferred: string) => {
    setRescheduleRequested(true);
    setRescheduleReason(reason);
    setReschedulePreferred(preferred);
    logAudit('Reschedule request submitted', `Reason: ${reason}, Preferred: ${preferred}`);
    closeDialog();
    showToast('Demo request recorded; original appointment retained.');
  };

  const assignScrutinySlot = (slot: 'booked' | 'available', duration: string): boolean => {
    if (slot === 'booked') {
      showToast('Conflict: this officer already has a booking. Choose an available slot.');
      return false;
    }
    setSlotRescheduled(true);
    setRescheduleRequested(false);
    logAudit('Non-conflicting demo scrutiny slot assigned', `Slot: 06 Nov 11:00 AM, Duration: ${duration}`);
    closeDialog();
    showToast('Demo slot assigned; no booking was persisted.');
    return true;
  };

  const submitDeficiencyResponse = (resp: string) => {
    setDeficiencyResponse(resp);
    setDeficiencyStatus('RESPONSE_SUBMITTED');
    logAudit('Mock deficiency response submitted', resp);
    closeDialog();
    showToast('Response recorded in demo state.');
  };

  const reviewDeficiencyResponse = (outcome: 'Resolved' | 'Retained / reopen', rsn: string) => {
    setDeficiencyOutcome(outcome);
    setDeficiencyReviewReason(rsn);
    setDeficiencyStatus('REVIEWED');
    logAudit('Mock deficiency response reviewed', `Outcome: ${outcome}, Reason: ${rsn}`);
    closeDialog();
    showToast('Review recorded in demo state.');
  };

  const simulateDocumentReplace = (docName: string) => {
    setDocuments((prev) => ({
      ...prev,
      [docName]: 'Pending Review',
    }));
    logAudit(`${docName} replacement simulated`);
    closeDialog();
    showToast('Replacement marked pending review in demo state.');
  };

  const markAllNotificationsRead = () => {
    setNotificationsRead(true);
    logAudit('Marked all notifications as read');
    showToast('Demo notifications marked read.');
  };

  const resetDemoState = () => {
    setSlotRescheduled(false);
    setRescheduleRequested(false);
    setRescheduleReason('');
    setReschedulePreferred('');
    setDeficiencyStatus('OPEN');
    setDeficiencyResponse('');
    setDeficiencyOutcome('');
    setDeficiencyReviewReason('');
    setDocuments({
      'Principal ID': 'Verified',
      'Registrar ID': 'Missing',
      'Management authorization letter': 'Pending Review',
      'Case-specific evidence': 'Uploaded',
    });
    setNotificationsRead(false);
    setAuditLogs([]);
    showToast('Demo state reset to baseline.');
  };

  return (
    <PortalContext.Provider
      value={{
        role,
        setRole,
        language,
        setLanguage,
        toggleLanguage,
        t,
        appId,
        setAppId,
        institutionName,
        slotRescheduled,
        rescheduleRequested,
        rescheduleReason,
        reschedulePreferred,
        deficiencyStatus,
        deficiencyResponse,
        deficiencyOutcome,
        deficiencyReviewReason,
        documents,
        notificationsRead,
        auditLogs,
        canonicalData: canonicalJson,
        toastMessage,
        showToast,
        dialog,
        openDialog,
        closeDialog,
        submitRescheduleRequest,
        assignScrutinySlot,
        submitDeficiencyResponse,
        reviewDeficiencyResponse,
        simulateDocumentReplace,
        markAllNotificationsRead,
        resetDemoState,
      }}
    >
      {children}
    </PortalContext.Provider>
  );
};

export const usePortal = (): PortalContextType => {
  const context = useContext(PortalContext);
  if (!context) {
    throw new Error('usePortal must be used within a PortalProvider');
  }
  return context;
};
