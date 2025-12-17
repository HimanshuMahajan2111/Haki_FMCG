import React, { useState } from 'react';
import { FlaskConical, CheckCircle2, DollarSign, Calendar, Building2, FileText } from 'lucide-react';
import { Card, CardHeader, CardBody, CardTitle, Badge } from './UI';

const TestRequirementsSection = ({ testData, onTestSelectionChange }) => {
  const [selectedTests, setSelectedTests] = useState([]);

  const testCategories = {
    routine: {
      name: 'Routine Tests',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      icon: FlaskConical
    },
    type: {
      name: 'Type Tests',
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20',
      icon: CheckCircle2
    },
    special: {
      name: 'Special Tests',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      icon: Building2
    }
  };

  const handleTestToggle = (test) => {
    const isSelected = selectedTests.some(t => t.id === test.id);
    const newSelection = isSelected
      ? selectedTests.filter(t => t.id !== test.id)
      : [...selectedTests, test];
    
    setSelectedTests(newSelection);
    onTestSelectionChange?.(newSelection);
  };

  const calculateTotalCost = () => {
    return selectedTests.reduce((sum, test) => sum + (test.cost || 0), 0);
  };

  const calculateTotalDuration = () => {
    return selectedTests.reduce((sum, test) => sum + (test.duration_days || 0), 0);
  };

  const renderTestCard = (test, category) => {
    const isSelected = selectedTests.some(t => t.id === test.id);
    const categoryInfo = testCategories[category];
    const Icon = categoryInfo.icon;

    return (
      <div
        key={test.id}
        onClick={() => handleTestToggle(test)}
        className={`
          p-4 rounded-lg border-2 cursor-pointer transition-all
          ${isSelected 
            ? 'border-primary-500 bg-primary-500/10' 
            : 'border-dark-600 bg-dark-700/50 hover:border-dark-500'
          }
        `}
      >
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${categoryInfo.bgColor}`}>
            <Icon className={`w-5 h-5 ${categoryInfo.color}`} />
          </div>
          
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-white">{test.name}</h4>
                <p className="text-sm text-gray-400 mt-1">{test.description}</p>
              </div>
              <Badge variant={isSelected ? 'success' : 'default'}>
                {isSelected ? 'Selected' : 'Select'}
              </Badge>
            </div>

            <div className="grid grid-cols-4 gap-3 mt-3">
              <div>
                <p className="text-xs text-gray-400">Cost</p>
                <p className="text-sm font-semibold text-white">
                  ₹{test.cost?.toLocaleString('en-IN') || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Duration</p>
                <p className="text-sm font-semibold text-white">
                  {test.duration_days || 'N/A'} days
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Standard</p>
                <p className="text-sm font-semibold text-white">
                  {test.standard || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Mandatory</p>
                <p className="text-sm font-semibold text-white">
                  {test.is_mandatory ? (
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                  ) : (
                    <span className="text-gray-500">Optional</span>
                  )}
                </p>
              </div>
            </div>

            {test.laboratories && test.laboratories.length > 0 && (
              <div className="mt-3 pt-3 border-t border-dark-600">
                <p className="text-xs text-gray-400 mb-2">Approved Laboratories:</p>
                <div className="flex flex-wrap gap-2">
                  {test.laboratories.slice(0, 3).map((lab, idx) => (
                    <Badge key={idx} variant="default" size="sm">
                      {lab.name}
                    </Badge>
                  ))}
                  {test.laboratories.length > 3 && (
                    <Badge variant="default" size="sm">
                      +{test.laboratories.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (!testData || Object.keys(testData).length === 0) {
    return (
      <Card>
        <CardBody>
          <div className="text-center py-12">
            <FlaskConical className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No test requirements available</p>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Test Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Test Requirements Summary</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <FlaskConical className="w-8 h-8 text-primary-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">
                {Object.values(testData).flat().length}
              </p>
              <p className="text-sm text-gray-400">Total Tests</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">
                {selectedTests.length}
              </p>
              <p className="text-sm text-gray-400">Selected</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <DollarSign className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">
                ₹{calculateTotalCost().toLocaleString('en-IN')}
              </p>
              <p className="text-sm text-gray-400">Total Cost</p>
            </div>
            <div className="text-center p-4 bg-dark-700 rounded-lg">
              <Calendar className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">
                {calculateTotalDuration()}
              </p>
              <p className="text-sm text-gray-400">Total Days</p>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Routine Tests */}
      {testData.routine && testData.routine.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <FlaskConical className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <CardTitle>Routine Tests</CardTitle>
                <p className="text-sm text-gray-400">
                  Basic quality assurance tests performed on every production batch
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {testData.routine.map(test => renderTestCard(test, 'routine'))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Type Tests */}
      {testData.type && testData.type.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <CheckCircle2 className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <CardTitle>Type Tests</CardTitle>
                <p className="text-sm text-gray-400">
                  Comprehensive tests conducted on product prototypes for certification
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {testData.type.map(test => renderTestCard(test, 'type'))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Special Tests */}
      {testData.special && testData.special.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/20">
                <Building2 className="w-5 h-5 text-yellow-400" />
              </div>
              <div>
                <CardTitle>Special Tests</CardTitle>
                <p className="text-sm text-gray-400">
                  Additional tests for specific requirements or certifications
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {testData.special.map(test => renderTestCard(test, 'special'))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Selected Tests Summary */}
      {selectedTests.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Selected Tests - Cost Breakdown</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-2 mb-4">
              {selectedTests.map((test, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-dark-700">
                  <span className="text-sm text-gray-300">{test.name}</span>
                  <span className="text-sm font-semibold text-white">
                    ₹{test.cost?.toLocaleString('en-IN')}
                  </span>
                </div>
              ))}
            </div>
            <div className="pt-3 border-t-2 border-primary-500 flex items-center justify-between">
              <div>
                <p className="text-lg font-bold text-white">Total Testing Cost</p>
                <p className="text-sm text-gray-400">
                  Duration: {calculateTotalDuration()} days
                </p>
              </div>
              <p className="text-2xl font-bold text-primary-400">
                ₹{calculateTotalCost().toLocaleString('en-IN')}
              </p>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default TestRequirementsSection;
