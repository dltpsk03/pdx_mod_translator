"""
Performance optimization module for translation engine
성능 최적화를 위한 동적 배치 크기 조정, 캐싱, 동시성 처리
"""

import time
import threading
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from functools import lru_cache
import asyncio
import concurrent.futures


class PerformanceOptimizer:
    """번역 성능 최적화 관리자"""
    
    def __init__(self):
        self.performance_history = deque(maxlen=10)
        self.adaptive_batch_sizing = True
        self.concurrent_api_calls = True
        self.max_concurrent_requests = 8
        self.batch_cache = {}
        self.request_queue = deque()
        self.adaptive_delay = 0.2
        self.success_rate_threshold = 0.85
        
        # 동적 배치 크기 조정
        self.dynamic_batch_size = None
        self.base_batch_size = 50
        
        # 스레드 안전성을 위한 락들
        self._stats_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        
        # 캐시 관리
        self._cache_size = 1000
        self._source_remnant_cache = deque(maxlen=self._cache_size)
        self._regex_error_cache = deque(maxlen=self._cache_size)
        
    def calculate_optimal_batch_size(self, current_batch_size: int) -> int:
        """성능 히스토리를 바탕으로 최적 배치 크기 계산 (최대 80라인 제한)"""
        if not self.performance_history:
            return min(current_batch_size + 15, 80)  # 점진적 증가, 최대 80
            
        # 최근 성공률 계산
        recent_success_rate = sum(1 for p in self.performance_history if p['success']) / len(self.performance_history)
        
        if recent_success_rate >= 0.9:
            # 매우 높은 성공률: 배치 크기 증가
            return min(current_batch_size + 20, 80)
        elif recent_success_rate >= 0.8:
            # 좋은 성공률: 배치 크기 유지 또는 약간 증가
            return min(current_batch_size + 10, 80)
        else:
            # 낮은 성공률: 배치 크기 감소
            return max(current_batch_size - 10, 20)
    
    def record_batch_performance(self, success: bool, batch_size: int, processing_time: float):
        """배치 성능 기록"""
        with self._stats_lock:
            self.performance_history.append({
                'success': success,
                'batch_size': batch_size,
                'time': processing_time,
                'timestamp': time.time()
            })
            
            # 동적 배치 크기 업데이트 (최대 80라인 제한)
            if self.adaptive_batch_sizing:
                self.dynamic_batch_size = self.calculate_optimal_batch_size(batch_size)
    
    def get_optimal_batch_size(self) -> int:
        """현재 최적 배치 크기 반환"""
        return self.dynamic_batch_size if self.dynamic_batch_size else self.base_batch_size
    
    def calculate_adaptive_delay(self) -> float:
        """성능 히스토리를 바탕으로 적응형 지연 계산"""
        if not self.performance_history:
            return self.adaptive_delay
        
        recent_times = [p['time'] for p in list(self.performance_history)[-3:]]
        if recent_times:
            avg_time = sum(recent_times) / len(recent_times)
            # 응답 시간이 빠르면 지연 시간 단축, 느리면 지연 시간 증가
            if avg_time < 2.0:
                return max(0.1, self.adaptive_delay * 0.8)
            elif avg_time > 5.0:
                return min(2.0, self.adaptive_delay * 1.5)
        
        return self.adaptive_delay
    
    def cleanup_cache(self):
        """캐시 메모리 정리"""
        with self._cache_lock:
            self.batch_cache.clear()
            self._source_remnant_cache.clear()
            self._regex_error_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return {
            'batch_cache_size': len(self.batch_cache),
            'source_remnant_cache_size': len(self._source_remnant_cache),
            'regex_error_cache_size': len(self._regex_error_cache),
            'performance_history_size': len(self.performance_history)
        }


