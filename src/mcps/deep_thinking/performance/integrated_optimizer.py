"""
Integrated Performance Optimizer

Brings together template optimization, database optimization, and system monitoring
for comprehensive performance optimization of the deep thinking engine.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from ..templates.performance_optimizer import TemplatePerformanceOptimizer
from ..data.database_performance import DatabasePerformanceOptimizer
from .system_monitor import SystemPerformanceMonitor

logger = logging.getLogger(__name__)


class IntegratedPerformanceOptimizer:
    """
    Integrated performance optimizer that coordinates template, database,
    and system-level optimizations for the deep thinking engine.
    """
    
    def __init__(
        self,
        templates_dir: str,
        db_path: str,
        enable_template_optimization: bool = True,
        enable_database_optimization: bool = True,
        enable_system_monitoring: bool = True,
        monitoring_interval: float = 30.0
    ):
        self.templates_dir = templates_dir
        self.db_path = db_path
        self.monitoring_interval = monitoring_interval
        
        # Initialize optimizers
        self.template_optimizer = None
        self.database_optimizer = None
        self.system_monitor = None
        
        if enable_template_optimization:
            try:
                from pathlib import Path
                self.template_optimizer = TemplatePerformanceOptimizer(
                    Path(templates_dir),
                    cache_size=100,
                    cache_memory_mb=50
                )
                logger.info("Template performance optimizer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize template optimizer: {e}")
        
        if enable_database_optimization and db_path != ":memory:":
            try:
                self.database_optimizer = DatabasePerformanceOptimizer(
                    db_path,
                    min_connections=2,
                    max_connections=10
                )
                logger.info("Database performance optimizer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database optimizer: {e}")
        
        if enable_system_monitoring:
            try:
                self.system_monitor = SystemPerformanceMonitor(monitoring_interval)
                # Register optimization callback
                self.system_monitor.add_optimization_callback(self._handle_performance_issues)
                logger.info("System performance monitor initialized")
            except Exception as e:
                logger.error(f"Failed to initialize system monitor: {e}")
        
        # Performance tracking
        self.optimization_history = []
        self.last_optimization = None
        self.lock = threading.RLock()
    
    def start_monitoring(self):
        """Start comprehensive performance monitoring"""
        if self.system_monitor:
            self.system_monitor.start_monitoring()
            logger.info("Integrated performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if self.system_monitor:
            self.system_monitor.stop_monitoring()
            logger.info("Integrated performance monitoring stopped")
    
    def track_operation(self, operation_name: str):
        """Track an operation across all performance systems"""
        if self.system_monitor:
            return self.system_monitor.track_operation(operation_name)
        else:
            # Return a no-op context manager
            return NoOpTracker()
    
    def get_template(self, name: str, load_func: Callable[[str], Optional[str]]) -> Optional[str]:
        """Get template with performance optimization"""
        if self.template_optimizer:
            return self.template_optimizer.get_template(name, load_func)
        else:
            return load_func(name)
    
    def execute_database_query(self, query: str, params: tuple = ()):
        """Execute database query with performance optimization"""
        if self.database_optimizer:
            return self.database_optimizer.execute_query(query, params)
        else:
            raise NotImplementedError("Database optimizer not available")
    
    def optimize_all_systems(self):
        """Run comprehensive optimization across all systems"""
        with self.lock:
            optimization_start = time.time()
            optimizations_applied = []
            
            try:
                logger.info("Starting comprehensive system optimization...")
                
                # Template optimization
                if self.template_optimizer:
                    try:
                        self.template_optimizer.optimize_cache()
                        self.template_optimizer.preload_high_priority_templates()
                        optimizations_applied.append("template_optimization")
                        logger.info("Template optimization completed")
                    except Exception as e:
                        logger.error(f"Template optimization failed: {e}")
                
                # Database optimization
                if self.database_optimizer:
                    try:
                        self.database_optimizer.optimize_database()
                        optimizations_applied.append("database_optimization")
                        logger.info("Database optimization completed")
                    except Exception as e:
                        logger.error(f"Database optimization failed: {e}")
                
                # System optimization
                if self.system_monitor:
                    try:
                        self.system_monitor.optimize_system_performance()
                        optimizations_applied.append("system_optimization")
                        logger.info("System optimization completed")
                    except Exception as e:
                        logger.error(f"System optimization failed: {e}")
                
                optimization_time = time.time() - optimization_start
                
                # Record optimization
                optimization_record = {
                    'timestamp': datetime.now(),
                    'optimizations_applied': optimizations_applied,
                    'optimization_time': optimization_time,
                    'success': len(optimizations_applied) > 0
                }
                
                self.optimization_history.append(optimization_record)
                self.last_optimization = optimization_record
                
                logger.info(f"Comprehensive optimization completed in {optimization_time:.2f}s")
                logger.info(f"Applied optimizations: {optimizations_applied}")
                
                return optimization_record
                
            except Exception as e:
                logger.error(f"Error during comprehensive optimization: {e}")
                return {
                    'timestamp': datetime.now(),
                    'optimizations_applied': [],
                    'optimization_time': time.time() - optimization_start,
                    'success': False,
                    'error': str(e)
                }
    
    def _handle_performance_issues(self, bottleneck_result: Dict[str, Any]):
        """Handle detected performance issues"""
        try:
            severity = bottleneck_result.get('severity', 'unknown')
            bottleneck_count = bottleneck_result.get('total_bottlenecks', 0)
            
            logger.warning(f"Performance issues detected: {bottleneck_count} bottlenecks, severity: {severity}")
            
            # Apply targeted optimizations based on bottleneck type
            if severity in ['medium', 'high']:
                logger.info("Applying automatic performance optimizations...")
                
                # Template cache optimization for memory issues
                if any('memory' in str(b) for b in bottleneck_result.get('resource_bottlenecks', [])):
                    if self.template_optimizer:
                        self.template_optimizer.optimize_cache()
                        logger.info("Applied template cache optimization for memory issues")
                
                # Database optimization for slow queries
                if any('Slow operation' in str(b) for b in bottleneck_result.get('response_bottlenecks', [])):
                    if self.database_optimizer:
                        self.database_optimizer.analyze_database_performance()
                        logger.info("Applied database analysis for slow operations")
                
                # System optimization for high resource usage
                if severity == 'high':
                    if self.system_monitor:
                        self.system_monitor.optimize_system_performance()
                        logger.info("Applied system optimization for high severity issues")
            
        except Exception as e:
            logger.error(f"Error handling performance issues: {e}")
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics from all systems"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'integrated_optimizer': {
                'template_optimizer_enabled': self.template_optimizer is not None,
                'database_optimizer_enabled': self.database_optimizer is not None,
                'system_monitor_enabled': self.system_monitor is not None,
                'last_optimization': self.last_optimization,
                'optimization_count': len(self.optimization_history)
            }
        }
        
        # Template metrics
        if self.template_optimizer:
            try:
                template_metrics = self.template_optimizer.get_performance_metrics()
                metrics['template_performance'] = template_metrics
            except Exception as e:
                logger.error(f"Error getting template metrics: {e}")
                metrics['template_performance'] = {'error': str(e)}
        
        # Database metrics
        if self.database_optimizer:
            try:
                database_metrics = self.database_optimizer.get_performance_metrics()
                metrics['database_performance'] = database_metrics
            except Exception as e:
                logger.error(f"Error getting database metrics: {e}")
                metrics['database_performance'] = {'error': str(e)}
        
        # System metrics
        if self.system_monitor:
            try:
                system_metrics = self.system_monitor.get_performance_summary()
                metrics['system_performance'] = system_metrics
            except Exception as e:
                logger.error(f"Error getting system metrics: {e}")
                metrics['system_performance'] = {'error': str(e)}
        
        return metrics
    
    def generate_performance_report(self) -> str:
        """Generate comprehensive performance report"""
        metrics = self.get_comprehensive_metrics()
        
        report = []
        report.append("=== Integrated Performance Report ===")
        report.append(f"Generated: {metrics['timestamp']}")
        report.append("")
        
        # Optimizer status
        optimizer_info = metrics['integrated_optimizer']
        report.append("Optimizer Status:")
        report.append(f"  Template Optimization: {'Enabled' if optimizer_info['template_optimizer_enabled'] else 'Disabled'}")
        report.append(f"  Database Optimization: {'Enabled' if optimizer_info['database_optimizer_enabled'] else 'Disabled'}")
        report.append(f"  System Monitoring: {'Enabled' if optimizer_info['system_monitor_enabled'] else 'Disabled'}")
        report.append(f"  Total Optimizations: {optimizer_info['optimization_count']}")
        report.append("")
        
        # Template performance
        if 'template_performance' in metrics and 'error' not in metrics['template_performance']:
            template_perf = metrics['template_performance']
            if 'cache_metrics' in template_perf:
                cache_metrics = template_perf['cache_metrics']
                report.append("Template Performance:")
                report.append(f"  Cache Hit Rate: {cache_metrics.get('hit_rate', 0):.1%}")
                report.append(f"  Cache Size: {cache_metrics.get('cache_size', 0)} templates")
                report.append(f"  Memory Usage: {cache_metrics.get('cache_memory_usage_mb', 0):.1f}MB")
                report.append("")
        
        # Database performance
        if 'database_performance' in metrics and 'error' not in metrics['database_performance']:
            db_perf = metrics['database_performance']
            if 'connection_pool' in db_perf:
                pool_metrics = db_perf['connection_pool']
                report.append("Database Performance:")
                report.append(f"  Active Connections: {pool_metrics.get('active_connections', 0)}")
                report.append(f"  Pool Utilization: {pool_metrics.get('pool_utilization', 0):.1%}")
                report.append(f"  Average Wait Time: {pool_metrics.get('average_wait_time', 0):.3f}s")
                report.append("")
        
        # System performance
        if 'system_performance' in metrics and 'error' not in metrics['system_performance']:
            sys_perf = metrics['system_performance']
            if 'system_resources' in sys_perf:
                resources = sys_perf['system_resources']
                report.append("System Performance:")
                report.append(f"  CPU Usage: {resources.get('cpu_percent', 0):.1f}%")
                report.append(f"  Memory Usage: {resources.get('memory_percent', 0):.1f}%")
                report.append(f"  Process Memory: {resources.get('process_memory_mb', 0):.1f}MB")
                report.append("")
            
            # Recent bottlenecks
            if sys_perf.get('recent_bottlenecks'):
                report.append("Recent Performance Issues:")
                for bottleneck in sys_perf['recent_bottlenecks'][-3:]:
                    report.append(f"  {bottleneck['timestamp']} - Severity: {bottleneck['severity']}")
                    for rec in bottleneck.get('recommendations', []):
                        report.append(f"    • {rec}")
                report.append("")
        
        # Optimization history
        if self.optimization_history:
            report.append("Recent Optimizations:")
            for opt in self.optimization_history[-5:]:  # Last 5 optimizations
                timestamp = opt['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                report.append(f"  {timestamp} - {', '.join(opt['optimizations_applied'])}")
            report.append("")
        
        return "\n".join(report)
    
    def reset_all_statistics(self):
        """Reset statistics across all performance systems"""
        with self.lock:
            if self.template_optimizer:
                self.template_optimizer.reset_statistics()
            
            if self.system_monitor:
                self.system_monitor.reset_statistics()
            
            self.optimization_history.clear()
            self.last_optimization = None
            
            logger.info("All performance statistics reset")
    
    def shutdown(self):
        """Shutdown all performance systems"""
        try:
            if self.system_monitor:
                self.system_monitor.shutdown()
            
            if self.template_optimizer:
                self.template_optimizer.shutdown()
            
            if self.database_optimizer:
                self.database_optimizer.shutdown()
            
            logger.info("Integrated performance optimizer shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


class NoOpTracker:
    """No-operation tracker for when system monitoring is disabled"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def mark_error(self):
        pass