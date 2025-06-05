# translator_project/translator_app/core/translator_engine.py
import os
import threading
import time
import codecs
import concurrent.futures
import google.generativeai as genai
import re
import tempfile
from ..utils.localization import get_language_code # localization.py의 get_language_code 사용

class TranslatorEngine:
    def __init__(self, log_callback, progress_callback, status_callback, stop_event, get_input_folder_callback):
        self.log_callback = log_callback
        self.main_progress_callback = progress_callback
        self.main_status_callback = status_callback
        self.stop_event = stop_event
        self.get_input_folder_callback = get_input_folder_callback

        self.current_processing_file_for_log = ""
        self.model = None
        self.translation_thread = None
        self.validation_thread = None

        self.api_key = None
        self.selected_model_name = None
        self.source_lang_for_api = None
        self.target_lang_for_api = None
        self.prompt_template_str = None
        self.glossary_str_for_prompt = None
        self.batch_size = 25
        self.max_tokens = 8192
        self.delay_between_batches = 0.8
        self.max_workers = 3
        self.keep_identifier = False
        self.check_internal_lang = False
        self.split_large_files_threshold = 0

        self.translated_files_info_for_review = []

        # 검증용 정규 표현식 - 요청하신 두 가지만 사용
        # 1. 올바른 YML 값 패턴
        self.regex_valid_yml_value_str = r'^[^"]*"([^"\\]|\\.)*$'

        # 2. 부적절한 선행 따옴표 패턴
        self.regex_error_improper_leading_quote_str = r'(?<![\r\n\t  ])"(?=[A-Za-z])'

        # 정규표현식 컴파일된 객체들 (성능 향상을 위해 미리 컴파일)
        self.compiled_regex_valid_yml_value = None
        self.compiled_regex_improper_leading_quote = None

        # 원본 언어(주로 영어) 잔존 의심 패턴 - 성능 개선된 버전
        # 더 정확한 영어 패턴: 최소 3글자 이상의 영어 단어가 2개 이상 연속으로 나오는 경우
        self.source_lang_heuristic_pattern_str = r'\b[a-zA-Z]{3,}(?:\s+[a-zA-Z]{2,})+\b'
        self.compiled_source_lang_pattern = None
        
        # 성능 향상을 위한 캐시
        self._source_remnant_cache = {}
        self._regex_error_cache = {}

    def _initialize_model(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.selected_model_name)
            self.log_callback("log_model_start", self.selected_model_name)
            return True
        except Exception as e:
            self.log_callback("log_api_model_init_fail", str(e))
            return False

    def _extract_yml_value(self, line_content):
        """YML 라인에서 값 부분만 추출"""
        line_no_comment = line_content.split('#', 1)[0]
        match = re.search(r':\s*"(.*)"\s*$', line_no_comment.rstrip())
        if match:
            return match.group(1)
        return None


    def _check_regex_errors_optimized(self, value_text):
        """정규식 오류 검사 - 수정된 버전"""
        if not value_text:
            return False
            
        # 캐시 확인
        cache_key = hash(value_text)
        if cache_key in self._regex_error_cache:
            return self._regex_error_cache[cache_key]
        
        has_error = False
        
        try:
            # 패턴 1: ^[^"]*"([^"\\]|\\.)*$ - 매치되면 오류
            yml_pattern = r'^[^"]*"([^"\\]|\\.)*$'
            full_line = f'key: "{value_text}"'
            if re.match(yml_pattern, full_line):
                has_error = True
            
            # 패턴 2: (?<![\r\n\t  ])"(?=[A-Za-z]) - 매치되면 오류
            if not has_error:
                improper_quote_pattern = r'(?<![\r\n\t  ])"(?=[A-Za-z])'
                if re.search(improper_quote_pattern, value_text):
                    has_error = True
                    
        except re.error:
            has_error = False
        
        # 캐시에 저장
        if len(self._regex_error_cache) < 1000:
            self._regex_error_cache[cache_key] = has_error
        
        return has_error

    def _check_line_for_yml_errors_engine(self, full_line):
        """엔진용 전체 라인 YML 문법 오류 검사 - 수정된 버전"""
        if not full_line or not full_line.strip():
            return False
        
        # 주석 제거
        line_without_comment = full_line.split('#')[0].strip()
        if not line_without_comment:
            return False
        
        try:
            # 콜론이 있는 라인만 검사
            if ':' not in line_without_comment:
                return False
            
            parts = line_without_comment.split(':', 1)
            if len(parts) != 2:
                return False
            
            key_part = parts[0].strip()
            value_part = parts[1].strip()
            
            if not key_part:
                return False
            
            # 값이 없거나 숫자/불린값이면 건너뛰기
            if not value_part or re.match(r'^(true|false|null|\d+|\d*\.\d+)$', value_part.lower()):
                return False
            
            # 패턴 1: ^[^"]*"([^"\\]|\\.)*$ - 매치되면 오류
            pattern = r'^[^"]*"([^"\\]|\\.)*$'
            if re.match(pattern, line_without_comment):
                return True
            
            # 패턴 2: (?<![\r\n\t  ])"(?=[A-Za-z]) - 매치되면 오류
            improper_quote_pattern = r'(?<![\r\n\t  ])"(?=[A-Za-z])'
            if re.search(improper_quote_pattern, value_part):
                return True
            
        except Exception:
            pass
        
        return False

    def _check_line_for_yml_errors(self, full_line):
        """전체 라인에서 YML 문법 오류 검사 - 수정된 버전"""
        if not full_line or not full_line.strip():
            return False
        
        # 주석 제거
        line_without_comment = full_line.split('#')[0].strip()
        if not line_without_comment:
            return False
        
        try:
            # 콜론이 있는 라인만 검사
            if ':' not in line_without_comment:
                return False
            
            parts = line_without_comment.split(':', 1)
            if len(parts) != 2:
                return False
            
            key_part = parts[0].strip()
            value_part = parts[1].strip()
            
            if not key_part:
                return False
            
            # 값이 없거나 숫자/불린값이면 건너뛰기
            if not value_part or re.match(r'^(true|false|null|\d+|\d*\.\d+)$', value_part.lower()):
                return False
            
            # 패턴 1: ^[^"]*"([^"\\]|\\.)*$ - 매치되면 오류
            pattern = r'^[^"]*"([^"\\]|\\.)*$'
            if re.match(pattern, line_without_comment):
                print(f"패턴1 오류 검출: {full_line.strip()}")
                return True
            
            # 패턴 2: (?<![\r\n\t  ])"(?=[A-Za-z]) - 매치되면 오류
            improper_quote_pattern = r'(?<![\r\n\t  ])"(?=[A-Za-z])'
            if re.search(improper_quote_pattern, value_part):
                print(f"패턴2 오류 검출: {full_line.strip()}")
                return True
            
        except Exception as e:
            print(f"검사 중 예외: {e}")
            return False
        
        return False

    def _check_source_remnants_optimized(self, value_text, original_lines, line_index):
        """원본 언어 잔존 검사 - 영어 단어 1개 이상"""
        if not value_text:
            return False
        
        try:
            clean_text = value_text.strip()
            
            # 1. 너무 짧은 텍스트나 숫자/특수문자만 있는 경우 제외
            if re.fullmatch(r'^[0-9\W_]{1,3}$', clean_text) or len(clean_text) <= 2:
                return False
            
            # 2. 영어 단어가 1개 이상 있는지 확인
            english_words = [w for w in clean_text.split() if re.match(r'[a-zA-Z]{2,}', w)]
            if len(english_words) < 1:
                return False
            
            # 3. 원본과 비교하여 정확히 동일한지 확인
            if line_index < len(original_lines):
                orig_value = self._extract_yml_value(original_lines[line_index])
                if orig_value and orig_value.strip().lower() == clean_text.lower():
                    return True  # 원본과 동일 = 번역되지 않음
            else:
                # 원본이 없는 경우에도 영어 단어가 있으면 의심
                return True
                                
        except:
            pass
        
        return False

    def _translate_batch_core(self, text_batch, temperature=0.2):
        batch_text_content = "\n".join([line.rstrip('\n') for line in text_batch])
        try:
            final_prompt = self.prompt_template_str.format(
                source_lang_for_prompt=self.source_lang_for_api,
                target_lang_for_prompt=self.target_lang_for_api,
                glossary_section=self.glossary_str_for_prompt,
                batch_text=batch_text_content
            )
        except KeyError as e:
            self.log_callback("log_batch_unknown_error", self.current_processing_file_for_log, f"Prompt formatting error (KeyError: {e}).")
            return [line if line.endswith('\n') else line + '\n' for line in text_batch]

        try:
            if self.stop_event.is_set():
                return [line if line.endswith('\n') else line + '\n' for line in text_batch]

            response = self.model.generate_content(
                final_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=self.max_tokens
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
                self.log_callback("log_batch_prompt_blocked", self.current_processing_file_for_log, response.prompt_feedback.block_reason)
                return [line if line.endswith('\n') else line + '\n' for line in text_batch]

            if finish_reason_val not in [0, 1]: 
                if finish_reason_val == 2: 
                    self.log_callback("log_batch_token_limit", self.current_processing_file_for_log, finish_reason_val)
                    if len(text_batch) > 1:
                        mid = len(text_batch) // 2
                        first_half = self._translate_batch_core(text_batch[:mid], temperature)
                        if self.stop_event.is_set(): return [line + '\n' for line in text_batch] 
                        second_half = self._translate_batch_core(text_batch[mid:], temperature)
                        return first_half + second_half
                    else:
                        self.log_callback("log_batch_single_line_token_limit", self.current_processing_file_for_log)
                        return [line if line.endswith('\n') else line + '\n' for line in text_batch]
                else: 
                    reason_str = f"Reason Code: {finish_reason_val}"
                    if candidate and candidate.safety_ratings:
                        safety_str = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in candidate.safety_ratings])
                        reason_str += f" (Safety: {safety_str})"
                    self.log_callback("log_batch_abnormal_termination", self.current_processing_file_for_log, reason_str)
                    return [line if line.endswith('\n') else line + '\n' for line in text_batch]

            if not translated_text.strip():
                self.log_callback("log_batch_empty_response", self.current_processing_file_for_log)
                return [line if line.endswith('\n') else line + '\n' for line in text_batch]

            if translated_text.startswith("```yaml\n"): translated_text = translated_text[len("```yaml\n"):]
            if translated_text.endswith("\n```"): translated_text = translated_text[:-len("\n```")]
            if translated_text.startswith("```\n"): translated_text = translated_text[len("```\n"):]
            if translated_text.endswith("```"): translated_text = translated_text[:-len("```")]

            translated_lines_raw = translated_text.split('\n')
            processed_lines = []

            for i in range(len(text_batch)):
                if i < len(translated_lines_raw):
                    api_translated_line = translated_lines_raw[i]
                    original_line_content = text_batch[i]
                    original_ends_with_newline = original_line_content.endswith('\n')

                    if original_ends_with_newline and not api_translated_line.endswith('\n'):
                        processed_lines.append(api_translated_line + '\n')
                    elif not original_ends_with_newline and api_translated_line.endswith('\n'):
                        processed_lines.append(api_translated_line.rstrip('\n'))
                    else:
                        processed_lines.append(api_translated_line) 
                else: 
                    self.log_callback("log_batch_line_mismatch", self.current_processing_file_for_log, "Translated lines less than original, padding with original.")
                    processed_lines.append(text_batch[i]) 
            
            if len(translated_lines_raw) > len(text_batch):
                 self.log_callback("log_batch_line_mismatch", self.current_processing_file_for_log, "Translated lines more than original, truncating.")
            return processed_lines

        except Exception as e:
            if self.stop_event.is_set():
                return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            error_str = str(e).lower()
            if ("token" in error_str and ("limit" in error_str or "exceeded" in error_str or "max" in error_str)) or \
               ("429" in error_str) or ("resource has been exhausted" in error_str) or \
               ("quota" in error_str) or ("rate limit" in error_str) or ("rpm" in error_str and "limit" in error_str) or \
               ("user_location" in error_str and "blocked" in error_str) or ("permission_denied" in error_str):
                self.log_callback("log_batch_api_limit_error_split", self.current_processing_file_for_log, str(e))
                if len(text_batch) > 1:
                    mid = len(text_batch) // 2
                    first_half = self._translate_batch_core(text_batch[:mid], temperature)
                    if self.stop_event.is_set(): return [line + '\n' for line in text_batch]
                    second_half = self._translate_batch_core(text_batch[mid:], temperature)
                    return first_half + second_half
                else:
                    self.log_callback("log_batch_single_line_api_limit", self.current_processing_file_for_log)
                    return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            self.log_callback("log_batch_unknown_error", self.current_processing_file_for_log, str(e))
            return [line if line.endswith('\n') else line + '\n' for line in text_batch]

    def get_language_code(self, lang_name_en_from_ui):
        return get_language_code(lang_name_en_from_ui)

    def get_translated_files_info(self):
        return self.translated_files_info_for_review

    def _process_single_file_core(self, input_file, output_file):
        self.current_processing_file_for_log = os.path.basename(input_file)
        try:
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            if not lines:
                self.log_callback("log_file_empty", self.current_processing_file_for_log)
                return
            total_lines = len(lines)

            if self.split_large_files_threshold > 0 and total_lines > self.split_large_files_threshold:
                self.log_callback("log_file_split_start", self.current_processing_file_for_log, total_lines, self.split_large_files_threshold)
                self._process_large_file_in_chunks(input_file, output_file, lines)
                return

            translated_lines_final = []
            self.log_callback("log_file_process_start", self.current_processing_file_for_log, total_lines)
            start_index = 0
            first_line_lang_pattern = re.compile(r"^\s*l_([a-zA-Z_]+)\s*:", re.IGNORECASE)

            if self.check_internal_lang and lines:
                first_line_match_check = first_line_lang_pattern.match(lines[0])
                source_lang_code_from_ui = self.get_language_code(self.source_lang_for_api)
                if first_line_match_check:
                    actual_lang_code_in_file = first_line_match_check.group(1).lower()
                    if actual_lang_code_in_file != source_lang_code_from_ui:
                        self.log_callback("log_internal_lang_mismatch_using_ui", self.current_processing_file_for_log, f"l_{actual_lang_code_in_file}", f"l_{source_lang_code_from_ui}")
                else:
                    self.log_callback("log_internal_lang_no_identifier_using_ui", self.current_processing_file_for_log, f"l_{source_lang_code_from_ui}")

            first_line_match_for_change = first_line_lang_pattern.match(lines[0]) if lines else None
            if first_line_match_for_change:
                original_first_line_content = lines[0]
                original_lang_identifier_in_file = first_line_match_for_change.group(0).strip()
                if self.keep_identifier:
                    translated_lines_final.append(original_first_line_content)
                    self.log_callback("log_first_line_keep")
                else:
                    target_lang_code_str = self.get_language_code(self.target_lang_for_api)
                    new_first_line_content = first_line_lang_pattern.sub(f"l_{target_lang_code_str}:", original_first_line_content, count=1)
                    translated_lines_final.append(new_first_line_content)
                    self.log_callback("log_first_line_change", original_lang_identifier_in_file, f"l_{target_lang_code_str}:")
                start_index = 1

            if start_index >= total_lines:
                if first_line_match_for_change:
                    self.log_callback("log_file_only_identifier", self.current_processing_file_for_log)
                else:
                    self.log_callback("log_file_no_content_to_translate", self.current_processing_file_for_log)
                if translated_lines_final:
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
                        f.writelines(translated_lines_final)
                    self.log_callback("log_translation_complete_save", os.path.basename(output_file))
                    if not self.stop_event.is_set():
                         self.translated_files_info_for_review.append({"original": input_file, "translated": output_file})
                return

            content_lines_to_translate = lines[start_index:]
            for i in range(0, len(content_lines_to_translate), self.batch_size):
                if self.stop_event.is_set():
                    self.log_callback("log_file_process_stopped", self.current_processing_file_for_log)
                    return
                batch_to_translate = content_lines_to_translate[i:i + self.batch_size]
                current_line_in_original_file = start_index + i + 1
                end_line_in_original_file = start_index + min(i + self.batch_size, len(content_lines_to_translate))
                self.log_callback("log_batch_translate", current_line_in_original_file, end_line_in_original_file, total_lines)
                
                translated_batch_lines = self._translate_batch_core(batch_to_translate)
                translated_lines_final.extend(translated_batch_lines)
                
                if i + self.batch_size < len(content_lines_to_translate) and not self.stop_event.is_set() and self.delay_between_batches > 0:
                    time.sleep(self.delay_between_batches)

            if self.stop_event.is_set(): return

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with codecs.open(output_file, 'w', encoding='utf-8-sig') as f:
                f.writelines(translated_lines_final)
            self.log_callback("log_translation_complete_save", os.path.basename(output_file))
            if not self.stop_event.is_set():
                self.translated_files_info_for_review.append({"original": input_file, "translated": output_file})
        except Exception as e:
            if not self.stop_event.is_set():
                self.log_callback("log_file_process_error", self.current_processing_file_for_log, str(e))
        finally:
            self.current_processing_file_for_log = ""

    def _process_large_file_in_chunks(self, original_input_file_path, final_output_file_path, all_lines):
        chunk_size = self.split_large_files_threshold
        num_chunks = (len(all_lines) + chunk_size - 1) // chunk_size
        translated_chunk_content_files = []
        temp_dir = ""
        try:
            temp_dir = tempfile.mkdtemp(prefix="translator_chunk_")
            self.log_callback("log_temp_dir_created", temp_dir)

            first_line_content_for_final_output = None 
            first_line_lang_pattern = re.compile(r"^\s*l_([a-zA-Z_]+)\s*:", re.IGNORECASE)
            original_first_line = all_lines[0] if all_lines else ""
            first_line_match_in_original = first_line_lang_pattern.match(original_first_line)

            if first_line_match_in_original:
                if self.keep_identifier:
                    first_line_content_for_final_output = original_first_line
                else:
                    target_lang_code_str = self.get_language_code(self.target_lang_for_api)
                    first_line_content_for_final_output = first_line_lang_pattern.sub(f"l_{target_lang_code_str}:", original_first_line, count=1)
            
            content_start_index_in_original = 1 if first_line_match_in_original else 0
            actual_content_lines = all_lines[content_start_index_in_original:]

            def translate_chunk(index, chunk_lines):
                translated_current_chunk_content = []
                for batch_start in range(0, len(chunk_lines), self.batch_size):
                    if self.stop_event.is_set():
                        break
                    batch_to_translate = chunk_lines[batch_start: batch_start + self.batch_size]
                    if not batch_to_translate:
                        continue
                    original_log_filename = self.current_processing_file_for_log
                    self.current_processing_file_for_log = f"{os.path.basename(original_input_file_path)} (chunk {index+1})"
                    translated_batch = self._translate_batch_core(batch_to_translate)
                    translated_current_chunk_content.extend(translated_batch)
                    self.current_processing_file_for_log = original_log_filename
                    if batch_start + self.batch_size < len(chunk_lines) and not self.stop_event.is_set() and self.delay_between_batches > 0:
                        time.sleep(self.delay_between_batches)

                if self.stop_event.is_set():
                    return None
                temp_chunk_output_content_file = os.path.join(temp_dir, f"chunk_{index}_translated_content.yml")
                with codecs.open(temp_chunk_output_content_file, 'w', encoding='utf-8-sig') as f_out_content:
                    f_out_content.writelines(translated_current_chunk_content)
                return temp_chunk_output_content_file

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_index = {}
                for i in range(num_chunks):
                    if self.stop_event.is_set():
                        break
                    chunk_start = i * chunk_size
                    chunk_end = min((i + 1) * chunk_size, len(actual_content_lines))
                    chunk_lines = actual_content_lines[chunk_start:chunk_end]
                    if not chunk_lines:
                        continue
                    self.log_callback("log_processing_chunk", i + 1, num_chunks, f"{os.path.basename(original_input_file_path)} part {i+1}")
                    fut = executor.submit(translate_chunk, i, chunk_lines)
                    future_to_index[fut] = i

                for fut in concurrent.futures.as_completed(future_to_index):
                    if self.stop_event.is_set():
                        break
                    result_file = fut.result()
                    if result_file:
                        translated_chunk_content_files.append((future_to_index[fut], result_file))

            if not self.stop_event.is_set() and len(translated_chunk_content_files) == num_chunks:
                self.log_callback("log_merging_chunks", final_output_file_path)
                os.makedirs(os.path.dirname(final_output_file_path), exist_ok=True)
                with codecs.open(final_output_file_path, 'w', encoding='utf-8-sig') as f_final:
                    if first_line_content_for_final_output:
                        f_final.write(first_line_content_for_final_output)
                    for _, chunk_content_file in sorted(translated_chunk_content_files, key=lambda x: x[0]):
                        with codecs.open(chunk_content_file, 'r', encoding='utf-8-sig') as f_chunk_read:
                            f_final.writelines(f_chunk_read.readlines())
                self.log_callback("log_translation_complete_save", os.path.basename(final_output_file_path))
                if not self.stop_event.is_set():
                     self.translated_files_info_for_review.append({"original": original_input_file_path, "translated": final_output_file_path})

            elif self.stop_event.is_set():
                self.log_callback("log_chunk_processing_stopped", self.current_processing_file_for_log)
            else:
                 self.log_callback("log_chunk_processing_failed", self.current_processing_file_for_log)
        finally:
            if temp_dir and os.path.isdir(temp_dir):
                try:
                    for f_name in os.listdir(temp_dir):
                        f_path = os.path.join(temp_dir, f_name)
                        if os.path.isfile(f_path): os.remove(f_path)
                    os.rmdir(temp_dir)
                    self.log_callback("log_temp_dir_removed", temp_dir)
                except Exception as e_clean:
                    self.log_callback("log_temp_dir_remove_fail", temp_dir, str(e_clean))

    def _translation_worker_thread_target(self, input_dir, output_dir):
        self.translated_files_info_for_review.clear()
        completed_count = 0
        total_files_to_process = 0

        if not self._initialize_model():
            self.main_status_callback("status_waiting", task_type="translation")
            return

        try:
            target_files = []
            source_lang_code_for_search = self.get_language_code(self.source_lang_for_api).lower()
            if self.keep_identifier:
                detected_identifier = None
                for root_path, _, files_in_dir in os.walk(input_dir):
                    if self.stop_event.is_set():
                        break
                    for file_name in files_in_dir:
                        match = re.search(r"l_[a-zA-Z_]+", file_name.lower())
                        if match:
                            detected_identifier = match.group(0)
                            break
                    if detected_identifier or self.stop_event.is_set():
                        break
                file_identifier_for_search = detected_identifier or "l_english"
            else:
                file_identifier_for_search = f"l_{source_lang_code_for_search}"
            self.log_callback("log_search_yml_files", file_identifier_for_search)

            for root_path, _, files_in_dir in os.walk(input_dir):
                if self.stop_event.is_set():
                    break
                for file_name in files_in_dir:
                    if self.stop_event.is_set():
                        break
                    if file_identifier_for_search in file_name.lower() and file_name.lower().endswith(('.yml', '.yaml')):
                        target_files.append(os.path.join(root_path, file_name))
                if self.stop_event.is_set():
                    break

            if not target_files and source_lang_code_for_search != "english":
                for root_path, _, files_in_dir in os.walk(input_dir):
                    if self.stop_event.is_set():
                        break
                    for file_name in files_in_dir:
                        if self.stop_event.is_set():
                            break
                        lower_name = file_name.lower()
                        if 'l_english' in lower_name and lower_name.endswith(('.yml', '.yaml')):
                            target_files.append(os.path.join(root_path, file_name))
                    if self.stop_event.is_set():
                        break

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

            def process_single_file_wrapper_for_thread(input_f):
                if self.stop_event.is_set(): return None
                relative_path = os.path.relpath(input_f, input_dir)
                output_f_path = os.path.join(output_dir, relative_path)

                if not self.keep_identifier:
                    base_name = os.path.basename(output_f_path)
                    dir_name = os.path.dirname(output_f_path)
                    identifier_to_replace_in_filename = f"l_{source_lang_code_for_search}"
                    new_target_identifier_for_filename = f"l_{target_lang_code_for_filename_output}"
                    new_base_name, num_replacements = re.subn(
                        re.escape(identifier_to_replace_in_filename),
                        new_target_identifier_for_filename,
                        base_name,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    if num_replacements > 0 and new_base_name != base_name:
                        self.log_callback("log_output_filename_change", base_name, new_base_name)
                        output_f_path = os.path.join(dir_name, new_base_name)
                
                self._process_single_file_core(input_f, output_f_path)
                return os.path.basename(input_f) if not self.stop_event.is_set() else None

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(process_single_file_wrapper_for_thread, f): f
                    for f in target_files if not self.stop_event.is_set()
                }
                for future in concurrent.futures.as_completed(future_to_file):
                    if self.stop_event.is_set():
                        for f_cancel in future_to_file.keys():
                            if not f_cancel.done(): f_cancel.cancel()
                        break
                    try:
                        completed_filename = future.result()
                        if completed_filename:
                            completed_count += 1
                            self.log_callback("log_file_completed", completed_filename)
                            progress_value = completed_count / total_files_to_process if total_files_to_process > 0 else 0
                            self.main_progress_callback(completed_count, total_files_to_process, progress_value, "translation")
                    except concurrent.futures.CancelledError:
                        if future_to_file.get(future):
                            self.log_callback("log_file_task_cancelled", os.path.basename(future_to_file[future]))
                    except Exception as exc:
                        if future_to_file.get(future):
                            self.log_callback("log_parallel_process_error", os.path.basename(future_to_file[future]), str(exc))
            
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
            elif completed_count == total_files_to_process and total_files_to_process > 0 :
                self.main_status_callback("status_completed_all", completed_count, total_files_to_process, task_type=task_type)
            else:
                self.main_status_callback("status_completed_some", completed_count, total_files_to_process, task_type=task_type)
            self.current_processing_file_for_log = ""

    def start_translation_process(self, api_key, selected_model_name,
                                  input_folder, output_folder,
                                  source_lang_api, target_lang_api,
                                  prompt_template, glossary_content,
                                  batch_size_val, max_tokens_val, delay_val, max_workers_val,
                                  keep_identifier_val, check_internal_lang_val,
                                  split_large_files_threshold):
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
        self.max_workers = max_workers_val
        self.keep_identifier = keep_identifier_val
        self.check_internal_lang = check_internal_lang_val
        self.split_large_files_threshold = split_large_files_threshold

        # 캐시 초기화
        self._regex_error_cache.clear()
        self._source_remnant_cache.clear()

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

    def _validation_worker_thread_target(self, output_dir, check_regex, check_source_lang,
                                         validation_results_display_callback,
                                         source_lang_ui_selected,
                                         validation_progress_callback,
                                         validation_status_callback):
        self.stop_event.clear()
        found_issues_details = []
        task_type = "validation"

        # 캐시 초기화
        self._regex_error_cache.clear()
        self._source_remnant_cache.clear()

        if not os.path.isdir(output_dir):
            results_data = [{"message_key": "validation_no_output_folder"}]
            validation_results_display_callback(results_data)
            validation_status_callback("validation_status_no_output_folder_selected", task_type=task_type)
            return

        files_to_validate = []
        for root, _, files in os.walk(output_dir):
            if self.stop_event.is_set(): break
            for file in files:
                if self.stop_event.is_set(): break
                if file.lower().endswith(('.yml', '.yaml')):
                    files_to_validate.append(os.path.join(root, file))
            if self.stop_event.is_set(): break
        
        if self.stop_event.is_set():
            validation_results_display_callback([{"message_key": "log_translation_stopped_by_user"}])
            validation_status_callback("status_stopped", task_type=task_type)
            return

        if not files_to_validate:
            validation_results_display_callback([{"message_key": "validation_no_files_in_output"}])
            validation_status_callback("validation_status_no_files_to_validate", task_type=task_type)
            return

        # 정규식 컴파일 (검사 시에만)
        if check_regex:
            try:
                self.compiled_regex_valid_yml_value = re.compile(self.regex_valid_yml_value_str)
                self.compiled_regex_improper_leading_quote = re.compile(self.regex_error_improper_leading_quote_str)
            except Exception as e:
                self.log_callback("log_regex_compile_error", f"Regex patterns: {e}")
                check_regex = False
        
        # 원본 언어 패턴 컴파일
        if check_source_lang:
            try:
                self.compiled_source_lang_pattern = re.compile(self.source_lang_heuristic_pattern_str)
            except Exception as e:
                self.log_callback("log_regex_compile_error", f"Source heuristic pattern: {e}")
                check_source_lang = False

        input_folder_path = self.get_input_folder_callback()

        for idx, translated_filepath in enumerate(files_to_validate):
            if self.stop_event.is_set(): break
            validation_progress_callback(idx + 1, len(files_to_validate), (idx + 1) / len(files_to_validate), task_type)
            self.current_processing_file_for_log = os.path.basename(translated_filepath)

            # 원본 파일 찾기 (원본 언어 잔존 검사용)
            original_filepath = None
            if check_source_lang and input_folder_path:
                matched_original_info = next((info for info in self.translated_files_info_for_review 
                                            if info["translated"] == translated_filepath), None)
                if matched_original_info:
                    original_filepath = matched_original_info["original"]
                else:
                    # 파일명 기반으로 원본 파일 추정
                    fname = os.path.basename(translated_filepath)
                    try:
                        current_target_lang_l_code = f"l_{self.get_language_code(self.target_lang_for_api).lower()}"
                        original_source_lang_l_code = f"l_{self.get_language_code(source_lang_ui_selected).lower()}"
                        if current_target_lang_l_code in fname.lower():
                            original_fname_stem = fname.lower().replace(current_target_lang_l_code, original_source_lang_l_code)
                            relative_dir = os.path.dirname(os.path.relpath(translated_filepath, output_dir))
                            potential_original_path_stem = os.path.splitext(original_fname_stem)[0]
                            search_dir = os.path.join(input_folder_path, relative_dir)
                            if os.path.isdir(search_dir):
                                for f_glob_name in os.listdir(search_dir):
                                    if os.path.splitext(f_glob_name)[0].lower() == potential_original_path_stem:
                                        original_filepath = os.path.join(search_dir, f_glob_name)
                                        break
                    except Exception: 
                        pass

            # 원본 파일 읽기
            original_lines = []
            if original_filepath and os.path.exists(original_filepath):
                try:
                    with codecs.open(original_filepath, 'r', encoding='utf-8-sig') as f_org:
                        original_lines = f_org.readlines()
                except Exception as e_org:
                     self.log_callback("log_file_process_error", os.path.basename(original_filepath), 
                                     f" (Original file read error for validation: {e_org})")

            # 번역 파일 읽기 및 검사
            try:
                with codecs.open(translated_filepath, 'r', encoding='utf-8-sig') as f_trans:
                    translated_lines = f_trans.readlines()
            except Exception as e_trans:
                found_issues_details.append({
                    "file": os.path.basename(translated_filepath), "line_num": "N/A",
                    "type_key": "validation_error_file_read", "message_detail": f"File read error: {e_trans}",
                    "original": "", "translated": ""
                })
                continue

            for line_num, translated_line_content in enumerate(translated_lines):
                if self.stop_event.is_set(): break
                current_original_line_stripped = original_lines[line_num].strip() if line_num < len(original_lines) else ""
                translated_value = self._extract_yml_value(translated_line_content)

                if check_regex:
                    # 전체 라인으로 정규식 오류 검사
                    if self._check_line_for_yml_errors_engine(translated_line_content):
                        found_issues_details.append({
                            "file": os.path.basename(translated_filepath), "line_num": line_num + 1,
                            "type_key": "validation_error_regex", "message_detail": "YML syntax error",
                            "original": current_original_line_stripped, 
                            "translated": translated_line_content.strip()
                        })
                        continue  # 한 라인에 여러 오류 중 하나만 보고

                if check_source_lang and translated_value is not None:
                    if self._check_source_remnants_optimized(translated_value, original_lines, line_num):
                        found_issues_details.append({
                            "file": os.path.basename(translated_filepath), "line_num": line_num + 1,
                            "type_key": "validation_error_source_lang_remaining",
                            "original": current_original_line_stripped,
                            "translated": translated_line_content.strip()
                        })
                if self.stop_event.is_set(): break
        
        if not self.stop_event.is_set() and not found_issues_details:
            found_issues_details.append({"message_key": "validation_no_issues_found"})
        elif self.stop_event.is_set():
            found_issues_details.append({"message_key": "log_translation_stopped_by_user"})

        validation_results_display_callback(found_issues_details)
        final_status_key = "validation_completed" if not self.stop_event.is_set() else "status_stopped"
        validation_status_callback(final_status_key, task_type=task_type)

    def start_validation_process(self, output_dir, check_regex, check_source_lang,
                                 validation_results_display_callback, source_lang_ui_selected,
                                 validation_progress_callback, validation_status_callback):
        if self.validation_thread and self.validation_thread.is_alive():
            self.log_callback("warn_already_validating")
            return False
        if self.translation_thread and self.translation_thread.is_alive():
            self.log_callback("warn_already_translating")
            return False

        self.stop_event.clear()
        validation_status_callback("validation_running", task_type="validation")

        self.validation_thread = threading.Thread(
            target=self._validation_worker_thread_target,
            args=(output_dir, check_regex, check_source_lang,
                  validation_results_display_callback, source_lang_ui_selected,
                  validation_progress_callback, validation_status_callback),
            daemon=True
        )
        self.validation_thread.start()
        return True

    def request_stop_validation(self):
        if self.validation_thread and self.validation_thread.is_alive():
            self.log_callback("log_stop_requested")
            self.stop_event.set()
            return True
        return False