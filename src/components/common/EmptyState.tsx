import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="empty-box" role="status">
      <div style={{ color: 'var(--meta)', display: 'grid', placeItems: 'center', marginBottom: '8px' }}>
        {icon || <Inbox size={42} strokeWidth={1.5} />}
      </div>
      <h3>{title}</h3>
      <p>{description}</p>
      {actionText && onAction && (
        <div style={{ marginTop: '16px' }}>
          <Button variant="secondary" onClick={onAction}>
            {actionText}
          </Button>
        </div>
      )}
    </div>
  );
};
