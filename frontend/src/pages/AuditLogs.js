import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Filter } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    action_type: '',
    limit: 100
  });

  useEffect(() => {
    fetchLogs();
  }, [filter]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('limit', filter.limit);
      if (filter.action_type) {
        params.append('action_type', filter.action_type);
      }

      const response = await axios.get(`${API}/audit-logs?${params.toString()}`);
      setLogs(response.data);
    } catch (error) {
      toast.error('Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (actionType) => {
    const colors = {
      task_created: 'bg-green-100 text-green-700',
      task_updated: 'bg-blue-100 text-blue-700',
      status_changed: 'bg-yellow-100 text-yellow-700',
      file_uploaded: 'bg-purple-100 text-purple-700',
      comment_added: 'bg-indigo-100 text-indigo-700',
      user_created: 'bg-pink-100 text-pink-700'
    };
    return colors[actionType] || 'bg-gray-100 text-gray-700';
  };

  const formatMetadata = (metadata) => {
    if (!metadata || Object.keys(metadata).length === 0) return 'N/A';
    
    return Object.entries(metadata).map(([key, value]) => (
      <span key={key} className="text-xs">
        <strong>{key}:</strong> {JSON.stringify(value)}
      </span>
    )).reduce((prev, curr) => [prev, ', ', curr]);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="audit-logs-page">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Shield size={32} className="text-primary" />
          <h2 className="text-3xl font-heading font-bold text-text-primary">Audit Logs</h2>
        </div>
        <p className="text-text-secondary">System activity and change history</p>
      </div>

      {/* Filters */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4">
        <div className="flex items-center gap-4">
          <Filter size={20} className="text-text-secondary" />
          <select
            value={filter.action_type}
            onChange={(e) => setFilter({ ...filter, action_type: e.target.value })}
            className="px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            data-testid="action-type-filter"
          >
            <option value="">All Actions</option>
            <option value="task_created">Task Created</option>
            <option value="task_updated">Task Updated</option>
            <option value="status_changed">Status Changed</option>
            <option value="file_uploaded">File Uploaded</option>
            <option value="comment_added">Comment Added</option>
            <option value="user_created">User Created</option>
          </select>

          <select
            value={filter.limit}
            onChange={(e) => setFilter({ ...filter, limit: parseInt(e.target.value) })}
            className="px-4 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="50">50 logs</option>
            <option value="100">100 logs</option>
            <option value="200">200 logs</option>
            <option value="500">500 logs</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Timestamp</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Action</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">User</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-text-primary">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center py-8 text-text-secondary">
                    No audit logs found
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 transition-colors" data-testid={`log-${log.id}`}>
                    <td className="px-6 py-4 text-sm text-text-secondary">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${getActionColor(log.action_type)}`}>
                        {log.action_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-text-primary">{log.user_name}</p>
                        <p className="text-xs text-text-secondary">{log.user_email}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-text-secondary max-w-md">
                      <div className="space-y-1">
                        {log.task_id && (
                          <p className="text-xs">
                            <strong>Task ID:</strong> {log.task_id.substring(0, 8)}...
                          </p>
                        )}
                        {formatMetadata(log.metadata)}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <p className="text-sm text-text-secondary">
          Showing {logs.length} audit log entries
        </p>
      </div>
    </div>
  );
};

export default AuditLogs;