import { CheckCircle2, XCircle, AlertCircle, TrendingUp, Award } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge } from './UI';

const SpecMatchVisualization = ({ matchData }) => {
  if (!matchData) {
    return (
      <Card>
        <CardBody>
          <p className="text-center text-gray-400 py-8">No match data available</p>
        </CardBody>
      </Card>
    );
  }

  const getMatchColor = (score) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-blue-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getMatchBgColor = (score) => {
    if (score >= 90) return 'bg-green-500/20 border-green-500';
    if (score >= 70) return 'bg-blue-500/20 border-blue-500';
    if (score >= 50) return 'bg-yellow-500/20 border-yellow-500';
    return 'bg-red-500/20 border-red-500';
  };

  const getMatchIcon = (score) => {
    if (score >= 70) return <CheckCircle2 className="w-5 h-5 text-green-400" />;
    if (score >= 50) return <AlertCircle className="w-5 h-5 text-yellow-400" />;
    return <XCircle className="w-5 h-5 text-red-400" />;
  };

  const renderComparisonTable = () => {
    return (
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-600">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Specification</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Required</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Product 1</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Product 2</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-400">Product 3</th>
            </tr>
          </thead>
          <tbody>
            {matchData.specifications?.map((spec, idx) => (
              <tr key={idx} className="border-b border-dark-700 hover:bg-dark-700/30">
                <td className="py-3 px-4 text-sm font-medium text-white">{spec.name}</td>
                <td className="py-3 px-4 text-sm text-gray-300">{spec.required}</td>
                {spec.products.map((product, pIdx) => (
                  <td key={pIdx} className="py-3 px-4 text-sm">
                    <div className="flex items-center gap-2">
                      {getMatchIcon(product.match_score)}
                      <span className={getMatchColor(product.match_score)}>
                        {product.value}
                      </span>
                      <span className="text-xs text-gray-500">
                        ({product.match_score}%)
                      </span>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderMatchScore = (product, index) => {
    const overallScore = product.overall_match_score || 0;
    
    return (
      <div key={index} className={`p-4 rounded-lg border-2 ${getMatchBgColor(overallScore)}`}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            {index === 0 && <Award className="w-5 h-5 text-yellow-400" />}
            <div>
              <h4 className="font-semibold text-white">{product.name}</h4>
              <p className="text-sm text-gray-400">{product.brand} • {product.model}</p>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-2xl font-bold ${getMatchColor(overallScore)}`}>
              {overallScore}%
            </p>
            <p className="text-xs text-gray-400">Match Score</p>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Specification Match</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-400"
                  style={{ width: `${product.spec_match || 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-white w-12 text-right">
                {product.spec_match || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Brand Preference</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-purple-400"
                  style={{ width: `${product.brand_score || 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-white w-12 text-right">
                {product.brand_score || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Price Competitiveness</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-500 to-green-400"
                  style={{ width: `${product.price_score || 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-white w-12 text-right">
                {product.price_score || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Availability</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-yellow-500 to-yellow-400"
                  style={{ width: `${product.availability_score || 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-white w-12 text-right">
                {product.availability_score || 0}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Certification</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-pink-500 to-pink-400"
                  style={{ width: `${product.certification_score || 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-white w-12 text-right">
                {product.certification_score || 0}%
              </span>
            </div>
          </div>
        </div>

        {/* Price & Stock Info */}
        <div className="grid grid-cols-3 gap-3 mt-4 pt-3 border-t border-dark-600">
          <div>
            <p className="text-xs text-gray-400">Price</p>
            <p className="text-sm font-semibold text-white">₹{product.price?.toLocaleString('en-IN')}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Stock</p>
            <p className="text-sm font-semibold text-white">{product.stock || 'N/A'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Lead Time</p>
            <p className="text-sm font-semibold text-white">{product.lead_time || 'N/A'} days</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Overall Match Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Match Summary</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-green-400">
                {matchData.products?.filter(p => p.overall_match_score >= 90).length || 0}
              </p>
              <p className="text-sm text-gray-400 mt-1">Excellent Matches (90%+)</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-blue-400">
                {matchData.products?.filter(p => p.overall_match_score >= 70 && p.overall_match_score < 90).length || 0}
              </p>
              <p className="text-sm text-gray-400 mt-1">Good Matches (70-89%)</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-yellow-400">
                {matchData.products?.filter(p => p.overall_match_score >= 50 && p.overall_match_score < 70).length || 0}
              </p>
              <p className="text-sm text-gray-400 mt-1">Fair Matches (50-69%)</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-red-400">
                {matchData.products?.filter(p => p.overall_match_score < 50).length || 0}
              </p>
              <p className="text-sm text-gray-400 mt-1">Poor Matches (&lt;50%)</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Top 3 Product Recommendations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Top 3 Product Recommendations</CardTitle>
            <Badge variant="primary">
              <TrendingUp className="w-4 h-4 mr-1" />
              AI-Powered Matching
            </Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            {matchData.products?.slice(0, 3).map((product, idx) => renderMatchScore(product, idx))}
          </div>
        </CardBody>
      </Card>

      {/* Detailed Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Specification Comparison</CardTitle>
        </CardHeader>
        <CardBody>
          {renderComparisonTable()}
        </CardBody>
      </Card>
    </div>
  );
};

export default SpecMatchVisualization;
