import React from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { DEMO_USERS } from '../../data/mockStore';
import { useStore } from '../../hooks/useStore';
import { toast } from '../common/Toast';
import { Check, ShieldAlert } from 'lucide-react';

interface RoleSwitcherModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RoleSwitcherModal: React.FC<RoleSwitcherModalProps> = ({ isOpen, onClose }) => {
  const { currentUser, store } = useStore();

  const handleSelectRole = (user: typeof DEMO_USERS[0]) => {
    store.setCurrentUser(user);
    toast.show(`Switched demo persona to: ${user.name} (${user.role})`, 'info');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Simulated Demo Persona"
      subtitle="Switch between roles to preview how different stakeholders interact with the workflow."
      footer={
        <Button variant="secondary" onClick={onClose}>
          Done
        </Button>
      }
    >
      <div style={{ marginBottom: '16px' }} className="flow-callout">
        <ShieldAlert size={20} color="var(--accent-active)" style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong>Illustrative Demo Role Selector</strong>
          <p>
            This prototype simulates role permissions for evaluation. It does not replace real
            production authentication or official statutory delegation.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '10px' }}>
        {DEMO_USERS.map((user) => {
          const isSelected = currentUser.id === user.id;
          return (
            <button
              key={user.id}
              type="button"
              onClick={() => handleSelectRole(user)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '12px 16px',
                borderRadius: 'var(--radius-sm)',
                border: isSelected ? '2px solid var(--accent-active)' : '1px solid var(--border)',
                background: isSelected ? 'var(--surface-ivory)' : '#ffffff',
                textAlign: 'left',
                width: '100%',
                cursor: 'pointer',
                transition: 'all var(--motion-fast)',
              }}
            >
              <span className="user-avatar">{user.avatar}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--ink)' }}>
                  {user.name}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--fg-2)', marginTop: '2px' }}>
                  {user.role} · <span style={{ color: 'var(--muted)' }}>{user.designation}</span>
                </div>
              </div>
              {isSelected && <Check size={18} color="var(--accent-active)" />}
            </button>
          );
        })}
      </div>
    </Modal>
  );
};
