import React from 'react';

interface SkeletonProps {
  lines?: number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ lines = 4, className = '' }) => {
  return (
    <div className={`card-pad ${className}`} aria-busy="true" aria-label="Loading content">
      <div className="skeleton wide" />
      <div className="skeleton medium" />
      <div className="skeleton wide" />
      {lines > 3 && <div className="skeleton short" />}
    </div>
  );
};
