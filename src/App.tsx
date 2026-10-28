import React from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { PortalProvider } from './context/PortalContext';
import { AppShell } from './components/layout/AppShell';

import { DashboardPage } from './pages/DashboardPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { CasePage } from './pages/CasePage';
import { SchedulePage } from './pages/SchedulePage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DeficienciesPage } from './pages/DeficienciesPage';
import { NotificationsPage } from './pages/NotificationsPage';
import { AuditPage } from './pages/AuditPage';
import { EvcPage } from './pages/EvcPage';
import { GuidePage } from './pages/GuidePage';
import { NewApplicationPage } from './pages/NewApplicationPage';
import { BpmnPage } from './pages/BpmnPage';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div>
      <div className="pagehead">
        <div>
          <div className="eyebrow">AICTE APPROVAL &amp; COMPLIANCE</div>
          <h1>Page not found</h1>
          <p>The requested page is not available in this prototype.</p>
        </div>
        <button className="btn primary" onClick={() => navigate('/')}>
          Return to dashboard
        </button>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <PortalProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/applications/new" element={<NewApplicationPage />} />
            <Route path="/applications/:id" element={<CasePage />} />
            <Route path="/case" element={<CasePage />} />
            <Route path="/schedule" element={<SchedulePage officerMode={false} />} />
            <Route path="/scheduling" element={<SchedulePage officerMode={true} />} />
            <Route path="/documents" element={<DocumentsPage complianceMode={false} />} />
            <Route path="/compliance" element={<DocumentsPage complianceMode={true} />} />
            <Route path="/deficiencies" element={<DeficienciesPage />} />
            <Route path="/evc" element={<EvcPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/guide" element={<GuidePage />} />
            <Route path="/workflow" element={<BpmnPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </PortalProvider>
  );
};

export default App;
