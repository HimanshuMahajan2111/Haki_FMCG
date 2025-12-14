import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import RFPDiscovery from './pages/RFPDiscovery';
import Processing from './pages/Processing';
import Review from './pages/Review';
import FinalDocument from './pages/FinalDocument';
import DataImport from './pages/DataImport';
import { FileText, Search, Settings, Cpu, CheckCircle, Upload } from 'lucide-react';
import './App.css';

const TabbedLayout = () => {
  const tabs = [
    { path: '/overview', label: 'Overview', icon: '🏠' },
    { path: '/active-rfps', label: 'Active RFPs', icon: '📄' },
    { path: '/drafts', label: 'Drafts', icon: '📑' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="site-wrapper">

      <nav className="side-nav-bar">
        <div className="nav-logo">
          <span>RFP Dashboard</span>
        </div>

        <div className="tab-links-container">
          {tabs.map((tab) => (
            <NavLink
              key={tab.path}
              to={tab.path}
              className={({ isActive }) => (isActive ? 'side-tab-link active' : 'side-tab-link')}
            >
              <span className="tab-icon">{tab.icon}</span>
              {tab.label}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="main-content-area">

        <header className="top-content-header">
          <div className="user-actions">
            <button className="icon-button notification-button">🔔</button>
            <button className="icon-button profile-button">👤</button>
          </div>
        </header>

        <div className="tab-content-container">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-primary-700 text-white transition-all duration-300`}>
          <div className="p-4">
            <h1 className={`font-bold text-xl ${!sidebarOpen && 'hidden'}`}>
              🤖 RFP AI System
            </h1>
            {!sidebarOpen && <span className="text-2xl">🤖</span>}
          </div>
          
          <nav className="mt-8">
            <SidebarLink to="/" icon={<FileText size={20} />} label="Dashboard" collapsed={!sidebarOpen} />
            <SidebarLink to="/discovery" icon={<Search size={20} />} label="RFP Discovery" collapsed={!sidebarOpen} />
            <SidebarLink to="/processing" icon={<Cpu size={20} />} label="Processing" collapsed={!sidebarOpen} />
            <SidebarLink to="/review" icon={<CheckCircle size={20} />} label="Review" collapsed={!sidebarOpen} />
            <SidebarLink to="/document" icon={<FileText size={20} />} label="Final Document" collapsed={!sidebarOpen} />
            <SidebarLink to="/import" icon={<Upload size={20} />} label="Data Import" collapsed={!sidebarOpen} />
          </nav>

          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="absolute bottom-4 left-4 text-white hover:text-gray-300"
          >
            <Settings size={20} />
          </button>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/discovery" element={<RFPDiscovery />} />
            <Route path="/processing" element={<Processing />} />
            <Route path="/review" element={<Review />} />
            <Route path="/document" element={<FinalDocument />} />
            <Route path="/import" element={<DataImport />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function SidebarLink({ to, icon, label, collapsed }) {
  return (
    <Link 
      to={to}
      className="flex items-center px-4 py-3 hover:bg-primary-600 transition-colors"
    >
      <span className="mr-3">{icon}</span>
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}

export default App;