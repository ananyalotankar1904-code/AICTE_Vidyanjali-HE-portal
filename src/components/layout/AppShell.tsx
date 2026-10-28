import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { usePortal, ROLES, PortalRole } from '../../context/PortalContext';

interface AppShellProps {
  children: React.ReactNode;
}

interface SubMenuItem {
  to: string;
  label: string;
}

interface NavGroup {
  id: string;
  type: 'group';
  label: string;
  icon: string;
  items: SubMenuItem[];
}

interface NavStandalone {
  id: string;
  type: 'standalone';
  to: string;
  label: string;
  icon: string;
  badge?: number;
}

type NavEntry = NavStandalone | NavGroup;

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const {
    role,
    setRole,
    language,
    toggleLanguage,
    t,
    toastMessage,
    dialog,
    closeDialog,
    showToast,
    notificationsRead,
  } = usePortal();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const isApplicant = role === ROLES[0];
  const isLangToggleSupported = role === ROLES[0] || role === 'Scrutiny Officer';

  // Submenu collapse/expand state (all open by default as requested)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    'app-processing': true,
    'compliance-oversight': true,
    'help-reference': true,
  });

  const toggleGroup = (groupId: string) => {
    setOpenGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId],
    }));
  };

  // Exactly aligned with user's requested order:
  // 1. Dashboard (standalone, top level)
  // 2. Application Processing (with submenus: Applications, Document Readiness, Scheduling, Deficiencies)
  // 3. Compliance & Oversight (with submenus: EVC Management, Compliance, Audit History)
  // 4. Notifications (standalone, so alerts stay one click away)
  // 5. Help & Reference (with submenus: Process Guide, Workflow / BPMN)
  const navEntries: NavEntry[] = [
    // 1. Dashboard (standalone, top level)
    {
      id: 'dashboard',
      type: 'standalone',
      to: '/',
      label: isApplicant ? t('nav_my_dashboard') : t('nav_dashboard'),
      icon: '⌂',
    },

    // 2. Application Processing
    {
      id: 'app-processing',
      type: 'group',
      label: t('nav_app_processing'),
      icon: '📑',
      items: [
        {
          to: '/applications',
          label: isApplicant ? t('nav_my_applications') : t('nav_applications'),
        },
        {
          to: '/documents',
          label: isApplicant ? t('nav_my_doc_readiness') : t('nav_doc_readiness'),
        },
        {
          to: isApplicant ? '/schedule' : '/scheduling',
          label: isApplicant ? t('nav_my_schedule') : t('nav_scheduling'),
        },
        {
          to: '/deficiencies',
          label: isApplicant ? t('nav_my_deficiencies') : t('nav_deficiencies'),
        },
      ],
    },

    // 3. Compliance & Oversight
    {
      id: 'compliance-oversight',
      type: 'group',
      label: t('nav_compliance_oversight'),
      icon: '🛡',
      items: [
        {
          to: '/evc',
          label: t('nav_evc'),
        },
        {
          to: '/compliance',
          label: t('nav_compliance'),
        },
        {
          to: '/audit',
          label: t('nav_audit'),
        },
      ],
    },

    // 4. Notifications (standalone, so alerts stay one click away)
    {
      id: 'notifications',
      type: 'standalone',
      to: '/notifications',
      label: t('nav_notifications'),
      icon: '♧',
      badge: !notificationsRead ? 3 : undefined,
    },

    // 5. Help & Reference
    {
      id: 'help-reference',
      type: 'group',
      label: t('nav_help_reference'),
      icon: 'ⓘ',
      items: [
        {
          to: '/guide',
          label: t('nav_process_guide'),
        },
        {
          to: '/workflow',
          label: t('nav_workflow_bpmn'),
        },
      ],
    },
  ];

  // Resolve breadcrumb title
  const getCrumbTitle = () => {
    const path = location.pathname;
    if (path === '/') return isApplicant ? t('nav_my_dashboard') : t('nav_dashboard');
    if (path.startsWith('/applications/new')) return language === 'hi' ? 'नया आवेदन' : 'New Application';
    if (path.startsWith('/applications/') || path === '/case') return language === 'hi' ? 'मामला फ़ाइल' : 'Case File';
    if (path.startsWith('/applications')) return isApplicant ? t('nav_my_applications') : t('nav_applications');
    if (path.startsWith('/schedule') || path.startsWith('/scheduling')) return isApplicant ? t('nav_my_schedule') : t('nav_scheduling');
    if (path.startsWith('/documents')) return isApplicant ? t('nav_my_doc_readiness') : t('nav_doc_readiness');
    if (path.startsWith('/compliance')) return t('nav_compliance');
    if (path.startsWith('/deficiencies')) return isApplicant ? t('nav_my_deficiencies') : t('nav_deficiencies');
    if (path.startsWith('/evc')) return t('nav_evc');
    if (path.startsWith('/notifications')) return t('nav_notifications');
    if (path.startsWith('/audit')) return t('nav_audit');
    if (path.startsWith('/guide')) return t('nav_process_guide');
    if (path.startsWith('/workflow')) return t('nav_workflow_bpmn');
    return 'Overview';
  };

  return (
    <div className="shell">
      {/* Sidebar */}
      <aside className={`sidebar ${mobileMenuOpen ? 'open' : ''}`} id="sidebar">
        <div className="brand">
          <img src="/aicte-logo.png" width="46" height="46" alt="AICTE logo" />
          <div>
            <strong>AICTE Portal</strong>
            <small>{language === 'hi' ? 'अनुमोदन एवं अनुपालन' : 'Approval & Compliance'}</small>
          </div>
        </div>

        <div className="navlabel">{language === 'hi' ? 'कार्यक्षेत्र' : 'WORKSPACE'}</div>

        <nav className="nav" id="nav">
          {navEntries.map((entry) => {
            if (entry.type === 'standalone') {
              return (
                <NavLink
                  key={entry.id}
                  to={entry.to}
                  end={entry.to === '/'}
                  className={({ isActive }) => (isActive ? 'active' : '')}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <span className="ico" aria-hidden="true">{entry.icon}</span>
                  <span style={{ flex: 1 }}>{entry.label}</span>
                  {entry.badge && (
                    <span
                      style={{
                        background: 'var(--red)',
                        color: 'white',
                        borderRadius: '99px',
                        padding: '1px 6px',
                        fontSize: '10px',
                        fontWeight: 800,
                      }}
                    >
                      {entry.badge}
                    </span>
                  )}
                </NavLink>
              );
            }

            // Group with Submenus
            const isOpen = openGroups[entry.id] ?? true;
            const hasActiveChild = entry.items.some((item) => {
              if (item.to === '/') return location.pathname === '/';
              return location.pathname.startsWith(item.to);
            });

            return (
              <div key={entry.id} className="nav-group">
                <button
                  type="button"
                  className={`nav-group-header ${hasActiveChild ? 'has-active' : ''}`}
                  onClick={() => toggleGroup(entry.id)}
                  aria-expanded={isOpen}
                >
                  <div className="nav-group-title">
                    <span className="ico" aria-hidden="true">{entry.icon}</span>
                    <span>{entry.label}</span>
                  </div>
                  <span className="nav-group-chevron">
                    {isOpen ? '▾' : '▸'}
                  </span>
                </button>

                {isOpen && (
                  <div className="nav-submenu">
                    {entry.items.map((sub) => (
                      <NavLink
                        key={sub.to}
                        to={sub.to}
                        className={({ isActive }) => (isActive ? 'active' : '')}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <span className="sub-bullet">•</span>
                        <span>{sub.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        <div className="side-bottom">
          Smart India Hackathon 2026<br />
          <strong>{language === 'hi' ? 'सांकेतिक प्रोटोटाइप' : 'Illustrative prototype'}</strong>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main">
        {/* Topbar */}
        <header className="topbar">
          <button
            className="iconbtn mobile-menu"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation"
          >
            ☰
          </button>

          <div className="crumb">
            {t('workspace')} &nbsp; / &nbsp; <b id="crumb">{getCrumbTitle()}</b>
          </div>

          <div className="topactions">
            <span className="cycle">{t('cycle_demo')}</span>

            {/* Yellow Language Toggle Button matching theme (shown for applicant demo & scrutiny officer demo mode) */}
            {isLangToggleSupported && (
              <button
                className="btn primary"
                style={{
                  minHeight: '38px',
                  padding: '6px 14px',
                  fontSize: '13px',
                  fontWeight: 800,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  borderRadius: '99px',
                  boxShadow: '0 2px 6px rgba(196, 133, 12, 0.25)',
                }}
                onClick={toggleLanguage}
                title={language === 'en' ? 'हिन्दी में बदलें' : 'Switch to English'}
                aria-label="Language Toggle"
              >
                <span style={{ fontSize: '14px' }}>🌐</span>
                <span>{language === 'en' ? 'हिन्दी' : 'English'}</span>
              </button>
            )}

            <button
              className="iconbtn"
              onClick={() => navigate('/notifications')}
              aria-label="Notifications"
              title={language === 'hi' ? 'सूचनाएं' : 'Notifications'}
            >
              ♧{!notificationsRead && <sup>3</sup>}
            </button>

            <button
              className="iconbtn avatar"
              aria-label="Demo profile"
              title="Demo Profile"
              onClick={() => showToast(language === 'hi' ? 'डेमो प्रोफ़ाइल · कोई वास्तविक लॉग-इन नहीं' : 'Demo profile · no production sign-in')}
            >
              SP
            </button>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <div className="content">
          {/* Rolebar */}
          <div className="rolebar">
            <div>
              <strong>{t('demo_workspace')}</strong>
              <small>{t('simulated_switcher')}</small>
            </div>
            <select
              id="role"
              value={role}
              aria-label="Select simulated demo role"
              onChange={(e) => setRole(e.target.value as PortalRole)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Child View */}
          <div id="view">{children}</div>
        </div>

        {/* Footer */}
        <footer className="footer">
          {t('footer_disclaimer')}
        </footer>
      </main>

      {/* Modal Overlay */}
      {dialog?.isOpen && (
        <div className="overlay" role="presentation" onClick={closeDialog}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={dialog.title}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>{dialog.title}</h2>
            {dialog.children}
            <hr className="divider" />
            <div className="buttonrow">
              <button className="btn" onClick={closeDialog}>
                {language === 'hi' ? 'रद्द करें' : 'Cancel'}
              </button>
              {dialog.onConfirm && (
                <button className="btn primary" onClick={dialog.onConfirm}>
                  {dialog.confirmLabel || (language === 'hi' ? 'कार्रवाई की पुष्टि करें' : 'Confirm demo action')}
                </button>
              )}
            </div>
            {dialog.notice && <p className="notice">{dialog.notice}</p>}
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div id="toast" className="toast" role="status">
          {toastMessage}
        </div>
      )}
    </div>
  );
};
