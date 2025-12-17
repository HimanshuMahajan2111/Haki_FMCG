import React, { useState, useEffect } from 'react';
import { Activity, Zap, CheckCircle2, Clock, AlertTriangle, Users, RefreshCw, Play, Pause } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge, Button } from './UI';

const WorkflowOrchestratorDashboard = () => {
  const [activeWorkflows, setActiveWorkflows] = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const [systemMetrics, setSystemMetrics] = useState({});
  const [refreshInterval, setRefreshInterval] = useState(2000);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    
    let interval;
    if (isAutoRefresh) {
      interval = setInterval(fetchDashboardData, refreshInterval);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAutoRefresh, refreshInterval]);

  const fetchDashboardData = async () => {
    try {
      // Fetch real workflow data from API
      const { listWorkflows, getAgentLogs, getDashboard } = await import('../services/api');
      
      const [workflowsData, agentLogsData, dashboardData] = await Promise.all([
        listWorkflows(null, 50).catch(() => []),
        getAgentLogs(null, 100).catch(() => ({ logs: [] })),
        getDashboard(1).catch(() => ({ rfp_processing: {} }))
      ]);

      // Transform real workflow data
      const workflows = Array.isArray(workflowsData) ? workflowsData : [];
      const transformedWorkflows = workflows.map(wf => {
        const stages = ['parsing', 'technical_analysis', 'pricing', 'response_generation'];
        const currentStageIndex = stages.indexOf(wf.current_stage || 'parsing');
        const completedStages = wf.stages_completed || [];
        const progress = Math.round((completedStages.length / stages.length) * 100);
        
        // Determine agent statuses based on workflow stage
        const agents = [
          { name: 'Parser Agent', status: completedStages.includes('parsing') ? 'completed' : (currentStageIndex === 0 ? 'processing' : 'waiting'), duration: 0 },
          { name: 'Technical Agent', status: completedStages.includes('technical_analysis') ? 'completed' : (currentStageIndex === 1 ? 'processing' : (currentStageIndex > 1 ? 'waiting' : 'waiting')), duration: 0 },
          { name: 'Pricing Agent', status: completedStages.includes('pricing') ? 'completed' : (currentStageIndex === 2 ? 'processing' : (currentStageIndex > 2 ? 'waiting' : 'waiting')), duration: 0 },
          { name: 'Response Agent', status: completedStages.includes('response_generation') ? 'completed' : (currentStageIndex === 3 ? 'processing' : 'waiting'), duration: 0 }
        ];

        return {
          id: wf.workflow_id,
          rfp_id: wf.rfp_id || `RFP-${wf.workflow_id.slice(-6)}`,
          rfp_title: wf.metadata?.title || `Workflow ${wf.workflow_id.slice(0, 8)}`,
          status: wf.status,
          current_stage: wf.current_stage || 'parsing',
          progress: progress,
          start_time: new Date(wf.start_time || Date.now()),
          agents: agents
        };
      });

      // Calculate agent status from logs
      const logs = agentLogsData.logs || [];
      const agentStatus = {
        sales_agent: { status: 'active', current_tasks: workflows.filter(w => w.status === 'in_progress').length, completed_today: logs.filter(l => l.agent_name === 'sales_agent').length },
        technical_agent: { status: 'active', current_tasks: workflows.filter(w => w.current_stage === 'technical_analysis').length, completed_today: logs.filter(l => l.agent_name === 'technical_agent').length },
        pricing_agent: { status: 'active', current_tasks: workflows.filter(w => w.current_stage === 'pricing').length, completed_today: logs.filter(l => l.agent_name === 'pricing_agent').length },
        parser_agent: { status: 'active', current_tasks: workflows.filter(w => w.current_stage === 'parsing').length, completed_today: logs.filter(l => l.agent_name === 'parser_agent').length },
        response_agent: { status: workflows.filter(w => w.current_stage === 'response_generation').length > 0 ? 'active' : 'idle', current_tasks: workflows.filter(w => w.current_stage === 'response_generation').length, completed_today: logs.filter(l => l.agent_name === 'response_agent').length },
        orchestrator: { status: 'active', current_tasks: workflows.length, completed_today: workflows.filter(w => w.status === 'completed').length }
      };

      // Calculate system metrics from real data
      const rfpProcessing = dashboardData.rfp_processing || {};
      const systemMetrics = {
        active_workflows: workflows.filter(w => w.status === 'in_progress').length,
        queued_workflows: workflows.filter(w => w.status === 'pending').length,
        completed_today: workflows.filter(w => w.status === 'completed').length,
        average_processing_time: Math.round((rfpProcessing.average_processing_time_seconds || 0) / 60),
        agent_utilization: Math.round((workflows.length / Math.max(1, workflows.length + 5)) * 100),
        success_rate: workflows.length > 0 ? Math.round((workflows.filter(w => w.status === 'completed').length / workflows.length) * 100) : 0
      };

      setActiveWorkflows(transformedWorkflows);
      setAgentStatus(agentStatus);
      setSystemMetrics(systemMetrics);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Set empty state on error
      setActiveWorkflows([]);
      setAgentStatus({});
      setSystemMetrics({
        active_workflows: 0,
        queued_workflows: 0,
        completed_today: 0,
        average_processing_time: 0,
        agent_utilization: 0,
        success_rate: 0
      });
    }
  };

  const getAgentStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'processing':
        return <Activity className="w-4 h-4 text-yellow-400 animate-pulse" />;
      case 'waiting':
        return <Clock className="w-4 h-4 text-gray-500" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-400';
      case 'idle':
        return 'text-gray-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatDuration = (startTime) => {
    const duration = Math.floor((new Date() - startTime) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  };

  const renderWorkflowCard = (workflow) => {
    return (
      <div key={workflow.id} className="p-4 bg-dark-700 rounded-lg border-2 border-dark-600 hover:border-primary-500 transition-all">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h4 className="font-semibold text-white mb-1">{workflow.rfp_title}</h4>
            <p className="text-sm text-gray-400">{workflow.rfp_id}</p>
          </div>
          <Badge variant="warning">
            {workflow.current_stage.replace('_', ' ')}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-400">Progress</span>
            <span className="text-white font-semibold">{workflow.progress}%</span>
          </div>
          <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-secondary-500 transition-all duration-500"
              style={{ width: `${workflow.progress}%` }}
            />
          </div>
        </div>

        {/* Agent Status Grid */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {workflow.agents.map((agent, idx) => (
            <div
              key={idx}
              className={`p-2 rounded-lg border ${
                agent.status === 'completed' ? 'bg-green-500/10 border-green-500/30' :
                agent.status === 'processing' ? 'bg-yellow-500/10 border-yellow-500/30' :
                'bg-dark-800 border-dark-600'
              }`}
            >
              <div className="flex items-center gap-2">
                {getAgentStatusIcon(agent.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-400 truncate">{agent.name}</p>
                  {agent.duration > 0 && (
                    <p className="text-xs text-white font-semibold">{agent.duration}s</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-dark-600">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">{formatDuration(workflow.start_time)}</span>
          </div>
          <Button variant="primary" size="sm">
            View Details
          </Button>
        </div>
      </div>
    );
  };

  const renderAgentCard = (name, data) => {
    return (
      <div key={name} className="p-4 bg-dark-700 rounded-lg border border-dark-600">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${
              data.status === 'active' ? 'bg-green-500/20' :
              data.status === 'error' ? 'bg-red-500/20' :
              'bg-gray-500/20'
            }`}>
              <Users className={`w-5 h-5 ${getStatusColor(data.status)}`} />
            </div>
            <div>
              <h4 className="font-semibold text-white capitalize">
                {name.replace('_', ' ')}
              </h4>
              <p className={`text-xs ${getStatusColor(data.status)}`}>
                {data.status.toUpperCase()}
              </p>
            </div>
          </div>
          {data.status === 'active' && (
            <Activity className="w-5 h-5 text-green-400 animate-pulse" />
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-gray-400">Current Tasks</p>
            <p className="text-xl font-bold text-white">{data.current_tasks}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400">Completed Today</p>
            <p className="text-xl font-bold text-primary-400">{data.completed_today}</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Workflow Orchestrator</h2>
          <p className="text-sm text-gray-400">Real-time parallel agent execution monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value={1000}>1s refresh</option>
            <option value={2000}>2s refresh</option>
            <option value={5000}>5s refresh</option>
            <option value={10000}>10s refresh</option>
          </select>
          <Button
            variant={isAutoRefresh ? 'warning' : 'primary'}
            size="sm"
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
          >
            {isAutoRefresh ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                Pause
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Resume
              </>
            )}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchDashboardData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-6 gap-4">
        <Card>
          <CardBody>
            <div className="text-center">
              <Activity className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.active_workflows}</p>
              <p className="text-sm text-gray-400">Active</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <Clock className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.queued_workflows}</p>
              <p className="text-sm text-gray-400">Queued</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.completed_today}</p>
              <p className="text-sm text-gray-400">Completed</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <Zap className="w-8 h-8 text-primary-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.average_processing_time}</p>
              <p className="text-sm text-gray-400">Avg Time (min)</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <Users className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.agent_utilization}%</p>
              <p className="text-sm text-gray-400">Utilization</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="text-center">
              <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-3xl font-bold text-white">{systemMetrics.success_rate}%</p>
              <p className="text-sm text-gray-400">Success Rate</p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Active Workflows */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Active Workflows ({activeWorkflows.length})</CardTitle>
            <Badge variant="warning">
              <Activity className="w-4 h-4 mr-1 animate-pulse" />
              Live Updates
            </Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeWorkflows.map(workflow => renderWorkflowCard(workflow))}
          </div>
        </CardBody>
      </Card>

      {/* Agent Status Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Status</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(agentStatus).map(([name, data]) => renderAgentCard(name, data))}
          </div>
        </CardBody>
      </Card>

      {/* Communication Flow */}
      <Card>
        <CardHeader>
          <CardTitle>Inter-Agent Communication Flow</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="relative">
            <div className="flex items-center justify-between">
              {['Orchestrator', 'Parser', 'Technical', 'Pricing', 'Response'].map((agent, idx) => (
                <div key={idx} className="flex flex-col items-center">
                  <div className={`p-4 rounded-lg border-2 ${
                    agentStatus[agent.toLowerCase() + '_agent']?.status === 'active'
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-dark-600 bg-dark-700'
                  }`}>
                    <Users className={`w-8 h-8 ${
                      agentStatus[agent.toLowerCase() + '_agent']?.status === 'active'
                        ? 'text-green-400'
                        : 'text-gray-400'
                    }`} />
                  </div>
                  <p className="text-sm text-gray-400 mt-2">{agent}</p>
                  {agentStatus[agent.toLowerCase() + '_agent']?.status === 'active' && (
                    <Badge variant="success" size="sm" className="mt-1">
                      Active
                    </Badge>
                  )}
                </div>
              ))}
            </div>

            {/* Connection Lines */}
            <svg className="absolute top-0 left-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
              {[1, 2, 3, 4].map((idx) => (
                <line
                  key={idx}
                  x1={`${idx * 20}%`}
                  y1="50%"
                  x2={`${(idx + 1) * 20}%`}
                  y2="50%"
                  stroke="rgba(14, 165, 233, 0.3)"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    from="0"
                    to="-10"
                    dur="1s"
                    repeatCount="indefinite"
                  />
                </line>
              ))}
            </svg>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default WorkflowOrchestratorDashboard;
