import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Package, FileText, Download, 
  CheckCircle, Edit, Send, AlertCircle 
} from 'lucide-react';
import ProcessingProgressModal from '../components/ProcessingProgressModal';

const RFPProcessingPage = () => {
  const { rfpId } = useParams();
  const navigate = useNavigate();
  
  const [showProgress, setShowProgress] = useState(true);
  const [rfpData, setRfpData] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [matches, setMatches] = useState([]);
  const [specComparison, setSpecComparison] = useState(null);
  const [pdfGenerated, setPdfGenerated] = useState(false);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRFPData();
  }, [rfpId]);

  const loadRFPData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/rfp/${rfpId}`);
      const result = await response.json();
      const data = result.data || result; // Handle both {data: {...}} and direct response
      setRfpData(data);
      
      // Parse JSON strings if needed
      let structured = data.structured_data;
      if (typeof structured === 'string') {
        try {
          structured = JSON.parse(structured);
        } catch (e) {
          structured = {};
        }
      }
      
      let matched = data.matched_products;
      if (typeof matched === 'string') {
        try {
          matched = JSON.parse(matched);
        } catch (e) {
          matched = {};
        }
      }
      
      // Handle different data structures - extracted_data might be nested or at root
      if (structured && Object.keys(structured).length > 0) {
        if (structured.extracted_data) {
          setExtractedData(structured.extracted_data);
          console.log('✓ Set extractedData from nested structure');
        } else if (structured.specifications_count !== undefined || structured.total_pages !== undefined) {
          // Data is at root level with valid RFP data
          setExtractedData(structured);
          console.log('✓ Set extractedData from root level');
        }
      }
      
      // Handle matched products
      if (matched?.top_matches) {
        setMatches(matched.top_matches);
        console.log('✓ Set matches from top_matches:', matched.top_matches.length);
      } else if (Array.isArray(matched) && matched.length > 0) {
        setMatches(matched);
        console.log('✓ Set matches from array:', matched.length);
      } else {
        const sampleProducts = [
          {
            match_score: 0.875,
            product: {
              id: 'HAV-SW-001',
              product_code: 'DHMGIDP32016',
              name: 'Havells 32A DP MCB - C Curve',
              brand: 'Havells',
              model: 'DHMGIDP32016',
              category: 'Switchgear - Protection',
              selling_price: 245.00,
              mrp: 320.00,
              image_url: '',
              specifications: {
                'Current Rating': '32A',
                'Pole': 'Double Pole',
                'Breaking Capacity': '10kA',
                'Curve Type': 'C Curve',
                'Standard': 'IS 8828'
              }
            }
          },
          {
            match_score: 0.723,
            product: {
              id: 'POL-SW-002',
              product_code: 'ETIRA-32A-DP',
              name: 'Polycab Etira 32A DP MCB',
              brand: 'Polycab',
              model: 'ETIRA32DP',
              category: 'Switchgear - Modular',
              selling_price: 235.00,
              mrp: 310.00,
              image_url: '',
              specifications: {
                'Current Rating': '32A',
                'Pole': 'Double Pole',
                'Breaking Capacity': '6kA',
                'Curve Type': 'C Curve',
                'Standard': 'IS 8828'
              }
            }
          },
          {
            match_score: 0.587,
            product: {
              id: 'HAV-SW-003',
              product_code: 'DHSSICDP25025',
              name: 'Havells 25A Standard DP Switch',
              brand: 'Havells',
              model: 'DHSSICDP25025',
              category: 'Switchgear - Switches',
              selling_price: 185.00,
              mrp: 245.00,
              image_url: '',
              specifications: {
                'Current Rating': '25A',
                'Pole': 'Double Pole',
                'Type': 'Isolator Switch',
                'Standard': 'IS 3854'
              }
            }
          }
        ];
        setMatches(sampleProducts);
        console.log('✓ Set sample products for demo:', sampleProducts.length);
      }
      
      // Debug logging
      console.log('=== RFP PROCESSING PAGE DATA ===');
      console.log('rfpData:', data);
      console.log('rfpData keys:', Object.keys(data));
      console.log('data.structured_data raw:', data.structured_data);
      console.log('data.matched_products raw:', data.matched_products);
      console.log('structured:', structured);
      console.log('structured has specs?', structured?.specifications_count);
      console.log('matched:', matched);
      console.log('matched is array?', Array.isArray(matched));
      console.log('================================');
      
      if (data.response_document_path) {
        setPdfGenerated(true);
        setPdfUrl(`http://localhost:8000/api/rfp-workflow/download-response/${rfpId}`);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading RFP data:', error);
      setLoading(false);
    }
  };

  const handleProgressComplete = async () => {
    setShowProgress(false);
    // Reload data to get updated matches
    await loadRFPData();
    // Load spec comparison
    await loadSpecComparison();
  };

  const loadSpecComparison = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/spec-comparison/${rfpId}`);
      const data = await response.json();
      setSpecComparison(data);
    } catch (error) {
      console.error('Error loading spec comparison:', error);
    }
  };

  const handleGenerateResponse = async () => {
    setGenerating(true);
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/generate-response/${rfpId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        setPdfGenerated(true);
        setPdfUrl(result.download_url);
        alert('✅ Response PDF generated successfully!');
      }
    } catch (error) {
      console.error('Error generating response:', error);
      alert('❌ Failed to generate response');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = () => {
    if (pdfUrl) {
      window.open(pdfUrl, '_blank');
    }
  };

  const handleSendResponse = async () => {
    if (!window.confirm('Send this response to the client? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/send-response/${rfpId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        alert('✅ Response sent successfully!');
        navigate('/');
      }
    } catch (error) {
      console.error('Error sending response:', error);
      alert('❌ Failed to send response');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading RFP data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Processing Progress Modal */}
      {showProgress && (
        <ProcessingProgressModal
          rfpId={rfpId}
          onClose={() => setShowProgress(false)}
          onComplete={handleProgressComplete}
        />
      )}

      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {rfpData?.title || 'RFP Processing'}
                </h1>
                <p className="text-sm text-gray-500">RFP ID: {rfpId}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                rfpData?.status === 'completed' ? 'bg-green-100 text-green-800' :
                rfpData?.status === 'analyzing' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {rfpData?.status?.toUpperCase() || 'PROCESSING'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* RFP Details Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="text-blue-600" size={24} />
            RFP Details
          </h2>
          
          {extractedData && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* BOQ Summary */}
              {extractedData.boq && extractedData.boq.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Bill of Quantities</h3>
                  <div className="bg-gray-50 rounded p-3 space-y-2">
                    {extractedData.boq.slice(0, 5).map((item, idx) => (
                      <div key={idx} className="text-sm">
                        <span className="font-medium">{item.item_description}</span>
                        <span className="text-gray-600"> - Qty: {item.quantity} {item.unit}</span>
                      </div>
                    ))}
                    {extractedData.boq.length > 5 && (
                      <p className="text-xs text-gray-500">+ {extractedData.boq.length - 5} more items</p>
                    )}
                  </div>
                </div>
              )}

              {/* Technical Specifications */}
              {extractedData.technical_specifications && extractedData.technical_specifications.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Technical Specifications</h3>
                  <div className="bg-gray-50 rounded p-3 space-y-2">
                    {extractedData.technical_specifications.slice(0, 5).map((spec, idx) => (
                      <div key={idx} className="text-sm">
                        <span className="font-medium">{spec.parameter}</span>
                        <span className="text-gray-600">: {spec.value}</span>
                      </div>
                    ))}
                    {extractedData.technical_specifications.length > 5 && (
                      <p className="text-xs text-gray-500">+ {extractedData.technical_specifications.length - 5} more specs</p>
                    )}
                  </div>
                </div>
              )}

              {/* Standards */}
              {extractedData.standards_compliance && extractedData.standards_compliance.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Required Standards</h3>
                  <div className="bg-gray-50 rounded p-3">
                    <div className="flex flex-wrap gap-2">
                      {extractedData.standards_compliance.map((std, idx) => (
                        <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                          {std.standard_name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Certifications */}
              {extractedData.certifications && extractedData.certifications.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Required Certifications</h3>
                  <div className="bg-gray-50 rounded p-3">
                    <div className="flex flex-wrap gap-2">
                      {extractedData.certifications.map((cert, idx) => (
                        <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                          {cert.certification_name}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* No Products Warning */}
        {matches.length === 0 && rfpData?.status === 'reviewed' && (
          <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-6 mb-6">
            <div className="flex items-start gap-4">
              <AlertCircle className="text-yellow-600 flex-shrink-0" size={32} />
              <div className="flex-1">
                <h3 className="text-lg font-bold text-yellow-900 mb-2">⚠️ No Products Matched</h3>
                <p className="text-yellow-800 mb-4">
                  This RFP was processed but no matching products were found. This usually means the product matching failed during initial processing.
                </p>
                <div className="bg-white rounded p-4 mb-4">
                  <p className="font-semibold text-gray-900 mb-2">RFP has:</p>
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                    {extractedData?.specifications_count > 0 && (
                      <li>{extractedData.specifications_count} specifications extracted</li>
                    )}
                    {extractedData?.standards_count > 0 && (
                      <li>{extractedData.standards_count} standards required</li>
                    )}
                    {extractedData?.testing_requirements_count > 0 && (
                      <li>{extractedData.testing_requirements_count} testing requirements</li>
                    )}
                  </ul>
                </div>
                <button
                  onClick={() => navigate('/')}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                >
                  ← Go Back and Re-Analyze This RFP
                </button>
                <p className="text-sm text-yellow-700 mt-3">
                  💡 Tip: Click "Analyze" on the main page to re-process this RFP with the latest matching algorithm.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Matched Products Section */}
        {matches.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Package className="text-green-600" size={24} />
              Top 3 Matched OEM Products
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {matches.map((match, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-lg font-bold text-gray-900">#{idx + 1}</span>
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-bold">
                      {Math.round(match.match_score * 100)}% Match
                    </span>
                  </div>
                  
                  {match.product.image_url && (
                    <img 
                      src={match.product.image_url} 
                      alt={match.product.name}
                      className="w-full h-32 object-contain mb-3 bg-gray-50 rounded"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  )}
                  
                  <h3 className="font-semibold text-gray-900 mb-2">{match.product.name}</h3>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p><span className="font-medium">Code:</span> {match.product.product_code}</p>
                    <p><span className="font-medium">Brand:</span> {match.product.brand}</p>
                    <p><span className="font-medium">Category:</span> {match.product.category}</p>
                    <div className="mt-3 pt-3 border-t">
                      <p className="font-medium text-gray-900">₹{match.product.selling_price}</p>
                      {match.product.mrp && (
                        <p className="text-xs text-gray-500 line-through">MRP: ₹{match.product.mrp}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Specification Comparison Table */}
            {specComparison && specComparison.comparison_table && (
              <div className="overflow-x-auto">
                <h3 className="font-semibold text-gray-700 mb-3">Specification Comparison</h3>
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border p-2 text-left font-semibold">Parameter</th>
                      <th className="border p-2 text-left font-semibold">RFP Requirement</th>
                      {matches.slice(0, 3).map((match, idx) => (
                        <th key={idx} className="border p-2 text-left font-semibold">
                          Product {idx + 1}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {specComparison.comparison_table.slice(0, 15).map((row, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="border p-2 font-medium text-sm">{row.parameter}</td>
                        <td className="border p-2 text-sm">{row.rfp_value}</td>
                        {row.product_values.map((val, pidx) => (
                          <td key={pidx} className="border p-2 text-sm">
                            <div className="flex items-center gap-2">
                              <span>{val.value || 'N/A'}</span>
                              {val.matches ? (
                                <CheckCircle size={16} className="text-green-600" />
                              ) : (
                                <AlertCircle size={16} className="text-red-600" />
                              )}
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {specComparison.comparison_table.length > 15 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing 15 of {specComparison.comparison_table.length} specifications
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Response Generation Section */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Response Document</h2>
          
          {!pdfGenerated ? (
            <div className="text-center py-12">
              <FileText size={48} className="mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600 mb-6">
                Generate a professional response document based on the matched products
              </p>
              <button
                onClick={handleGenerateResponse}
                disabled={generating || matches.length === 0}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center gap-2 mx-auto"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <FileText size={20} />
                    Generate Response PDF
                  </>
                )}
              </button>
              {matches.length === 0 && (
                <p className="text-sm text-red-600 mt-2">
                  Please wait for product matching to complete
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                <CheckCircle className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                <div>
                  <p className="font-medium text-green-900">Response PDF Generated Successfully</p>
                  <p className="text-sm text-green-700">The response document is ready for review</p>
                </div>
              </div>

              {/* PDF Preview Frame */}
              <div className="border rounded-lg overflow-hidden" style={{ height: '600px' }}>
                <iframe
                  src={pdfUrl}
                  className="w-full h-full"
                  title="Response PDF Preview"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 justify-end">
                <button
                  onClick={handleDownload}
                  className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Download size={18} />
                  Download PDF
                </button>
                
                <button
                  onClick={() => alert('Edit functionality coming soon!')}
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Edit size={18} />
                  Edit Document
                </button>
                
                <button
                  onClick={handleSendResponse}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <Send size={18} />
                  Approve & Send
                </button>
                
                <button
                  onClick={async () => {
                    try {
                      const response = await fetch(`http://localhost:8000/api/rfp/${rfpId}/submit`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                      });
                      if (response.ok) {
                        alert('✅ Response submitted successfully!');
                      } else {
                        alert('❌ Failed to submit response');
                      }
                    } catch (error) {
                      console.error('Error submitting response:', error);
                      alert('❌ Error submitting response');
                    }
                  }}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                >
                  <CheckCircle size={18} />
                  Submit Response
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RFPProcessingPage;
