import React, { useState } from 'react'
import { FileText, Download, Clock, CheckCircle, DollarSign } from 'lucide-react'

export default function FinalDocument() {
  const [generating, setGenerating] = useState(false)
  const [generated, setGenerated] = useState(false)

  const handleGenerate = () => {
    setGenerating(true)
    setTimeout(() => {
      setGenerating(false)
      setGenerated(true)
    }, 2000)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Step 4: Final RFP Response Document</h1>
        <p className="text-gray-600 mt-2">Generate complete submission-ready document</p>
      </div>

      {/* Approval Status */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
        <CheckCircle className="text-green-600" size={24} />
        <p className="text-green-800 font-semibold">✅ Response reviewed and approved</p>
      </div>

      {/* Generate Button */}
      {!generated && (
        <button
          onClick={handleGenerate}
          disabled={generating}
          className={`mb-6 px-6 py-3 rounded-lg font-semibold text-white transition-colors flex items-center gap-2
            ${generating ? 'bg-gray-400 cursor-not-allowed' : 'bg-primary-600 hover:bg-primary-700'}`}
        >
          <FileText size={20} />
          {generating ? 'Generating Document...' : '📄 Generate Final Document'}
        </button>
      )}

      {generating && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            <p className="text-blue-800">Generating DOCX document...</p>
          </div>
        </div>
      )}

      {generated && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800 font-semibold">✅ Document generated successfully!</p>
          </div>

          {/* Download Button */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">Download RFP Response</h2>
            <button className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2">
              <Download size={20} />
              ⬇️ Download RFP Response (DOCX)
            </button>
          </div>

          {/* Process Summary */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">Process Summary</h2>
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Clock className="mx-auto mb-2 text-blue-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Processing Time</p>
                <p className="text-2xl font-bold text-blue-600">2.3s</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle className="mx-auto mb-2 text-green-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Products Matched</p>
                <p className="text-2xl font-bold text-green-600">2</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <DollarSign className="mx-auto mb-2 text-purple-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Total Value</p>
                <p className="text-2xl font-bold text-purple-600">₹12.5L</p>
              </div>
            </div>
          </div>

          {/* Time Reduction */}
          <div className="bg-gradient-to-r from-primary-500 to-primary-700 rounded-lg shadow-lg p-6 text-white">
            <h2 className="text-xl font-bold mb-4">🎯 Time Reduction Achievement</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-primary-100 mb-1">Traditional Manual Process</p>
                <p className="text-4xl font-bold">15-25 days</p>
                <ul className="mt-3 space-y-1 text-sm text-primary-100">
                  <li>• Sequential handoffs</li>
                  <li>• Manual matching</li>
                  <li>• Knowledge silos</li>
                </ul>
              </div>
              <div>
                <p className="text-primary-100 mb-1">AI-Powered Parallel System</p>
                <p className="text-4xl font-bold">~1 hour</p>
                <ul className="mt-3 space-y-1 text-sm text-primary-100">
                  <li>• Parallel processing</li>
                  <li>• Automated matching</li>
                  <li>• Expert validation</li>
                </ul>
              </div>
            </div>
            <div className="mt-6 text-center">
              <p className="text-3xl font-bold">⚡ 80% Time Reduction</p>
              <p className="text-primary-100 mt-1">Enabling 3x increase in RFP throughput</p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
