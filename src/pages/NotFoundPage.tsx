import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FileQuestion } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{ textAlign: 'center', padding: '80px 20px' }}>
      <FileQuestion size={56} color="var(--accent-active)" style={{ marginBottom: '16px' }} />
      <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--ink)' }}>Page Not Found</h1>
      <p style={{ color: 'var(--muted)', marginTop: '8px', maxWidth: '45ch', margin: '8px auto 24px' }}>
        The workflow resource or page you requested does not exist in the AICTE_Vidyanjali-HE-portal workspace.
      </p>
      <Button variant="primary" onClick={() => navigate('/')}>
        Return to Overview
      </Button>
    </div>
  );
};
