import React, { useState } from 'react';
import { Info, CheckCircle2, TrendingUp, DollarSign, Package, Award, X } from 'lucide-react';

/**
 * SpecMatchExplainer Component
 * 
 * Displays transparent step-by-step calculation of how spec match percentage is computed.
 * Shows the 5-component scoring system with actual numbers from current RFP.
 * 
 * Backend Integration:
 * - GET /api/v1/rfp/{rfp_id}/match-explanation?product_id={product_id}
 * 
 * Match Formula:
 * Total Score = (Spec * 0.40) + (Brand * 0.20) + (Price * 0.20) + (Availability * 0.10) + (Certification * 0.10)
 */

const SpecMatchExplainer = ({ rfpId, productId, matchData, isOpen, onClose }) => {
  const [activeStep, setActiveStep] = useState(null);

  // Real backend data structure (replace with API call)
  const explanationData = matchData || {
    overallScore: 95.2,
    components: [
      {
        id: 'specification',
        name: 'Technical Specification Match',
        weight: 40,
        score: 97.5,
        maxPoints: 40,
        earnedPoints: 39.0,
        icon: Package,
        color: 'bg-blue-500',
        breakdown: [
          { parameter: 'Voltage Rating', required: '1100V', actual: '1100V', match: 100, weight: 25 },
          { parameter: 'Cross Section', required: '50 sq.mm', actual: '50 sq.mm', match: 100, weight: 25 },
          { parameter: 'Core Type', required: '4 Core', actual: '4 Core', match: 100, weight: 20 },
          { parameter: 'Insulation Material', required: 'XLPE', actual: 'XLPE', match: 100, weight: 15 },
          { parameter: 'Conductor Type', required: 'Aluminum', actual: 'Aluminum', match: 100, weight: 15 }
        ],
        explanation: 'Product specifications are compared parameter-by-parameter. Each parameter has a weight based on criticality. Perfect matches get 100%, close matches 80-99%, partial matches 50-79%.'
      },
      {
        id: 'brand',
        name: 'Brand Reputation Score',
        weight: 20,
        score: 95.0,
        maxPoints: 20,
        earnedPoints: 19.0,
        icon: Award,
        color: 'bg-purple-500',
        breakdown: [
          { metric: 'Brand Tier', value: 'Tier 1 (Polycab)', score: 100 },
          { metric: 'Market Presence', value: '35 years experience', score: 95 },
          { metric: 'Quality History', value: '4.8/5 rating', score: 96 },
          { metric: 'Previous RFP Success', value: '12 wins with this client', score: 90 }
        ],
        explanation: 'Brand scoring considers manufacturer reputation, market presence, quality history, and past success with similar RFPs. Tier 1 brands get highest scores.'
      },
      {
        id: 'price',
        name: 'Price Competitiveness',
        weight: 20,
        score: 92.0,
        maxPoints: 20,
        earnedPoints: 18.4,
        icon: DollarSign,
        color: 'bg-green-500',
        breakdown: [
          { metric: 'Price vs Market Average', value: '5% below', score: 95 },
          { metric: 'Price vs Estimated Budget', value: 'Within 10%', score: 90 },
          { metric: 'Bulk Discount Potential', value: '8% available', score: 92 },
          { metric: 'Payment Terms Flexibility', value: '30-60 days', score: 90 }
        ],
        explanation: 'Price scoring evaluates competitiveness against market rates, estimated RFP budget, bulk discounts, and payment flexibility. Lower prices score higher but quality is never compromised.'
      },
      {
        id: 'availability',
        name: 'Stock & Delivery',
        weight: 10,
        score: 100.0,
        maxPoints: 10,
        earnedPoints: 10.0,
        icon: TrendingUp,
        color: 'bg-amber-500',
        breakdown: [
          { metric: 'Current Stock Status', value: 'In Stock - 5000m', score: 100 },
          { metric: 'Lead Time', value: '2-3 days', score: 100 },
          { metric: 'Supplier Reliability', value: '98% on-time delivery', score: 100 },
          { metric: 'Backup Suppliers', value: '3 alternatives available', score: 100 }
        ],
        explanation: 'Availability considers current stock levels, lead times, supplier reliability, and backup options. Products in stock with fast delivery score highest.'
      },
      {
        id: 'certification',
        name: 'Certifications & Compliance',
        weight: 10,
        score: 95.0,
        maxPoints: 10,
        earnedPoints: 9.5,
        icon: CheckCircle2,
        color: 'bg-indigo-500',
        breakdown: [
          { requirement: 'BIS Certification', status: 'Available', score: 100 },
          { requirement: 'IS 7098 Compliance', status: 'Certified', score: 100 },
          { requirement: 'ISO 9001:2015', status: 'Valid until 2026', score: 100 },
          { requirement: 'Environmental Compliance', status: 'RoHS, REACH', score: 80 }
        ],
        explanation: 'Certification scoring checks all required certifications, their validity, and compliance standards. Missing certifications significantly reduce score.'
      }
    ],
    calculationSteps: [
      { step: 1, description: 'Extract RFP technical requirements', detail: 'AI parses RFP to identify all technical parameters, certifications, and constraints' },
      { step: 2, description: 'Search product database using embeddings', detail: 'Semantic search finds products matching technical profile using vector similarity' },
      { step: 3, description: 'Score each component (5 categories)', detail: 'Calculate weighted scores for specifications, brand, price, availability, and certifications' },
      { step: 4, description: 'Apply weighting formula', detail: 'Multiply each score by its weight: Spec(40%), Brand(20%), Price(20%), Avail(10%), Cert(10%)' },
      { step: 5, description: 'Sum to get final match percentage', detail: 'Add all weighted scores to get final match percentage (0-100%)' }
    ]
  };

  const ComponentCard = ({ component }) => {
    const Icon = component.icon;
    const isActive = activeStep === component.id;

    return (
      <div
        onClick={() => setActiveStep(isActive ? null : component.id)}
        className={`cursor-pointer rounded-lg border-2 transition-all duration-300 ${
          isActive ? 'border-sky-500 shadow-lg scale-105' : 'border-gray-200 hover:border-gray-300'
        }`}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className={`${component.color} p-2 rounded-lg`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">{component.name}</h4>
                <p className="text-sm text-gray-500">Weight: {component.weight}%</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{component.score}%</div>
              <div className="text-sm text-gray-500">
                {component.earnedPoints.toFixed(1)}/{component.maxPoints} points
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-3">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${component.color} transition-all duration-500`}
                style={{ width: `${component.score}%` }}
              />
            </div>
          </div>

          {/* Explanation */}
          <p className="text-sm text-gray-600 mb-3">{component.explanation}</p>

          {/* Detailed Breakdown (Expanded) */}
          {isActive && (
            <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
              {component.breakdown.map((item, idx) => (
                <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium text-gray-700">
                      {item.parameter || item.metric || item.requirement}
                    </span>
                    <span className={`text-sm font-semibold ${
                      (item.match || item.score) >= 90 ? 'text-green-600' :
                      (item.match || item.score) >= 80 ? 'text-amber-600' : 'text-red-600'
                    }`}>
                      {item.match || item.score}%
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {item.required && <span>Required: <strong>{item.required}</strong></span>}
                    {item.actual && <span className="ml-3">Actual: <strong>{item.actual}</strong></span>}
                    {item.value && <span>Value: <strong>{item.value}</strong></span>}
                    {item.status && <span>Status: <strong>{item.status}</strong></span>}
                  </div>
                  {item.weight && (
                    <div className="mt-1 text-xs text-gray-500">Weight: {item.weight}%</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-sky-500 to-blue-600 p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Specification Match Calculation</h2>
              <p className="text-sky-100">Transparent breakdown of how we calculate the {explanationData.overallScore}% match score</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Overall Score Summary */}
          <div className="bg-gradient-to-br from-sky-50 to-blue-50 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Final Match Score</h3>
                <p className="text-gray-600">Calculated using 5-component weighted formula</p>
              </div>
              <div className="text-right">
                <div className="text-5xl font-bold text-sky-600">{explanationData.overallScore}%</div>
                <div className="text-sm text-gray-500 mt-1">
                  {explanationData.overallScore >= 90 ? 'Excellent Match' :
                   explanationData.overallScore >= 80 ? 'Good Match' :
                   explanationData.overallScore >= 70 ? 'Fair Match' : 'Poor Match'}
                </div>
              </div>
            </div>

            {/* Formula Display */}
            <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
              <p className="text-sm font-mono text-gray-700">
                <strong>Formula:</strong> Total Score = 
                <span className="text-blue-600"> (Spec × 0.40)</span> +
                <span className="text-purple-600"> (Brand × 0.20)</span> +
                <span className="text-green-600"> (Price × 0.20)</span> +
                <span className="text-amber-600"> (Avail × 0.10)</span> +
                <span className="text-indigo-600"> (Cert × 0.10)</span>
              </p>
              <p className="text-sm font-mono text-gray-700 mt-2">
                <strong>Calculation:</strong> {explanationData.overallScore}% = 
                <span className="text-blue-600"> ({explanationData.components[0].score} × 0.40)</span> +
                <span className="text-purple-600"> ({explanationData.components[1].score} × 0.20)</span> +
                <span className="text-green-600"> ({explanationData.components[2].score} × 0.20)</span> +
                <span className="text-amber-600"> ({explanationData.components[3].score} × 0.10)</span> +
                <span className="text-indigo-600"> ({explanationData.components[4].score} × 0.10)</span>
              </p>
            </div>
          </div>

          {/* Calculation Steps */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">How We Calculate Matches</h3>
            <div className="space-y-3">
              {explanationData.calculationSteps.map((step) => (
                <div key={step.step} className="flex space-x-4 p-4 bg-gray-50 rounded-lg">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 rounded-full bg-sky-500 text-white flex items-center justify-center font-bold">
                      {step.step}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-1">{step.description}</h4>
                    <p className="text-sm text-gray-600">{step.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Component Breakdown */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Score Components <span className="text-sm font-normal text-gray-500">(Click to expand details)</span>
            </h3>
            <div className="grid gap-4">
              {explanationData.components.map((component) => (
                <ComponentCard key={component.id} component={component} />
              ))}
            </div>
          </div>

          {/* Methodology Note */}
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700">
                <strong>Why Equal Weightage?</strong>
                <p className="mt-1">
                  We use a balanced weighting system where technical specifications (40%) are weighted highest as they're critical for RFP compliance. 
                  Brand (20%) and Price (20%) are equally important for competitive positioning. 
                  Availability (10%) and Certifications (10%) are essential but typically binary (you have them or you don't).
                </p>
                <p className="mt-2">
                  This methodology ensures we recommend products that meet technical requirements while remaining commercially competitive.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              <strong>Note:</strong> Scores are recalculated in real-time as product data updates
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition-colors font-medium"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpecMatchExplainer;
