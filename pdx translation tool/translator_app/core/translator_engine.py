#translator_project/translator_app/core/translator_engine.py
import os
import threading
import time
import codecs
import concurrent.futures
import google.generativeai as genai
import re
import tempfile
import json
import shutil
from datetime import datetime
from functools import lru_cache
from collections import deque
from ..utils.localization import get_language_code
from .game_prompts import get_enhanced_prompt

class TranslationRecovery:
    """번역 중단 시 복구를 위한 체크포인트 관리"""
    def __init__(self, checkpoint_dir="checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def save_checkpoint(self, file_path, completed_lines, total_lines):
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{os.path.basename(file_path)}.checkpoint")
        checkpoint_data = {
            'file_path': file_path,
            'completed_lines': completed_lines,
            'total_lines': total_lines,
            'timestamp': time.time()
        }
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f)
    
    def load_checkpoint(self, file_path):
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{os.path.basename(file_path)}.checkpoint")
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def remove_checkpoint(self, file_path):
        checkpoint_file = os.path.join(self.checkpoint_dir, f"{os.path.basename(file_path)}.checkpoint")
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

class TranslatorEngine:
    def __init__(self, log_callback, progress_callback, status_callback, stop_event, get_input_folder_callback):
        self.log_callback = log_callback
        self.main_progress_callback = progress_callback
        self.main_status_callback = status_callback
        self.stop_event = stop_event
        self.get_input_folder_callback = get_input_folder_callback

        # 스레드 로컬 저장소 (동시성 문제 해결)
        self.thread_local = threading.local()
        
        # 스레드 안전성을 위한 락들
        self._stats_lock = threading.RLock()
        self._cache_lock = threading.RLock()
        self._file_processing_lock = threading.RLock()
        self._callback_lock = threading.RLock()
        
        self.model = None
        self.translation_thread = None
        self.validation_thread = None
        self.recovery = TranslationRecovery()

        # 설정 변수들
        self.enable_backup = False  
        self.api_key = None
        self.selected_model_name = None
        self.source_lang_for_api = None
        self.target_lang_for_api = None
        self.prompt_template_str = None
        self.glossary_str_for_prompt = None
        self.batch_size = 50
        self.max_tokens = 65536
        self.delay_between_batches = 0.8
        self.temperature = 0.5
        
        # 성능 최적화를 위한 설정
        self.adaptive_batch_sizing = True
        self.concurrent_api_calls = True
        self.max_concurrent_requests = 8  # API 제한 고려
        self.batch_cache = {}  # 배치 결과 캐싱
        self.request_queue = deque()  # 요청 큐
        self.adaptive_delay = 0.2  # 기본 지연 시간 단축
        
        # 동적 배치 크기 조정
        self.dynamic_batch_size = None
        self.performance_history = deque(maxlen=10)
        self.success_rate_threshold = 0.85 
        self.max_workers = 100
        self.keep_identifier = False
        self.check_internal_lang = False
        self.split_large_files_threshold = 1000
        self.skip_already_translated = False
        self.selected_game = None
        self.max_retries = 3

        self.translated_files_info_for_review = []
        
        # UI 콜백 및 통계 콜백
        self.preview_callback = None
        self.stats_callback = None

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
            'Italian': re.compile(r'\b[a-zA-Z\u00C0-\u017FàèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ]{3,}\b', re.IGNORECASE),
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
        
        # 편의를 위한 직접 참조
        self.lang_identifier_pattern = self.compiled_patterns['lang_identifier']
        
        # 캐시 초기화
        self._cache_size = 1000
        self._source_remnant_cache = deque(maxlen=self._cache_size)
        self._regex_error_cache = deque(maxlen=self._cache_size)
    
    def _calculate_optimal_batch_size(self):
        """성능 히스토리를 바탕으로 최적 배치 크기 계산 (최대 80라인 제한)"""
        if not self.performance_history:
            return min(self.batch_size + 15, 80)  # 점진적 증가, 최대 80
            
        # 최근 성공률 계산
        recent_success_rate = sum(1 for p in self.performance_history if p['success']) / len(self.performance_history)
        
        if recent_success_rate >= 0.9:
            # 매우 높은 성공률: 배치 크기 증가
            return min(self.batch_size + 20, 80)
        elif recent_success_rate >= 0.8:
            # 좋은 성공률: 배치 크기 유지 또는 약간 증가
            return min(self.batch_size + 10, 80)
        else:
            # 낮은 성공률: 배치 크기 감소
            return max(self.batch_size - 10, 20)
    
    def _record_batch_performance(self, success, batch_size, processing_time):
        """배치 성능 기록"""
        self.performance_history.append({
            'success': success,
            'batch_size': batch_size,
            'time': processing_time,
            'timestamp': time.time()
        })
        
        # 동적 배치 크기 업데이트 (최대 80라인 제한)
        if self.adaptive_batch_sizing:
            self.dynamic_batch_size = self._calculate_optimal_batch_size()
        
        # 리소스 정리를 위한 추적
        self._temp_directories = set()
        self._active_threads = set()
        
        # 현재 파일 통계
        self.current_file_stats = {}
        self.current_file_start_time = None

    def __del__(self):
        """리소스 정리"""
        try:
            self.cleanup_resources()
        except:
            pass
    
    def cleanup_resources(self):
        """모든 리소스 정리"""
        try:
            # 정지 신호 설정
            if hasattr(self, 'stop_event'):
                self.stop_event.set()
            
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
            
            # 캐시 정리
            self._cleanup_caches()
            
            # 콜백 정리
            self.clear_callbacks()
            
        except Exception as e:
            if hasattr(self, 'log_callback') and self.log_callback:
                self.log_callback("log_cleanup_error", str(e))
    
    def _cleanup_caches(self):
        """캐시 메모리 정리"""
        try:
            self._source_remnant_cache.clear()
            self._regex_error_cache.clear()
        except:
            pass
    
    def clear_callbacks(self):
        """모든 콜백 참조 제거"""
        try:
            self.log_callback = None
            self.main_progress_callback = None
            self.main_status_callback = None
            self.preview_callback = None
            self.stats_callback = None
        except:
            pass

    def _get_current_file_for_log(self):
        """스레드 안전한 현재 파일명 가져오기"""
        if not hasattr(self.thread_local, 'current_file'):
            return ""
        return self.thread_local.current_file

    def _set_current_file_for_log(self, filename):
        """스레드 안전한 현재 파일명 설정"""
        self.thread_local.current_file = filename

    def _initialize_model(self):
        """모델 초기화 with 강화된 에러 처리"""
        try:
            # API 키 설정 (타임아웃 추가)
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.selected_model_name)
            
            # API 연결 테스트
            test_response = self.model.generate_content(
                "test", 
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1,
                    temperature=0.1
                )
            )
            
            self.log_callback("log_model_start", self.selected_model_name)
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 구체적인 에러 타입 감지
            if "api_key" in error_msg or "authentication" in error_msg or "unauthenticated" in error_msg:
                self.log_callback("log_api_auth_error", str(e))
            elif "quota" in error_msg or "limit" in error_msg or "exceeded" in error_msg:
                self.log_callback("log_api_quota_exceeded", str(e))
            elif "permission" in error_msg or "denied" in error_msg:
                self.log_callback("log_api_permission_error", str(e))
            elif "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                self.log_callback("log_api_network_error", str(e))
            elif "model" in error_msg or "not found" in error_msg:
                self.log_callback("log_api_model_error", str(e))
            else:
                self.log_callback("log_api_model_init_fail", str(e))
            
            return False

    def _extract_yml_value(self, line_content):
        """YML 라인에서 값 부분만 추출 (최적화된 정규식 사용)"""
        line_no_comment = line_content.split('#', 1)[0]
        match = self.compiled_patterns['yml_value'].search(line_no_comment.rstrip())
        if match:
            return match.group(1)
        return None

    def _extract_yml_key(self, line_content):
        """YML 라인에서 키(id) 부분 추출"""
        line_no_comment = line_content.split('#', 1)[0]
        if ':' in line_no_comment:
            return line_no_comment.split(':', 1)[0].strip()
        return None

    def validate_yml_file(self, file_path):
        """YML 파일의 구문 검증"""
        errors = []
        
        try:
            with codecs.open(file_path, 'r', encoding='utf-8-sig') as f:
                for line_num, line in enumerate(f, 1):
                    # YML 구문 검증
                    if ':' in line and not line.strip().startswith('#'):
                        if line.count('"') % 2 != 0:
                            errors.append(f"Line {line_num}: 따옴표 불일치")
                        
                        # 키 검증
                        key = line.split(':', 1)[0].strip()
                        if key and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\.]*$', key):
                            errors.append(f"Line {line_num}: 잘못된 키 형식 '{key}'")
        except Exception as e:
            errors.append(f"파일 읽기 오류: {str(e)}")
        
        return errors

    @lru_cache(maxsize=1000)
    def _check_line_for_yml_errors_cached(self, line_hash):
        """캐시된 YML 오류 검사"""
        return None

    def _check_line_for_yml_errors_engine(self, full_line):
        """YML 라인의 정규식 오류 검사 - 개선된 버전"""
        if not full_line or not full_line.strip():
            return False
        
        # 주석 라인은 검사하지 않음
        if full_line.strip().startswith('#'):
            return False
        
        # 키-값 쌍이 아닌 라인은 검사하지 않음
        if ':' not in full_line:
            return False
        
        # 캐시 확인 (스레드 안전)
        line_hash = hash(full_line)
        with self._cache_lock:
            for cached_hash, result in self._regex_error_cache:
                if cached_hash == line_hash:
                    return result
        
        try:
            # 주석 제거 (따옴표 뒤의 주석 처리)
            key_value_match = re.match(r'^(\s*[^:]+:\d*\s*"[^"]*")(.*)', full_line)
            if key_value_match:
                key_value_part = key_value_match.group(1)
                remainder = key_value_match.group(2)
                
                comment_match = re.search(r'(\s*#.*)', remainder)
                if comment_match:
                    full_line = key_value_part + remainder[:comment_match.start()]
            
            has_error = False
            
            # 패턴 1: 올바른 YML 값 패턴 검사
            yml_pattern = r'^[^"]*"([^"\\]|\\.)*$'
            if re.match(yml_pattern, full_line):
                has_error = True
            
            # 패턴 2: 부적절한 선행 따옴표 검사
            if not has_error:
                value_match = re.search(r':\s*"(.*?)"?\s*$', full_line)
                if value_match:
                    value_text = value_match.group(1)
                    improper_quote_pattern = r'(?<!^)(?<![\r\n\t ])"(?=[A-Za-z])'
                    if re.search(improper_quote_pattern, value_text):
                        has_error = True
            
            # 추가 검사: 따옴표가 제대로 닫히지 않은 경우
            if not has_error:
                quote_count = full_line.count('"')
                if quote_count % 2 != 0:
                    has_error = True
            
            # 추가 검사: 값이 따옴표로 시작하지만 끝나지 않는 경우
            if not has_error:
                if re.search(r':\s*"[^"]*$', full_line) and not re.search(r':\s*"[^"]*"\s*(?:#.*)?$', full_line):
                    has_error = True
            
            # 캐시에 저장 (스레드 안전)
            with self._cache_lock:
                self._regex_error_cache.append((line_hash, has_error))
            
            return has_error
        except Exception as e:
            self.log_callback("log_yml_check_error", str(e))
            return False

    def _check_regex_errors_optimized(self, value_text):
        """정규식 오류 검사 - 개선된 버전"""
        if not value_text:
            return False
        
        # 캐시 확인
        cache_key = hash(value_text)
        for cached_key, result in self._regex_error_cache:
            if cached_key == cache_key:
                return result
        
        has_error = False
        
        try:
            # 전체 라인 형태로 만들어서 검사
            full_line = f'key:0 "{value_text}"'
            
            # 패턴 1: 올바른 YML 값 패턴 - 매치되면 오류
            yml_pattern = r'^[^"]*"([^"\\]|\\.)*$'
            if re.match(yml_pattern, full_line):
                has_error = True
            
            # 패턴 2: 값 내부의 부적절한 따옴표
            if not has_error:
                improper_quote_pattern = r'(?<!^)"(?=[A-Za-z])'
                if re.search(improper_quote_pattern, value_text):
                    has_error = True
            
            # 패턴 3: 이스케이프되지 않은 따옴표
            if not has_error:
                unescaped_quote_pattern = r'(?<!\\)"'
                matches = list(re.finditer(unescaped_quote_pattern, value_text))
                if len(matches) > 0:
                    for match in matches:
                        if 0 < match.start() < len(value_text) - 1:
                            has_error = True
                            break
                            
        except re.error:
            has_error = False
        
        # 캐시에 저장
        self._regex_error_cache.append((cache_key, has_error))
        
        return has_error

    def _check_line_for_yml_errors(self, full_line):
        """디버깅용 YML 오류 검사."""
        result = self._check_line_for_yml_errors_engine(full_line)
        return result

    def _check_source_remnants_optimized(self, value_text, original_lines, line_index):
        """원본과 동일한 값이 번역 결과에 남아있는지 확인."""
        if value_text is None or line_index >= len(original_lines):
            return False

        orig_value = self._extract_yml_value(original_lines[line_index])
        if orig_value is None:
            return False

        return orig_value.strip() == value_text.strip()

    def _is_already_translated(self, text, target_lang):
        """텍스트가 이미 대상 언어로 번역되었는지 확인 - 개선된 로직"""
        if not text or not text.strip():
            return False
        
        # 특수 코드 제거
        cleaned_text = self._clean_text_for_language_detection(text)
        if not cleaned_text.strip():
            return False
        
        # 캐시 확인
        source_lang = getattr(self, 'source_lang_for_api', 'English')
        cache_key = (hash(text), target_lang, source_lang)
        if hasattr(self, '_translation_check_cache'):
            if cache_key in self._translation_check_cache:
                return self._translation_check_cache[cache_key]
        else:
            self._translation_check_cache = {}
        
        # 원본 언어 감지
        is_source_lang = self._detect_language(cleaned_text, source_lang)
        # 대상 언어 감지
        is_target_lang = self._detect_language(cleaned_text, target_lang)
        
        # 스킵 조건: 대상 언어이면서 원본 언어가 아닌 경우만
        result = is_target_lang and not is_source_lang
        
        # 캐시에 저장 (최대 10000개)
        if len(self._translation_check_cache) < 10000:
            self._translation_check_cache[cache_key] = result
        
        return result
    
    def _detect_language(self, text, lang):
        """특정 언어가 텍스트에 포함되어 있는지 감지"""
        if not text or not lang:
            return False
            
        if lang == 'Korean':
            return bool(re.search(r'[\uAC00-\uD7AF]', text))
        elif lang == 'Japanese':
            return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        elif lang in ['Simplified Chinese', 'Traditional Chinese']:
            return bool(re.search(r'[\u4E00-\u9FFF]', text))
        elif lang == 'Russian':
            return bool(re.search(r'[\u0400-\u04FF]', text))
        elif lang == 'English':
            # 영어는 다른 언어 문자가 없고 영어 단어가 있는 경우
            has_other_lang = any([
                re.search(r'[\uAC00-\uD7AF]', text),  # 한글
                re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text),  # 일본어
                re.search(r'[\u4E00-\u9FFF]', text),  # 중국어
                re.search(r'[\u0400-\u04FF]', text),  # 러시아어
            ])
            if has_other_lang:
                return False
            return bool(re.search(r'\b[a-zA-Z]{2,}\b', text))
        else:
            # 기타 언어는 간단한 패턴 체크
            language_patterns = {
                'French': r'[àâäçèéêëîïôùûüÿœæ]',
                'German': r'[äöüßÄÖÜ]', 
                'Spanish': r'[áéíóúñ¿¡]',
                'Italian': r'[àèéìíîòóùú]',
                'Portuguese': r'[àáâãçéêíóôõúü]',
                'Polish': r'[ąćęłńóśźż]',
                'Turkish': r'[çğıöşü]',
                'Arabic': r'[\u0600-\u06FF]',
                'Thai': r'[\u0E00-\u0E7F]',
                'Vietnamese': r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]'
            }
            pattern = language_patterns.get(lang)
            if pattern:
                return bool(re.search(pattern, text, re.IGNORECASE))
        
        return False

    def _calculate_batch_translation_ratio(self, text_batch):
        """배치 내 대상 언어로 번역된 라인의 비율 계산"""
        if not text_batch:
            return 0.0
        
        translated_count = 0
        total_valuable_lines = 0
        
        for line in text_batch:
            value = self._extract_yml_value(line)
            if value and value.strip():  # 값이 있는 라인만 카운트
                total_valuable_lines += 1
                if self._is_already_translated(value, self.target_lang_for_api):
                    translated_count += 1
        
        if total_valuable_lines == 0:
            return 0.0
        
        return translated_count / total_valuable_lines
    
    def _clean_text_for_language_detection(self, text):
        """언어 감지를 위한 텍스트 정리"""
        # 게임 특수 코드 제거
        special_patterns = [
            r'\$[^$]*\$',  # $variable$
            r'\[[^\]]*\]',  # [variable]
            r'§[A-Za-z0-9]',  # §Y 색상 코드
            r'£[^£]*£',  # £gold£ 아이콘 코드
            r'<[^>]*>',  # <tag>
            r'\{[^}]*\}',  # {variable}
            r'%[^%]*%',  # %variable%
            r'#[A-Fa-f0-9]{6}',  # 색상 코드
        ]
        
        cleaned = text
        for pattern in special_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 연속된 공백 정리
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _is_english_translation(self, cleaned_text, language_patterns):
        """영어 번역 여부 판단 - 개선된 로직"""
        # 다른 언어 문자가 있으면 이미 번역된 것
        for lang, pattern in language_patterns.items():
            if lang != 'English' and re.search(pattern, cleaned_text):
                return True
        
        # 순수 영어인지 확인
        english_words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned_text)
        if not english_words:
            return False
        
        # 숫자나 기호만 있는 경우 번역 안된 것으로 판단
        if re.match(r'^[\d\s\-+*/=<>().,!?:;%$€£¥]+$', cleaned_text):
            return False
        
        # 영어 단어가 있고 다른 언어가 없으면, 소스 언어가 영어가 아닐 때만 번역된 것으로 판단
        if hasattr(self, 'source_lang_for_api') and self.source_lang_for_api != 'English':
            # 일반적인 영어 단어들이 있으면 번역된 것으로 판단
            common_english_indicators = [
                r'\b(the|and|or|in|on|at|to|for|of|with|by)\b',  # 전치사, 접속사
                r'\b(is|are|was|were|have|has|will|would|can|could)\b',  # 동사
                r'\b(this|that|these|those|what|when|where|why|how)\b',  # 의문사, 지시어
            ]
            
            for indicator in common_english_indicators:
                if re.search(indicator, cleaned_text, re.IGNORECASE):
                    return True
        
        return False

    def calculate_translation_quality(self, original, translated):
        """번역 품질 점수 계산 - 다국어 지원 개선"""
        score = 100
        
        # 길이 비율 체크
        if original and len(original) > 0:
            length_ratio = len(translated) / len(original)
            if length_ratio < 0.3 or length_ratio > 3.0:
                score -= 25
            elif length_ratio < 0.5 or length_ratio > 2.0:
                score -= 15
        
        # 특수 코드 보존 체크
        original_codes = re.findall(r'[\$\[\]§£][^$\[\]§£]+[\$\[\]§£]', original)
        translated_codes = re.findall(r'[\$\[\]§£][^$\[\]§£]+[\$\[\]§£]', translated)
        if len(original_codes) != len(translated_codes):
            score -= 30
        
        # 원본 언어 잔존 체크 (개선된 다국어 지원)
        if hasattr(self, 'source_lang_for_api') and hasattr(self, 'target_lang_for_api'):
            if self.source_lang_for_api != self.target_lang_for_api:
                if self._check_source_language_remnants(translated, original, self.source_lang_for_api):
                    score -= 40  # 원본 언어 잔존은 심각한 문제로 간주
        
        # 번역 완전성 체크 - 빈 번역이나 너무 짧은 번역
        if not translated.strip():
            score = 0
        elif len(translated.strip()) < 2 and len(original.strip()) > 5:
            score -= 30
        
        # 동일한 텍스트인 경우 (번역되지 않음)
        if original.strip() == translated.strip() and len(original.strip()) > 3:
            score -= 20
        
        return max(0, score)

    def create_auto_backup(self, output_file):
        """자동 백업 생성 (설정에 따라)"""
        if not self.enable_backup:
            return
            
        try:
            backup_dir = os.path.join(os.path.dirname(output_file), ".backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{os.path.basename(output_file)}.{timestamp}.bak")
            
            if os.path.exists(output_file):
                shutil.copy2(output_file, backup_file)
                self.log_callback("log_backup_created", backup_file)
                
                # 오래된 백업 삭제 (7일 이상)
                self.cleanup_old_backups(backup_dir, days=7)
        except Exception as e:
            self.log_callback("log_backup_error", str(e))
    
    def cleanup_old_backups(self, backup_dir, days=7):
        """오래된 백업 파일 삭제"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath) and os.path.getctime(filepath) < cutoff_time:
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    def _is_valid_content_line(self, line):
        """번역 대상이 되는 유효한 컨텐츠 라인인지 확인"""
        if not line or not line.strip():
            return False
        
        stripped = line.strip()
        
        # 주석 라인 제외
        if stripped.startswith('#'):
            return False
        
        # 언어 식별자 라인 제외
        if self.lang_identifier_pattern.match(line):
            return False
        
        # 키-값 쌍이 있는 라인만 포함
        if ':' in line:
            # 값 부분에 따옴표가 있는지 확인
            key_value_split = line.split(':', 1)
            if len(key_value_split) > 1:
                value_part = key_value_split[1]
                if '"' in value_part:
                    return True
        
        return False

    def _verify_translation_completeness(self, original_file_path, translated_file_path):
        """번역 완료 후 검증 단계 - 언어 식별자, 주석, 빈 줄 무시"""
        try:
            # 원본 파일의 유효 key-value 라인 파싱
            with codecs.open(original_file_path, 'r', encoding='utf-8-sig') as f:
                original_lines = f.readlines()
            
            original_keys = {}
            original_line_nums = {}
            valid_line_count = 0
            
            for idx, line in enumerate(original_lines):
                if self._is_valid_content_line(line):
                    key = self._extract_yml_key(line)
                    if key:
                        original_keys[key] = (valid_line_count, line)
                        original_line_nums[key] = idx
                        valid_line_count += 1
            
            # 번역 파일의 유효 key-value 라인 파싱
            with codecs.open(translated_file_path, 'r', encoding='utf-8-sig') as f:
                translated_lines = f.readlines()
            
            translated_keys = {}
            valid_line_count = 0
            
            for idx, line in enumerate(translated_lines):
                if self._is_valid_content_line(line):
                    key = self._extract_yml_key(line)
                    if key:
                        translated_keys[key] = (valid_line_count, line)
                        valid_line_count += 1
            
            # 누락된 키 식별
            missing_keys = set(original_keys.keys()) - set(translated_keys.keys())
            
            if missing_keys:
                self.log_callback("log_missing_lines_detected", len(missing_keys), len(original_keys))
                # 누락된 키들의 원본 라인 번호 추가
                missing_keys_with_info = {}
                for key in missing_keys:
                    if key in original_line_nums:
                        missing_keys_with_info[key] = original_line_nums[key]
                return list(missing_keys), original_keys, original_lines, missing_keys_with_info
            
            return [], original_keys, original_lines, {}
            
        except Exception as e:
            self.log_callback("log_verification_error", str(e))
            return [], {}, [], {}

    def _retry_missing_translations(self, missing_keys, original_keys, original_lines, missing_keys_info, 
                                   translated_file_path, max_retries=3):
        """누락된 라인이 포함된 배치 전체를 재번역"""
        retry_count = 0
        
        while missing_keys and retry_count < max_retries:
            retry_count += 1
            self.log_callback("log_retrying_missing_lines", len(missing_keys), retry_count)
            
            # 누락된 키를 포함하는 원본 라인 인덱스 수집
            missing_line_indices = set()
            for key in missing_keys:
                if key in missing_keys_info:
                    missing_line_indices.add(missing_keys_info[key])
            
            # 배치 단위로 재번역
            batches_to_retry = {}
            for idx in sorted(missing_line_indices):
                batch_num = idx // self.batch_size
                if batch_num not in batches_to_retry:
                    batches_to_retry[batch_num] = []
                batches_to_retry[batch_num].append(idx)
            
            # 번역 파일 읽기
            with codecs.open(translated_file_path, 'r', encoding='utf-8-sig') as f:
                all_translated_lines = f.readlines()
            
            # 각 배치 재번역
            for batch_num, indices in batches_to_retry.items():
                batch_start = batch_num * self.batch_size
                batch_end = min(batch_start + self.batch_size, len(original_lines))
                
                # 배치에서 유효한 컨텐츠 라인만 추출
                batch_lines = []
                batch_indices = []
                for i in range(batch_start, batch_end):
                    if i < len(original_lines) and self._is_valid_content_line(original_lines[i]):
                        batch_lines.append(original_lines[i])
                        batch_indices.append(i)
                
                if not batch_lines:
                    continue
                
                # 배치 전체 재번역 (온도 약간 상승)
                new_temperature = min(self.temperature + (0.1 * retry_count), 1.0)
                translated_batch = self._translate_batch_core(
                    batch_lines, 
                    temperature=new_temperature,
                    retry=True
                )
                
                # 번역 결과를 원본 파일 구조에 맞게 매핑
                translated_dict = {}
                for i, translated_line in enumerate(translated_batch):
                    if i < len(batch_indices):
                        original_idx = batch_indices[i]
                        key = self._extract_yml_key(original_lines[original_idx])
                        if key:
                            translated_dict[key] = translated_line
                
                # 번역 파일 업데이트
                updated_lines = []
                for line in all_translated_lines:
                    key = self._extract_yml_key(line)
                    if key and key in translated_dict:
                        updated_lines.append(translated_dict[key])
                    else:
                        updated_lines.append(line)
                
                # 파일 다시 저장
                with codecs.open(translated_file_path, 'w', encoding='utf-8-sig') as f:
                    f.writelines(updated_lines)
                
                all_translated_lines = updated_lines
            
            # 다시 검증
            missing_keys, _, _, missing_keys_info = self._verify_translation_completeness(
                original_file_path, translated_file_path
            )
            
            if missing_keys:
                time.sleep(min(self.adaptive_delay * 2, 0.5))  # 재시도 전 대기 시간 단축
        
        if missing_keys:
            self.log_callback("log_failed_to_translate_all", len(missing_keys))

    def _translate_batch_core(self, text_batch, temperature=None, retry=False):
        """배치 번역 핵심 로직 - 98% 임계값 기반 스킵 로직"""
        # 기번역 라인 필터링
        if hasattr(self, 'skip_already_translated') and self.skip_already_translated:
            # 배치의 번역 비율 계산
            translation_ratio = self._calculate_batch_translation_ratio(text_batch)
            
            # 98% 이상이 이미 번역되어 있으면 배치 전체 건너뛰기
            if translation_ratio >= 0.98:
                self.log_callback("log_batch_skip_high_ratio", 
                                self._get_current_file_for_log(), 
                                f"{translation_ratio*100:.1f}%")
                return text_batch
            
            # 98% 미만이면 라인별 검사
            elif translation_ratio > 0:
                lines_to_translate = []
                line_mapping = []  # 원본 인덱스 매핑
                
                for idx, line in enumerate(text_batch):
                    value = self._extract_yml_value(line)
                    
                    if not value:
                        # 값이 없는 라인은 그대로 포함
                        lines_to_translate.append(line)
                        line_mapping.append((idx, True))  # True = 번역 필요
                    elif self._is_already_translated(value, self.target_lang_for_api):
                        # 이미 번역된 라인은 매핑만 저장
                        line_mapping.append((idx, False))  # False = 번역 불필요
                    else:
                        # 번역 필요한 라인만 추가
                        lines_to_translate.append(line)
                        line_mapping.append((idx, True))
                
                # 번역할 라인이 없으면 원본 반환
                if not any(need_translate for _, need_translate in line_mapping if need_translate):
                    return text_batch
                
                # 선별된 라인만 번역
                self.log_callback("log_batch_selective_translation", 
                                len(lines_to_translate), 
                                len(text_batch))
                
                translated_lines = self._translate_batch_core_original(lines_to_translate, temperature, retry)
                
                # 결과 병합
                final_result = []
                translated_idx = 0
                
                for idx, (original_idx, need_translate) in enumerate(line_mapping):
                    if need_translate:
                        # 번역된 라인 사용
                        if translated_idx < len(translated_lines):
                            final_result.append(translated_lines[translated_idx])
                            translated_idx += 1
                        else:
                            # 번역 실패 시 원본 사용
                            final_result.append(text_batch[original_idx])
                    else:
                        # 이미 번역된 라인은 원본 그대로
                        final_result.append(text_batch[original_idx])
                
                return final_result
        
        # 기번역 건너뛰기 비활성화 시 기존 로직 사용
        return self._translate_batch_core_original(text_batch, temperature, retry)
    
    def _translate_batch_core_original(self, text_batch, temperature=None, retry=False):
        """실제 번역 수행 - 디버그 로그 제거 버전"""
        retry_count = 0
        max_retries = getattr(self, 'max_retries', 3)
        
        batch_start_time = time.time()
        
        while retry_count <= max_retries:
            # 번역할 텍스트만 추출
            batch_text_content = "\n".join([line.rstrip('\n') for line in text_batch])
            
            if temperature is None:
                temperature = self.temperature
            
            # 프롬프트 준비
            try:
                if hasattr(self, 'selected_game') and self.selected_game and self.selected_game != "None":
                    try:
                        enhanced_prompt = get_enhanced_prompt(self.selected_game, self.prompt_template_str)
                    except Exception as e:
                        self.log_callback("log_game_prompt_error", str(e))
                        enhanced_prompt = self.prompt_template_str
                else:
                    enhanced_prompt = self.prompt_template_str
                
                final_prompt = enhanced_prompt.format(
                    source_lang_for_prompt=self.source_lang_for_api,
                    target_lang_for_prompt=self.target_lang_for_api,
                    glossary_section=self.glossary_str_for_prompt if self.glossary_str_for_prompt else "",
                    batch_text=batch_text_content
                )
                
            except KeyError as e:
                self.log_callback("log_batch_unknown_error", self._get_current_file_for_log(), 
                            f"Prompt formatting error (KeyError: {e}).")
                return text_batch

            try:
                if self.stop_event.is_set():
                    return text_batch

                # API 호출
                response = self.model.generate_content(
                    final_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=self.max_tokens,
                        top_k=40,
                        top_p=0.95
                    )
                )
                
                translated_text = ""
                finish_reason_val = 0
                candidate = None

                if response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        translated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason_val = candidate.finish_reason
                elif hasattr(response, 'text') and response.text: 
                    translated_text = response.text

                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    self.log_callback("log_batch_prompt_blocked", self._get_current_file_for_log(), 
                                response.prompt_feedback.block_reason)
                    return text_batch

                # 응답 처리
                if finish_reason_val not in [0, 1]:
                    if finish_reason_val == 2:  # 토큰 한계
                        self.log_callback("log_batch_token_limit", self._get_current_file_for_log(), 
                                    finish_reason_val)
                        if len(text_batch) > 1:
                            mid = len(text_batch) // 2
                            first_half = self._translate_batch_core(text_batch[:mid], temperature)
                            if self.stop_event.is_set(): 
                                return text_batch
                            second_half = self._translate_batch_core(text_batch[mid:], temperature)
                            return first_half + second_half
                        else:
                            return text_batch
                    else:
                        return text_batch

                if not translated_text.strip():
                    self.log_callback("log_batch_empty_response", self._get_current_file_for_log())
                    return text_batch

                # 코드 블록 제거
                translated_text = re.sub(r'```(yaml|yml)?\n?', '', translated_text, flags=re.IGNORECASE)
                translated_text = re.sub(r'\n?```', '', translated_text)

                translated_lines_raw = translated_text.split('\n')
                
                # 라인 수 차이 처리
                line_diff = abs(len(translated_lines_raw) - len(text_batch))
                
                # 공백 라인만 제거한 후 비교
                non_empty_original = [line for line in text_batch if line.strip()]
                non_empty_translated = [line for line in translated_lines_raw if line.strip()]
                
                # 공백 라인을 제외한 실제 컨텐츠 라인 수가 같거나 1줄 차이면 OK
                content_line_diff = abs(len(non_empty_translated) - len(non_empty_original))
                
                if content_line_diff <= 1 or line_diff <= 1:
                    # 라인 매칭 로직
                    final_result = []
                    translated_idx = 0
                    
                    for i in range(len(text_batch)):
                        original_line = text_batch[i]
                        
                        # 번역된 라인이 있으면 사용
                        if translated_idx < len(translated_lines_raw):
                            translated_line = translated_lines_raw[translated_idx]
                            translated_idx += 1
                        else:
                            # 번역된 라인이 부족하면 원본 사용
                            translated_line = original_line
                        
                        # 원본이 빈 라인이고 번역도 빈 라인이면 OK
                        if not original_line.strip() and not translated_line.strip():
                            final_result.append(original_line)
                            continue
                        
                        # 원본 라인에서 키와 따옴표까지 추출
                        original_match = re.match(r'^(\s*[^:]+:\s*)"', original_line)
                        translated_match = re.match(r'^(\s*[^:]+:\s*)"', translated_line)
                        
                        # 만약 번역된 라인에 키가 없다면, 원본 키를 사용
                        if original_match and not translated_match:
                            key_part = original_match.group(1)
                            # 번역된 라인이 따옴표로 시작하지 않으면 추가
                            if translated_line.strip() and not translated_line.strip().startswith('"'):
                                translated_line = f'{key_part}"{translated_line.strip()}"'
                            else:
                                translated_line = key_part + translated_line.strip()
                        
                        # 줄바꿈 처리
                        if original_line.endswith('\n') and not translated_line.endswith('\n'):
                            translated_line += '\n'
                        elif not original_line.endswith('\n') and translated_line.endswith('\n'):
                            translated_line = translated_line.rstrip('\n')
                        
                        final_result.append(translated_line)
                    
                    # 번역 품질 검증 및 원본 언어 잔존 검사
                    translated_count = 0
                    source_remnant_count = 0
                    
                    for i in range(len(final_result)):
                        if i >= len(text_batch):
                            continue
                            
                        original_line = text_batch[i]
                        translated_line = final_result[i]
                        
                        # 실제로 번역되었는지 확인
                        original_value = self._extract_yml_value(original_line)
                        translated_value = self._extract_yml_value(translated_line)
                        
                        if original_value and translated_value:
                            if original_value != translated_value:
                                translated_count += 1
                                
                                # 원본 언어 잔존 검사
                                if self.source_lang_for_api != self.target_lang_for_api:
                                    if self._check_source_language_remnants(translated_value, original_value, self.source_lang_for_api):
                                        source_remnant_count += 1
                                
                                # Live Preview 콜백
                                if self.preview_callback:
                                    try:
                                        score = self.calculate_translation_quality(original_value, translated_value)
                                        has_error = self._check_regex_errors_optimized(translated_value)
                                        self.preview_callback(original_value, translated_value, score, has_error)
                                    except Exception as e:
                                        pass
                                
                                # 통계 수집
                                if hasattr(self, 'current_file_stats'):
                                    score = self.calculate_translation_quality(original_value, translated_value)
                                    self.current_file_stats.setdefault('batch_qualities', []).append(score)
                    
                    # 원본 언어가 너무 많이 남아있으면 재시도
                    source_remnant_threshold = 0.1 if retry_count == 0 else 0.05
                    if source_remnant_count > len(text_batch) * source_remnant_threshold:
                        retry_count += 1
                        if retry_count <= max_retries:
                            self.log_callback("log_batch_retry_source_remnants", 
                                        source_remnant_count, 
                                        len(text_batch),
                                        retry_count, 
                                        max_retries)
                            
                            temperature = min(temperature + (0.2 * retry_count), 1.0)
                            time.sleep(min(self.adaptive_delay * 3, 1.0))
                            continue
                    
                    # 배치 시간 기록
                    batch_time = time.time() - batch_start_time
                    if hasattr(self, 'current_file_stats'):
                        self.current_file_stats.setdefault('batch_times', []).append(batch_time)
                    
                    return final_result
                
                # 라인 수 차이가 크면 재시도
                retry_count += 1
                if retry_count <= max_retries:
                    self.log_callback("log_batch_retry_due_to_mismatch", 
                                self._get_current_file_for_log(), 
                                len(text_batch), 
                                len(translated_lines_raw), 
                                retry_count, 
                                max_retries)
                    temperature = min(temperature + 0.1, 1.0)
                    time.sleep(min(self.adaptive_delay * 2, 0.5))
                    continue

            except Exception as e:
                if self.stop_event.is_set():
                    return text_batch
                
                error_str = str(e).lower()
                # API 한계 에러 처리
                if ("token" in error_str and ("limit" in error_str or "exceeded" in error_str)) or \
                ("429" in error_str) or ("resource has been exhausted" in error_str):
                    self.log_callback("log_batch_api_limit_error_split", self._get_current_file_for_log(), str(e))
                    if len(text_batch) > 1:
                        mid = len(text_batch) // 2
                        first_half = self._translate_batch_core(text_batch[:mid], temperature)
                        if self.stop_event.is_set(): 
                            return text_batch
                        second_half = self._translate_batch_core(text_batch[mid:], temperature)
                        return first_half + second_half
                    else:
                        return text_batch
                
                # 일반 오류 재시도
                retry_count += 1
                if retry_count <= max_retries:
                    self.log_callback("log_batch_retrying", self._get_current_file_for_log(), str(e))
                    time.sleep(min(self.adaptive_delay * 2, 0.5))
                    temperature = min(temperature + 0.1, 1.0)
                    continue
                else:
                    self.log_callback("log_batch_unknown_error", self._get_current_file_for_log(), str(e))
                    return text_batch
        
        # 최대 재시도 횟수 초과
        self.log_callback("log_batch_max_retries_exceeded", self._get_current_file_for_log(), max_retries)
        return text_batch

    def _check_source_language_remnants(self, translated_value, original_value, source_lang):
        """번역된 텍스트에 원본 언어가 남아있는지 검사"""
        # 특수 코드 패턴 (이들은 번역하면 안됨)
        special_patterns = [
            r'\$[^$]+\$',  # $variable$
            r'\[[^\]]+\]',  # [variable]
            r'§[A-Z]',      # §Y 같은 색상 코드
            r'£[^£]+£',     # £gold£ 같은 아이콘 코드
            r'<[^>]+>',     # <tag>
            r'\{[^}]+\}',   # {variable}
        ]
        
        # 특수 패턴을 모두 제거한 텍스트
        cleaned_translated = translated_value
        cleaned_original = original_value
        
        for pattern in special_patterns:
            cleaned_translated = re.sub(pattern, '', cleaned_translated)
            cleaned_original = re.sub(pattern, '', cleaned_original)
        
        # 언어별 단어 패턴 정의 - 개선된 버전
        language_patterns = {
            'English': r'\b[a-zA-Z]{3,}\b',
            'Korean': r'[\uAC00-\uD7AF]+',
            'Japanese': r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+',
            'Simplified Chinese': r'[\u4E00-\u9FFF]+',
            'Traditional Chinese': r'[\u4E00-\u9FFF]+',
            'Russian': r'[\u0400-\u04FF]+',
            'French': r'\b[a-zA-Z\u00C0-\u017FàâäçèéêëîïôùûüÿœæÀÂÄÇÈÉÊËÎÏÔÙÛÜŸŒÆ]{3,}\b',
            'German': r'\b[a-zA-Z\u00C0-\u017FäöüßÄÖÜ]{3,}\b',
            'Spanish': r'\b[a-zA-Z\u00C0-\u017FáéíóúñÁÉÍÓÚÑüÜ]{3,}\b',
            'Italian': r'\b[a-zA-Z\u00C0-\u017FàèéìíîòóùúÀÈÉÌÍÎÒÓÙÚ]{3,}\b',
            'Portuguese': r'\b[a-zA-Z\u00C0-\u017FàáâãçéêíóôõúüÀÁÂÃÇÉÊÍÓÔÕÚÜ]{3,}\b',
            'Polish': r'\b[a-zA-Z\u0100-\u017FąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}\b',
            'Turkish': r'\b[a-zA-ZçğıöşüÇĞIİÖŞÜ]{3,}\b',
            'Arabic': r'[\u0600-\u06FF]+',
            'Hebrew': r'[\u0590-\u05FF]+',
            'Thai': r'[\u0E00-\u0E7F]+',
            'Vietnamese': r'\b[a-zA-ZàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]{2,}\b'
        }
        
        # 원본 언어의 패턴 가져오기
        source_pattern = language_patterns.get(source_lang, r'\b[a-zA-Z]{3,}\b')
        
        # 번역된 텍스트에서 원본 언어 단어 찾기
        translated_source_words = set(re.findall(source_pattern, cleaned_translated, re.IGNORECASE))
        original_source_words = set(re.findall(source_pattern, cleaned_original, re.IGNORECASE))
        
        # 대소문자 무시하고 비교
        translated_source_words_lower = {word.lower() for word in translated_source_words}
        original_source_words_lower = {word.lower() for word in original_source_words}
        
        # 원본에 있던 단어가 번역 후에도 남아있는지 확인
        common_words = translated_source_words_lower.intersection(original_source_words_lower)
        
        # 언어별 허용 단어들 정의 - 게임에서 공통으로 사용되는 용어들
        common_allowed_words = {
            'English': {'ok', 'yes', 'no', 'id', 'hp', 'mp', 'exp', 'lv', 'level', 'max', 'min', 'fps', 'ui', 'ai', 'cpu', 'gpu', 'ram', 'dps', 'aoe', 'rpg', 'mmo', 'pvp', 'pve', 'dlc', 'mod', 'beta', 'alpha'},
            'Korean': set(),  # 한국어는 일반적으로 허용할 단어가 적음
            'Japanese': set(),
            'Simplified Chinese': set(),
            'Traditional Chinese': set(),
            'Russian': {'ok', 'id', 'max', 'min'},
            'French': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'German': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'Spanish': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'Italian': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'Portuguese': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'Polish': {'ok', 'id', 'max', 'min', 'fps', 'dps', 'pvp', 'pve', 'dlc', 'mod'},
            'Turkish': {'ok', 'id', 'max', 'min'},
            'Arabic': set(),
            'Hebrew': set(),
            'Thai': set(),
            'Vietnamese': {'ok', 'id', 'max', 'min'}
        }
        
        allowed_words = common_allowed_words.get(source_lang, set())
        common_words = common_words - allowed_words
        
        # 원본 단어의 30% 이상이 남아있으면 번역 실패로 간주
        if original_source_words_lower and len(common_words) > len(original_source_words_lower) * 0.3:
            return True
        
        # 연속된 원본 언어 구문이 그대로 남아있는지 확인
        if source_lang == 'English':
            phrase_pattern = r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){2,}\b'  # 3개 이상의 연속된 영어 단어
        elif source_lang in ['Korean', 'Japanese', 'Simplified Chinese']:
            # 아시아 언어는 공백 없이 연결되므로 다른 패턴 사용
            phrase_pattern = language_patterns[source_lang]
        else:
            # 기타 유럽 언어
            phrase_pattern = r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){2,}\b'
        
        original_phrases = re.findall(phrase_pattern, cleaned_original, re.IGNORECASE)
        for phrase in original_phrases:
            if len(phrase) > 10 and phrase.lower() in cleaned_translated.lower():  # 10글자 이상의 긴 구문만 체크
                return True
        
        return False

    def get_language_code(self, lang_name_en_from_ui):
        return get_language_code(lang_name_en_from_ui)

    def get_translated_files_info(self):
        return self.translated_files_info_for_review

    def _process_single_file_core(self, input_file, output_file):
        """단일 파일 처리 - 통계 콜백 수정"""
        self._set_current_file_for_log(os.path.basename(input_file))
        
        # 파일 처리 시작 시 통계 초기화
        self.current_file_start_time = time.time()
        self.current_file_stats = {
            'file_path': output_file,
            'start_time': self.current_file_start_time,
            'lines': 0,
            'errors': 0,
            'error_types': {},
            'batch_times': [],
            'batch_qualities': [],
            'original_file': input_file
        }
        
        try:
            # 체크포인트 확인
            checkpoint = self.recovery.load_checkpoint(input_file)
            start_from_line = 0
            if checkpoint and checkpoint.get('file_path') == input_file:
                start_from_line = checkpoint.get('completed_lines', 0)
                if start_from_line > 0:
                    self.log_callback("log_checkpoint_found", self._get_current_file_for_log(), start_from_line)
            
            # 파일 읽기
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            if not lines:
                self.log_callback("log_file_empty", self._get_current_file_for_log())
                return
                
            total_lines = len(lines)
            
            # 대용량 파일 처리
            if self.split_large_files_threshold > 0 and total_lines > self.split_large_files_threshold:
                self.log_callback("log_file_split_start", self._get_current_file_for_log(), 
                            total_lines, self.split_large_files_threshold)
                self._process_large_file_in_chunks(input_file, output_file, lines)
                return

            translated_lines_final = []
            self.log_callback("log_file_process_start", self._get_current_file_for_log(), total_lines)
            
            # 언어 식별자 처리
            start_index = 0
            first_line_match = self.lang_identifier_pattern.match(lines[0]) if lines else None
            if first_line_match:
                original_first_line_content = lines[0]
                if self.keep_identifier:
                    translated_lines_final.append(original_first_line_content)
                else:
                    target_lang_code_str = self.get_language_code(self.target_lang_for_api)
                    new_first_line_content = self.lang_identifier_pattern.sub(
                        f"l_{target_lang_code_str}:", original_first_line_content, count=1)
                    translated_lines_final.append(new_first_line_content)
                start_index = 1

            # 콘텐츠 라인 번역
            content_lines_to_translate = lines[start_index:]
            
            # 체크포인트에서 재개
            if start_from_line > len(translated_lines_final):
                num_to_skip = start_from_line - len(translated_lines_final)
                translated_lines_final.extend(content_lines_to_translate[:num_to_skip])
                content_lines_to_translate = content_lines_to_translate[num_to_skip:]
            
            # 배치 단위로 번역
            for i in range(0, len(content_lines_to_translate), self.batch_size):
                if self.stop_event.is_set():
                    self.log_callback("log_file_process_stopped", self._get_current_file_for_log())
                    return
                
                batch_to_translate = content_lines_to_translate[i:i + self.batch_size]
                current_line_in_file = start_index + len(translated_lines_final) - len(translated_lines_final[:start_index])
                
                self.log_callback("log_batch_translate", current_line_in_file + 1, 
                            current_line_in_file + len(batch_to_translate), total_lines)
                
                # 번역 수행
                translated_batch_lines = self._translate_batch_core(batch_to_translate)
                
                # 번역 결과 확인 로그
                translated_count = sum(1 for j, line in enumerate(translated_batch_lines) 
                                    if line != batch_to_translate[j])
                if translated_count > 0:
                    self.log_callback("log_batch_translated_count", 
                                self._get_current_file_for_log(), 
                                translated_count, 
                                len(batch_to_translate))
                
                translated_lines_final.extend(translated_batch_lines)
                
                # 체크포인트 저장
                completed_so_far = len(translated_lines_final)
                if i % (self.batch_size * 10) == 0:
                    self.recovery.save_checkpoint(input_file, completed_so_far, total_lines)
                
                # 딜레이
                if i + self.batch_size < len(content_lines_to_translate) and not self.stop_event.is_set() and self.delay_between_batches > 0:
                    time.sleep(self.adaptive_delay)

            if self.stop_event.is_set(): 
                return

            # 백업 생성
            if os.path.exists(output_file):
                self.create_auto_backup(output_file)

            self.current_file_stats['lines'] = len(translated_lines_final)
            
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 파일 저장
            try:
                with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
                    f.writelines(translated_lines_final)
                self.log_callback("log_translation_complete_save", os.path.basename(output_file))
                
                # 저장 확인
                if os.path.exists(output_file):
                    saved_size = os.path.getsize(output_file)
                    self.log_callback("log_file_saved_size", os.path.basename(output_file), saved_size)
            except Exception as e:
                self.log_callback("log_file_save_error", self._get_current_file_for_log(), str(e))
                return
            
            # 통계 처리
            if not self.stop_event.is_set():
                try:
                    self.current_file_stats['time'] = time.time() - (self.current_file_start_time or time.time())
                    
                    if self.current_file_stats.get('batch_qualities'):
                        avg_quality = sum(self.current_file_stats['batch_qualities']) / len(self.current_file_stats['batch_qualities'])
                        self.current_file_stats['quality'] = round(avg_quality, 1)
                    else:
                        self.current_file_stats['quality'] = 100
                    
                    # 통계 저장
                    self.save_translation_result(output_file, self.current_file_stats)
                    
                    # 콜백 호출
                    if self.stats_callback:
                        self.stats_callback(output_file, self.current_file_stats)
                        
                except Exception as e:
                    self.log_callback("log_stats_error", str(e))

            # 검증 수행
            if not self.stop_event.is_set():
                missing_keys, original_keys, original_lines_for_retry, missing_keys_info = self._verify_translation_completeness(
                    input_file, output_file
                )
                
                if missing_keys:
                    self._retry_missing_translations(
                        missing_keys, original_keys, original_lines_for_retry, missing_keys_info, output_file
                    )
                
                self.translated_files_info_for_review.append({"original": input_file, "translated": output_file})
                self.recovery.remove_checkpoint(input_file)
                
        except Exception as e:
            if not self.stop_event.is_set():
                self.log_callback("log_file_process_error", self._get_current_file_for_log(), str(e))
        finally:
            self._set_current_file_for_log("")

    def _process_large_file_in_chunks(self, original_input_file_path, final_output_file_path, all_lines):
        chunk_start_time = time.time()
        chunk_stats = {
            'file_path': final_output_file_path,
            'start_time': chunk_start_time,
            'lines': len(all_lines),
            'errors': 0,
            'error_types': {},
            'chunk_times': [],
            'original_file': original_input_file_path
        }
        chunk_size = self.split_large_files_threshold
        translated_chunk_content_files = []
        temp_dir = ""
        
        try:
            temp_dir = tempfile.mkdtemp(prefix="translator_chunk_")
            self.log_callback("log_temp_dir_created", temp_dir)

            first_line_content_for_final_output = None 
            original_first_line = all_lines[0] if all_lines else ""
            first_line_match_in_original = self.lang_identifier_pattern.match(original_first_line)

            if first_line_match_in_original:
                if self.keep_identifier:
                    first_line_content_for_final_output = original_first_line
                else:
                    target_lang_code_str = self.get_language_code(self.target_lang_for_api)
                    first_line_content_for_final_output = self.lang_identifier_pattern.sub(
                        f"l_{target_lang_code_str}:", original_first_line, count=1)
            
            content_start_index_in_original = 1 if first_line_match_in_original else 0
            actual_content_lines = all_lines[content_start_index_in_original:]
            num_chunks = (len(actual_content_lines) + chunk_size - 1) // chunk_size

            def translate_chunk(index, chunk_lines):
                chunk_process_start = time.time()
                translated_current_chunk_content = []
                original_log_filename = self._get_current_file_for_log()
                self._set_current_file_for_log(f"{os.path.basename(original_input_file_path)} (chunk {index+1})")
                
                # 동적 배치 크기 사용 (최대 80라인 제한)
                effective_batch_size = min(self.dynamic_batch_size or self.batch_size, 80)
                for batch_start in range(0, len(chunk_lines), effective_batch_size):
                    if self.stop_event.is_set(): 
                        break
                    batch_to_translate = chunk_lines[batch_start: batch_start + effective_batch_size]
                    if not batch_to_translate: 
                        continue
                    
                    batch_start_time = time.time()
                    translated_batch = self._translate_batch_core(batch_to_translate)
                    batch_processing_time = time.time() - batch_start_time
                    
                    # 성능 기록
                    batch_success = len(translated_batch) == len(batch_to_translate)
                    self._record_batch_performance(batch_success, effective_batch_size, batch_processing_time)
                    
                    translated_current_chunk_content.extend(translated_batch)
                    
                    if self.delay_between_batches > 0 and not self.stop_event.is_set():
                        time.sleep(self.adaptive_delay)

                self._set_current_file_for_log(original_log_filename)
                if self.stop_event.is_set(): 
                    return None, 0
                
                temp_chunk_output_content_file = os.path.join(temp_dir, f"chunk_{index}_translated_content.yml")
                with codecs.open(temp_chunk_output_content_file, 'w', encoding='utf-8-sig') as f_out_content:
                    f_out_content.writelines(translated_current_chunk_content)
                chunk_time = time.time() - chunk_process_start
                return temp_chunk_output_content_file, chunk_time

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_index = {
                    executor.submit(translate_chunk, i, actual_content_lines[i*chunk_size:(i+1)*chunk_size]): i
                    for i in range(num_chunks) if not self.stop_event.is_set()
                }

                completed_chunks = 0
                translated_chunk_files = [None] * num_chunks
                for fut in concurrent.futures.as_completed(future_to_index):
                    if self.stop_event.is_set(): 
                        break
                    idx = future_to_index[fut]
                    try:
                        result_file, chunk_time = fut.result()
                        if result_file:
                            translated_chunk_files[idx] = result_file
                            chunk_stats['chunk_times'].append(chunk_time)
                            self.log_callback("log_chunk_completed", idx + 1, num_chunks)
                            completed_chunks += 1
                            self.main_status_callback("status_chunk_progress", completed_chunks, num_chunks, 
                                                   task_type="translation")
                    except Exception as exc:
                        self.log_callback("log_chunk_processing_failed", f"Chunk {idx+1}: {exc}")

            if not self.stop_event.is_set() and all(translated_chunk_files):
                self.log_callback("log_merging_chunks", final_output_file_path)

                if self.stats_callback:
                    try:
                        chunk_stats['time'] = time.time() - chunk_start_time
                        chunk_stats['quality'] = 85
                        self.stats_callback(final_output_file_path, chunk_stats)
                    except Exception as e:
                        self.log_callback("log_stats_callback_error", str(e))
                
                if os.path.exists(final_output_file_path):
                    self.create_auto_backup(final_output_file_path)
                
                os.makedirs(os.path.dirname(final_output_file_path), exist_ok=True)
                with codecs.open(final_output_file_path, 'w', encoding='utf-8-sig') as f_final:
                    if first_line_content_for_final_output:
                        f_final.write(first_line_content_for_final_output)
                    for chunk_file in translated_chunk_files:
                        if chunk_file and os.path.exists(chunk_file):
                            with codecs.open(chunk_file, 'r', encoding='utf-8-sig') as f_chunk_read:
                                shutil.copyfileobj(f_chunk_read, f_final)

                self.log_callback("log_translation_complete_save", os.path.basename(final_output_file_path))
                if not self.stop_event.is_set():
                    self.translated_files_info_for_review.append(
                        {"original": original_input_file_path, "translated": final_output_file_path})

            elif self.stop_event.is_set():
                self.log_callback("log_chunk_processing_stopped", self._get_current_file_for_log())
            else:
                self.log_callback("log_chunk_processing_failed", self._get_current_file_for_log())
        finally:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.log_callback("log_temp_dir_removed", temp_dir)

    def _translation_worker_thread_target(self, input_dir, output_dir):
        """번역 작업 스레드 - 동시 처리 복원 및 개선"""
        self.translated_files_info_for_review.clear()
        completed_count = 0
        total_files_to_process = 0

        if not self._initialize_model():
            self.main_status_callback("status_waiting", task_type="translation")
            return

        try:
            target_files = []
            source_lang_code_for_search = self.get_language_code(self.source_lang_for_api).lower()
            file_identifier_for_search = f"l_{source_lang_code_for_search}"
            self.log_callback("log_search_yml_files", file_identifier_for_search)

            for root_path, _, files_in_dir in os.walk(input_dir):
                if self.stop_event.is_set(): 
                    break
                for file_name in files_in_dir:
                    if file_identifier_for_search in file_name.lower() and file_name.lower().endswith(('.yml', '.yaml')):
                        target_files.append(os.path.join(root_path, file_name))

            if self.stop_event.is_set():
                self.log_callback("log_translation_stopped_by_user")
                self.main_status_callback("status_stopped", completed_count, len(target_files), task_type="translation")
                return

            total_files_to_process = len(target_files)
            if not target_files:
                self.log_callback("log_no_yml_files_found", input_dir, file_identifier_for_search)
                self.main_status_callback("status_no_files", task_type="translation")
                return

            self.log_callback("log_total_files_start", total_files_to_process)
            self.main_status_callback("status_translating_progress", 0, total_files_to_process, task_type="translation")

            target_lang_code_for_filename_output = self.get_language_code(self.target_lang_for_api).lower()
            
            # 동시 처리를 위한 Lock
            completed_lock = threading.Lock()
            
            # 파일 처리 함수
            def process_file(input_f):
                if self.stop_event.is_set():
                    return False
                    
                try:
                    relative_path = os.path.relpath(os.path.dirname(input_f), input_dir)
                    base_name = os.path.basename(input_f)
                    
                    if not self.keep_identifier:
                        identifier_to_replace_in_filename = f"l_{source_lang_code_for_search}"
                        new_target_identifier_for_filename = f"l_{target_lang_code_for_filename_output}"
                        new_base_name, num_replacements = re.subn(
                            re.escape(identifier_to_replace_in_filename),
                            new_target_identifier_for_filename,
                            base_name,
                            count=1,
                            flags=re.IGNORECASE
                        )
                        if num_replacements > 0:
                            base_name = new_base_name
                    
                    output_f_path = os.path.join(output_dir, relative_path, base_name)
                    
                    # 단일 파일 처리
                    self._process_single_file_core(input_f, output_f_path)
                    
                    return not self.stop_event.is_set()
                except Exception as e:
                    self.log_callback("log_file_process_error", os.path.basename(input_f), str(e))
                    return False

            # 실제 동시 처리 워커 수 제한 (API 제한 고려하여 증가)
            actual_max_workers = min(self.max_workers, 300, len(target_files))  # 250 API 호출 제한 고려 
            self.log_callback("log_concurrent_workers", actual_max_workers)
            
            # ThreadPoolExecutor로 동시 처리
            with concurrent.futures.ThreadPoolExecutor(max_workers=actual_max_workers) as executor:
                # 모든 작업 제출
                future_to_file = {executor.submit(process_file, f): f for f in target_files}
                
                # 완료된 작업 처리
                for future in concurrent.futures.as_completed(future_to_file):
                    if self.stop_event.is_set():
                        # 중지 요청 시 모든 미완료 작업 취소
                        for f in future_to_file:
                            f.cancel()
                        break
                    
                    file_path = future_to_file[future]
                    try:
                        success = future.result()
                        if success:
                            with completed_lock:
                                completed_count += 1
                                progress_value = completed_count / total_files_to_process
                                self.main_progress_callback(completed_count, total_files_to_process, 
                                                        progress_value, "translation")
                    except Exception as e:
                        self.log_callback("log_file_thread_error", os.path.basename(file_path), str(e))
            
            final_log_msg_key = "log_all_translation_done" if not self.stop_event.is_set() else "log_translation_stopped_by_user"
            self.log_callback(final_log_msg_key)

        except Exception as e:
            if not self.stop_event.is_set():
                self.log_callback("log_translation_process_error", str(e))
        finally:
            task_type = "translation"
            if self.stop_event.is_set():
                self.main_status_callback("status_stopped", completed_count, total_files_to_process, task_type=task_type)
            elif total_files_to_process == 0:
                self.main_status_callback("status_no_files", task_type=task_type)
            elif completed_count == total_files_to_process and total_files_to_process > 0:
                self.main_status_callback("status_completed_all", completed_count, total_files_to_process, task_type=task_type)
            else:
                self.main_status_callback("status_completed_some", completed_count, total_files_to_process, task_type=task_type)
            self._set_current_file_for_log("")

    def start_translation_process(self, api_key, selected_model_name,
                                input_folder, output_folder,
                                source_lang_api, target_lang_api,
                                prompt_template, glossary_content,
                                batch_size_val, max_tokens_val, delay_val, temperature_val, max_workers_val,
                                keep_identifier_val, check_internal_lang_val,
                                split_large_files_threshold,
                                selected_game=None,
                                skip_already_translated=False,
                                max_retries=3,
                                preview_callback=None,
                                stats_callback=None,
                                enable_backup=False):
        if self.translation_thread and self.translation_thread.is_alive():
            self.log_callback("warn_already_translating")
            return False
        if self.validation_thread and self.validation_thread.is_alive():
            self.log_callback("warn_already_validating")
            return False

        self.stop_event.clear()
        self.api_key = api_key
        self.selected_model_name = selected_model_name
        self.source_lang_for_api = source_lang_api
        self.target_lang_for_api = target_lang_api
        self.prompt_template_str = prompt_template
        self.glossary_str_for_prompt = glossary_content
        self.batch_size = batch_size_val
        self.max_tokens = max_tokens_val
        self.delay_between_batches = delay_val
        self.temperature = temperature_val
        self.max_workers = max_workers_val
        self.keep_identifier = keep_identifier_val
        self.check_internal_lang = check_internal_lang_val
        self.split_large_files_threshold = split_large_files_threshold
        self.selected_game = selected_game
        self.skip_already_translated = skip_already_translated
        self.max_retries = max_retries
        self.enable_backup = enable_backup
        
        # 콜백 설정 (안전하게)
        self.preview_callback = preview_callback if callable(preview_callback) else None
        self.stats_callback = stats_callback if callable(stats_callback) else None

        # 캐시 초기화
        self._regex_error_cache.clear()
        self._source_remnant_cache.clear()
        self.clear_statistics()

        self.main_status_callback("status_preparing", task_type="translation")
        self.translation_thread = threading.Thread(
            target=self._translation_worker_thread_target,
            args=(input_folder, output_folder),
            daemon=True
        )
        self.translation_thread.start()
        return True

    def request_stop_translation(self):
        if self.translation_thread and self.translation_thread.is_alive():
            self.log_callback("log_stop_requested")
            self.stop_event.set()
            return True
        return False

    def save_translation_result(self, file_path, stats_dict):
        """번역 결과를 파일에 저장 (스레드 안전)"""
        stats_file = "translation_stats.json"
        
        # 스레드 안전을 위한 락 사용
        with self._stats_lock:
            try:
                # 기존 통계 로드
                if os.path.exists(stats_file):
                    with open(stats_file, 'r', encoding='utf-8') as f:
                        all_stats = json.load(f)
                else:
                    all_stats = []
                
                # 새 통계 추가
                stat_entry = {
                    'file_path': file_path,
                    'filename': os.path.basename(file_path),
                    'timestamp': datetime.now().isoformat(),
                    'time': stats_dict.get('time', 0),
                    'quality': stats_dict.get('quality', 100),
                    'lines': stats_dict.get('lines', 0),
                    'errors': stats_dict.get('errors', 0),
                    'original_file': stats_dict.get('original_file', '')
                }
                
                all_stats.append(stat_entry)
                
                # 최대 1000개까지만 유지
                if len(all_stats) > 1000:
                    all_stats = all_stats[-1000:]
                
                # 원자적 쓰기: 임시 파일에 먼저 쓰고 이후 이동
                temp_file = stats_file + '.tmp'
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(all_stats, f, indent=2, ensure_ascii=False)
                
                # 원자적 이동 (Windows에서도 안전)
                if os.path.exists(stats_file):
                    os.replace(temp_file, stats_file)
                else:
                    os.rename(temp_file, stats_file)
                    
            except Exception as e:
                # 임시 파일 정리
                temp_file = stats_file + '.tmp'
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                self.log_callback("log_stats_save_error", str(e))

    def get_translation_statistics(self):
        """현재까지의 번역 통계 반환"""
        stats = {
            'total_files': len(self.translated_files_info_for_review),
            'current_file': self._get_current_file_for_log(),
            'is_running': self.translation_thread and self.translation_thread.is_alive()
        }
        return stats

    def clear_statistics(self):
        """통계 초기화"""
        self.translated_files_info_for_review.clear()
        self.current_file_stats = {}
        self.current_file_start_time = None
        
    def get_current_translation_progress(self):
        """현재 번역 진행 상황을 실시간으로 반환"""
        if hasattr(self, 'current_file_stats') and self.current_file_stats:
            return {
                'current_file': self._get_current_file_for_log(),
                'elapsed_time': time.time() - (self.current_file_stats.get('start_time') or time.time()),
                'is_running': self.translation_thread and self.translation_thread.is_alive()
            }
        return None

    def get_completed_files_count(self):
        """완료된 파일 수 반환"""
        return len(self.translated_files_info_for_review)
    
    def clear_callbacks(self):
        """모든 UI 콜백 초기화"""
        self.preview_callback = None
        self.stats_callback = None

    def classify_error_type(self, line, value):
        """오류 타입 상세 분류"""
        error_types = []
        
        # 정규식 오류
        if self._check_regex_errors_optimized(value):
            error_types.append('regex_error')
        
        # 따옴표 오류
        if value.count('"') % 2 != 0:
            error_types.append('unclosed_quote')
        
        # 코드 블록 오류
        if re.search(r'\$[^$]*$', value) or re.search(r'^\[[^\]]*\]', value):
            error_types.append('code_block_error')
        
        # 원본 언어 잔존
        if self.source_lang_for_api == 'English':
            if re.search(r'\b[a-zA-Z]{4,}\b', value):
                error_types.append('source_remnant')
        
        # 병합된 라인 (줄바꿈 오류)
        if '\\n' not in value and len(value) > 200:
            error_types.append('merged_lines')
        
        return error_types or ['unknown']