"""
Enhanced Translation Engine
G드라이브의 모든 기능을 통합한 완전한 번역 엔진
"""

import os
import re
import time
import threading
import codecs
import json
import tempfile
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path

# 새로운 모듈들 import
from .performance_engine import PerformanceOptimizer, RegexPatternManager, ConcurrentProcessor, ResourceManager
from .validation_engine import ValidationEngine, DuplicateDetector
from .prompt_glossary_engine import GamePromptManager
from .api_providers import APIProviderFactory
from .recovery_manager import TranslationRecovery
from .progress_tracker import ProgressTracker
from .file_processor import FileProcessor


class EnhancedTranslatorEngine:
    """향상된 번역 엔진 - 모든 기능 통합"""
    
    def __init__(self, log_callback: Callable, progress_callback: Callable, 
                 status_callback: Callable, stop_event: threading.Event, 
                 get_input_folder_callback: Callable):
        
        # 기본 콜백 및 이벤트
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.stop_event = stop_event
        self.get_input_folder_callback = get_input_folder_callback
        
        # 스레드 로컬 저장소
        self.thread_local = threading.local()
        
        # 모듈 초기화
        self.performance_optimizer = PerformanceOptimizer()
        self.pattern_manager = RegexPatternManager()
        self.validation_engine = ValidationEngine()
        self.duplicate_detector = DuplicateDetector()
        self.prompt_manager = GamePromptManager()
        self.concurrent_processor = ConcurrentProcessor(max_workers=8)
        self.resource_manager = ResourceManager()
        
        # 기존 컴포넌트들
        self.recovery_manager = TranslationRecovery()
        self.progress_tracker = ProgressTracker(progress_callback)
        self.file_processor = FileProcessor(log_callback)
        
        # API 관련
        self.current_api_provider = None
        
        # 설정 변수들
        self.api_key = None
        self.selected_model_name = None
        self.source_lang_for_api = "English"
        self.target_lang_for_api = "Korean"
        self.prompt_template_str = None
        self.glossary_str_for_prompt = None
        self.batch_size = 50
        self.max_tokens = 65536
        self.delay_between_batches = 0.8
        self.temperature = 0.5
        self.max_workers = 100
        self.max_retries = 3
        self.selected_game = None
        
        # 성능 설정
        self.skip_already_translated = False
        self.split_large_files_threshold = 1000
        self.enable_backup = False
        
        # 번역 상태
        self.translation_thread = None
        self.translated_files_info_for_review = []
        
        # 통계 및 콜백
        self.preview_callback = None
        self.stats_callback = None
        
        # 현재 파일 통계
        self.current_file_stats = {}
        self.current_file_start_time = None
    
    def __del__(self):
        """리소스 정리"""
        self.cleanup_resources()
    
    def cleanup_resources(self):
        """모든 리소스 정리"""
        try:
            if hasattr(self, 'stop_event'):
                self.stop_event.set()
            
            self.resource_manager.cleanup_resources()
            self.concurrent_processor.shutdown()
            self.performance_optimizer.cleanup_cache()
            
        except Exception as e:
            if self.log_callback:
                self.log_callback("Cleanup error", str(e))
    
    def set_api_provider(self, provider_type: str, api_key: str, model: str) -> bool:
        """API 제공자 설정"""
        try:
            self.api_key = api_key
            self.selected_model_name = model
            
            self.current_api_provider = APIProviderFactory.create_provider(
                provider_type, api_key, model
            )
            
            if self.current_api_provider:
                self.log_callback(f"API 프로바이더 설정 완료: {provider_type} ({model})")
                return True
            else:
                self.log_callback(f"API 프로바이더 설정 실패: {provider_type}")
                return False
                
        except Exception as e:
            self.log_callback(f"API 프로바이더 설정 중 오류: {e}")
            return False
    
    def validate_api_connection(self) -> bool:
        """API 연결 검증"""
        if not self.current_api_provider:
            return False
        
        try:
            return self.current_api_provider.validate_connection()
        except Exception as e:
            self.log_callback(f"API 연결 검증 실패: {e}")
            return False
    
    def start_translation_process(self, input_folder: str, output_folder: str,
                                source_lang: str, target_lang: str,
                                batch_size: int, max_workers: int,
                                prompt: str, glossary_content: str, **kwargs) -> bool:
        """번역 프로세스 시작"""
        if self.translation_thread and self.translation_thread.is_alive():
            self.log_callback("이미 번역이 진행 중입니다.")
            return False
        
        # 설정 업데이트
        self.source_lang_for_api = source_lang
        self.target_lang_for_api = target_lang
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.prompt_template_str = prompt
        self.glossary_str_for_prompt = glossary_content
        
        # 추가 설정 적용
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 정지 이벤트 초기화
        self.stop_event.clear()
        
        # 번역 스레드 시작
        self.translation_thread = threading.Thread(
            target=self._run_translation_process,
            args=(input_folder, output_folder),
            daemon=True
        )
        
        self.translation_thread.start()
        return True
    
    def _run_translation_process(self, input_folder: str, output_folder: str):
        """번역 프로세스 실행"""
        try:
            self.log_callback("번역 엔진이 초기화되었습니다.")
            
            if not self.current_api_provider:
                self.log_callback("API 제공자가 설정되지 않았습니다.")
                return
            
            self.log_callback(f"API 프로바이더 설정 완료: {self.current_api_provider.__class__.__name__}")
            
            # 파일 처리 시작
            self.log_callback("파일 프로세싱 시작...")
            
            # YAML 파일 찾기
            yaml_files = self._find_yaml_files(input_folder)
            
            if not yaml_files:
                self.log_callback("번역할 YAML 파일을 찾을 수 없습니다.")
                return
            
            total_size = sum(os.path.getsize(f) for f in yaml_files if os.path.exists(f))
            self.log_callback(f"{len(yaml_files)}개의 YAML 파일을 발견했습니다.")
            self.log_callback(f"발견된 파일: {len(yaml_files)}개 (총 {total_size/1024/1024:.1f}MB)")
            
            # 전체 번역 시작 시간
            translation_start_time = time.time()
            
            # G드라이브 방식으로 동시 처리
            completed_count = 0
            completed_lock = threading.Lock()
            
            def process_file(input_file):
                """단일 파일 처리 함수"""
                nonlocal completed_count
                
                try:
                    if self.stop_event.is_set():
                        return False
                    
                    # 상태 정보 전송
                    current_file = os.path.basename(input_file)
                    
                    self.status_callback("file_started", {
                        "current_file": current_file,
                        "total_files": len(yaml_files),
                        "completed_files": completed_count,
                        "progress": completed_count / len(yaml_files) * 100
                    })
                    
                    # 출력 파일 경로 생성
                    relative_path = os.path.relpath(input_file, input_folder)
                    output_file = os.path.join(output_folder, relative_path)
                    
                    # 출력 디렉토리 생성
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    
                    # 파일 처리
                    success = self._process_single_file_enhanced(input_file, output_file)
                    
                    # 완료 카운트 업데이트 (스레드 안전)
                    with completed_lock:
                        completed_count += 1
                        progress = completed_count / len(yaml_files) * 100
                        self.status_callback("file_completed", {
                            "current_file": current_file,
                            "total_files": len(yaml_files),
                            "completed_files": completed_count,
                            "progress": progress
                        })
                        
                        if self.progress_callback:
                            self.progress_callback(progress, f"완료: {current_file}")
                    
                    return success
                    
                except Exception as e:
                    self.log_callback(f"파일 처리 오류 {os.path.basename(input_file)}: {str(e)}")
                    return False
            
            # 실제 동시 처리 워커 수 계산 (G드라이브 방식)
            import concurrent.futures
            actual_max_workers = min(self.max_workers, len(yaml_files))
            self.log_callback(f"동시 처리 시작: {len(yaml_files)}개 파일, {actual_max_workers}개 워커")
            
            # ThreadPoolExecutor로 파일 레벨 동시 처리
            with concurrent.futures.ThreadPoolExecutor(max_workers=actual_max_workers) as executor:
                # 모든 파일 작업 제출
                future_to_file = {executor.submit(process_file, f): f for f in yaml_files}
                
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
                    except Exception as e:
                        self.log_callback(f"파일 스레드 오류 {os.path.basename(file_path)}: {str(e)}")
            
            # 완료 메시지
            if not self.stop_event.is_set():
                self.log_callback("모든 파일 번역 완료!")
            else:
                self.log_callback("사용자가 번역을 중지했습니다.")
                
                # 정교한 ETA 계산
                progress_info = self.progress_tracker.get_detailed_progress()
                eta_seconds = progress_info.get('eta', 0)
                
                if eta_seconds > 0:
                    remaining_minutes = int(eta_seconds // 60)
                    remaining_seconds = int(eta_seconds % 60)
                    confidence = progress_info.get('eta_confidence', 0) * 100
                    
                    time_message = f"파일 {i}/{len(yaml_files)} 완료 (예상 남은 시간: {remaining_minutes}분 {remaining_seconds}초, 신뢰도: {confidence:.0f}%)"
                else:
                    time_message = f"파일 {i}/{len(yaml_files)} 완료"
                
                self.progress_callback(completed_progress, time_message)
                
                if success:
                    self.log_callback(f"파일 번역 완료: {current_file}")
                    self.status_callback("file_completed", {
                        "current_file": current_file,
                        "completed_files": i,
                        "total_files": len(yaml_files)
                    })
                else:
                    self.log_callback(f"파일 번역 실패: {current_file}")
                    self.status_callback("file_failed", {
                        "current_file": current_file,
                        "error": "Translation failed"
                    })
            
            self.log_callback("모든 번역이 완료되었습니다.")
            
        except Exception as e:
            self.log_callback(f"번역 프로세스 오류: {str(e)}")
    
    def _find_yaml_files(self, folder: str) -> List[str]:
        """YAML 파일 찾기"""
        yaml_files = []
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.yml', '.yaml')):
                    yaml_files.append(os.path.join(root, file))
        
        return sorted(yaml_files)
    
    def _get_language_code(self, language: str) -> str:
        """언어명을 파일명/태그에 사용할 언어 코드로 변환 (Paradox 게임 표준)"""
        language_code_mapping = {
            "English": "english",
            "French": "french",
            "German": "german",
            "Japanese": "japanese", 
            "Korean": "korean",
            "Polish": "polish",
            "Portuguese": "braz_por",
            "Russian": "russian",
            "Chinese Simplified": "simp_chinese",
            "Spanish": "spanish",
            "Turkish": "turkish"
        }
        return language_code_mapping.get(language, language.lower())
    
    def _replace_language_in_filename(self, filename: str, source_lang: str, target_lang: str) -> str:
        """파일명의 언어 태그를 교체 (파일명 어디에 있어도 가능)"""
        source_code = self._get_language_code(source_lang)
        target_code = self._get_language_code(target_lang)
        
        # l_언어 패턴을 파일명 어디에서든 찾아 교체
        # 예: l_english_abs.yml, a_l_english_bs.yml, test_l_english.yml 등
        pattern = f"l_{source_code}"
        replacement = f"l_{target_code}"
        
        if pattern in filename:
            return filename.replace(pattern, replacement)
        
        return filename
    
    def _replace_language_tag_in_content(self, lines: List[str], source_lang: str, target_lang: str) -> List[str]:
        """파일 내용에서 첫 번째 언어 태그를 교체"""
        source_code = self._get_language_code(source_lang)
        target_code = self._get_language_code(target_lang)
        
        result_lines = []
        tag_replaced = False
        
        for line in lines:
            if not tag_replaced and f"l_{source_code}:" in line:
                # 첫 번째 l_언어: 태그를 교체
                modified_line = line.replace(f"l_{source_code}:", f"l_{target_code}:")
                result_lines.append(modified_line)
                tag_replaced = True
                self.log_callback(f"언어 태그 교체: l_{source_code}: → l_{target_code}:")
            else:
                result_lines.append(line)
        
        return result_lines
    
    def _process_single_file_enhanced(self, input_file: str, output_file: str) -> bool:
        """향상된 단일 파일 처리"""
        try:
            self._set_current_file_for_log(os.path.basename(input_file))
            
            # 언어 정의 파일 보존 옵션 확인
            keep_lang_def_unchanged = getattr(self, 'keep_lang_def_unchanged', False)
            
            # 출력 파일명에서 언어 태그 교체 (보존 옵션이 꺼져 있을 때만)
            original_output = output_file
            if not keep_lang_def_unchanged:
                output_file = self._replace_language_in_filename(
                    output_file, 
                    self.source_lang_for_api, 
                    self.target_lang_for_api
                )
                
                if original_output != output_file:
                    self.log_callback(f"파일명 언어 태그 교체: {os.path.basename(original_output)} → {os.path.basename(output_file)}")
                    # 출력 디렉토리 다시 생성
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # 파일 검증
            self.log_callback(f"파일 단계 1: 파일 존재 확인 - {input_file}")
            if not os.path.exists(input_file):
                self.log_callback(f"파일이 존재하지 않습니다: {input_file}")
                return False
            
            # 파일 읽기
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            # 번역 가능한 라인 확인
            valid_lines = [line for line in lines if self._is_valid_content_line(line)]
            if valid_lines:
                self.log_callback(f"번역 대상: {len(valid_lines)}줄")
            
            # 체크포인트 확인
            checkpoint_data = self.recovery_manager.load_checkpoint(input_file)
            if checkpoint_data:
                self.log_callback(f"체크포인트 발견 - 이어서 진행")
            
            # 파일이 너무 크면 청크로 분할
            if len(lines) > self.split_large_files_threshold:
                return self._process_large_file_in_chunks(input_file, output_file, lines)
            else:
                return self._process_normal_file(input_file, output_file, lines)
                
        except Exception as e:
            self.log_callback(f"파일 처리 오류: {str(e)}")
            return False
    
    def _process_normal_file(self, input_file: str, output_file: str, lines: List[str]) -> bool:
        """일반 크기 파일 처리"""
        try:
            # 번역 가능한 라인만 추출
            content_lines = []
            content_line_indices = []
            
            for i, line in enumerate(lines):
                if self._is_valid_content_line(line):
                    content_lines.append(line)
                    content_line_indices.append(i)
            
            if not content_lines:
                # 번역할 내용이 없으면 원본 복사
                with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
                    f.writelines(lines)
                return True
            
            # 배치 단위로 번역 처리
            translated_lines = []
            batch_size = self.performance_optimizer.get_optimal_batch_size()
            
            for i in range(0, len(content_lines), batch_size):
                if self.stop_event.is_set():
                    break
                
                batch = content_lines[i:i + batch_size]
                
                # 배치 번역
                start_time = time.time()
                translated_batch = self._translate_batch_enhanced(batch)
                processing_time = time.time() - start_time
                
                # 성능 기록
                success = len(translated_batch) == len(batch)
                self.performance_optimizer.record_batch_performance(success, len(batch), processing_time)
                
                translated_lines.extend(translated_batch)
                
                # 적응형 지연
                delay = self.performance_optimizer.calculate_adaptive_delay()
                time.sleep(delay)
            
            # 번역 결과를 원본 구조에 맞게 재구성
            result_lines = lines.copy()
            for i, translated_line in enumerate(translated_lines):
                if i < len(content_line_indices):
                    result_lines[content_line_indices[i]] = translated_line
            
            # 유효성 검증
            if hasattr(self, 'validation_level') and self.validation_level != "off":
                result_lines = self._validate_and_fix_lines(result_lines, lines)
            
            # 언어 태그 교체 (보존 옵션이 꺼져 있을 때만)
            keep_lang_def_unchanged = getattr(self, 'keep_lang_def_unchanged', False)
            if not keep_lang_def_unchanged:
                result_lines = self._replace_language_tag_in_content(
                    result_lines, 
                    self.source_lang_for_api, 
                    self.target_lang_for_api
                )
            
            # 결과 저장
            with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
                f.writelines(result_lines)
            
            # 체크포인트 제거
            self.recovery_manager.remove_checkpoint(input_file)
            
            return True
            
        except Exception as e:
            self.log_callback(f"파일 번역 오류: {str(e)}")
            return False
    
    def _process_large_file_in_chunks(self, input_file: str, output_file: str, lines: List[str]) -> bool:
        """대용량 파일 청크 처리"""
        chunk_size = self.split_large_files_threshold
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
        self.log_callback(f"대용량 파일: {len(chunks)}개 청크로 분할")
        
        all_translated_lines = []
        
        for chunk_idx, chunk_lines in enumerate(chunks):
            if self.stop_event.is_set():
                break
            
            # 청크 번역
            translated_chunk = self._process_normal_file_chunk(chunk_lines)
            all_translated_lines.extend(translated_chunk)
            
            # 진행률 업데이트
            progress = (chunk_idx + 1) / len(chunks) * 100
            if self.progress_callback:
                self.progress_callback(progress, f"청크 {chunk_idx + 1}/{len(chunks)} 완료")
        
        # 언어 태그 교체 (보존 옵션이 꺼져 있을 때만)
        keep_lang_def_unchanged = getattr(self, 'keep_lang_def_unchanged', False)
        if not keep_lang_def_unchanged:
            all_translated_lines = self._replace_language_tag_in_content(
                all_translated_lines, 
                self.source_lang_for_api, 
                self.target_lang_for_api
            )
        
        # 전체 결과 저장
        with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
            f.writelines(all_translated_lines)
        
        return True
    
    def _process_normal_file_chunk(self, lines: List[str]) -> List[str]:
        """청크 내 번역 처리"""
        content_lines = []
        content_line_indices = []
        
        for i, line in enumerate(lines):
            if self._is_valid_content_line(line):
                content_lines.append(line)
                content_line_indices.append(i)
        
        if not content_lines:
            return lines
        
        # 배치 번역 - 파일 레벨에서 이미 동시 처리하므로 순차 처리
        translated_lines = []
        batch_size = self.performance_optimizer.get_optimal_batch_size()
        
        for i in range(0, len(content_lines), batch_size):
            batch = content_lines[i:i + batch_size]
            translated_batch = self._translate_batch_enhanced(batch)
            translated_lines.extend(translated_batch)
        
        # 결과 재구성
        result_lines = lines.copy()
        for i, translated_line in enumerate(translated_lines):
            if i < len(content_line_indices):
                result_lines[content_line_indices[i]] = translated_line
        
        return result_lines
    
    def _translate_batch_enhanced(self, text_batch: List[str]) -> List[str]:
        """향상된 배치 번역"""
        if not text_batch:
            return []
        
        # 이미 번역된 라인 건너뛰기
        if self.skip_already_translated:
            batch_to_translate = []
            skip_indices = []
            
            for i, line in enumerate(text_batch):
                value = self._extract_yml_value(line)
                if value and self.validation_engine._is_already_translated(
                    value, self.target_lang_for_api, self.source_lang_for_api
                ):
                    skip_indices.append(i)
                else:
                    batch_to_translate.append(line)
            
            # 번역할 것이 없으면 원본 반환
            if not batch_to_translate:
                return text_batch
        else:
            batch_to_translate = text_batch
            skip_indices = []
        
        # 실제 번역 수행
        try:
            translated_batch = self._perform_api_translation(batch_to_translate)
            
            # 건너뛴 라인들 재삽입
            if skip_indices:
                result = text_batch.copy()
                translated_idx = 0
                
                for i in range(len(text_batch)):
                    if i not in skip_indices:
                        if translated_idx < len(translated_batch):
                            result[i] = translated_batch[translated_idx]
                            translated_idx += 1
                
                return result
            else:
                return translated_batch
                
        except Exception as e:
            self.log_callback(f"배치 번역 오류: {str(e)}")
            return text_batch
    
    def _perform_api_translation(self, text_batch: List[str]) -> List[str]:
        """실제 API 번역 수행 - G드라이브 방식으로 완전 개선"""
        if not self.current_api_provider:
            return text_batch
        
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                # 새로운 google.genai 클라이언트 방식 사용
                from google import genai
                
                if not hasattr(self, '_genai_client'):
                    self._genai_client = genai.Client(api_key=self.api_key)
                
                # 배치를 하나의 텍스트로 결합 (정확한 라인 구분 포함)
                batch_lines = []
                for line in text_batch:
                    clean_line = line.rstrip('\r\n')
                    batch_lines.append(clean_line)
                
                batch_text = "\n".join(batch_lines)
                
                # 게임별 프롬프트 가져오기
                game_prompt = self._get_game_specific_prompt()
                
                # 최종 프롬프트 구성 (영어로)
                final_prompt = f"""{game_prompt}

Source text:
{batch_text}

Please translate the above text from {self.source_lang_for_api} to {self.target_lang_for_api}.
CRITICAL RULES:
- Translate each line exactly, maintaining the same number of lines as the original
- Preserve YAML structure and formatting completely
- Do NOT translate keys, only translate values
- Keep variables ($VAR$), color tags (§), icons (£) unchanged
- Output ONLY the translated text, no explanations"""

                if self.glossary_str_for_prompt:
                    final_prompt += f"\n\nGlossary:\n{self.glossary_str_for_prompt}"

                # 새로운 API 호출 방식
                response = self._genai_client.models.generate_content(
                    model=self.selected_model_name,
                    contents=final_prompt,
                    config={
                        'temperature': self.temperature,
                        'max_output_tokens': 65536,
                        'top_k': 40,
                        'top_p': 0.95
                    }
                )
                
                # 새로운 응답 처리 방식
                if not hasattr(response, 'text') or not response.text:
                    self.log_callback("API 응답에 텍스트가 없습니다")
                    return text_batch
                
                translated_text = response.text.strip()
                
                if not translated_text.strip():
                    self.log_callback("빈 번역 결과를 받았습니다")
                    return text_batch
                
                # 마크다운 코드 블록 제거
                translated_text = re.sub(r'```(?:yaml|yml)?\s*\n?', '', translated_text, flags=re.IGNORECASE)
                translated_text = re.sub(r'\n?\s*```\s*', '', translated_text)
                translated_text = translated_text.strip()
                
                # 라인 분할
                result_lines = translated_text.split('\n')
                
                # 라인 수 검증 및 조정
                expected_lines = len(text_batch)
                actual_lines = len(result_lines)
                
                # 로그 레벨 조정: 중요한 정보만 표시
                if actual_lines != expected_lines:
                    self.log_callback(f"라인 수 조정: {actual_lines} → {expected_lines}")
                    
                    # 라인이 부족한 경우 원본으로 채움
                    while len(result_lines) < expected_lines:
                        missing_idx = len(result_lines)
                        if missing_idx < len(text_batch):
                            result_lines.append(text_batch[missing_idx].rstrip('\r\n'))
                        else:
                            result_lines.append("")
                    
                    # 라인이 초과한 경우 잘라냄
                    result_lines = result_lines[:expected_lines]
                
                # 개행 문자 추가하여 최종 결과 생성
                final_result = []
                for i, line in enumerate(result_lines):
                    # 원본 라인의 개행 패턴 유지
                    original_line = text_batch[i] if i < len(text_batch) else ""
                    if original_line.endswith('\r\n'):
                        final_result.append(line + '\r\n')
                    elif original_line.endswith('\n'):
                        final_result.append(line + '\n')
                    else:
                        final_result.append(line + '\n')  # 기본적으로 \n 추가
                
                # 성공한 배치만 로그 (스팸 감소)
                return final_result
                
            except Exception as e:
                self.log_callback(f"API 번역 오류 (시도 {retry_count + 1}/{self.max_retries + 1}): {str(e)}")
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    wait_time = min(self.delay_between_batches * retry_count, 5.0)
                    self.log_callback(f"{wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
        
        self.log_callback("모든 재시도 실패. 원본 텍스트 반환")
        return text_batch
    
    def _get_game_specific_prompt(self) -> str:
        """게임별 특화 프롬프트 반환"""
        if hasattr(self, 'prompt_template_str') and self.prompt_template_str:
            return self.prompt_template_str
        
        if hasattr(self, 'selected_game') and self.selected_game and self.selected_game != "None":
            # Game-specific prompts in English
            game_prompts = {
                "Hearts of Iron IV": "This is a Hearts of Iron IV mod translation. Please accurately translate military terms, country names, and place names.",
                "Europa Universalis IV": "This is a Europa Universalis IV mod translation. Please accurately translate historical terms and country names.",
                "Crusader Kings III": "This is a Crusader Kings III mod translation. Please appropriately translate medieval terms, personal names, and place names.",
                "Victoria 3": "This is a Victoria 3 mod translation. Please accurately translate 19th century terms and technology names.",
                "Stellaris": "This is a Stellaris mod translation. Please appropriately translate scientific terms and alien species names.",
                "Imperator Rome": "This is an Imperator Rome mod translation. Please accurately translate ancient Roman terms, personal names, and place names."
            }
            return game_prompts.get(self.selected_game, "This is a Paradox game mod translation.")
        
        return "This is a Paradox game mod translation."
    
    def _get_default_prompt(self) -> str:
        """기본 프롬프트 반환"""
        return """Please translate the following YML formatted text from '{source_lang_for_prompt}' to '{target_lang_for_prompt}'.
{glossary_section}
You MUST adhere to the following rules strictly:
1. Only translate the text enclosed in double quotes after a colon (:). (e.g., `key: "text to translate"`)
2. Do NOT translate code-like strings, variable names (e.g., `$variable$`, `[variable]`, `<variable>`), special tags (e.g., `§Y`, `£gold£`), file paths, or URLs.
3. **CRITICAL**: You MUST preserve all original newline characters (\\n) and leading whitespace (indentation) for each line. Do NOT change or remove them. Each translated line must retain its original line break.
4. Provide ONLY the translated text. Do NOT include any other explanations, headers, or footers.
5. For each input line, you MUST output exactly one translated line.

Text to translate:
```yaml
{batch_text}
```"""
    
    def _parse_translation_response(self, response_text: str, expected_lines: int) -> List[str]:
        """번역 응답 파싱"""
        if not response_text:
            return []
        
        # 코드 블록 제거
        if "```" in response_text:
            parts = response_text.split("```")
            if len(parts) >= 3:
                response_text = parts[1]
                # yaml 헤더 제거
                if response_text.startswith("yaml\n"):
                    response_text = response_text[5:]
                elif response_text.startswith("yml\n"):
                    response_text = response_text[4:]
        
        # 라인 분할 - 실제 개행 문자 사용
        lines = response_text.split('\n')
        
        # 빈 라인 제거 및 정리
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line:
                # 개행 문자 추가
                if not line.endswith('\n'):
                    line += '\n'
                cleaned_lines.append(line)
        
        # 예상된 라인 수와 일치하지 않으면 로그 출력
        if len(cleaned_lines) != expected_lines:
            self.log_callback(f"파싱된 라인 수: {len(cleaned_lines)}, 예상 라인 수: {expected_lines}")
            # 디버깅을 위해 원본 응답 일부 로그
            self.log_callback(f"응답 시작 부분: {response_text[:200]}...")
        
        return cleaned_lines
    
    def _validate_and_fix_lines(self, translated_lines: List[str], original_lines: List[str]) -> List[str]:
        """라인 유효성 검증 및 자동 수정"""
        fixed_lines = []
        
        for i, (trans_line, orig_line) in enumerate(zip(translated_lines, original_lines)):
            if self._is_valid_content_line(trans_line):
                # 유효성 검증
                if self.validation_engine._check_line_for_yml_errors_engine(trans_line):
                    # 자동 수정 시도
                    fixed_line, fixes = self.validation_engine.auto_fix_line(trans_line)
                    if fixes:
                        self.log_callback(f"라인 {i+1} 자동 수정: {', '.join(fixes)}")
                        fixed_lines.append(fixed_line)
                    else:
                        # 수정 실패시 원본 사용
                        fixed_lines.append(orig_line)
                else:
                    fixed_lines.append(trans_line)
            else:
                fixed_lines.append(trans_line)
        
        return fixed_lines
    
    def _is_valid_content_line(self, line: str) -> bool:
        """번역 가능한 컨텐츠 라인인지 확인"""
        if not line or not line.strip():
            return False
        
        stripped = line.strip()
        
        # 주석 라인
        if stripped.startswith('#'):
            return False
        
        # 키-값 쌍이 아닌 라인
        if ':' not in stripped:
            return False
        
        # l_language 라인
        if self.pattern_manager.get_pattern('lang_identifier').match(stripped):
            return False
        
        # 값이 따옴표로 둘러싸인 라인만
        if '"' not in stripped:
            return False
        
        return True
    
    def _extract_yml_value(self, line_content: str) -> Optional[str]:
        """YML 라인에서 값 부분만 추출"""
        return self.validation_engine._extract_yml_value(line_content)
    
    def _set_current_file_for_log(self, filename: str):
        """현재 처리 중인 파일명 설정 (스레드 안전)"""
        self.thread_local.current_file = filename
    
    def _get_current_file_for_log(self) -> str:
        """현재 처리 중인 파일명 가져오기"""
        if not hasattr(self.thread_local, 'current_file'):
            return ""
        return self.thread_local.current_file
    
    def request_stop_translation(self):
        """번역 중지 요청"""
        if self.stop_event:
            self.stop_event.set()
        
        if self.translation_thread and self.translation_thread.is_alive():
            self.translation_thread.join(timeout=5.0)
    
    def get_translation_statistics(self) -> Dict[str, Any]:
        """번역 통계 반환"""
        performance_stats = self.performance_optimizer.get_cache_stats()
        
        return {
            'performance': performance_stats,
            'files_processed': len(self.translated_files_info_for_review),
            'current_file': self._get_current_file_for_log(),
            'is_running': self.translation_thread and self.translation_thread.is_alive()
        }