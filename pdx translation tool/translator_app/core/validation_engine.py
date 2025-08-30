"""
Validation and error correction module for translation engine
번역 결과 검증, 오류 감지 및 자동 교정 기능
"""

import re
import codecs
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import deque
from functools import lru_cache
from .performance_engine import RegexPatternManager


class ValidationEngine:
    """번역 검증 및 오류 교정 엔진"""
    
    def __init__(self):
        self.pattern_manager = RegexPatternManager()
        
        # 캐시 관리
        self._cache_size = 1000
        self._source_remnant_cache = deque(maxlen=self._cache_size)
        self._regex_error_cache = deque(maxlen=self._cache_size)
        self._translation_check_cache = {}
        
        # 스레드 안전성을 위한 락
        self._cache_lock = threading.RLock()
        
        # 유효성 검사 설정
        self.validation_level = "standard"  # off, basic, standard, strict
        self.auto_fix_enabled = True
        
        # 언어 감지 임계값
        self.language_detection_threshold = 0.3
        
    def validate_yml_file(self, file_path: str) -> List[str]:
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
    def _check_line_for_yml_errors_cached(self, line_hash: int) -> Optional[bool]:
        """캐시된 YML 오류 검사"""
        return None
    
    def _check_line_for_yml_errors_engine(self, full_line: str) -> bool:
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
        except Exception:
            return False
    
    def _check_regex_errors_optimized(self, value_text: str) -> bool:
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
    
    def _check_source_remnants_optimized(self, value_text: str, original_lines: List[str], line_index: int) -> bool:
        """원본과 동일한 값이 번역 결과에 남아있는지 확인"""
        if value_text is None or line_index >= len(original_lines):
            return False

        orig_value = self._extract_yml_value(original_lines[line_index])
        if orig_value is None:
            return False

        return orig_value.strip() == value_text.strip()
    
    def _extract_yml_value(self, line_content: str) -> Optional[str]:
        """YML 라인에서 값 부분만 추출"""
        line_no_comment = line_content.split('#', 1)[0]
        match = self.pattern_manager.get_pattern('yml_value').search(line_no_comment.rstrip())
        if match:
            return match.group(1)
        return None
    
    def _extract_yml_key(self, line_content: str) -> Optional[str]:
        """YML 라인에서 키(id) 부분 추출"""
        line_no_comment = line_content.split('#', 1)[0]
        if ':' in line_no_comment:
            return line_no_comment.split(':', 1)[0].strip()
        return None
    
    def _is_already_translated(self, text: str, target_lang: str, source_lang: str = "English") -> bool:
        """텍스트가 이미 대상 언어로 번역되었는지 확인"""
        if not text or not text.strip():
            return False
        
        # 특수 코드 제거
        cleaned_text = self._clean_text_for_language_detection(text)
        if not cleaned_text.strip():
            return False
        
        # 캐시 확인
        cache_key = (hash(text), target_lang, source_lang)
        if cache_key in self._translation_check_cache:
            return self._translation_check_cache[cache_key]
        
        # 원본 언어 감지
        is_source_lang = self._detect_language(cleaned_text, source_lang)
        # 대상 언어 감지
        is_target_lang = self._detect_language(cleaned_text, target_lang)
        
        # 번역 상태 판단
        result = is_target_lang and not is_source_lang
        
        # 캐시에 저장
        self._translation_check_cache[cache_key] = result
        return result
    
    def _detect_language(self, text: str, lang: str) -> bool:
        """텍스트의 언어 감지"""
        if not text or not text.strip():
            return False
        
        pattern = self.pattern_manager.get_language_pattern(lang)
        if not pattern:
            return False
        
        matches = pattern.findall(text)
        if not matches:
            return False
        
        # 언어별 특성에 따른 임계값 조정
        total_chars = len(text)
        language_chars = sum(len(match) for match in matches)
        
        if lang == 'Korean':
            # 한국어: 한글 문자의 비율
            return language_chars / total_chars > 0.3
        elif lang == 'English':
            # 영어: 영문 단어 수 기준
            words = text.split()
            english_words = len([w for w in words if pattern.match(w)])
            return english_words / len(words) > 0.6 if words else False
        else:
            # 기타 언어: 해당 언어 문자 비율
            return language_chars / total_chars > self.language_detection_threshold
    
    def _clean_text_for_language_detection(self, text: str) -> str:
        """언어 감지를 위한 텍스트 정리"""
        if not text:
            return ""
        
        # 특수 코드 제거 ($VAR$, [code], §색상§, £아이콘£ 등)
        special_pattern = self.pattern_manager.get_pattern('special_code')
        if special_pattern:
            text = special_pattern.sub('', text)
        
        # 숫자, 기호 제거
        text = re.sub(r'[0-9\s\.,;:\-!?()\\"\[\]{}]+', ' ', text)
        
        return text.strip()
    
    def calculate_translation_quality(self, original: str, translated: str) -> Dict[str, Any]:
        """번역 품질 계산"""
        if not original or not translated:
            return {'score': 0.0, 'issues': ['Empty text']}
        
        issues = []
        score = 100.0
        
        # 길이 비율 검사
        length_ratio = len(translated) / len(original)
        if length_ratio < 0.3:
            issues.append('Too short translation')
            score -= 30
        elif length_ratio > 3.0:
            issues.append('Too long translation')
            score -= 20
        
        # 특수 문자 보존 검사
        original_codes = re.findall(r'[\$\[\]§£][^$\[\]§£]*[\$\[\]§£]', original)
        translated_codes = re.findall(r'[\$\[\]§£][^$\[\]§£]*[\$\[\]§£]', translated)
        
        if len(original_codes) != len(translated_codes):
            issues.append('Special codes not preserved')
            score -= 25
        
        # 원본 언어 잔존 검사
        if self._detect_language(translated, "English") and "Korean" in str(type(self)):
            issues.append('Source language remnants detected')
            score -= 20
        
        return {
            'score': max(0.0, score),
            'issues': issues,
            'length_ratio': length_ratio,
            'special_codes_preserved': len(original_codes) == len(translated_codes)
        }
    
    def auto_fix_line(self, line: str) -> Tuple[str, List[str]]:
        """라인 자동 수정"""
        if not self.auto_fix_enabled:
            return line, []
        
        fixes_applied = []
        fixed_line = line
        
        # 따옴표 수정
        if line.count('"') % 2 != 0:
            # 마지막에 따옴표 추가
            if not line.rstrip().endswith('"'):
                fixed_line = line.rstrip() + '"'
                fixes_applied.append('Added missing closing quote')
        
        # 이스케이프 처리
        if '\\' not in fixed_line and '"' in fixed_line:
            # 값 내부의 따옴표 이스케이프
            value_match = re.search(r':\s*"([^"]*)"', fixed_line)
            if value_match:
                value = value_match.group(1)
                if '"' in value:
                    escaped_value = value.replace('"', '\\"')
                    fixed_line = fixed_line.replace(f'"{value}"', f'"{escaped_value}"')
                    fixes_applied.append('Escaped quotes in value')
        
        return fixed_line, fixes_applied
    
    def verify_translation_completeness(self, original_file_path: str, translated_file_path: str) -> Dict[str, Any]:
        """번역 완성도 검증"""
        try:
            with codecs.open(original_file_path, 'r', encoding='utf-8-sig') as f:
                original_lines = f.readlines()
            
            with codecs.open(translated_file_path, 'r', encoding='utf-8-sig') as f:
                translated_lines = f.readlines()
            
            if len(original_lines) != len(translated_lines):
                return {
                    'complete': False,
                    'issue': 'Line count mismatch',
                    'original_lines': len(original_lines),
                    'translated_lines': len(translated_lines)
                }
            
            missing_keys = []
            for i, (orig_line, trans_line) in enumerate(zip(original_lines, translated_lines)):
                orig_key = self._extract_yml_key(orig_line)
                trans_key = self._extract_yml_key(trans_line)
                
                if orig_key and orig_key != trans_key:
                    missing_keys.append({'line': i+1, 'original_key': orig_key, 'translated_key': trans_key})
            
            return {
                'complete': len(missing_keys) == 0,
                'missing_keys': missing_keys,
                'total_lines': len(original_lines),
                'issues_count': len(missing_keys)
            }
            
        except Exception as e:
            return {
                'complete': False,
                'issue': f'Verification error: {str(e)}'
            }
    
    def classify_error_type(self, line: str, value: str) -> str:
        """오류 유형 분류"""
        if not line or not value:
            return "empty"
        
        # YML 구문 오류
        if self._check_line_for_yml_errors_engine(line):
            return "yaml_syntax"
        
        # 정규식 오류
        if self._check_regex_errors_optimized(value):
            return "regex_error"
        
        # 언어 감지 오류 (원본 언어 잔존)
        if self._detect_language(value, "English"):
            return "source_remnant"
        
        return "unknown"


