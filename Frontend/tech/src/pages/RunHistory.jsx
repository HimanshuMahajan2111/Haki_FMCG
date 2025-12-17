import React, { useState, useEffect } from 'react';
import { Clock, User, TrendingUp, Download, Filter, Search, Calendar, Award, DollarSign, Package } from 'lucide-react';

/**
 * Run History Page - RAF AI Audit Log
 * 
 * Features:
 * - Complete audit log of all AI analyses
 * - Timestamps, users, win probabilities
 * - Scenario choices tracking
 * - Governance and tracing
 * - AI decision evolution monitoring
 * - Export capabilities
 */

const RunHistory = () => {
  const [history, setHistory] = useState([]);
  const [filters, setFilters] = useState({
    dateRange: '30days',
    user: 'all',
    status: 'all',
    search: ''
  });
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []); // Only load on mount, removed filters dependency to prevent auto-reload

  const fetchHistory = async () => {
    setLoading(true);
    try {
      // Fetch from API
      const response = await fetch('/api/rfp/history?limit=100');
      if (response.ok) {
        const data = await response.json();
        console.log('History data from backend:', data);
        
        const historyList = data.data?.history || data.history || [];
        const enrichedHistory = historyList.map((item, index) => ({
          ...item,
          runId: item.id ? `RUN-${String(item.id).padStart(4, '0')}` : `RUN-${index + 1}`,
          user: item.processed_by || 'sales@hakifmcg.com',
          winProbability: item.confidence_score ? (item.confidence_score * 100).toFixed(1) : '75.0',
          scenarioChosen: item.scenario || item.metadata?.scenario || 'Standard Pricing',
          recommendedSKU: item.recommended_sku || item.metadata?.sku || 'N/A',
          estimatedValue: item.estimated_value || item.metadata?.value || 5000000,
          analysisTime: item.processing_time || item.processing_time_seconds || 0
        }));
        
        console.log('Enriched history:', enrichedHistory);
        setHistory(enrichedHistory);
      } else {
        console.error('Failed to fetch history:', response.status);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    const csv = [
      ['Run ID', 'Timestamp', 'User', 'RFP Title', 'Win Probability', 'Scenario', 'Status', 'Analysis Time'],
      ...history.map(h => [
        h.runId,
        new Date(h.processed_at).toLocaleString(),
        h.user,
        h.title,
        `${h.winProbability}%`,
        h.scenarioChosen,
        h.status,
        `${h.analysisTime}s`
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rfp-run-history-${Date.now()}.csv`;
    a.click();
  };

  const filteredHistory = history.filter(h => {
    if (filters.user !== 'all' && h.user !== filters.user) return false;
    if (filters.status !== 'all' && h.status !== filters.status) return false;
    if (filters.search && !h.title.toLowerCase().includes(filters.search.toLowerCase())) return false;
    
    // Date range filter
    const itemDate = new Date(h.processed_at);
    const now = new Date();
    const daysDiff = (now - itemDate) / (1000 * 60 * 60 * 24);
    if (filters.dateRange === '7days' && daysDiff > 7) return false;
    if (filters.dateRange === '30days' && daysDiff > 30) return false;
    if (filters.dateRange === '90days' && daysDiff > 90) return false;
    
    return true;
  });

  const getStatusColor = (status) => {
    const colors = {
      'approved': 'bg-green-100 text-green-700 border-green-300',
      'reviewed': 'bg-blue-100 text-blue-700 border-blue-300',
      'processing': 'bg-amber-100 text-amber-700 border-amber-300',
      'rejected': 'bg-red-100 text-red-700 border-red-300',
      'discovered': 'bg-gray-100 text-gray-700 border-gray-300'
    };
    return colors[status] || colors.discovered;
  };

  const getWinProbabilityBadge = (probability) => {
    const prob = parseFloat(probability);
    if (prob >= 70) return 'bg-green-500';
    if (prob >= 50) return 'bg-blue-500';
    if (prob >= 30) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const RunDetailModal = ({ run, onClose }) => {
    if (!run) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="bg-gradient-to-r from-sky-500 to-blue-600 p-6 text-white">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold mb-2">Run Details</h2>
                <p className="text-sky-100">{run.runId}</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">RFP Title</div>
                <div className="font-bold text-gray-900">{run.title}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Processed By</div>
                <div className="font-bold text-gray-900">{run.user}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Timestamp</div>
                <div className="font-bold text-gray-900">
                  {new Date(run.processed_at).toLocaleString()}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Analysis Time</div>
                <div className="font-bold text-gray-900">{run.analysisTime}s</div>
              </div>
            </div>

            {/* AI Decision Summary */}
            <div className="border-2 border-gray-200 rounded-xl p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">AI Decision Summary</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Win Probability</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getWinProbabilityBadge(run.winProbability)}`}></div>
                    <span className="font-bold text-2xl text-gray-900">{run.winProbability}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Recommended SKU</span>
                  <span className="font-bold text-gray-900">{run.recommendedSKU}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Pricing Scenario</span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-semibold text-sm">
                    {run.scenarioChosen}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Estimated Value</span>
                  <span className="font-bold text-gray-900">
                    ₹{(run.estimatedValue / 100000).toFixed(2)}L
                  </span>
                </div>
              </div>
            </div>

            {/* Processing Timeline */}
            <div className="border-2 border-gray-200 rounded-xl p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Processing Timeline</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">✓</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">RFP Parsing</div>
                    <div className="text-sm text-gray-600">Completed in 8s</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">✓</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">Technical Analysis</div>
                    <div className="text-sm text-gray-600">Completed in 15s</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">✓</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">Pricing Scenarios</div>
                    <div className="text-sm text-gray-600">Completed in 12s</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">✓</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900">Stock Verification</div>
                    <div className="text-sm text-gray-600">Completed in 5s</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 p-6 bg-gray-50">
            <button
              onClick={onClose}
              className="w-full py-3 bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold rounded-lg hover:from-sky-600 hover:to-blue-700 transition-all"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Run History & Audit Log</h1>
            <p className="text-gray-600">Complete traceability of AI analysis decisions</p>
          </div>
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl"
          >
            <Download className="w-5 h-5" />
            <span>Export to CSV</span>
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-blue-100">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8 text-blue-600" />
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{history.length}</div>
            <div className="text-sm text-gray-600">Total Runs</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-green-100">
            <div className="flex items-center justify-between mb-2">
              <Award className="w-8 h-8 text-green-600" />
              <span className="text-sm font-bold text-green-600">+8%</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {((history.filter(h => h.status === 'approved').length / history.length) * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Approval Rate</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-purple-100">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-8 h-8 text-purple-600" />
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {(history.reduce((sum, h) => sum + h.winProbability, 0) / history.length).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-600">Avg Win Probability</div>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-lg border-2 border-amber-100">
            <div className="flex items-center justify-between mb-2">
              <Package className="w-8 h-8 text-amber-600" />
              <span className="text-sm font-bold text-green-600">Fast</span>
            </div>
            <div className="text-3xl font-bold text-gray-900">
              {(history.reduce((sum, h) => sum + h.analysisTime, 0) / history.length).toFixed(0)}s
            </div>
            <div className="text-sm text-gray-600">Avg Analysis Time</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                Date Range
              </label>
              <select
                value={filters.dateRange}
                onChange={(e) => setFilters({ ...filters, dateRange: e.target.value })}
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
              >
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="90days">Last 90 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <User className="w-4 h-4 inline mr-1" />
                User
              </label>
              <select
                value={filters.user}
                onChange={(e) => setFilters({ ...filters, user: e.target.value })}
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
              >
                <option value="all">All Users</option>
                <option value="sales@hakifmcg.com">Sales Team</option>
                <option value="ops@hakifmcg.com">Operations</option>
                <option value="admin@hakifmcg.com">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Filter className="w-4 h-4 inline mr-1" />
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
              >
                <option value="all">All Status</option>
                <option value="approved">Approved</option>
                <option value="reviewed">Reviewed</option>
                <option value="processing">Processing</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                <Search className="w-4 h-4 inline mr-1" />
                Search
              </label>
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                placeholder="Search RFPs..."
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-white rounded-xl shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-blue-50 border-b-2 border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Run ID</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Timestamp</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">User</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">RFP Title</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Win Probability</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Scenario</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Analysis Time</th>
                <th className="px-6 py-4 text-center text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="9" className="px-6 py-12 text-center">
                    <div className="flex justify-center items-center space-x-2">
                      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-gray-600">Loading history...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredHistory.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-6 py-12 text-center text-gray-600">
                    No runs found matching your filters
                  </td>
                </tr>
              ) : (
                filteredHistory.map((run, idx) => (
                  <tr key={idx} className="hover:bg-blue-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-mono text-sm text-gray-900">{run.runId}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {new Date(run.processed_at).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-blue-600" />
                        </div>
                        <span className="text-sm text-gray-900">{run.user}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-gray-900 max-w-xs truncate">
                        {run.title}
                      </div>
                      <div className="text-xs text-gray-500">ID: {run.id}</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${getWinProbabilityBadge(run.winProbability)}`}></div>
                        <span className="font-bold text-gray-900">{run.winProbability}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                        {run.scenarioChosen}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(run.status)}`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="text-sm font-semibold text-gray-900">{run.analysisTime}s</div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => setSelectedRun(run)}
                        className="text-blue-600 hover:text-blue-700 font-semibold text-sm"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Run Detail Modal */}
      {selectedRun && (
        <RunDetailModal run={selectedRun} onClose={() => setSelectedRun(null)} />
      )}
    </div>
  );
};

export default RunHistory;
