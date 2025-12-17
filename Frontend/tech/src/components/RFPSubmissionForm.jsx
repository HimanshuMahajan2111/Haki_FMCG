 
import React, { useState } from 'react';
import { useSubmitRFP, useWorkflowStatus } from '../hooks/useRFPApi';
import { FileText, Upload, CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function RFPSubmissionForm() {
  const [formData, setFormData] = useState({
    rfp_id: '',
    customer_id: '',
    document: '',
    priority: 'normal',
    estimated_value: '',
    deadline: ''
  });

  const [workflowId, setWorkflowId] = useState(null);
  const { submitRFP, isSubmitting, error: submitError, data: submitData } = useSubmitRFP();
  const { status, error: statusError } = useWorkflowStatus(workflowId, {
    refetchInterval: 3000, // Check every 3 seconds
    stopOnComplete: true
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      await submitRFP(
        {
          rfp_id: formData.rfp_id || `RFP-${Date.now()}`,
          customer_id: formData.customer_id,
          document: formData.document,
          priority: formData.priority,
          estimated_value: parseFloat(formData.estimated_value) || null,
          deadline: formData.deadline || null,
          metadata: {
            submitted_from: 'web_ui',
            timestamp: new Date().toISOString()
          }
        },
        {
          onSuccess: (data) => {
            setWorkflowId(data.workflow_id);
            console.log('RFP submitted successfully:', data);
          }
        }
      );
    } catch (err) {
      console.error('Submission failed:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <FileText className="w-6 h-6" />
        Submit New RFP
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg shadow">
        <div>
          <label className="block text-sm font-medium mb-2">RFP ID (optional)</label>
          <input
            type="text"
            name="rfp_id"
            value={formData.rfp_id}
            onChange={handleInputChange}
            placeholder="Auto-generated if empty"
            className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Customer ID *</label>
          <input
            type="text"
            name="customer_id"
            value={formData.customer_id}
            onChange={handleInputChange}
            required
            className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">RFP Document *</label>
          <textarea
            name="document"
            value={formData.document}
            onChange={handleInputChange}
            required
            rows={6}
            placeholder="Paste RFP content or requirements..."
            className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Priority</label>
            <select
              name="priority"
              value={formData.priority}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
            >
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Estimated Value</label>
            <input
              type="number"
              name="estimated_value"
              value={formData.estimated_value}
              onChange={handleInputChange}
              placeholder="0.00"
              step="0.01"
              className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Deadline</label>
          <input
            type="datetime-local"
            name="deadline"
            value={formData.deadline}
            onChange={handleInputChange}
            min="2025-01-01T00:00"
            max="2026-12-31T23:59"
            className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {submitError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Submission Failed</p>
              <p className="text-sm text-red-600">{submitError.message}</p>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Submit RFP
            </>
          )}
        </button>
      </form>

      {/* Workflow Status Display */}
      {submitData && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Workflow Status</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Workflow ID:</span>
              <code className="text-sm bg-gray-100 px-2 py-1 rounded">{submitData.workflow_id}</code>
            </div>

            {status && (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Status:</span>
                  <StatusBadge status={status.status} />
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Current Stage:</span>
                  <span className="text-sm font-medium">{status.current_stage}</span>
                </div>

                {status.stages_completed && status.stages_completed.length > 0 && (
                  <div>
                    <span className="text-sm text-gray-600 block mb-2">Completed Stages:</span>
                    <div className="flex flex-wrap gap-2">
                      {status.stages_completed.map((stage) => (
                        <span
                          key={stage}
                          className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded flex items-center gap-1"
                        >
                          <CheckCircle className="w-3 h-3" />
                          {stage}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {status.duration_seconds && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Duration:</span>
                    <span className="text-sm">{status.duration_seconds.toFixed(2)}s</span>
                  </div>
                )}

                {status.status === 'completed' && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
                    <p className="text-green-800 font-medium flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Workflow completed successfully!
                    </p>
                  </div>
                )}
              </>
            )}

            {statusError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded">
                <p className="text-sm text-red-600">{statusError.message}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }) {
  const statusColors = {
    submitted: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800'
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
}
