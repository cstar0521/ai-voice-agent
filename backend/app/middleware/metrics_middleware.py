"""
Middleware for automatic metrics collection on API requests.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.metrics_collector import get_metrics_collector, MetricCategory

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect API request metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Normalize path for metrics (remove IDs)
        normalized_path = self._normalize_path(path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Collect metrics
            try:
                metrics_collector = await get_metrics_collector()
                
                await metrics_collector.track_api_request(
                    endpoint=normalized_path,
                    method=method,
                    status_code=response.status_code,
                    duration=duration
                )
                
                # Add metrics headers to response
                response.headers["X-Response-Time"] = f"{duration:.3f}s"
                
            except Exception as e:
                logger.error(f"Error collecting API metrics: {e}")
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time
            
            # Collect error metrics
            try:
                metrics_collector = await get_metrics_collector()
                
                await metrics_collector.track_api_request(
                    endpoint=normalized_path,
                    method=method,
                    status_code=500,  # Assume 500 for unhandled exceptions
                    duration=duration
                )
                
            except Exception as metrics_error:
                logger.error(f"Error collecting error metrics: {metrics_error}")
            
            # Re-raise the original exception
            raise e
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize API path for metrics by replacing IDs with placeholders.
        
        Examples:
        /api/v1/calls/call_123 -> /api/v1/calls/{call_id}
        /api/v1/leads/lead_456/handoff -> /api/v1/leads/{lead_id}/handoff
        """
        # Split path into segments
        segments = path.split('/')
        normalized_segments = []
        
        for i, segment in enumerate(segments):
            if not segment:  # Empty segment (leading slash)
                normalized_segments.append(segment)
                continue
            
            # Check if segment looks like an ID
            if self._is_id_segment(segment, i, segments):
                # Replace with placeholder based on context
                placeholder = self._get_placeholder(segment, i, segments)
                normalized_segments.append(placeholder)
            else:
                normalized_segments.append(segment)
        
        return '/'.join(normalized_segments)
    
    def _is_id_segment(self, segment: str, index: int, segments: List[str]) -> bool:
        """Check if a segment looks like an ID."""
        # Common ID patterns
        id_patterns = [
            lambda s: s.startswith('call_'),
            lambda s: s.startswith('lead_'),
            lambda s: s.startswith('conv_'),
            lambda s: s.startswith('user_'),
            lambda s: s.startswith('test_'),
            lambda s: len(s) > 10 and ('_' in s or '-' in s),  # Long IDs with separators
            lambda s: s.isdigit() and len(s) > 3,  # Numeric IDs
            lambda s: len(s) == 36 and s.count('-') == 4,  # UUIDs
        ]
        
        return any(pattern(segment) for pattern in id_patterns)
    
    def _get_placeholder(self, segment: str, index: int, segments: List[str]) -> str:
        """Get appropriate placeholder for an ID segment."""
        # Look at previous segment for context
        if index > 0:
            prev_segment = segments[index - 1].lower()
            
            if prev_segment == 'calls':
                return '{call_id}'
            elif prev_segment == 'leads':
                return '{lead_id}'
            elif prev_segment == 'conversations':
                return '{conversation_id}'
            elif prev_segment == 'users':
                return '{user_id}'
            elif prev_segment == 'versions':
                return '{version_id}'
            elif prev_segment == 'ab-tests':
                return '{test_id}'
        
        # Check segment prefix
        if segment.startswith('call_'):
            return '{call_id}'
        elif segment.startswith('lead_'):
            return '{lead_id}'
        elif segment.startswith('conv_'):
            return '{conversation_id}'
        elif segment.startswith('user_'):
            return '{user_id}'
        elif segment.startswith('test_'):
            return '{test_id}'
        
        # Generic placeholder
        return '{id}'


# System metrics collection
class SystemMetricsCollector:
    """Collector for system-level metrics."""
    
    def __init__(self):
        self._running = False
        self._collection_task = None
    
    async def start(self):
        """Start system metrics collection."""
        self._running = True
        self._collection_task = asyncio.create_task(self._collect_system_metrics())
        logger.info("System metrics collection started")
    
    async def stop(self):
        """Stop system metrics collection."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("System metrics collection stopped")
    
    async def _collect_system_metrics(self):
        """Periodic collection of system metrics."""
        import asyncio
        import psutil
        import socket
        
        hostname = socket.gethostname()
        
        while self._running:
            try:
                metrics_collector = await get_metrics_collector()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                await metrics_collector.track_system_resource(
                    "cpu", cpu_percent, hostname
                )
                
                # Memory usage
                memory = psutil.virtual_memory()
                await metrics_collector.track_system_resource(
                    "memory", memory.percent, hostname
                )
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                await metrics_collector.track_system_resource(
                    "disk", disk_percent, hostname
                )
                
                # Network I/O
                network = psutil.net_io_counters()
                await metrics_collector.set_gauge(
                    "network_bytes_sent",
                    MetricCategory.SYSTEM,
                    float(network.bytes_sent),
                    {"host": hostname}
                )
                await metrics_collector.set_gauge(
                    "network_bytes_recv",
                    MetricCategory.SYSTEM,
                    float(network.bytes_recv),
                    {"host": hostname}
                )
                
                # Process count
                process_count = len(psutil.pids())
                await metrics_collector.set_gauge(
                    "process_count",
                    MetricCategory.SYSTEM,
                    float(process_count),
                    {"host": hostname}
                )
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)


# Global system metrics collector instance
_system_metrics_collector = None


async def start_system_metrics_collection():
    """Start system metrics collection."""
    global _system_metrics_collector
    if _system_metrics_collector is None:
        _system_metrics_collector = SystemMetricsCollector()
        await _system_metrics_collector.start()


async def stop_system_metrics_collection():
    """Stop system metrics collection."""
    global _system_metrics_collector
    if _system_metrics_collector:
        await _system_metrics_collector.stop()
        _system_metrics_collector = None