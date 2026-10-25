import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { RoleSwitcherModal } from './RoleSwitcherModal';
import { ToastContainer } from '../common/Toast';
import { Info } from 'lucide-react';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar onOpenRoleModal={() => setIsRoleModalOpen(true)} />

      <div className="app-main">
        <Topbar onOpenRoleModal={() => setIsRoleModalOpen(true)} />

        <main className="app-content" id="main-content">
          {children}

          <div className="footer-disclaimer-note">
            <Info size={14} />
            <span>
              AICTE_Vidyanjali-HE-portal · Smart India Hackathon (SIH26262) · Synthetic demonstration records only.
              No official AICTE production database or legal decisions are connected.
            </span>
          </div>
        </main>
      </div>

      <RoleSwitcherModal
        isOpen={isRoleModalOpen}
        onClose={() => setIsRoleModalOpen(false)}
      />

      <ToastContainer />
    </div>
  );
};
