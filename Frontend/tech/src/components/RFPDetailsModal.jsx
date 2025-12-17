import React, { useState, useEffect } from 'react';
import { X, Calendar, FileText, Tag, TrendingUp, CheckCircle, Clock, AlertCircle, Loader, Package, TestTube, Award, FileCheck, DollarSign } from 'lucide-react';
import ProcessingProgressModal from './ProcessingProgressModal';
import MatchedProductsDisplay from './MatchedProductsDisplay';

const RFPDetailsModal = ({ rfp, onClose }) => {
  const [extractedData, setExtractedData] = useState(null);
  const [loadingExtraction, setLoadingExtraction] = useState(false);
  const [isCached, setIsCached] = useState(false);
  const [showProcessing, setShowProcessing] = useState(false);
  const [showMatches, setShowMatches] = useState(false);
  const [refreshedRfp, setRefreshedRfp] = useState(null);
  
  if (!rfp) return null;
  
  // Use refreshed RFP data if available, otherwise use prop
  const currentRfp = refreshedRfp || rfp;

  // Debug logging
  console.log('=== RFP DETAILS MODAL DEBUG ===');
  console.log('rfp prop:', rfp);
  console.log('rfp.id:', rfp.id);
  console.log('rfp.title:', rfp.title);
  console.log('rfp.status:', rfp.status);
  console.log('currentRfp:', currentRfp);
  console.log('===============================');
  
  // Auto-fetch extracted PDF data when modal opens
  useEffect(() => {
    const fetchExtractedData = async () => {
      if (!rfp.id) return;
      
      setLoadingExtraction(true);
      try {
        const response = await fetch(`http://localhost:8000/api/rfp/extract/${rfp.id}`);
        if (response.ok) {
          const data = await response.json();
          setExtractedData(data.extracted_data);
          setIsCached(data.cached || false);
        } else {
          console.error('Failed to fetch extracted data:', await response.text());
        }
      } catch (error) {
        console.error('Error fetching extracted data:', error);
      } finally {
        setLoadingExtraction(false);
      }
    };
    
    fetchExtractedData();
  }, [rfp.id]);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch (e) {
      return 'Invalid Date';
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      discovered: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      processing: 'bg-blue-100 text-blue-800 border-blue-300',
      completed: 'bg-green-100 text-green-800 border-green-300',
      failed: 'bg-red-100 text-red-800 border-red-300',
      pending: 'bg-gray-100 text-gray-800 border-gray-300'
    };
    return colors[status] || colors.pending;
  };

  const getStatusIcon = (status) => {
    const icons = {
      discovered: <AlertCircle size={20} />,
      processing: <Clock size={20} className="animate-spin" />,
      completed: <CheckCircle size={20} />,
      failed: <X size={20} />,
      pending: <Clock size={20} />
    };
    return icons[status] || icons.pending;
  };

  return (
    <>
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
        style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }}
      >
        <div 
          className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slide-up"
          onClick={(e) => e.stopPropagation()}
        >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-full transition-colors z-10"
            aria-label="Close"
          >
            <X size={24} />
          </button>
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white/20 rounded-lg">
              <FileText size={32} />
            </div>
            <div className="flex-1 pr-12">
              <h2 className="text-2xl font-bold mb-2">{rfp.title || rfp.name || 'Untitled RFP'}</h2>
              <div className="flex items-center gap-4 text-blue-100">
                <span className="flex items-center gap-1">
                  <Tag size={16} />
                  {rfp.source || rfp.buyer || 'Unknown Source'}
                </span>
                {rfp.id && (
                  <span className="text-sm">ID: {rfp.id}</span>
                )}
              </div>
            </div>
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
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="text-sm text-gray-600 mb-1">Status</div>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getStatusColor(rfp.status)}`}>
                {getStatusIcon(rfp.status)}
                <span className="font-semibold capitalize">{rfp.status || 'Pending'}</span>
              </div>
            </div>

            {rfp.created_at && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-1">
                  <Calendar size={16} />
                  Created
                </div>
                <div className="font-semibold text-gray-900">{formatDate(rfp.created_at)}</div>
              </div>
            )}

            {(rfp.due_date || rfp.dueDate) && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="text-sm text-gray-600 mb-1 flex items-center gap-1">
                  <Calendar size={16} />
                  Due Date
                </div>
                <div className="font-semibold text-gray-900">
                  {formatDate(rfp.due_date || rfp.dueDate)}
                  {(rfp.days_remaining || rfp.daysRemaining) && (
                    <span className={`ml-2 text-sm ${
                      (rfp.days_remaining || rfp.daysRemaining) < 7 ? 'text-red-600' :
                      (rfp.days_remaining || rfp.daysRemaining) < 30 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      ({rfp.days_remaining || rfp.daysRemaining} days)
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Loading Extraction */}
          {loadingExtraction && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 flex items-center gap-3">
              <Loader className="animate-spin text-blue-600" size={24} />
              <div>
                <p className="font-medium text-blue-900">Extracting PDF Data...</p>
                <p className="text-sm text-blue-700">This may take a few moments for first-time extraction</p>
              </div>
            </div>
          )}

          {/* Cached Data Indicator */}
          {!loadingExtraction && isCached && extractedData && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm">
              <CheckCircle size={16} className="text-green-600" />
              <span className="text-green-800">Showing previously extracted data (cached)</span>
            </div>
          )}

          {/* Fresh Data Indicator */}
          {!loadingExtraction && !isCached && extractedData && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm">
              <AlertCircle size={16} className="text-blue-600" />
              <span className="text-blue-800">Freshly extracted data from PDF • Now cached for future views</span>
            </div>
          )}

          {/* BOQ Summary */}
          {extractedData?.boq_summary && (
            <div className="mb-6 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-5 border border-purple-200">
              <h3 className="font-semibold text-purple-900 mb-4 flex items-center gap-2">
                <Package size={20} className="text-purple-600" />
                Bill of Quantities (BOQ) Summary
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {extractedData.boq_summary.total_items && (
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-purple-700 mb-1">Total Items</div>
                    <div className="text-2xl font-bold text-purple-900">{extractedData.boq_summary.total_items}</div>
                  </div>
                )}
                {extractedData.boq_summary.total_quantity && (
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-purple-700 mb-1">Total Quantity</div>
                    <div className="text-2xl font-bold text-purple-900">{extractedData.boq_summary.total_quantity.toLocaleString()}</div>
                  </div>
                )}
                {extractedData.boq_summary.total_amount && (
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="text-sm text-purple-700 mb-1">Estimated Value</div>
                    <div className="text-2xl font-bold text-purple-900">₹{(extractedData.boq_summary.total_amount / 100000).toFixed(2)}L</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Technical Specifications */}
          {extractedData?.specifications && extractedData.specifications.length > 0 && (
            <div className="mb-6 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-5 border border-blue-200">
              <h3 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
                <FileCheck size={20} className="text-blue-600" />
                Technical Specifications ({extractedData.specifications.length})
              </h3>
              <div className="bg-white rounded-lg p-4 max-h-60 overflow-y-auto space-y-2">
                {extractedData.specifications.map((spec, idx) => (
                  <div key={idx} className="flex items-start justify-between py-2 border-b border-gray-100 last:border-0">
                    <div className="flex-1">
                      <span className="font-medium text-gray-900">{spec.parameter}</span>
                      <span className="text-gray-600 ml-2">{spec.value} {spec.unit}</span>
                    </div>
                    {spec.requirement_type === 'mandatory' && (
                      <span className="ml-2 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">Required</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Testing Requirements */}
          {extractedData?.testing_requirements && extractedData.testing_requirements.length > 0 && (
            <div className="mb-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-5 border border-green-200">
              <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2">
                <TestTube size={20} className="text-green-600" />
                Testing Requirements ({extractedData.testing_requirements.length})
              </h3>
              <div className="bg-white rounded-lg p-4 space-y-2">
                {extractedData.testing_requirements.map((test, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                    <span className="font-medium text-gray-900">{test.test_type}</span>
                    <span className="text-sm text-gray-600">{test.standard}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Standards & Certifications */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            {extractedData?.standards && extractedData.standards.length > 0 && (
              <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-lg p-5 border border-yellow-200">
                <h3 className="font-semibold text-yellow-900 mb-3 flex items-center gap-2">
                  <Award size={18} className="text-yellow-600" />
                  Standards ({extractedData.standards.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {extractedData.standards.map((std, idx) => (
                    <span key={idx} className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full font-medium border border-yellow-300">
                      {std}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extractedData?.certifications && extractedData.certifications.length > 0 && (
              <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-5 border border-indigo-200">
                <h3 className="font-semibold text-indigo-900 mb-3 flex items-center gap-2">
                  <Award size={18} className="text-indigo-600" />
                  Certifications ({extractedData.certifications.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {extractedData.certifications.map((cert, idx) => (
                    <span key={idx} className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm rounded-full font-medium border border-indigo-300">
                      {cert}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quality Score */}
          {extractedData?.quality_score !== undefined && (
            <div className="mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-5 text-white">
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <CheckCircle size={20} />
                Document Quality Score
              </h3>
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold">{(extractedData.quality_score * 100).toFixed(0)}%</div>
                <div className="text-sm opacity-90">
                  Overall completeness and quality of the RFP document based on extracted data
                </div>
              </div>
            </div>
          )}

          {/* Processing Metrics */}
          {(rfp.processing_time_seconds || rfp.confidence_score) && (
            <div className="bg-blue-50 rounded-lg p-4 mb-6 border border-blue-200">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <TrendingUp size={20} />
                Processing Metrics
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {rfp.processing_time_seconds && (
                  <div>
                    <div className="text-sm text-blue-700">Processing Time</div>
                    <div className="text-2xl font-bold text-blue-900">
                      {rfp.processing_time_seconds.toFixed(2)}s
                    </div>
                  </div>
                )}
                {rfp.confidence_score && (
                  <div>
                    <div className="text-sm text-blue-700">Confidence Score</div>
                    <div className="text-2xl font-bold text-blue-900">
                      {(rfp.confidence_score * 100).toFixed(1)}%
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* File Path */}
          {rfp.file_path && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <FileText size={18} />
                File Location
              </h3>
              <div className="bg-gray-100 rounded-lg p-3 text-sm text-gray-700 font-mono break-all">
                {rfp.file_path}
              </div>
            </div>
          )}

          {/* Raw Text */}
          {rfp.raw_text && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <FileText size={18} />
                Raw Text Content
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-60 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
                  {rfp.raw_text}
                </pre>
              </div>
            </div>
          )}

          {/* Structured Data */}
          {rfp.structured_data && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Structured Data</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-60 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(rfp.structured_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Requirements */}
          {rfp.requirements && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Requirements</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-60 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {typeof rfp.requirements === 'string' 
                    ? rfp.requirements 
                    : JSON.stringify(rfp.requirements, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Matched Products */}
          {currentRfp.matched_products && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <CheckCircle size={18} />
                Matched Products
              </h3>
              <div className="bg-green-50 rounded-lg p-4 border border-green-200 max-h-60 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {typeof currentRfp.matched_products === 'string'
                    ? currentRfp.matched_products
                    : JSON.stringify(currentRfp.matched_products, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Pricing Data */}
          {currentRfp.pricing_data && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Pricing Data</h3>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-60 overflow-y-auto">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {typeof currentRfp.pricing_data === 'string'
                    ? currentRfp.pricing_data
                    : JSON.stringify(currentRfp.pricing_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Response Document */}
          {rfp.response_document_path && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-2">Response Document</h3>
              <div className="bg-gray-100 rounded-lg p-3 text-sm text-gray-700 font-mono break-all">
                {rfp.response_document_path}
              </div>
            </div>
          )}

          {/* Timestamps */}
          {(rfp.updated_at || rfp.updatedAt || rfp.processed_at || rfp.processedAt) && (
            <div className="border-t pt-4 mt-6">
              <h3 className="font-semibold text-gray-900 mb-3">Timeline</h3>
              <div className="space-y-2 text-sm">
                {(rfp.processed_at || rfp.processedAt) && (
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-600" />
                    <span className="text-gray-600">Processed:</span>
                    <span className="font-medium">{formatDate(rfp.processed_at || rfp.processedAt)}</span>
                  </div>
                )}
                {(rfp.updated_at || rfp.updatedAt) && (
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-blue-600" />
                    <span className="text-gray-600">Last Updated:</span>
                    <span className="font-medium">{formatDate(rfp.updated_at || rfp.updatedAt)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Debug Info - All RFP Properties */}
          <div className="border-t pt-4 mt-6">
            <details className="cursor-pointer">
              <summary className="font-semibold text-gray-900 mb-2 hover:text-blue-600">
                🔍 Debug: All Available Data
              </summary>
              <div className="bg-gray-100 rounded-lg p-3 mt-2 max-h-40 overflow-y-auto">
                <pre className="text-xs text-gray-700">
                  {JSON.stringify(rfp, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        </div>
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 p-4 flex justify-between items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            {extractedData && (
              <span className="flex items-center gap-1">
                <FileCheck size={16} className="text-green-600" />
                <span>PDF data extracted successfully</span>
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg transition-colors font-medium"
            >
              Close
            </button>
            {rfp.status !== 'completed' && (
              <button
                onClick={async () => {
                  try {
                    // Show processing modal immediately
                    setShowProcessing(true);
                    
                    // Start the analysis
                    const response = await fetch(`http://localhost:8000/api/rfp/analyze/${rfp.id}`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' }
                    });
                    
                    if (!response.ok) {
                      setShowProcessing(false);
                      throw new Error('Analysis failed');
                    }
                  } catch (error) {
                    console.error('Analysis error:', error);
                    setShowProcessing(false);
                    alert('❌ Failed to start analysis. Please try again.');
                  }
                }}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
              >
                <TrendingUp size={18} />
                Process RFP
              </button>
            )}
            
            {currentRfp.matched_products && (
              <button
                onClick={() => setShowMatches(!showMatches)}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
              >
                <Package size={18} />
                {showMatches ? 'Hide' : 'View'} Matched Products
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Processing Progress Modal */}
      {showProcessing && (
        <ProcessingProgressModal
          rfpId={rfp.id}
          onClose={() => {
            setShowProcessing(false);
            window.location.reload();
          }}
          onComplete={async () => {
            setShowProcessing(false);
            // Fetch fresh RFP data with updated matched products
            try {
              const response = await fetch(`http://localhost:8000/api/rfp/${rfp.id}`);
              if (response.ok) {
                const data = await response.json();
                if (data.data) {
                  setRefreshedRfp(data.data);
                }
              }
            } catch (error) {
              console.error('Error fetching refreshed RFP data:', error);
            }
            // Auto-open matched products view after processing completes
            setTimeout(() => {
              setShowMatches(true);
            }, 500);
          }}
        />
      )}

      {/* Matched Products Display */}
      {showMatches && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto" style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }} onClick={(e) => e.stopPropagation()}>
          <div className="bg-gray-100 rounded-2xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-6 bg-white rounded-lg p-4 sticky top-0">
              <h2 className="text-2xl font-bold text-gray-900">RFP #{rfp.id} - Matched Products & Response</h2>
              <button
                onClick={() => setShowMatches(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X size={24} />
              </button>
            </div>
            <MatchedProductsDisplay rfpId={rfp.id} />
          </div>
        </div>
      )}
    </>
  );
};

export default RFPDetailsModal;
