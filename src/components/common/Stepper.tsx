import React from 'react';
import { WORKFLOW_STAGES, WorkflowStage } from '../../types';

interface StepperProps {
  currentStageIndex: number;
  stages?: readonly WorkflowStage[];
}

export const Stepper: React.FC<StepperProps> = ({
  currentStageIndex,
  stages = WORKFLOW_STAGES,
}) => {
  return (
    <div className="stepper-container" role="progressbar" aria-valuenow={currentStageIndex} aria-valuemin={0} aria-valuemax={stages.length - 1}>
      {stages.map((stage, index) => {
        let statusClass = '';
        let ariaStatus = 'Upcoming';

        if (index < currentStageIndex) {
          statusClass = 'done';
          ariaStatus = 'Completed';
        } else if (index === currentStageIndex) {
          statusClass = 'current';
          ariaStatus = 'Current stage';
        }

        return (
          <div
            key={stage}
            className={`step-node ${statusClass}`}
            aria-label={`${stage}: ${ariaStatus}`}
          >
            {stage}
          </div>
        );
      })}
    </div>
  );
};
