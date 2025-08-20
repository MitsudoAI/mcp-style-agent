"""
Template Performance Optimizer

Implements template preloading, caching strategies, memory monitoring,
and performance optimization for the template management system.
"""

import gc
import logging
import os
import psutil
import threading
import time
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class TemplateUsageStats:
    """Template usage statistics for optimization"""

    name: str
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    total_access_time: float = 0.0
    average_access_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_size: int = 0
    priority_score: float = 0.0


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    memory_usage: int = 0
    evictions: int = 0
    preload_time: float = 0.0


class LRUCache:
    """Least Recently Used cache with size limits"""

    def __init__(self, max_size: int = 100, max_memory_mb: int = 50):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.memory_usage = 0
        self.access_times = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[str]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.access_times[key] = datetime.now()
                return value
            return None

    def put(self, key: str, value: str) -> bool:
        """Put item in cache with eviction if needed"""
        with self.lock:
            value_size = len(value.encode("utf-8"))

            # Check if we need to evict items
            while (
                len(self.cache) >= self.max_size
                or self.memory_usage + value_size > self.max_memory_bytes
            ):
                if not self.cache:
                    break
                self._evict_lru()

            # Add new item
            if key in self.cache:
                # Update existing
                old_value = self.cache.pop(key)
                old_size = len(old_value.encode("utf-8"))
                self.memory_usage -= old_size

            self.cache[key] = value
            self.memory_usage += value_size
            self.access_times[key] = datetime.now()
            return True

    def _evict_lru(self) -> Optional[str]:
        """Evict least recently used item"""
        if not self.cache:
            return None

        # Remove oldest item
        key, value = self.cache.popitem(last=False)
        value_size = len(value.encode("utf-8"))
        self.memory_usage -= value_size
        self.access_times.pop(key, None)
        return key

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.memory_usage = 0

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def memory_size(self) -> int:
        """Get current memory usage in bytes"""
        return self.memory_usage


