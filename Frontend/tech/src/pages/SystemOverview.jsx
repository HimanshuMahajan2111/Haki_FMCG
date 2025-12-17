/**
 * System Overview Page - Complete system documentation and architecture
 */
import React from 'react';
import { Database, Cpu, Package, Activity, Zap, Shield, Users, FileText } from 'lucide-react';

const SystemOverview = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-800 to-dark-900 p-6">
      {/* Header */}
      <div className="bg-dark-900/50 backdrop-blur-xl rounded-lg border border-dark-700/50 p-6 mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">RFP AI System Architecture</h1>
        <p className="text-gray-400">
          Multi-agent system for automated RFP processing and product matching
        </p>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <StatCard
          icon={<Database className="text-blue-400" />}
          title="OEM Products"
          value="693"
          subtitle="From 5 manufacturers"
          color="blue"
        />
        <StatCard
          icon={<Users className="text-purple-400" />}
          title="Active Agents"
          value="4"
          subtitle="Sales, Technical, Pricing, Master"
          color="purple"
        />
        <StatCard
          icon={<Activity className="text-green-400" />}
          title="Workflows"
          value="11/11"
          subtitle="Tests passing"
          color="green"
        />
        <StatCard
          icon={<Zap className="text-yellow-400" />}
          title="Performance"
          value="<100ms"
          subtitle="Database query speed"
          color="yellow"
        />
      </div>

      {/* Architecture Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Multi-Agent System */}
        <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Users size={24} className="text-primary-400" />
            Multi-Agent Architecture
          </h2>
          <div className="space-y-4">
            <AgentCard
              name="Sales Agent"
              description="RFP discovery and opportunity identification"
              responsibilities={[
                'Monitors 3 procurement websites',
                'Identifies next 3 months RFPs',
                'Forwards to Master Agent with structured data'
              ]}
            />
            <AgentCard
              name="Technical Agent"
              description="Product matching and specification analysis"
              responsibilities={[
                'Matches RFP requirements to 693 OEM products',
                'Calculates spec match percentage (equal weightage)',
                'Recommends top 3 products with comparison table'
              ]}
            />
            <AgentCard
              name="Pricing Agent"
              description="Cost calculation and pricing strategy"
              responsibilities={[
                'Material costs (meter rate × quantity)',
                'Testing costs (routine, type, acceptance)',
                'GST and final pricing with 10% contingency'
              ]}
            />
            <AgentCard
              name="Master Agent"
              description="Orchestration and coordination"
              responsibilities={[
                'Receives inputs from all agents',
                'Consolidates recommendations',
                'Generates outputs (JSON, Excel, PDF)'
              ]}
            />
          </div>
        </div>

        {/* Database Architecture */}
        <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Database size={24} className="text-blue-400" />
            Database Architecture
          </h2>
          <div className="space-y-4">
            <div className="bg-dark-700/30 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-2">OEM Products (693 items)</h3>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• Havells: 33 products</li>
                <li>• Polycab: 285 products</li>
                <li>• KEI: 45 products</li>
                <li>• Finolex: 164 products</li>
                <li>• RR Kabel: 166 products</li>
              </ul>
            </div>
            <div className="bg-dark-700/30 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-2">Product Fields (30+)</h3>
              <ul className="text-sm text-gray-400 space-y-1">
                <li>• product_id, manufacturer, model_number</li>
                <li>• Voltage rating, conductor material/size</li>
                <li>• Insulation type, temperature rating</li>
                <li>• Unit price, stock quantity, delivery days</li>
                <li>• Certifications (BIS, IEC, TUV)</li>
                <li>• Standards (IS 694, IEC 60502, etc.)</li>
              </ul>
            </div>
            <div className="bg-dark-700/30 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-2">Categories</h3>
              <div className="flex flex-wrap gap-2">
                {[
                  'Solar Cables',
                  'Power Cables - LT',
                  'Flexible Cables',
                  'Control Cables',
                  'Armoured Cables'
                ].map((cat) => (
                  <span key={cat} className="px-2 py-1 text-xs bg-blue-500/20 text-blue-300 rounded">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Endpoints */}
      <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6 mb-6">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Zap size={24} className="text-yellow-400" />
          API Endpoints
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <EndpointCard
            method="GET"
            path="/api/oem/products"
            description="Get OEM products with pagination and filtering"
            params={['page', 'page_size', 'manufacturer', 'category', 'search', 'voltage']}
          />
          <EndpointCard
            method="GET"
            path="/api/oem/products/{id}"
            description="Get specific product by ID"
          />
          <EndpointCard
            method="GET"
            path="/api/oem/search"
            description="Full-text search across products"
            params={['q', 'limit']}
          />
          <EndpointCard
            method="GET"
            path="/api/oem/manufacturers"
            description="List all manufacturers with product counts"
          />
          <EndpointCard
            method="GET"
            path="/api/oem/categories"
            description="List all categories with product counts"
          />
          <EndpointCard
            method="GET"
            path="/api/oem/statistics"
            description="Comprehensive product statistics"
          />
          <EndpointCard
            method="POST"
            path="/api/v1/rfp"
            description="Submit RFP for processing"
          />
          <EndpointCard
            method="GET"
            path="/api/v1/rfp/status/{id}"
            description="Get workflow status and results"
          />
        </div>
      </div>

      {/* Features */}
      <div className="bg-dark-800/50 backdrop-blur rounded-lg border border-dark-700/50 p-6">
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <Shield size={24} className="text-green-400" />
          Key Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            title="Automated RFP Discovery"
            features={[
              'Web scraping from 3 procurement sites',
              'Next 3 months opportunity tracking',
              'Automatic categorization'
            ]}
          />
          <FeatureCard
            title="Intelligent Product Matching"
            features={[
              'Database-backed search (693 products)',
              'Spec match % calculation',
              'Top 3 recommendations with comparison'
            ]}
          />
          <FeatureCard
            title="Comprehensive Pricing"
            features={[
              'Material cost calculations',
              'Testing cost breakdown',
              'GST and contingency inclusion'
            ]}
          />
          <FeatureCard
            title="Multi-Format Output"
            features={[
              'JSON for system integration',
              'Excel for data analysis',
              'PDF for client presentation'
            ]}
          />
          <FeatureCard
            title="Performance Optimized"
            features={[
              'Database queries < 100ms',
              'Async processing pipeline',
              'Efficient pagination'
            ]}
          />
          <FeatureCard
            title="Production Ready"
            features={[
              'All 11 tests passing',
              'Error handling & logging',
              'Scalable architecture'
            ]}
          />
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, title, value, subtitle, color }) => {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/20 border-blue-500/30',
    purple: 'from-purple-500/20 to-purple-600/20 border-purple-500/30',
    green: 'from-green-500/20 to-green-600/20 border-green-500/30',
    yellow: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} backdrop-blur rounded-lg border p-6`}>
      <div className="flex items-center gap-4 mb-3">
        <div className="w-12 h-12 rounded-lg bg-dark-800/50 flex items-center justify-center">
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
      <p className="text-xs text-gray-400">{subtitle}</p>
    </div>
  );
};

const AgentCard = ({ name, description, responsibilities }) => (
  <div className="bg-dark-700/30 rounded-lg p-4">
    <h3 className="font-semibold text-white mb-1">{name}</h3>
    <p className="text-sm text-gray-400 mb-3">{description}</p>
    <ul className="text-xs text-gray-500 space-y-1">
      {responsibilities.map((resp, i) => (
        <li key={i}>• {resp}</li>
      ))}
    </ul>
  </div>
);

const EndpointCard = ({ method, path, description, params }) => (
  <div className="bg-dark-700/30 rounded-lg p-4">
    <div className="flex items-center gap-2 mb-2">
      <span className={`px-2 py-1 text-xs font-mono rounded ${
        method === 'GET' ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'
      }`}>
        {method}
      </span>
      <code className="text-sm text-white font-mono">{path}</code>
    </div>
    <p className="text-sm text-gray-400 mb-2">{description}</p>
    {params && (
      <div className="flex flex-wrap gap-1">
        {params.map((param) => (
          <span key={param} className="px-2 py-0.5 text-xs bg-dark-600/50 text-gray-400 rounded">
            {param}
          </span>
        ))}
      </div>
    )}
  </div>
);

const FeatureCard = ({ title, features }) => (
  <div className="bg-dark-700/30 rounded-lg p-4">
    <h3 className="font-semibold text-white mb-3">{title}</h3>
    <ul className="text-sm text-gray-400 space-y-2">
      {features.map((feature, i) => (
        <li key={i} className="flex items-start gap-2">
          <span className="text-primary-400 mt-1">✓</span>
          <span>{feature}</span>
        </li>
      ))}
    </ul>
  </div>
);

export default SystemOverview;
