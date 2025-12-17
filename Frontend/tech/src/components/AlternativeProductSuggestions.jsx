import React, { useState, useEffect } from 'react';
import { AlertCircle, Wrench, Clock, DollarSign, CheckCircle2, ArrowRight, Package, TrendingUp, Info, X } from 'lucide-react';

/**
 * AlternativeProductSuggestions Component
 * 
 * Displays alternative products when no perfect match exists (score <80%).
 * Shows made-to-order options, similar products, and tradeoff analysis.
 * 
 * Backend Integration:
 * - GET /api/v1/rfp/{rfp_id}/alternatives?product_id={product_id}
 * 
 * Triggers when:
 * - Primary match score <80%
 * - User clicks "View Alternatives" on product card
 * - Critical specifications don't match
 */

const AlternativeProductSuggestions = ({ rfpId, primaryProduct, onSelectAlternative, isOpen, onClose }) => {
  const [selectedTab, setSelectedTab] = useState('made-to-order');
  const [selectedAlternative, setSelectedAlternative] = useState(null);

  // Real backend data structure (replace with API call)
  const alternativesData = {
    primaryProduct: primaryProduct || {
      name: 'Polycab 4 Core 50 sq.mm 1100V XLPE Cable',
      matchScore: 78,
      missingSpecs: ['Armored sheath', 'Fire retardant grade FR1']
    },
    
    madeToOrder: {
      available: true,
      feasibility: 'HIGH',
      estimatedCost: 2850000,
      costIncrease: 12, // percentage
      estimatedTime: '18-22 days',
      timeIncrease: 8, // days over standard
      specifications: [
        { spec: 'Voltage Rating', value: '1100V', status: 'standard', icon: CheckCircle2, color: 'text-green-600' },
        { spec: 'Cross Section', value: '50 sq.mm', status: 'standard', icon: CheckCircle2, color: 'text-green-600' },
        { spec: 'Core Type', value: '4 Core', status: 'standard', icon: CheckCircle2, color: 'text-green-600' },
        { spec: 'Insulation', value: 'XLPE', status: 'standard', icon: CheckCircle2, color: 'text-green-600' },
        { spec: 'Armored Sheath', value: 'Steel Wire Armoring', status: 'custom', icon: Wrench, color: 'text-amber-600' },
        { spec: 'Fire Retardant', value: 'FR1 Grade', status: 'custom', icon: Wrench, color: 'text-amber-600' }
      ],
      rdRequirements: [
        { item: 'Custom armoring integration', effort: 'LOW', reason: 'Standard process, just not for this spec' },
        { item: 'FR1 compound testing', effort: 'MEDIUM', reason: 'Need to validate flame resistance standards' },
        { item: 'Sample production & testing', effort: 'MEDIUM', reason: '3-5 samples for client approval' }
      ],
      advantages: [
        'Exact match to RFP requirements (100% compliance)',
        'Higher margins due to customization (18-22%)',
        'Competitive differentiation - few suppliers offer this',
        'Potential for recurring orders if RFP is won'
      ],
      risks: [
        'Longer lead time may not meet urgent deadlines',
        'Higher cost may reduce competitiveness',
        'Client may not accept custom product without prior history',
        'Testing delays could push delivery further'
      ]
    },

    similarProducts: [
      {
        id: 'alt-1',
        name: 'Polycab 4 Core 50 sq.mm 1100V XLPE Armored Cable',
        brand: 'Polycab',
        matchScore: 92,
        price: 2680000,
        priceDiff: 6.8, // percentage vs budget
        availability: 'In Stock',
        leadTime: '4-6 days',
        tradeoffs: {
          advantages: [
            'Has armored sheath (RFP requirement)',
            'In stock - immediate delivery',
            '92% match score - very close',
            'Same trusted brand (Polycab)'
          ],
          disadvantages: [
            'Missing FR1 fire retardant grade',
            'Standard FR grade only (not specified in RFP)',
            'May need client approval for spec deviation'
          ]
        },
        recommendation: 'RECOMMENDED',
        reasoning: 'Best available match. FR grade difference is minor - standard FR may be acceptable to client. Suggest including compliance note in proposal.'
      },
      {
        id: 'alt-2',
        name: 'KEI 4 Core 50 sq.mm 1100V XLPE FR1 Cable',
        brand: 'KEI',
        matchScore: 88,
        price: 2590000,
        priceDiff: 3.2, // percentage vs budget
        availability: 'Available',
        leadTime: '7-10 days',
        tradeoffs: {
          advantages: [
            'Has FR1 fire retardant (RFP requirement)',
            '3.2% cheaper than budget',
            'Good brand reputation (KEI)',
            'Available within reasonable timeframe'
          ],
          disadvantages: [
            'Missing armored sheath',
            'Different brand than preferred (client may prefer Polycab)',
            'Slightly longer lead time (7-10 days)',
            'May need client approval for non-armored variant'
          ]
        },
        recommendation: 'CONSIDER',
        reasoning: 'Good alternative if FR1 grade is more critical than armoring. Lower price is competitive advantage. Suggest offering as secondary option.'
      },
      {
        id: 'alt-3',
        name: 'Havells 4 Core 50 sq.mm 1100V XLPE Standard Cable',
        brand: 'Havells',
        matchScore: 82,
        price: 2450000,
        priceDiff: -2.5, // percentage vs budget (negative = cheaper)
        availability: 'In Stock',
        leadTime: '2-3 days',
        tradeoffs: {
          advantages: [
            'Lowest price - 2.5% under budget',
            'Fastest delivery (2-3 days)',
            'Reputable brand (Havells)',
            'In stock - no wait time'
          ],
          disadvantages: [
            'Missing armored sheath',
            'Missing FR1 grade',
            'Only 82% match score',
            'May not meet critical RFP requirements'
          ]
        },
        recommendation: 'BACKUP',
        reasoning: 'Use only if client accepts spec deviations and price is the deciding factor. Best for urgent, cost-sensitive scenarios.'
      }
    ],

    hybridStrategy: {
      available: true,
      description: 'Offer primary match + alternative as package deal',
      options: [
        {
          name: 'Dual Sourcing',
          details: 'Supply 70% with Polycab armored (in stock) + 30% custom made-to-order with full specs',
          advantages: ['Partial immediate delivery', 'Meet all specs eventually', 'Risk mitigation'],
          cost: 2720000,
          timeline: '10-15 days for full completion'
        },
        {
          name: 'Phased Delivery',
          details: 'Deliver standard product now, upgrade to custom in Phase 2 of project',
          advantages: ['No project delay', 'Client can start immediately', 'Upgrade path available'],
          cost: 2650000,
          timeline: '4-6 days Phase 1, 18-22 days Phase 2'
        }
      ]
    }
  };

  const MadeToOrderSection = () => (
    <div className="space-y-6">
      {/* Feasibility Banner */}
      <div className={`p-6 rounded-xl ${
        alternativesData.madeToOrder.feasibility === 'HIGH' ? 'bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200' :
        alternativesData.madeToOrder.feasibility === 'MEDIUM' ? 'bg-gradient-to-br from-amber-50 to-yellow-50 border border-amber-200' :
        'bg-gradient-to-br from-red-50 to-rose-50 border border-red-200'
      }`}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Custom Manufacturing Available</h3>
            <p className="text-gray-600">We can manufacture a product that meets 100% of RFP requirements</p>
          </div>
          <div className={`px-4 py-2 rounded-full text-sm font-bold ${
            alternativesData.madeToOrder.feasibility === 'HIGH' ? 'bg-green-500 text-white' :
            alternativesData.madeToOrder.feasibility === 'MEDIUM' ? 'bg-amber-500 text-white' :
            'bg-red-500 text-white'
          }`}>
            {alternativesData.madeToOrder.feasibility} FEASIBILITY
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <DollarSign className="w-8 h-8 text-green-600 mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              ₹{(alternativesData.madeToOrder.estimatedCost / 100000).toFixed(2)}L
            </div>
            <div className="text-sm text-gray-600">
              +{alternativesData.madeToOrder.costIncrease}% over standard
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <Clock className="w-8 h-8 text-blue-600 mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {alternativesData.madeToOrder.estimatedTime}
            </div>
            <div className="text-sm text-gray-600">
              +{alternativesData.madeToOrder.timeIncrease} days over standard
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <CheckCircle2 className="w-8 h-8 text-purple-600 mb-2" />
            <div className="text-2xl font-bold text-gray-900">100%</div>
            <div className="text-sm text-gray-600">RFP compliance</div>
          </div>
        </div>
      </div>

      {/* Specification Breakdown */}
      <div>
        <h4 className="text-lg font-semibold text-gray-900 mb-4">Custom Specification Breakdown</h4>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Specification</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Value</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Type</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {alternativesData.madeToOrder.specifications.map((spec, idx) => {
                const Icon = spec.icon;
                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{spec.spec}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{spec.value}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <Icon className={`w-4 h-4 ${spec.color}`} />
                        <span className={`text-sm font-medium ${spec.color}`}>
                          {spec.status === 'standard' ? 'Standard' : 'Custom Modification'}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* R&D Requirements */}
      <div>
        <h4 className="text-lg font-semibold text-gray-900 mb-4">R&D Requirements</h4>
        <div className="space-y-3">
          {alternativesData.madeToOrder.rdRequirements.map((req, idx) => (
            <div key={idx} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-start justify-between mb-2">
                <h5 className="font-semibold text-gray-900">{req.item}</h5>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  req.effort === 'LOW' ? 'bg-green-100 text-green-700' :
                  req.effort === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {req.effort} EFFORT
                </span>
              </div>
              <p className="text-sm text-gray-600">{req.reason}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Advantages & Risks */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <h4 className="font-semibold text-green-900 mb-3 flex items-center">
            <CheckCircle2 className="w-5 h-5 mr-2" />
            Advantages
          </h4>
          <ul className="space-y-2">
            {alternativesData.madeToOrder.advantages.map((adv, idx) => (
              <li key={idx} className="text-sm text-green-800 flex items-start">
                <span className="mr-2">✓</span>
                <span>{adv}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <h4 className="font-semibold text-red-900 mb-3 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            Risks & Considerations
          </h4>
          <ul className="space-y-2">
            {alternativesData.madeToOrder.risks.map((risk, idx) => (
              <li key={idx} className="text-sm text-red-800 flex items-start">
                <span className="mr-2">!</span>
                <span>{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );

  const SimilarProductsSection = () => (
    <div className="space-y-4">
      {alternativesData.similarProducts.map((product) => (
        <div key={product.id} className="bg-white rounded-xl border-2 border-gray-200 overflow-hidden hover:border-sky-300 transition-colors">
          {/* Header */}
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-4 border-b border-gray-200">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">{product.name}</h3>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span className="font-medium">{product.brand}</span>
                  <span>•</span>
                  <span>{product.availability}</span>
                  <span>•</span>
                  <span>Delivery: {product.leadTime}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{product.matchScore}%</div>
                <div className="text-sm text-gray-500">Match Score</div>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-4">
            {/* Price & Recommendation */}
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  ₹{(product.price / 100000).toFixed(2)}L
                </div>
                <div className={`text-sm font-medium ${
                  product.priceDiff > 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {product.priceDiff > 0 ? '+' : ''}{product.priceDiff}% vs budget
                </div>
              </div>
              <div className={`px-4 py-2 rounded-full text-sm font-bold ${
                product.recommendation === 'RECOMMENDED' ? 'bg-green-500 text-white' :
                product.recommendation === 'CONSIDER' ? 'bg-amber-500 text-white' :
                'bg-gray-500 text-white'
              }`}>
                {product.recommendation}
              </div>
            </div>

            {/* Tradeoffs */}
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="font-semibold text-green-700 mb-2 text-sm">✓ Advantages</h4>
                <ul className="space-y-1">
                  {product.tradeoffs.advantages.map((adv, idx) => (
                    <li key={idx} className="text-sm text-gray-700">{adv}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-red-700 mb-2 text-sm">✗ Disadvantages</h4>
                <ul className="space-y-1">
                  {product.tradeoffs.disadvantages.map((dis, idx) => (
                    <li key={idx} className="text-sm text-gray-700">{dis}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Reasoning */}
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <div className="flex items-start space-x-2">
                <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-blue-900 mb-1">Our Recommendation:</p>
                  <p className="text-sm text-blue-800">{product.reasoning}</p>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={() => onSelectAlternative?.(product)}
              className="mt-4 w-full py-3 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors font-semibold flex items-center justify-center space-x-2"
            >
              <span>Select This Alternative</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  const HybridStrategySection = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl p-6 border border-purple-200">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Hybrid Approach</h3>
        <p className="text-gray-600 mb-4">{alternativesData.hybridStrategy.description}</p>
        
        <div className="space-y-4">
          {alternativesData.hybridStrategy.options.map((option, idx) => (
            <div key={idx} className="bg-white rounded-lg p-5 border border-gray-200">
              <h4 className="font-bold text-gray-900 mb-2">{option.name}</h4>
              <p className="text-sm text-gray-600 mb-3">{option.details}</p>
              
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="bg-gray-50 rounded p-3">
                  <DollarSign className="w-5 h-5 text-green-600 mb-1" />
                  <div className="font-bold text-gray-900">₹{(option.cost / 100000).toFixed(2)}L</div>
                  <div className="text-xs text-gray-600">Total Cost</div>
                </div>
                <div className="bg-gray-50 rounded p-3">
                  <Clock className="w-5 h-5 text-blue-600 mb-1" />
                  <div className="font-bold text-gray-900">{option.timeline}</div>
                  <div className="text-xs text-gray-600">Timeline</div>
                </div>
              </div>
              
              <div className="space-y-1">
                {option.advantages.map((adv, i) => (
                  <div key={i} className="text-sm text-gray-700 flex items-center">
                    <CheckCircle2 className="w-4 h-4 text-green-600 mr-2 flex-shrink-0" />
                    {adv}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-600 p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Alternative Product Suggestions</h2>
              <p className="text-amber-100">
                Primary match score: {alternativesData.primaryProduct.matchScore}% - 
                Missing: {alternativesData.primaryProduct.missingSpecs.join(', ')}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="flex space-x-1 p-2">
            <button
              onClick={() => setSelectedTab('made-to-order')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                selectedTab === 'made-to-order'
                  ? 'bg-white text-sky-600 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Wrench className="w-5 h-5 inline mr-2" />
              Made-to-Order
            </button>
            <button
              onClick={() => setSelectedTab('similar')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                selectedTab === 'similar'
                  ? 'bg-white text-sky-600 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Package className="w-5 h-5 inline mr-2" />
              Similar Products ({alternativesData.similarProducts.length})
            </button>
            <button
              onClick={() => setSelectedTab('hybrid')}
              className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                selectedTab === 'hybrid'
                  ? 'bg-white text-sky-600 shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <TrendingUp className="w-5 h-5 inline mr-2" />
              Hybrid Strategy
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {selectedTab === 'made-to-order' && <MadeToOrderSection />}
          {selectedTab === 'similar' && <SimilarProductsSection />}
          {selectedTab === 'hybrid' && <HybridStrategySection />}
        </div>
      </div>
    </div>
  );
};

export default AlternativeProductSuggestions;