class TemplatePreloader:
    """Template preloading system for performance optimization"""

    def __init__(self, templates_dir: Path, cache: LRUCache):
        self.templates_dir = templates_dir
        self.cache = cache
        self.preload_stats = {}
        self.preload_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="template-preload"
        )
        self.lock = threading.RLock()

    def preload_templates(
        self, template_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Preload templates into cache

        Args:
            template_names: Specific templates to preload, or None for all

        Returns:
            Dict mapping template names to success status
        """
        start_time = time.time()
        results = {}

        try:
            # Get list of templates to preload
            if template_names is None:
                template_names = self._discover_templates()

            logger.info(f"Preloading {len(template_names)} templates...")

            # Submit preload tasks
            future_to_name = {}
            for name in template_names:
                future = self.preload_executor.submit(
                    self._preload_single_template, name
                )
                future_to_name[future] = name

            # Collect results
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    success = future.result(
                        timeout=10.0
                    )  # 10 second timeout per template
                    results[name] = success
                    if success:
                        logger.debug(f"Successfully preloaded template: {name}")
                    else:
                        logger.warning(f"Failed to preload template: {name}")
                except Exception as e:
                    logger.error(f"Error preloading template {name}: {e}")
                    results[name] = False

            preload_time = time.time() - start_time
            success_count = sum(1 for success in results.values() if success)

            logger.info(
                f"Preloaded {success_count}/{len(template_names)} templates in {preload_time:.2f}s"
            )

            # Update preload stats
            with self.lock:
                self.preload_stats = {
                    "last_preload_time": datetime.now(),
                    "preload_duration": preload_time,
                    "templates_attempted": len(template_names),
                    "templates_successful": success_count,
                    "success_rate": (
                        success_count / len(template_names) if template_names else 0.0
                    ),
                }

            return results

        except Exception as e:
            logger.error(f"Error during template preloading: {e}")
            return {}

    def _discover_templates(self) -> List[str]:
        """Discover all available template files"""
        template_names = []

        if not self.templates_dir.exists():
            return template_names

        for template_file in self.templates_dir.glob("*.tmpl"):
            template_names.append(template_file.stem)

        return template_names

    def _preload_single_template(self, name: str) -> bool:
        """Preload a single template"""
        try:
            template_path = self.templates_dir / f"{name}.tmpl"

            if not template_path.exists():
                return False

            # Read template content
            content = template_path.read_text(encoding="utf-8")

            # Add to cache
            success = self.cache.put(name, content)

            return success

        except Exception as e:
            logger.error(f"Error preloading template {name}: {e}")
            return False

    def get_preload_stats(self) -> Dict[str, Any]:
        """Get preloading statistics"""
        with self.lock:
            return self.preload_stats.copy()


class MemoryMonitor:
    """Memory usage monitoring and cleanup for template system"""

    def __init__(
        self, warning_threshold_mb: int = 100, critical_threshold_mb: int = 200
    ):
        self.warning_threshold = warning_threshold_mb * 1024 * 1024
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        self.monitoring_active = False
        self.monitor_thread = None
        self.cleanup_callbacks = []
        self.memory_stats = {
            "peak_usage": 0,
            "current_usage": 0,
            "cleanup_count": 0,
            "last_cleanup": None,
        }
        self.lock = threading.RLock()

    def start_monitoring(self, check_interval: float = 30.0):
        """Start memory monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True,
            name="memory-monitor",
        )
        self.monitor_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        logger.info("Memory monitoring stopped")

    def add_cleanup_callback(self, callback):
        """Add a cleanup callback function"""
        self.cleanup_callbacks.append(callback)

    def _monitor_loop(self, check_interval: float):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                current_usage = self._get_memory_usage()

                with self.lock:
                    self.memory_stats["current_usage"] = current_usage
                    if current_usage > self.memory_stats["peak_usage"]:
                        self.memory_stats["peak_usage"] = current_usage

                # Check thresholds
                if current_usage > self.critical_threshold:
                    logger.warning(
                        f"Critical memory usage: {current_usage / 1024 / 1024:.1f}MB"
                    )
                    self._trigger_cleanup(aggressive=True)
                elif current_usage > self.warning_threshold:
                    logger.info(
                        f"High memory usage: {current_usage / 1024 / 1024:.1f}MB"
                    )
                    self._trigger_cleanup(aggressive=False)

                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"Error in memory monitoring: {e}")
                time.sleep(check_interval)

    def _get_memory_usage(self) -> int:
        """Get current process memory usage in bytes"""
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            # Fallback to basic memory info
            return 0

    def _trigger_cleanup(self, aggressive: bool = False):
        """Trigger memory cleanup"""
        try:
            logger.info(
                f"Triggering {'aggressive' if aggressive else 'normal'} memory cleanup"
            )

            # Call registered cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback(aggressive)
                except Exception as e:
                    logger.error(f"Error in cleanup callback: {e}")

            # Force garbage collection
            if aggressive:
                gc.collect()

            with self.lock:
                self.memory_stats["cleanup_count"] += 1
                self.memory_stats["last_cleanup"] = datetime.now()

        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory monitoring statistics"""
        with self.lock:
            stats = self.memory_stats.copy()
            stats["current_usage_mb"] = stats["current_usage"] / 1024 / 1024
            stats["peak_usage_mb"] = stats["peak_usage"] / 1024 / 1024
            stats["warning_threshold_mb"] = self.warning_threshold / 1024 / 1024
            stats["critical_threshold_mb"] = self.critical_threshold / 1024 / 1024
            return stats


class TemplatePerformanceOptimizer:
    """Main performance optimizer for template system"""

    def __init__(
        self, templates_dir: Path, cache_size: int = 100, cache_memory_mb: int = 50
    ):
        self.templates_dir = templates_dir
        self.cache = LRUCache(max_size=cache_size, max_memory_mb=cache_memory_mb)
        self.preloader = TemplatePreloader(templates_dir, self.cache)
        self.memory_monitor = MemoryMonitor()
        self.usage_stats = defaultdict(lambda: TemplateUsageStats(""))
        self.metrics = CacheMetrics()
        self.lock = threading.RLock()

        # Register cleanup callback
        self.memory_monitor.add_cleanup_callback(self._memory_cleanup_callback)

        # Start memory monitoring
        self.memory_monitor.start_monitoring()

    def get_template(self, name: str, load_func) -> Optional[str]:
        """
        Get template with performance optimization

        Args:
            name: Template name
            load_func: Function to load template if not in cache

        Returns:
            Template content or None
        """
        start_time = time.time()

        try:
            with self.lock:
                self.metrics.total_requests += 1

                # Try cache first
                content = self.cache.get(name)
                if content is not None:
                    self.metrics.cache_hits += 1
                    self._update_usage_stats(
                        name, time.time() - start_time, cache_hit=True
                    )
                    return content

                # Cache miss - load template
                self.metrics.cache_misses += 1
                content = load_func(name)

                if content is not None:
                    # Add to cache
                    self.cache.put(name, content)
                    self._update_usage_stats(
                        name, time.time() - start_time, cache_hit=False
                    )
                    return content

                return None

        except Exception as e:
            logger.error(f"Error getting template {name}: {e}")
            return None
        finally:
            # Update hit rate
            if self.metrics.total_requests > 0:
                self.metrics.hit_rate = (
                    self.metrics.cache_hits / self.metrics.total_requests
                )

    def _update_usage_stats(self, name: str, access_time: float, cache_hit: bool):
        """Update usage statistics for a template"""
        stats = self.usage_stats[name]
        stats.name = name
        stats.access_count += 1
        stats.last_accessed = datetime.now()
        stats.total_access_time += access_time
        stats.average_access_time = stats.total_access_time / stats.access_count

        if cache_hit:
            stats.cache_hits += 1
        else:
            stats.cache_misses += 1

        # Calculate priority score (higher = more important to keep in cache)
        stats.priority_score = self._calculate_priority_score(stats)

    def _calculate_priority_score(self, stats: TemplateUsageStats) -> float:
        """Calculate priority score for template caching"""
        # Factors: access frequency, recency, cache hit rate
        frequency_score = min(stats.access_count / 100.0, 1.0)  # Normalize to 0-1

        recency_score = 0.0
        if stats.last_accessed:
            hours_since_access = (
                datetime.now() - stats.last_accessed
            ).total_seconds() / 3600
            recency_score = max(
                0.0, 1.0 - (hours_since_access / 24.0)
            )  # Decay over 24 hours

        hit_rate = stats.cache_hits / max(stats.access_count, 1)

        # Weighted combination
        priority = frequency_score * 0.4 + recency_score * 0.4 + hit_rate * 0.2
        return priority

    def preload_high_priority_templates(
        self, max_templates: int = 20
    ) -> Dict[str, bool]:
        """Preload high-priority templates based on usage statistics"""
        # Get top templates by priority
        sorted_stats = sorted(
            self.usage_stats.values(), key=lambda s: s.priority_score, reverse=True
        )

        high_priority_names = [stats.name for stats in sorted_stats[:max_templates]]

        if not high_priority_names:
            # If no usage stats, preload common templates
            high_priority_names = [
                "decomposition",
                "evidence_collection",
                "critical_evaluation",
                "bias_detection",
                "innovation",
                "reflection",
            ]

        return self.preloader.preload_templates(high_priority_names)

    def optimize_cache(self):
        """Optimize cache based on usage patterns"""
        try:
            with self.lock:
                # Get current cache contents
                cached_templates = list(self.cache.cache.keys())

                # Calculate which templates should be evicted
                templates_to_evict = []
                for template_name in cached_templates:
                    stats = self.usage_stats.get(template_name)
                    if stats and stats.priority_score < 0.1:  # Low priority threshold
                        templates_to_evict.append(template_name)

                # Evict low-priority templates
                for template_name in templates_to_evict:
                    if template_name in self.cache.cache:
                        del self.cache.cache[template_name]
                        logger.debug(f"Evicted low-priority template: {template_name}")

                logger.info(
                    f"Cache optimization complete. Evicted {len(templates_to_evict)} templates"
                )

        except Exception as e:
            logger.error(f"Error optimizing cache: {e}")

    def _memory_cleanup_callback(self, aggressive: bool):
        """Callback for memory cleanup"""
        try:
            if aggressive:
                # Clear half the cache, keeping highest priority items
                current_size = self.cache.size()
                target_size = current_size // 2

                # Get templates sorted by priority
                cached_templates = list(self.cache.cache.keys())
                template_priorities = [
                    (
                        name,
                        self.usage_stats.get(
                            name, TemplateUsageStats(name)
                        ).priority_score,
                    )
                    for name in cached_templates
                ]
                template_priorities.sort(
                    key=lambda x: x[1]
                )  # Sort by priority (ascending)

                # Remove lowest priority templates
                templates_to_remove = template_priorities[: current_size - target_size]
                for template_name, _ in templates_to_remove:
                    if template_name in self.cache.cache:
                        del self.cache.cache[template_name]

                logger.info(
                    f"Aggressive cleanup: removed {len(templates_to_remove)} templates from cache"
                )
            else:
                # Normal cleanup - just optimize cache
                self.optimize_cache()

        except Exception as e:
            logger.error(f"Error in memory cleanup callback: {e}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        with self.lock:
            metrics = {
                "cache_metrics": {
                    "total_requests": self.metrics.total_requests,
                    "cache_hits": self.metrics.cache_hits,
                    "cache_misses": self.metrics.cache_misses,
                    "hit_rate": self.metrics.hit_rate,
                    "cache_size": self.cache.size(),
                    "cache_memory_usage": self.cache.memory_size(),
                    "cache_memory_usage_mb": self.cache.memory_size() / 1024 / 1024,
                },
                "usage_stats": {
                    name: {
                        "access_count": stats.access_count,
                        "last_accessed": (
                            stats.last_accessed.isoformat()
                            if stats.last_accessed
                            else None
                        ),
                        "average_access_time": stats.average_access_time,
                        "cache_hits": stats.cache_hits,
                        "cache_misses": stats.cache_misses,
                        "priority_score": stats.priority_score,
                    }
                    for name, stats in self.usage_stats.items()
                },
                "memory_stats": self.memory_monitor.get_memory_stats(),
                "preload_stats": self.preloader.get_preload_stats(),
            }

            return metrics

    def reset_statistics(self):
        """Reset all performance statistics"""
        with self.lock:
            self.usage_stats.clear()
            self.metrics = CacheMetrics()
            logger.info("Performance statistics reset")

    def shutdown(self):
        """Shutdown the performance optimizer"""
        try:
            self.memory_monitor.stop_monitoring()
            self.preloader.preload_executor.shutdown(wait=True)
            logger.info("Performance optimizer shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
