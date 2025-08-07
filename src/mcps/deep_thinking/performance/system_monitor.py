"""
System Performance Monitor

Implements system resource monitoring, performance bottleneck detection,
response time statistics, and comprehensive system performance testing.
"""

import gc
import logging
import os
import psutil
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import weakref

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"


@dataclass
class SystemResourceStats:
    """System resource statistics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_free_gb: float = 0.0
    process_memory_mb: float = 0.0
    process_cpu_percent: float = 0.0
    thread_count: int = 0
    open_files: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResponseTimeStats:
    """Response time statistics for operations"""
    operation_name: str
    total_calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    average_time: float = 0.0
    p95_time: float = 0.0
    p99_time: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


class PerformanceBottleneckDetector:
    """Detects performance bottlenecks in the system"""
    
    def __init__(self):
        self.bottlenecks = []
        self.thresholds = {
            'cpu_high': 80.0,
            'memory_high': 85.0,
            'disk_high': 90.0,
            'response_time_slow': 2.0,  # seconds
            'error_rate_high': 0.05,   # 5%
        }
        self.detection_history = deque(maxlen=100)
    
    def analyze_system_resources(self, stats: SystemResourceStats) -> List[str]:
        """Analyze system resources for bottlenecks"""
        bottlenecks = []
        
        if stats.cpu_percent > self.thresholds['cpu_high']:
            bottlenecks.append(f"High CPU usage: {stats.cpu_percent:.1f}%")
        
        if stats.memory_percent > self.thresholds['memory_high']:
            bottlenecks.append(f"High memory usage: {stats.memory_percent:.1f}%")
        
        if stats.disk_usage_percent > self.thresholds['disk_high']:
            bottlenecks.append(f"High disk usage: {stats.disk_usage_percent:.1f}%")
        
        if stats.process_memory_mb > 500:  # 500MB threshold for process
            bottlenecks.append(f"High process memory: {stats.process_memory_mb:.1f}MB")
        
        return bottlenecks
    
    def analyze_response_times(self, response_stats: Dict[str, ResponseTimeStats]) -> List[str]:
        """Analyze response times for bottlenecks"""
        bottlenecks = []
        
        for operation, stats in response_stats.items():
            if stats.average_time > self.thresholds['response_time_slow']:
                bottlenecks.append(
                    f"Slow operation '{operation}': {stats.average_time:.3f}s average"
                )
            
            if stats.total_calls > 0:
                error_rate = stats.error_count / stats.total_calls
                if error_rate > self.thresholds['error_rate_high']:
                    bottlenecks.append(
                        f"High error rate for '{operation}': {error_rate:.1%}"
                    )
        
        return bottlenecks
    
    def detect_bottlenecks(
        self, 
        system_stats: SystemResourceStats, 
        response_stats: Dict[str, ResponseTimeStats]
    ) -> Dict[str, Any]:
        """Detect all types of bottlenecks"""
        resource_bottlenecks = self.analyze_system_resources(system_stats)
        response_bottlenecks = self.analyze_response_times(response_stats)
        
        all_bottlenecks = resource_bottlenecks + response_bottlenecks
        
        detection_result = {
            'timestamp': datetime.now(),
            'resource_bottlenecks': resource_bottlenecks,
            'response_bottlenecks': response_bottlenecks,
            'total_bottlenecks': len(all_bottlenecks),
            'severity': self._calculate_severity(all_bottlenecks),
            'recommendations': self._generate_recommendations(all_bottlenecks)
        }
        
        self.detection_history.append(detection_result)
        return detection_result
    
    def _calculate_severity(self, bottlenecks: List[str]) -> str:
        """Calculate overall severity of bottlenecks"""
        if not bottlenecks:
            return "none"
        elif len(bottlenecks) == 1:
            return "low"
        elif len(bottlenecks) <= 3:
            return "medium"
        else:
            return "high"
    
    def _generate_recommendations(self, bottlenecks: List[str]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        for bottleneck in bottlenecks:
            if "CPU usage" in bottleneck:
                recommendations.append("Consider optimizing CPU-intensive operations or scaling horizontally")
            elif "memory usage" in bottleneck:
                recommendations.append("Review memory usage patterns and implement garbage collection")
            elif "disk usage" in bottleneck:
                recommendations.append("Clean up temporary files or increase disk space")
            elif "Slow operation" in bottleneck:
                recommendations.append("Profile and optimize slow operations")
            elif "error rate" in bottleneck:
                recommendations.append("Investigate and fix error-prone operations")
        
        return list(set(recommendations))  # Remove duplicates


class ResponseTimeTracker:
    """Tracks response times for various operations"""
    
    def __init__(self):
        self.stats = defaultdict(lambda: ResponseTimeStats(""))
        self.lock = threading.RLock()
    
    def track_operation(self, operation_name: str):
        """Context manager to track operation response time"""
        return OperationTracker(self, operation_name)
    
    def record_response_time(self, operation_name: str, response_time: float, success: bool = True):
        """Record a response time for an operation"""
        with self.lock:
            stats = self.stats[operation_name]
            stats.operation_name = operation_name
            stats.total_calls += 1
            stats.total_time += response_time
            stats.min_time = min(stats.min_time, response_time)
            stats.max_time = max(stats.max_time, response_time)
            stats.average_time = stats.total_time / stats.total_calls
            stats.recent_times.append(response_time)
            stats.last_updated = datetime.now()
            
            if not success:
                stats.error_count += 1
            
            # Calculate percentiles from recent times
            if len(stats.recent_times) >= 10:
                sorted_times = sorted(stats.recent_times)
                stats.p95_time = sorted_times[int(len(sorted_times) * 0.95)]
                stats.p99_time = sorted_times[int(len(sorted_times) * 0.99)]
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all response time statistics"""
        with self.lock:
            return {
                name: {
                    'total_calls': stats.total_calls,
                    'average_time': stats.average_time,
                    'min_time': stats.min_time if stats.min_time != float('inf') else 0,
                    'max_time': stats.max_time,
                    'p95_time': stats.p95_time,
                    'p99_time': stats.p99_time,
                    'error_count': stats.error_count,
                    'error_rate': stats.error_count / max(stats.total_calls, 1),
                    'last_updated': stats.last_updated.isoformat()
                }
                for name, stats in self.stats.items()
            }
    
    def reset_stats(self):
        """Reset all statistics"""
        with self.lock:
            self.stats.clear()


