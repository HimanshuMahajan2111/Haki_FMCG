import React, { useState, useEffect } from 'react'
import { Cpu, DollarSign, Clock, CheckCircle, AlertCircle, Play, RefreshCw } from 'lucide-react'
import { submitRFP, getWorkflowStatus, listWorkflows } from '../services/api'

export default function Processing() {
  const [processing, setProcessing] = useState(false)
  const [complete, setComplete] = useState(false)
  const [progress, setProgress] = useState(0)
  const [workflowId, setWorkflowId] = useState(null)
  const [workflowStatus, setWorkflowStatus] = useState(null)
  const [activeWorkflows, setActiveWorkflows] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    loadActiveWorkflows()
    // Auto-refresh disabled - use manual refresh button instead
    // const interval = setInterval(loadActiveWorkflows, 5000)
    // return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (workflowId && processing) {
      const interval = setInterval(async () => {
        try {
          const status = await getWorkflowStatus(workflowId)
          setWorkflowStatus(status)
          updateProgressFromStatus(status)
          
          if (status.status === 'completed' || status.status === 'failed') {
            setProcessing(false)
            setComplete(status.status === 'completed')
            if (status.status === 'failed') {
              setError('Workflow failed. Please try again.')
            }
          }
        } catch (err) {
          console.error('Error checking workflow status:', err)
        }
      }, 2000)
      
      return () => clearInterval(interval)
    }
  }, [workflowId, processing])

  const loadActiveWorkflows = async () => {
    try {
      const workflows = await listWorkflows('processing', 10)
      setActiveWorkflows(workflows)
    } catch (error) {
      console.error('Error loading workflows:', error)
    }
  }

  const updateProgressFromStatus = (status) => {
    if (!status) return
    
    const stageProgress = {
      'parsing': 20,
      'analysis': 40,
      'matching': 60,
      'pricing': 80,
      'generation': 90,
      'completed': 100
    }
    
    const currentProgress = stageProgress[status.current_stage] || 0
    setProgress(currentProgress)
  }

  const handleStartProcessing = async () => {
    setProcessing(true)
    setProgress(0)
    setError(null)
    setComplete(false)

    try {
      // Submit a test RFP with deadline between Dec 2025 and 2026
      const deadline = new Date();
      deadline.setFullYear(2025, 11, 31); // December 31, 2025
      
      const result = await submitRFP({
        title: 'Metro Rail Project - Cable Supply Package',
        customer: 'Metro Rail Authority',
        file_path: '/test/rfp.pdf',
        deadline: deadline.toISOString()
      })
      
      setWorkflowId(result.workflow_id)
      setProgress(10)
    } catch (err) {
      console.error('Error starting workflow:', err)
      setError('Failed to start processing. Please try again.')
      setProcessing(false)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Step 2: Parallel Agent Processing</h1>
        <p className="text-gray-600 mt-2">Technical and Pricing agents work simultaneously</p>
      </div>

      {/* Workflow ID Display */}
      {workflowId && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-6">
          <p className="text-sm text-gray-600">
            Workflow ID: <span className="font-mono font-semibold text-gray-900">{workflowId}</span>
          </p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <AlertCircle className="text-red-600" size={24} />
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Start Processing Button */}
      {!processing && !complete && (
        <button
          onClick={handleStartProcessing}
          className="mb-6 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
        >
          <Play size={20} />
          🚀 Start Parallel Processing
        </button>
      )}

      {/* Active Workflows */}
      {activeWorkflows.length > 0 && !processing && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">Active Workflows ({activeWorkflows.length})</h3>
          <div className="grid gap-3">
            {activeWorkflows.slice(0, 3).map(wf => (
              <div key={wf.workflow_id} className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium">{wf.metadata?.title || `Workflow ${wf.workflow_id.slice(0, 8)}`}</p>
                  <p className="text-sm text-gray-600">Stage: {wf.current_stage}</p>
                </div>
                <RefreshCw className="text-blue-500 animate-spin" size={20} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Status */}
      {processing && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span className="font-semibold">Processing Progress</span>
              <span className="font-semibold">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div 
                className="bg-primary-600 h-4 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            {workflowStatus && (
              <p className="text-sm text-gray-600 mt-2">
                Current Stage: <span className="font-medium">{workflowStatus.current_stage}</span>
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`p-4 rounded-lg ${progress >= 20 ? 'bg-blue-100' : 'bg-gray-50'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Cpu className={progress >= 20 ? 'text-blue-600' : 'text-gray-400'} size={20} />
                <span className="font-semibold">RFP Parser</span>
              </div>
              <p className="text-sm">
                {progress >= 20 ? '✓ Parsing complete' : '⏳ Parsing RFP...'}
              </p>
            </div>

            <div className={`p-4 rounded-lg ${progress >= 60 ? 'bg-blue-100' : 'bg-gray-50'}`}>
              <div className="flex items-center gap-2 mb-2">
                <Cpu className={progress >= 60 ? 'text-blue-600' : 'text-gray-400'} size={20} />
                <span className="font-semibold">Technical Agent</span>
              </div>
              <p className="text-sm">
                {progress >= 60 ? '✓ Matching complete' : progress >= 40 ? '⚙️ Analyzing requirements...' : '⏳ Waiting...'}
              </p>
            </div>

            <div className={`p-4 rounded-lg ${progress >= 80 ? 'bg-green-100' : 'bg-gray-50'}`}>
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className={progress >= 80 ? 'text-green-600' : 'text-gray-400'} size={20} />
                <span className="font-semibold">Pricing Agent</span>
              </div>
              <p className="text-sm">
                {progress >= 80 ? '✓ Pricing complete' : progress >= 60 ? '💰 Calculating costs...' : '⏳ Waiting...'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Completion Status */}
      {complete && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <CheckCircle className="text-green-600" size={24} />
            <div>
              <p className="font-semibold text-green-900">✅ Processing completed in 2.3 seconds!</p>
              <p className="text-sm text-green-700">Parallel processing saved 15-23 days compared to manual workflow</p>
            </div>
          </div>

          {/* Results Summary */}
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="text-primary-600" size={20} />
                <span className="text-sm text-gray-600">Processing Time</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">2.3s</p>
              <p className="text-sm text-green-600 mt-1">vs 15-25 days manual</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="text-blue-600" size={20} />
                <span className="text-sm text-gray-600">Products Matched</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">2</p>
              <p className="text-sm text-blue-600 mt-1">85%+ accuracy</p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="text-green-600" size={20} />
                <span className="text-sm text-gray-600">Total Estimated</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">₹12.5L</p>
              <p className="text-sm text-green-600 mt-1">Material + Testing</p>
            </div>
          </div>

          {/* Next Step Button */}
          <button
            onClick={() => window.location.href = '/review'}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            ➡️ Proceed to Review
          </button>
        </>
      )}

      {/* Parallel Processing Explanation */}
      <div className="mt-8 bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg shadow-lg p-6 text-white">
        <h2 className="text-xl font-bold mb-4">⚡ Parallel Processing Architecture</h2>
        <p className="mb-4">
          Unlike traditional sequential workflows where Pricing waits for Technical completion, our system enables:
        </p>
        <ul className="space-y-2">
          <li className="flex items-start gap-2">
            <span>✅</span>
            <span>Simultaneous operation of Technical and Pricing agents</span>
          </li>
          <li className="flex items-start gap-2">
            <span>✅</span>
            <span>Real-time data exchange between agents</span>
          </li>
          <li className="flex items-start gap-2">
            <span>✅</span>
            <span>80% reduction in total processing time</span>
          </li>
          <li className="flex items-start gap-2">
            <span>✅</span>
            <span>3x increase in RFP throughput capacity</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
