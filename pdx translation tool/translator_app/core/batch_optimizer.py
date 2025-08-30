"""
Intelligent batch processing and optimization system
"""

import time
from typing import List, Dict, Optional, Any
from collections import deque


class AdaptiveBatcher:
    """Intelligent batching system that adapts to API provider capabilities and performance"""
    
    def __init__(self):
        self.performance_history = {}
        self.optimal_batch_sizes = {}
        self.api_error_rates = {}
    
    def get_optimal_batch_size(self, api_provider: str, model: str, 
                              current_performance: Optional[Dict] = None) -> int:
        """Get optimal batch size based on historical performance"""
        key = f"{api_provider}_{model}"
        
        if current_performance:
            self._update_performance_history(key, current_performance)
        
        # Start with provider defaults
        default_sizes = {
            'gemini_flash': 50,
            'gemini_pro': 20,
            'claude_sonnet': 40,
            'claude_haiku': 45,
            'claude_opus': 15,
            'openai_gpt-4': 25,
            'openai_gpt-4-turbo': 35,
            'openai_gpt-3.5-turbo': 45
        }
        
        base_size = default_sizes.get(key, 30)
        
        # Adjust based on historical performance
        if key in self.performance_history:
            history = self.performance_history[key]
            avg_response_time = sum(h['response_time'] for h in history[-10:]) / min(len(history), 10)
            error_rate = sum(1 for h in history[-20:] if h.get('error', False)) / min(len(history), 20)
            
            # Decrease batch size if high error rate or slow response
            if error_rate > 0.1:  # More than 10% errors
                base_size = max(base_size - 10, 5)
            elif error_rate > 0.05:  # More than 5% errors
                base_size = max(base_size - 5, 10)
            
            if avg_response_time > 30:  # Slow responses
                base_size = max(base_size - 5, 10)
            elif avg_response_time < 10:  # Fast responses
                base_size = min(base_size + 5, 60)
        
        self.optimal_batch_sizes[key] = base_size
        return base_size
    
    def _update_performance_history(self, key: str, performance: Dict):
        """Update performance history for an API provider/model"""
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        # Keep only recent history (last 50 entries)
        self.performance_history[key].append(performance)
        if len(self.performance_history[key]) > 50:
            self.performance_history[key] = self.performance_history[key][-50:]
    
    def create_batches(self, texts: List[str], api_provider: str, model: str) -> List[List[str]]:
        """Create optimized batches for translation"""
        batch_size = self.get_optimal_batch_size(api_provider, model)
        
        batches = []
        for i in range(0, len(texts), batch_size):
            batches.append(texts[i:i + batch_size])
        
        return batches


class DynamicBatchOptimizer:
    """Dynamic batch size optimization based on current system load and performance"""
    
    def __init__(self, initial_batch_size: int = 30, max_concurrent: int = 100):
        self.initial_batch_size = initial_batch_size
        self.max_concurrent = max_concurrent
        self.current_active_requests = 0
        self.total_requests_capacity = max_concurrent
        
        # Performance tracking
        self.request_completion_times = deque(maxlen=50)
        self.batch_performance_history = deque(maxlen=20)
        
        # Dynamic sizing parameters
        self.min_batch_size = 10
        self.max_batch_size = 150
        self.scaling_factor = 1.5
    
    def calculate_optimal_batch_size(self, remaining_items: int, available_capacity: int) -> int:
        """
        Calculate optimal batch size based on current system state
        
        Args:
            remaining_items: Number of items left to process
            available_capacity: Available concurrent request slots
            
        Returns:
            Optimal batch size for current conditions
        """
        # Base batch size on available capacity
        if available_capacity >= self.total_requests_capacity * 0.8:  # 80% capacity available
            # High capacity available - use larger batches for efficiency
            optimal_size = min(
                int(self.initial_batch_size * self.scaling_factor), 
                self.max_batch_size,
                remaining_items // max(1, available_capacity // 2)  # Distribute evenly
            )
        elif available_capacity >= self.total_requests_capacity * 0.5:  # 50% capacity available
            # Medium capacity - use standard batch sizes
            optimal_size = self.initial_batch_size
        else:
            # Low capacity - use smaller batches for responsiveness
            optimal_size = max(
                self.min_batch_size,
                int(self.initial_batch_size * 0.7)
            )
        
        # Adjust based on recent performance
        if len(self.batch_performance_history) >= 3:
            recent_avg_time = sum(self.batch_performance_history[-3:]) / 3
            if recent_avg_time > 30:  # Slow batches
                optimal_size = max(self.min_batch_size, int(optimal_size * 0.8))
            elif recent_avg_time < 10:  # Fast batches
                optimal_size = min(self.max_batch_size, int(optimal_size * 1.2))
        
        return max(self.min_batch_size, min(self.max_batch_size, optimal_size))
    
    def create_dynamic_batches(self, items: List[str], available_capacity: int) -> List[List[str]]:
        """
        Create batches with dynamic sizing based on current capacity
        
        Args:
            items: List of items to batch
            available_capacity: Currently available concurrent slots
            
        Returns:
            List of batches optimized for current system state
        """
        if not items:
            return []
        
        batches = []
        remaining_items = len(items)
        start_idx = 0
        
        while start_idx < len(items):
            # Recalculate optimal batch size for remaining items
            batch_size = self.calculate_optimal_batch_size(remaining_items, available_capacity)
            end_idx = min(start_idx + batch_size, len(items))
            
            batch = items[start_idx:end_idx]
            batches.append(batch)
            
            start_idx = end_idx
            remaining_items = len(items) - start_idx
        
        return batches
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the batch optimizer"""
        return {
            'current_active_requests': self.current_active_requests,
            'total_requests_capacity': self.total_requests_capacity,
            'recent_batches_count': len(self.batch_performance_history),
            'average_batch_size': sum(b.get('batch_size', 0) for b in self.batch_performance_history) / max(1, len(self.batch_performance_history)),
            'min_batch_size': self.min_batch_size,
            'max_batch_size': self.max_batch_size,
            'initial_batch_size': self.initial_batch_size
        }