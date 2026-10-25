import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Bell, Sparkles } from 'lucide-react';
import { useStore } from '../../hooks/useStore';

interface TopbarProps {
  onOpenRoleModal: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenRoleModal }) => {
  const location = useLocation();
  const { notifications, currentUser } = useStore();
  const unreadCount = notifications.filter((n) => !n.read).length;

  const getBreadcrumbTitle = (pathname: string): string => {
    if (pathname === '/') return 'Overview';
    if (pathname.startsWith('/applications/new')) return 'New Application Intake';
    if (pathname.startsWith('/applications/') && pathname !== '/applications') return 'Application Details';
    if (pathname.startsWith('/applications')) return 'Applications';
    if (pathname.startsWith('/evc')) return 'EVC Management';
    if (pathname.startsWith('/compliance')) return 'Compliance & Documents';
    if (pathname.startsWith('/notifications')) return 'Notifications';
    if (pathname.startsWith('/audit')) return 'Audit History';
    return 'Workspace';
  };

  return (
    <header className="app-topbar">
      <div className="breadcrumb-area">
        <span>Workspace</span>
        <span>/</span>
        <b>{getBreadcrumbTitle(location.pathname)}</b>
      </div>

      <div className="topbar-actions">
        <span className="demo-badge-pill" title="Demonstration prototype environment with synthetic data">
          <Sparkles size={13} color="var(--accent-active)" />
          <span>Cycle 2026–27 · Illustrative Demo</span>
        </span>

        <Link
          to="/notifications"
          className="icon-btn"
          aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
        >
          <Bell size={18} />
          {unreadCount > 0 && <span className="notification-dot" />}
        </Link>

        <button
          type="button"
          className="user-avatar"
          onClick={onOpenRoleModal}
          title={`Active demo persona: ${currentUser.name} (${currentUser.role}). Click to switch.`}
          style={{ cursor: 'pointer' }}
        >
          {currentUser.avatar}
        </button>
      </div>
    </header>
  );
};
