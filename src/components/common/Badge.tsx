import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  tone?: 'blue' | 'green' | 'amber' | 'red' | 'gray';
  statusText?: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, tone, statusText, className = '' }) => {
  // Infer tone if not explicitly provided
  let computedTone: 'blue' | 'green' | 'amber' | 'red' | 'gray' = tone || 'blue';

  const text = (statusText || (typeof children === 'string' ? children : '')).toLowerCase();

  if (!tone && text) {
    if (/approved|completed|valid|verified|success/.test(text)) {
      computedTone = 'green';
    } else if (/deficiency|expired|missing|urgent|rejected/.test(text)) {
      computedTone = 'red';
    } else if (/pending|scheduled|expiring|awaiting|submitted|due/.test(text)) {
      computedTone = 'amber';
    } else {
      computedTone = 'blue';
    }
  }

  return (
    <span className={`badge ${computedTone} ${className}`}>
      {children}
    </span>
  );
};
