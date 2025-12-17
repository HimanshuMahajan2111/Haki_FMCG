/**
 * Analytics Dashboard Page
 */
import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, CheckCircle, AlertCircle, DollarSign } from 'lucide-react';
import { getDashboard, getRFPProcessing } from '../services/api';

const AnalyticsPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [processingData, setProcessingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadData();
  }, []); // Only load on mount, removed timeRange dependency to prevent auto-reload

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashboard, processing] = await Promise.all([
        getDashboard(timeRange),
        getRFPProcessing(timeRange),
      ]);
      setDashboardData(dashboard);
      setProcessingData(processing);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-dark-800 to-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-800 to-dark-900">
      {/* Header */}
      <div className="bg-dark-900/50 backdrop-blur-xl border-b border-dark-700/50 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
            <p className="text-gray-400">
              System performance and RFP processing metrics
            </p>
          </div>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500"
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
          </select>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            icon={<CheckCircle className="text-green-400" />}
            title="Completed RFPs"
            value={dashboardData?.data?.total_completed || 0}
            trend="+12%"
            trendUp={true}
            color="green"
          />
          <MetricCard
            icon={<Clock className="text-yellow-400" />}
            title="In Progress"
            value={dashboardData?.data?.in_progress || 0}
            trend="Active"
            color="yellow"
          />
          <MetricCard
            icon={<TrendingUp className="text-blue-400" />}
            title="Success Rate"
            value={`${dashboardData?.data?.success_rate || 95}%`}
            trend="+5%"
            trendUp={true}
            color="blue"
          />
          <MetricCard
            icon={<DollarSign className="text-purple-400" />}
            title="Avg. Processing Time"
            value={`${dashboardData?.data?.avg_time || 45}s`}
            trend="-8%"
            trendUp={true}
            color="purple"
          />
        </div>

        {/* Processing Statistics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* RFP Status Distribution */}
          <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">RFP Status Distribution</h2>
            <div className="space-y-4">
              <StatusBar label="Completed" value={65} color="green" />
              <StatusBar label="In Progress" value={20} color="yellow" />
              <StatusBar label="Pending" value={10} color="blue" />
              <StatusBar label="Failed" value={5} color="red" />
            </div>
          </div>

          {/* Agent Performance */}
          <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Agent Performance</h2>
            <div className="space-y-4">
              <AgentMetric name="Sales Agent" success={98} avgTime="5s" />
              <AgentMetric name="Technical Agent" success={96} avgTime="15s" />
              <AgentMetric name="Pricing Agent" success={99} avgTime="8s" />
              <AgentMetric name="Master Agent" success={97} avgTime="12s" />
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Recent Processing Activity</h2>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-4 bg-dark-700/30 rounded-lg border border-dark-600/30"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle size={20} className="text-green-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">RFP #{12345 - i}</p>
                    <p className="text-sm text-gray-400">Solar Cable Procurement - NTPC</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-white font-medium">45.2s</p>
                  <p className="text-sm text-gray-400">2 hours ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Product Matching Statistics */}
        <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Product Matching Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-dark-700/30 rounded-lg">
              <div className="text-3xl font-bold text-primary-400 mb-2">693</div>
              <div className="text-gray-400">Total Products</div>
            </div>
            <div className="text-center p-4 bg-dark-700/30 rounded-lg">
              <div className="text-3xl font-bold text-green-400 mb-2">94%</div>
              <div className="text-gray-400">Match Success Rate</div>
            </div>
            <div className="text-center p-4 bg-dark-700/30 rounded-lg">
              <div className="text-3xl font-bold text-blue-400 mb-2">3.2</div>
              <div className="text-gray-400">Avg. Matches per RFP</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ icon, title, value, trend, trendUp, color }) => {
  const colorClasses = {
    green: 'from-green-500/20 to-green-600/20 border-green-500/30',
    yellow: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30',
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} backdrop-blur rounded-lg border p-6`}>
      <div className="flex items-center justify-between mb-4">
        <div className="w-12 h-12 rounded-lg bg-dark-800/50 flex items-center justify-center">
          {icon}
        </div>
        {trend && (
          <span className={`text-sm ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
            {trend}
          </span>
        )}
      </div>
      <h3 className="text-gray-400 text-sm mb-1">{title}</h3>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
};

const StatusBar = ({ label, value, color }) => {
  const colorClasses = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    blue: 'bg-blue-500',
    red: 'bg-red-500',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-2">
        <span className="text-gray-400">{label}</span>
        <span className="text-white font-medium">{value}%</span>
      </div>
      <div className="w-full h-2 bg-dark-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all duration-500`}
          style={{ width: `${value}%` }}
        ></div>
      </div>
    </div>
  );
};

const AgentMetric = ({ name, success, avgTime }) => (
  <div className="flex items-center justify-between p-4 bg-dark-700/30 rounded-lg">
    <div>
      <p className="text-white font-medium">{name}</p>
      <p className="text-sm text-gray-400">Avg. Time: {avgTime}</p>
    </div>
    <div className="text-right">
      <p className="text-2xl font-bold text-green-400">{success}%</p>
      <p className="text-xs text-gray-400">Success Rate</p>
    </div>
  </div>
);

export default AnalyticsPage;
