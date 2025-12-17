import React, { useState, useEffect } from 'react';
import { X, Calendar, FileText, Tag, TrendingUp, CheckCircle, Clock, AlertCircle, Loader, Package, TestTube, Award, FileCheck, DollarSign } from 'lucide-react';

const RFPDetailsModal = ({ rfp, onClose }) => {
  const [extractedData, setExtractedData] = useState(null);
  const [loadingExtraction, setLoadingExtraction] = useState(false);
  
  if (!rfp) return null;

  console.log('RFP Modal Data:', rfp);
  
  // Fetch extracted PDF data when modal opens
  useEffect(() => {
    const fetchExtractedData = async () => {
      if (!rfp.id) return;
      
      setLoadingExtraction(true);
      try {
        const response = await fetch(`http://localhost:8000/api/rfp/extract/${rfp.id}`);
        if (response.ok) {
          const data = await response.json();
          setExtractedData(data.extracted_data);
        }
      } catch (error) {
        console.error('Failed to fetch extracted data:', error);
      } finally {
        setLoadingExtraction(false);
      }
    };
    
    fetchExtractedData();
  }, [rfp.id]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    const statusStr = status?.toLowerCase() || 'pending';
    const colors = {
      completed: 'bg-green-100 text-green-800 border-green-300',
      processing: 'bg-blue-100 text-blue-800 border-blue-300',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      failed: 'bg-red-100 text-red-800 border-red-300',
      discovered: 'bg-purple-100 text-purple-800 border-purple-300'
    };
    return colors[statusStr] || colors.pending;
  };

  const getStatusIcon = (status) => {
    const statusStr = status?.toLowerCase() || 'pending';
    const icons = {
      completed: CheckCircle,
      processing: TrendingUp,
      pending: Clock,
      failed: AlertCircle,
      discovered: FileText
    };
    const Icon = icons[statusStr] || Clock;
    return <Icon size={18} />;
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }}
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <FileText size={28} />
                <h2 className="text-2xl font-bold">{rfp.title || rfp.name || 'RFP Details'}</h2>
              </div>
              <div className="flex items-center gap-4 text-blue-100 text-sm">
                {rfp.source && (
                  <span className="flex items-center gap-1">
                    <Tag size={14} />
                    {rfp.source}
                  </span>
                )}
                {rfp.id && (
                  <span>ID: {rfp.id}</span>
                )}
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-180px)] p-6">
          {/* Always show basic info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800">
              <strong>Viewing RFP:</strong> {rfp.title || rfp.name || 'No title available'}
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Check browser console (F12) for full data structure
            </p>
          </div>

          {/* Status and Key Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Status */}
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">Status</p>
              <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${getStatusColor(rfp.status)}`}>
                {getStatusIcon(rfp.status)}
                <span className="font-semibold capitalize">{rfp.status || 'Pending'}</span>
              </div>
            </div>

            {/* Created Date */}
            {(rfp.created_at || rfp.createdAt) && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-2">Created</p>
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-blue-600" />
                  <span className="font-semibold">{formatDate(rfp.created_at || rfp.createdAt)}</span>
                </div>
              </div>
            )}

            {/* Due Date */}
            {rfp.due_date && (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-2">Due Date</p>
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-red-600" />
                  <span className="font-semibold">{formatDate(rfp.due_date)}</span>
                </div>
              </div>
            )}
          </div>

          {/* Loading Extraction */}
          {loadingExtraction && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-4 flex items-center gap-3">
              <Loader className="animate-spin text-blue-600" size={24} />
              <div>
                <p className="font-medium text-blue-900">Extracting PDF Data...</p>
                <p className="text-sm text-blue-700">Analyzing RFP document structure</p>
              </div>
            </div>
          )}

          {/* Extracted PDF Data */}
          {extractedData && !loadingExtraction && (
            <div className="space-y-4 mb-6">
              {/* BOQ Summary */}
              {extractedData.boq_summary && Object.keys(extractedData.boq_summary).length > 0 && (
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Package className="text-purple-600" size={20} />
                    <h3 className="font-semibold text-purple-900">Bill of Quantities (BOQ)</h3>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white rounded p-3">
                      <p className="text-sm text-gray-600">Total Items</p>
                      <p className="text-2xl font-bold text-purple-600">{extractedData.boq_summary.total_items || 0}</p>
                    </div>
                    <div className="bg-white rounded p-3">
                      <p className="text-sm text-gray-600">Quantity</p>
                      <p className="text-2xl font-bold text-purple-600">{extractedData.boq_summary.total_quantity || 0}</p>
                    </div>
                    {extractedData.boq_summary.total_amount && (
                      <div className="bg-white rounded p-3">
                        <p className="text-sm text-gray-600">Est. Value</p>
                        <p className="text-2xl font-bold text-purple-600">
                          <DollarSign size={16} className="inline" />
                          {(extractedData.boq_summary.total_amount / 100000).toFixed(1)}L
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Specifications */}
              {extractedData.specifications && extractedData.specifications.length > 0 && (
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <FileCheck className="text-blue-600" size={20} />
                    <h3 className="font-semibold text-blue-900">Technical Specifications ({extractedData.specifications.length})</h3>
                  </div>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {extractedData.specifications.slice(0, 10).map((spec, idx) => (
                      <div key={idx} className="bg-white rounded p-2 text-sm flex items-center justify-between">
                        <span className="font-medium text-gray-700">{spec.parameter}</span>
                        <span className="text-gray-900">{spec.value} {spec.unit}</span>
                        {spec.requirement_type === 'mandatory' && (
                          <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">Required</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Testing Requirements */}
              {extractedData.testing_requirements && extractedData.testing_requirements.length > 0 && (
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <TestTube className="text-green-600" size={20} />
                    <h3 className="font-semibold text-green-900">Testing Requirements ({extractedData.testing_requirements.length})</h3>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {extractedData.testing_requirements.slice(0, 5).map((test, idx) => (
                      <div key={idx} className="bg-white rounded p-2 text-sm">
                        <p className="font-medium text-gray-700">{test.test_type}</p>
                        {test.standard && <p className="text-xs text-gray-600">Standard: {test.standard}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Standards & Certifications */}
              <div className="grid grid-cols-2 gap-4">
                {extractedData.standards && extractedData.standards.length > 0 && (
                  <div className="bg-gradient-to-br from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Award className="text-yellow-600" size={18} />
                      <h3 className="font-semibold text-yellow-900">Standards ({extractedData.standards.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {extractedData.standards.slice(0, 8).map((std, idx) => (
                        <span key={idx} className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                          {std}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {extractedData.certifications && extractedData.certifications.length > 0 && (
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Award className="text-indigo-600" size={18} />
                      <h3 className="font-semibold text-indigo-900">Certifications ({extractedData.certifications.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {extractedData.certifications.slice(0, 5).map((cert, idx) => (
                        <span key={idx} className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded">
                          {cert}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Quality Score */}
              {extractedData.quality_score !== undefined && (
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm opacity-90">Document Quality Score</p>
                      <p className="text-3xl font-bold">{extractedData.quality_score}%</p>
                    </div>
                    <CheckCircle size={48} className="opacity-80" />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Debug section */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-gray-600 hover:text-gray-800 font-medium">
              🔍 Debug: Full RFP Data
            </summary>
            <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-60">
              {JSON.stringify(rfp, null, 2)}
            </pre>
          </details>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-4 border-t flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors font-medium"
          >
            Close
          </button>
          {rfp.status !== 'completed' && (
            <button
              onClick={() => {
                fetch(`http://localhost:8000/api/rfp/analyze/${rfp.id}`, { method: 'POST' })
                  .then(res => res.json())
                  .then(data => alert(`✅ ${data.message}`))
                  .catch(() => alert('❌ Failed to start analysis'));
              }}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Process RFP
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default RFPDetailsModal;
