import React, { useState, useEffect } from 'react'
import { FileText, TrendingUp, CheckCircle, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getDashboardAnalytics } from '../services/api'

export default function Dashboard() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      const data = await getDashboardAnalytics()
      setAnalytics(data)
    } catch (error) {
      console.error('Error loading analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    )
  }

  const stats = [
    {
      label: 'Total Products',
      value: analytics?.total_products || 0,
      icon: <FileText size={24} />,
      color: 'bg-blue-500',
    },
    {
      label: 'Total RFPs',
      value: analytics?.total_rfps || 0,
      icon: <TrendingUp size={24} />,
      color: 'bg-green-500',
    },
    {
      label: 'Processed RFPs',
      value: analytics?.processed_rfps || 0,
      icon: <CheckCircle size={24} />,
      color: 'bg-purple-500',
    },
    {
      label: 'Processing Rate',
      value: `${analytics?.processing_rate?.toFixed(1) || 0}%`,
      icon: <Clock size={24} />,
      color: 'bg-orange-500',
    },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">AI-Powered RFP Response System</h1>
        <p className="text-gray-600 mt-2">Parallel Agent Processing for Faster B2B RFP Responses</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`${stat.color} text-white p-3 rounded-lg`}>
                {stat.icon}
              </div>
            </div>
            <div>
              <p className="text-gray-600 text-sm">{stat.label}</p>
              <p className="text-3xl font-bold">{stat.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/discovery" className="p-4 border-2 border-primary-500 rounded-lg hover:bg-primary-50 transition-colors">
            <h3 className="font-semibold text-primary-700">🔍 Scan RFP Sources</h3>
            <p className="text-sm text-gray-600 mt-1">Identify new RFPs due within 3 months</p>
          </Link>
          <Link to="/processing" className="p-4 border-2 border-green-500 rounded-lg hover:bg-green-50 transition-colors">
            <h3 className="font-semibold text-green-700">⚡ Start Processing</h3>
            <p className="text-sm text-gray-600 mt-1">Begin parallel agent workflow</p>
          </Link>
          <Link to="/import" className="p-4 border-2 border-purple-500 rounded-lg hover:bg-purple-50 transition-colors">
            <h3 className="font-semibold text-purple-700">📊 Import Data</h3>
            <p className="text-sm text-gray-600 mt-1">Upload wire & cable catalog</p>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {analytics?.recent_activity?.slice(0, 5).map((activity, index) => (
            <div key={index} className="flex items-center justify-between border-b pb-3">
              <div>
                <p className="font-medium">{activity.agent_name}</p>
                <p className="text-sm text-gray-600">{activity.action}</p>
              </div>
              <span className="text-xs text-gray-500">
                {new Date(activity.timestamp).toLocaleString()}
              </span>
            </div>
          )) || <p className="text-gray-500">No recent activity</p>}
        </div>
      </div>
    </div>
  )
}
