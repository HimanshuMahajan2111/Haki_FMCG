import React from 'react';
import { Clock, Zap, TrendingUp, Users, Brain, FileText } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge } from './UI';

const ProcessTimeComparison = () => {
  const comparisonData = {
    manual: {
      total_hours: 48,
      stages: [
        { name: 'Document Review', hours: 8, description: 'Manual reading and analysis' },
        { name: 'Product Research', hours: 12, description: 'Catalog search and matching' },
        { name: 'Pricing Calculation', hours: 6, description: 'Manual spreadsheet work' },
        { name: 'Proposal Writing', hours: 16, description: 'Document creation and formatting' },
        { name: 'Review & Approval', hours: 6, description: 'Management review cycles' }
      ],
      team_size: 4,
      cost_per_hour: 2000
    },
    ai: {
      total_hours: 0.67, // 40 minutes
      stages: [
        { name: 'RFP Parsing', hours: 0.17, description: 'AI document extraction' },
        { name: 'Product Matching', hours: 0.25, description: 'Vector similarity search' },
        { name: 'Pricing Engine', hours: 0.08, description: 'Automated calculation' },
        { name: 'Response Generation', hours: 0.17, description: 'AI content creation' }
      ],
      team_size: 1,
      cost_per_hour: 500
    }
  };

  const timeSaved = comparisonData.manual.total_hours - comparisonData.ai.total_hours;
  const timeSavedPercent = ((timeSaved / comparisonData.manual.total_hours) * 100).toFixed(1);
  const costSavings = (comparisonData.manual.total_hours * comparisonData.manual.cost_per_hour * comparisonData.manual.team_size) - 
                     (comparisonData.ai.total_hours * comparisonData.ai.cost_per_hour * comparisonData.ai.team_size);

  const formatHours = (hours) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)} min`;
    }
    return `${hours.toFixed(1)} hrs`;
  };

  const renderStageComparison = () => {
    const maxStages = Math.max(comparisonData.manual.stages.length, comparisonData.ai.stages.length);
    
    return (
      <div className="space-y-3">
        {Array.from({ length: maxStages }).map((_, idx) => {
          const manualStage = comparisonData.manual.stages[idx];
          const aiStage = comparisonData.ai.stages[idx];
          
          return (
            <div key={idx} className="grid grid-cols-2 gap-4">
              {/* Manual Process */}
              {manualStage && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-white text-sm">{manualStage.name}</h4>
                      <p className="text-xs text-gray-400 mt-1">{manualStage.description}</p>
                    </div>
                    <Badge variant="danger" size="sm">
                      {formatHours(manualStage.hours)}
                    </Badge>
                  </div>
                  <div className="mt-2 h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-500"
                      style={{ width: `${(manualStage.hours / comparisonData.manual.total_hours) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {/* AI Process */}
              {aiStage && (
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-white text-sm">{aiStage.name}</h4>
                      <p className="text-xs text-gray-400 mt-1">{aiStage.description}</p>
                    </div>
                    <Badge variant="success" size="sm">
                      {formatHours(aiStage.hours)}
                    </Badge>
                  </div>
                  <div className="mt-2 h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500"
                      style={{ width: `${(aiStage.hours / comparisonData.ai.total_hours) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header Comparison */}
      <div className="grid grid-cols-2 gap-6">
        {/* Manual Process */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <Clock className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <CardTitle>Manual Process</CardTitle>
                <p className="text-sm text-gray-400">Traditional workflow</p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <div className="text-center p-6 bg-red-500/10 border-2 border-red-500 rounded-lg">
                <p className="text-5xl font-bold text-red-400 mb-2">
                  {comparisonData.manual.total_hours}
                </p>
                <p className="text-sm text-gray-400">Hours per RFP</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-dark-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Users className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-400">Team Size</span>
                  </div>
                  <p className="text-xl font-bold text-white">{comparisonData.manual.team_size}</p>
                </div>

                <div className="p-3 bg-dark-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-400">Stages</span>
                  </div>
                  <p className="text-xl font-bold text-white">{comparisonData.manual.stages.length}</p>
                </div>
              </div>

              <div className="p-3 bg-dark-700 rounded-lg">
                <p className="text-xs text-gray-400 mb-1">Estimated Cost</p>
                <p className="text-2xl font-bold text-white">
                  ₹{(comparisonData.manual.total_hours * comparisonData.manual.cost_per_hour * comparisonData.manual.team_size).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* AI Process */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <Zap className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <CardTitle>AI-Powered Process</CardTitle>
                <p className="text-sm text-gray-400">Automated workflow</p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <div className="text-center p-6 bg-green-500/10 border-2 border-green-500 rounded-lg">
                <p className="text-5xl font-bold text-green-400 mb-2">
                  {formatHours(comparisonData.ai.total_hours)}
                </p>
                <p className="text-sm text-gray-400">Time per RFP</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-dark-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Brain className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-400">AI Agents</span>
                  </div>
                  <p className="text-xl font-bold text-white">6</p>
                </div>

                <div className="p-3 bg-dark-700 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Zap className="w-4 h-4 text-gray-400" />
                    <span className="text-xs text-gray-400">Stages</span>
                  </div>
                  <p className="text-xl font-bold text-white">{comparisonData.ai.stages.length}</p>
                </div>
              </div>

              <div className="p-3 bg-dark-700 rounded-lg">
                <p className="text-xs text-gray-400 mb-1">Estimated Cost</p>
                <p className="text-2xl font-bold text-white">
                  ₹{(comparisonData.ai.total_hours * comparisonData.ai.cost_per_hour * comparisonData.ai.team_size).toLocaleString('en-IN')}
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Savings Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Efficiency Gains</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center p-6 bg-primary-500/10 border-2 border-primary-500 rounded-lg">
              <TrendingUp className="w-8 h-8 text-primary-400 mx-auto mb-3" />
              <p className="text-4xl font-bold text-primary-400 mb-2">
                {timeSavedPercent}%
              </p>
              <p className="text-sm text-gray-400">Faster Processing</p>
              <p className="text-xs text-gray-500 mt-2">
                {formatHours(timeSaved)} saved per RFP
              </p>
            </div>

            <div className="text-center p-6 bg-green-500/10 border-2 border-green-500 rounded-lg">
              <span className="text-4xl font-bold text-green-400 mb-2 block">
                ₹{(costSavings / 1000).toFixed(0)}K
              </span>
              <p className="text-sm text-gray-400">Cost Savings</p>
              <p className="text-xs text-gray-500 mt-2">
                Per RFP processed
              </p>
            </div>

            <div className="text-center p-6 bg-yellow-500/10 border-2 border-yellow-500 rounded-lg">
              <span className="text-4xl font-bold text-yellow-400 mb-2 block">
                {Math.floor(comparisonData.manual.total_hours / comparisonData.ai.total_hours)}x
              </span>
              <p className="text-sm text-gray-400">Speed Multiplier</p>
              <p className="text-xs text-gray-500 mt-2">
                Capacity increase
              </p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Stage-by-Stage Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Stage-by-Stage Breakdown</CardTitle>
        </CardHeader>
        <CardBody>
          {renderStageComparison()}
        </CardBody>
      </Card>

      {/* Monthly Impact */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Impact (20 RFPs)</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Manual Process</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Total Hours</span>
                  <span className="text-xl font-bold text-red-400">
                    {comparisonData.manual.total_hours * 20} hrs
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Team Cost</span>
                  <span className="text-xl font-bold text-red-400">
                    ₹{((comparisonData.manual.total_hours * 20 * comparisonData.manual.cost_per_hour * comparisonData.manual.team_size) / 100000).toFixed(1)}L
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Team Utilization</span>
                  <span className="text-xl font-bold text-red-400">
                    {((comparisonData.manual.total_hours * 20) / (160 * comparisonData.manual.team_size) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-4">AI-Powered Process</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Total Time</span>
                  <span className="text-xl font-bold text-green-400">
                    {formatHours(comparisonData.ai.total_hours * 20)}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Total Cost</span>
                  <span className="text-xl font-bold text-green-400">
                    ₹{((comparisonData.ai.total_hours * 20 * comparisonData.ai.cost_per_hour * comparisonData.ai.team_size) / 1000).toFixed(1)}K
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <span className="text-gray-400">Team Utilization</span>
                  <span className="text-xl font-bold text-green-400">
                    {((comparisonData.ai.total_hours * 20) / 160 * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gradient-to-r from-primary-500/20 to-secondary-500/20 border-2 border-primary-500 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg font-semibold text-white">Monthly Savings with AI</p>
                <p className="text-sm text-gray-400">Process 20 RFPs with 98.6% less time</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-primary-400">
                  ₹{((costSavings * 20) / 100000).toFixed(1)}L
                </p>
                <p className="text-xs text-gray-400">{formatHours(timeSaved * 20)} saved</p>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default ProcessTimeComparison;
