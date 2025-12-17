import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, Mail, Lock, Eye, EyeOff, Zap } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({
    email: 'sales@hakifmcg.com',
    password: 'demo123'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const demoAccounts = [
    { role: 'Sales Team', email: 'sales@hakifmcg.com', password: 'demo123', color: 'bg-blue-500' },
    { role: 'Operations', email: 'ops@hakifmcg.com', password: 'demo123', color: 'bg-green-500' },
    { role: 'Admin', email: 'admin@hakifmcg.com', password: 'demo123', color: 'bg-purple-500' }
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));

      // Store user info in localStorage
      const userRole = credentials.email.split('@')[0];
      localStorage.setItem('user', JSON.stringify({
        email: credentials.email,
        role: userRole,
        name: userRole.charAt(0).toUpperCase() + userRole.slice(1),
        loginTime: new Date().toISOString()
      }));
      localStorage.setItem('credentials_verified', 'true'); // mark credentials as complete

      // Navigate to dashboard
      navigate('/');
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = (demo) => {
    setCredentials({
      email: demo.email,
      password: demo.password
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      {/* Background Animation */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute w-96 h-96 bg-blue-500/20 rounded-full blur-3xl -top-48 -left-48 animate-pulse"></div>
        <div className="absolute w-96 h-96 bg-purple-500/20 rounded-full blur-3xl -bottom-48 -right-48 animate-pulse delay-1000"></div>
      </div>

      <div className="relative w-full max-w-6xl grid md:grid-cols-2 gap-8 items-center">
        {/* Left Side - Branding */}
        <div className="text-white space-y-6 hidden md:block">
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-sky-400 to-blue-600 rounded-xl flex items-center justify-center">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">RAF AI</h1>
              <p className="text-blue-300 text-sm">RFP Analysis Framework</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold mb-4">
            Transform Your<br />RFP Sales Process
          </h2>
          <p className="text-xl text-blue-200 mb-8">
            AI-powered multi-agent system for intelligent tender analysis and bid optimization
          </p>

          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-blue-300 font-bold">1</span>
              </div>
              <div>
                <h3 className="font-semibold text-lg">30-60 Second Analysis</h3>
                <p className="text-blue-300">Complete RFP evaluation in under a minute</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-blue-300 font-bold">2</span>
              </div>
              <div>
                <h3 className="font-semibold text-lg">Win Probability Scoring</h3>
                <p className="text-blue-300">AI-driven likelihood assessment for each opportunity</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-blue-300 font-bold">3</span>
              </div>
              <div>
                <h3 className="font-semibold text-lg">Multi-Scenario Pricing</h3>
                <p className="text-blue-300">Margin-focused, competitive, and aggressive strategies</p>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-blue-700/50">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-sky-400">90%</div>
                <div className="text-sm text-blue-300">Win Rate</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-sky-400">60s</div>
                <div className="text-sm text-blue-300">Avg Response</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-sky-400">500+</div>
                <div className="text-sm text-blue-300">RFPs Analyzed</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-10">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
            <p className="text-gray-600">Sign in to access your AI-powered RFP cockpit</p>
          </div>

          
          <div className="mb-6">
            <p className="text-sm font-semibold text-gray-700 mb-3">Quick Demo Access:</p>
            <div className="grid gap-2">
              {demoAccounts.map((demo, idx) => (
                <button
                  key={idx}
                  onClick={() => handleDemoLogin(demo)}
                  className={`${demo.color} bg-opacity-10 hover:bg-opacity-20 transition-all p-3 rounded-lg text-left border-2 ${
                    credentials.email === demo.email ? 'border-blue-500' : 'border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-gray-900">{demo.role}</div>
                      <div className="text-sm text-gray-600">{demo.email}</div>
                    </div>
                    <div className={`w-8 h-8 ${demo.color} rounded-full flex items-center justify-center`}>
                      <span className="text-white font-bold text-xs">{demo.role.charAt(0)}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">or enter manually</span>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="email"
                  value={credentials.email}
                  onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
                  className="w-full pl-11 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all outline-none"
                  placeholder="Enter your email"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={credentials.password}
                  onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  className="w-full pl-11 pr-12 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all outline-none"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input type="checkbox" className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500" />
                <span className="ml-2 text-sm text-gray-600">Remember me</span>
              </label>
              <a href="#" className="text-sm font-semibold text-blue-600 hover:text-blue-700">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-sky-500 to-blue-600 text-white font-bold py-3 rounded-lg hover:from-sky-600 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              Don't have an account?{' '}
              <a href="#" className="font-semibold text-blue-600 hover:text-blue-700">
                Contact Admin
              </a>
            </p>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-800">
              <strong>Demo Mode:</strong> Use any of the quick access accounts above. All features are fully functional with sample data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
