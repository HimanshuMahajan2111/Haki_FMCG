import React, { useState, useEffect } from 'react';
import { X, Loader, CheckCircle, Clock, AlertCircle, TrendingUp, FileText, Package, TestTube, Brain, Zap, Sparkles } from 'lucide-react';

const ProcessingProgressModal = ({ rfpId, onClose, onComplete }) => {
  const [progress, setProgress] = useState({
    status: 'processing',
    progress: 0,
    current_stage: 'Initializing',
    agents_status: {},
    estimated_time_remaining: '2-5 minutes'
  });
  const [currentTipIndex, setCurrentTipIndex] = useState(0);
  const [dots, setDots] = useState('');
  const [isCompleted, setIsCompleted] = useState(false);

  const tips = [
    '💡 Analyzing your RFP requirements...',
    '🎯 Searching through 50,000+ products...',
    '⚡ AI matching specifications intelligently...',
    '🔍 Checking compliance standards...',
    '📊 Optimizing pricing strategies...',
    '✨ Preparing your response...',
  ];

  useEffect(() => {
    if (!rfpId || isCompleted) return;

    // Poll for progress updates
    const interval = setInterval(async () => {
      try {
        // Check progress
        const progressResponse = await fetch(`http://localhost:8000/api/rfp-workflow/progress/${rfpId}`);
        if (progressResponse.ok) {
          const progressData = await progressResponse.json();
          setProgress(progressData);

          // Check if completed via progress status
          if (progressData.status === 'completed' || progressData.progress >= 100) {
            setIsCompleted(true);
            clearInterval(interval);
            setTimeout(() => {
              if (onComplete) onComplete();
            }, 2000);
            return;
          }
        }

        // Also check RFP status directly (in case progress tracker state is lost)
        const rfpResponse = await fetch(`http://localhost:8000/api/rfp/${rfpId}`);
        if (rfpResponse.ok) {
          const rfpData = await rfpResponse.json();
          if (rfpData.data && (rfpData.data.status === 'reviewed' || rfpData.data.status === 'cancelled')) {
            setIsCompleted(true);
            clearInterval(interval);
            // Update progress to show completion
            setProgress(prev => ({ ...prev, status: 'completed', progress: 100 }));
            setTimeout(() => {
              if (onComplete) onComplete();
            }, 2000);
          }
        }
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [rfpId, onComplete, isCompleted]);

  // Rotating tips
  useEffect(() => {
    const tipInterval = setInterval(() => {
      setCurrentTipIndex((prev) => (prev + 1) % tips.length);
    }, 3000);
    return () => clearInterval(tipInterval);
  }, []);

  // Animated dots
  useEffect(() => {
    const dotInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);
    return () => clearInterval(dotInterval);
  }, []);

  const getAgentIcon = (agentName) => {
    const icons = {
      'extraction': <FileText size={20} />,
      'matching': <Package size={20} />,
      'pricing': <TrendingUp size={20} />,
      'compliance': <TestTube size={20} />
    };
    return icons[agentName.toLowerCase()] || <Loader size={20} />;
  };

  const getStatusColor = (status) => {
    const colors = {
      'running': 'text-blue-600',
      'completed': 'text-green-600',
      'failed': 'text-red-600',
      'pending': 'text-gray-400'
    };
    return colors[status] || 'text-gray-400';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'running': <Loader className="animate-spin" size={18} />,
      'completed': <CheckCircle size={18} />,
      'failed': <AlertCircle size={18} />,
      'pending': <Clock size={18} />
    };
    return icons[status] || <Clock size={18} />;
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse"></div>
        
        {/* Close/Cancel Button */}
        {progress.status !== 'completed' && (
          <button
            onClick={async () => {
              if (window.confirm('Cancel RFP processing? This will stop all agents.')) {
                try {
                  await fetch(`http://localhost:8000/api/rfp-workflow/cancel/${rfpId}`, {
                    method: 'POST'
                  });
                  onClose();
                } catch (error) {
                  console.error('Failed to cancel:', error);
                  onClose();
                }
              }
            }}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-colors z-10"
          >
            <X size={24} className="text-gray-600" />
          </button>
        )}
        
        {/* Header with Animation */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4 animate-bounce">
            <Brain className="text-white" size={40} />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Processing RFP #{rfpId}
          </h2>
          <p className="text-sm text-gray-600 animate-pulse">
            {tips[currentTipIndex]}
          </p>
        </div>

        {/* Progress Bar with Sparkle */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <Sparkles size={16} className="text-yellow-500" />
              {progress.current_stage}{dots}
            </span>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {progress.progress}%
            </span>
          </div>
          <div className="relative w-full bg-gray-200 rounded-full h-5 overflow-hidden shadow-inner">
            <div
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${progress.progress}%` }}
            >
              <div className="absolute inset-0 bg-white/30 animate-shimmer" style={{
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent)',
                animation: 'shimmer 2s infinite'
              }}></div>
            </div>
          </div>
        </div>

        {/* Estimated Time with Better Design */}
        {progress.estimated_time_remaining && progress.status !== 'completed' && (
          <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border-2 border-blue-200">
            <div className="flex items-center justify-center gap-3">
              <Zap className="text-yellow-500 animate-pulse" size={20} />
              <span className="text-sm font-semibold text-gray-700">
                Est. Time: {progress.estimated_time_remaining}
              </span>
              <Clock className="text-blue-600 animate-spin" size={20} style={{ animationDuration: '3s' }} />
            </div>
          </div>
        )}

        {/* Agent Status - More Engaging */}
        <div className="space-y-3 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Zap size={18} className="text-yellow-500" />
            AI Agents at Work
          </h3>
          {Object.keys(progress.agents_status).length > 0 ? (
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(progress.agents_status).map(([agentName, agentData]) => (
                <div
                  key={agentName}
                  className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                    agentData.status === 'running' 
                      ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-lg transform scale-105' 
                      : agentData.status === 'completed'
                      ? 'bg-green-50 border-green-300'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`${getStatusColor(agentData.status)} ${agentData.status === 'running' ? 'animate-bounce' : ''}`}>
                      {getAgentIcon(agentName)}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 capitalize mb-1">
                        {agentName}
                      </div>
                      <div className={`flex items-center gap-2 mb-1 ${getStatusColor(agentData.status)}`}>
                        {getStatusIcon(agentData.status)}
                        <span className="text-xs font-medium uppercase">
                          {agentData.status === 'running' ? `${agentData.status}${dots}` : agentData.status}
                        </span>
                      </div>
                      {agentData.details && (
                        <div className="text-xs text-gray-600">{agentData.details}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Loader className="animate-spin text-blue-600 mx-auto mb-4" size={40} />
              <p className="text-lg font-medium text-gray-900 mb-2">Starting AI Engines{dots}</p>
              <p className="text-sm text-gray-600">Preparing intelligent agents for analysis</p>
            </div>
          )}
        </div>

        {/* Completion Message */}
        {progress.status === 'completed' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle className="text-green-600" size={24} />
            <div className="flex-1">
              <p className="font-medium text-green-900">Processing Complete!</p>
              <p className="text-sm text-green-700">Your RFP has been analyzed successfully</p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {progress.status === 'failed' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="text-red-600" size={24} />
            <div className="flex-1">
              <p className="font-medium text-red-900">Processing Failed</p>
              <p className="text-sm text-red-700">An error occurred during processing</p>
            </div>
          </div>
        )}

        {/* Footer */}
        {progress.status === 'completed' && (
          <div className="mt-6 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors font-medium"
            >
              View Results
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
                    onClose();
                  } else {
                    alert('❌ Failed to submit response');
                  }
                } catch (error) {
                  console.error('Error submitting response:', error);
                  alert('❌ Error submitting response');
                }
              }}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium flex items-center gap-2"
            >
              <CheckCircle size={18} />
              Submit Response
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingProgressModal;

// Add these styles to your global CSS or tailwind.config.js
// @keyframes shimmer {
//   0% { transform: translateX(-100%); }
//   100% { transform: translateX(100%); }
// }
// @keyframes pulse-slow {
//   0%, 100% { opacity: 1; }
//   50% { opacity: 0.8; }
// }
// .animate-shimmer { animation: shimmer 2s infinite; }
// .animate-pulse-slow { animation: pulse-slow 2s infinite; }
// .animate-fade-in { animation: fadeIn 0.5s ease-in; }
// @keyframes fadeIn {
//   from { opacity: 0; transform: translateY(-10px); }
//   to { opacity: 1; transform: translateY(0); }
// }
