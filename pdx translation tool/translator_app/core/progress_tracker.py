"""
Progress tracking and monitoring module
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Callable, Any
from collections import deque


class ProgressTracker:
    """Enhanced progress tracking with detailed statistics"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.translation_lock = threading.Lock()
        
        # Progress tracking
        self.progress_tracker = {
            'stage': 'idle',
            'overall_progress': 0.0,
            'current_file': '',
            'current_file_progress': 0.0,
            'files_completed': 0,
            'total_files': 0,
            'total_lines': 0,
            'lines_processed': 0,
            'start_time': None,
            'current_file_start_time': None,
            'files_tracker': {},
            'batch_progress': {'current': 0, 'total': 0},
            'performance_history': deque(maxlen=50)
        }
    
    def initialize_progress_tracking(self, total_files: int, total_lines: int = None) -> None:
        """Initialize progress tracking for a new translation session"""
        with self.translation_lock:
            self.progress_tracker.update({
                'stage': 'starting',
                'overall_progress': 0.0,
                'current_file': '',
                'current_file_progress': 0.0,
                'files_completed': 0,
                'total_files': total_files,
                'total_lines': total_lines or 0,
                'lines_processed': 0,
                'start_time': time.time(),
                'current_file_start_time': None,
                'files_tracker': {},
                'batch_progress': {'current': 0, 'total': 0},
                'performance_history': deque(maxlen=50)
            })
    
    def update_file_progress(self, file_name: str, progress: float, stage: str = 'translating',
                           lines_processed: int = 0, total_lines: int = 0) -> None:
        """Update progress for a specific file"""
        with self.translation_lock:
            # Update current file progress
            self.progress_tracker['current_file'] = file_name
            self.progress_tracker['current_file_progress'] = progress
            self.progress_tracker['stage'] = stage
            
            # Update file tracker
            if file_name not in self.progress_tracker['files_tracker']:
                self.progress_tracker['files_tracker'][file_name] = {
                    'progress': 0.0,
                    'stage': 'pending',
                    'start_time': time.time(),
                    'lines_processed': 0,
                    'total_lines': total_lines,
                    'errors': 0
                }
            
            file_tracker = self.progress_tracker['files_tracker'][file_name]
            file_tracker.update({
                'progress': progress,
                'stage': stage,
                'lines_processed': lines_processed
            })
            
            if stage == 'translating' and file_tracker.get('start_time') is None:
                file_tracker['start_time'] = time.time()
                self.progress_tracker['current_file_start_time'] = time.time()
            
            # Update overall progress
            total_files = self.progress_tracker['total_files']
            if total_files > 0:
                completed_files = sum(1 for f in self.progress_tracker['files_tracker'].values() 
                                    if f['stage'] == 'completed')
                files_in_progress = sum(f['progress'] / 100.0 for f in self.progress_tracker['files_tracker'].values() 
                                      if f['stage'] != 'completed')
                
                self.progress_tracker['overall_progress'] = min(100.0, 
                    ((completed_files + files_in_progress) / total_files) * 100.0)
                self.progress_tracker['files_completed'] = completed_files
                self.progress_tracker['lines_processed'] += lines_processed
        
        # Call progress callback
        if self.progress_callback:
            self._call_progress_callback()
    
    def update_batch_progress(self, current_batch: int, total_batches: int) -> None:
        """Update batch processing progress"""
        with self.translation_lock:
            self.progress_tracker['batch_progress'] = {
                'current': current_batch,
                'total': total_batches
            }
        
        if self.progress_callback:
            self._call_progress_callback()
    
    def complete_file_progress(self, file_name: str, lines_processed: int = None) -> None:
        """Mark file as completed"""
        with self.translation_lock:
            if file_name in self.progress_tracker['files_tracker']:
                file_tracker = self.progress_tracker['files_tracker'][file_name]
                file_tracker.update({
                    'progress': 100.0,
                    'stage': 'completed',
                    'end_time': time.time()
                })
                
                if lines_processed is not None:
                    file_tracker['lines_processed'] = lines_processed
                
                # Record performance data
                if 'start_time' in file_tracker and file_tracker['start_time']:
                    processing_time = time.time() - file_tracker['start_time']
                    self.progress_tracker['performance_history'].append({
                        'file_name': file_name,
                        'processing_time': processing_time,
                        'lines_processed': file_tracker.get('lines_processed', 0),
                        'timestamp': time.time()
                    })
                
                # Update overall counters
                self.progress_tracker['files_completed'] = sum(
                    1 for f in self.progress_tracker['files_tracker'].values() 
                    if f['stage'] == 'completed'
                )
                
                # Calculate overall progress
                total_files = self.progress_tracker['total_files']
                if total_files > 0:
                    self.progress_tracker['overall_progress'] = min(100.0,
                        (self.progress_tracker['files_completed'] / total_files) * 100.0)
        
        if self.progress_callback:
            self._call_progress_callback()
    
    def get_comprehensive_progress(self) -> Dict[str, Any]:
        """Get detailed progress information"""
        with self.translation_lock:
            tracker = self.progress_tracker.copy()
            
            # Calculate ETA
            eta = self._calculate_accurate_eta(tracker)
            eta_confidence = self._calculate_eta_confidence(tracker)
            
            # Generate status message
            overall_progress = tracker['overall_progress']
            status_message = self._generate_status_message(tracker, overall_progress)
            
            return {
                'overall_progress': overall_progress,
                'current_file': tracker['current_file'],
                'current_file_progress': tracker['current_file_progress'],
                'files_completed': tracker['files_completed'],
                'total_files': tracker['total_files'],
                'stage': tracker['stage'],
                'eta_seconds': eta,
                'eta_confidence': eta_confidence,
                'status_message': status_message,
                'batch_progress': tracker['batch_progress'],
                'performance_stats': self._get_performance_stats(),
                'files_tracker': tracker['files_tracker']
            }
    
    def _calculate_accurate_eta(self, tracker: Dict) -> float:
        """Calculate ETA with enhanced accuracy"""
        if not tracker.get('start_time') or tracker['files_completed'] == 0:
            return 0.0
        
        current_time = time.time()
        elapsed_time = current_time - tracker['start_time']
        
        # Use recent performance history for better ETA
        if len(tracker['performance_history']) >= 3:
            recent_history = list(tracker['performance_history'])[-10:]
            avg_time_per_file = sum(h['processing_time'] for h in recent_history) / len(recent_history)
            
            remaining_files = tracker['total_files'] - tracker['files_completed']
            eta = remaining_files * avg_time_per_file
            
            # Add current file remaining time
            if tracker['current_file_progress'] > 0:
                current_file_eta = (avg_time_per_file * 
                                  (100 - tracker['current_file_progress']) / 100.0)
                eta += current_file_eta
                
            return max(0.0, eta)
        
        # Fallback to simple calculation
        if tracker['overall_progress'] > 0:
            total_estimated_time = elapsed_time * (100.0 / tracker['overall_progress'])
            return max(0.0, total_estimated_time - elapsed_time)
            
        return 0.0
    
    def _calculate_eta_confidence(self, tracker: Dict) -> float:
        """Calculate confidence level for ETA prediction"""
        if len(tracker['performance_history']) < 3:
            return 0.3
        
        # Base confidence on data points and consistency
        data_points = len(tracker['performance_history'])
        base_confidence = min(0.9, data_points / 20.0)  # Max confidence at 20+ files
        
        # Adjust for performance consistency
        recent_times = [h['processing_time'] for h in tracker['performance_history'][-10:]]
        if len(recent_times) >= 3:
            avg_time = sum(recent_times) / len(recent_times)
            variance = sum((t - avg_time) ** 2 for t in recent_times) / len(recent_times)
            consistency_factor = max(0.5, 1.0 - (variance / (avg_time ** 2)))
            base_confidence *= consistency_factor
        
        return min(0.95, base_confidence)
    
    def _generate_status_message(self, tracker: Dict, overall_progress: float) -> str:
        """Generate human-readable status message"""
        stage = tracker['stage']
        current_file = tracker['current_file']
        files_completed = tracker['files_completed']
        total_files = tracker['total_files']
        
        if stage == 'completed':
            return f"번역 완료! {files_completed}개 파일 처리됨"
        elif stage == 'translating' and current_file:
            return f"번역 중: {current_file} ({files_completed + 1}/{total_files})"
        elif stage == 'starting':
            return f"번역 시작 중... ({total_files}개 파일 발견)"
        else:
            return f"진행률: {overall_progress:.1f}%"
    
    def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.translation_lock:
            if not self.progress_tracker['performance_history']:
                return {}
            
            processing_times = [h['processing_time'] for h in self.progress_tracker['performance_history']]
            lines_per_file = [h['lines_processed'] for h in self.progress_tracker['performance_history'] 
                             if h['lines_processed'] > 0]
            
            stats = {
                'avg_processing_time': sum(processing_times) / len(processing_times),
                'min_processing_time': min(processing_times),
                'max_processing_time': max(processing_times),
                'files_processed': len(processing_times)
            }
            
            if lines_per_file:
                stats.update({
                    'avg_lines_per_file': sum(lines_per_file) / len(lines_per_file),
                    'total_lines_processed': sum(lines_per_file)
                })
            
            return stats
    
    def _call_progress_callback(self) -> None:
        """Call the progress callback with current progress"""
        if self.progress_callback:
            try:
                progress_data = self.get_comprehensive_progress()
                self.progress_callback(
                    progress_data['overall_progress'],
                    progress_data['status_message'],
                    progress_data['current_file']
                )
            except Exception as e:
                print(f"Warning: Progress callback failed: {e}")
                # Don't re-raise, just log and continue
    
    def reset(self) -> None:
        """Reset progress tracker"""
        with self.translation_lock:
            self.progress_tracker = {
                'stage': 'idle',
                'overall_progress': 0.0,
                'current_file': '',
                'current_file_progress': 0.0,
                'files_completed': 0,
                'total_files': 0,
                'total_lines': 0,
                'lines_processed': 0,
                'start_time': None,
                'current_file_start_time': None,
                'files_tracker': {},
                'batch_progress': {'current': 0, 'total': 0},
                'performance_history': deque(maxlen=50)
            }