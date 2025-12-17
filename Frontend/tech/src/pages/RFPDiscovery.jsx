import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, ExternalLink, AlertCircle, CheckCircle, Clock } from 'lucide-react'
import { getDashboard, getLatestRFPs, scanRFPs } from '../services/api'

export default function RFPDiscovery() {
  const [rfps, setRfps] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    loadRFPs()
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(loadRFPs, 30000)
    // return () => clearInterval(interval)
  }, [])

  const loadRFPs = async () => {
    setLoading(true)
    try {
      const [dashData, rfpData] = await Promise.all([
        getDashboard(7).catch(() => ({ rfp_processing: { total_rfps: 0 } })),
        getLatestRFPs().catch(() => ({ data: { rfps: [] } }))
      ])
      
      setStats(dashData.rfp_processing)
      
      // Use real RFP data from API
      const rfpList = (rfpData.data?.rfps || []).map(rfp => ({
        id: rfp.id,
        title: rfp.title,
        customer: rfp.source || 'Unknown',
        status: rfp.status,
        created_at: rfp.created_at,
        due_date: rfp.due_date,
        days_remaining: rfp.days_remaining,
        source: rfp.source || 'Manual Upload',
        estimated_value: null,
        priority_score: null
      }))
      setRfps(rfpList)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      // Trigger real RFP scan API
      await scanRFPs(false)
      // Wait a moment for scan to start, then reload
      setTimeout(() => {
        loadRFPs()
      }, 2000)
    } catch (error) {
      console.error('Error scanning RFPs:', error)
    } finally {
      setScanning(false)
    }
  }

  const filteredRFPs = rfps.filter(rfp =>
    rfp.title?.toLowerCase().includes(filter.toLowerCase()) ||
    rfp.source?.toLowerCase().includes(filter.toLowerCase()) ||
    rfp.customer?.toLowerCase().includes(filter.toLowerCase())
  )

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={20} />
      case 'in_progress': case 'processing': return <Clock className="text-blue-500" size={20} />
      case 'failed': case 'error': return <AlertCircle className="text-red-500" size={20} />
      default: return <Clock className="text-gray-500" size={20} />
    }
  }

  const getStatusBadge = (status) => {
    const colors = {
      completed: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      processing: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      error: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="p-8 animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">RFP Discovery</h1>
          <p className="text-dark-400 mt-2">Discover and track RFP opportunities</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="bg-gradient-to-r from-primary-600 to-primary-500 text-white px-6 py-3 rounded-xl hover:from-primary-500 hover:to-primary-400 flex items-center gap-2 disabled:opacity-50 shadow-lg shadow-primary-500/30 transition-all"
        >
          <RefreshCw size={20} className={scanning ? 'animate-spin' : ''} />
          {scanning ? 'Scanning...' : 'Scan RFPs'}
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-3 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search RFPs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total RFPs</p>
            <p className="text-2xl font-bold">{stats.total_rfps || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Active</p>
            <p className="text-2xl font-bold text-blue-600">{stats.processing || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Completed</p>
            <p className="text-2xl font-bold text-green-600">{stats.completed || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-2xl font-bold text-purple-600">
              {stats.total_rfps > 0 ? Math.round((stats.completed / stats.total_rfps) * 100) : 0}%
            </p>
          </div>
        </div>
      )}

      {/* RFP List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading RFPs...</p>
        </div>
      ) : filteredRFPs.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">No RFPs found. Click "Scan RFPs" to discover new opportunities.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredRFPs.map((rfp, index) => (
            <div key={rfp.id || index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-start gap-3 flex-1">
                  {getStatusIcon(rfp.status)}
                  <div>
                    <h3 className="text-xl font-bold mb-1">{rfp.title}</h3>
                    <p className="text-gray-600 text-sm">Customer: {rfp.customer}</p>
                    <p className="text-gray-500 text-sm">Source: {rfp.source}</p>
                  </div>
                </div>
                <div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(rfp.status)}`}>
                    {rfp.status?.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Created</p>
                  <p className="font-medium">{rfp.created_at ? new Date(rfp.created_at).toLocaleDateString() : 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Deadline</p>
                  <p className="font-medium">{rfp.due_date}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Days Remaining</p>
                  <p className="font-medium">{rfp.days_remaining} days</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Estimated Value</p>
                  <p className="font-medium">{rfp.estimated_value}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Priority Score</p>
                  <p className="font-medium text-blue-600">{rfp.priority_score}</p>
                </div>
              </div>

              <div className="flex justify-end">
                <button className="text-blue-600 hover:text-blue-800 flex items-center gap-2">
                  View Details <ExternalLink size={16} />
                </button>
              </div>
            </div>
          ))}
          {filteredRFPs.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No RFPs found. Click "Scan RFPs" to discover new opportunities.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
