import React, { useState, useEffect } from 'react';
import { 
  getDashboard, 
  getRFPProcessing, 
  getMatchAccuracy, 
  getWinRates, 
  getAgentPerformance,
  getSystemHealth,
  getPerformanceMetrics,
  getBottlenecks,
  getCacheStats
} from '../services/api';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState(30);
  
  // State for different data sections
  const [dashboardData, setDashboardData] = useState(null);
  const [rfpData, setRFPData] = useState(null);
  const [matchData, setMatchData] = useState(null);
  const [winData, setWinData] = useState(null);
  const [agentData, setAgentData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [perfData, setPerfData] = useState(null);
  const [cacheData, setCacheData] = useState(null);
  const [bottlenecks, setBottlenecks] = useState([]);

  useEffect(() => {
    loadAnalytics();
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(loadAnalytics, 30000); // Refresh every 30 seconds
    // return () => clearInterval(interval);
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboard, health, perf, cache] = await Promise.all([
        getDashboard(timeRange),
        getSystemHealth(),
        getPerformanceMetrics(),
        getCacheStats()
      ]);

      setDashboardData(dashboard);
      setHealthData(health);
      setPerfData(perf);
      setCacheData(cache);

      // Extract individual sections from dashboard
      if (dashboard) {
        setRFPData(dashboard.rfp_processing);
        setMatchData(dashboard.match_accuracy);
        setWinData(dashboard.win_rates);
        setAgentData(dashboard.agent_performance);
      }

      // Load bottlenecks
      try {
        const bottleneckData = await getBottlenecks();
        setBottlenecks(bottleneckData || []);
      } catch (e) {
        console.warn('Bottlenecks not available:', e);
      }

    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Analytics</h3>
        <p className="text-red-600">{error}</p>
        <button 
          onClick={loadAnalytics}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
        <div className="flex gap-3">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button 
            onClick={loadAnalytics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-4">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'rfp', label: 'RFP Processing' },
            { id: 'matching', label: 'Match Accuracy' },
            { id: 'wins', label: 'Win Rates' },
            { id: 'agents', label: 'Agent Performance' },
            { id: 'system', label: 'System Health' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <OverviewTab 
          rfpData={rfpData} 
          matchData={matchData} 
          winData={winData} 
          agentData={agentData}
          healthData={healthData}
        />
      )}

      {activeTab === 'rfp' && <RFPTab data={rfpData} />}
      {activeTab === 'matching' && <MatchingTab data={matchData} />}
      {activeTab === 'wins' && <WinRatesTab data={winData} />}
      {activeTab === 'agents' && <AgentsTab data={agentData} />}
      {activeTab === 'system' && (
        <SystemTab 
          healthData={healthData} 
          perfData={perfData} 
          cacheData={cacheData}
          bottlenecks={bottlenecks}
        />
      )}

      {/* Last Updated */}
      <p className="text-sm text-gray-500 text-center">
        Last updated: {new Date().toLocaleTimeString()}
      </p>
    </div>
  );
};

// Overview Tab Component
const OverviewTab = ({ rfpData, matchData, winData, agentData, healthData }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <MetricCard
      title="Total RFPs"
      value={rfpData?.total_rfps || 0}
      subtitle={`${Math.round(rfpData?.success_rate || 0)}% success rate`}
      color="blue"
    />
    <MetricCard
      title="Avg Processing Time"
      value={`${Math.round(rfpData?.average_processing_time_seconds || 0)}s`}
      subtitle="Per workflow"
      color="green"
    />
    <MetricCard
      title="Match Accuracy"
      value={`${Math.round((matchData?.average_match_score || 0) * 100)}%`}
      subtitle={`${matchData?.total_matches || 0} matches`}
      color="purple"
    />
    <MetricCard
      title="Win Rate"
      value={`${Math.round(winData?.overall_win_rate || 0)}%`}
      subtitle={`${winData?.total_won || 0} deals won`}
      color="yellow"
    />
    <MetricCard
      title="Active Agents"
      value={agentData?.agents?.length || 0}
      subtitle={`${agentData?.total_executions || 0} executions`}
      color="indigo"
    />
    <MetricCard
      title="System Health"
      value={`${Math.round(100 - (healthData?.cpu_percent || 0))}%`}
      subtitle={`CPU: ${Math.round(healthData?.cpu_percent || 0)}%`}
      color="red"
    />
  </div>
);

