import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Download,
  Search,
  ChevronRight,
  ShieldCheck,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { toast } from '../components/common/Toast';
import { apiClient } from '../api/client';
import { AuditEvent } from '../types';

export const AuditHistoryPage: React.FC = () => {
  const navigate = useNavigate();

  const [auditLogs, setAuditLogs] = useState<AuditEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState('All');

  const loadAuditLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const logs = await apiClient.getAuditLogs();
      setAuditLogs(logs);
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve audit trail from unified gateway');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const filteredLogs = auditLogs.filter((log) => {
    if (actionFilter !== 'All' && log.action !== actionFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        log.actor.toLowerCase().includes(q) ||
        log.app.toLowerCase().includes(q) ||
        log.action.toLowerCase().includes(q) ||
        log.reason.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const distinctActions = Array.from(new Set(auditLogs.map((l) => l.action)));

  const handleExportCsv = () => {
    if (filteredLogs.length === 0) return;

    const headers = ['Timestamp', 'Actor', 'Action', 'Application ID', 'Previous State', 'New State', 'Reason'];
    const rows = filteredLogs.map((l) => [
      l.at,
      l.actor,
      l.action,
      l.app,
      l.before,
      l.after,
      `"${l.reason.replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `aicte_audit_trail_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);

    toast.show(`Exported ${filteredLogs.length} audit records to CSV.`, 'success');
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Traceable Governance</div>
          <h1 className="page-title">Regulatory Audit Trail</h1>
          <p className="page-subtitle">
            An append-only, tamper-evident record of all operational actions, deficiency issuances,
            stage advancements, and official decisions.
          </p>
        </div>

        <div className="head-actions">
          <Button
            variant="secondary"
            onClick={loadAuditLogs}
            icon={<RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />}
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            onClick={handleExportCsv}
            disabled={filteredLogs.length === 0}
            icon={<Download size={15} />}
          >
            Export Visible Events ({filteredLogs.length})
          </Button>
        </div>
      </div>

      {/* Filter and Search Toolbar */}
      <div className="toolbar">
        <div className="form-field search">
          <label htmlFor="audit-search">Search audit events</label>
          <div style={{ position: 'relative' }}>
            <input
              id="audit-search"
              type="search"
              placeholder="Filter by actor, application ID, or reason…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '34px' }}
            />
            <Search
              size={16}
              color="var(--muted)"
              style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
            />
          </div>
        </div>

        <div className="form-field" style={{ minWidth: '220px' }}>
          <label htmlFor="action-filter">Action Type</label>
          <select
            id="action-filter"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="All">All recorded actions</option>
            {distinctActions.map((act) => (
              <option key={act} value={act}>
                {act}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Audit Log Card */}
      <Card>
        <CardHeader
          title="Chronological Audit Log"
          subtitle={`Displaying ${filteredLogs.length} verified events`}
          action={
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                fontSize: '11px',
                fontWeight: 650,
                color: 'var(--green-ink)',
                background: 'var(--green-bg)',
                border: '1px solid var(--green-border)',
                padding: '3px 8px',
                borderRadius: '4px',
              }}
            >
              <ShieldCheck size={13} /> Append-Only Immutable Log
            </span>
          }
        />

        {isLoading ? (
          <Skeleton lines={5} />
        ) : error ? (
          <EmptyState
            title="Audit trail could not be retrieved"
            description={error}
            actionText="Retry Connection"
            onAction={loadAuditLogs}
            icon={<AlertCircle size={44} color="#dc2626" />}
          />
        ) : auditLogs.length === 0 ? (
          <EmptyState
            title="No audit events recorded"
            description="No operational or regulatory actions have been logged yet in the unified backend database."
          />
        ) : filteredLogs.length === 0 ? (
          <EmptyState
            title="No audit events matched"
            description="Try modifying search keywords or resetting the action filter."
            actionText="Clear Filters"
            onAction={() => {
              setSearchQuery('');
              setActionFilter('All');
            }}
          />
        ) : (
          <div className="audit-timeline" style={{ marginTop: '12px' }}>
            {filteredLogs.map((event) => (
              <article key={event.id} className="audit-event-item">
                <div className="audit-timestamp">{event.at}</div>
                <div className="audit-content">
                  <strong>{event.action}</strong>
                  <p>
                    Actor: <b>{event.actor}</b> · Target:{' '}
                    <button
                      type="button"
                      className="button ghost"
                      style={{ padding: 0, minHeight: 'auto', display: 'inline', fontWeight: 650 }}
                      onClick={() => {
                        if (event.app && event.app !== 'GLOBAL') {
                          navigate(`/applications/${event.app}`);
                        }
                      }}
                    >
                      {event.app}
                    </button>
                  </p>

                  <div className="state-transition-pill">
                    <span className="state-pill">{event.before}</span>
                    <ChevronRight size={13} color="var(--muted)" />
                    <span className="state-pill" style={{ fontWeight: 700, color: 'var(--ink)' }}>
                      {event.after}
                    </span>
                  </div>

                  <p style={{ marginTop: '6px', fontSize: '13px', color: 'var(--fg-2)' }}>
                    <b>Reason:</b> {event.reason}
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
