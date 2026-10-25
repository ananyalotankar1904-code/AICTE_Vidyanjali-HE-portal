import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  RefreshCw,
  Send,
  AlertCircle,
  Eye,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Skeleton } from '../components/common/Skeleton';
import { EmptyState } from '../components/common/EmptyState';
import { toast } from '../components/common/Toast';
import { useStore } from '../hooks/useStore';
import { WORKFLOW_STAGES, FilterView, ApplicationRecord } from '../types';

export const ApplicationsListPage: React.FC = () => {
  const navigate = useNavigate();
  const { applications, store } = useStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sortBy, setSortBy] = useState<'Deadline' | 'Institution' | 'Oldest'>('Deadline');
  const [activeView, setActiveView] = useState<FilterView>('All applications');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 5;

  // Prototype loading and error simulation states
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Filter logic
  const filteredRows = useMemo(() => {
    let rows: ApplicationRecord[] = [...applications];

    // 1. Saved view filters
    if (activeView === 'My queue') {
      rows = rows.filter((a) => a.owner === 'Ananya Rao' || a.owner === 'R. Menon');
    } else if (activeView === 'At risk') {
      rows = rows.filter((a) => Boolean(a.deficiency) || a.deadline <= '2026-11-04');
    } else if (activeView === 'EVC pipeline') {
      rows = rows.filter((a) => a.stage === 3);
    }

    // 2. Status filter
    if (statusFilter !== 'All') {
      rows = rows.filter((a) => a.status === statusFilter);
    }

    // 3. Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      rows = rows.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.id.toLowerCase().includes(q) ||
          a.city.toLowerCase().includes(q) ||
          a.type.toLowerCase().includes(q)
      );
    }

    // 4. Sorting
    rows.sort((a, b) => {
      if (sortBy === 'Institution') return a.name.localeCompare(b.name);
      if (sortBy === 'Oldest') return b.age - a.age;
      return a.deadline.localeCompare(b.deadline);
    });

    return rows;
  }, [applications, activeView, statusFilter, searchQuery, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const displayedRows = filteredRows.slice(
    (safeCurrentPage - 1) * pageSize,
    safeCurrentPage * pageSize
  );

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const newSet = new Set(selectedIds);
      displayedRows.forEach((r) => newSet.add(r.id));
      setSelectedIds(newSet);
    } else {
      const newSet = new Set(selectedIds);
      displayedRows.forEach((r) => newSet.delete(r.id));
      setSelectedIds(newSet);
    }
  };

  const handleToggleRow = (id: string) => {
    const newSet = new Set(selectedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedIds(newSet);
  };

  const handleBulkReminder = () => {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    ids.forEach((id) => {
      store.addAuditLog(
        'Sent bulk reminder',
        id,
        'Not sent',
        'Sent',
        'Bulk reminder dispatched from Applications Registry.'
      );
    });
    setSelectedIds(new Set());
    toast.show(
      `Dispatched deadline reminders to ${ids.length} selected institution${
        ids.length > 1 ? 's' : ''
      }.`,
      'success'
    );
  };

  const handleSimulateLoading = () => {
    setIsLoading(true);
    setHasError(false);
    setTimeout(() => {
      setIsLoading(false);
      toast.show('Applications refreshed successfully.', 'info');
    }, 800);
  };

  const handleSimulateError = () => {
    setHasError(true);
    setIsLoading(false);
  };

  const handleRetry = () => {
    setHasError(false);
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      toast.show('Applications recovered.', 'success');
    }, 700);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('All');
    setSortBy('Deadline');
    setActiveView('All applications');
    setCurrentPage(1);
    toast.show('Filter criteria reset.', 'info');
  };

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
          <div className="eyebrow">Application Registry</div>
          <h1 className="page-title">Applications</h1>
          <p className="page-subtitle">
            Search the institutional approval portfolio, focus your active queue, and inspect detailed
            workflow timelines.
          </p>
        </div>
        <div className="head-actions">
          <Button
            variant="secondary"
            onClick={handleSimulateLoading}
            icon={<RefreshCw size={14} />}
          >
            Show Loading
          </Button>
          <Button
            variant="secondary"
            onClick={handleSimulateError}
            icon={<AlertCircle size={14} />}
          >
            Simulate Error
          </Button>
          <Button
            onClick={() => navigate('/applications/new')}
            icon={<Plus size={16} />}
          >
            New Application
          </Button>
        </div>
      </div>

      {/* Saved View Chips */}
      <div className="saved-views" role="group" aria-label="Saved views">
        {(['All applications', 'My queue', 'At risk', 'EVC pipeline'] as FilterView[]).map(
          (view) => (
            <button
              key={view}
              type="button"
              className={`view-chip ${activeView === view ? 'selected' : ''}`}
              onClick={() => {
                setActiveView(view);
                setCurrentPage(1);
              }}
              aria-pressed={activeView === view}
            >
              {view}
            </button>
          )
        )}
      </div>

      {/* Filter and Search Toolbar */}
      <div className="toolbar">
        <div className="form-field search">
          <label htmlFor="app-search-input">Search applications</label>
          <div style={{ position: 'relative' }}>
            <input
              id="app-search-input"
              type="search"
              placeholder="Search by Institution, ID, or City…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              style={{ paddingLeft: '34px' }}
            />
            <Search
              size={16}
              color="var(--muted)"
              style={{ position: 'absolute', left: 10, top: 12, pointerEvents: 'none' }}
            />
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="status-select">Status</label>
          <select
            id="status-select"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="All">All statuses</option>
            {Array.from(new Set(applications.map((a) => a.status))).map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>

        <div className="form-field">
          <label htmlFor="sort-select">Sort by</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="Deadline">Target Deadline</option>
            <option value="Institution">Institution Name</option>
            <option value="Oldest">Ageing (Oldest First)</option>
          </select>
        </div>
      </div>

      {/* Main Content Table Card */}
      <Card padded={false}>
        {isLoading ? (
          <Skeleton lines={5} />
        ) : hasError ? (
          <EmptyState
            title="Applications could not be loaded"
            description="A temporary error occurred while retrieving application records in the prototype. Retry to restore data."
            actionText="Retry Request"
            onAction={handleRetry}
            icon={<AlertCircle size={44} color="#dc2626" />}
          />
        ) : filteredRows.length === 0 ? (
          <EmptyState
            title="No applications match these filters"
            description="Try modifying your search terms, changing the active view, or clearing filters."
            actionText="Clear Filters"
            onAction={handleClearFilters}
          />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: 40 }}>
                      <input
                        type="checkbox"
                        checked={
                          displayedRows.length > 0 &&
                          displayedRows.every((r) => selectedIds.has(r.id))
                        }
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        aria-label="Select all visible applications"
                        style={{ cursor: 'pointer' }}
                      />
                    </th>
                    <th>Institution / Application ID</th>
                    <th>Application Type</th>
                    <th>Status</th>
                    <th>Current Stage</th>
                    <th>Responsible Owner</th>
                    <th>Deadline</th>
                    <th style={{ textAlign: 'right' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {displayedRows.map((app) => (
                    <tr key={app.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(app.id)}
                          onChange={() => handleToggleRow(app.id)}
                          aria-label={`Select ${app.name}`}
                          style={{ cursor: 'pointer' }}
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          className="table-institution"
                          onClick={() => navigate(`/applications/${app.id}`)}
                        >
                          {app.name}
                        </button>
                        <span className="table-sub">
                          {app.id} · {app.city}
                        </span>
                      </td>
                      <td>{app.type}</td>
                      <td>
                        <Badge statusText={app.status}>{app.status}</Badge>
                      </td>
                      <td>{WORKFLOW_STAGES[app.stage]}</td>
                      <td>{app.owner}</td>
                      <td style={{ whiteSpace: 'nowrap' }}>{formatDate(app.deadline)}</td>
                      <td style={{ textAlign: 'right' }}>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/applications/${app.id}`)}
                          icon={<Eye size={14} />}
                        >
                          Inspect
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Table Tools (Bulk Actions) */}
            <div className="table-tools">
              <span>
                <b>{selectedIds.size}</b> selected · <b>{filteredRows.length}</b> total matches
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleBulkReminder}
                disabled={selectedIds.size === 0}
                icon={<Send size={13} />}
              >
                Send Reminder to Selected ({selectedIds.size})
              </Button>
            </div>

            {/* Pagination Controls */}
            <div className="table-pagination">
              <span>
                Showing {(safeCurrentPage - 1) * pageSize + 1}–
                {Math.min(safeCurrentPage * pageSize, filteredRows.length)} of {filteredRows.length}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={safeCurrentPage === 1}
                >
                  Previous
                </Button>
                <span>
                  Page {safeCurrentPage} of {totalPages}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safeCurrentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
};
