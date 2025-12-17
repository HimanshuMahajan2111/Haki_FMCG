import React, { useState, useEffect } from 'react'
import { 
  RefreshCw, Database, Search, CheckCircle, AlertCircle, 
  FileText, Upload, Download, Trash2, Eye, Settings,
  Activity, Zap, Server, BarChart3 
} from 'lucide-react'
import { 
  scanRFPs, getLatestRFPs, getRFPHistory, processRFP,
  getProducts, searchProducts, getAgentLogs,
  healthCheck, exportAnalytics, clearCache
} from '../services/api'
import RFPDetailsModal from '../components/RFPDetailsModal'

export default function SystemManagement() {
  const [activeTab, setActiveTab] = useState('rfp-scan')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  
  // RFP Scan State
  const [latestRFPs, setLatestRFPs] = useState([])
  const [rfpHistory, setRFPHistory] = useState([])
  const [scanning, setScanning] = useState(false)
  const [selectedRFP, setSelectedRFP] = useState(null)
  
  // Product State
  const [products, setProducts] = useState([])
  const [productSearch, setProductSearch] = useState('')
  const [searchResults, setSearchResults] = useState([])
  
  // Agent Logs State
  const [agentLogs, setAgentLogs] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  
  // System Health State
  const [systemHealth, setSystemHealth] = useState(null)
  
  useEffect(() => {
    // Initial load only - use manual refresh buttons to reload
    loadRFPData()
    // Removed auto-reload on tab change to prevent annoying reloads
  }, [])
  
  // ==================== RFP Functions ====================
  const loadRFPData = async () => {
    setLoading(true)
    try {
      const [latest, history] = await Promise.all([
        getLatestRFPs().catch(() => ({ data: { rfps: [] } })),
        getRFPHistory().catch(() => ({ data: { history: [] } }))
      ])
      setLatestRFPs(latest.data?.rfps || [])
      setRFPHistory(history.data?.history || [])
      setMessage({ type: 'success', text: 'RFP data loaded successfully' })
    } catch (error) {
      console.error('Error loading RFP data:', error)
      setMessage({ type: 'error', text: 'Failed to load RFP data' })
    } finally {
      setLoading(false)
    }
  }
  
  const handleScanRFPs = async (forceRescan = false) => {
    setScanning(true)
    setMessage({ type: 'info', text: 'Scanning RFP directory...' })
    try {
      const result = await scanRFPs(forceRescan)
      setMessage({ type: 'success', text: result.message || 'RFP scan completed' })
      setTimeout(() => loadRFPData(), 2000)
    } catch (error) {
      console.error('Error scanning RFPs:', error)
      setMessage({ type: 'error', text: 'Failed to scan RFPs' })
    } finally {
      setScanning(false)
    }
  }
  
  const handleProcessRFP = async (rfpId) => {
    try {
      setMessage({ type: 'info', text: 'Starting RFP analysis...' })
      const response = await fetch(`http://localhost:8000/api/rfp/analyze/${rfpId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const result = await response.json()
        setMessage({ type: 'success', text: `${result.message} - ${result.estimated_time}` })
        setTimeout(loadRFPData, 3000)
      } else {
        throw new Error('Analysis failed')
      }
    } catch (error) {
      console.error('Error processing RFP:', error)
      setMessage({ type: 'error', text: 'Failed to process RFP' })
    }
  }
  
  // ==================== Product Functions ====================
  const loadProducts = async () => {
    setLoading(true)
    try {
      const result = await getProducts(0, 50)
      setProducts(result.data || [])
      setMessage({ type: 'success', text: `Loaded ${result.data?.length || 0} products` })
    } catch (error) {
      console.error('Error loading products:', error)
      setMessage({ type: 'error', text: 'Failed to load products' })
    } finally {
      setLoading(false)
    }
  }
  
  const handleSearchProducts = async () => {
    if (!productSearch.trim()) {
      setSearchResults([])
      return
    }
    
    setLoading(true)
    try {
      const result = await searchProducts(productSearch, 20)
      setSearchResults(result.results || [])
      setMessage({ type: 'success', text: `Found ${result.results?.length || 0} matching products` })
    } catch (error) {
      console.error('Error searching products:', error)
      setMessage({ type: 'error', text: 'Failed to search products' })
    } finally {
      setLoading(false)
    }
  }
  
  // ==================== Agent Functions ====================
  const loadAgentLogs = async (agentName = null) => {
    setLoading(true)
    try {
      const result = await getAgentLogs(agentName, 100)
      setAgentLogs(result.logs || [])
      setMessage({ type: 'success', text: `Loaded ${result.logs?.length || 0} agent logs` })
    } catch (error) {
      console.error('Error loading agent logs:', error)
      setMessage({ type: 'error', text: 'Failed to load agent logs' })
    } finally {
      setLoading(false)
    }
  }
  
  // ==================== System Functions ====================
  const checkSystemHealth = async () => {
    setLoading(true)
    try {
      const result = await healthCheck()
      setSystemHealth(result)
      setMessage({ type: 'success', text: `System is ${result.status}` })
    } catch (error) {
      console.error('Error checking health:', error)
      setMessage({ type: 'error', text: 'Failed to check system health' })
    } finally {
      setLoading(false)
    }
  }
  
  const handleExportAnalytics = async () => {
    try {
      setMessage({ type: 'info', text: 'Exporting analytics...' })
      const result = await exportAnalytics()
      // Trigger download
      const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analytics_export_${new Date().toISOString()}.json`
      a.click()
      setMessage({ type: 'success', text: 'Analytics exported successfully' })
    } catch (error) {
      console.error('Error exporting analytics:', error)
      setMessage({ type: 'error', text: 'Failed to export analytics' })
    }
  }
  
  const handleClearCache = async () => {
    if (!confirm('Are you sure you want to clear the cache?')) return
    
    try {
      setMessage({ type: 'info', text: 'Clearing cache...' })
      await clearCache()
      setMessage({ type: 'success', text: 'Cache cleared successfully' })
    } catch (error) {
      console.error('Error clearing cache:', error)
      setMessage({ type: 'error', text: 'Failed to clear cache' })
    }
  }
  
  // ==================== Render Functions ====================
  const renderMessage = () => {
    if (!message) return null
    
    const colors = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    }
    
    const icons = {
      success: <CheckCircle size={20} />,
      error: <AlertCircle size={20} />,
      info: <Activity size={20} />
    }
    
    return (
      <div className={`${colors[message.type]} border rounded-lg p-4 mb-4 flex items-center gap-3`}>
        {icons[message.type]}
        <span>{message.text}</span>
      </div>
    )
  }
  
  const renderRFPScan = () => (
    <div className="space-y-6">
      <div className="flex gap-4">
        <button
          onClick={() => handleScanRFPs(false)}
          disabled={scanning}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <RefreshCw size={20} className={scanning ? 'animate-spin' : ''} />
          {scanning ? 'Scanning...' : 'Scan RFP Directory'}
        </button>
        <button
          onClick={() => handleScanRFPs(true)}
          disabled={scanning}
          className="flex-1 bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Zap size={20} />
          Force Rescan All
        </button>
      </div>
      
      {/* Latest RFPs */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <FileText size={24} />
          Latest Discovered RFPs ({latestRFPs.length})
        </h3>
        {latestRFPs.length === 0 ? (
          <p className="text-gray-500">No RFPs found. Click "Scan RFP Directory" to discover new RFPs.</p>
        ) : (
          <div className="space-y-3">
            {latestRFPs.map(rfp => (
              <div 
                key={rfp.id} 
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedRFP(rfp)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h4 className="font-bold text-lg hover:text-blue-600 transition-colors">{rfp.title}</h4>
                    <p className="text-sm text-gray-600">Source: {rfp.source}</p>
                    <p className="text-sm text-gray-600">Created: {new Date(rfp.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      rfp.status === 'discovered' ? 'bg-yellow-100 text-yellow-800' :
                      rfp.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {rfp.status}
                    </span>
                    {rfp.status === 'discovered' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleProcessRFP(rfp.id);
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded text-sm"
                      >
                        Process
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedRFP(rfp);
                      }}
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm"
                    >
                      <Eye size={16} />
                      View Details
                    </button>
                  </div>
                </div>
                {rfp.due_date && (
                  <p className="text-sm mt-2">
                    <span className="font-semibold">Due Date:</span> {new Date(rfp.due_date).toLocaleDateString()}
                    {rfp.days_remaining && ` (${rfp.days_remaining} days remaining)`}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* RFP History */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <BarChart3 size={24} />
          Processing History ({rfpHistory.length})
        </h3>
        {rfpHistory.length === 0 ? (
          <p className="text-gray-500">No processing history available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Title</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Processed</th>
                  <th className="px-4 py-2 text-left">Time (s)</th>
                  <th className="px-4 py-2 text-left">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {rfpHistory.map(rfp => (
                  <tr key={rfp.id} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-2">{rfp.title}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        rfp.status === 'approved' ? 'bg-green-100 text-green-800' :
                        rfp.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {rfp.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-sm">{rfp.processed_at ? new Date(rfp.processed_at).toLocaleString() : 'N/A'}</td>
                    <td className="px-4 py-2">{rfp.processing_time || 'N/A'}</td>
                    <td className="px-4 py-2">{rfp.confidence_score ? `${(rfp.confidence_score * 100).toFixed(1)}%` : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
  
  const renderProducts = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Search size={24} />
          Product Search
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearchProducts()}
            placeholder="Search products by name, SKU, or description..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSearchProducts}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Search
          </button>
        </div>
        
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="font-semibold">Search Results: {searchResults.length}</p>
            {searchResults.map((product, idx) => (
              <div key={idx} className="border rounded p-3 hover:bg-gray-50">
                <p className="font-bold">{product.name || product.product_name}</p>
                <p className="text-sm text-gray-600">SKU: {product.sku || product.product_code}</p>
                <p className="text-sm text-gray-600">Category: {product.category}</p>
                {product.score && <p className="text-sm text-blue-600">Match Score: {(product.score * 100).toFixed(1)}%</p>}
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Database size={24} />
          Product Database ({products.length})
        </h3>
        <button
          onClick={loadProducts}
          className="mb-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
        
        {products.length === 0 ? (
          <p className="text-gray-500">No products loaded. Click Refresh to load products.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">SKU</th>
                  <th className="px-3 py-2 text-left">Name</th>
                  <th className="px-3 py-2 text-left">Category</th>
                  <th className="px-3 py-2 text-left">Brand</th>
                  <th className="px-3 py-2 text-left">Price</th>
                </tr>
              </thead>
              <tbody>
                {products.slice(0, 20).map((product, idx) => (
                  <tr key={idx} className="border-t hover:bg-gray-50">
                    <td className="px-3 py-2">{product.sku || product.product_code}</td>
                    <td className="px-3 py-2">{product.name || product.product_name}</td>
                    <td className="px-3 py-2">{product.category}</td>
                    <td className="px-3 py-2">{product.brand}</td>
                    <td className="px-3 py-2">{product.price ? `₹${product.price}` : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
  
  const renderAgents = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Activity size={24} />
          Agent Logs
        </h3>
        
        <div className="flex gap-2 mb-4">
          <select
            value={selectedAgent || ''}
            onChange={(e) => {
              setSelectedAgent(e.target.value || null)
              loadAgentLogs(e.target.value || null)
            }}
            className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Agents</option>
            <option value="sales_agent">Sales Agent</option>
            <option value="technical_agent">Technical Agent</option>
            <option value="pricing_agent">Pricing Agent</option>
            <option value="rfp_parser_agent">RFP Parser Agent</option>
            <option value="response_generator_agent">Response Generator</option>
          </select>
          <button
            onClick={() => loadAgentLogs(selectedAgent)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
        
        {agentLogs.length === 0 ? (
          <p className="text-gray-500">No agent logs available.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {agentLogs.map((log, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 bg-gray-50 p-3 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold text-sm">{log.agent_name}</p>
                    <p className="text-xs text-gray-600">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    log.level === 'error' ? 'bg-red-100 text-red-800' :
                    log.level === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {log.level}
                  </span>
                </div>
                <p className="text-sm mt-2">{log.message}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
  
  const renderSystem = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Server size={24} />
          System Health
        </h3>
        
        <button
          onClick={checkSystemHealth}
          className="mb-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <RefreshCw size={16} />
          Check Health
        </button>
        
        {systemHealth && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
              <CheckCircle size={32} className="text-green-600" />
              <div>
                <p className="font-bold text-lg">Status: {systemHealth.status}</p>
                <p className="text-sm text-gray-600">Version: {systemHealth.version}</p>
                <p className="text-sm text-gray-600">Active Workflows: {systemHealth.active_workflows}</p>
              </div>
            </div>
            
            {systemHealth.features && (
              <div>
                <p className="font-semibold mb-2">Features:</p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(systemHealth.features).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 text-sm">
                      {value ? <CheckCircle size={16} className="text-green-600" /> : <AlertCircle size={16} className="text-gray-400" />}
                      <span>{key.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Settings size={24} />
          System Operations
        </h3>
        
        <div className="space-y-3">
          <button
            onClick={handleExportAnalytics}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg flex items-center justify-center gap-2"
          >
            <Download size={20} />
            Export Analytics Data
          </button>
          
          <button
            onClick={handleClearCache}
            className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-3 rounded-lg flex items-center justify-center gap-2"
          >
            <Trash2 size={20} />
            Clear System Cache
          </button>
        </div>
      </div>
    </div>
  )
  
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">🔧 System Management</h1>
        <p className="text-gray-600 mt-2">Manage RFPs, products, agents, and system settings</p>
      </div>
      
      {renderMessage()}
      
      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('rfp-scan')}
            className={`px-6 py-4 font-semibold flex items-center gap-2 ${
              activeTab === 'rfp-scan' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'
            }`}
          >
            <FileText size={20} />
            RFP Scan
          </button>
          <button
            onClick={() => setActiveTab('products')}
            className={`px-6 py-4 font-semibold flex items-center gap-2 ${
              activeTab === 'products' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'
            }`}
          >
            <Database size={20} />
            Products
          </button>
          <button
            onClick={() => setActiveTab('agents')}
            className={`px-6 py-4 font-semibold flex items-center gap-2 ${
              activeTab === 'agents' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'
            }`}
          >
            <Activity size={20} />
            Agent Logs
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`px-6 py-4 font-semibold flex items-center gap-2 ${
              activeTab === 'system' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'
            }`}
          >
            <Server size={20} />
            System Health
          </button>
        </div>
      </div>
      
      {/* Tab Content */}
      {loading && !scanning && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      )}
      
      {!loading && activeTab === 'rfp-scan' && renderRFPScan()}
      {!loading && activeTab === 'products' && renderProducts()}
      {!loading && activeTab === 'agents' && renderAgents()}
      {!loading && activeTab === 'system' && renderSystem()}

      {/* RFP Details Modal */}
      {selectedRFP && (
        <RFPDetailsModal 
          rfp={selectedRFP} 
          onClose={() => setSelectedRFP(null)}
        />
      )}
    </div>
  )
}
