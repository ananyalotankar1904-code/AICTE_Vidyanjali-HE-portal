import React, { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { usePortal, ROLES, PortalRole } from '../../context/PortalContext';

interface AppShellProps {
  children: React.ReactNode;
}

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

  const applicantNav = [
    { to: '/', label: language === 'hi' ? 'मेरा डैशबोर्ड' : 'My Dashboard', icon: '⌂' },
    { to: '/applications', label: language === 'hi' ? 'मेरे आवेदन' : 'My Applications', icon: '▤' },
    { to: '/schedule', label: language === 'hi' ? 'मेरी समय-सारणी' : 'My Schedule', icon: '▦' },
    { to: '/documents', label: language === 'hi' ? 'दस्तावेज़ एवं तत्परता' : 'Documents & Readiness', icon: '▧' },
    { to: '/deficiencies', label: language === 'hi' ? 'कमियां एवं प्रत्युत्तर' : 'Deficiencies & Responses', icon: '⚑' },
    { to: '/notifications', label: language === 'hi' ? 'सूचनाएं' : 'Notifications', icon: '♧' },
    { to: '/guide', label: language === 'hi' ? 'प्रक्रिया मार्गदर्शिका' : 'Help / Process Guide', icon: 'ⓘ' },
  ];

  const officerNav = [
    { to: '/', label: language === 'hi' ? 'डैशबोर्ड' : 'Dashboard', icon: '⌂' },
    { to: '/applications', label: language === 'hi' ? 'आवेदन' : 'Applications', icon: '▤' },
    { to: '/scheduling', label: language === 'hi' ? 'समय-निर्धारण' : 'Scheduling', icon: '▦' },
    { to: '/documents', label: language === 'hi' ? 'दस्तावेज़ संवीक्षा' : 'Document Readiness', icon: '▧' },
    { to: '/deficiencies', label: language === 'hi' ? 'कमियां (त्रुटियां)' : 'Deficiencies', icon: '⚑' },
    { to: '/evc', label: 'EVC Management', icon: '◇' },
    { to: '/compliance', label: 'Compliance', icon: '▣' },
    { to: '/notifications', label: language === 'hi' ? 'सूचनाएं' : 'Notifications', icon: '♧' },
    { to: '/audit', label: language === 'hi' ? 'लेखा परीक्षा इतिहास' : 'Audit History', icon: '◷' },
    { to: '/guide', label: language === 'hi' ? 'मार्गदर्शिका' : 'Process Guide', icon: 'ⓘ' },
    { to: '/workflow', label: 'Workflow / BPMN', icon: '⚙' },
  ];

  const navItems = isApplicant ? applicantNav : officerNav;

  // Resolve breadcrumb title
  const getCrumbTitle = () => {
    const path = location.pathname;
    if (path === '/') return isApplicant ? (language === 'hi' ? 'मेरा डैशबोर्ड' : 'My Dashboard') : (language === 'hi' ? 'डैशबोर्ड' : 'Dashboard');
    if (path.startsWith('/applications/new')) return language === 'hi' ? 'नया आवेदन' : 'New Application';
    if (path.startsWith('/applications/') || path === '/case') return language === 'hi' ? 'मामला फ़ाइल' : 'Case File';
    if (path.startsWith('/applications')) return language === 'hi' ? 'आवेदन' : 'Applications';
    if (path.startsWith('/schedule') || path.startsWith('/scheduling')) return isApplicant ? (language === 'hi' ? 'मेरी समय-सारणी' : 'My Schedule') : (language === 'hi' ? 'समय-निर्धारण' : 'Scheduling');
    if (path.startsWith('/documents')) return isApplicant ? (language === 'hi' ? 'दस्तावेज़ तत्परता' : 'Documents & Readiness') : (language === 'hi' ? 'दस्तावेज़ संवीक्षा' : 'Document Readiness');
    if (path.startsWith('/compliance')) return 'Compliance & Undertakings';
    if (path.startsWith('/deficiencies')) return language === 'hi' ? 'कमियां एवं प्रत्युत्तर' : 'Deficiencies & Responses';
    if (path.startsWith('/evc')) return 'EVC Management';
    if (path.startsWith('/notifications')) return language === 'hi' ? 'सूचनाएं एवं समय-सीमाएं' : 'Notifications & Deadlines';
    if (path.startsWith('/audit')) return language === 'hi' ? 'लेखा परीक्षा इतिहास' : 'Audit History';
    if (path.startsWith('/guide')) return language === 'hi' ? 'प्रक्रिया मार्गदर्शिका' : 'Process Guide';
    if (path.startsWith('/workflow')) return 'BPMN Workflow Showcase';
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
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'active' : '')}
              onClick={() => setMobileMenuOpen(false)}
            >
              <span className="ico" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
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
