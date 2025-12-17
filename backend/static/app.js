// RFP AI System - API Client & Dashboard Logic

class RFPAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.wsConnection = null;
    }

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // Analytics Endpoints
    async getDashboard(days = 30) {
        return this.request(`/api/v1/analytics/dashboard?days=${days}`);
    }

    async getRFPProcessing(days = 30) {
        return this.request(`/api/v1/analytics/rfp-processing?days=${days}`);
    }

    async getMatchAccuracy(days = 30) {
        return this.request(`/api/v1/analytics/match-accuracy?days=${days}`);
    }

    async getWinRates(days = 30) {
        return this.request(`/api/v1/analytics/win-rates?days=${days}`);
    }

    async getAgentPerformance(days = 30) {
        return this.request(`/api/v1/analytics/agent-performance?days=${days}`);
    }

    async getSystemHealth() {
        return this.request('/api/v1/analytics/system-health');
    }

    async getRealtime() {
        return this.request('/api/v1/analytics/realtime');
    }

    async getPerformance() {
        return this.request('/api/v1/analytics/performance');
    }

    async getBottlenecks() {
        return this.request('/api/v1/analytics/bottlenecks');
    }

    async getCacheStats() {
        return this.request('/api/v1/analytics/cache-stats');
    }

    async clearCache(pattern = '*') {
        return this.request('/api/v1/analytics/cache/clear', {
            method: 'POST',
            body: JSON.stringify({ pattern })
        });
    }

    async getErrors() {
        return this.request('/api/v1/analytics/errors');
    }

    // RFP Workflow Endpoints
    async submitRFP(rfpData) {
        return this.request('/api/v1/rfp', {
            method: 'POST',
            body: JSON.stringify(rfpData)
        });
    }

    async getWorkflowStatus(workflowId) {
        return this.request(`/api/v1/workflow/${workflowId}`);
    }

    async listWorkflows() {
        return this.request('/api/v1/workflows');
    }

    async getHealth() {
        return this.request('/api/v1/health');
    }

    // WebSocket for Real-Time Updates
    connectWebSocket() {
        const wsURL = this.baseURL.replace('http', 'ws');
        this.wsConnection = new WebSocket(`${wsURL}/ws/updates`);
        
        this.wsConnection.onopen = () => {
            console.log('WebSocket connected');
            addRealTimeUpdate('Connected to real-time updates');
        };

        this.wsConnection.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleRealTimeUpdate(data);
        };

        this.wsConnection.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.wsConnection.onclose = () => {
            console.log('WebSocket closed, reconnecting...');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }

    disconnectWebSocket() {
        if (this.wsConnection) {
            this.wsConnection.close();
        }
    }
}

// Initialize API Client
const apiClient = new RFPAPIClient();

// Dashboard State
let dashboardData = null;
let updateInterval = null;

// Initialize Dashboard
async function initDashboard() {
    try {
        await loadOverview();
        startAutoRefresh();
        // Try to connect WebSocket (will fail gracefully if not supported)
        // apiClient.connectWebSocket();
    } catch (error) {
        showError('Failed to initialize dashboard', error);
    }
}

// Load Overview Tab
async function loadOverview() {
    try {
        dashboardData = await apiClient.getDashboard(30);
        renderOverviewMetrics(dashboardData);
        updateLastRefreshTime();
    } catch (error) {
        showError('Failed to load overview', error);
    }
}

