import { useState, useEffect } from 'react';
import { mockStore } from '../data/mockStore';

export function useStore() {
  const [state, setState] = useState(() => mockStore.getState());

  useEffect(() => {
    const unsubscribe = mockStore.subscribe(() => {
      setState({ ...mockStore.getState() });
    });
    return unsubscribe;
  }, []);

  return {
    state,
    currentUser: state.currentUser,
    applications: state.applications,
    documents: state.documents,
    evcs: state.evcs,
    notifications: state.notifications,
    auditLogs: state.auditLogs,
    notificationPreferences: state.notificationPreferences,
    store: mockStore,
  };
}
