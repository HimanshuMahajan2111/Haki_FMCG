import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Zap, Upload, TrendingUp, Clock, CheckCircle, Activity } from 'lucide-react'
import Overview from '../components/Overview'
import Analytics from '../components/Analytics'
import { PageHeader, Card, CardBody, Button } from '../components/UI'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview')

  const quickActions = [
    {
      to: '/discovery',
      icon: <Search size={24} className="text-white" />,
      title: 'Scan RFP Sources',
      description: 'Discover new RFPs due within 3 months',
      color: 'from-primary-600 to-primary-500',
      hoverColor: 'hover:shadow-primary-500/30'
    },
    {
      to: '/processing',
      icon: <Zap size={24} className="text-white" />,
      title: 'Start Processing',
      description: 'Begin parallel agent workflow',
      color: 'from-success-600 to-success-500',
      hoverColor: 'hover:shadow-success-500/30'
    },
    {
      to: '/import',
      icon: <Upload size={24} className="text-white" />,
      title: 'Import Data',
      description: 'Upload wire & cable catalog',
      color: 'from-secondary-600 to-secondary-500',
      hoverColor: 'hover:shadow-secondary-500/30'
    }
  ]

  return (
    <div className="p-8 animate-fade-in">
      <PageHeader
        title="AI-Powered RFP Response System"
        subtitle="Parallel Agent Processing for Faster B2B RFP Responses"
        action={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-4 py-2 bg-dark-800/50 rounded-xl border border-dark-700/50">
              <Activity size={16} className="text-success-400 animate-pulse" />
              <span className="text-sm text-dark-300">System Online</span>
            </div>
          </div>
        }
      />

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-primary-400" />
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, index) => (
            <Link
              key={index}
              to={action.to}
              className="group relative"
            >
              <Card hover className={`${action.hoverColor} overflow-hidden`}>
                <CardBody className="relative">
                  <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${action.color} opacity-10 rounded-full blur-3xl -mr-16 -mt-16 group-hover:opacity-20 transition-opacity`}></div>
                  <div className="relative z-10">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center shadow-lg mb-4 group-hover:scale-110 transition-transform`}>
                      {action.icon}
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-primary-400 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-dark-400 text-sm">
                      {action.description}
                    </p>
                  </div>
                </CardBody>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <Card className="p-2">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 px-6 py-3 font-medium rounded-xl transition-all ${
                activeTab === 'overview'
                  ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/30'
                  : 'text-dark-300 hover:text-white hover:bg-dark-800/50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Clock size={18} />
                Overview
              </div>
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex-1 px-6 py-3 font-medium rounded-xl transition-all ${
                activeTab === 'analytics'
                  ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/30'
                  : 'text-dark-300 hover:text-white hover:bg-dark-800/50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Activity size={18} />
                Analytics
              </div>
            </button>
          </div>
        </Card>
      </div>

      {/* Content */}
      <div className="animate-slide-up">
        {activeTab === 'overview' && <Overview />}
        {activeTab === 'analytics' && <Analytics />}
      </div>
    </div>
  )
}
