import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  AlertTriangle,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { toast } from '../components/common/Toast';
import { useStore } from '../hooks/useStore';
import { NotificationKind } from '../types';

export const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();
  const { notifications, notificationPreferences, store } = useStore();

  const [activeFilter, setActiveFilter] = useState<string>('All');

  const filteredNotifications = notifications.filter((item) => {
    if (activeFilter === 'All') return true;
    if (activeFilter === 'Unread') return !item.read;
    return item.kind === activeFilter;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAllRead = () => {
    store.markAllNotificationsRead();
    toast.show('All notifications marked as read.', 'info');
  };

  const handleToggleRead = (id: string) => {
    store.toggleNotificationRead(id);
  };

  const getKindIcon = (kind: NotificationKind) => {
    switch (kind) {
      case 'Deficiency alert':
        return <AlertTriangle size={18} color="var(--danger)" />;
      case 'EVC reminder':
        return <Calendar size={18} color="var(--accent-active)" />;
      case 'Escalation':
        return <ShieldAlert size={18} color="var(--warn)" />;
      default:
        return <Bell size={18} color="var(--muted)" />;
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Your Attention Queue</div>
          <h1 className="page-title">Notifications & Reminders</h1>
          <p className="page-subtitle">
            Consolidated alerts for upcoming target deadlines, deficiency notices, EVC visit updates,
            and executive decision escalations.
          </p>
        </div>

        <div className="head-actions">
          <Button
            variant="secondary"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            icon={<CheckCircle2 size={15} />}
          >
            Mark All Read ({unreadCount})
          </Button>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Left: Notification Feed */}
        <Card padded={false}>
          <div style={{ padding: '20px 22px 14px', borderBottom: '1px solid var(--border-soft)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>Inbox Stream</h2>
              <div className="form-field" style={{ minWidth: '180px' }}>
                <select
                  value={activeFilter}
                  onChange={(e) => setActiveFilter(e.target.value)}
                  aria-label="Filter notifications by category"
                >
                  <option value="All">All notifications</option>
                  <option value="Unread">Unread only</option>
                  <option value="Deadline reminder">Deadline reminders</option>
                  <option value="Deficiency alert">Deficiency alerts</option>
                  <option value="EVC reminder">EVC reminders</option>
                  <option value="Escalation">Escalations</option>
                </select>
              </div>
            </div>
          </div>

          {filteredNotifications.length === 0 ? (
            <EmptyState
              title="All caught up!"
              description="No notifications match the chosen filter view."
              icon={<CheckCircle2 size={42} color="#16a34a" />}
            />
          ) : (
            <div>
              {filteredNotifications.map((note) => (
                <div
                  key={note.id}
                  className={`notification-card ${note.read ? '' : 'unread'}`}
                >
                  <div className="notification-icon-pill">{getKindIcon(note.kind)}</div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600 }}>
                        {note.kind} · {note.time}
                      </span>
                      {!note.read && (
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 700,
                            background: 'var(--accent-subtle)',
                            color: 'var(--accent-active)',
                            border: '1px solid var(--accent-border)',
                            padding: '1px 6px',
                            borderRadius: '4px',
                          }}
                        >
                          NEW
                        </span>
                      )}
                    </div>

                    <h3 style={{ fontSize: '14px', fontWeight: 700, margin: '4px 0 2px', color: 'var(--ink)' }}>
                      {note.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--fg-2)', margin: 0, lineHeight: 1.45 }}>
                      {note.body}
                    </p>

                    <div style={{ display: 'flex', gap: '14px', alignItems: 'center', marginTop: '8px' }}>
                      <button
                        type="button"
                        className="button ghost"
                        style={{ padding: 0, minHeight: 'auto', fontSize: '12px' }}
                        onClick={() => navigate(`/applications/${note.app}`)}
                      >
                        Inspect Application {note.app} <ChevronRight size={13} />
                      </button>
                    </div>
                  </div>

                  <div style={{ flexShrink: 0 }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleToggleRead(note.id)}
                    >
                      {note.read ? 'Mark Unread' : 'Mark Read'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Right: Notification Delivery Preferences */}
        <div style={{ display: 'grid', gap: '18px', alignContent: 'start' }}>
          <Card>
            <CardHeader
              title="Alert Preferences"
              subtitle="Configure which operational reminders appear in your active workspace"
            />

            <div style={{ display: 'grid', gap: '14px', marginTop: '12px' }}>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-soft)',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 650 }}>Target Deadline Alerts</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Upcoming response deadlines within 15 days
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notificationPreferences.deadlines}
                  onChange={(e) => store.setNotificationPreference('deadlines', e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                />
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-soft)',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 650 }}>Deficiency Correction Notices</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Institutional document deficiency alerts
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notificationPreferences.deficiencies}
                  onChange={(e) => store.setNotificationPreference('deficiencies', e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                />
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-soft)',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 650 }}>EVC Inspection Reminders</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Visiting committee visits and report filings
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notificationPreferences.evcs}
                  onChange={(e) => store.setNotificationPreference('evcs', e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                />
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-soft)',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 650 }}>Executive Escalations</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    Authorised decision delays exceeding 7 days
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notificationPreferences.escalations}
                  onChange={(e) => store.setNotificationPreference('escalations', e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--accent)' }}
                />
              </label>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