// Render Overview Metrics
function renderOverviewMetrics(data) {
    const container = document.getElementById('overviewMetrics');
    
    const metrics = [
        {
            title: 'Total RFPs Processed',
            value: data.rfp_processing?.total_rfps || 0,
            subtitle: `${data.rfp_processing?.success_rate || 0}% success rate`
        },
        {
            title: 'Average Processing Time',
            value: `${Math.round(data.rfp_processing?.average_processing_time_seconds || 0)}s`,
            subtitle: 'Per RFP workflow'
        },
        {
            title: 'Match Accuracy',
            value: `${Math.round(data.match_accuracy?.average_match_score * 100 || 0)}%`,
            subtitle: `${data.match_accuracy?.total_matches || 0} total matches`
        },
        {
            title: 'Win Rate',
            value: `${Math.round(data.win_rates?.overall_win_rate || 0)}%`,
            subtitle: `$${(data.win_rates?.average_quote_value_won || 0).toLocaleString()} avg deal`
        },
        {
            title: 'Active Workflows',
            value: data.system_health?.active_workflows || 0,
            subtitle: 'Currently processing'
        },
        {
            title: 'System Health',
            value: `${Math.round(100 - (data.system_health?.cpu_percent || 0))}%`,
            subtitle: `CPU: ${Math.round(data.system_health?.cpu_percent || 0)}%`
        }
    ];

    container.innerHTML = metrics.map(metric => `
        <div class="metric-card">
            <h3>${metric.title}</h3>
            <div class="metric-value">${metric.value}</div>
            <div class="metric-subtitle">${metric.subtitle}</div>
        </div>
    `).join('');

    // Add charts below metrics
    container.innerHTML += `
        <div class="chart-container" style="grid-column: 1 / -1;">
            <h2>Recent Activity</h2>
            ${renderStatusBreakdown(data.rfp_processing)}
        </div>
        <div class="chart-container" style="grid-column: 1 / -1;">
            <h2>Top Performing Agents</h2>
            ${renderAgentPerformance(data.agent_performance)}
        </div>
    `;
}

