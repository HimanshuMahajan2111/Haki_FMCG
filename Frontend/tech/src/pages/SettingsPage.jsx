import React, { useState, useEffect } from 'react';
import { Settings, Building2, Globe, Package, Users, Save, Bell, Zap, X, Plus, Trash2 } from 'lucide-react';

const SettingsPage = () => {
  const CREDENTIALS_FLAG = 'credentials_verified';
  const [activeTab, setActiveTab] = useState('company');
  const [saving, setSaving] = useState(false);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [showProductModal, setShowProductModal] = useState(false);
  const [newSource, setNewSource] = useState({ name: '', url: '', priority: 'medium' });
  const [newProduct, setNewProduct] = useState({
    product_code: '',
    name: '',
    brand: '',
    category: '',
    price: '',
    specifications: ''
  });

  const [companyProfile, setCompanyProfile] = useState({
    company_name: 'Haki FMCG',
    business_segments: ['Electrical', 'Wires & Cables', 'Lighting'],
    target_categories: ['Government Tenders', 'Corporate RFPs', 'Industrial Projects'],
    min_rfp_value: 100000,
    preferred_margin: 18,
    response_time_target: 60,
    auto_analyze: true
  });

  const [leadSources, setLeadSources] = useState([
    { id: 1, name: 'GeM Portal', url: 'https://gem.gov.in', enabled: true, priority: 'high' },
    { id: 2, name: 'CPPP Portal', url: 'https://eprocure.gov.in', enabled: true, priority: 'high' },
    { id: 3, name: 'Railways', url: 'https://www.ireps.gov.in', enabled: true, priority: 'medium' },
    { id: 4, name: 'NTPC', url: 'https://www.ntpctender.com', enabled: true, priority: 'high' }
  ]);

  const [notifications, setNotifications] = useState({
    email_alerts: true,
    high_value_rfps: true,
    urgent_deadlines: true,
    daily_summary: true,
    win_probability_threshold: 70
  });

  const [products, setProducts] = useState([
    { id: 1, product_code: 'HAV-SW-001', name: 'Havells 32A DP MCB', brand: 'Havells', category: 'Switchgear', price: 245 },
    { id: 2, product_code: 'POL-SW-002', name: 'Polycab 40A MCB', brand: 'Polycab', category: 'Switchgear', price: 280 },
    { id: 3, product_code: 'KEI-CB-001', name: 'KEI 2.5 SQMM Wire', brand: 'KEI', category: 'Cables', price: 1250 }
  ]);

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      // Save to localStorage
      localStorage.setItem('rfp_settings', JSON.stringify({
        companyProfile,
        leadSources,
        notifications,
        products
      }));
      
      setTimeout(() => {
        setSaving(false);
        alert('Settings saved successfully!');
      }, 1000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaving(false);
    }
  };

  const handleAddSource = () => {
    if (!newSource.name || !newSource.url) {
      alert('Please fill in all fields');
      return;
    }
    const source = {
      id: leadSources.length + 1,
      name: newSource.name,
      url: newSource.url,
      enabled: true,
      priority: newSource.priority
    };
    setLeadSources([...leadSources, source]);
    setNewSource({ name: '', url: '', priority: 'medium' });
    setShowSourceModal(false);
  };

  const handleRemoveSource = (id) => {
    setLeadSources(leadSources.filter(s => s.id !== id));
  };

  const handleAddProduct = () => {
    if (!newProduct.product_code || !newProduct.name || !newProduct.brand) {
      alert('Please fill in required fields');
      return;
    }
    const product = {
      id: products.length + 1,
      product_code: newProduct.product_code,
      name: newProduct.name,
      brand: newProduct.brand,
      category: newProduct.category,
      price: parseFloat(newProduct.price) || 0,
      specifications: newProduct.specifications
    };
    setProducts([...products, product]);
    setNewProduct({ product_code: '', name: '', brand: '', category: '', price: '', specifications: '' });
    setShowProductModal(false);
  };

  const handleRemoveProduct = (id) => {
    setProducts(products.filter(p => p.id !== id));
  };

  // Load settings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('rfp_settings');
    if (saved) {
      const settings = JSON.parse(saved);
      if (settings.companyProfile) setCompanyProfile(settings.companyProfile);
      if (settings.leadSources) setLeadSources(settings.leadSources);
      if (settings.notifications) setNotifications(settings.notifications);
      if (settings.products) setProducts(settings.products);
    }

    const onCredentialsPage = window.location.pathname.includes('/credentials');
    const hasVerified = sessionStorage.getItem(CREDENTIALS_FLAG) === 'true';
    if (!hasVerified && !onCredentialsPage) {
      window.location.replace('http://localhost:3002/credentials');
    }
  }, []);

  useEffect(() => {
    const user = localStorage.getItem('user');
    if (!user) {
      window.location.replace('http://localhost:3002/login');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg">
            <Settings className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Settings & Configuration</h1>
            <p className="text-gray-600">Manage your RFP AI system preferences</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 bg-white p-2 rounded-xl shadow-md border border-gray-200 overflow-x-auto">
          <button
            onClick={() => setActiveTab('company')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === 'company'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Building2 className="w-5 h-5" />
            Company
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === 'sources'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Globe className="w-5 h-5" />
            Lead Sources
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === 'notifications'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Bell className="w-5 h-5" />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === 'system'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Zap className="w-5 h-5" />
            System Info
          </button>
          <button
            onClick={() => setActiveTab('import')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
              activeTab === 'import'
                ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Package className="w-5 h-5" />
            Data Import
          </button>
        </div>
      </div>

      {/* Company Profile Tab */}
      {activeTab === 'company' && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-purple-600" />
            Company Profile
          </h2>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Company Name</label>
              <input
                type="text"
                value={companyProfile.company_name}
                onChange={(e) => setCompanyProfile({ ...companyProfile, company_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Business Segments</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {companyProfile.business_segments.map((segment, idx) => (
                  <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                    {segment}
                  </span>
                ))}
              </div>
              <input
                type="text"
                placeholder="Add new segment (press Enter)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && e.target.value) {
                    setCompanyProfile({
                      ...companyProfile,
                      business_segments: [...companyProfile.business_segments, e.target.value]
                    });
                    e.target.value = '';
                  }
                }}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Minimum RFP Value (₹)</label>
                <input
                  type="number"
                  value={companyProfile.min_rfp_value}
                  onChange={(e) => setCompanyProfile({ ...companyProfile, min_rfp_value: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Preferred Margin (%)</label>
                <input
                  type="number"
                  value={companyProfile.preferred_margin}
                  onChange={(e) => setCompanyProfile({ ...companyProfile, preferred_margin: parseInt(e.target.value) })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Response Time Target (seconds)</label>
              <input
                type="number"
                value={companyProfile.response_time_target}
                onChange={(e) => setCompanyProfile({ ...companyProfile, response_time_target: parseInt(e.target.value) })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <input
                type="checkbox"
                checked={companyProfile.auto_analyze}
                onChange={(e) => setCompanyProfile({ ...companyProfile, auto_analyze: e.target.checked })}
                className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
              />
              <div>
                <p className="font-medium text-gray-900">Auto-analyze New RFPs</p>
                <p className="text-sm text-gray-600">Automatically start AI analysis when new RFPs are discovered</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Lead Sources Tab */}
      {activeTab === 'sources' && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Globe className="w-6 h-6 text-purple-600" />
            Lead Sources Management
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {leadSources.map((source) => (
              <div key={source.id} className="p-4 border-2 border-gray-200 rounded-xl hover:border-purple-300 transition-all bg-white shadow-sm">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={source.enabled}
                      onChange={(e) => {
                        setLeadSources(leadSources.map(s => 
                          s.id === source.id ? { ...s, enabled: e.target.checked } : s
                        ));
                      }}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                    />
                    <div>
                      <p className="font-bold text-gray-900">{source.name}</p>
                      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">{source.url}</a>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveSource(source.id)}
                    className="p-1 hover:bg-red-100 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4 text-red-600" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <select
                    value={source.priority}
                    onChange={(e) => {
                      setLeadSources(leadSources.map(s => 
                        s.id === source.id ? { ...s, priority: e.target.value } : s
                      ));
                    }}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="high">High Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="low">Low Priority</option>
                  </select>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    source.priority === 'high' ? 'bg-red-100 text-red-800' :
                    source.priority === 'medium' ? 'bg-amber-100 text-amber-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {source.priority.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <button 
            onClick={() => setShowSourceModal(true)}
            className="mt-6 flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all"
          >
            <Plus className="w-5 h-5" />
            Add New Source
          </button>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Bell className="w-6 h-6 text-purple-600" />
            Notification Preferences
          </h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">Email Alerts</p>
                <p className="text-sm text-gray-600">Receive email notifications for new RFPs</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications.email_alerts}
                  onChange={(e) => setNotifications({ ...notifications, email_alerts: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">High-Value RFPs</p>
                <p className="text-sm text-gray-600">Priority alerts for RFPs above threshold</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications.high_value_rfps}
                  onChange={(e) => setNotifications({ ...notifications, high_value_rfps: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">Urgent Deadlines</p>
                <p className="text-sm text-gray-600">Alerts for RFPs with approaching deadlines</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications.urgent_deadlines}
                  onChange={(e) => setNotifications({ ...notifications, urgent_deadlines: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-semibold text-gray-900">Daily Summary</p>
                <p className="text-sm text-gray-600">Daily digest of RFP activity and AI performance</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={notifications.daily_summary}
                  onChange={(e) => setNotifications({ ...notifications, daily_summary: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Win Probability Alert Threshold (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={notifications.win_probability_threshold}
                onChange={(e) => setNotifications({ ...notifications, win_probability_threshold: parseInt(e.target.value) })}
                className="w-full px-4 py-3 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-sm text-gray-600 mt-2">Get notified when win probability exceeds this threshold</p>
            </div>
          </div>
        </div>
      )}

      {/* System Info Tab */}
      {activeTab === 'system' && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Zap className="w-6 h-6 text-purple-600" />
            System Information
          </h2>

          <div className="space-y-6">
            {/* top stats cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-600 mb-1">Database Status</p>
                <p className="text-2xl font-bold text-gray-900">✅ Connected</p>
                <p className="text-sm text-gray-600 mt-2">693 OEM Products Loaded</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
                <p className="text-sm text-gray-600 mb-1">Backend API</p>
                <p className="text-2xl font-bold text-gray-900">✅ Running</p>
                <p className="text-sm text-gray-600 mt-2">Port 8000</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
                <p className="text-sm text-gray-600 mb-1">Procurement Portals</p>
                <p className="text-2xl font-bold text-gray-900">4 Active</p>
                <p className="text-sm text-gray-600 mt-2">11 RFPs Available</p>
              </div>
              <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
                <p className="text-sm text-gray-600 mb-1">Total RFP Value</p>
                <p className="text-2xl font-bold text-gray-900">₹31.6 Cr</p>
                <p className="text-sm text-gray-600 mt-2">Across All Portals</p>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">System Components</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">Vector Embeddings</span>
                  <span className="text-green-600 font-semibold">✓ Active</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">Multi-Agent Workflow</span>
                  <span className="text-green-600 font-semibold">✓ Active</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">Website Scanner</span>
                  <span className="text-green-600 font-semibold">✓ Active</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-gray-700">Pricing Engine</span>
                  <span className="text-green-600 font-semibold">✓ Active</span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Database</p>
                  <p className="font-bold text-gray-900">SQLite</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Python</p>
                  <p className="font-bold text-gray-900">3.11+</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">API Port</p>
                  <p className="font-bold text-gray-900">8000</p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between mb-4 mt-6">
              <h3 className="text-lg font-bold text-gray-900">Product Catalog</h3>
              <button
                onClick={() => setShowProductModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:shadow-lg transition-all"
              >
                <Plus className="w-5 h-5" />
                Add Product
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.map((product) => (
                <div key={product.id} className="p-4 border-2 border-gray-200 rounded-xl hover:border-purple-300 transition-all bg-white shadow-sm">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <p className="text-xs text-gray-500 font-mono">{product.product_code}</p>
                      <p className="font-bold text-gray-900 mt-1">{product.name}</p>
                    </div>
                    <button
                      onClick={() => handleRemoveProduct(product.id)}
                      className="p-1 hover:bg-red-100 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                  <div className="space-y-1 text-sm">
                    <p className="text-gray-600"><span className="font-semibold">Brand:</span> {product.brand}</p>
                    <p className="text-gray-600"><span className="font-semibold">Category:</span> {product.category}</p>
                    <p className="text-green-600 font-bold text-lg mt-2">₹{product.price.toFixed(2)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Add Source Modal */}
      {showSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" onClick={(e) => e.stopPropagation()}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Globe className="w-6 h-6 text-purple-600" />
                Add New Lead Source
              </h3>
              <button onClick={() => setShowSourceModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Source Name *</label>
                <input
                  type="text"
                  value={newSource.name}
                  onChange={(e) => { e.stopPropagation(); setNewSource({ ...newSource, name: e.target.value }); }}
                  placeholder="e.g., GeM Portal"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Website URL *</label>
                <input
                  type="url"
                  value={newSource.url}
                  onChange={(e) => { e.stopPropagation(); setNewSource({ ...newSource, url: e.target.value }); }}
                  placeholder="https://example.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Priority</label>
                <select
                  value={newSource.priority}
                  onChange={(e) => { e.stopPropagation(); setNewSource({ ...newSource, priority: e.target.value }); }}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="high">High Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="low">Low Priority</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowSourceModal(false)}
                className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleAddSource}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all font-medium"
              >
                Add Source
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Product Modal */}
      {showProductModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" onClick={(e) => e.stopPropagation()}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Package className="w-6 h-6 text-green-600" />
                Add New Product
              </h3>
              <button onClick={() => setShowProductModal(false)} className="p-2 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Product Code *</label>
                  <input
                    type="text"
                    value={newProduct.product_code}
                    onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, product_code: e.target.value }); }}
                    placeholder="HAV-SW-001"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Brand *</label>
                  <input
                    type="text"
                    value={newProduct.brand}
                    onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, brand: e.target.value }); }}
                    placeholder="Havells"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Product Name *</label>
                <input
                  type="text"
                  value={newProduct.name}
                  onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, name: e.target.value }); }}
                  placeholder="32A DP MCB - C Curve"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Category</label>
                  <input
                    type="text"
                    value={newProduct.category}
                    onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, category: e.target.value }); }}
                    placeholder="Switchgear"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Price (₹)</label>
                  <input
                    type="number"
                    value={newProduct.price}
                    onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, price: e.target.value }); }}
                    placeholder="245.00"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Specifications</label>
                <textarea
                  value={newProduct.specifications}
                  onChange={(e) => { e.stopPropagation(); setNewProduct({ ...newProduct, specifications: e.target.value }); }}
                  placeholder="Current Rating: 32A, Pole: Double Pole, Breaking Capacity: 10kA"
                  rows="3"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowProductModal(false)}
                className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleAddProduct}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:shadow-lg transition-all font-medium"
              >
                Add Product
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Data Import Tab */}
      {activeTab === 'import' && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Package className="w-6 h-6 text-purple-600" />
            Data Import & Management
          </h2>

          <div className="space-y-6">
            <div className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
              <h3 className="text-lg font-bold text-gray-900 mb-2">Current Database Status</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-sm text-gray-600">Havells</p>
                  <p className="text-xl font-bold text-gray-900">33 products</p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-sm text-gray-600">Polycab</p>
                  <p className="text-xl font-bold text-gray-900">285 products</p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-sm text-gray-600">KEI</p>
                  <p className="text-xl font-bold text-gray-900">45 products</p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-sm text-gray-600">Finolex</p>
                  <p className="text-xl font-bold text-gray-900">164 products</p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm">
                  <p className="text-sm text-gray-600">RR Kabel</p>
                  <p className="text-xl font-bold text-gray-900">166 products</p>
                </div>
                <div className="bg-white p-3 rounded-lg shadow-sm border-2 border-purple-300">
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-xl font-bold text-purple-600">693 products</p>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Import New Data</h3>
              <p className="text-gray-600 mb-4">Upload CSV files to import new OEM product data into the system.</p>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 hover:bg-purple-50 transition-all cursor-pointer">
                <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-700 font-medium mb-2">Drop CSV files here or click to browse</p>
                <p className="text-sm text-gray-500">Supports: Havells, Polycab, KEI, Finolex, RR Kabel formats</p>
                <button className="mt-4 px-6 py-2 bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg transition-all">
                  Select Files
                </button>
              </div>

              <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  <strong>Note:</strong> CSV files will be automatically validated before import. Duplicate entries will be skipped.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Save Button */}
      <div className="mt-6 flex justify-end">
        <button
          onClick={handleSaveSettings}
          disabled={saving}
          className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50 font-semibold text-lg"
        >
          {saving ? (
            <>
              <Zap className="w-6 h-6 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-6 h-6" />
              Save All Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default SettingsPage;