class OperationTracker:
    """Context manager for tracking individual operations"""
    
    def __init__(self, tracker: ResponseTimeTracker, operation_name: str):
        self.tracker = tracker
        self.operation_name = operation_name
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            response_time = time.time() - self.start_time
            self.success = exc_type is None
            self.tracker.record_response_time(
                self.operation_name, 
                response_time, 
                self.success
            )
    
    def mark_error(self):
        """Mark this operation as having an error"""
        self.success = False


class SystemResourceMonitor:
    """Monitors system resource usage"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.monitoring_active = False
        self.monitor_thread = None
        self.resource_history = deque(maxlen=1000)
        self.callbacks = []
        self.lock = threading.RLock()
    
    def start_monitoring(self):
        """Start system resource monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="system-resource-monitor"
        )
        self.monitor_thread.start()
        logger.info("System resource monitoring started")
    
    def stop_monitoring(self):
        """Stop system resource monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)
        logger.info("System resource monitoring stopped")
    
    def add_callback(self, callback: Callable[[SystemResourceStats], None]):
        """Add callback for resource updates"""
        self.callbacks.append(callback)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                stats = self._collect_resource_stats()
                
                with self.lock:
                    self.resource_history.append(stats)
                
                # Call registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        logger.error(f"Error in resource monitor callback: {e}")
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_resource_stats(self) -> SystemResourceStats:
        """Collect current system resource statistics"""
        try:
            # System-wide stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific stats
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return SystemResourceStats(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                process_memory_mb=process_memory.rss / 1024 / 1024,
                process_cpu_percent=process_cpu,
                thread_count=process.num_threads(),
                open_files=len(process.open_files()) if hasattr(process, 'open_files') else 0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error collecting resource stats: {e}")
            return SystemResourceStats()
    
    def get_current_stats(self) -> Optional[SystemResourceStats]:
        """Get current resource statistics"""
        try:
            return self._collect_resource_stats()
        except Exception as e:
            logger.error(f"Error getting current stats: {e}")
            return None
    
    def get_historical_stats(self, minutes: int = 10) -> List[SystemResourceStats]:
        """Get historical resource statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self.lock:
            return [
                stats for stats in self.resource_history
                if stats.timestamp >= cutoff_time
            ]


