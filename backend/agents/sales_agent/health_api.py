"""
Health Check API - HTTP endpoints for monitoring and status.
"""
from flask import Flask, jsonify, request
from typing import Dict, Any, Optional, Callable
import structlog
from datetime import datetime
from pathlib import Path
import json
import psutil
import os

logger = structlog.get_logger()


class HealthAPI:
    """Flask-based health check and monitoring API."""
    
    def __init__(self, port: int = 5000, host: str = '0.0.0.0'):
        """Initialize health API.
        
        Args:
            port: Port to run on
            host: Host to bind to
        """
        self.app = Flask('sales_agent_health')
        self.port = port
        self.host = host
        self.logger = logger.bind(component="HealthAPI")
        
        # Status tracking
        self.start_time = datetime.now()
        self.status_callbacks: Dict[str, Callable[[], Dict[str, Any]]] = {}
        
        # Register routes
        self._register_routes()
        
        self.logger.info("Health API initialized", port=port, host=host)
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Basic health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            })
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Detailed status endpoint."""
            status_data = {
                'service': 'sales_agent',
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'components': {}
            }
            
            # Get status from all registered callbacks
            for component_name, callback in self.status_callbacks.items():
                try:
                    status_data['components'][component_name] = callback()
                except Exception as e:
                    self.logger.error("Error getting component status", 
                                    component=component_name, error=str(e))
                    status_data['components'][component_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return jsonify(status_data)
        
        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Metrics endpoint (Prometheus-compatible)."""
            metrics_data = self._collect_metrics()
            
            # Check if Prometheus format requested
            if request.args.get('format') == 'prometheus':
                return self._format_prometheus(metrics_data), 200, {'Content-Type': 'text/plain'}
            
            return jsonify(metrics_data)
        
        @self.app.route('/metrics/dashboard', methods=['GET'])
        def dashboard_metrics():
            """Dashboard-specific metrics."""
            try:
                dashboard_file = Path('backend/agents/dashboard_export.json')
                if dashboard_file.exists():
                    with open(dashboard_file, 'r') as f:
                        return jsonify(json.load(f))
                else:
                    return jsonify({'error': 'Dashboard data not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/system', methods=['GET'])
        def system_info():
            """System resource information."""
            return jsonify({
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent,
                    'used': psutil.virtual_memory().used
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                },
                'process': {
                    'pid': os.getpid(),
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                    'cpu_percent': psutil.Process().cpu_percent(interval=0.1)
                }
            })
        
        @self.app.route('/config', methods=['GET'])
        def get_config():
            """Get current configuration."""
            try:
                config_file = Path('backend/agents/sales_agent_config.json')
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        return jsonify(json.load(f))
                else:
                    return jsonify({'error': 'Config not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/config', methods=['POST'])
        def update_config():
            """Update configuration."""
            try:
                new_config = request.json
                config_file = Path('backend/agents/sales_agent_config.json')
                
                with open(config_file, 'w') as f:
                    json.dump(new_config, f, indent=2)
                
                return jsonify({'status': 'updated', 'message': 'Configuration updated successfully'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/state', methods=['GET'])
        def get_state():
            """Get agent state."""
            try:
                state_file = Path('backend/agents/sales_agent_state.json')
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        return jsonify(json.load(f))
                else:
                    return jsonify({'error': 'State not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/logs', methods=['GET'])
        def get_logs():
            """Get recent logs."""
            try:
                limit = int(request.args.get('limit', 100))
                level = request.args.get('level', 'all').upper()
                
                logs = []
                log_file = Path('backend/logs/sales_agent.log')
                
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        for line in f:
                            try:
                                log_entry = json.loads(line)
                                if level == 'ALL' or log_entry.get('level', '').upper() == level:
                                    logs.append(log_entry)
                            except:
                                continue
                
                # Return last N logs
                return jsonify({
                    'logs': logs[-limit:],
                    'total': len(logs),
                    'limit': limit
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/control/start', methods=['POST'])
        def start_monitoring():
            """Start monitoring."""
            # Trigger start via callback
            if 'control' in self.status_callbacks:
                try:
                    result = self.status_callbacks['control']({'action': 'start'})
                    return jsonify(result)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'Control not available'}), 404
        
        @self.app.route('/control/stop', methods=['POST'])
        def stop_monitoring():
            """Stop monitoring."""
            if 'control' in self.status_callbacks:
                try:
                    result = self.status_callbacks['control']({'action': 'stop'})
                    return jsonify(result)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'Control not available'}), 404
        
        @self.app.route('/control/check', methods=['POST'])
        def check_now():
            """Trigger immediate check."""
            if 'control' in self.status_callbacks:
                try:
                    result = self.status_callbacks['control']({'action': 'check'})
                    return jsonify(result)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'Control not available'}), 404
    
    def register_status_callback(self, component_name: str, callback: Callable[[], Dict[str, Any]]):
        """Register status callback for a component.
        
        Args:
            component_name: Name of the component
            callback: Function that returns status dict
        """
        self.status_callbacks[component_name] = callback
        self.logger.info("Status callback registered", component=component_name)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all components."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        # Collect from callbacks
        for component_name, callback in self.status_callbacks.items():
            try:
                component_metrics = callback()
                if isinstance(component_metrics, dict) and 'metrics' in component_metrics:
                    metrics[component_name] = component_metrics['metrics']
            except Exception as e:
                self.logger.error("Error collecting metrics", 
                                component=component_name, error=str(e))
        
        return metrics
    
    def _format_prometheus(self, metrics: Dict[str, Any]) -> str:
        """Format metrics as Prometheus text format.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Prometheus-formatted string
        """
        lines = []
        
        # Add uptime
        lines.append(f"# HELP sales_agent_uptime_seconds Uptime in seconds")
        lines.append(f"# TYPE sales_agent_uptime_seconds gauge")
        lines.append(f"sales_agent_uptime_seconds {metrics['uptime_seconds']}")
        
        # Add component metrics
        for component, data in metrics.items():
            if component in ['timestamp', 'uptime_seconds']:
                continue
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        metric_name = f"sales_agent_{component}_{key}"
                        lines.append(f"# HELP {metric_name} {component} {key}")
                        lines.append(f"# TYPE {metric_name} gauge")
                        lines.append(f"{metric_name} {value}")
        
        return '\n'.join(lines)
    
    def run(self, debug: bool = False, threaded: bool = True):
        """Run Flask server.
        
        Args:
            debug: Enable debug mode
            threaded: Enable threading
        """
        self.logger.info("Starting health API server", port=self.port, host=self.host)
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=threaded)
    
    def run_background(self):
        """Run Flask server in background thread."""
        import threading
        
        thread = threading.Thread(target=self.run, kwargs={'debug': False, 'threaded': True})
        thread.daemon = True
        thread.start()
        
        self.logger.info("Health API running in background")
        return thread


