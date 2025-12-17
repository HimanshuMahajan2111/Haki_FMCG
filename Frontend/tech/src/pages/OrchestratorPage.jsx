/**
 * Workflow Orchestrator Page - Monitor and manage multi-agent workflows
 */
import React, { useState, useEffect } from 'react';
import { Activity, Play, Pause, CheckCircle, Clock, AlertCircle, Users } from 'lucide-react';
import { listWorkflows, getWorkflowStatus } from '../services/api';

const OrchestratorPage = () => {
  const [workflows, setWorkflows] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadWorkflows();
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(loadWorkflows, 5000);
    // return () => clearInterval(interval);
  }, [filter]);

  const loadWorkflows = async () => {
    try {
      const statusFilter = filter === 'all' ? null : filter;
      const data = await listWorkflows(statusFilter, 50);
      setWorkflows(data.data?.workflows || []);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load workflows:', err);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      completed: 'green',
      processing: 'yellow',
      pending: 'blue',
      failed: 'red',
    };
    return colors[status] || 'gray';
  };

  const getStatusIcon = (status) => {
    const icons = {
      completed: <CheckCircle size={16} />,
      processing: <Clock size={16} className="animate-spin" />,
      pending: <Clock size={16} />,
      failed: <AlertCircle size={16} />,
    };
    return icons[status] || <Clock size={16} />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-800 to-dark-900">
      {/* Header */}
      <div className="bg-dark-900/50 backdrop-blur-xl border-b border-dark-700/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Workflow Orchestrator</h1>
            <p className="text-gray-400">
              Monitor and manage multi-agent RFP processing workflows
            </p>
          </div>
          <button
            onClick={loadWorkflows}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            <Activity size={16} />
            Refresh
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2">
          {['all', 'processing', 'completed', 'pending', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                filter === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700/50 text-gray-400 hover:bg-dark-700'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            <p className="mt-4 text-gray-400">Loading workflows...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Workflows List */}
            <div className="lg:col-span-2 space-y-4">
              {workflows.length === 0 ? (
                <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-12 text-center">
                  <Activity size={48} className="mx-auto text-gray-600 mb-4" />
                  <p className="text-gray-400">No workflows found</p>
                </div>
              ) : (
                workflows.map((workflow) => (
                  <div
                    key={workflow.workflow_id}
                    onClick={() => setSelectedWorkflow(workflow)}
                    className={`bg-dark-800/50 backdrop-blur rounded-lg border ${
                      selectedWorkflow?.workflow_id === workflow.workflow_id
                        ? 'border-primary-500'
                        : 'border-dark-700/50'
                    } p-5 cursor-pointer hover:border-primary-500/50 transition-all`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">
                            {workflow.rfp_title || 'Untitled RFP'}
                          </h3>
                          <span
                            className={`flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-${getStatusColor(
                              workflow.status
                            )}-500/20 text-${getStatusColor(workflow.status)}-400 border border-${getStatusColor(
                              workflow.status
                            )}-500/30`}
                          >
                            {getStatusIcon(workflow.status)}
                            {workflow.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400 line-clamp-1">
                          {workflow.rfp_description || 'No description'}
                        </p>
                      </div>
                    </div>

                    {/* Workflow Progress */}
                    <div className="mb-3">
                      <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                        <span>Progress</span>
                        <span>{workflow.progress || 0}%</span>
                      </div>
                      <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary-500 to-primary-400 transition-all duration-500"
                          style={{ width: `${workflow.progress || 0}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Agents Status */}
                    <div className="grid grid-cols-4 gap-2">
                      <AgentStatus name="Sales" status={workflow.agents?.sales || 'pending'} />
                      <AgentStatus name="Technical" status={workflow.agents?.technical || 'pending'} />
                      <AgentStatus name="Pricing" status={workflow.agents?.pricing || 'pending'} />
                      <AgentStatus name="Master" status={workflow.agents?.master || 'pending'} />
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-dark-700/50 text-xs text-gray-400">
                      <span>ID: {workflow.workflow_id.substring(0, 8)}</span>
                      <span>{new Date(workflow.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Workflow Details */}
            <div className="lg:col-span-1">
              {selectedWorkflow ? (
                <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-5 sticky top-6">
                  <h2 className="text-xl font-semibold text-white mb-4">Workflow Details</h2>

                  <div className="space-y-4">
                    {/* Status */}
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Status</p>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(selectedWorkflow.status)}
                        <span className="text-white capitalize">{selectedWorkflow.status}</span>
                      </div>
                    </div>

                    {/* Progress */}
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Overall Progress</p>
                      <div className="text-2xl font-bold text-white">
                        {selectedWorkflow.progress || 0}%
                      </div>
                    </div>

                    {/* Agents */}
                    <div>
                      <p className="text-sm text-gray-400 mb-2">Agents</p>
                      <div className="space-y-2">
                        {Object.entries(selectedWorkflow.agents || {}).map(([agent, status]) => (
                          <div
                            key={agent}
                            className="flex items-center justify-between p-2 bg-dark-700/30 rounded"
                          >
                            <span className="text-white capitalize">{agent}</span>
                            <span className={`text-xs text-${getStatusColor(status)}-400`}>
                              {status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Timing */}
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Processing Time</p>
                      <p className="text-white">{selectedWorkflow.processing_time || 'N/A'}</p>
                    </div>

                    {/* Created */}
                    <div>
                      <p className="text-sm text-gray-400 mb-1">Created</p>
                      <p className="text-white text-sm">
                        {new Date(selectedWorkflow.created_at).toLocaleString()}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="pt-4 border-t border-dark-700/50">
                      <button className="w-full px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors mb-2">
                        View Details
                      </button>
                      <button className="w-full px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-lg transition-colors">
                        Download Results
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-12 text-center">
                  <Users size={48} className="mx-auto text-gray-600 mb-4" />
                  <p className="text-gray-400">Select a workflow to view details</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const AgentStatus = ({ name, status }) => {
  const getColor = () => {
    const colors = {
      completed: 'green',
      processing: 'yellow',
      pending: 'gray',
      failed: 'red',
    };
    return colors[status] || 'gray';
  };

  return (
    <div
      className={`text-center p-2 rounded bg-${getColor()}-500/10 border border-${getColor()}-500/30`}
    >
      <p className={`text-xs text-${getColor()}-400 font-medium`}>{name}</p>
    </div>
  );
};

export default OrchestratorPage;
