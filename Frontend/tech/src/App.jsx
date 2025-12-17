import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { FileText, Search, Settings, Cpu, CheckCircle, Upload, Wrench, BarChart3, Package, Activity, Home, Globe, History } from 'lucide-react';

// Import RAF AI pages
import Login from './pages/Login';
import EnhancedDashboard from './pages/EnhancedDashboard';
import RunHistory from './pages/RunHistory';
import WebsiteMonitoring from './pages/WebsiteMonitoring';
import SettingsPage from './pages/SettingsPage';
import RFPProcessingPage from './pages/RFPProcessingPage';

// Import existing pages
import Dashboard from './pages/Dashboard';
import RFPDiscovery from './pages/RFPDiscovery';
import Processing from './pages/Processing';
import Review from './pages/Review';
import FinalDocument from './pages/FinalDocument';
import DataImport from './pages/DataImport';
import SystemManagement from './pages/SystemManagement';
import ChallengeFlow from './pages/ChallengeFlow';
import ProductsPage from './pages/ProductsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import OrchestratorPage from './pages/OrchestratorPage';
import SystemOverview from './pages/SystemOverview';
import ProcurementPortalsPage from './pages/ProcurementPortalsPage';

import './App.css';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [systemStatus, setSystemStatus] = useState({ online: true, activeWorkflows: 0 });

  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const response = await fetch('/health');
        if (response.ok) {
          const data = await response.json();
          setSystemStatus({
            online: data.status === 'healthy',
            activeWorkflows: data.active_workflows || 0
          });
        }
      } catch (error) {
        setSystemStatus({ online: false, activeWorkflows: 0 });
      }
    };

    fetchSystemStatus();
    // Auto-refresh disabled
    // const interval = setInterval(fetchSystemStatus, 30000); // Changed from 10s to 30s
    // return () => clearInterval(interval);
  }, []);

  const ProtectedRoute = ({ children }) => {
    const user = localStorage.getItem('user');
    return user ? children : <Navigate to="/login" replace />;
  };

  return (
    <Router>
      <div className="flex flex-col h-screen bg-gradient-to-br from-dark-900 to-dark-800">
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/*" element={
            <div className="flex flex-col h-screen">
              <header className="bg-dark-900/80 backdrop-blur-xl border-b border-dark-700/50 shadow-lg z-50">
                <div className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-lg">
                        <span className="text-2xl">🤖</span>
                      </div>
                      <div>
                        <h1 className="font-bold text-lg text-white">RFP AI System</h1>
                        <p className="text-xs text-gray-400">Intelligent Automation Platform</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-400">Admin</span>
                      <button 
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 text-gray-400 hover:text-white hover:bg-dark-800 rounded-lg transition-all"
                      >
                        <Settings size={20} />
                      </button>
                    </div>
                  </div>
                </div>
              </header>

              <div className="flex flex-1 overflow-hidden">
                <aside className={`${sidebarOpen ? 'w-72' : 'w-20'} bg-dark-900/50 backdrop-blur-xl border-r border-dark-700/50 transition-all duration-300 flex flex-col shadow-2xl`}>
                  {sidebarOpen && (
                    <div className="p-4 border-b border-dark-700/50">
                      <div className="bg-dark-800/50 rounded-lg p-4">
                        <h3 className="text-xs text-gray-400 mb-2">Quick Stats</h3>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-300">Active RFPs</span>
                            <span className="text-sm font-bold text-primary-400">12</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-300">Processing</span>
                            <span className="text-sm font-bold text-yellow-400">5</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-300">Completed</span>
                            <span className="text-sm font-bold text-green-400">47</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {/* 6 ESSENTIAL TABS - Fully Integrated */}
                    <SidebarLink to="/" icon={<Home size={20} />} label="Dashboard" collapsed={!sidebarOpen} />
                    <SidebarLink to="/rfps" icon={<Globe size={20} />} label="RFP Processing" collapsed={!sidebarOpen} />
                    <SidebarLink to="/products" icon={<Package size={20} />} label="Products (693)" collapsed={!sidebarOpen} />
                    <SidebarLink to="/analytics" icon={<BarChart3 size={20} />} label="Analytics" collapsed={!sidebarOpen} />
                    <SidebarLink to="/history" icon={<History size={20} />} label="History" collapsed={!sidebarOpen} />
                    <SidebarLink to="/settings" icon={<Settings size={20} />} label="Settings" collapsed={!sidebarOpen} />
                  </nav>

                  <div className="p-4 border-t border-dark-700/50">
                    <button 
                      onClick={() => setSidebarOpen(!sidebarOpen)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 text-dark-300 hover:text-white hover:bg-dark-800/50 rounded-xl transition-all duration-200"
                    >
                      {sidebarOpen ? (
                        <>
                          <span className="transform rotate-180">→</span>
                          <span>Collapse</span>
                        </>
                      ) : (
                        <span>→</span>
                      )}
                    </button>
                  </div>
                </aside>

                <main className="flex-1 overflow-y-auto bg-gradient-to-br from-dark-800 to-dark-900">
                  <div className="w-full h-full">
                    <Routes>
                      {/* 6 ESSENTIAL TABS - Fully Integrated System */}
                      <Route path="/" element={<ProtectedRoute><EnhancedDashboard /></ProtectedRoute>} />
                      <Route path="/rfps" element={<ProtectedRoute><ProcurementPortalsPage /></ProtectedRoute>} />
                      <Route path="/rfp/process/:rfpId" element={<ProtectedRoute><RFPProcessingPage /></ProtectedRoute>} />
                      <Route path="/products" element={<ProtectedRoute><ProductsPage /></ProtectedRoute>} />
                      <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
                      <Route path="/history" element={<ProtectedRoute><RunHistory /></ProtectedRoute>} />
                      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
                    </Routes>
                  </div>
                </main>
              </div>

              <footer className="bg-dark-900/80 backdrop-blur-xl border-t border-dark-700/50 px-6 py-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${systemStatus.online ? 'bg-green-400 animate-pulse-slow' : 'bg-red-400'}`}></span>
                      <span className="text-gray-400">
                        System Status: <span className={systemStatus.online ? 'text-green-400' : 'text-red-400'}>
                          {systemStatus.online ? 'Online' : 'Offline'}
                        </span>
                      </span>
                    </div>
                    <div className="text-gray-400">
                      Active Workflows: <span className="text-white font-semibold">{systemStatus.activeWorkflows}</span>
                    </div>
                    <div className="text-gray-400">
                      Version: <span className="text-white">1.0.0</span>
                    </div>
                  </div>
                  <div className="text-gray-400">
                    © 2024 RFP AI System. All rights reserved.
                  </div>
                </div>
              </footer>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
}

function SidebarLink({ to, icon, label, collapsed }) {
  const location = window.location;
  const isActive = location.pathname === to;
  
  return (
    <Link 
      to={to}
      className={`group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
        isActive 
          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/30' 
          : 'text-dark-300 hover:text-white hover:bg-dark-800/50'
      }`}
    >
      <span className={`${isActive ? 'text-white' : 'text-dark-400 group-hover:text-primary-400'} transition-colors`}>
        {icon}
      </span>
      {!collapsed && (
        <span className="text-sm font-medium">{label}</span>
      )}
      {!collapsed && isActive && (
        <span className="ml-auto w-2 h-2 bg-white rounded-full animate-pulse"></span>
      )}
    </Link>
  );
}

export default App;
