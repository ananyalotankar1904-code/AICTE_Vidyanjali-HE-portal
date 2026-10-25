import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  FilePlus2,
  Calendar,
  ShieldCheck,
  Bell,
  History,
  UserCheck,
} from 'lucide-react';
import { useStore } from '../../hooks/useStore';

interface SidebarProps {
  onOpenRoleModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenRoleModal }) => {
  const { notifications, currentUser } = useStore();
  const unreadCount = notifications.filter((n) => !n.read).length;

  const navItems = [
    { to: '/', label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { to: '/applications', label: 'Applications', icon: <FileText size={18} /> },
    { to: '/applications/new', label: 'New Intake', icon: <FilePlus2 size={18} /> },
    { to: '/evc', label: 'EVC Management', icon: <Calendar size={18} /> },
    { to: '/compliance', label: 'Compliance & Docs', icon: <ShieldCheck size={18} /> },
    {
      to: '/notifications',
      label: 'Notifications',
      icon: <Bell size={18} />,
      counter: unreadCount > 0 ? unreadCount : undefined,
    },
    { to: '/audit', label: 'Audit History', icon: <History size={18} /> },
  ];

  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      <div className="brand-section">
        {/* AICTE Logo Emblem in Golden Yellow */}
        <div className="brand-mark" aria-hidden="true" title="AICTE Logo">
          <svg
            width="28"
            height="28"
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Outer Golden Gear/Sunburst */}
            <circle cx="50" cy="50" r="44" stroke="#F4C542" strokeWidth="6" fill="#FFFCF2" />
            <circle cx="50" cy="50" r="36" stroke="#D99A13" strokeWidth="2" strokeDasharray="3 3" />
            {/* Center Sacred Lamp / Flame of Knowledge */}
            <path
              d="M50 20C50 20 58 32 58 42C58 47 54.4 51 50 51C45.6 51 42 47 42 42C42 32 50 20 50 20Z"
              fill="#F4C542"
            />
            <path
              d="M50 28C50 28 54 35 54 41C54 44 52.2 46 50 46C47.8 46 46 44 46 41C46 35 50 28 50 28Z"
              fill="#D99A13"
            />
            {/* Base Lamp / Vessel */}
            <path
              d="M32 55C32 55 36 68 50 68C64 68 68 55 68 55C68 55 62 62 50 62C38 62 32 55 32 55Z"
              fill="#514332"
            />
            {/* Pedestal */}
            <rect x="42" y="68" width="16" height="5" rx="2" fill="#514332" />
            <rect x="36" y="74" width="28" height="4" rx="2" fill="#F4C542" />
          </svg>
        </div>
        <div className="brand-info">
          <span className="brand-name">AICTE_Vidyanjali-HE-portal</span>
          <span className="brand-subtitle">Approval & Compliance</span>
        </div>
      </div>

      <div className="nav-group-label">Workflow Management</div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-link-btn ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
            {item.counter !== undefined && (
              <span className="nav-counter" aria-label={`${item.counter} unread notifications`}>
                {item.counter}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button
          type="button"
          onClick={onOpenRoleModal}
          className="profile-card"
          style={{
            background: 'transparent',
            border: 'none',
            padding: '6px',
            textAlign: 'left',
            width: '100%',
            cursor: 'pointer',
          }}
          title="Click to switch simulated demo role"
        >
          <span className="user-avatar">{currentUser.avatar}</span>
          <div className="profile-info">
            <span className="profile-name">{currentUser.name}</span>
            <span className="profile-role">
              {currentUser.role} <UserCheck size={11} style={{ display: 'inline', marginLeft: 2, color: 'var(--accent-active)' }} />
            </span>
          </div>
        </button>
      </div>
    </aside>
  );
};