class SystemPerformanceMonitor:
    """Main system performance monitoring and optimization"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.resource_monitor = SystemResourceMonitor(monitoring_interval)
        self.response_tracker = ResponseTimeTracker()
        self.bottleneck_detector = PerformanceBottleneckDetector()
        self.performance_history = deque(maxlen=1000)
        self.optimization_callbacks = []
        self.lock = threading.RLock()
        
        # Register bottleneck detection callback
        self.resource_monitor.add_callback(self._check_for_bottlenecks)
    
    def start_monitoring(self):
        """Start comprehensive performance monitoring"""
        self.resource_monitor.start_monitoring()
        logger.info("System performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.resource_monitor.stop_monitoring()
        logger.info("System performance monitoring stopped")
    
    def track_operation(self, operation_name: str):
        """Track an operation's performance"""
        return self.response_tracker.track_operation(operation_name)
    
    def add_optimization_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for optimization recommendations"""
        self.optimization_callbacks.append(callback)
    
    def _check_for_bottlenecks(self, resource_stats: SystemResourceStats):
        """Check for performance bottlenecks"""
        try:
            response_stats = {
                name: ResponseTimeStats(
                    operation_name=name,
                    total_calls=stats['total_calls'],
                    average_time=stats['average_time'],
                    error_count=stats['error_count']
                )
                for name, stats in self.response_tracker.get_stats().items()
            }
            
            bottleneck_result = self.bottleneck_detector.detect_bottlenecks(
                resource_stats, response_stats
            )
            
            # Store in history
            with self.lock:
                self.performance_history.append({
                    'timestamp': datetime.now(),
                    'resource_stats': resource_stats,
                    'bottleneck_result': bottleneck_result
                })
            
            # Trigger optimization callbacks if bottlenecks detected
            if bottleneck_result['total_bottlenecks'] > 0:
                for callback in self.optimization_callbacks:
                    try:
                        callback(bottleneck_result)
                    except Exception as e:
                        logger.error(f"Error in optimization callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error checking for bottlenecks: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        current_stats = self.resource_monitor.get_current_stats()
        response_stats = self.response_tracker.get_stats()
        
        # Get recent bottlenecks
        recent_bottlenecks = []
        if self.bottleneck_detector.detection_history:
            recent_bottlenecks = list(self.bottleneck_detector.detection_history)[-5:]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_resources': {
                'cpu_percent': current_stats.cpu_percent if current_stats else 0,
                'memory_percent': current_stats.memory_percent if current_stats else 0,
                'disk_usage_percent': current_stats.disk_usage_percent if current_stats else 0,
                'process_memory_mb': current_stats.process_memory_mb if current_stats else 0,
                'thread_count': current_stats.thread_count if current_stats else 0
            },
            'response_times': response_stats,
            'recent_bottlenecks': [
                {
                    'timestamp': result['timestamp'].isoformat(),
                    'severity': result['severity'],
                    'total_bottlenecks': result['total_bottlenecks'],
                    'recommendations': result['recommendations']
                }
                for result in recent_bottlenecks
            ],
            'performance_trends': self._calculate_performance_trends()
        }
    
    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        if len(self.performance_history) < 2:
            return {}
        
        recent_history = list(self.performance_history)[-10:]  # Last 10 measurements
        
        # Calculate trends
        cpu_trend = self._calculate_trend([
            h['resource_stats'].cpu_percent for h in recent_history
        ])
        memory_trend = self._calculate_trend([
            h['resource_stats'].memory_percent for h in recent_history
        ])
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'bottleneck_frequency': len([
                h for h in recent_history 
                if h['bottleneck_result']['total_bottlenecks'] > 0
            ]) / len(recent_history)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = (second_half - first_half) / max(first_half, 0.1) * 100
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def optimize_system_performance(self):
        """Run system performance optimizations"""
        try:
            logger.info("Running system performance optimizations...")
            
            # Force garbage collection
            gc.collect()
            
            # Get current stats for analysis
            current_stats = self.resource_monitor.get_current_stats()
            if not current_stats:
                return
            
            optimizations_applied = []
            
            # Memory optimization
            if current_stats.process_memory_mb > 200:  # 200MB threshold
                gc.collect()
                optimizations_applied.append("garbage_collection")
            
            # Thread optimization (placeholder for actual thread pool optimization)
            if current_stats.thread_count > 50:
                optimizations_applied.append("thread_pool_optimization")
            
            logger.info(f"Applied optimizations: {optimizations_applied}")
            
        except Exception as e:
            logger.error(f"Error during system optimization: {e}")
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        summary = self.get_performance_summary()
        
        report = []
        report.append("=== System Performance Report ===")
        report.append(f"Generated: {summary['timestamp']}")
        report.append("")
        
        # System resources
        resources = summary['system_resources']
        report.append("System Resources:")
        report.append(f"  CPU Usage: {resources['cpu_percent']:.1f}%")
        report.append(f"  Memory Usage: {resources['memory_percent']:.1f}%")
        report.append(f"  Disk Usage: {resources['disk_usage_percent']:.1f}%")
        report.append(f"  Process Memory: {resources['process_memory_mb']:.1f}MB")
        report.append(f"  Thread Count: {resources['thread_count']}")
        report.append("")
        
        # Response times
        if summary['response_times']:
            report.append("Operation Response Times:")
            for op_name, stats in summary['response_times'].items():
                report.append(f"  {op_name}:")
                report.append(f"    Calls: {stats['total_calls']}")
                report.append(f"    Avg Time: {stats['average_time']:.3f}s")
                report.append(f"    Error Rate: {stats['error_rate']:.1%}")
            report.append("")
        
        # Recent bottlenecks
        if summary['recent_bottlenecks']:
            report.append("Recent Bottlenecks:")
            for bottleneck in summary['recent_bottlenecks'][-3:]:  # Last 3
                report.append(f"  {bottleneck['timestamp']} - Severity: {bottleneck['severity']}")
                for rec in bottleneck['recommendations']:
                    report.append(f"    • {rec}")
            report.append("")
        
        # Performance trends
        trends = summary['performance_trends']
        if trends:
            report.append("Performance Trends:")
            report.append(f"  CPU Trend: {trends.get('cpu_trend', 'unknown')}")
            report.append(f"  Memory Trend: {trends.get('memory_trend', 'unknown')}")
            report.append(f"  Bottleneck Frequency: {trends.get('bottleneck_frequency', 0):.1%}")
        
        return "\n".join(report)
    
    def reset_statistics(self):
        """Reset all performance statistics"""
        self.response_tracker.reset_stats()
        with self.lock:
            self.performance_history.clear()
        self.bottleneck_detector.detection_history.clear()
        logger.info("Performance statistics reset")
    
    def shutdown(self):
        """Shutdown the performance monitor"""
        self.stop_monitoring()
        logger.info("System performance monitor shutdown complete")