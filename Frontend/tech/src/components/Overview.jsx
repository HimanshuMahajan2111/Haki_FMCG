import React, { useState, useEffect } from 'react';
import { getDashboard, getSystemHealth, getRealtimeMetrics } from '../services/api';
import { Activity, TrendingUp, Clock, CheckCircle, AlertCircle } from 'lucide-react';

const Overview = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [health, setHealth] = useState(null);
  const [realtime, setRealtime] = useState(null);

  useEffect(() => {
    loadData();
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    // return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [dashData, healthData, realtimeData] = await Promise.all([
        getDashboard(7),
        getSystemHealth(),
        getRealtimeMetrics().catch(() => null)
      ]);
      
      setDashboard(dashData);
      setHealth(healthData);
      setRealtime(realtimeData);
      setError(null);
    } catch (err) {
      console.error('Failed to load overview:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboard) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 m-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="text-red-600 mt-1" size={24} />
          <div>
            <h3 className="text-red-800 font-semibold text-lg mb-2">Failed to Load Dashboard</h3>
            <p className="text-red-600 mb-4">{error}</p>
            <button 
              onClick={loadData}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const rfp = dashboard?.rfp_processing || {};
  const match = dashboard?.match_accuracy || {};
  const wins = dashboard?.win_rates || {};
  const agents = dashboard?.agent_performance || {};

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Dashboard Overview</h2>
          <p className="text-gray-600 mt-1">Last 7 days performance summary</p>
        </div>
        <button 
          onClick={loadData}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <Activity size={18} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={<CheckCircle className="text-blue-600" size={28} />}
          title="Total RFPs"
          value={rfp.total_rfps || 0}
          subtitle={`${Math.round(rfp.success_rate || 0)}% success rate`}
          trend={rfp.total_rfps > 0 ? 'up' : 'neutral'}
          color="blue"
        />
        
        <MetricCard
          icon={<Clock className="text-green-600" size={28} />}
          title="Avg Processing"
          value={`${Math.round(rfp.average_processing_time_seconds || 0)}s`}
          subtitle="Per workflow"
          trend="neutral"
          color="green"
        />
        
        <MetricCard
          icon={<TrendingUp className="text-purple-600" size={28} />}
          title="Match Accuracy"
          value={`${Math.round((match.average_match_score || 0) * 100)}%`}
          subtitle={`${match.total_matches || 0} total matches`}
          trend={match.average_match_score > 0.8 ? 'up' : 'neutral'}
          color="purple"
        />
        
        <MetricCard
          icon={<Activity className="text-yellow-600" size={28} />}
          title="Win Rate"
          value={`${Math.round(wins.overall_win_rate || 0)}%`}
          subtitle={`${wins.total_won || 0} / ${wins.total_completed || 0} deals`}
          trend={wins.overall_win_rate > 60 ? 'up' : 'neutral'}
          color="yellow"
        />
      </div>

      {/* System Health */}
      {health && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="text-blue-600" size={24} />
            System Health
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">CPU Usage</span>
                <span className="text-sm font-semibold">{health.cpu_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health.cpu_percent > 80 ? 'bg-red-500' : 
                    health.cpu_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.cpu_percent}%` }}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Memory Usage</span>
                <span className="text-sm font-semibold">{health.memory_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health.memory_percent > 80 ? 'bg-red-500' : 
                    health.memory_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.memory_percent}%` }}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Disk Usage</span>
                <span className="text-sm font-semibold">{health.disk_percent.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    health.disk_percent > 80 ? 'bg-red-500' : 
                    health.disk_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${health.disk_percent}%` }}
                />
              </div>
            </div>
          </div>
          
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">CPU Cores:</span>
              <span className="ml-2 font-semibold">{health.cpu_count}</span>
            </div>
            <div>
              <span className="text-gray-600">Memory:</span>
              <span className="ml-2 font-semibold">{health.memory_used_gb.toFixed(1)} GB</span>
            </div>
            <div>
              <span className="text-gray-600">Disk Free:</span>
              <span className="ml-2 font-semibold">{health.disk_free_gb.toFixed(1)} GB</span>
            </div>
            <div>
              <span className="text-gray-600">Active Workflows:</span>
              <span className="ml-2 font-semibold">{health.active_workflows || 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* RFP Status Breakdown */}
      {rfp.status_breakdown && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">RFP Status Distribution</h3>
          <div className="space-y-3">
            {Object.entries(rfp.status_breakdown).map(([status, count]) => {
              const percentage = (count / rfp.total_rfps) * 100;
              const statusColors = {
                completed: 'bg-green-500',
                in_progress: 'bg-blue-500',
                pending: 'bg-yellow-500',
                failed: 'bg-red-500'
              };
              
              return (
                <div key={status} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium capitalize">{status.replace('_', ' ')}</span>
                    <span className="text-gray-600">{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${statusColors[status] || 'bg-gray-500'}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top Agents */}
      {agents.agents && agents.agents.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Top Performing Agents</h3>
          <div className="space-y-3">
            {agents.agents.slice(0, 5).map((agent, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                    {idx + 1}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{agent.agent_name}</p>
                    <p className="text-sm text-gray-600">{agent.total_executions} executions</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${
                    agent.success_rate > 90 ? 'text-green-600' :
                    agent.success_rate > 70 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {Math.round(agent.success_rate)}%
                  </div>
                  <div className="text-xs text-gray-500">{agent.avg_duration_seconds.toFixed(2)}s avg</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Real-time Activity */}
      {realtime && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="text-green-600 animate-pulse" size={24} />
            Real-time Activity
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">
                {realtime.active_workflows || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Active Workflows</div>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {realtime.recent_completions || 0}
              </div>
              <div className="text-sm text-gray-600 mt-1">Recent Completions</div>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl font-bold text-yellow-600">
                {realtime.avg_queue_time_seconds?.toFixed(1) || 0}s
              </div>
              <div className="text-sm text-gray-600 mt-1">Avg Queue Time</div>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <p className="text-sm text-gray-500 text-center">
        Last updated: {new Date().toLocaleTimeString()}
      </p>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ icon, title, value, subtitle, trend, color }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    yellow: 'from-yellow-500 to-yellow-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-lg bg-gradient-to-br ${colorClasses[color]} bg-opacity-10`}>
          {icon}
        </div>
        {trend === 'up' && (
          <TrendingUp className="text-green-600" size={20} />
        )}
      </div>
      <h3 className="text-gray-600 text-sm font-medium mb-2">{title}</h3>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <p className="text-sm text-gray-500">{subtitle}</p>
    </div>
  );
};

export default Overview;