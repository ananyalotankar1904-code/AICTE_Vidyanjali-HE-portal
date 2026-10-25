import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Clock,
  AlertTriangle,
  Calendar,
  ShieldAlert,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { useStore } from '../hooks/useStore';
import { WORKFLOW_STAGES } from '../types';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { applications, documents, evcs, auditLogs, currentUser } = useStore();

  const counts = {
    total: applications.length,
    pendingScrutiny: applications.filter((a) => a.status === 'Pending scrutiny').length,
    deficiencyCases: applications.filter((a) => Boolean(a.deficiency)).length,
    evcsScheduled: evcs.filter((e) => e.status === 'Scheduled').length,
    expiringDocs: documents.filter((d) => ['Expiring soon', 'Expired'].includes(d.status)).length,
    upcomingDeadlines: applications.filter((a) => a.deadline <= '2026-11-09').length,
  };

  // Coordinated gold and warm amber shades for distinguishing data series
  const ageingColors = ['#F4C542', '#E5B530', '#D99A13', '#C4850C', '#A86A03'];

  const ageingData = [
    { range: '0–15 days', count: applications.filter((a) => a.age <= 15).length },
    { range: '16–30 days', count: applications.filter((a) => a.age > 15 && a.age <= 30).length },
    { range: '31–45 days', count: applications.filter((a) => a.age > 30 && a.age <= 45).length },
    { range: '46–60 days', count: applications.filter((a) => a.age > 45 && a.age <= 60).length },
    { range: '60+ days', count: applications.filter((a) => a.age > 60).length },
  ];

  const attentionCases = applications
    .filter((a) => Boolean(a.deficiency) || a.status === 'Pending scrutiny')
    .slice(0, 4);

  const recentAudit = auditLogs.slice(0, 5);

  const formatDate = (dateStr: string) => {
    if (dateStr === '—') return '—';
    try {
      return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Approval Command Centre</div>
          <h1 className="page-title">Welcome back, {currentUser.name}</h1>
          <p className="page-subtitle">
            A clear operational overview of what is progressing, who acts next, and where compliance
            may require scrutiny in AICTE_Vidyanjali-HE-portal.
          </p>
        </div>
        <div className="head-actions">
          <Button
            onClick={() => navigate('/applications/new')}
            variant="secondary"
          >
            Start New Intake
          </Button>
          <Button
            onClick={() => navigate('/applications')}
            icon={<ChevronRight size={16} />}
            iconPosition="right"
          >
            Review Applications
          </Button>
        </div>
      </div>

      {/* Metric Cards Grid — Pure White Cards with Golden/Warm Accents */}
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Total Applications</span>
            <span className="metric-icon-wrap">
              <FileText size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.total}</div>
            <div className="metric-footer">Across 2026–27 approval cycle</div>
          </div>
        </div>

        <div className="metric-card warn">
          <div className="metric-top">
            <span className="metric-label">Pending Scrutiny</span>
            <span className="metric-icon-wrap">
              <Clock size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.pendingScrutiny}</div>
            <div className="metric-footer">Officer review action required</div>
          </div>
        </div>

        <div className="metric-card danger">
          <div className="metric-top">
            <span className="metric-label">Deficiency Cases</span>
            <span className="metric-icon-wrap">
              <AlertTriangle size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.deficiencyCases}</div>
            <div className="metric-footer">Institution response awaiting</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">EVCs Scheduled</span>
            <span className="metric-icon-wrap">
              <Calendar size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.evcsScheduled}</div>
            <div className="metric-footer">Upcoming inspections</div>
          </div>
        </div>

        <div className="metric-card warn">
          <div className="metric-top">
            <span className="metric-label">Expiring Documents</span>
            <span className="metric-icon-wrap">
              <ShieldAlert size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.expiringDocs}</div>
            <div className="metric-footer">Expired or expiring within 30 days</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-top">
            <span className="metric-label">Upcoming Deadlines</span>
            <span className="metric-icon-wrap">
              <TrendingUp size={17} />
            </span>
          </div>
          <div>
            <div className="metric-value">{counts.upcomingDeadlines}</div>
            <div className="metric-footer">Due within the next 15 days</div>
          </div>
        </div>
      </div>

      {/* Analytical Charts — Coordinated Gold & Warm Amber Series */}
      <div className="dashboard-grid">
        <Card>
          <CardHeader
            title="Application Ageing Distribution"
            subtitle="Days elapsed since initial submission across active portfolio"
          />
          <div style={{ width: '100%', height: 210, marginTop: 10 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ageingData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="range" tick={{ fontSize: 12, fill: '#867761' }} axisLine={{ stroke: '#E8DFC9' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: '#867761' }} axisLine={{ stroke: '#E8DFC9' }} />
                <Tooltip
                  cursor={{ fill: 'rgba(244, 197, 66, 0.08)' }}
                  contentStyle={{
                    borderRadius: '8px',
                    borderColor: '#E8DFC9',
                    background: '#FFFFFF',
                    color: '#514332',
                    fontSize: '13px',
                    boxShadow: '0 4px 12px rgba(81, 67, 50, 0.08)',
                  }}
                  formatter={(value: any) => [`${value} Applications`, 'Count']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {ageingData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={ageingColors[index % ageingColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Stage Distribution"
            subtitle="Where active applications stand today"
          />
          <div className="stage-rows" style={{ marginTop: 12 }}>
            {WORKFLOW_STAGES.slice(0, 5).map((stage, idx) => {
              const count = applications.filter((a) => a.stage === idx).length;
              const percentage = applications.length ? Math.round((count / applications.length) * 100) : 0;
              return (
                <div key={stage} className="stage-row">
                  <span style={{ color: 'var(--ink)' }}>{stage}</span>
                  <div className="stage-track">
                    <div
                      className="stage-fill"
                      style={{ width: `${percentage}%` }}
                      title={`${percentage}% of total`}
                    />
                  </div>
                  <b style={{ textAlign: 'right', color: 'var(--ink)' }}>{count}</b>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Lower Split: Attention & Activity */}
      <div className="split-lower">
        <Card>
          <CardHeader
            title="Requires Attention"
            subtitle="Cases with active deficiencies or pending scrutiny"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/applications')}
                icon={<ChevronRight size={14} />}
                iconPosition="right"
              >
                View all
              </Button>
            }
          />

          <div style={{ display: 'grid', gap: '8px' }}>
            {attentionCases.map((app) => (
              <div
                key={app.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '14px',
                  padding: '12px 0',
                  borderTop: '1px solid var(--border-soft)',
                }}
              >
                <div>
                  <button
                    type="button"
                    className="table-institution"
                    onClick={() => navigate(`/applications/${app.id}`)}
                  >
                    {app.name}
                  </button>
                  <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
                    {app.owner} acts next · Target due {formatDate(app.deadline)}
                  </div>
                </div>
                <Badge statusText={app.status}>{app.status}</Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Recent Activity"
            subtitle="Audited workflow state transitions"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/audit')}
                icon={<ChevronRight size={14} />}
                iconPosition="right"
              >
                Full audit
              </Button>
            }
          />

          <div className="audit-timeline">
            {recentAudit.map((log) => (
              <div
                key={log.id}
                style={{
                  position: 'relative',
                  padding: '0 0 16px 20px',
                  borderLeft: '1px solid var(--border)',
                  marginLeft: '7px',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    left: '-5px',
                    top: '4px',
                    width: '9px',
                    height: '9px',
                    background: 'var(--accent-active)',
                    border: '2px solid white',
                    borderRadius: '50%',
                    boxShadow: '0 0 0 1px var(--accent-border)',
                  }}
                />
                <strong style={{ display: 'block', fontSize: '13px', lineHeight: 1.4 }}>
                  {log.action} ·{' '}
                  <span style={{ color: 'var(--accent-active)' }}>{log.app}</span>
                </strong>
                <p style={{ fontSize: '12px', color: 'var(--muted)', margin: '2px 0 0' }}>
                  {log.actor} · {log.at}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
