import React, { useState, useEffect } from 'react';
import { Package, TrendingUp, Download, Send, FileText, Table as TableIcon, CheckCircle, XCircle } from 'lucide-react';

const MatchedProductsDisplay = ({ rfpId }) => {
  const [matches, setMatches] = useState(null);
  const [specComparison, setSpecComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (rfpId) {
      loadMatches();
      loadSpecComparison();
    }
  }, [rfpId]);

  const loadMatches = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/match-products/${rfpId}`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        setMatches(data);
      }
    } catch (error) {
      console.error('Failed to load matches:', error);
    }
  };

  const loadSpecComparison = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/spec-comparison/${rfpId}`);
      if (response.ok) {
        const data = await response.json();
        setSpecComparison(data);
      }
    } catch (error) {
      console.error('Failed to load spec comparison:', error);
    }
  };

  const handleGenerateResponse = async () => {
    setGenerating(true);
    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/generate-response/${rfpId}`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        alert(`✅ Response document generated successfully!\nYou can now download it.`);
        // Refresh to show download button
        window.location.reload();
      } else {
        throw new Error('Generation failed');
      }
    } catch (error) {
      alert('❌ Failed to generate response document');
      console.error(error);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadResponse = () => {
    window.open(`http://localhost:8000/api/rfp-workflow/download-response/${rfpId}`, '_blank');
  };

  const handleDownloadDetails = () => {
    window.open(`http://localhost:8000/api/rfp-workflow/export-details/${rfpId}`, '_blank');
  };

  const handleSendResponse = async () => {
    if (!confirm('Send response to RFP portal? This will mark the RFP as submitted.')) return;

    try {
      const response = await fetch(`http://localhost:8000/api/rfp-workflow/send-response/${rfpId}`, {
        method: 'POST'
      });
      if (response.ok) {
        alert('✅ Response sent successfully!');
        window.location.reload();
      } else {
        throw new Error('Send failed');
      }
    } catch (error) {
      alert('❌ Failed to send response');
      console.error(error);
    }
  };

  if (!matches) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">No matched products yet. Processing...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FileText size={20} />
          Actions
        </h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleGenerateResponse}
            disabled={generating}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2 disabled:opacity-50"
          >
            {generating ? <div className="animate-spin">⏳</div> : <FileText size={18} />}
            {generating ? 'Generating...' : 'Generate Response PDF'}
          </button>
          
          <button
            onClick={handleDownloadResponse}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
          >
            <Download size={18} />
            Download Response
          </button>
          
          <button
            onClick={handleDownloadDetails}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
          >
            <Download size={18} />
            Export Details CSV
          </button>
          
          <button
            onClick={handleSendResponse}
            className="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
          >
            <Send size={18} />
            Send Response
          </button>
        </div>
      </div>

      {/* Top 3 Matched Products */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Package size={20} />
          Top 3 Matched Products
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {matches.top_matches.map((product, idx) => (
            <div
              key={product.product_id}
              className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-2xl font-bold text-blue-600">#{idx + 1}</span>
                <div className="text-right">
                  <div className="text-xs text-gray-600">Match Score</div>
                  <div className="text-2xl font-bold text-green-600">{product.match_score}%</div>
                </div>
              </div>
              
              {product.image_url && (
                <img
                  src={product.image_url}
                  alt={product.product_name}
                  className="w-full h-40 object-cover rounded-lg mb-3"
                  onError={(e) => e.target.style.display = 'none'}
                />
              )}
              
              <h4 className="font-semibold text-gray-900 mb-2">{product.product_name}</h4>
              <p className="text-sm text-gray-600 mb-1">Code: {product.product_code}</p>
              <p className="text-sm text-gray-600 mb-1">Brand: {product.brand}</p>
              <p className="text-sm text-gray-600 mb-3">Category: {product.category}</p>
              
              <div className="border-t pt-3 space-y-1">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">MRP:</span>
                  <span className="text-sm font-semibold">₹{product.mrp || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Selling Price:</span>
                  <span className="text-sm font-semibold text-green-600">₹{product.selling_price || 'N/A'}</span>
                </div>
              </div>
              
              {product.certifications && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs text-gray-600 mb-1">Certifications:</p>
                  <p className="text-xs text-gray-800">{product.certifications}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Specification Comparison Table */}
      {specComparison && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TableIcon size={20} />
            Specification Comparison Matrix
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Specification
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    RFP Requirement
                  </th>
                  {specComparison.matched_products.slice(0, 3).map((product, idx) => (
                    <th key={idx} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product {idx + 1}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {specComparison.comparison_table.slice(0, 15).map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {row.parameter}
                      {row.required && (
                        <span className="ml-2 px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full">Required</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {row.rfp_requirement} {row.rfp_unit}
                    </td>
                    {row.products.map((prod, prodIdx) => (
                      <td key={prodIdx} className="px-4 py-3 text-sm">
                        <div className="flex items-center gap-2">
                          {prod.matches ? (
                            <CheckCircle size={16} className="text-green-600" />
                          ) : (
                            <XCircle size={16} className="text-red-400" />
                          )}
                          <span className={prod.matches ? 'text-green-700 font-medium' : 'text-gray-600'}>
                            {prod.value}
                          </span>
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {specComparison.comparison_table.length > 15 && (
            <p className="mt-4 text-sm text-gray-600 text-center">
              Showing first 15 of {specComparison.comparison_table.length} specifications
            </p>
          )}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="text-sm text-blue-700 mb-1">Total Matches Found</div>
          <div className="text-2xl font-bold text-blue-900">{matches.total_matches}</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="text-sm text-green-700 mb-1">Average Match Score</div>
          <div className="text-2xl font-bold text-green-900">
            {(matches.top_matches.reduce((sum, p) => sum + p.match_score, 0) / matches.top_matches.length).toFixed(1)}%
          </div>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="text-sm text-purple-700 mb-1">Specifications Analyzed</div>
          <div className="text-2xl font-bold text-purple-900">
            {specComparison?.comparison_table.length || 0}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchedProductsDisplay;
