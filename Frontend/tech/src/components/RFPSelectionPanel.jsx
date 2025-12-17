import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Calendar, DollarSign, TrendingUp, Clock, Filter } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge, Button } from './UI';
import api from '../services/api';

const RFPSelectionPanel = ({ onSelectionChange, allowMultiple = false }) => {
  const [rfps, setRfps] = useState([]);
  const [selectedRfps, setSelectedRfps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('priority'); // priority, deadline, value
  const [filterCategory, setFilterCategory] = useState('all');

  useEffect(() => {
    fetchDiscoveredRfps();
  }, []);

  const fetchDiscoveredRfps = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/rfp/latest?limit=50');
      const rfpData = response.data.data?.rfps || [];
      
      // Calculate priority scores
      const enrichedRfps = rfpData.map(rfp => ({
        ...rfp,
        priority_score: calculatePriorityScore(rfp),
        days_remaining: calculateDaysRemaining(rfp.due_date)
      }));
      
      setRfps(enrichedRfps);
    } catch (error) {
      console.error('Error fetching RFPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculatePriorityScore = (rfp) => {
    let score = 0;
    
    // Value score (0-40 points)
    const value = parseFloat(rfp.estimated_value || 0);
    if (value > 10000000) score += 40;
    else if (value > 5000000) score += 30;
    else if (value > 1000000) score += 20;
    else score += 10;
    
    // Urgency score (0-30 points)
    const daysRemaining = calculateDaysRemaining(rfp.due_date);
    if (daysRemaining <= 3) score += 30;
    else if (daysRemaining <= 7) score += 25;
    else if (daysRemaining <= 14) score += 15;
    else score += 5;
    
    // Category match score (0-20 points)
    const relevantCategories = ['electrical', 'cables', 'wires', 'fmcg'];
    if (relevantCategories.some(cat => rfp.title?.toLowerCase().includes(cat))) {
      score += 20;
    }
    
    // Confidence score (0-10 points)
    score += (rfp.confidence_score || 0) * 10;
    
    return Math.min(100, score);
  };

  const calculateDaysRemaining = (dueDate) => {
    if (!dueDate) return 999;
    const today = new Date();
    const deadline = new Date(dueDate);
    const diffTime = deadline - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const handleSelectRfp = (rfp) => {
    if (allowMultiple) {
      const isSelected = selectedRfps.some(r => r.id === rfp.id);
      const newSelection = isSelected
        ? selectedRfps.filter(r => r.id !== rfp.id)
        : [...selectedRfps, rfp];
      setSelectedRfps(newSelection);
      onSelectionChange?.(newSelection);
    } else {
      setSelectedRfps([rfp]);
      onSelectionChange?.([rfp]);
    }
  };

  const getSortedRfps = () => {
    let sorted = [...rfps];
    
    // Apply category filter
    if (filterCategory !== 'all') {
      sorted = sorted.filter(rfp => 
        rfp.title?.toLowerCase().includes(filterCategory.toLowerCase())
      );
    }
    
    // Apply sorting
    switch (sortBy) {
      case 'priority':
        sorted.sort((a, b) => b.priority_score - a.priority_score);
        break;
      case 'deadline':
        sorted.sort((a, b) => a.days_remaining - b.days_remaining);
        break;
      case 'value':
        sorted.sort((a, b) => (b.estimated_value || 0) - (a.estimated_value || 0));
        break;
      default:
        break;
    }
    
    return sorted;
  };

  const getPriorityBadge = (score) => {
    if (score >= 80) return { variant: 'danger', label: 'Critical' };
    if (score >= 60) return { variant: 'warning', label: 'High' };
    if (score >= 40) return { variant: 'primary', label: 'Medium' };
    return { variant: 'default', label: 'Low' };
  };

  const formatValue = (value) => {
    if (!value) return 'N/A';
    const num = parseFloat(value);
    if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
    if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`;
    return `₹${num.toLocaleString('en-IN')}`;
  };

  const sortedRfps = getSortedRfps();

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>RFP Selection & Prioritization</CardTitle>
            <p className="text-sm text-gray-400 mt-1">
              {selectedRfps.length} of {rfps.length} RFPs selected
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Categories</option>
              <option value="electrical">Electrical</option>
              <option value="cables">Cables</option>
              <option value="wires">Wires</option>
              <option value="fmcg">FMCG</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="priority">Sort by Priority</option>
              <option value="deadline">Sort by Deadline</option>
              <option value="value">Sort by Value</option>
            </select>
            <Button variant="outline" size="sm" onClick={fetchDiscoveredRfps}>
              <Filter className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            <p className="mt-4 text-gray-400">Loading RFPs...</p>
          </div>
        ) : sortedRfps.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400">No RFPs discovered yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedRfps.map(rfp => {
              const isSelected = selectedRfps.some(r => r.id === rfp.id);
              const priorityBadge = getPriorityBadge(rfp.priority_score);
              
              return (
                <div
                  key={rfp.id}
                  onClick={() => handleSelectRfp(rfp)}
                  className={`
                    p-4 rounded-lg border-2 transition-all cursor-pointer
                    ${isSelected 
                      ? 'border-primary-500 bg-primary-500/10' 
                      : 'border-dark-600 bg-dark-700/50 hover:border-dark-500'
                    }
                  `}
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-1">
                      {isSelected ? (
                        <CheckCircle2 className="w-6 h-6 text-primary-500" />
                      ) : (
                        <Circle className="w-6 h-6 text-gray-500" />
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-white mb-1">{rfp.title}</h4>
                          <p className="text-sm text-gray-400">
                            {rfp.source} • Created {new Date(rfp.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant={priorityBadge.variant}>
                            {priorityBadge.label}
                          </Badge>
                          <Badge variant="default">
                            Score: {rfp.priority_score}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4 mt-3">
                        <div className="flex items-center gap-2 text-sm">
                          <DollarSign className="w-4 h-4 text-green-400" />
                          <div>
                            <p className="text-gray-400">Est. Value</p>
                            <p className="font-semibold text-white">{formatValue(rfp.estimated_value)}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <Clock className="w-4 h-4 text-yellow-400" />
                          <div>
                            <p className="text-gray-400">Days Left</p>
                            <p className={`font-semibold ${
                              rfp.days_remaining <= 3 ? 'text-red-400' :
                              rfp.days_remaining <= 7 ? 'text-yellow-400' :
                              'text-green-400'
                            }`}>
                              {rfp.days_remaining > 0 ? rfp.days_remaining : 'Expired'}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm">
                          <TrendingUp className="w-4 h-4 text-primary-400" />
                          <div>
                            <p className="text-gray-400">Confidence</p>
                            <p className="font-semibold text-white">
                              {((rfp.confidence_score || 0) * 100).toFixed(0)}%
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        
        {selectedRfps.length > 0 && (
          <div className="mt-6 p-4 bg-primary-500/10 border border-primary-500 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-white">
                  {selectedRfps.length} RFP{selectedRfps.length > 1 ? 's' : ''} Selected
                </p>
                <p className="text-sm text-gray-400">
                  Total Value: {formatValue(
                    selectedRfps.reduce((sum, rfp) => sum + (parseFloat(rfp.estimated_value) || 0), 0)
                  )}
                </p>
              </div>
              <Button variant="primary" size="md">
                Process Selected RFPs →
              </Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default RFPSelectionPanel;
