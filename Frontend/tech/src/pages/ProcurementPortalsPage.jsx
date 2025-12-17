import React, { useState, useEffect } from 'react';
import { Activity, Globe, Search, Filter, Download, ExternalLink, Clock, DollarSign, MapPin, FileText } from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000';

const ProcurementPortalsPage = () => {
  const [rfps, setRfps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedWebsite, setSelectedWebsite] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [websites, setWebsites] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [selectedRfp, setSelectedRfp] = useState(null);

  useEffect(() => {
    loadWebsites();
    loadStatistics();
  }, []);

  const loadWebsites = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/scanner/websites`);
      setWebsites(response.data.websites);
    } catch (error) {
      console.error('Failed to load websites:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/scanner/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const scanWebsites = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/scanner/scan`;
      
      if (selectedWebsite !== 'all') {
        url = `${API_BASE}/api/scanner/scan/${selectedWebsite}`;
      }
      
      if (selectedCategory) {
        url += `?category=${selectedCategory}`;
      }

      const response = await axios.get(url);
      setRfps(response.data.rfps);
      await loadStatistics();
    } catch (error) {
      console.error('Scan failed:', error);
      alert('Failed to scan websites. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const processRfps = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/api/scanner/process-rfps`, null, {
        params: selectedCategory ? { category: selectedCategory } : {}
      });
      alert(`${response.data.rfps_ready_for_processing} RFPs are ready for agent processing!`);
    } catch (error) {
      console.error('Processing failed:', error);
      alert('Failed to process RFPs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    } else if (value >= 100000) {
      return `₹${(value / 100000).toFixed(2)} Lakhs`;
    } else {
      return `₹${value.toLocaleString('en-IN')}`;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const getDaysUntilDeadline = (deadlineString) => {
    const deadline = new Date(deadlineString);
    const now = new Date();
    const diffTime = deadline - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getWebsiteColor = (website) => {
    const colors = {
      'eprocure.gov.in': 'bg-blue-500',
      'gem.gov.in': 'bg-green-500',
      'ion.tcs.com': 'bg-purple-500',
      'eprocure.lntecc.com': 'bg-orange-500'
    };
    return colors[website] || 'bg-gray-500';
  };

  const filteredRfps = rfps.filter(rfp => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      rfp.title.toLowerCase().includes(query) ||
      rfp.buyer.toLowerCase().includes(query) ||
      rfp.category.toLowerCase().includes(query) ||
      rfp.rfp_id.toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                <Globe className="text-purple-400" />
                Procurement Portals
              </h1>
              <p className="text-gray-300">
                Scan and monitor RFPs from official procurement websites
              </p>
            </div>
            <button
              onClick={scanWebsites}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg"
            >
              <Activity className={loading ? "animate-spin" : ""} size={20} />
              {loading ? 'Scanning...' : 'Scan Websites'}
            </button>
          </div>
        </div>

        {/* Statistics */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-dark-800/50 backdrop-blur border border-purple-500/30 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Total Scans</div>
              <div className="text-2xl font-bold text-white">{statistics.total_scans}</div>
            </div>
            <div className="bg-dark-800/50 backdrop-blur border border-blue-500/30 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">RFPs Found</div>
              <div className="text-2xl font-bold text-white">{statistics.total_rfps_found}</div>
            </div>
            <div className="bg-dark-800/50 backdrop-blur border border-green-500/30 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Avg per Scan</div>
              <div className="text-2xl font-bold text-white">{statistics.avg_rfps_per_scan.toFixed(1)}</div>
            </div>
            <div className="bg-dark-800/50 backdrop-blur border border-orange-500/30 rounded-lg p-4">
              <div className="text-gray-400 text-sm mb-1">Last Scan</div>
              <div className="text-sm font-medium text-white">
                {statistics.last_scan ? formatDate(statistics.last_scan) : 'Never'}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-dark-800/50 backdrop-blur border border-purple-500/30 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Filter size={20} className="text-purple-400" />
            <h2 className="text-xl font-semibold text-white">Filters</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Website Filter */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Website</label>
              <select
                value={selectedWebsite}
                onChange={(e) => setSelectedWebsite(e.target.value)}
                className="w-full bg-dark-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:border-purple-500 focus:outline-none"
              >
                <option value="all">All Websites</option>
                <option value="eProcure">eProcure</option>
                <option value="GEM">GEM</option>
                <option value="TCS iON">TCS iON</option>
                <option value="L&T eProcure">L&T eProcure</option>
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-dark-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:border-purple-500 focus:outline-none"
              >
                <option value="">All Categories</option>
                <option value="Power Cables">Power Cables</option>
                <option value="Solar Cables">Solar Cables</option>
                <option value="Control Cables">Control Cables</option>
                <option value="Flexible Cables">Flexible Cables</option>
                <option value="Signaling Cables">Signaling Cables</option>
              </select>
            </div>

            {/* Search */}
            <div>
              <label className="block text-sm text-gray-300 mb-2">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search RFPs..."
                  className="w-full bg-dark-700 text-white border border-gray-600 rounded-lg pl-10 pr-4 py-2 focus:border-purple-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 mt-4">
            <button
              onClick={processRfps}
              disabled={loading || rfps.length === 0}
              className="px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Process Selected RFPs
            </button>
          </div>
        </div>

        {/* Website Cards */}
        {websites.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {websites.map((website, index) => (
              <div
                key={index}
                className="bg-dark-800/50 backdrop-blur border border-purple-500/30 rounded-lg p-4 hover:border-purple-400 transition-all"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">{website.name}</h3>
                  <div className={`w-3 h-3 rounded-full ${getWebsiteColor(website.base_url)}`}></div>
                </div>
                <div className="text-sm text-gray-400 mb-2">{website.base_url}</div>
                <div className="text-2xl font-bold text-purple-400">{website.rfp_count} RFPs</div>
              </div>
            ))}
          </div>
        )}

        {/* RFP List */}
        <div className="space-y-4">
          {filteredRfps.length === 0 ? (
            <div className="bg-dark-800/50 backdrop-blur border border-purple-500/30 rounded-lg p-12 text-center">
              <Globe size={48} className="mx-auto text-gray-500 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No RFPs Found</h3>
              <p className="text-gray-400 mb-4">Click "Scan Websites" to discover new RFPs</p>
            </div>
          ) : (
            filteredRfps.map((rfp) => {
              const daysUntil = getDaysUntilDeadline(rfp.submission_deadline);
              const isUrgent = daysUntil <= 7;

              return (
                <div
                  key={rfp.rfp_id}
                  className="bg-dark-800/50 backdrop-blur border border-purple-500/30 rounded-lg p-6 hover:border-purple-400 transition-all cursor-pointer"
                  onClick={() => setSelectedRfp(rfp)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 ${getWebsiteColor(rfp.website)} text-white text-xs font-medium rounded-full`}>
                          {rfp.website}
                        </span>
                        <span className="px-3 py-1 bg-blue-500/20 text-blue-300 text-xs font-medium rounded-full">
                          {rfp.category}
                        </span>
                        <span className="text-gray-400 text-sm">{rfp.rfp_id}</span>
                      </div>
                      <h3 className="text-xl font-semibold text-white mb-2">{rfp.title}</h3>
                      <p className="text-gray-300 mb-3">{rfp.buyer}</p>
                    </div>
                    <ExternalLink size={20} className="text-gray-400 hover:text-purple-400" />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center gap-2">
                      <DollarSign size={16} className="text-green-400" />
                      <div>
                        <div className="text-xs text-gray-400">Estimated Value</div>
                        <div className="text-sm font-semibold text-white">{formatCurrency(rfp.estimated_value)}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Clock size={16} className={isUrgent ? "text-red-400" : "text-blue-400"} />
                      <div>
                        <div className="text-xs text-gray-400">Deadline</div>
                        <div className={`text-sm font-semibold ${isUrgent ? "text-red-400" : "text-white"}`}>
                          {daysUntil} days left
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="text-purple-400" />
                      <div>
                        <div className="text-xs text-gray-400">Location</div>
                        <div className="text-sm font-semibold text-white">{rfp.location}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-orange-400" />
                      <div>
                        <div className="text-xs text-gray-400">Bid Type</div>
                        <div className="text-sm font-semibold text-white">{rfp.bid_type}</div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      Quantity: <span className="text-white font-medium">{rfp.quantity}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRfp(rfp);
                      }}
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all text-sm"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* RFP Detail Modal */}
        {selectedRfp && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={() => setSelectedRfp(null)}>
            <div className="bg-dark-800 border border-purple-500/30 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">{selectedRfp.title}</h2>
                    <div className="flex items-center gap-3">
                      <span className={`px-3 py-1 ${getWebsiteColor(selectedRfp.website)} text-white text-xs font-medium rounded-full`}>
                        {selectedRfp.website}
                      </span>
                      <span className="text-gray-400">{selectedRfp.rfp_id}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedRfp(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">Description</h3>
                    <p className="text-gray-300 whitespace-pre-line">{selectedRfp.description}</p>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3">Specifications</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {Object.entries(selectedRfp.specifications).map(([key, value]) => (
                        <div key={key} className="bg-dark-700/50 rounded-lg p-3">
                          <div className="text-sm text-gray-400 mb-1">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                          <div className="text-white font-medium">
                            {Array.isArray(value) ? value.join(', ') : value}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Contact</h3>
                      <p className="text-gray-300">{selectedRfp.contact}</p>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">Documents</h3>
                      <ul className="space-y-1">
                        {selectedRfp.documents.map((doc, idx) => (
                          <li key={idx} className="text-purple-400 hover:text-purple-300 cursor-pointer text-sm flex items-center gap-2">
                            <Download size={14} />
                            {doc}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcurementPortalsPage;
