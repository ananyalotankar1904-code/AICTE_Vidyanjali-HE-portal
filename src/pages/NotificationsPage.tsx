import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortal } from '../context/PortalContext';

export const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    role,
    appId,
    notificationsRead,
    markAllNotificationsRead,
    canonicalData,
  } = usePortal();

  const coreNotifications = [
    {
      title: 'Meeting confirmed',
      detail: '05 Nov · 11:00 AM',
      route: '/schedule',
      priority: 'Attention',
    },
    {
      title: 'Deficiency response due',
      detail: '12 Nov 2026',
      route: '/deficiencies',
      priority: 'Urgent',
    },
    {
      title: 'Document requires attention',
      detail: 'Registrar ID is missing',
      route: '/documents',
      priority: 'Attention',
    },
  ];

  // Also include Dataset 7 notifications
  const datasetNotifications = (canonicalData.notifications || []).slice(0, 7).map((n: any) => ({
    title: n.title || n.message || 'Notification Notice',
    detail: `${n.priority || 'Informational'} · Target: ${n.target_role || 'All'} · App: ${n.application_id || 'AICTE'}`,
    route: '/applications',
    priority: n.priority || 'Informational',
  }));

  const allNotifications = [...coreNotifications, ...datasetNotifications];

  const getPriorityBadgeColor = (p: string) => {
    if (p === 'Urgent') return 'red';
    if (p === 'Attention') return 'amber';
    return 'blue';
  };

  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Notifications &amp; deadlines</h1>
          <p>Messages and upcoming actions for the selected demo role.</p>
        </div>
        <button className="btn" onClick={markAllNotificationsRead}>
          Mark all read
        </button>
      </div>

      <section className="card">
        {allNotifications.map((n, idx) => (
          <div key={idx} className="listrow">
            <div>
              <strong>{n.title}</strong>
              <small>
                {n.detail} · Role: {role} · Case: {appId}
              </small>
            </div>
            <div className="buttonrow">
              <span className={`badge ${getPriorityBadgeColor(n.priority)}`}>
                {n.priority}
              </span>
              <span className={`badge ${notificationsRead ? '' : 'blue'}`}>
                {notificationsRead ? 'Read' : 'Unread'}
              </span>
              <button className="btn text" onClick={() => navigate(n.route)}>
                Open →
              </button>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
};
