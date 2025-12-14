import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, ExternalLink } from 'lucide-react'
import { scanRFPs, getLatestRFPs } from '../services/api'

export default function RFPDiscovery() {
  const [rfps, setRfps] = useState([])
  const [loading, setLoading] = useState(false)
  const [scanning, setScanning] = useState(false)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    loadLatestRFPs()
  }, [])

  const loadLatestRFPs = async () => {
    setLoading(true)
    try {
      const result = await getLatestRFPs()
      if (result.data && result.data.rfps) {
        setRfps(result.data.rfps)
      }
    } catch (error) {
      console.error('Error loading RFPs:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleScan = async () => {
    setScanning(true)
    try {
      await scanRFPs(true)
      // Wait a bit for scan to complete
      setTimeout(loadLatestRFPs, 5000)
    } catch (error) {
      console.error('Error scanning RFPs:', error)
    } finally {
      setScanning(false)
    }
  }

  const filteredRFPs = rfps.filter(rfp =>
    rfp.title?.toLowerCase().includes(filter.toLowerCase()) ||
    rfp.source?.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">RFP Discovery</h1>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50"
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

      {/* RFP List */}
      {loading ? (
        <div className="text-center py-12">Loading RFPs...</div>
      ) : (
        <div className="grid gap-4">
          {filteredRFPs.map((rfp, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold mb-2">{rfp.title}</h3>
                  <p className="text-gray-600">{rfp.source}</p>
                </div>
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                  {rfp.status}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Due Date</p>
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
