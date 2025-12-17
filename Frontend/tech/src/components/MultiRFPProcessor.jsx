import React, { useState, useEffect } from 'react';
import { Play, Pause, XCircle, CheckCircle2, Clock, Zap, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge, Button } from './UI';
import api from '../services/api';

const MultiRFPProcessor = ({ selectedRfps = [] }) => {
  const [processingQueue, setProcessingQueue] = useState([]);
  const [activeProcesses, setActiveProcesses] = useState([]);
  const [completedProcesses, setCompletedProcesses] = useState([]);
  const [maxParallel, setMaxParallel] = useState(3);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (selectedRfps.length > 0) {
      initializeQueue();
    }
  }, [selectedRfps]);

  useEffect(() => {
    if (isProcessing && activeProcesses.length < maxParallel && processingQueue.length > 0) {
      startNextProcess();
    }
  }, [isProcessing, activeProcesses, processingQueue, maxParallel]);

  const initializeQueue = () => {
    const queue = selectedRfps.map(rfp => ({
      id: rfp.id,
      rfp_id: rfp.rfp_id || `RFP-${rfp.id}`,
      title: rfp.title,
      status: 'queued',
      progress: 0,
      startTime: null,
      endTime: null,
      stages: [
        { name: 'Parsing', status: 'pending', progress: 0 },
        { name: 'Technical Analysis', status: 'pending', progress: 0 },
        { name: 'Pricing', status: 'pending', progress: 0 },
        { name: 'Response Generation', status: 'pending', progress: 0 }
      ],
      workflow_id: null,
      error: null
    }));
    setProcessingQueue(queue);
    setActiveProcesses([]);
    setCompletedProcesses([]);
  };

  const startNextProcess = async () => {
    if (processingQueue.length === 0) return;

    const nextRfp = processingQueue[0];
    const updatedQueue = processingQueue.slice(1);
    
    const activeRfp = {
      ...nextRfp,
      status: 'processing',
      startTime: new Date()
    };

    setProcessingQueue(updatedQueue);
    setActiveProcesses(prev => [...prev, activeRfp]);

    try {
      const response = await api.post('/api/v1/rfp/submit', {
        rfp_id: activeRfp.rfp_id,
        customer_id: 'MULTI_PROCESS',
        template_id: 'standard_rfp',
        priority: 'high'
      });

      const workflowId = response.data.workflow_id;
      updateActiveProcess(activeRfp.id, { workflow_id: workflowId });
      
      // Start polling for status
      pollWorkflowStatus(activeRfp.id, workflowId);
    } catch (error) {
      console.error(`Error starting RFP ${activeRfp.id}:`, error);
      moveToCompleted(activeRfp.id, { 
        status: 'failed', 
        error: error.message,
        endTime: new Date()
      });
    }
  };

  const pollWorkflowStatus = async (rfpId, workflowId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/api/v1/rfp/status/${workflowId}`);
        const statusData = response.data;

        updateActiveProcess(rfpId, {
          progress: calculateProgress(statusData),
          stages: updateStages(statusData)
        });

        if (statusData.status === 'completed') {
          clearInterval(pollInterval);
          moveToCompleted(rfpId, {
            status: 'completed',
            endTime: new Date(),
            progress: 100
          });
        } else if (statusData.status === 'failed') {
          clearInterval(pollInterval);
          moveToCompleted(rfpId, {
            status: 'failed',
            error: statusData.error || 'Processing failed',
            endTime: new Date()
          });
        }
      } catch (error) {
        console.error(`Error polling workflow ${workflowId}:`, error);
      }
    }, 2000); // Poll every 2 seconds
  };

  const calculateProgress = (statusData) => {
    const stages = ['parsing', 'technical_analysis', 'pricing', 'response_generation'];
    const currentStageIndex = stages.indexOf(statusData.current_stage);
    if (currentStageIndex === -1) return 0;
    return ((currentStageIndex + 1) / stages.length) * 100;
  };

  const updateStages = (statusData) => {
    const stageMap = {
      'parsing': 0,
      'technical_analysis': 1,
      'pricing': 2,
      'response_generation': 3
    };

    const currentStageIndex = stageMap[statusData.current_stage];
    
    return [
      { name: 'Parsing', status: currentStageIndex > 0 ? 'completed' : currentStageIndex === 0 ? 'processing' : 'pending', progress: currentStageIndex > 0 ? 100 : currentStageIndex === 0 ? 50 : 0 },
      { name: 'Technical Analysis', status: currentStageIndex > 1 ? 'completed' : currentStageIndex === 1 ? 'processing' : 'pending', progress: currentStageIndex > 1 ? 100 : currentStageIndex === 1 ? 50 : 0 },
      { name: 'Pricing', status: currentStageIndex > 2 ? 'completed' : currentStageIndex === 2 ? 'processing' : 'pending', progress: currentStageIndex > 2 ? 100 : currentStageIndex === 2 ? 50 : 0 },
      { name: 'Response Generation', status: currentStageIndex > 3 ? 'completed' : currentStageIndex === 3 ? 'processing' : 'pending', progress: currentStageIndex > 3 ? 100 : currentStageIndex === 3 ? 50 : 0 }
    ];
  };

  const updateActiveProcess = (rfpId, updates) => {
    setActiveProcesses(prev =>
      prev.map(p => p.id === rfpId ? { ...p, ...updates } : p)
    );
  };

  const moveToCompleted = (rfpId, updates) => {
    const process = activeProcesses.find(p => p.id === rfpId);
    if (process) {
      setCompletedProcesses(prev => [...prev, { ...process, ...updates }]);
      setActiveProcesses(prev => prev.filter(p => p.id !== rfpId));
    }
  };

  const handleStartProcessing = () => {
    setIsProcessing(true);
  };

  const handlePauseProcessing = () => {
    setIsProcessing(false);
  };

  const handleCancelProcess = (rfpId) => {
    // Move from active to completed with cancelled status
    const process = activeProcesses.find(p => p.id === rfpId);
    if (process) {
      moveToCompleted(rfpId, {
        status: 'cancelled',
        endTime: new Date()
      });
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-400" />;
      case 'failed':
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'processing':
        return <Zap className="w-5 h-5 text-yellow-400 animate-pulse" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      'queued': 'default',
      'processing': 'warning',
      'completed': 'success',
      'failed': 'danger',
      'cancelled': 'default'
    };
    return variants[status] || 'default';
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'N/A';
    const end = endTime || new Date();
    const duration = Math.floor((end - startTime) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  const renderProcessCard = (process, type) => {
    return (
      <div key={process.id} className="p-4 bg-dark-700 rounded-lg border border-dark-600">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3 flex-1">
            {getStatusIcon(process.status)}
            <div className="flex-1">
              <h4 className="font-semibold text-white">{process.title}</h4>
              <p className="text-sm text-gray-400">{process.rfp_id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getStatusBadge(process.status)}>
              {process.status}
            </Badge>
            {type === 'active' && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleCancelProcess(process.id)}
              >
                <XCircle className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-400">Overall Progress</span>
            <span className="text-white font-semibold">{Math.round(process.progress)}%</span>
          </div>
          <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                process.status === 'failed' ? 'bg-red-500' :
                process.status === 'completed' ? 'bg-green-500' :
                'bg-gradient-to-r from-primary-500 to-secondary-500'
              }`}
              style={{ width: `${process.progress}%` }}
            />
          </div>
        </div>

        {/* Stages */}
        <div className="space-y-2">
          {process.stages.map((stage, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              {stage.status === 'completed' && <CheckCircle2 className="w-4 h-4 text-green-400" />}
              {stage.status === 'processing' && <Zap className="w-4 h-4 text-yellow-400 animate-pulse" />}
              {stage.status === 'pending' && <Clock className="w-4 h-4 text-gray-500" />}
              <span className={`flex-1 ${
                stage.status === 'completed' ? 'text-green-400' :
                stage.status === 'processing' ? 'text-yellow-400' :
                'text-gray-500'
              }`}>
                {stage.name}
              </span>
            </div>
          ))}
        </div>

        {/* Time Info */}
        <div className="mt-3 pt-3 border-t border-dark-600 flex items-center justify-between text-sm">
          <span className="text-gray-400">Duration</span>
          <span className="text-white font-semibold">
            {formatDuration(process.startTime, process.endTime)}
          </span>
        </div>

        {process.error && (
          <div className="mt-3 p-2 bg-red-500/10 border border-red-500 rounded text-sm text-red-400">
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            {process.error}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Multi-RFP Parallel Processing</CardTitle>
              <p className="text-sm text-gray-400 mt-1">
                Process multiple RFPs simultaneously for faster turnaround
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-400">Max Parallel:</label>
                <select
                  value={maxParallel}
                  onChange={(e) => setMaxParallel(Number(e.target.value))}
                  disabled={isProcessing}
                  className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value={1}>1</option>
                  <option value={2}>2</option>
                  <option value={3}>3</option>
                  <option value={4}>4</option>
                  <option value={5}>5</option>
                </select>
              </div>
              {!isProcessing ? (
                <Button
                  variant="primary"
                  onClick={handleStartProcessing}
                  disabled={processingQueue.length === 0 && activeProcesses.length === 0}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Processing
                </Button>
              ) : (
                <Button variant="warning" onClick={handlePauseProcessing}>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-gray-400">{processingQueue.length}</p>
              <p className="text-sm text-gray-400 mt-1">In Queue</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-yellow-400">{activeProcesses.length}</p>
              <p className="text-sm text-gray-400 mt-1">Processing</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-green-400">
                {completedProcesses.filter(p => p.status === 'completed').length}
              </p>
              <p className="text-sm text-gray-400 mt-1">Completed</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <p className="text-3xl font-bold text-red-400">
                {completedProcesses.filter(p => p.status === 'failed' || p.status === 'cancelled').length}
              </p>
              <p className="text-sm text-gray-400 mt-1">Failed/Cancelled</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Active Processes */}
      {activeProcesses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Processes ({activeProcesses.length})</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeProcesses.map(process => renderProcessCard(process, 'active'))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Queue */}
      {processingQueue.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Queued ({processingQueue.length})</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-2">
              {processingQueue.map((process, idx) => (
                <div key={process.id} className="flex items-center gap-3 p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-500 font-semibold">#{idx + 1}</span>
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="flex-1 text-white">{process.title}</span>
                  <Badge variant="default">Queued</Badge>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Completed */}
      {completedProcesses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Completed ({completedProcesses.length})</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {completedProcesses.map(process => renderProcessCard(process, 'completed'))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default MultiRFPProcessor;
