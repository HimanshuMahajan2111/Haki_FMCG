 
import React, { useState } from 'react';
import { useWorkflows } from '../hooks/useRFPApi';
import { RefreshCw, Search, Filter, Eye, Download } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function WorkflowDashboard() {
  const [filters, setFilters] = useState({
    status: '',
    customer_id: '',
    limit: 20,
    skip: 0
  });

  const { workflows, isLoading, error, refetch } = useWorkflows(filters);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, skip: 0 }));
  };

  const handlePageChange = (direction) => {
    setFilters(prev => ({
      ...prev,
      skip: direction === 'next' ? prev.skip + prev.limit : Math.max(0, prev.skip - prev.limit)
    }));
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">RFP Workflows</h1>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium">Filters:</span>
          </div>

          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          <input
            type="text"
            placeholder="Customer ID"
            value={filters.customer_id}
            onChange={(e) => handleFilterChange('customer_id', e.target.value)}
            className="px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={filters.limit}
            onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
            className="px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          >
            <option value="10">10 per page</option>
            <option value="20">20 per page</option>
            <option value="50">50 per page</option>
          </select>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">Error loading workflows: {error.message}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center items-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      )}

      {/* Workflows List */}
      {!isLoading && workflows.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No workflows found</p>
        </div>
      )}

      {!isLoading && workflows.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Workflow ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  RFP ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Stage
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Duration
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {workflows.map((workflow) => (
                <WorkflowRow key={workflow.workflow_id} workflow={workflow} />
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="bg-gray-50 px-6 py-3 flex justify-between items-center border-t">
            <button
              onClick={() => handlePageChange('prev')}
              disabled={filters.skip === 0}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Showing {filters.skip + 1} - {filters.skip + workflows.length}
            </span>
            <button
              onClick={() => handlePageChange('next')}
              disabled={workflows.length < filters.limit}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Workflow Row Component
function WorkflowRow({ workflow }) {
  const statusColors = {
    submitted: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800'
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-6 py-4 text-sm font-mono text-gray-900">
        {workflow.workflow_id?.substring(0, 8)}...
      </td>
      <td className="px-6 py-4 text-sm text-gray-900">{workflow.rfp_id}</td>
      <td className="px-6 py-4 text-sm text-gray-900">{workflow.customer_id}</td>
      <td className="px-6 py-4">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[workflow.status] || 'bg-gray-100 text-gray-800'}`}>
          {workflow.status}
        </span>
      </td>
      <td className="px-6 py-4 text-sm text-gray-600">{workflow.current_stage}</td>
      <td className="px-6 py-4 text-sm text-gray-600">
        {formatDuration(workflow.duration_seconds)}
      </td>
      <td className="px-6 py-4 text-right text-sm">
        <div className="flex justify-end gap-2">
          <Link
            to={`/workflow/${workflow.workflow_id}`}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
            title="View Details"
          >
            <Eye className="w-4 h-4" />
          </Link>
          {workflow.status === 'completed' && (
            <button
              className="p-2 text-green-600 hover:bg-green-50 rounded"
              title="Download Result"
            >
              <Download className="w-4 h-4" />
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}
