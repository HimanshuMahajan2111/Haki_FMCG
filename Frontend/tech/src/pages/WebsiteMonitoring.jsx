import React, { useState, useEffect } from 'react';
import { Globe, RefreshCw, CheckCircle, XCircle, Clock, Activity, Settings as SettingsIcon, Plus, Edit, Trash2, Play } from 'lucide-react';

const WebsiteMonitoring = () => {
  const [websites, setWebsites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [scanningId, setScanningId] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSite, setEditingSite] = useState(null);

  useEffect(() => {
    fetchWebsites();
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(fetchWebsites, 60000); // Refresh every minute
    // return () => clearInterval(interval);
  }, []);

  const fetchWebsites = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/monitoring/websites');
      if (response.ok) {
        const data = await response.json();
        setWebsites(data.websites || []);
      } else {
        // No fallback - show empty state if API is not available
        setWebsites([]);
      }
    } catch (error) {
      console.error('Error fetching websites:', error);
      setWebsites([]);
    } finally {
      setLoading(false);
    }
  };

  const handleScanSite = async (siteId) => {
    setScanningId(siteId);
    try {
      const response = await fetch(`/api/monitoring/trigger-scan?site_id=${siteId}`, {
        method: 'POST'
      });
      if (response.ok) {
        setTimeout(() => {
          fetchWebsites();
          setScanningId(null);
        }, 3000);
      }
    } catch (error) {
      console.error('Error scanning site:', error);
      setTimeout(() => setScanningId(null), 2000);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'warning':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4" />;
      case 'warning':
        return <Clock className="w-4 h-4" />;
      case 'error':
        return <XCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getTimeSince = (timestamp) => {
    const minutes = Math.floor((Date.now() - new Date(timestamp)) / 60000);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg">
              <Globe className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Website Monitoring</h1>
              <p className="text-gray-600">Real-time RFP discovery from monitored sources</p>
            </div>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:shadow-lg transition-all"
          >
            <Plus className="w-5 h-5" />
            Add Website
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl shadow-md border border-blue-100">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Globe className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Sources</p>
                <p className="text-2xl font-bold text-gray-900">{websites.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-md border border-green-100">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">
                  {websites.filter(w => w.status === 'active').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-md border border-purple-100">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Activity className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total RFPs Found</p>
                <p className="text-2xl font-bold text-gray-900">
                  {websites.reduce((sum, w) => sum + (w.rfps_found || 0), 0)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-md border border-amber-100">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Clock className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Avg Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(websites.reduce((sum, w) => sum + (w.success_rate || 0), 0) / websites.length).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Websites Table */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-blue-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Website</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Last Check</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Success Rate</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">RFPs Found</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Interval</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Category</th>
                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {websites.map((site) => (
                <tr key={site.id} className="hover:bg-blue-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-semibold text-gray-900">{site.name}</p>
                      <p className="text-sm text-gray-500 truncate max-w-xs">{site.url}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(site.status)}`}>
                      {getStatusIcon(site.status)}
                      {site.status.charAt(0).toUpperCase() + site.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {getTimeSince(site.last_check)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            site.success_rate >= 90 ? 'bg-green-500' :
                            site.success_rate >= 75 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${site.success_rate}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">{site.success_rate}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                      {site.rfps_found}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {site.interval_minutes}m
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                      {site.category}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleScanSite(site.id)}
                        disabled={scanningId === site.id}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50"
                        title="Scan Now"
                      >
                        <Play className={`w-4 h-4 ${scanningId === site.id ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => setEditingSite(site)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Configure"
                      >
                        <SettingsIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scan History */}
      <div className="mt-6 bg-white rounded-xl shadow-lg border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-6 h-6 text-blue-600" />
          Recent Scan Activity
        </h2>
        <div className="space-y-3">
          {websites.slice(0, 5).map((site, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                {getStatusIcon(site.status)}
                <div>
                  <p className="font-medium text-gray-900">{site.name}</p>
                  <p className="text-sm text-gray-500">Last scan: {getTimeSince(site.last_check)}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{site.rfps_found} RFPs</p>
                <p className="text-xs text-gray-500">{site.success_rate}% success</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WebsiteMonitoring;
