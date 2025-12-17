import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, TrendingUp, FileCheck, DollarSign, Award, Info, X, AlertCircle } from 'lucide-react';

/**
 * QualityPreSubmissionScore Component
 * 
 * Displays internal quality assessment before final RFP submission.
 * Prevents submitting low-quality responses (<60% score).
 * 
 * Backend Integration:
 * - GET /api/v1/rfp/{rfp_id}/quality-score
 * - POST /api/v1/rfp/{rfp_id}/auto-fix
 * 
 * Quality Metrics:
 * - Completeness (40%): All sections filled, no missing data
 * - Technical Compliance (35%): Specs match, certifications valid
 * - Commercial Attractiveness (25%): Competitive pricing, good terms
 */

const QualityPreSubmissionScore = ({ rfpId, proposalData, onAutoFix, onSubmit, isOpen, onClose }) => {
  const [isFixing, setIsFixing] = useState(false);
  const [fixedIssues, setFixedIssues] = useState([]);

  // Real backend data structure (replace with API call)
  const qualityData = proposalData || {
    overallScore: 76,
    overallGrade: 'GOOD', // EXCELLENT (90+), GOOD (75-89), FAIR (60-74), POOR (<60)
    canSubmit: true, // false if score <60
    
    metrics: {
      completeness: {
        score: 85,
        weight: 40,
        weightedScore: 34.0,
        maxScore: 40,
        checks: [
          { item: 'Executive Summary', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: '850 words, covers all key points' },
          { item: 'Technical Response', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'All 24 line items matched' },
          { item: 'Pricing Breakdown', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'Detailed pricing with tests' },
          { item: 'Certifications Attached', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: '8 certificates included' },
          { item: 'Company Profile', status: 'warning', icon: AlertTriangle, color: 'text-amber-600', detail: 'Missing recent project references' },
          { item: 'Terms & Conditions', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'All terms addressed' }
        ],
        issues: [
          { severity: 'low', message: 'Company profile missing recent project references (last 3 projects)', autoFixable: false }
        ]
      },
      
      technicalCompliance: {
        score: 72,
        weight: 35,
        weightedScore: 25.2,
        maxScore: 35,
        checks: [
          { item: 'Spec Match Average', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: '91% average match across products' },
          { item: 'All Certifications Valid', status: 'warning', icon: AlertTriangle, color: 'text-amber-600', detail: '2 certificates expiring in 3 months' },
          { item: 'Test Requirements Covered', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'All 15 tests included' },
          { item: 'Delivery Timeline Feasible', status: 'warning', icon: AlertTriangle, color: 'text-amber-600', detail: 'Timeline tight - 2 day buffer only' },
          { item: 'Alternative Products Provided', status: 'error', icon: XCircle, color: 'text-red-600', detail: 'No alternatives for low-match items' },
          { item: 'Compliance Statements', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'All regulatory statements present' }
        ],
        issues: [
          { severity: 'medium', message: '2 certifications expiring within 90 days - include renewal status', autoFixable: true },
          { severity: 'medium', message: 'Delivery timeline has only 2-day buffer - add contingency note', autoFixable: true },
          { severity: 'high', message: '3 products with <85% match - provide alternatives or justification', autoFixable: false }
        ]
      },
      
      commercialAttractiveness: {
        score: 68,
        weight: 25,
        weightedScore: 17.0,
        maxScore: 25,
        checks: [
          { item: 'Pricing Competitiveness', status: 'warning', icon: AlertTriangle, color: 'text-amber-600', detail: '8% above market average' },
          { item: 'Payment Terms Favorable', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: '30-60 days offered' },
          { item: 'Discount Structure Clear', status: 'warning', icon: AlertTriangle, color: 'text-amber-600', detail: 'Volume discounts not clearly stated' },
          { item: 'Warranty Terms Competitive', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: '2-year warranty included' },
          { item: 'Value-Add Services', status: 'error', icon: XCircle, color: 'text-red-600', detail: 'No installation/training services mentioned' },
          { item: 'T&C Favorable to Client', status: 'complete', icon: CheckCircle2, color: 'text-green-600', detail: 'Standard favorable terms' }
        ],
        issues: [
          { severity: 'medium', message: 'Pricing 8% above market - justify with quality/service benefits', autoFixable: true },
          { severity: 'low', message: 'Volume discount structure unclear - specify tiers', autoFixable: true },
          { severity: 'high', message: 'No value-add services mentioned - add installation/training options', autoFixable: false }
        ]
      }
    },
    
    commonIssues: [
      { id: 1, severity: 'high', category: 'Technical', message: '3 products with match score <85% - provide alternatives', autoFixable: false, impact: 'May fail technical evaluation' },
      { id: 2, severity: 'high', category: 'Commercial', message: 'No value-add services (installation, training) mentioned', autoFixable: false, impact: 'Less competitive vs full-service bidders' },
      { id: 3, severity: 'medium', category: 'Technical', message: '2 certifications expiring in 90 days - add renewal status', autoFixable: true, impact: 'Client may question validity' },
      { id: 4, severity: 'medium', category: 'Commercial', message: 'Pricing 8% above market average - add justification', autoFixable: true, impact: 'May be rejected on price alone' },
      { id: 5, severity: 'medium', category: 'Technical', message: 'Delivery buffer only 2 days - add contingency note', autoFixable: true, impact: 'Risk of late delivery penalties' },
      { id: 6, severity: 'low', category: 'Completeness', message: 'Company profile missing recent project references', autoFixable: false, impact: 'Weakens credibility' },
      { id: 7, severity: 'low', category: 'Commercial', message: 'Volume discount tiers not clearly specified', autoFixable: true, impact: 'Missed negotiation opportunity' }
    ],
    
    recommendations: [
      { priority: 'CRITICAL', action: 'Add alternative products for 3 low-match items', reason: 'Shows problem-solving, increases win chance', effort: 'MEDIUM' },
      { priority: 'CRITICAL', action: 'Include value-add services (installation, training, AMC)', reason: 'Differentiates from competitors', effort: 'LOW' },
      { priority: 'HIGH', action: 'Add pricing justification section', reason: 'Explains 8% premium with quality/service benefits', effort: 'LOW' },
      { priority: 'HIGH', action: 'Update certification renewal status', reason: 'Addresses validity concerns proactively', effort: 'LOW' },
      { priority: 'MEDIUM', action: 'Add delivery contingency plan', reason: 'Shows risk management', effort: 'LOW' },
      { priority: 'MEDIUM', action: 'Clarify volume discount structure', reason: 'Enables better negotiation', effort: 'LOW' },
      { priority: 'LOW', action: 'Add recent project references', reason: 'Strengthens credibility', effort: 'HIGH' }
    ],
    
    autoFixCapability: {
      available: 4,
      total: 7,
      items: [
        'Add certification renewal status notes',
        'Insert pricing justification template',
        'Add delivery contingency standard clause',
        'Insert volume discount tier table'
      ]
    }
  };

  const handleAutoFix = async () => {
    setIsFixing(true);
    try {
      // Simulate API call to auto-fix issues
      await new Promise(resolve => setTimeout(resolve, 2000));
      setFixedIssues(qualityData.autoFixCapability.items);
      // Refresh quality score after fixes
      onAutoFix?.();
    } catch (error) {
      console.error('Auto-fix failed:', error);
    } finally {
      setIsFixing(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score) => {
    if (score >= 90) return 'bg-green-100 border-green-500';
    if (score >= 75) return 'bg-blue-100 border-blue-500';
    if (score >= 60) return 'bg-amber-100 border-amber-500';
    return 'bg-red-100 border-red-500';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className={`p-6 text-white ${
          qualityData.overallScore >= 90 ? 'bg-gradient-to-r from-green-500 to-emerald-600' :
          qualityData.overallScore >= 75 ? 'bg-gradient-to-r from-blue-500 to-indigo-600' :
          qualityData.overallScore >= 60 ? 'bg-gradient-to-r from-amber-500 to-orange-600' :
          'bg-gradient-to-r from-red-500 to-rose-600'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold mb-2">Quality Pre-Submission Assessment</h2>
              <p className="opacity-90">Internal quality check before final submission to client</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Overall Score Banner */}
        <div className={`p-6 border-b-2 ${getScoreBgColor(qualityData.overallScore)}`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Overall Quality Score</h3>
              <p className="text-gray-600">
                {qualityData.canSubmit 
                  ? 'Proposal meets minimum quality standards for submission'
                  : 'Proposal below minimum threshold - critical issues must be fixed'}
              </p>
            </div>
            <div className="text-right">
              <div className={`text-6xl font-bold ${getScoreColor(qualityData.overallScore)}`}>
                {qualityData.overallScore}
              </div>
              <div className="text-lg font-semibold text-gray-700 mt-1">
                {qualityData.overallGrade}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Quality Metrics Breakdown */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Quality Metrics Breakdown</h3>
            <div className="grid gap-6">
              {Object.entries(qualityData.metrics).map(([key, metric]) => (
                <div key={key} className="bg-white rounded-xl border-2 border-gray-200 p-6">
                  {/* Metric Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h4 className="text-lg font-bold text-gray-900 capitalize mb-1">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </h4>
                      <p className="text-sm text-gray-600">Weight: {metric.weight}% of total score</p>
                    </div>
                    <div className="text-right">
                      <div className={`text-3xl font-bold ${getScoreColor(metric.score)}`}>
                        {metric.score}%
                      </div>
                      <div className="text-sm text-gray-600">
                        {metric.weightedScore.toFixed(1)}/{metric.maxScore} points
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          metric.score >= 90 ? 'bg-green-500' :
                          metric.score >= 75 ? 'bg-blue-500' :
                          metric.score >= 60 ? 'bg-amber-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${metric.score}%` }}
                      />
                    </div>
                  </div>

                  {/* Checks */}
                  <div className="space-y-2 mb-4">
                    {metric.checks.map((check, idx) => {
                      const Icon = check.icon;
                      return (
                        <div key={idx} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                          <Icon className={`w-5 h-5 ${check.color} flex-shrink-0 mt-0.5`} />
                          <div className="flex-1">
                            <div className="flex justify-between items-start">
                              <span className="font-semibold text-gray-900">{check.item}</span>
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                check.status === 'complete' ? 'bg-green-100 text-green-700' :
                                check.status === 'warning' ? 'bg-amber-100 text-amber-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {check.status.toUpperCase()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{check.detail}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Issues */}
                  {metric.issues.length > 0 && (
                    <div className="space-y-2">
                      {metric.issues.map((issue, idx) => (
                        <div key={idx} className={`flex items-start space-x-3 p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}>
                          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                          <div className="flex-1">
                            <div className="flex justify-between items-start">
                              <span className="text-sm font-medium">{issue.message}</span>
                              {issue.autoFixable && (
                                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                                  Auto-fixable
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Common Issues */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Common Issues Detected ({qualityData.commonIssues.length})</h3>
            <div className="space-y-3">
              {qualityData.commonIssues.map((issue) => (
                <div key={issue.id} className={`p-4 rounded-lg border ${getSeverityColor(issue.severity)}`}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-semibold">{issue.category}</span>
                          <span>•</span>
                          <span className="text-sm uppercase font-bold">{issue.severity} Priority</span>
                        </div>
                        <p className="text-sm">{issue.message}</p>
                        <p className="text-xs mt-1 opacity-75">Impact: {issue.impact}</p>
                      </div>
                    </div>
                    {issue.autoFixable && (
                      <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-bold whitespace-nowrap">
                        Auto-fix Available
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Recommended Actions</h3>
            <div className="space-y-3">
              {qualityData.recommendations.map((rec, idx) => (
                <div key={idx} className="bg-white rounded-lg border-2 border-gray-200 p-4 hover:border-sky-300 transition-colors">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          rec.priority === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                          rec.priority === 'HIGH' ? 'bg-amber-100 text-amber-700' :
                          'bg-blue-100 text-blue-700'
                        }`}>
                          {rec.priority}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          rec.effort === 'LOW' ? 'bg-green-100 text-green-700' :
                          rec.effort === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {rec.effort} Effort
                        </span>
                      </div>
                      <h4 className="font-semibold text-gray-900 mb-1">{rec.action}</h4>
                      <p className="text-sm text-gray-600">{rec.reason}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Auto-Fix Capability */}
          {qualityData.autoFixCapability.available > 0 && (
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border-2 border-green-200">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">Automatic Fixes Available</h3>
                  <p className="text-gray-600 mb-4">
                    {qualityData.autoFixCapability.available} out of {qualityData.autoFixCapability.total} issues can be automatically fixed
                  </p>
                  <ul className="space-y-2">
                    {qualityData.autoFixCapability.items.map((item, idx) => (
                      <li key={idx} className="flex items-center space-x-2 text-sm text-gray-700">
                        <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <button
                  onClick={handleAutoFix}
                  disabled={isFixing || fixedIssues.length > 0}
                  className={`px-6 py-3 rounded-lg font-bold transition-all ${
                    isFixing || fixedIssues.length > 0
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-green-500 text-white hover:bg-green-600 hover:scale-105 shadow-lg'
                  }`}
                >
                  {isFixing ? 'Fixing...' : fixedIssues.length > 0 ? 'Fixed ✓' : 'Auto-Fix Issues'}
                </button>
              </div>

              {fixedIssues.length > 0 && (
                <div className="mt-4 p-4 bg-white rounded-lg border border-green-300">
                  <h4 className="font-semibold text-green-900 mb-2 flex items-center">
                    <CheckCircle2 className="w-5 h-5 mr-2" />
                    Successfully Fixed {fixedIssues.length} Issues
                  </h4>
                  <p className="text-sm text-green-800">
                    Quality score will increase after re-evaluation. Review changes before submission.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="flex items-center justify-between">
            <div>
              {!qualityData.canSubmit && (
                <div className="flex items-center space-x-2 text-red-600">
                  <XCircle className="w-5 h-5" />
                  <span className="font-semibold">Cannot submit - score below 60% minimum threshold</span>
                </div>
              )}
              {qualityData.canSubmit && qualityData.overallScore < 75 && (
                <div className="flex items-center space-x-2 text-amber-600">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-semibold">Can submit, but quality improvements recommended</span>
                </div>
              )}
              {qualityData.canSubmit && qualityData.overallScore >= 75 && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-semibold">High quality - ready for submission</span>
                </div>
              )}
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-semibold"
              >
                Review More
              </button>
              <button
                onClick={() => onSubmit?.(qualityData)}
                disabled={!qualityData.canSubmit}
                className={`px-8 py-3 rounded-lg font-bold transition-all ${
                  qualityData.canSubmit
                    ? 'bg-sky-500 text-white hover:bg-sky-600 hover:scale-105 shadow-lg'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {qualityData.canSubmit ? 'Proceed to Submit' : 'Fix Issues First'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QualityPreSubmissionScore;