// RFP Tab Component
const RFPTab = ({ data }) => {
  if (!data) return <div>No RFP data available</div>;

  const statusData = Object.entries(data.status_breakdown || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Total RFPs" value={data.total_rfps} color="blue" />
        <MetricCard title="Success Rate" value={`${Math.round(data.success_rate)}%`} color="green" />
        <MetricCard title="Avg Time" value={`${Math.round(data.average_processing_time_seconds)}s`} color="purple" />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Status Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={statusData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {statusData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {data.daily_volume && data.daily_volume.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Daily Volume</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.daily_volume.slice(-14)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// Matching Tab Component
const MatchingTab = ({ data }) => {
  if (!data) return <div>No matching data available</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard 
          title="Avg Match Score" 
          value={`${(data.average_match_score * 100).toFixed(1)}%`} 
          color="blue" 
        />
        <MetricCard 
          title="Avg Confidence" 
          value={`${(data.average_confidence * 100).toFixed(1)}%`} 
          color="green" 
        />
        <MetricCard 
          title="High Confidence" 
          value={data.high_confidence_matches} 
          subtitle={`${((data.high_confidence_matches / data.total_matches) * 100).toFixed(1)}%`}
          color="purple" 
        />
      </div>
    </div>
  );
};

// Win Rates Tab Component
const WinRatesTab = ({ data }) => {
  if (!data) return <div>No win rate data available</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Win Rate" value={`${Math.round(data.overall_win_rate)}%`} color="green" />
        <MetricCard title="Total Won" value={data.total_won} color="blue" />
        <MetricCard title="Avg Quote (Won)" value={`$${data.average_quote_value_won?.toLocaleString()}`} color="yellow" />
      </div>

      {data.win_rates_by_customer && data.win_rates_by_customer.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Win Rates by Customer</h3>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Won</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Win Rate</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.win_rates_by_customer.slice(0, 10).map((customer, idx) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {customer.customer_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.total}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.won}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="px-2 py-1 rounded bg-green-100 text-green-800">
                      {Math.round(customer.win_rate)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// Agents Tab Component
const AgentsTab = ({ data }) => {
  if (!data || !data.agents) return <div>No agent data available</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Total Agents" value={data.agents.length} color="blue" />
        <MetricCard title="Total Executions" value={data.total_executions} color="green" />
        <MetricCard title="Avg Success Rate" value={`${Math.round(data.average_success_rate)}%`} color="purple" />
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold">Agent Performance Rankings</h3>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Executions</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Success Rate</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Duration</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.agents.map((agent, idx) => (
              <tr key={idx}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">#{idx + 1}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {agent.agent_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {agent.total_executions}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className={`px-2 py-1 rounded ${
                    agent.success_rate > 90 ? 'bg-green-100 text-green-800' :
                    agent.success_rate > 70 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {Math.round(agent.success_rate)}%
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {agent.avg_duration_seconds.toFixed(2)}s
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// System Tab Component
const SystemTab = ({ healthData, perfData, cacheData, bottlenecks }) => {
  if (!healthData) return <div>No system data available</div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard 
          title="CPU Usage" 
          value={`${healthData.cpu_percent.toFixed(1)}%`}
          subtitle={`${healthData.cpu_count} cores`}
          color="blue" 
        />
        <MetricCard 
          title="Memory Usage" 
          value={`${healthData.memory_percent.toFixed(1)}%`}
          subtitle={`${healthData.memory_used_gb.toFixed(1)} GB used`}
          color="purple" 
        />
        <MetricCard 
          title="Disk Usage" 
          value={`${healthData.disk_percent.toFixed(1)}%`}
          subtitle={`${healthData.disk_free_gb.toFixed(1)} GB free`}
          color="yellow" 
        />
      </div>

      {cacheData && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Cache Performance</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Hit Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {cacheData.hit_rate ? (cacheData.hit_rate * 100).toFixed(1) : 0}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Cache Size</p>
              <p className="text-2xl font-bold text-blue-600">{cacheData.size || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Redis Status</p>
              <p className="text-2xl font-bold text-gray-600">
                {cacheData.redis_connected ? '✓ Connected' : '✗ Disconnected'}
              </p>
            </div>
          </div>
        </div>
      )}

      {bottlenecks && bottlenecks.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4 text-yellow-600">⚠️ Performance Bottlenecks</h3>
          <div className="space-y-2">
            {bottlenecks.slice(0, 10).map((b, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-yellow-50 rounded">
                <span className="font-medium">{b.operation_name}</span>
                <span className="text-yellow-700">{b.duration.toFixed(2)}s (threshold: {b.threshold}s)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, subtitle, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    purple: 'bg-purple-50 border-purple-200 text-purple-900',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    red: 'bg-red-50 border-red-200 text-red-900',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-900'
  };

  return (
    <div className={`rounded-lg shadow p-6 border ${colors[color]}`}>
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <p className="text-3xl font-bold mb-1">{value}</p>
      {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
};

export default Analytics;