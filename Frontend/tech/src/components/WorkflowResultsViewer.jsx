 
import React from 'react';
import { useParams } from 'react-router-dom';
import { useWorkflowResult } from '../hooks/useRFPApi';
import { FileText, DollarSign, CheckCircle, Clock, Download, Share2 } from 'lucide-react';

export default function WorkflowResultsViewer() {
  const { workflowId } = useParams();
  const { result, isLoading, error } = useWorkflowResult(workflowId);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error Loading Results</h2>
          <p className="text-red-600">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-800">No results available for this workflow yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Workflow Results</h1>
            <p className="text-gray-600">Workflow ID: <span className="font-mono text-sm">{workflowId}</span></p>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              <Download className="w-4 h-4" />
              Export PDF
            </button>
            <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
              <Share2 className="w-4 h-4" />
              Share
            </button>
          </div>
        </div>

        {/* Metadata */}
        <div className="grid grid-cols-4 gap-4">
          <MetadataCard
            icon={<FileText className="w-5 h-5" />}
            label="RFP ID"
            value={result.rfp_id}
          />
          <MetadataCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Status"
            value={result.status}
            valueClass="capitalize"
          />
          <MetadataCard
            icon={<Clock className="w-5 h-5" />}
            label="Duration"
            value={`${result.duration_seconds?.toFixed(1)}s`}
          />
          <MetadataCard
            icon={<DollarSign className="w-5 h-5" />}
            label="Total Value"
            value={result.quote?.total_amount ? `₹${result.quote.total_amount.toLocaleString()}` : 'N/A'}
          />
        </div>
      </div>

      {/* Quote Details */}
      {result.quote && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-green-600" />
            Quote Details
          </h2>

          {/* Line Items */}
          <div className="overflow-x-auto mb-4">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Product</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Quantity</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Unit Price</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {result.quote.line_items?.map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm">{item.product_name}</td>
                    <td className="px-4 py-3 text-sm">{item.quantity} {item.unit}</td>
                    <td className="px-4 py-3 text-sm text-right">₹{item.unit_price.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-right font-medium">₹{item.total_price.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 border-t-2">
                <tr>
                  <td colSpan="3" className="px-4 py-3 text-sm font-bold text-right">Total Amount:</td>
                  <td className="px-4 py-3 text-sm font-bold text-right">₹{result.quote.total_amount.toLocaleString()}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Quote Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Valid Until:</span>
              <span className="ml-2 font-medium">{new Date(result.quote.valid_until).toLocaleDateString()}</span>
            </div>
            <div>
              <span className="text-gray-600">Currency:</span>
              <span className="ml-2 font-medium">{result.quote.currency}</span>
            </div>
          </div>
        </div>
      )}

      {/* Compliance Results */}
      {result.compliance && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-blue-600" />
            Compliance Analysis
          </h2>

          <div className="space-y-4">
            {/* Overall Score */}
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium">Overall Compliance Score</span>
                  <span className="text-sm font-bold">{result.compliance.overall_score}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${
                      result.compliance.overall_score >= 80 ? 'bg-green-600' :
                      result.compliance.overall_score >= 60 ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                    style={{ width: `${result.compliance.overall_score}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Requirements */}
            {result.compliance.requirements && (
              <div>
                <h3 className="font-medium mb-2">Requirements Status</h3>
                <div className="space-y-2">
                  {result.compliance.requirements.map((req, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                      <CheckCircle className={`w-5 h-5 mt-0.5 ${req.met ? 'text-green-600' : 'text-red-600'}`} />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{req.requirement}</p>
                        {req.notes && <p className="text-sm text-gray-600 mt-1">{req.notes}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline */}
      {result.timeline && (
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Clock className="w-6 h-6 text-purple-600" />
            Delivery Timeline
          </h2>

          <div className="space-y-3">
            {result.timeline.milestones?.map((milestone, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div className="w-24 text-sm text-gray-600">{milestone.date}</div>
                <div className="flex-1">
                  <div className="font-medium">{milestone.title}</div>
                  {milestone.description && (
                    <div className="text-sm text-gray-600">{milestone.description}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stage Results */}
      {result.stage_results && Object.keys(result.stage_results).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold mb-4">Stage Results</h2>
          <div className="space-y-3">
            {Object.entries(result.stage_results).map(([stage, data]) => (
              <div key={stage} className="border-l-4 border-blue-500 pl-4 py-2">
                <div className="font-medium capitalize">{stage.replace(/_/g, ' ')}</div>
                <pre className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper component for metadata cards
function MetadataCard({ icon, label, value, valueClass = '' }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="flex items-center gap-2 text-gray-600 mb-1">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className={`text-xl font-bold ${valueClass}`}>{value}</div>
    </div>
  );
}
