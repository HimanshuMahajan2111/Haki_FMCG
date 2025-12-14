import React, { useState } from 'react'
import { Cpu, DollarSign, Clock, CheckCircle } from 'lucide-react'

export default function Processing() {
  const [processing, setProcessing] = useState(false)
  const [complete, setComplete] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleStartProcessing = () => {
    setProcessing(true)
    setProgress(0)

    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setProcessing(false)
          setComplete(true)
          return 100
        }
        return prev + 10
      })
    }, 300)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Step 2: Parallel Agent Processing</h1>
        <p className="text-gray-600 mt-2">Technical and Pricing agents work simultaneously</p>
      </div>

      {/* Selected RFP Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="font-semibold text-blue-900">Selected RFP: Metro Rail Project - Cable Supply Package 1</p>
        <div className="flex gap-8 mt-2">
          <span className="text-blue-700">📦 Products to Match: 2</span>
          <span className="text-blue-700">📅 Days Remaining: 45</span>
        </div>
      </div>

      {/* Start Processing Button */}
      {!processing && !complete && (
        <button
          onClick={handleStartProcessing}
          className="mb-6 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
        >
          <Cpu size={20} />
          🚀 Start Parallel Processing
        </button>
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
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="text-blue-600" size={20} />
                <span className="font-semibold text-blue-900">Technical Agent</span>
              </div>
              <p className="text-sm text-blue-700">⚙️ Processing product matching...</p>
              <div className="mt-2 animate-pulse">
                <div className="h-2 bg-blue-200 rounded"></div>
              </div>
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="text-green-600" size={20} />
                <span className="font-semibold text-green-900">Pricing Agent</span>
              </div>
              <p className="text-sm text-green-700">💰 Processing cost estimation...</p>
              <div className="mt-2 animate-pulse">
                <div className="h-2 bg-green-200 rounded"></div>
              </div>
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
