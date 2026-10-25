import { NotificationItem } from '../types';

export const seedNotes: NotificationItem[] = [
  {
    id: 'N-1',
    kind: 'Deficiency alert',
    title: 'Response due in 3 days',
    body: 'Sahyadri College of Engineering needs to address two document deficiencies.',
    time: '25 Oct · 09:40',
    read: false,
    app: 'AI-2026-1826',
  },
  {
    id: 'N-2',
    kind: 'Deadline reminder',
    title: 'Fire safety NOC has expired',
    body: 'Bhopal Institute of Management needs a renewed certificate.',
    time: '24 Oct · 16:15',
    read: false,
    app: 'AI-2026-1675',
  },
  {
    id: 'N-3',
    kind: 'EVC reminder',
    title: 'Inspection scheduled for 7 Nov',
    body: 'Chennai Technical University is ready for the committee visit.',
    time: '24 Oct · 10:05',
    read: false,
    app: 'AI-2026-1794',
  },
  {
    id: 'N-4',
    kind: 'Escalation',
    title: 'Decision awaiting executive review',
    body: 'Ahmedabad Institute of Design has been in decision review for 8 days.',
    time: '23 Oct · 14:30',
    read: true,
    app: 'AI-2026-1778',
  },
];
