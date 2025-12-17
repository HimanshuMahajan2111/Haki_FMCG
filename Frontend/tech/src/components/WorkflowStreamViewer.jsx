 
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useWorkflowStream } from '../hooks/useRFPApi';
import { Radio, CheckCircle, XCircle, Clock, Zap, MessageSquare } from 'lucide-react';

export default function WorkflowStreamViewer() {
  const { workflowId } = useParams();
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  const { streamData, isConnected: connected, error } = useWorkflowStream(workflowId);

  // Update connection status
  useEffect(() => {
    setIsConnected(connected);
  }, [connected]);

  // Add new stream data to logs
  useEffect(() => {
    if (streamData) {
      setLogs(prev => [...prev, { ...streamData, timestamp: new Date() }]);
    }
  }, [streamData]);

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold mb-2">Live Workflow Stream</h1>
            <p className="text-gray-600">
              Workflow ID: <span className="font-mono text-sm">{workflowId}</span>
            </p>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-3">
            <ConnectionStatus isConnected={isConnected} />
            <button
              onClick={clearLogs}
              className="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50"
            >
              Clear Logs
            </button>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-800">Connection Error</p>
              <p className="text-sm text-red-600 mt-1">{error.message}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stream Logs */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-3 border-b flex justify-between items-center">
          <h2 className="font-semibold">Event Stream</h2>
          <span className="text-sm text-gray-600">{logs.length} events</span>
        </div>

        {/* Logs Container */}
        <div className="h-[600px] overflow-y-auto">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Radio className="w-16 h-16 mb-4" />
              <p>Waiting for events...</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {logs.map((log, index) => (
                <LogEntry key={index} log={log} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="mt-6 bg-blue-50 rounded-lg p-6">
        <h3 className="font-medium text-blue-900 mb-3">About Real-time Streaming</h3>
        <div className="space-y-2 text-sm text-blue-700">
          <p>• Server-Sent Events (SSE) provide live updates as the workflow progresses</p>
          <p>• Events include stage transitions, agent communications, and status changes</p>
          <p>• Connection automatically reconnects if interrupted</p>
          <p>• All events are timestamped and logged in chronological order</p>
        </div>
      </div>
    </div>
  );
}

// Connection Status Component
function ConnectionStatus({ isConnected }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-full ${
      isConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
    }`}>
      <div className={`w-2 h-2 rounded-full ${
        isConnected ? 'bg-green-600 animate-pulse' : 'bg-gray-400'
      }`}></div>
      <span className="text-xs font-medium">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}

// Log Entry Component
function LogEntry({ log }) {
  const getEventIcon = (type) => {
    switch (type) {
      case 'stage_start':
      case 'stage_complete':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'stage_error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'agent_message':
        return <MessageSquare className="w-5 h-5 text-blue-600" />;
      case 'status_update':
        return <Zap className="w-5 h-5 text-yellow-600" />;
      default:
        return <Radio className="w-5 h-5 text-gray-600" />;
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'stage_complete':
        return 'border-l-green-500 bg-green-50';
      case 'stage_error':
        return 'border-l-red-500 bg-red-50';
      case 'agent_message':
        return 'border-l-blue-500 bg-blue-50';
      case 'status_update':
        return 'border-l-yellow-500 bg-yellow-50';
      case 'stage_start':
        return 'border-l-purple-500 bg-purple-50';
      default:
        return 'border-l-gray-300 bg-white';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  return (
    <div className={`border-l-4 p-4 ${getEventColor(log.event)}`}>
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="mt-0.5">
          {getEventIcon(log.event)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-1">
            <div>
              <span className="font-medium text-gray-900 capitalize">
                {log.event?.replace(/_/g, ' ')}
              </span>
              {log.stage && (
                <span className="ml-2 text-sm text-gray-600">
                  • {log.stage.replace(/_/g, ' ')}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              {formatTimestamp(log.timestamp)}
            </div>
          </div>

          {/* Message */}
          {log.message && (
            <p className="text-sm text-gray-700 mb-2">{log.message}</p>
          )}

          {/* Agent Info */}
          {log.agent && (
            <div className="text-xs text-gray-600 mb-2">
              Agent: <span className="font-medium">{log.agent}</span>
            </div>
          )}

          {/* Data */}
          {log.data && Object.keys(log.data).length > 0 && (
            <details className="mt-2">
              <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                View data
              </summary>
              <pre className="mt-2 text-xs bg-white border border-gray-200 rounded p-2 overflow-x-auto">
                {JSON.stringify(log.data, null, 2)}
              </pre>
            </details>
          )}

          {/* Progress */}
          {log.progress !== undefined && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Progress</span>
                <span>{log.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div
                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${log.progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Error Details */}
          {log.error && (
            <div className="mt-2 bg-red-100 border border-red-200 rounded p-2">
              <p className="text-xs font-medium text-red-800 mb-1">Error Details:</p>
              <p className="text-xs text-red-700">{log.error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