class RegexPatternManager:
    """정규식 패턴 관리자 - 성능 최적화를 위한 미리 컴파일된 패턴들"""
    
    def __init__(self):
        # 미리 컴파일된 정규식 패턴들 (성능 최적화)
        self.compiled_patterns = {
            'yml_value': re.compile(r':\s*"(.*)"\s*$'),
            'yml_key': re.compile(r'^(\s*[^:]+:\s*)"'),
            'lang_identifier': re.compile(r"^\s*l_([a-zA-Z_]+)\s*:", re.IGNORECASE),
            'valid_yml_value': re.compile(r'^[^"]*"([^"\\]|\\.)*$'),
            'improper_quote': re.compile(r'(?<!^)(?<![\r\n\t ])"(?=[A-Za-z])'),
            'key_value_split': re.compile(r'^(\s*[^:]+:\d*\s*"[^"]*")(.*)'),
            'comment_extract': re.compile(r'(\s*#.*)'),
            'unescaped_quote': re.compile(r'(?<!\\)"'),
            'unclosed_quote': re.compile(r':\s*"[^"]*$'),
            'valid_key': re.compile(r'^[a-zA-Z_][a-zA-Z0-9_\.]*$'),
            'special_code': re.compile(r'[\$\[\]§£][^$\[\]§£]+[\$\[\]§£]'),
            'code_blocks': re.compile(r'```(yaml|yml)?\n?', re.IGNORECASE)
        }
        
        # 언어별 패턴들 - 개선된 버전
        self.language_patterns = {
            'English': re.compile(r'\b[a-zA-Z]{3,}\b', re.IGNORECASE),
            'Korean': re.compile(r'[\uAC00-\uD7AF]+'),
            'Japanese': re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'),
            'Simplified Chinese': re.compile(r'[\u4E00-\u9FFF]+'),
            'Traditional Chinese': re.compile(r'[\u4E00-\u9FFF]+'),
            'Russian': re.compile(r'[\u0400-\u04FF]+'),
            'French': re.compile(r'\b[a-zA-Z\u00C0-\u017FàâäçèéêëîïôùûüÿœæÀÂÄÇÈÉÊËÎÏÔÙÛÜŸŒÆ]{3,}\b', re.IGNORECASE),
            'German': re.compile(r'\b[a-zA-Z\u00C0-\u017FäöüßÄÖÜ]{3,}\b', re.IGNORECASE),
            'Spanish': re.compile(r'\b[a-zA-Z\u00C0-\u017FáéíóúñÁÉÍÓÚÑüÜ]{3,}\b', re.IGNORECASE),
            'Italian': re.compile(r'\b[a-zA-Z\u00C0-\u017FàèéìíòóùúÀÈÉÌÍÎÒÓÙÚ]{3,}\b', re.IGNORECASE),
            'Portuguese': re.compile(r'\b[a-zA-Z\u00C0-\u017FàáâãçéêíóôõúüÀÁÂÃÇÉÊÍÓÔÕÚÜ]{3,}\b', re.IGNORECASE),
            'Polish': re.compile(r'\b[a-zA-Z\u0100-\u017FąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}\b', re.IGNORECASE),
            'Turkish': re.compile(r'\b[a-zA-ZçğıöşüÇĞIİÖŞÜ]{3,}\b', re.IGNORECASE),
            'Arabic': re.compile(r'[\u0600-\u06FF]+'),
            'Hebrew': re.compile(r'[\u0590-\u05FF]+'),
            'Thai': re.compile(r'[\u0E00-\u0E7F]+'),
            'Vietnamese': re.compile(r'\b[a-zA-ZàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{3,}\b', re.IGNORECASE)
        }
        
        # 구문 패턴들
        self.phrase_patterns = {
            'english_phrase': re.compile(r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){2,}\b', re.IGNORECASE),
            'european_phrase': re.compile(r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){2,}\b', re.IGNORECASE)
        }
    
    def get_pattern(self, pattern_name: str):
        """패턴 가져오기"""
        return self.compiled_patterns.get(pattern_name) or self.language_patterns.get(pattern_name) or self.phrase_patterns.get(pattern_name)
    
    def get_language_pattern(self, language: str):
        """언어별 패턴 가져오기"""
        return self.language_patterns.get(language)


class ConcurrentProcessor:
    """동시성 처리 관리자"""
    
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._active_futures = set()
        
    async def process_batches_concurrently(self, batches: List[Any], process_func, *args, **kwargs) -> List[Any]:
        """배치들을 동시에 처리"""
        loop = asyncio.get_event_loop()
        futures = []
        
        for batch in batches:
            future = loop.run_in_executor(
                self.executor, 
                process_func, 
                batch, 
                *args, 
                **kwargs
            )
            futures.append(future)
            self._active_futures.add(future)
        
        try:
            results = await asyncio.gather(*futures, return_exceptions=True)
            return results
        finally:
            for future in futures:
                self._active_futures.discard(future)
    
    def shutdown(self):
        """실행자 종료"""
        # 활성 작업들 취소
        for future in list(self._active_futures):
            future.cancel()
        
        self.executor.shutdown(wait=True)
        self._active_futures.clear()


class ResourceManager:
    """리소스 관리자"""
    
    def __init__(self):
        self._temp_directories = set()
        self._active_threads = set()
        
    def add_temp_directory(self, temp_dir: str):
        """임시 디렉토리 추가"""
        self._temp_directories.add(temp_dir)
    
    def add_active_thread(self, thread: threading.Thread):
        """활성 스레드 추가"""
        self._active_threads.add(thread)
    
    def cleanup_resources(self):
        """모든 리소스 정리"""
        try:
            # 활성 스레드 정리
            for thread in list(self._active_threads):
                if thread.is_alive():
                    thread.join(timeout=2.0)
            self._active_threads.clear()
            
            # 임시 디렉토리 정리
            import shutil
            for temp_dir in list(self._temp_directories):
                try:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                except:
                    pass
            self._temp_directories.clear()
            
        except Exception:
            pass  # Silent cleanup