class DuplicateDetector:
    """중복 감지 및 처리"""
    
    def __init__(self):
        self.duplicate_strategy = "keep_first"  # keep_first, keep_last, keep_longest, keep_shortest
    
    def find_duplicates(self, lines: List[str]) -> Dict[str, List[int]]:
        """중복 키 찾기"""
        key_positions = {}
        
        for i, line in enumerate(lines):
            if ':' in line and not line.strip().startswith('#'):
                key = line.split(':', 1)[0].strip()
                if key in key_positions:
                    key_positions[key].append(i)
                else:
                    key_positions[key] = [i]
        
        # 중복된 것만 반환
        return {k: v for k, v in key_positions.items() if len(v) > 1}
    
    def resolve_duplicates(self, lines: List[str], duplicates: Dict[str, List[int]]) -> List[str]:
        """중복 해결"""
        result_lines = lines.copy()
        lines_to_remove = set()
        
        for key, positions in duplicates.items():
            if self.duplicate_strategy == "keep_first":
                lines_to_remove.update(positions[1:])
            elif self.duplicate_strategy == "keep_last":
                lines_to_remove.update(positions[:-1])
            elif self.duplicate_strategy == "keep_longest":
                longest_pos = max(positions, key=lambda i: len(lines[i]))
                lines_to_remove.update(pos for pos in positions if pos != longest_pos)
            elif self.duplicate_strategy == "keep_shortest":
                shortest_pos = min(positions, key=lambda i: len(lines[i]))
                lines_to_remove.update(pos for pos in positions if pos != shortest_pos)
        
        # 제거할 라인들을 마킹
        for i in sorted(lines_to_remove, reverse=True):
            result_lines[i] = None
        
        # None 제거
        return [line for line in result_lines if line is not None]