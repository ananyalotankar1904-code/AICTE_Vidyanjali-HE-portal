import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Clock,
  AlertTriangle,
  Calendar,
  ShieldAlert,
  ChevronRight,
  TrendingUp,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Skeleton } from '../components/common/Skeleton';
import { useStore } from '../hooks/useStore';
import { apiClient } from '../api/client';
import { WORKFLOW_STAGES, ApplicationRecord, AuditEvent, DashboardSummary } from '../types';
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
  const { currentUser } = useStore();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, appsRes, auditRes] = await Promise.all([
        apiClient.getDashboardSummary(),
        apiClient.getApplications(),
        apiClient.getAuditLogs().catch(() => []),
      ]);
      setSummary(sumRes);
      setApplications(appsRes);
      setAuditLogs(auditRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to connect to unified AICTE backend API.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const counts = {
    total: summary?.totalApplications ?? applications.length,
    pendingScrutiny: summary?.pendingScrutiny ?? applications.filter((a) => a.status === 'Pending scrutiny').length,
    deficiencyCases: summary?.deficiencyCases ?? applications.filter((a) => Boolean(a.deficiency)).length,
    evcsScheduled: summary?.evcsScheduled ?? 0,
    expiringDocs: summary?.expiringDocuments ?? 0,
    upcomingDeadlines: summary?.upcomingDeadlines ?? applications.filter((a) => a.deadline <= '2026-11-09').length,
  };

  // Coordinated gold and warm amber shades for distinguishing data series
  const ageingColors = ['#F4C542', '#E5B530', '#D99A13', '#C4850C', '#A86A03'];

  const ageingData = summary?.ageingBuckets && summary.ageingBuckets.length > 0
    ? summary.ageingBuckets.map((b) => ({ range: b.bucket, count: b.count }))
    : [
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

      {/* Degraded mode warning if Member 4 compliance subsystem is offline */}
      {summary?.degraded && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            backgroundColor: '#FFFBEB',
            border: '1px solid #FDE68A',
            borderRadius: '8px',
            color: '#92400E',
            marginBottom: '20px',
            fontSize: '14px',
          }}
        >
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>Compliance Subsystem Degraded:</strong> Member 4 compliance service is unreachable or returning errors. Core workflow metrics remain active while compliance numbers use fallback defaults.
          </div>
        </div>
      )}

      {/* Honest error display if backend connection fails */}
      {error && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '36px 20px',
            background: '#FFF5F5',
            border: '1px solid #FED7D7',
            borderRadius: '8px',
            marginBottom: '24px',
            textAlign: 'center',
          }}
        >
          <AlertCircle size={36} color="#E53E3E" style={{ marginBottom: '12px' }} />
          <h3 style={{ color: '#C53030', margin: '0 0 8px' }}>Live API Connection Failed</h3>
          <p style={{ color: '#9B2C2C', maxWidth: '520px', fontSize: '14px', margin: '0 0 16px' }}>
            {error}
          </p>
          <Button variant="secondary" onClick={fetchDashboardData} icon={<RefreshCw size={15} />}>
            Retry Backend Connection
          </Button>
        </div>
      )}

      {/* Loading state */}
      {isLoading ? (
        <div style={{ display: 'grid', gap: '20px' }}>
          <div className="metric-grid">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i}>
                <Skeleton lines={2} />
              </Card>
            ))}
          </div>
          <div className="dashboard-grid">
            <Card>
              <Skeleton lines={4} />
            </Card>
            <Card>
              <Skeleton lines={4} />
            </Card>
          </div>
        </div>
      ) : (
        <>
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
                {attentionCases.length === 0 ? (
                  <p style={{ fontSize: '13px', color: 'var(--muted)', padding: '16px 0', textAlign: 'center' }}>
                    No cases currently requiring immediate attention.
                  </p>
                ) : (
                  attentionCases.map((app) => (
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
                  ))
                )}
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
                {recentAudit.length === 0 ? (
                  <p style={{ fontSize: '13px', color: 'var(--muted)', padding: '16px 0', textAlign: 'center' }}>
                    No recent workflow activity recorded.
                  </p>
                ) : (
                  recentAudit.map((log) => (
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
                  ))
                )}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};