# FastAPI alternative
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import PlainTextResponse
    import uvicorn
    
    class HealthAPIFastAPI:
        """FastAPI-based health check and monitoring API."""
        
        def __init__(self, port: int = 8000, host: str = '0.0.0.0'):
            """Initialize health API.
            
            Args:
                port: Port to run on
                host: Host to bind to
            """
            self.app = FastAPI(title="Sales Agent Health API")
            self.port = port
            self.host = host
            self.logger = logger.bind(component="HealthAPIFastAPI")
            
            self.start_time = datetime.now()
            self.status_callbacks: Dict[str, Callable[[], Dict[str, Any]]] = {}
            
            self._register_routes()
            
            self.logger.info("FastAPI Health API initialized", port=port, host=host)
        
        def _register_routes(self):
            """Register API routes."""
            
            @self.app.get('/health')
            async def health():
                return {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
                }
            
            @self.app.get('/status')
            async def status():
                status_data = {
                    'service': 'sales_agent',
                    'status': 'running',
                    'timestamp': datetime.now().isoformat(),
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                    'components': {}
                }
                
                for component_name, callback in self.status_callbacks.items():
                    try:
                        status_data['components'][component_name] = callback()
                    except Exception as e:
                        status_data['components'][component_name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                return status_data
            
            @self.app.get('/metrics')
            async def metrics(format: str = 'json'):
                metrics_data = self._collect_metrics()
                
                if format == 'prometheus':
                    return PlainTextResponse(self._format_prometheus(metrics_data))
                
                return metrics_data
        
        def register_status_callback(self, component_name: str, callback: Callable[[], Dict[str, Any]]):
            """Register status callback for a component."""
            self.status_callbacks[component_name] = callback
            self.logger.info("Status callback registered", component=component_name)
        
        def _collect_metrics(self) -> Dict[str, Any]:
            """Collect metrics from all components."""
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
            
            for component_name, callback in self.status_callbacks.items():
                try:
                    component_metrics = callback()
                    if isinstance(component_metrics, dict) and 'metrics' in component_metrics:
                        metrics[component_name] = component_metrics['metrics']
                except Exception as e:
                    self.logger.error("Error collecting metrics", 
                                    component=component_name, error=str(e))
            
            return metrics
        
        def _format_prometheus(self, metrics: Dict[str, Any]) -> str:
            """Format metrics as Prometheus text format."""
            lines = []
            
            lines.append(f"# HELP sales_agent_uptime_seconds Uptime in seconds")
            lines.append(f"# TYPE sales_agent_uptime_seconds gauge")
            lines.append(f"sales_agent_uptime_seconds {metrics['uptime_seconds']}")
            
            for component, data in metrics.items():
                if component in ['timestamp', 'uptime_seconds']:
                    continue
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)):
                            metric_name = f"sales_agent_{component}_{key}"
                            lines.append(f"# HELP {metric_name} {component} {key}")
                            lines.append(f"# TYPE {metric_name} gauge")
                            lines.append(f"{metric_name} {value}")
            
            return '\n'.join(lines)
        
        def run(self):
            """Run uvicorn server."""
            self.logger.info("Starting FastAPI server", port=self.port, host=self.host)
            uvicorn.run(self.app, host=self.host, port=self.port)
        
        def run_background(self):
            """Run uvicorn server in background thread."""
            import threading
            
            thread = threading.Thread(target=self.run)
            thread.daemon = True
            thread.start()
            
            self.logger.info("FastAPI running in background")
            return thread

except ImportError:
    HealthAPIFastAPI = None