// Render Status Breakdown
function renderStatusBreakdown(rfpData) {
    if (!rfpData || !rfpData.status_breakdown) {
        return '<p>No data available</p>';
    }

    const total = rfpData.total_rfps || 1;
    return `
        ${Object.entries(rfpData.status_breakdown).map(([status, count]) => {
            const percentage = (count / total * 100).toFixed(1);
            const badgeClass = status === 'completed' ? 'badge-success' : 
                              status === 'failed' ? 'badge-error' : 'badge-info';
            return `
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span><span class="badge ${badgeClass}">${status}</span></span>
                        <span>${count} (${percentage}%)</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        }).join('')}
    `;
}

// Render Agent Performance
function renderAgentPerformance(agentData) {
    if (!agentData || !agentData.agents || agentData.agents.length === 0) {
        return '<p>No agent data available</p>';
    }

    return `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Executions</th>
                    <th>Success Rate</th>
                    <th>Avg Duration</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${agentData.agents.slice(0, 10).map(agent => `
                    <tr>
                        <td><strong>${agent.agent_name}</strong></td>
                        <td>${agent.total_executions}</td>
                        <td>${Math.round(agent.success_rate)}%</td>
                        <td>${agent.avg_duration_seconds.toFixed(2)}s</td>
                        <td><span class="badge badge-success">Active</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Load RFP Processing Tab
async function loadRFPProcessing() {
    try {
        const data = await apiClient.getRFPProcessing(30);
        const container = document.getElementById('rfpContent');
        
        container.innerHTML = `
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Total RFPs</h3>
                    <div class="metric-value">${data.total_rfps}</div>
                    <div class="metric-subtitle">Last 30 days</div>
                </div>
                <div class="metric-card">
                    <h3>Success Rate</h3>
                    <div class="metric-value">${Math.round(data.success_rate)}%</div>
                    <div class="metric-subtitle">${data.status_breakdown?.completed || 0} completed</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Processing Time</h3>
                    <div class="metric-value">${Math.round(data.average_processing_time_seconds)}s</div>
                    <div class="metric-subtitle">End-to-end workflow</div>
                </div>
            </div>
            ${renderStatusBreakdown(data)}
            <h3 style="margin-top: 30px;">Stage Processing Times</h3>
            ${renderStageBreakdown(data.stage_times)}
            <h3 style="margin-top: 30px;">Daily Volume Trend</h3>
            ${renderDailyVolume(data.daily_volume)}
        `;
    } catch (error) {
        showError('Failed to load RFP processing data', error);
    }
}

// Render Stage Breakdown
function renderStageBreakdown(stageTimes) {
    if (!stageTimes) {
        return '<p>No stage data available</p>';
    }

    return `
        <div style="margin-top: 15px;">
            ${Object.entries(stageTimes).map(([stage, seconds]) => `
                <div style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span><strong>${stage.replace('_', ' ')}</strong></span>
                        <span>${seconds.toFixed(2)}s</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(seconds / 10 * 100, 100)}%"></div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Render Daily Volume
function renderDailyVolume(dailyVolume) {
    if (!dailyVolume || dailyVolume.length === 0) {
        return '<p>No daily volume data available</p>';
    }

    const maxCount = Math.max(...dailyVolume.map(d => d.count));
    return `
        <div style="margin-top: 15px;">
            ${dailyVolume.slice(-14).map(day => {
                const percentage = (day.count / maxCount * 100);
                return `
                    <div style="margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>${day.date}</span>
                            <span><strong>${day.count}</strong> RFPs</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Load Analytics Tab
async function loadAnalytics() {
    try {
        const [matchData, winData] = await Promise.all([
            apiClient.getMatchAccuracy(30),
            apiClient.getWinRates(30)
        ]);
        
        const container = document.getElementById('analyticsContent');
        container.innerHTML = `
            <h3>Match Accuracy Metrics</h3>
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Avg Match Score</h3>
                    <div class="metric-value">${(matchData.average_match_score * 100).toFixed(1)}%</div>
                    <div class="metric-subtitle">${matchData.total_matches} matches</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Confidence</h3>
                    <div class="metric-value">${(matchData.average_confidence * 100).toFixed(1)}%</div>
                    <div class="metric-subtitle">Match confidence</div>
                </div>
                <div class="metric-card">
                    <h3>High Confidence</h3>
                    <div class="metric-value">${matchData.high_confidence_matches}</div>
                    <div class="metric-subtitle">${((matchData.high_confidence_matches / matchData.total_matches) * 100).toFixed(1)}% of total</div>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Win Rate Analytics</h3>
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Overall Win Rate</h3>
                    <div class="metric-value">${Math.round(winData.overall_win_rate)}%</div>
                    <div class="metric-subtitle">${winData.total_completed} completed</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Quote Value (Won)</h3>
                    <div class="metric-value">$${winData.average_quote_value_won.toLocaleString()}</div>
                    <div class="metric-subtitle">${winData.total_won} deals won</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Quote Value (Lost)</h3>
                    <div class="metric-value">$${winData.average_quote_value_lost.toLocaleString()}</div>
                    <div class="metric-subtitle">${winData.total_lost} deals lost</div>
                </div>
            </div>
            
            ${renderWinRatesByCustomer(winData.win_rates_by_customer)}
        `;
    } catch (error) {
        showError('Failed to load analytics', error);
    }
}

// Render Win Rates by Customer
function renderWinRatesByCustomer(customerData) {
    if (!customerData || customerData.length === 0) {
        return '';
    }

    return `
        <h3 style="margin-top: 30px;">Win Rates by Customer</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Customer</th>
                    <th>Total RFPs</th>
                    <th>Won</th>
                    <th>Win Rate</th>
                </tr>
            </thead>
            <tbody>
                ${customerData.slice(0, 10).map(customer => `
                    <tr>
                        <td><strong>${customer.customer_id}</strong></td>
                        <td>${customer.total}</td>
                        <td>${customer.won}</td>
                        <td><span class="badge badge-success">${Math.round(customer.win_rate)}%</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Load Performance Tab
async function loadPerformance() {
    try {
        const [perfData, healthData, cacheData, bottlenecks] = await Promise.all([
            apiClient.getPerformance(),
            apiClient.getSystemHealth(),
            apiClient.getCacheStats(),
            apiClient.getBottlenecks()
        ]);
        
        const container = document.getElementById('performanceContent');
        container.innerHTML = `
            <h3>System Resources</h3>
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>CPU Usage</h3>
                    <div class="metric-value">${healthData.cpu_percent.toFixed(1)}%</div>
                    <div class="metric-subtitle">${healthData.cpu_count} cores</div>
                </div>
                <div class="metric-card">
                    <h3>Memory Usage</h3>
                    <div class="metric-value">${healthData.memory_percent.toFixed(1)}%</div>
                    <div class="metric-subtitle">${(healthData.memory_used_gb).toFixed(1)} GB used</div>
                </div>
                <div class="metric-card">
                    <h3>Disk Usage</h3>
                    <div class="metric-value">${healthData.disk_percent.toFixed(1)}%</div>
                    <div class="metric-subtitle">${healthData.disk_free_gb.toFixed(1)} GB free</div>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Cache Performance</h3>
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Cache Hit Rate</h3>
                    <div class="metric-value">${cacheData.hit_rate ? (cacheData.hit_rate * 100).toFixed(1) : 0}%</div>
                    <div class="metric-subtitle">${cacheData.hits || 0} hits / ${cacheData.misses || 0} misses</div>
                </div>
                <div class="metric-card">
                    <h3>Cache Size</h3>
                    <div class="metric-value">${cacheData.size || 0}</div>
                    <div class="metric-subtitle">Cached items</div>
                </div>
                <div class="metric-card">
                    <h3>Redis Status</h3>
                    <div class="metric-value">${cacheData.redis_connected ? '✓' : '✗'}</div>
                    <div class="metric-subtitle">${cacheData.redis_connected ? 'Connected' : 'Disconnected'}</div>
                </div>
            </div>
            
            ${renderBottlenecks(bottlenecks)}
            
            <div class="quick-actions">
                <button class="btn btn-primary" onclick="clearCache()">Clear Cache</button>
                <button class="btn btn-secondary" onclick="loadPerformance()">Refresh</button>
            </div>
        `;
    } catch (error) {
        showError('Failed to load performance data', error);
    }
}

// Render Bottlenecks
function renderBottlenecks(bottlenecks) {
    if (!bottlenecks || bottlenecks.length === 0) {
        return '<h3 style="margin-top: 30px;">No Performance Bottlenecks Detected ✓</h3>';
    }

    return `
        <h3 style="margin-top: 30px;">⚠️ Detected Bottlenecks</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Operation</th>
                    <th>Duration</th>
                    <th>Threshold</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                ${bottlenecks.slice(0, 20).map(b => `
                    <tr>
                        <td><strong>${b.operation_name}</strong></td>
                        <td><span class="badge badge-warning">${b.duration.toFixed(2)}s</span></td>
                        <td>${b.threshold.toFixed(2)}s</td>
                        <td>${new Date(b.timestamp).toLocaleTimeString()}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Load Agents Tab
async function loadAgents() {
    try {
        const data = await apiClient.getAgentPerformance(30);
        const container = document.getElementById('agentsContent');
        
        if (!data.agents || data.agents.length === 0) {
            container.innerHTML = '<p>No agent execution data available</p>';
            return;
        }

        container.innerHTML = `
            <div class="dashboard-grid">
                <div class="metric-card">
                    <h3>Total Agents</h3>
                    <div class="metric-value">${data.agents.length}</div>
                    <div class="metric-subtitle">Active agents</div>
                </div>
                <div class="metric-card">
                    <h3>Total Executions</h3>
                    <div class="metric-value">${data.total_executions}</div>
                    <div class="metric-subtitle">Last 30 days</div>
                </div>
                <div class="metric-card">
                    <h3>Avg Success Rate</h3>
                    <div class="metric-value">${Math.round(data.average_success_rate)}%</div>
                    <div class="metric-subtitle">Across all agents</div>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Agent Rankings</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Agent Name</th>
                        <th>Executions</th>
                        <th>Success Rate</th>
                        <th>Avg Duration</th>
                        <th>Failed</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.agents.map((agent, index) => {
                        const badgeClass = agent.success_rate > 90 ? 'badge-success' : 
                                         agent.success_rate > 70 ? 'badge-warning' : 'badge-error';
                        return `
                            <tr>
                                <td><strong>#${index + 1}</strong></td>
                                <td><strong>${agent.agent_name}</strong></td>
                                <td>${agent.total_executions}</td>
                                <td><span class="badge ${badgeClass}">${Math.round(agent.success_rate)}%</span></td>
                                <td>${agent.avg_duration_seconds.toFixed(2)}s</td>
                                <td>${agent.failed_executions}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    } catch (error) {
        showError('Failed to load agent data', error);
    }
}

// Load API Documentation Tab
function loadAPIDocumentation() {
    const container = document.getElementById('apiContent');
    container.innerHTML = `
        <h3>API Endpoints</h3>
        <p style="margin-bottom: 20px;">Complete API reference for the RFP AI System</p>
        
        <div class="quick-actions" style="margin-bottom: 30px;">
            <button class="btn btn-primary" onclick="window.open('/docs', '_blank')">OpenAPI Docs (Swagger)</button>
            <button class="btn btn-primary" onclick="window.open('/redoc', '_blank')">ReDoc</button>
            <button class="btn btn-secondary" onclick="testAPIEndpoint()">Test API</button>
        </div>
        
        <h3>Analytics Endpoints</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Method</th>
                    <th>Endpoint</th>
                    <th>Description</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/dashboard</td>
                    <td>Complete dashboard data</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/dashboard')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/rfp-processing</td>
                    <td>RFP processing metrics</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/rfp-processing')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/match-accuracy</td>
                    <td>Match accuracy statistics</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/match-accuracy')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/win-rates</td>
                    <td>Win/loss analytics</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/win-rates')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/agent-performance</td>
                    <td>Agent execution metrics</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/agent-performance')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/analytics/system-health</td>
                    <td>System resource monitoring</td>
                    <td><button class="btn btn-secondary" onclick="testEndpoint('/api/v1/analytics/system-health')">Test</button></td>
                </tr>
                <tr>
                    <td><span class="badge badge-success">POST</span></td>
                    <td>/api/v1/analytics/cache/clear</td>
                    <td>Clear cache by pattern</td>
                    <td><button class="btn btn-secondary" onclick="clearCache()">Test</button></td>
                </tr>
            </tbody>
        </table>
        
        <h3 style="margin-top: 30px;">RFP Workflow Endpoints</h3>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Method</th>
                    <th>Endpoint</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="badge badge-success">POST</span></td>
                    <td>/api/v1/rfp</td>
                    <td>Submit new RFP for processing</td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/workflow/{id}</td>
                    <td>Get workflow status</td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/workflows</td>
                    <td>List all workflows</td>
                </tr>
                <tr>
                    <td><span class="badge badge-info">GET</span></td>
                    <td>/api/v1/health</td>
                    <td>System health check</td>
                </tr>
            </tbody>
        </table>
        
        <h3 style="margin-top: 30px;">Example API Call (JavaScript)</h3>
        <pre style="background: #f5f5f5; padding: 20px; border-radius: 8px; overflow-x: auto;">
const apiClient = new RFPAPIClient('http://localhost:8000');

// Get dashboard data
const dashboard = await apiClient.getDashboard(30);
console.log(dashboard);

// Submit RFP
const rfp = await apiClient.submitRFP({
    title: "Network Equipment RFP",
    customer: "Acme Corp",
    file_path: "/path/to/rfp.pdf"
});
console.log('Workflow ID:', rfp.workflow_id);

// Check status
const status = await apiClient.getWorkflowStatus(rfp.workflow_id);
console.log('Status:', status);
        </pre>
        
        <h3 style="margin-top: 30px;">Python Example</h3>
        <pre style="background: #f5f5f5; padding: 20px; border-radius: 8px; overflow-x: auto;">
import requests

# Get dashboard
response = requests.get('http://localhost:8000/api/v1/analytics/dashboard?days=30')
dashboard = response.json()

# Submit RFP
rfp_data = {
    "title": "Network Equipment RFP",
    "customer": "Acme Corp",
    "file_path": "/path/to/rfp.pdf"
}
response = requests.post('http://localhost:8000/api/v1/rfp', json=rfp_data)
workflow = response.json()
print(f"Workflow ID: {workflow['workflow_id']}")
        </pre>
    `;
}

// Test API Endpoint
async function testEndpoint(endpoint) {
    try {
        const response = await apiClient.request(endpoint);
        alert(`Success! Response:\n\n${JSON.stringify(response, null, 2).substring(0, 500)}...`);
        console.log('API Response:', response);
    } catch (error) {
        alert(`Error testing endpoint:\n${error.message}`);
    }
}

// Clear Cache
async function clearCache() {
    if (!confirm('Clear all cache? This will temporarily slow down requests.')) {
        return;
    }
    
    try {
        await apiClient.clearCache('*');
        alert('Cache cleared successfully!');
        await loadPerformance();
    } catch (error) {
        alert(`Failed to clear cache: ${error.message}`);
    }
}

// Tab Switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    // Load tab data
    switch(tabName) {
        case 'overview':
            loadOverview();
            break;
        case 'rfp':
            loadRFPProcessing();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'performance':
            loadPerformance();
            break;
        case 'agents':
            loadAgents();
            break;
        case 'api':
            loadAPIDocumentation();
            break;
    }
}

// Auto Refresh
function startAutoRefresh() {
    updateInterval = setInterval(() => {
        const activeTab = document.querySelector('.tab.active');
        if (activeTab) {
            activeTab.click();
        }
    }, 30000); // Refresh every 30 seconds
}

// Update Last Refresh Time
function updateLastRefreshTime() {
    const element = document.getElementById('lastUpdate');
    if (element) {
        element.textContent = `Last Updated: ${new Date().toLocaleTimeString()}`;
    }
}

// Show Error
function showError(message, error) {
    console.error(message, error);
    const activeContent = document.querySelector('.tab-content.active > div:first-child, .tab-content.active');
    if (activeContent) {
        activeContent.innerHTML = `
            <div class="error">
                <h3>❌ ${message}</h3>
                <p>${error?.message || 'Unknown error occurred'}</p>
                <button class="btn btn-primary" onclick="location.reload()">Reload Page</button>
            </div>
        `;
    }
}

// Real-Time Updates
function addRealTimeUpdate(message) {
    const updates = document.getElementById('realTimeUpdates');
    const list = document.getElementById('updatesList');
    
    if (updates && list) {
        updates.style.display = 'block';
        
        const item = document.createElement('div');
        item.className = 'update-item';
        item.innerHTML = `
            <div>${message}</div>
            <div class="update-time">${new Date().toLocaleTimeString()}</div>
        `;
        
        list.insertBefore(item, list.firstChild);
        
        // Keep only last 5 updates
        while (list.children.length > 5) {
            list.removeChild(list.lastChild);
        }
    }
}

function handleRealTimeUpdate(data) {
    addRealTimeUpdate(`${data.type}: ${data.message}`);
    
    // Refresh relevant tab if needed
    if (data.type === 'workflow_completed' || data.type === 'workflow_failed') {
        loadOverview();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDashboard);

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    apiClient.disconnectWebSocket();
});
