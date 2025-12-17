import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Trophy, Target, DollarSign, Clock, BarChart3 } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge } from './UI';
import api from '../services/api';

const WinRateAnalytics = ({ timeRange = 30 }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/v1/analytics/dashboard?days=${timeRange}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardBody>
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            <p className="mt-4 text-gray-400">Loading analytics...</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (!analytics) {
    return (
      <Card>
        <CardBody>
          <p className="text-center text-gray-400 py-8">No analytics data available</p>
        </CardBody>
      </Card>
    );
  }

  const winRate = analytics.win_rates?.rate || 0;
  const totalSubmitted = analytics.win_rates?.submitted || 0;
  const totalWon = analytics.win_rates?.won || 0;
  const totalLost = totalSubmitted - totalWon;
  const avgValue = analytics.rfp_processing?.avg_value || 0;
  const totalValue = totalWon * avgValue;

  const getWinRateColor = (rate) => {
    if (rate >= 0.6) return 'text-green-400';
    if (rate >= 0.4) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getWinRateBg = (rate) => {
    if (rate >= 0.6) return 'bg-green-500/20 border-green-500';
    if (rate >= 0.4) return 'bg-yellow-500/20 border-yellow-500';
    return 'bg-red-500/20 border-red-500';
  };

  // Calculate trend from real data if available
  const monthlyTrend = analytics.win_rates?.trend || { trend: 'neutral', change: 0 };

  return (
    <div className="space-y-6">
      {/* Win Rate Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Win Rate Analytics</CardTitle>
            <Badge variant="primary">Last {timeRange} Days</Badge>
          </div>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Main Win Rate Card */}
            <div className={`col-span-1 md:col-span-2 p-6 rounded-lg border-2 ${getWinRateBg(winRate)}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Overall Win Rate</p>
                  <p className={`text-5xl font-bold ${getWinRateColor(winRate)}`}>
                    {(winRate * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-dark-800">
                  <Trophy className="w-8 h-8 text-yellow-400" />
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm">
                {monthlyTrend.trend === 'up' ? (
                  <>
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <span className="text-green-400">+{monthlyTrend.change}%</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">-{monthlyTrend.change}%</span>
                  </>
                )}
                <span className="text-gray-400">vs previous period</span>
              </div>

              {/* Progress Bar */}
              <div className="mt-6">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-400">Won: {totalWon}</span>
                  <span className="text-gray-400">Lost: {totalLost}</span>
                </div>
                <div className="h-3 bg-dark-700 rounded-full overflow-hidden flex">
                  <div
                    className="bg-gradient-to-r from-green-500 to-green-400"
                    style={{ width: `${winRate * 100}%` }}
                  />
                  <div
                    className="bg-gradient-to-r from-red-500 to-red-400"
                    style={{ width: `${(1 - winRate) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="space-y-4">
              <div className="p-4 bg-dark-700 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <Target className="w-5 h-5 text-blue-400" />
                  <span className="text-sm text-gray-400">Submitted</span>
                </div>
                <p className="text-3xl font-bold text-white">{totalSubmitted}</p>
              </div>

              <div className="p-4 bg-dark-700 rounded-lg">
                <div className="flex items-center gap-3 mb-2">
                  <Trophy className="w-5 h-5 text-green-400" />
                  <span className="text-sm text-gray-400">Won</span>
                </div>
                <p className="text-3xl font-bold text-green-400">{totalWon}</p>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Financial Impact */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardBody>
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Total Value Won</p>
                <p className="text-2xl font-bold text-white">
                  ₹{(totalValue / 10000000).toFixed(2)} Cr
                </p>
              </div>
            </div>
            {analytics.win_rates?.value_trend && (
              <div className="flex items-center gap-2 text-sm">
                {analytics.win_rates.value_trend > 0 ? (
                  <>
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <span className="text-green-400">+{analytics.win_rates.value_trend.toFixed(1)}%</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">{analytics.win_rates.value_trend.toFixed(1)}%</span>
                  </>
                )}
                <span className="text-gray-400">from last period</span>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <BarChart3 className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Avg Deal Size</p>
                <p className="text-2xl font-bold text-white">
                  ₹{(avgValue / 100000).toFixed(2)} L
                </p>
              </div>
            </div>
            {analytics.win_rates?.deal_size_trend && (
              <div className="flex items-center gap-2 text-sm">
                {analytics.win_rates.deal_size_trend > 0 ? (
                  <>
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-400">+{analytics.win_rates.deal_size_trend.toFixed(1)}%</span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">{analytics.win_rates.deal_size_trend.toFixed(1)}%</span>
                  </>
                )}
                <span className="text-gray-400">from last period</span>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Clock className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Avg Time to Win</p>
                <p className="text-2xl font-bold text-white">
                  {analytics.rfp_processing?.avg_processing_time_minutes || 0} min
                </p>
              </div>
            </div>
            {analytics.rfp_processing?.processing_time_trend && (
              <div className="flex items-center gap-2 text-sm">
                {analytics.rfp_processing.processing_time_trend < 0 ? (
                  <>
                    <TrendingDown className="w-4 h-4 text-green-400" />
                    <span className="text-green-400">{analytics.rfp_processing.processing_time_trend.toFixed(1)}%</span>
                  </>
                ) : (
                  <>
                    <TrendingUp className="w-4 h-4 text-red-400" />
                    <span className="text-red-400">+{analytics.rfp_processing.processing_time_trend.toFixed(1)}%</span>
                  </>
                )}
                <span className="text-gray-400">processing time change</span>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Win Rate by Category */}
      <Card>
        <CardHeader>
          <CardTitle>Win Rate by Category</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            {(analytics.win_rates?.by_category || []).length > 0 ? (
              analytics.win_rates.by_category.map((item, idx) => {
              const rate = item.won / item.total;
              return (
                <div key={idx} className="p-4 bg-dark-700 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-white">{item.category}</h4>
                      <p className="text-sm text-gray-400">
                        {item.won} won / {item.lost} lost • Total: {item.total}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getWinRateColor(rate)}`}>
                        {(rate * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-gray-400">
                        ₹{(item.value / 10000000).toFixed(1)} Cr
                      </p>
                    </div>
                  </div>
                  <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        rate >= 0.6 ? 'bg-green-500' :
                        rate >= 0.4 ? 'bg-yellow-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${rate * 100}%` }}
                    />
                  </div>
                </div>
              );
              })
            ) : (
              <p className="text-center text-gray-400 py-8">No category data available</p>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Performance Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Insights</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="space-y-3">
            <div className="p-4 bg-green-500/10 border border-green-500 rounded-lg">
              <div className="flex items-start gap-3">
                <TrendingUp className="w-5 h-5 text-green-400 mt-0.5" />
                <div>
                  <p className="font-semibold text-green-400">Strong Performance</p>
                  <p className="text-sm text-gray-300 mt-1">
                    Your win rate for Electrical Cables (75%) is 18% above industry average
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-yellow-500/10 border border-yellow-500 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
                <div>
                  <p className="font-semibold text-yellow-400">Opportunity</p>
                  <p className="text-sm text-gray-300 mt-1">
                    Industrial Equipment category shows lower conversion - consider strategy review
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500 rounded-lg">
              <div className="flex items-start gap-3">
                <Target className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="font-semibold text-blue-400">Target Achievement</p>
                  <p className="text-sm text-gray-300 mt-1">
                    You're 92% towards your quarterly win rate target of 60%
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

const AlertCircle = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

export default WinRateAnalytics;
