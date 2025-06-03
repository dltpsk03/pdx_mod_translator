import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import os
import threading
import time
import codecs
import concurrent.futures
import google.generativeai as genai
import re
import tkinter as tk
import sys
import json # 설정 저장/로드용

# --- 언어별 UI 텍스트 및 메시지 (이전과 동일하게 유지) ---
LANGUAGES = {
    "ko": {
        "title": "패독겜 모드번역기 v0.3",
        "ui_settings_frame_title": "UI 설정",
        "ui_lang_label": "UI 언어:", "ui_lang_tooltip": "프로그램 인터페이스의 표시 언어를 변경합니다.",
        "appearance_mode_label": "테마 모드:", "dark_mode": "어둡게", "light_mode": "밝게", "system_mode": "시스템 기본",
        "api_settings_frame": "API 및 모델 설정",
        "api_key_label": "Gemini API 키:", "api_key_tooltip": "Google AI Studio에서 발급받은 Gemini API 키를 입력하세요.\n예: AIzaSy...",
        "model_label": "번역 모델:", "model_tooltip": "번역에 사용할 Gemini 모델을 선택합니다.\n모델마다 성능과 비용이 다를 수 있습니다.",
        "folder_frame": "폴더 선택",
        "input_folder_label": "입력 폴더:", "input_folder_tooltip": "번역할 원본 YML 파일들이 들어있는 폴더를 선택하세요.",
        "browse_button": "찾아보기", "input_browse_tooltip": "입력 폴더를 선택하는 탐색기를 엽니다.",
        "output_folder_label": "출력 폴더:", "output_folder_tooltip": "번역된 YML 파일들을 저장할 폴더를 선택하세요.",
        "output_browse_tooltip": "출력 폴더를 선택하는 탐색기를 엽니다.",
        "lang_settings_frame": "번역 언어 설정 (API 요청용)",
        "source_content_lang_label": "원본 내용 언어:", "source_content_lang_tooltip": "YML 파일 내 텍스트의 실제 원본 언어를 선택합니다.\nAPI에 이 정보를 전달하여 번역 품질을 높입니다.",
        "target_trans_lang_label": "번역 대상 언어:", "target_trans_lang_tooltip": "텍스트를 어떤 언어로 번역할지 선택합니다.\n출력 파일의 언어 식별자(l_korean 등)도 이 설정에 따라 변경될 수 있습니다.",
        "detailed_settings_frame": "번역 상세 설정",
        "batch_size_label": "배치 크기:", "batch_size_tooltip": "한 번에 API로 보내 번역할 텍스트 라인(줄)의 수입니다.\n너무 크면 API가 응답하지 않거나 오류가 발생할 수 있습니다.",
        "concurrent_files_label": "동시 파일 수:", "concurrent_files_tooltip": "여러 파일을 동시에 번역할 때, 한 번에 몇 개까지 병렬로 처리할지 설정합니다.\n컴퓨터 성능에 따라 조절하세요.",
        "max_output_tokens_label": "최대 출력 토큰:", "max_output_tokens_tooltip": "번역 결과물(텍스트)의 최대 길이를 토큰 단위로 제한합니다.\n선택한 모델의 최대 토큰 한도를 넘지 않도록 주의하세요.",
        "batch_delay_label": "배치 간 대기(초):", "batch_delay_tooltip": "각 번역 배치 요청 사이에 얼마 동안 대기할지 설정합니다 (초 단위).\nAPI의 분당 요청 한도를 초과하지 않도록 돕습니다.",
        "keep_identifier_label": "l_english 식별자 원본 유지", "keep_identifier_tooltip": "체크 시: 파일 첫 줄의 'l_english:' 및 파일명의 'l_english' 부분을 변경하지 않고 그대로 둡니다.\n체크 해제 시: '번역 대상 언어'에 맞춰 변경합니다 (예: l_korean).",
        "check_internal_lang_label": "파일명과 다른 내부 언어일 경우 UI 설정 우선",
        "check_internal_lang_tooltip": "체크 시: 파일명이나 파일 첫 줄의 언어 식별자와 UI '원본 내용 언어' 설정이 다를 경우, UI 설정을 우선하여 번역 API에 전달합니다.\n(예: l_english 파일이지만 내용은 중국어일 때, UI 원본을 중국어로 설정하면 중국어로 간주)\n로그에 관련 정보가 기록됩니다.",
        "prompt_glossary_frame_title": "프롬프트 및 용어집 관리",
        "prompt_edit_frame_title": "프롬프트 편집",
        "prompt_edit_textbox_tooltip": "번역 API에 전달될 프롬프트입니다.\n{source_lang_for_prompt}, {target_lang_for_prompt}, {glossary_section}, {batch_text} 플레이스홀더는 유지해야 합니다.",
        "load_prompt_button": "파일에서 불러오기", "load_prompt_button_tooltip": "텍스트 파일에서 프롬프트를 불러옵니다.",
        "save_prompt_button": "파일에 저장", "save_prompt_button_tooltip": "현재 프롬프트를 텍스트 파일에 저장합니다.",
        "reset_prompt_button": "기본값 복원", "reset_prompt_button_tooltip": "프롬프트를 프로그램 기본값으로 되돌립니다.",
        "prompt_file_load_title": "프롬프트 파일 불러오기",
        "prompt_file_save_title": "프롬프트 파일 저장",
        "glossary_management_frame_title": "용어집 관리",
        "add_glossary_button": "용어집 추가", "add_glossary_button_tooltip": "새 용어집 파일을 목록에 추가합니다.",
        "remove_glossary_button": "선택 용어집 제거", "remove_glossary_button_tooltip": "목록에서 선택된 용어집 파일을 제거합니다.",
        "glossary_list_tooltip": "활성화된 용어집 목록입니다. 번역에 사용됩니다.",
        "glossary_file_select_title": "용어집 파일 선택",
        "glossary_item_loaded": "로드됨: {0} ({1}개 항목)", "glossary_item_error": "오류: {0}", "glossary_item_empty": "비어있음: {0}",
        "log_prompt_loaded_from_custom": "사용자 정의 프롬프트를 사용합니다.",
        "log_prompt_loaded_from_file": "파일 '{0}'에서 프롬프트를 로드했습니다.",
        "log_prompt_saved_to_file": "프롬프트가 파일 '{0}'에 저장되었습니다.",
        "log_prompt_reset_to_default": "프롬프트가 기본값으로 복원되었습니다.",
        "log_glossary_added": "용어집 '{0}' 추가됨.", "log_glossary_removed": "용어집 '{0}' 제거됨.",
        "log_combined_glossary_empty": "병합된 용어집이 비어있습니다.",
        "log_combined_glossary_info": "병합된 용어집에서 {0}개 유효 항목을 사용합니다.",
        "translate_button": "번역 시작", "translate_button_tooltip": "입력된 설정으로 모든 대상 파일의 번역을 시작합니다.",
        "stop_button": "중지", "stop_button_tooltip": "현재 진행 중인 번역 작업을 중지합니다.\n(이미 시작된 배치는 완료될 수 있습니다)",
        "progress_frame": "진행 상황",
        "status_waiting": "대기 중...", "status_translating": "번역 중...", "status_preparing": "번역 준비 중...",
        "status_completed_all": "모든 파일 번역 완료 ({0}/{1} 처리)", "status_stopped": "번역 중지됨 ({0}/{1} 처리)",
        "status_completed_some": "번역 완료됨 ({0}/{1} 처리)", "status_no_files": "처리할 YML 파일을 찾지 못했습니다.",
        "log_frame": "실행 로그", "error_title": "오류", "warn_title": "경고", "info_title": "정보",
        "error_api_key_needed": "Gemini API 키를 입력해야 합니다.", "error_model_needed": "번역 모델을 선택해야 합니다.",
        "error_input_folder_invalid": "올바른 입력 폴더를 선택해야 합니다.", "error_output_folder_needed": "출력 폴더를 선택해야 합니다.",
        "error_numeric_setting_invalid": "숫자 설정값이 올바르지 않습니다. 유효한 숫자를 입력해주세요.",
        "warn_already_translating": "이미 번역 작업이 진행 중입니다. 기다려 주십시오.", "info_no_translation_active": "현재 진행 중인 번역 작업이 없습니다.",
        "error_create_output_folder": "출력 폴더를 만들 수 없습니다: {0}",
        "log_api_model_init_fail": "API 또는 모델 초기화에 실패했습니다: {0}", "log_model_start": "'{0}' 모델을 사용하여 번역을 시작합니다.",
        "log_search_yml_files": "입력 폴더에서 파일명에 '{0}' 문자열을 포함하는 YML 파일을 찾고 있습니다...", "log_no_yml_files_found": "입력 폴더 '{0}'에서 파일명에 '{1}'을(를) 포함하는 YML 파일을 찾지 못했습니다.",
        "log_total_files_start": "총 {0}개의 파일을 번역합니다.", "log_file_empty": "파일 '{0}'이(가) 비어있어 건너<0xE1><0xB9><0xA5>니다.",
        "log_file_process_start": "파일 '{0}' ({1}줄) 번역을 시작합니다.", "log_first_line_keep": "  파일 첫 줄의 'l_english:' 식별자를 원본 그대로 유지합니다.",
        "log_first_line_change": "  파일 첫 줄 식별자를 '{0}'에서 '{1}'(으)로 변경합니다.", "log_file_only_identifier": "  파일 '{0}'은(는) 식별자 라인만 포함하고 있어, 내용 번역은 건너<0xE1><0xB9><0xA5>니다.",
        "log_file_no_content_to_translate": "  파일 '{0}'에 번역할 내용이 없습니다.", "log_batch_translate": "  텍스트 일부 번역 중: {0}~{1} / 총 {2}줄",
        "log_translation_complete_save": "번역 완료! 파일 '{0}'(으)로 저장되었습니다.", "log_file_process_error": "파일 '{0}' 처리 중 오류 발생: {1}",
        "log_output_filename_change": "  출력 파일명을 '{0}'에서 '{1}'(으)로 변경합니다.", "log_file_task_cancelled": "파일 '{0}' 번역 작업이 취소되었습니다.",
        "log_parallel_process_error": "파일 '{0}' 병렬 처리 중 오류 발생: {1}", "log_all_translation_done": "모든 파일의 번역 작업이 완료되었습니다!",
        "log_translation_stopped_by_user": "사용자에 의해 번역 작업이 중지되었습니다.", "log_translation_process_error": "번역 작업 중 전체 오류 발생: {0}",
        "log_stop_requested": "번역 중지 요청됨...", "ui_lang_self_name": "한국어",
        "log_batch_prompt_blocked": "파일 '{0}', 배치 처리: API 프롬프트가 차단되었습니다 (이유: {1}). 원본 내용을 반환합니다.", "log_batch_token_limit": "파일 '{0}', 배치 처리: API 출력 토큰 한계에 도달했습니다 (사유 코드: {1}). 배치를 나눠 다시 시도합니다.",
        "log_batch_single_line_token_limit": "파일 '{0}', 배치 처리: 한 줄의 내용도 토큰 한계를 초과합니다. 원본 내용을 반환합니다.", "log_batch_abnormal_termination": "파일 '{0}', 배치 처리: 번역이 비정상적으로 종료되었습니다 ({1}). 원본 내용을 반환합니다.",
        "log_batch_empty_response": "파일 '{0}', 배치 처리: API로부터 빈 응답을 받았습니다. 원본 내용을 반환합니다.", "log_batch_line_mismatch": "파일 '{0}', 배치 처리: 번역된 줄 수가 원본과 다릅니다. 부족한 부분은 원본으로 채웁니다.",
        "log_batch_api_limit_error_split": "파일 '{0}', 배치 처리: API 요청 제한 관련 오류 발생 ({1}). 배치를 나눠 다시 시도합니다.", "log_batch_single_line_api_limit": "파일 '{0}', 배치 처리: 한 줄의 내용도 API 요청 제한 오류가 발생했습니다. 원본 내용을 반환합니다.",
        "log_batch_unknown_error": "파일 '{0}', 배치 처리 중 알 수 없는 오류 발생: {1}", "log_file_process_stopped": "파일 '{0}' 처리 중 번역이 중지되었습니다.",
        "log_file_completed": "파일 번역 완료: {0}", "status_translating_progress": "번역 진행 중... ({0}/{1})",
        "log_no_yml_files_found_short": "파일 없음", "log_search_yml_files_short": "파일 검색 중...",
        "status_stopped_short": "중지됨", "status_completed_some_short": "완료됨", "status_completed_all_short": "모두 완료",
        "log_internal_lang_mismatch_using_ui": "파일 '{0}'의 첫 줄 식별자 '{1}'(은)는 UI에서 설정한 원본 언어 '{2}'와 다릅니다. UI 설정을 사용하여 번역합니다.",
        "log_internal_lang_no_identifier_using_ui": "파일 '{0}'에서 언어 식별자를 찾을 수 없습니다. UI에서 설정한 원본 언어 '{1}'을(를) 사용하여 번역합니다.",
        "prompt_template_file_label": "프롬프트 템플릿 파일:",
        "prompt_template_file_tooltip": "API에 전달할 번역 지침이 담긴 텍스트 파일입니다.\n(기본값: 프로그램 폴더 내 'prompt_template.txt')",
        "prompt_file_status_ok": "'{0}' 사용 중",
        "prompt_file_status_default": "기본 프롬프트 사용 중",
        "prompt_file_status_error": "파일 오류! 기본 프롬프트 사용",
        "glossary_file_label": "용어집 파일 (선택):",
        "glossary_file_tooltip": "번역 시 참고할 고유명사 목록이 담긴 텍스트 파일입니다.\n한 줄에 '영어단어:번역단어' 형식으로 작성하세요.",
        "browse_glossary_button_tooltip": "용어집 파일을 선택하는 탐색기를 엽니다.",
        "glossary_file_status_ok": "'{0}' ({1}개 항목) 사용 중",
        "glossary_file_status_not_used": "용어집 사용 안 함",
        "glossary_file_status_empty": "용어집 비어있음",
        "select_glossary_file_title": "용어집 파일 선택",
        "log_prompt_file_loaded": "프롬프트 템플릿 파일 '{0}'에서 로드했습니다.",
        "log_prompt_file_not_found_using_default": "프롬프트 템플릿 파일 '{0}'을(를) 찾을 수 없어 내장된 기본 프롬프트를 사용합니다.",
        "log_prompt_file_error_using_default": "프롬프트 템플릿 파일 '{0}' 로드 중 오류 ({1}). 내장된 기본 프롬프트를 사용합니다.",
        "log_glossary_loaded": "용어집 파일 '{0}'에서 {1}개 항목을 로드했습니다.",
        "log_glossary_not_selected_or_empty": "용어집 파일이 선택되지 않았거나 비어있어 사용하지 않습니다.",
        "log_glossary_error": "용어집 파일 '{0}' 로드 중 오류: {1}"
    },
    "en": {
        "title": "Paradox Game Mod Translator v0.3",
        "ui_settings_frame_title": "UI Settings",
        "ui_lang_label": "UI Language:", "ui_lang_tooltip": "Changes the display language of the program interface.",
        "appearance_mode_label": "Theme Mode:", "dark_mode": "Dark", "light_mode": "Light", "system_mode": "System Default",
        "api_settings_frame": "API and Model Settings",
        "api_key_label": "Gemini API Key:", "api_key_tooltip": "Enter the Gemini API key issued from Google AI Studio.\nExample: AIzaSy...",
        "model_label": "Translation Model:", "model_tooltip": "Select the Gemini model to use for translation.\nPerformance and cost may vary by model.",
        "folder_frame": "Folder Selection",
        "input_folder_label": "Input Folder:", "input_folder_tooltip": "Select the folder containing the original YML files to be translated.",
        "browse_button": "Browse", "input_browse_tooltip": "Opens a file explorer to select the input folder.",
        "output_folder_label": "Output Folder:", "output_folder_tooltip": "Select the folder to save the translated YML files.",
        "output_browse_tooltip": "Opens a file explorer to select the output folder.",
        "lang_settings_frame": "Translation Language Settings (for API request)",
        "source_content_lang_label": "Source Content Language:", "source_content_lang_tooltip": "Select the actual source language of the text within the YML files.\nThis information is passed to the API to improve translation quality.",
        "target_trans_lang_label": "Target Translation Language:", "target_trans_lang_tooltip": "Select the language to translate the text into.\nThe language identifier in the output file (e.g., l_korean) may also change based on this setting.",
        "detailed_settings_frame": "Detailed Translation Settings",
        "batch_size_label": "Batch Size:", "batch_size_tooltip": "The number of text lines to send to the API for translation at once.\nIf too large, the API may not respond or an error may occur.",
        "concurrent_files_label": "Concurrent Files:", "concurrent_files_tooltip": "When translating multiple files concurrently, set how many to process in parallel at once.\nAdjust according to your computer's performance.",
        "max_output_tokens_label": "Max Output Tokens:", "max_output_tokens_tooltip": "Limits the maximum length of the translated text in tokens.\nBe careful not to exceed the maximum token limit of the selected model.",
        "batch_delay_label": "Delay Between Batches (sec):", "batch_delay_tooltip": "Sets how long to wait between each translation batch request (in seconds).\nHelps prevent exceeding the API's requests per minute limit.",
        "keep_identifier_label": "Keep original l_english identifier", "keep_identifier_tooltip": "Checked: Keeps the 'l_english:' in the first line of the file and 'l_english' in the filename unchanged.\nUnchecked: Changes it according to the 'Target Translation Language' (e.g., l_korean).",
        "check_internal_lang_label": "Prioritize UI setting if internal language differs from filename",
        "check_internal_lang_tooltip": "Checked: If the language identifier in the filename or first line differs from the UI 'Source Content Language' setting, the UI setting is prioritized for the translation API.\n(e.g., If an l_english file actually contains Chinese text, and the UI source is set to Chinese, it's treated as Chinese).\nRelevant information will be logged.",
        "prompt_glossary_frame_title": "Prompt & Glossary Management",
        "prompt_edit_frame_title": "Edit Prompt",
        "prompt_edit_textbox_tooltip": "This is the prompt that will be sent to the translation API.\nThe placeholders {source_lang_for_prompt}, {target_lang_for_prompt}, {glossary_section}, {batch_text} must be maintained.",
        "load_prompt_button": "Load from File", "load_prompt_button_tooltip": "Loads the prompt from a text file.",
        "save_prompt_button": "Save to File", "save_prompt_button_tooltip": "Saves the current prompt to a text file.",
        "reset_prompt_button": "Restore Default", "reset_prompt_button_tooltip": "Resets the prompt to the program's default value.",
        "prompt_file_load_title": "Load Prompt File",
        "prompt_file_save_title": "Save Prompt File",
        "glossary_management_frame_title": "Glossary Management",
        "add_glossary_button": "Add Glossary", "add_glossary_button_tooltip": "Adds a new glossary file to the list.",
        "remove_glossary_button": "Remove Selected Glossary", "remove_glossary_button_tooltip": "Removes the selected glossary file from the list.",
        "glossary_list_tooltip": "List of active glossaries. Used for translation.",
        "glossary_file_select_title": "Select Glossary File",
        "glossary_item_loaded": "Loaded: {0} ({1} items)", "glossary_item_error": "Error: {0}", "glossary_item_empty": "Empty: {0}",
        "log_prompt_loaded_from_custom": "Using custom prompt.",
        "log_prompt_loaded_from_file": "Prompt loaded from file '{0}'.",
        "log_prompt_saved_to_file": "Prompt saved to file '{0}'.",
        "log_prompt_reset_to_default": "Prompt reset to default.",
        "log_glossary_added": "Glossary '{0}' added.", "log_glossary_removed": "Glossary '{0}' removed.",
        "log_combined_glossary_empty": "Combined glossary is empty.",
        "log_combined_glossary_info": "Using {0} valid items from the combined glossary.",
        "translate_button": "Start Translation", "translate_button_tooltip": "Starts translating all target files with the entered settings.",
        "stop_button": "Stop", "stop_button_tooltip": "Stops the currently ongoing translation process.\n(Batches already started may complete)",
        "progress_frame": "Progress",
        "status_waiting": "Waiting...", "status_translating": "Translating...", "status_preparing": "Preparing for translation...",
        "status_completed_all": "All files translated ({0}/{1} processed)", "status_stopped": "Translation stopped ({0}/{1} processed)",
        "status_completed_some": "Translation completed ({0}/{1} processed)", "status_no_files": "No YML files found to process.",
        "log_frame": "Execution Log", "error_title": "Error", "warn_title": "Warning", "info_title": "Information",
        "error_api_key_needed": "Gemini API key is required.", "error_model_needed": "A translation model must be selected.",
        "error_input_folder_invalid": "A valid input folder must be selected.", "error_output_folder_needed": "An output folder must be selected.",
        "error_numeric_setting_invalid": "Numeric setting is invalid. Please enter a valid number.",
        "warn_already_translating": "Translation is already in progress. Please wait.", "info_no_translation_active": "No translation process is currently active.",
        "error_create_output_folder": "Could not create output folder: {0}",
        "log_api_model_init_fail": "API or model initialization failed: {0}", "log_model_start": "Starting translation using '{0}' model.",
        "log_search_yml_files": "Searching for YML files containing '{0}' in their filename in the input folder...", "log_no_yml_files_found": "No YML files containing '{1}' in their filename found in input folder '{0}'.",
        "log_total_files_start": "Translating a total of {0} files.", "log_file_empty": "File '{0}' is empty, skipping.",
        "log_file_process_start": "Starting translation of file '{0}' ({1} lines).", "log_first_line_keep": "  Keeping the 'l_english:' identifier in the first line of the file as original.",
        "log_first_line_change": "  Changing the first line identifier from '{0}' to '{1}'.", "log_file_only_identifier": "  File '{0}' only contains the identifier line, skipping content translation.",
        "log_file_no_content_to_translate": "  File '{0}' has no content to translate.", "log_batch_translate": "  Translating text batch: lines {0}~{1} / total {2} lines",
        "log_translation_complete_save": "Translation complete! Saved to file '{0}'.", "log_file_process_error": "Error processing file '{0}': {1}",
        "log_output_filename_change": "  Changing output filename from '{0}' to '{1}'.", "log_file_task_cancelled": "Translation task for file '{0}' was cancelled.",
        "log_parallel_process_error": "Error during parallel processing of file '{0}': {1}", "log_all_translation_done": "Translation of all files completed!",
        "log_translation_stopped_by_user": "Translation process stopped by user.", "log_translation_process_error": "Global error during translation process: {0}",
        "log_stop_requested": "Stop translation requested...", "ui_lang_self_name": "English",
        "log_batch_prompt_blocked": "File '{0}', batch processing: API prompt blocked (reason: {1}). Returning original content.", "log_batch_token_limit": "File '{0}', batch processing: API output token limit reached (reason code: {1}). Splitting batch and retrying.",
        "log_batch_single_line_token_limit": "File '{0}', batch processing: Single line content exceeds token limit. Returning original content.", "log_batch_abnormal_termination": "File '{0}', batch processing: Translation terminated abnormally ({1}). Returning original content.",
        "log_batch_empty_response": "File '{0}', batch processing: Received empty response from API. Returning original content.", "log_batch_line_mismatch": "File '{0}', batch processing: Translated line count differs from original. Missing lines filled with original content.",
        "log_batch_api_limit_error_split": "File '{0}', batch processing: API request limit error ({1}). Splitting batch and retrying.", "log_batch_single_line_api_limit": "File '{0}', batch processing: Single line content caused API request limit error. Returning original content.",
        "log_batch_unknown_error": "File '{0}', unknown error during batch processing: {1}", "log_file_process_stopped": "Translation stopped while processing file '{0}'.",
        "log_file_completed": "File translation completed: {0}", "status_translating_progress": "Translating... ({0}/{1})",
        "log_no_yml_files_found_short": "No files", "log_search_yml_files_short": "Searching files...",
        "status_stopped_short": "Stopped", "status_completed_some_short": "Completed", "status_completed_all_short": "All Done",
        "log_internal_lang_mismatch_using_ui": "The first line identifier '{1}' in file '{0}' differs from the source language '{2}' set in the UI. Translating using UI setting.",
        "log_internal_lang_no_identifier_using_ui": "Cannot find language identifier in file '{0}'. Translating using source language '{1}' set in UI.",
        "prompt_template_file_label": "Prompt Template File:",
        "prompt_template_file_tooltip": "Text file containing translation instructions for the API.\n(Default: 'prompt_template.txt' in the program folder)",
        "prompt_file_status_ok": "Using '{0}'",
        "prompt_file_status_default": "Using default prompt",
        "prompt_file_status_error": "File error! Using default prompt",
        "glossary_file_label": "Glossary File (Optional):",
        "glossary_file_tooltip": "Text file containing a list of proper nouns for reference during translation.\nWrite in 'EnglishWord:TranslatedWord' format per line.",
        "browse_glossary_button_tooltip": "Opens a file explorer to select a glossary file.",
        "glossary_file_status_ok": "Using '{0}' ({1} items)",
        "glossary_file_status_not_used": "Glossary not used",
        "glossary_file_status_empty": "Glossary empty",
        "select_glossary_file_title": "Select Glossary File",
        "log_prompt_file_loaded": "Loaded from prompt template file '{0}'.",
        "log_prompt_file_not_found_using_default": "Prompt template file '{0}' not found. Using built-in default prompt.",
        "log_prompt_file_error_using_default": "Error loading prompt template file '{0}' ({1}). Using built-in default prompt.",
        "log_glossary_loaded": "Loaded {1} items from glossary file '{0}'.",
        "log_glossary_not_selected_or_empty": "Glossary file not selected or empty. Not using.",
        "log_glossary_error": "Error loading glossary file '{0}': {1}"
    },
    "zh_CN": {
        "title": "P社游戏模组翻译器 v0.3",
        "ui_settings_frame_title": "界面设置",
        "ui_lang_label": "界面语言：", "ui_lang_tooltip": "更改程序界面的显示语言。",
        "appearance_mode_label": "主题模式：", "dark_mode": "深色", "light_mode": "浅色", "system_mode": "系统默认",
        "api_settings_frame": "API 及模型设置",
        "api_key_label": "Gemini API 密钥：", "api_key_tooltip": "请输入从 Google AI Studio 获取的 Gemini API 密钥。\n例如：AIzaSy...",
        "model_label": "翻译模型：", "model_tooltip": "选择用于翻译的 Gemini 模型。\n不同模型的性能和成本可能有所不同。",
        "folder_frame": "文件夹选择",
        "input_folder_label": "输入文件夹：", "input_folder_tooltip": "选择包含待翻译的原始 YML 文件的文件夹。",
        "browse_button": "浏览", "input_browse_tooltip": "打开文件浏览器以选择输入文件夹。",
        "output_folder_label": "输出文件夹：", "output_folder_tooltip": "选择用于保存已翻译 YML 文件的文件夹。",
        "output_browse_tooltip": "打开文件浏览器以选择输出文件夹。",
        "lang_settings_frame": "翻译语言设置 (用于 API 请求)",
        "source_content_lang_label": "源内容语言：", "source_content_lang_tooltip": "选择 YML 文件内文本的实际源语言。\n此信息将传递给 API 以提高翻译质量。",
        "target_trans_lang_label": "目标翻译语言：", "target_trans_lang_tooltip": "选择要将文本翻译成的语言。\n输出文件的语言标识符（例如 l_korean）也可能根据此设置更改。",
        "detailed_settings_frame": "翻译详细设置",
        "batch_size_label": "批处理大小：", "batch_size_tooltip": "一次发送到 API 进行翻译的文本行数。\n如果设置过大，API 可能无响应或发生错误。",
        "concurrent_files_label": "并发文件数：", "concurrent_files_tooltip": "同时翻译多个文件时，设置一次并行处理的文件数量。\n请根据您的计算机性能进行调整。",
        "max_output_tokens_label": "最大输出令牌数：", "max_output_tokens_tooltip": "以令牌为单位限制翻译结果（文本）的最大长度。\n请注意不要超过所选模型的最大令牌限制。",
        "batch_delay_label": "批次间延迟（秒）：", "batch_delay_tooltip": "设置每个翻译批处理请求之间的等待时间（以秒为单位）。\n有助于避免超出 API 每分钟请求限制。",
        "keep_identifier_label": "保留原始 l_english 标识符", "keep_identifier_tooltip": "选中时：文件首行的 'l_english:' 及文件名中的 'l_english' 部分保持不变。\n未选中时：根据“目标翻译语言”进行更改（例如：l_korean）。",
        "check_internal_lang_label": "当内部语言与文件名不同时，优先使用UI设置",
        "check_internal_lang_tooltip": "选中时：如果文件名或文件首行的语言标识符与UI“源内容语言”设置不同，则优先使用UI设置传递给翻译API。\n（例如：l_english 文件但内容为中文时，若UI源语言设置为中文，则视为中文）。\n相关信息会记录在日志中。",
        "prompt_glossary_frame_title": "提示词与术语表管理",
        "prompt_edit_frame_title": "编辑提示词",
        "prompt_edit_textbox_tooltip": "这是将传递给翻译 API 的提示词。\n必须保留 {source_lang_for_prompt}、{target_lang_for_prompt}、{glossary_section}、{batch_text} 这些占位符。",
        "load_prompt_button": "从文件加载", "load_prompt_button_tooltip": "从文本文件加载提示词。",
        "save_prompt_button": "保存到文件", "save_prompt_button_tooltip": "将当前提示词保存到文本文件。",
        "reset_prompt_button": "恢复默认值", "reset_prompt_button_tooltip": "将提示词重置为程序默认值。",
        "prompt_file_load_title": "加载提示词文件",
        "prompt_file_save_title": "保存提示词文件",
        "glossary_management_frame_title": "术语表管理",
        "add_glossary_button": "添加术语表", "add_glossary_button_tooltip": "将新的术语表文件添加到列表中。",
        "remove_glossary_button": "移除选定术语表", "remove_glossary_button_tooltip": "从列表中移除选定的术语表文件。",
        "glossary_list_tooltip": "已激活的术语表列表。用于翻译。",
        "glossary_file_select_title": "选择术语表文件",
        "glossary_item_loaded": "已加载: {0} ({1} 个条目)", "glossary_item_error": "错误: {0}", "glossary_item_empty": "为空: {0}",
        "log_prompt_loaded_from_custom": "正在使用自定义提示词。",
        "log_prompt_loaded_from_file": "已从文件 '{0}' 加载提示词。",
        "log_prompt_saved_to_file": "提示词已保存到文件 '{0}'。",
        "log_prompt_reset_to_default": "提示词已重置为默认值。",
        "log_glossary_added": "已添加术语表 '{0}'。", "log_glossary_removed": "已移除术语表 '{0}'。",
        "log_combined_glossary_empty": "合并后的术语表为空。",
        "log_combined_glossary_info": "正在使用合并后术语表中的 {0} 个有效条目。",
        "translate_button": "开始翻译", "translate_button_tooltip": "使用输入的设置开始翻译所有目标文件。",
        "stop_button": "停止", "stop_button_tooltip": "停止当前正在进行的翻译任务。\n（已开始的批处理可能会完成）",
        "progress_frame": "进度",
        "status_waiting": "等待中...", "status_translating": "翻译中...", "status_preparing": "准备翻译中...",
        "status_completed_all": "所有文件翻译完成 ({0}/{1} 已处理)", "status_stopped": "翻译已停止 ({0}/{1} 已处理)",
        "status_completed_some": "翻译完成 ({0}/{1} 已处理)", "status_no_files": "未找到要处理的 YML 文件。",
        "log_frame": "运行日志", "error_title": "错误", "warn_title": "警告", "info_title": "信息",
        "error_api_key_needed": "需要输入 Gemini API 密钥。", "error_model_needed": "必须选择翻译模型。",
        "error_input_folder_invalid": "必须选择一个有效的输入文件夹。", "error_output_folder_needed": "必须选择输出文件夹。",
        "error_numeric_setting_invalid": "数字设置无效。请输入一个有效的数字。",
        "warn_already_translating": "翻译任务已在进行中。请稍候。", "info_no_translation_active": "当前没有正在进行的翻译任务。",
        "error_create_output_folder": "无法创建输出文件夹：{0}",
        "log_api_model_init_fail": "API 或模型初始化失败：{0}", "log_model_start": "开始使用 '{0}' 模型进行翻译。",
        "log_search_yml_files": "正在输入文件夹中搜索文件名包含 '{0}' 字符串的 YML 文件...", "log_no_yml_files_found": "在输入文件夹 '{0}' 中未找到文件名包含 '{1}' 的 YML 文件。",
        "log_total_files_start": "共翻译 {0} 个文件。", "log_file_empty": "文件 '{0}' 为空，已跳过。",
        "log_file_process_start": "开始翻译文件 '{0}' ({1} 行)。", "log_first_line_keep": "  文件首行的 'l_english:' 标识符将保持原始状态。",
        "log_first_line_change": "  将文件首行标识符从 '{0}' 更改为 '{1}'。", "log_file_only_identifier": "  文件 '{0}' 仅包含标识符行，跳过内容翻译。",
        "log_file_no_content_to_translate": "  文件 '{0}' 没有可翻译的内容。", "log_batch_translate": "  正在翻译部分文本：{0}~{1} 行 / 共 {2} 行",
        "log_translation_complete_save": "翻译完成！已保存到文件 '{0}'。", "log_file_process_error": "处理文件 '{0}' 时发生错误：{1}",
        "log_output_filename_change": "  将输出文件名从 '{0}' 更改为 '{1}'。", "log_file_task_cancelled": "文件 '{0}' 的翻译任务已取消。",
        "log_parallel_process_error": "并行处理文件 '{0}' 时发生错误：{1}", "log_all_translation_done": "所有文件的翻译任务已完成！",
        "log_translation_stopped_by_user": "翻译任务已被用户停止。", "log_translation_process_error": "翻译过程中发生全局错误：{0}",
        "log_stop_requested": "已请求停止翻译...", "ui_lang_self_name": "简体中文",
        "log_batch_prompt_blocked": "文件 '{0}', 批处理：API 提示词被阻止 (原因: {1})。返回原始内容。", "log_batch_token_limit": "文件 '{0}', 批处理：已达到 API 输出令牌限制 (原因代码: {1})。将拆分批次并重试。",
        "log_batch_single_line_token_limit": "文件 '{0}', 批处理：单行内容也超出令牌限制。返回原始内容。", "log_batch_abnormal_termination": "文件 '{0}', 批处理：翻译异常终止 ({1})。返回原始内容。",
        "log_batch_empty_response": "文件 '{0}', 批处理：从 API 收到空响应。返回原始内容。", "log_batch_line_mismatch": "文件 '{0}', 批处理：翻译后的行数与原始行数不符。缺失部分将用原始内容填充。",
        "log_batch_api_limit_error_split": "文件 '{0}', 批处理：发生 API 请求限制相关错误 ({1})。将拆分批次并重试。", "log_batch_single_line_api_limit": "文件 '{0}', 批处理：单行内容也发生 API 请求限制错误。返回原始内容。",
        "log_batch_unknown_error": "文件 '{0}', 批处理过程中发生未知错误: {1}", "log_file_process_stopped": "处理文件 '{0}' 时翻译已停止。",
        "log_file_completed": "文件翻译完成: {0}", "status_translating_progress": "翻译进行中... ({0}/{1})",
        "log_no_yml_files_found_short": "无文件", "log_search_yml_files_short": "正在搜索文件...",
        "status_stopped_short": "已停止", "status_completed_some_short": "已完成", "status_completed_all_short": "全部完成",
        "log_internal_lang_mismatch_using_ui": "文件 '{0}' 中的首行标识符 '{1}' 与 UI 中设置的源语言 '{2}' 不同。将使用 UI 设置进行翻译。",
        "log_internal_lang_no_identifier_using_ui": "在文件 '{0}' 中找不到语言标识符。将使用 UI 中设置的源语言 '{1}' 进行翻译。",
        "prompt_template_file_label": "提示词模板文件：",
        "prompt_template_file_tooltip": "包含传递给 API 的翻译指令的文本文件。\n（默认值：程序文件夹内的 'prompt_template.txt'）",
        "prompt_file_status_ok": "正在使用 '{0}'",
        "prompt_file_status_default": "正在使用默认提示词",
        "prompt_file_status_error": "文件错误！使用默认提示词",
        "glossary_file_label": "术语表文件 (可选)：",
        "glossary_file_tooltip": "包含翻译时参考的专有名词列表的文本文件。\n每行以“英语单词:翻译后单词”格式编写。",
        "browse_glossary_button_tooltip": "打开文件浏览器以选择术语表文件。",
        "glossary_file_status_ok": "正在使用 '{0}' ({1} 个条目)",
        "glossary_file_status_not_used": "未使用术语表",
        "glossary_file_status_empty": "术语表为空",
        "select_glossary_file_title": "选择术语表文件",
        "log_prompt_file_loaded": "已从提示词模板文件 '{0}' 加载。",
        "log_prompt_file_not_found_using_default": "找不到提示词模板文件 '{0}'。将使用内置的默认提示词。",
        "log_prompt_file_error_using_default": "加载提示词模板文件 '{0}' 时出错 ({1})。将使用内置的默认提示词。",
        "log_glossary_loaded": "已从术语表文件 '{0}' 加载 {1} 个条目。",
        "log_glossary_not_selected_or_empty": "未选择术语表文件或文件为空，不使用。",
        "log_glossary_error": "加载术语表文件 '{0}' 时出错：{1}"
    }
}
CONFIG_FILE = "translation_gui_config.json"

# --- Tooltip Helper Class (이전과 동일) ---
class Tooltip:
    def __init__(self, widget, text='위젯 정보'):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.enter, add="+")
        self.widget.bind("<Leave>", self.leave, add="+")
        self.widget.bind("<ButtonPress>", self.leave, add="+")

    def enter(self, event=None):
        if self.tooltip_window or not self.text: return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except tk.TclError: 
            if hasattr(self.widget, 'master') and self.widget.master:
                try:
                    x = self.widget.master.winfo_rootx() + self.widget.winfo_x() + self.widget.winfo_width() // 2
                    y = self.widget.master.winfo_rooty() + self.widget.winfo_y() + self.widget.winfo_height() + 5
                except tk.TclError: x = event.x_root + 10; y = event.y_root + 10
            else: x = event.x_root + 10; y = event.y_root + 10
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        current_mode = ctk.get_appearance_mode()
        bg_color = "#2E2E2E" if current_mode == "Dark" else "#FFFFE0" 
        fg_color = "#DCE4EE" if current_mode == "Dark" else "#333333" 
        border_color = "#4A4A4A" if current_mode == "Dark" else "#AAAAAA"
        self.tooltip_window.configure(bg=border_color) 
        label_frame = tk.Frame(self.tooltip_window, bg=bg_color) 
        label_frame.pack(padx=1, pady=1) 
        label_inner = tk.Label(label_frame, text=self.text, justify='left', background=bg_color, foreground=fg_color, font=("Arial", 9, "normal"))
        label_inner.pack(ipadx=3, ipady=3)
        self.tooltip_window.update_idletasks() 
        tooltip_width = self.tooltip_window.winfo_width()
        screen_width = self.widget.winfo_screenwidth()
        if x + tooltip_width > screen_width - 10: x = screen_width - tooltip_width - 10
        if x < 10: x = 10
        self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")

    def leave(self, event=None):
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = None
    
    def update_text(self, new_text):
        self.text = new_text
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            for child_frame in self.tooltip_window.winfo_children():
                if isinstance(child_frame, tk.Frame):
                    for child_label in child_frame.winfo_children():
                        if isinstance(child_label, tk.Label): child_label.configure(text=new_text); return

# --- Main Application Class ---
class TranslationGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_lang_code = tk.StringVar(value="ko")
        self.texts = LANGUAGES[self.current_lang_code.get()]

        self.title(self.texts.get("title"))
        self.geometry("1920x1080") # 창 크기 및 초기 위치 변경
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.api_key_var = tk.StringVar()
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.source_lang_for_api_var = tk.StringVar(value='English')
        self.target_lang_for_api_var = tk.StringVar(value='Korean')
        self.batch_size_var = tk.IntVar(value=25)
        self.max_workers_var = tk.IntVar(value=3)
        self.keep_lang_def_unchanged_var = tk.BooleanVar(value=False)
        self.check_internal_lang_var = tk.BooleanVar(value=False)
        self.max_tokens_var = tk.IntVar(value=8192)
        self.delay_between_batches_var = tk.DoubleVar(value=0.8)
        self.appearance_mode_var = tk.StringVar(value="Dark")

        self.api_lang_options_en = ('English', 'Korean', 'Simplified Chinese', 'French', 'German', 'Spanish', 'Japanese', 'Portuguese', 'Russian', 'Turkish')
        self.available_models = ['gemini-2.5-flash-preview-05-20', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
        self.model_name_var = tk.StringVar(value=self.available_models[0] if self.available_models else "")

        self.default_prompt_template_str = """Please translate the following YML formatted text from '{source_lang_for_prompt}' to '{target_lang_for_prompt}'.
{glossary_section}
You MUST adhere to the following rules strictly:
1. Only translate the text enclosed in double quotes after a colon (:). (e.g., `key: "text to translate"`)
2. Do NOT translate code-like strings, variable names (e.g., `$variable$`, `[variable]`, `<variable>`), special tags (e.g., `§Y`, `£gold£`), file paths, or URLs.
3. **CRITICAL**: You MUST preserve all original newline characters (\\n) and leading whitespace (indentation) for each line. Do NOT change or remove them. Each translated line must retain its original line break.
   Example:
   Original:
     key1: "First line\\nSecond line"
     key2: "  Indented text"
   Translation (assuming target is {target_lang_for_prompt}):
     key1: "Translated first line\\nTranslated second line"
     key2: "  Translated indented text"
4. Provide ONLY the translated text. Do NOT include any other explanations, headers, or footers.
5. Translate all personal names and proper nouns according to the context. (However, specific in-game unique item or skill names might be considered for keeping in original form).
6. If the content within quotes is a number, consists only of special characters, or is a simple path string (e.g., `gfx/interface/...`), do NOT translate it.
7. Do NOT translate YML comments (lines starting with '#'). Keep them as they are.
8. For each input line, you MUST output exactly one translated line. (Number of input lines = Number of output lines)

Text to translate:
```yaml
{batch_text}
```"""
        self.glossary_files = [] 

        self.is_translating = False
        self.stop_event = threading.Event()
        self.current_processing_file_for_log = ""
        self.translation_thread = None

        self.load_settings() 
        ctk.set_appearance_mode(self.appearance_mode_var.get())
        self.texts = LANGUAGES[self.current_lang_code.get()]
        self.title(self.texts.get("title"))

        self.create_widgets()
        self.update_ui_texts()
        
        if not hasattr(self, 'loaded_prompt_from_config') or not self.loaded_prompt_from_config:
            if hasattr(self, 'prompt_textbox'):
                 self.prompt_textbox.delete("1.0", "end")
                 self.prompt_textbox.insert("1.0", self.default_prompt_template_str)
        
        self._update_glossary_list_ui()

    def _on_closing(self):
        self.save_settings()
        self.destroy()

    def load_settings(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f: config = json.load(f)
                self.current_lang_code.set(config.get("ui_language", "ko"))
                self.appearance_mode_var.set(config.get("appearance_mode", "Dark"))
                self.api_key_var.set(config.get("api_key", ""))
                self.input_folder_var.set(config.get("input_folder", ""))
                self.output_folder_var.set(config.get("output_folder", ""))
                self.model_name_var.set(config.get("model_name", self.available_models[0] if self.available_models else ""))
                self.source_lang_for_api_var.set(config.get("source_lang_api", "English"))
                self.target_lang_for_api_var.set(config.get("target_lang_api", "Korean"))
                self.batch_size_var.set(config.get("batch_size", 25))
                self.max_workers_var.set(config.get("max_workers", 3))
                self.max_tokens_var.set(config.get("max_tokens", 8192))
                self.delay_between_batches_var.set(config.get("delay_between_batches", 0.8))
                self.keep_lang_def_unchanged_var.set(config.get("keep_identifier", False))
                self.check_internal_lang_var.set(config.get("check_internal_lang", False))
                prompt_str = config.get("custom_prompt", self.default_prompt_template_str)
                self.loaded_prompt_from_config = prompt_str if prompt_str != self.default_prompt_template_str else None
                loaded_glossaries = config.get("glossaries", [])
                self.glossary_files = []
                for g_path in loaded_glossaries:
                    if os.path.exists(g_path): self.glossary_files.append({"path": g_path, "status_var": tk.StringVar(), "entry_count": 0})
            else: self.loaded_prompt_from_config = None
        except Exception as e: print(f"Error loading settings: {e}"); self.loaded_prompt_from_config = None

    def save_settings(self):
        config = {
            "ui_language": self.current_lang_code.get(),
            "appearance_mode": ctk.get_appearance_mode(),
            "api_key": self.api_key_var.get(),
            "input_folder": self.input_folder_var.get(),
            "output_folder": self.output_folder_var.get(),
            "model_name": self.model_name_var.get(),
            "source_lang_api": self.source_lang_for_api_var.get(),
            "target_lang_api": self.target_lang_for_api_var.get(),
            "batch_size": self.batch_size_var.get(),
            "max_workers": self.max_workers_var.get(),
            "max_tokens": self.max_tokens_var.get(),
            "delay_between_batches": self.delay_between_batches_var.get(),
            "keep_identifier": self.keep_lang_def_unchanged_var.get(),
            "check_internal_lang": self.check_internal_lang_var.get(),
            "custom_prompt": self.prompt_textbox.get("1.0", "end-1c") if hasattr(self, 'prompt_textbox') else self.default_prompt_template_str,
            "glossaries": [g["path"] for g in self.glossary_files]
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, indent=4, ensure_ascii=False)
            if hasattr(self, 'log_message'): self.log_message("info_title", "설정이 저장되었습니다.")
        except Exception as e:
            if hasattr(self, 'log_message'): self.log_message("error_title", f"설정 저장 오류: {e}")
            else: print(f"Error saving settings: {e}")

    def create_widgets(self):
        # 메인 레이아웃: 상단(설정+프롬프트/용어집), 중단(버튼+진행바), 하단(로그)
        self.grid_rowconfigure(0, weight=5)  # 상단 영역 (설정, 프롬프트/용어집)
        self.grid_rowconfigure(1, weight=0)  # 중단 영역 (버튼, 진행바) - 고정 크기
        self.grid_rowconfigure(2, weight=2)  # 하단 영역 (로그)
        self.grid_columnconfigure(0, weight=1) # 전체 가로 확장

        # --- 상단 프레임 (왼쪽: UI 설정, 오른쪽: 프롬프트/용어집) ---
        top_main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_main_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="nsew")
        top_main_frame.grid_columnconfigure(0, weight=5) # 왼쪽 UI 설정 영역 (5)
        top_main_frame.grid_columnconfigure(1, weight=3) # 오른쪽 프롬프트/용어집 영역 (3)
        top_main_frame.grid_rowconfigure(0, weight=1) # 두 영역이 세로로 확장되도록

        # --- 왼쪽: 스크롤 가능한 설정 패널 ---
        self.settings_scroll_frame = ctk.CTkScrollableFrame(top_main_frame, corner_radius=10)
        self.settings_scroll_frame.grid(row=0, column=0, padx=(0,5), pady=0, sticky="nsew")
        self.settings_scroll_frame.grid_columnconfigure(0, weight=1)
        current_row_in_settings = 0
        # UI 설정
        self.ui_settings_frame = ctk.CTkFrame(self.settings_scroll_frame, corner_radius=10)
        self.ui_settings_frame.grid(row=current_row_in_settings, column=0, padx=0, pady=(0,7), sticky="ew"); current_row_in_settings+=1
        self.ui_settings_frame.grid_columnconfigure(1, minsize=130); self.ui_settings_frame.grid_columnconfigure(3, minsize=130)
        self.ui_settings_title_label = ctk.CTkLabel(self.ui_settings_frame, font=ctk.CTkFont(size=14, weight="bold")); self.ui_settings_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(5,10), sticky="w")
        self.ui_lang_label_widget = ctk.CTkLabel(self.ui_settings_frame); self.ui_lang_label_widget.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        ui_lang_combo_values = [LANGUAGES[code].get("ui_lang_self_name", code) for code in LANGUAGES.keys()]
        self.ui_lang_combo_widget = ctk.CTkComboBox(self.ui_settings_frame, variable=self.current_lang_code, values=ui_lang_combo_values, command=self._on_ui_lang_selected, width=120); self.ui_lang_combo_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.ui_lang_combo_tooltip = Tooltip(self.ui_lang_combo_widget, "")
        self.appearance_mode_label_widget = ctk.CTkLabel(self.ui_settings_frame); self.appearance_mode_label_widget.grid(row=1, column=2, padx=(20,5), pady=5, sticky="w")
        self.appearance_mode_optionmenu = ctk.CTkOptionMenu(self.ui_settings_frame, variable=self.appearance_mode_var, command=self.change_appearance_mode_event, width=120); self.appearance_mode_optionmenu.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        # API 및 모델 설정
        self.api_model_frame = ctk.CTkFrame(self.settings_scroll_frame, corner_radius=10); self.api_model_frame.grid(row=current_row_in_settings, column=0, padx=0, pady=7, sticky="ew"); current_row_in_settings+=1
        self.api_model_frame.grid_columnconfigure(1, weight=1)
        self.api_model_title_label = ctk.CTkLabel(self.api_model_frame, font=ctk.CTkFont(size=13, weight="bold")); self.api_model_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")
        self.api_key_label_widget = ctk.CTkLabel(self.api_model_frame); self.api_key_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.api_entry_widget = ctk.CTkEntry(self.api_model_frame, textvariable=self.api_key_var, show="*", placeholder_text="Enter API Key"); self.api_entry_widget.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.api_entry_tooltip = Tooltip(self.api_entry_widget, "")
        self.model_label_widget = ctk.CTkLabel(self.api_model_frame); self.model_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_combo_widget = ctk.CTkComboBox(self.api_model_frame, variable=self.model_name_var, values=self.available_models, state='readonly'); self.model_combo_widget.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_combo_tooltip = Tooltip(self.model_combo_widget, "")
        # 폴더 선택
        self.folder_frame = ctk.CTkFrame(self.settings_scroll_frame, corner_radius=10); self.folder_frame.grid(row=current_row_in_settings, column=0, padx=0, pady=7, sticky="ew"); current_row_in_settings+=1
        self.folder_frame.grid_columnconfigure(1, weight=1)
        self.folder_frame_title_label = ctk.CTkLabel(self.folder_frame, font=ctk.CTkFont(size=13, weight="bold")); self.folder_frame_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")
        self.input_folder_label_widget = ctk.CTkLabel(self.folder_frame); self.input_folder_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.input_folder_entry_widget = ctk.CTkEntry(self.folder_frame, textvariable=self.input_folder_var, placeholder_text="Input folder"); self.input_folder_entry_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.input_folder_entry_tooltip = Tooltip(self.input_folder_entry_widget, "")
        self.input_folder_button_widget = ctk.CTkButton(self.folder_frame, command=self.select_input_folder, width=100); self.input_folder_button_widget.grid(row=1, column=2, padx=(5,10), pady=5)
        self.input_folder_button_tooltip = Tooltip(self.input_folder_button_widget, "")
        self.output_folder_label_widget = ctk.CTkLabel(self.folder_frame); self.output_folder_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.output_folder_entry_widget = ctk.CTkEntry(self.folder_frame, textvariable=self.output_folder_var, placeholder_text="Output folder"); self.output_folder_entry_widget.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.output_folder_entry_tooltip = Tooltip(self.output_folder_entry_widget, "")
        self.output_folder_button_widget = ctk.CTkButton(self.folder_frame, command=self.select_output_folder, width=100); self.output_folder_button_widget.grid(row=2, column=2, padx=(5,10), pady=5)
        self.output_folder_button_tooltip = Tooltip(self.output_folder_button_widget, "")
        # 번역 언어 설정
        self.lang_frame_api = ctk.CTkFrame(self.settings_scroll_frame, corner_radius=10); self.lang_frame_api.grid(row=current_row_in_settings, column=0, padx=0, pady=7, sticky="ew"); current_row_in_settings+=1
        self.lang_frame_api.grid_columnconfigure(1, weight=1); self.lang_frame_api.grid_columnconfigure(3, weight=1) 
        self.lang_frame_api_title_label = ctk.CTkLabel(self.lang_frame_api, font=ctk.CTkFont(size=13, weight="bold")); self.lang_frame_api_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")
        self.source_content_lang_label_widget = ctk.CTkLabel(self.lang_frame_api); self.source_content_lang_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.source_combo_api_widget = ctk.CTkComboBox(self.lang_frame_api, variable=self.source_lang_for_api_var, values=self.api_lang_options_en, state='readonly', width=180); self.source_combo_api_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.source_combo_api_tooltip = Tooltip(self.source_combo_api_widget, "")
        self.target_trans_lang_label_widget = ctk.CTkLabel(self.lang_frame_api); self.target_trans_lang_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.target_combo_api_widget = ctk.CTkComboBox(self.lang_frame_api, variable=self.target_lang_for_api_var, values=self.api_lang_options_en, state='readonly', width=180); self.target_combo_api_widget.grid(row=1, column=3, sticky="ew", padx=10, pady=5)
        self.target_combo_api_tooltip = Tooltip(self.target_combo_api_widget, "")
        # 번역 상세 설정
        self.setting_frame_details = ctk.CTkFrame(self.settings_scroll_frame, corner_radius=10); self.setting_frame_details.grid(row=current_row_in_settings, column=0, padx=0, pady=7, sticky="ew"); current_row_in_settings+=1
        self.setting_frame_details.grid_columnconfigure(1, weight=1); self.setting_frame_details.grid_columnconfigure(3, weight=1)
        self.setting_frame_details_title_label = ctk.CTkLabel(self.setting_frame_details, font=ctk.CTkFont(size=13, weight="bold")); self.setting_frame_details_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")
        self.batch_size_label_widget = ctk.CTkLabel(self.setting_frame_details); self.batch_size_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.batch_size_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.batch_size_var, width=80, justify='center'); self.batch_size_entry_widget.grid(row=1, column=1, sticky="w", padx=(5,10), pady=5)
        self.batch_size_spinbox_tooltip = Tooltip(self.batch_size_entry_widget, "")
        self.concurrent_files_label_widget = ctk.CTkLabel(self.setting_frame_details); self.concurrent_files_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.max_workers_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.max_workers_var, width=80, justify='center'); self.max_workers_entry_widget.grid(row=1, column=3, sticky="w", padx=(5,10), pady=5)
        self.max_workers_spinbox_tooltip = Tooltip(self.max_workers_entry_widget, "")
        self.max_output_tokens_label_widget = ctk.CTkLabel(self.setting_frame_details); self.max_output_tokens_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.max_tokens_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.max_tokens_var, width=80, justify='center'); self.max_tokens_entry_widget.grid(row=2, column=1, sticky="w", padx=(5,10), pady=5)
        self.max_tokens_spinbox_tooltip = Tooltip(self.max_tokens_entry_widget, "")
        self.batch_delay_label_widget = ctk.CTkLabel(self.setting_frame_details); self.batch_delay_label_widget.grid(row=2, column=2, sticky="w", padx=(20,10), pady=5)
        self.delay_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.delay_between_batches_var, width=80, justify='center'); self.delay_entry_widget.grid(row=2, column=3, sticky="w", padx=(5,10), pady=5)
        self.delay_spinbox_tooltip = Tooltip(self.delay_entry_widget, "")
        self.lang_def_option_check_widget = ctk.CTkCheckBox(self.setting_frame_details, variable=self.keep_lang_def_unchanged_var, onvalue=True, offvalue=False); self.lang_def_option_check_widget.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.lang_def_option_check_tooltip = Tooltip(self.lang_def_option_check_widget, "")
        self.internal_lang_check_widget = ctk.CTkCheckBox(self.setting_frame_details, variable=self.check_internal_lang_var, onvalue=True, offvalue=False); self.internal_lang_check_widget.grid(row=3, column=2, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.internal_lang_check_tooltip = Tooltip(self.internal_lang_check_widget, "")


        # --- 오른쪽: 프롬프트, 용어집 관리 패널 ---
        self.prompt_glossary_main_frame = ctk.CTkFrame(top_main_frame, corner_radius=10)
        self.prompt_glossary_main_frame.grid(row=0, column=1, padx=(5,0), pady=0, sticky="nsew")
        self.prompt_glossary_main_frame.grid_columnconfigure(0, weight=1)
        self.prompt_glossary_main_frame.grid_rowconfigure(0, weight=0) # 타이틀
        self.prompt_glossary_main_frame.grid_rowconfigure(1, weight=3) # 프롬프트 편집 (3)
        self.prompt_glossary_main_frame.grid_rowconfigure(2, weight=2) # 용어집 관리 (2)

        self.pg_title_label = ctk.CTkLabel(self.prompt_glossary_main_frame, font=ctk.CTkFont(size=14, weight="bold")); self.pg_title_label.grid(row=0, column=0, padx=10, pady=(7,10), sticky="w")
        
        # 프롬프트 편집 영역
        prompt_edit_subframe = ctk.CTkFrame(self.prompt_glossary_main_frame); prompt_edit_subframe.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        prompt_edit_subframe.grid_columnconfigure(0, weight=1); prompt_edit_subframe.grid_rowconfigure(1, weight=1)
        self.prompt_edit_title_label = ctk.CTkLabel(prompt_edit_subframe, font=ctk.CTkFont(size=13, weight="bold")); self.prompt_edit_title_label.grid(row=0, column=0, columnspan=3, padx=5, pady=(5,0), sticky="w")
        self.prompt_textbox = ctk.CTkTextbox(prompt_edit_subframe, wrap="word"); self.prompt_textbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.prompt_textbox_tooltip = Tooltip(self.prompt_textbox, "")
        if hasattr(self, 'loaded_prompt_from_config') and self.loaded_prompt_from_config: self.prompt_textbox.insert("1.0", self.loaded_prompt_from_config)
        else: self.prompt_textbox.insert("1.0", self.default_prompt_template_str)
        prompt_button_frame = ctk.CTkFrame(prompt_edit_subframe, fg_color="transparent"); prompt_button_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=(0,5), sticky="ew")
        self.load_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self._load_prompt_from_file); self.load_prompt_btn.pack(side="left", padx=(0,5))
        self.load_prompt_btn_tooltip = Tooltip(self.load_prompt_btn, "")
        self.save_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self._save_prompt_to_file); self.save_prompt_btn.pack(side="left", padx=5)
        self.save_prompt_btn_tooltip = Tooltip(self.save_prompt_btn, "")
        self.reset_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self._reset_default_prompt); self.reset_prompt_btn.pack(side="left", padx=5)
        self.reset_prompt_btn_tooltip = Tooltip(self.reset_prompt_btn, "")

        # 용어집 관리 영역
        glossary_manage_subframe = ctk.CTkFrame(self.prompt_glossary_main_frame); glossary_manage_subframe.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        glossary_manage_subframe.grid_columnconfigure(0, weight=1); glossary_manage_subframe.grid_rowconfigure(1, weight=1)
        self.glossary_manage_title_label = ctk.CTkLabel(glossary_manage_subframe, font=ctk.CTkFont(size=13, weight="bold")); self.glossary_manage_title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5,0), sticky="w")
        self.glossary_list_frame = ctk.CTkScrollableFrame(glossary_manage_subframe, label_text=""); self.glossary_list_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.glossary_list_frame.grid_columnconfigure(0, weight=1)
        glossary_button_frame = ctk.CTkFrame(glossary_manage_subframe, fg_color="transparent"); glossary_button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")
        self.add_glossary_btn = ctk.CTkButton(glossary_button_frame, command=self._add_glossary_file); self.add_glossary_btn.pack(side="left", padx=(0,5))
        self.add_glossary_btn_tooltip = Tooltip(self.add_glossary_btn, "")

        # --- 중단 프레임 (버튼, 진행바) ---
        middle_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        middle_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        middle_frame.grid_columnconfigure(0, weight=1) # 버튼 중앙 정렬용
        
        button_container_frame = ctk.CTkFrame(middle_frame, fg_color="transparent"); button_container_frame.pack(pady=5) # pack으로 중앙 배치
        self.translate_btn_widget = ctk.CTkButton(button_container_frame, command=self.start_translation, width=120, height=32, font=ctk.CTkFont(weight="bold")); self.translate_btn_widget.pack(side="left", padx=(0,5))
        self.translate_btn_tooltip = Tooltip(self.translate_btn_widget, "")
        self.stop_btn_widget = ctk.CTkButton(button_container_frame, command=self.stop_translation, state='disabled', width=120, height=32); self.stop_btn_widget.pack(side="left", padx=(5,0))
        self.stop_btn_tooltip = Tooltip(self.stop_btn_widget, "")

        self.progress_frame_display = ctk.CTkFrame(middle_frame, corner_radius=10); self.progress_frame_display.pack(fill="x", padx=0, pady=(5,0)) # pack으로 가로 채움
        self.progress_frame_display.grid_columnconfigure(0, weight=1)
        self.progress_frame_display_title_label = ctk.CTkLabel(self.progress_frame_display, font=ctk.CTkFont(size=13, weight="bold")); self.progress_frame_display_title_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(7,5))
        self.progress_text_var = tk.StringVar(); self.progress_label_widget = ctk.CTkLabel(self.progress_frame_display, textvariable=self.progress_text_var, anchor="w"); self.progress_label_widget.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,5))
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame_display, mode='determinate', height=10, corner_radius=5); self.progress_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,10)); self.progress_bar.set(0)


        # --- 하단 프레임 (로그) ---
        self.log_frame_display = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame_display.grid(row=2, column=0, padx=10, pady=(5,10), sticky="nsew")
        self.log_frame_display.grid_rowconfigure(1, weight=1); self.log_frame_display.grid_columnconfigure(0, weight=1)
        self.log_frame_display_title_label = ctk.CTkLabel(self.log_frame_display, font=ctk.CTkFont(size=13, weight="bold")); self.log_frame_display_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(7,5))
        self.log_text_widget = ctk.CTkTextbox(self.log_frame_display, wrap="word", corner_radius=8, border_width=1); self.log_text_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.log_text_widget.configure(state="disabled")

    def update_ui_texts(self):
        current_code = self.current_lang_code.get()
        if current_code not in LANGUAGES: current_code = "ko"; self.current_lang_code.set(current_code)
        self.texts = LANGUAGES.get(current_code, LANGUAGES["ko"])
        self.title(self.texts.get("title"))
        self.ui_settings_title_label.configure(text=self.texts.get("ui_settings_frame_title"))
        self.ui_lang_label_widget.configure(text=self.texts.get("ui_lang_label"))
        self.ui_lang_combo_tooltip.update_text(self.texts.get("ui_lang_tooltip"))
        self.appearance_mode_label_widget.configure(text=self.texts.get("appearance_mode_label"))
        appearance_mode_values = [self.texts.get("dark_mode"), self.texts.get("light_mode"), self.texts.get("system_mode")]
        self.appearance_mode_optionmenu.configure(values=appearance_mode_values)
        current_appearance_key = self.appearance_mode_var.get()
        if current_appearance_key == "Dark": self.appearance_mode_optionmenu.set(self.texts.get("dark_mode"))
        elif current_appearance_key == "Light": self.appearance_mode_optionmenu.set(self.texts.get("light_mode"))
        else: self.appearance_mode_optionmenu.set(self.texts.get("system_mode"))
        self.api_model_title_label.configure(text=self.texts.get("api_settings_frame"))
        self.folder_frame_title_label.configure(text=self.texts.get("folder_frame"))
        self.lang_frame_api_title_label.configure(text=self.texts.get("lang_settings_frame"))
        self.setting_frame_details_title_label.configure(text=self.texts.get("detailed_settings_frame"))
        self.api_key_label_widget.configure(text=self.texts.get("api_key_label"))
        self.api_entry_tooltip.update_text(self.texts.get("api_key_tooltip"))
        self.model_label_widget.configure(text=self.texts.get("model_label"))
        self.model_combo_tooltip.update_text(self.texts.get("model_tooltip"))
        self.input_folder_label_widget.configure(text=self.texts.get("input_folder_label"))
        self.input_folder_entry_tooltip.update_text(self.texts.get("input_folder_tooltip"))
        self.input_folder_button_widget.configure(text=self.texts.get("browse_button"))
        self.input_folder_button_tooltip.update_text(self.texts.get("input_browse_tooltip"))
        self.output_folder_label_widget.configure(text=self.texts.get("output_folder_label"))
        self.output_folder_entry_tooltip.update_text(self.texts.get("output_folder_tooltip"))
        self.output_folder_button_widget.configure(text=self.texts.get("browse_button"))
        self.output_folder_button_tooltip.update_text(self.texts.get("output_browse_tooltip"))
        self.source_content_lang_label_widget.configure(text=self.texts.get("source_content_lang_label"))
        self.source_combo_api_tooltip.update_text(self.texts.get("source_content_lang_tooltip"))
        self.target_trans_lang_label_widget.configure(text=self.texts.get("target_trans_lang_label"))
        self.target_combo_api_tooltip.update_text(self.texts.get("target_trans_lang_tooltip"))
        self.batch_size_label_widget.configure(text=self.texts.get("batch_size_label"))
        self.batch_size_spinbox_tooltip.update_text(self.texts.get("batch_size_tooltip"))
        self.concurrent_files_label_widget.configure(text=self.texts.get("concurrent_files_label"))
        self.max_workers_spinbox_tooltip.update_text(self.texts.get("concurrent_files_tooltip"))
        self.max_output_tokens_label_widget.configure(text=self.texts.get("max_output_tokens_label"))
        self.max_tokens_spinbox_tooltip.update_text(self.texts.get("max_output_tokens_tooltip"))
        self.batch_delay_label_widget.configure(text=self.texts.get("batch_delay_label"))
        self.delay_spinbox_tooltip.update_text(self.texts.get("batch_delay_tooltip"))
        self.lang_def_option_check_widget.configure(text=self.texts.get("keep_identifier_label"))
        self.lang_def_option_check_tooltip.update_text(self.texts.get("keep_identifier_tooltip"))
        self.internal_lang_check_widget.configure(text=self.texts.get("check_internal_lang_label"))
        self.internal_lang_check_tooltip.update_text(self.texts.get("check_internal_lang_tooltip"))
        self.pg_title_label.configure(text=self.texts.get("prompt_glossary_frame_title"))
        self.prompt_edit_title_label.configure(text=self.texts.get("prompt_edit_frame_title"))
        self.prompt_textbox_tooltip.update_text(self.texts.get("prompt_edit_textbox_tooltip"))
        self.load_prompt_btn.configure(text=self.texts.get("load_prompt_button"))
        self.load_prompt_btn_tooltip.update_text(self.texts.get("load_prompt_button_tooltip"))
        self.save_prompt_btn.configure(text=self.texts.get("save_prompt_button"))
        self.save_prompt_btn_tooltip.update_text(self.texts.get("save_prompt_button_tooltip"))
        self.reset_prompt_btn.configure(text=self.texts.get("reset_prompt_button"))
        self.reset_prompt_btn_tooltip.update_text(self.texts.get("reset_prompt_button_tooltip"))
        self.glossary_manage_title_label.configure(text=self.texts.get("glossary_management_frame_title"))
        self.add_glossary_btn.configure(text=self.texts.get("add_glossary_button"))
        self.add_glossary_btn_tooltip.update_text(self.texts.get("add_glossary_button_tooltip"))
        self.translate_btn_widget.configure(text=self.texts.get("translate_button"))
        self.translate_btn_tooltip.update_text(self.texts.get("translate_button_tooltip"))
        self.stop_btn_widget.configure(text=self.texts.get("stop_button"))
        self.stop_btn_tooltip.update_text(self.texts.get("stop_button_tooltip"))
        self.progress_frame_display_title_label.configure(text=self.texts.get("progress_frame"))
        self.log_frame_display_title_label.configure(text=self.texts.get("log_frame"))
        if not self.is_translating: self.progress_text_var.set(self.texts.get("status_waiting"))
        self._update_glossary_list_ui()

    # --- 나머지 메서드들 (이전과 거의 동일, progress_bar 업데이트 부분만 수정됨) ---
    def _on_ui_lang_selected(self, choice_code_or_display_name):
        selected_code = self.current_lang_code.get()
        for code, names in LANGUAGES.items():
            if names.get("ui_lang_self_name", code) == choice_code_or_display_name: selected_code = code; break
        self.current_lang_code.set(selected_code)
        self.update_ui_texts()

    def change_appearance_mode_event(self, new_appearance_mode_str_display):
        mode_to_set = "System"
        if new_appearance_mode_str_display == self.texts.get("dark_mode"): mode_to_set = "Dark"
        elif new_appearance_mode_str_display == self.texts.get("light_mode"): mode_to_set = "Light"
        self.appearance_mode_var.set(mode_to_set)
        ctk.set_appearance_mode(mode_to_set)

    def _load_prompt_from_file(self):
        filepath = filedialog.askopenfilename(title=self.texts.get("prompt_file_load_title"), filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath:
            try:
                with codecs.open(filepath, 'r', encoding='utf-8-sig') as f: prompt_content = f.read()
                self.prompt_textbox.delete("1.0", "end"); self.prompt_textbox.insert("1.0", prompt_content)
                self.log_message("log_prompt_loaded_from_file", os.path.basename(filepath))
            except Exception as e: messagebox.showerror(self.texts.get("error_title"), f"Error loading prompt file: {e}"); self.log_message("log_prompt_file_error_using_default", os.path.basename(filepath), str(e))

    def _save_prompt_to_file(self):
        filepath = filedialog.asksaveasfilename(title=self.texts.get("prompt_file_save_title"), defaultextension=".txt", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath:
            try:
                prompt_content = self.prompt_textbox.get("1.0", "end-1c")
                with codecs.open(filepath, 'w', encoding='utf-8-sig') as f: f.write(prompt_content)
                self.log_message("log_prompt_saved_to_file", os.path.basename(filepath))
            except Exception as e: messagebox.showerror(self.texts.get("error_title"), f"Error saving prompt file: {e}")

    def _reset_default_prompt(self):
        self.prompt_textbox.delete("1.0", "end"); self.prompt_textbox.insert("1.0", self.default_prompt_template_str)
        self.log_message("log_prompt_reset_to_default")

    def _add_glossary_file(self):
        filepaths = filedialog.askopenfilenames(title=self.texts.get("glossary_file_select_title"), filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        newly_added_count = 0
        if filepaths:
            for fp in filepaths:
                if not any(g["path"] == fp for g in self.glossary_files):
                    self.glossary_files.append({"path": fp, "status_var": tk.StringVar(), "entry_count": 0})
                    self.log_message("log_glossary_added", os.path.basename(fp)); newly_added_count +=1
            if newly_added_count > 0: self._update_glossary_list_ui()

    def _remove_glossary_file(self, file_path_to_remove):
        self.glossary_files = [g for g in self.glossary_files if g["path"] != file_path_to_remove]
        self.log_message("log_glossary_removed", os.path.basename(file_path_to_remove))
        self._update_glossary_list_ui()

    def _update_glossary_list_ui(self):
        for widget in self.glossary_list_frame.winfo_children(): widget.destroy()
        if not self.glossary_files:
            no_glossary_label = ctk.CTkLabel(self.glossary_list_frame, text=self.texts.get("glossary_file_status_not_used")); no_glossary_label.pack(pady=5)
            return
        for i, glossary_item in enumerate(self.glossary_files):
            item_frame = ctk.CTkFrame(self.glossary_list_frame, fg_color="transparent"); item_frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)
            file_path = glossary_item["path"]; base_name = os.path.basename(file_path)
            status_text = base_name
            if not os.path.exists(file_path): status_text += f" ({self.texts.get('error_title')}: File not found)"
            status_label = ctk.CTkLabel(item_frame, text=status_text, anchor="w"); status_label.grid(row=0, column=0, sticky="ew", padx=(0,5))
            remove_btn = ctk.CTkButton(item_frame, text="X", width=30, height=20, command=lambda fp=file_path: self._remove_glossary_file(fp)); remove_btn.grid(row=0, column=1, sticky="e")

    def _get_combined_glossary_content(self):
        combined_glossary_for_prompt = []; total_valid_entries = 0
        for glossary_item_info in self.glossary_files:
            filepath = glossary_item_info["path"]; base_name = os.path.basename(filepath)
            if not (os.path.exists(filepath) and os.path.isfile(filepath)):
                glossary_item_info["status_var"].set(self.texts.get("glossary_item_error").format(base_name)); glossary_item_info["entry_count"] = 0; continue
            try:
                with codecs.open(filepath, 'r', encoding='utf-8-sig') as f: lines = [line.strip() for line in f if line.strip()]
                current_file_entries = 0
                if not lines: glossary_item_info["status_var"].set(self.texts.get("glossary_item_empty").format(base_name)); glossary_item_info["entry_count"] = 0; continue
                for line in lines:
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            combined_glossary_for_prompt.append(f"- \"{parts[0].strip()}\" should be translated as \"{parts[1].strip()}\""); current_file_entries += 1
                total_valid_entries += current_file_entries; glossary_item_info["entry_count"] = current_file_entries
                glossary_item_info["status_var"].set(self.texts.get("glossary_item_loaded").format(base_name, current_file_entries))
            except Exception as e: glossary_item_info["status_var"].set(self.texts.get("glossary_item_error").format(base_name)); glossary_item_info["entry_count"] = 0; self.log_message("log_glossary_error", base_name, str(e))
        if not combined_glossary_for_prompt: self.log_message("log_combined_glossary_empty"); return ""
        self.log_message("log_combined_glossary_info", total_valid_entries)
        header = "Please refer to the following glossary for translation. Ensure these terms are translated as specified:\n"
        return header + "\n".join(combined_glossary_for_prompt) + "\n\n"

    def select_input_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("input_folder_label")[:-1]); 
        if folder: self.input_folder_var.set(folder)
    def select_output_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("output_folder_label")[:-1]); 
        if folder: self.output_folder_var.set(folder)

    def log_message(self, message_key, *args):
        if not hasattr(self, 'texts') or not self.texts: current_texts = LANGUAGES[self.current_lang_code.get()]
        else: current_texts = self.texts
        log_text_template = current_texts.get(message_key, message_key)
        try: formatted_message = log_text_template.format(*args)
        except (IndexError, KeyError, TypeError): formatted_message = log_text_template; 
        if args: formatted_message += " " + str(args)
        if hasattr(self, 'log_text_widget') and self.log_text_widget and self.log_text_widget.winfo_exists():
            self.log_text_widget.configure(state="normal"); self.log_text_widget.insert("end", f"{time.strftime('%H:%M:%S')} - {formatted_message}\n"); self.log_text_widget.see("end"); self.log_text_widget.configure(state="disabled"); self.update_idletasks()

    def validate_inputs(self):
        def is_valid_int(value_var, min_val, max_val):
            try: val = int(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False
        def is_valid_float(value_var, min_val, max_val):
            try: val = float(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False
        if not self.api_key_var.get().strip(): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_api_key_needed")); return False
        if not self.model_name_var.get(): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_model_needed")); return False
        if not self.input_folder_var.get() or not os.path.isdir(self.input_folder_var.get()): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_input_folder_invalid")); return False
        if not self.output_folder_var.get(): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_output_folder_needed")); return False
        if not is_valid_int(self.batch_size_var, 1, 500): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_size_label')[:-1]})"); return False
        if not is_valid_int(self.max_workers_var, 1, 256): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('concurrent_files_label')[:-1]})"); return False
        if not is_valid_int(self.max_tokens_var, 100, 65536): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('max_output_tokens_label')[:-1]})"); return False
        if not is_valid_float(self.delay_between_batches_var, 0.0, 60.0): messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_delay_label')[:-1]})"); return False
        current_prompt = self.prompt_textbox.get("1.0", "end-1c")
        required_placeholders = ["{source_lang_for_prompt}", "{target_lang_for_prompt}", "{glossary_section}", "{batch_text}"]
        missing_placeholders = [ph for ph in required_placeholders if ph not in current_prompt]
        if missing_placeholders: messagebox.showerror(self.texts.get("error_title"), f"프롬프트에 필수 플레이스홀더가 누락되었습니다: {', '.join(missing_placeholders)}"); return False
        return True

    def get_language_code(self, lang_name_en):
        mapping = {'English':"english", 'Korean':"korean", 'Simplified Chinese':"simp_chinese", 'French':"french", 'German':"german", 'Spanish':"spanish", 'Japanese':"japanese", 'Portuguese':"portuguese", 'Russian':"russian", 'Turkish':"turkish"}
        return mapping.get(lang_name_en, "english") 

    def translate_batch(self, text_batch, model, temperature=0.2, max_output_tokens=8192):
        batch_text_content = "\n".join([line.rstrip('\n') for line in text_batch])
        source_lang_for_prompt = self.source_lang_for_api_var.get(); target_lang_for_prompt = self.target_lang_for_api_var.get()
        prompt_template_str = self.prompt_textbox.get("1.0", "end-1c"); glossary_str_for_prompt = self._get_combined_glossary_content() 
        try: final_prompt = prompt_template_str.format(source_lang_for_prompt=source_lang_for_prompt, target_lang_for_prompt=target_lang_for_prompt, glossary_section=glossary_str_for_prompt, batch_text=batch_text_content)
        except KeyError as e: self.log_message("log_batch_unknown_error", self.current_processing_file_for_log, f"Prompt formatting error (KeyError: {e}). Using default structure."); final_prompt = self.default_prompt_template_str.format(source_lang_for_prompt=source_lang_for_prompt, target_lang_for_prompt=target_lang_for_prompt, glossary_section=glossary_str_for_prompt, batch_text=batch_text_content)
        try:
            if self.stop_event.is_set(): return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            response = model.generate_content(final_prompt, generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_output_tokens))
            translated_text = ""; finish_reason_val = 0 
            if response.candidates: candidate = response.candidates[0]; 
            if candidate.content and candidate.content.parts: translated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
            if hasattr(candidate, 'finish_reason'): finish_reason_val = candidate.finish_reason
            elif hasattr(response, 'text') and response.text: translated_text = response.text
            if response.prompt_feedback and response.prompt_feedback.block_reason: self.log_message("log_batch_prompt_blocked", self.current_processing_file_for_log, response.prompt_feedback.block_reason); return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            if finish_reason_val not in [0, 1]:
                if finish_reason_val == 2: 
                    self.log_message("log_batch_token_limit", self.current_processing_file_for_log, finish_reason_val)
                    if len(text_batch) > 1: mid = len(text_batch) // 2; first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens); second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens); return first_half + second_half
                    else: self.log_message("log_batch_single_line_token_limit", self.current_processing_file_for_log); return [line if line.endswith('\n') else line + '\n' for line in text_batch]
                else: 
                    reason_str = f"Reason Code: {finish_reason_val}"
                    if response.candidates and response.candidates[0].safety_ratings: safety_str = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in response.candidates[0].safety_ratings]); reason_str += f" (Safety: {safety_str})"
                    self.log_message("log_batch_abnormal_termination", self.current_processing_file_for_log, reason_str); return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            if not translated_text.strip(): self.log_message("log_batch_empty_response", self.current_processing_file_for_log); return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            if translated_text.startswith("```yaml\n"): translated_text = translated_text[len("```yaml\n"):]
            if translated_text.endswith("\n```"): translated_text = translated_text[:-len("\n```")]
            if translated_text.startswith("```\n"): translated_text = translated_text[len("```\n"):]
            if translated_text.endswith("```"): translated_text = translated_text[:-len("```")]
            translated_lines_raw = translated_text.split('\n'); processed_lines = []
            for i in range(len(translated_lines_raw)):
                api_translated_line = translated_lines_raw[i]
                if i < len(text_batch): 
                    original_line_content = text_batch[i]; original_ends_with_newline = original_line_content.endswith('\n')
                    if original_ends_with_newline and not api_translated_line.endswith('\n'): processed_lines.append(api_translated_line + '\n')
                    else: processed_lines.append(api_translated_line)
                else: processed_lines.append(api_translated_line) 
            if len(processed_lines) < len(text_batch):
                self.log_message("log_batch_line_mismatch", self.current_processing_file_for_log)
                for k in range(len(processed_lines), len(text_batch)): original_line = text_batch[k]; processed_lines.append(original_line if original_line.endswith('\n') else original_line + '\n')
            return processed_lines
        except Exception as e:
            if self.stop_event.is_set(): return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            error_str = str(e).lower()
            if ("token" in error_str and ("limit" in error_str or "exceeded" in error_str or "max" in error_str)) or ("429" in error_str) or ("resource has been exhausted" in error_str) or ("quota" in error_str) or ("rate limit" in error_str) or ("rpm" in error_str and "limit" in error_str):
                self.log_message("log_batch_api_limit_error_split", self.current_processing_file_for_log, str(e))
                if len(text_batch) > 1: mid = len(text_batch) // 2; first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens); second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens); return first_half + second_half
                else: self.log_message("log_batch_single_line_api_limit", self.current_processing_file_for_log); return [line if line.endswith('\n') else line + '\n' for line in text_batch]
            self.log_message("log_batch_unknown_error", self.current_processing_file_for_log, str(e)); return [line if line.endswith('\n') else line + '\n' for line in text_batch]

    def process_file(self, input_file, output_file, model):
        self.current_processing_file_for_log = os.path.basename(input_file)
        try:
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f: lines = f.readlines()
            if not lines: self.log_message("log_file_empty", self.current_processing_file_for_log); return
            total_lines = len(lines); translated_lines_final = []; self.log_message("log_file_process_start", self.current_processing_file_for_log, total_lines)
            start_index = 0; first_line_lang_pattern = re.compile(r"^\s*l_([a-zA-Z_]+)\s*:", re.IGNORECASE)
            if self.check_internal_lang_var.get() and lines:
                first_line_match_check = first_line_lang_pattern.match(lines[0]); source_lang_ui_selected_api_name = self.source_lang_for_api_var.get(); source_lang_code_from_ui = self.get_language_code(source_lang_ui_selected_api_name) 
                if first_line_match_check:
                    actual_lang_code_in_file = first_line_match_check.group(1).lower()
                    if actual_lang_code_in_file != source_lang_code_from_ui: self.log_message("log_internal_lang_mismatch_using_ui", self.current_processing_file_for_log, f"l_{actual_lang_code_in_file}", f"l_{source_lang_code_from_ui}")
                else: self.log_message("log_internal_lang_no_identifier_using_ui", self.current_processing_file_for_log, f"l_{source_lang_code_from_ui}")
            first_line_match_for_change = first_line_lang_pattern.match(lines[0])
            if first_line_match_for_change:
                original_first_line_content = lines[0]; original_lang_identifier_in_file = first_line_match_for_change.group(0).strip() 
                if self.keep_lang_def_unchanged_var.get(): translated_lines_final.append(original_first_line_content); self.log_message("log_first_line_keep") 
                else: target_lang_code_str = self.get_language_code(self.target_lang_for_api_var.get()); new_first_line_content = first_line_lang_pattern.sub(f"l_{target_lang_code_str}:", original_first_line_content, count=1); translated_lines_final.append(new_first_line_content); self.log_message("log_first_line_change", original_lang_identifier_in_file, f"l_{target_lang_code_str}:")
                start_index = 1
            if start_index >= total_lines:
                if first_line_match_for_change : self.log_message("log_file_only_identifier", self.current_processing_file_for_log)
                else: self.log_message("log_file_no_content_to_translate", self.current_processing_file_for_log)
                if translated_lines_final: os.makedirs(os.path.dirname(output_file), exist_ok=True); 
                with codecs.open(output_file, 'w', encoding='utf-8-sig') as f: f.writelines(translated_lines_final); self.log_message("log_translation_complete_save", os.path.basename(output_file))
                return
            batch_size = self.batch_size_var.get(); current_max_tokens = self.max_tokens_var.get(); delay_time = self.delay_between_batches_var.get()
            for i in range(start_index, total_lines, batch_size):
                if self.stop_event.is_set(): self.log_message("log_file_process_stopped", self.current_processing_file_for_log); return
                batch_to_translate = lines[i:i+batch_size]; self.log_message("log_batch_translate", i+1, min(i+batch_size, total_lines), total_lines)
                translated_batch_lines = self.translate_batch(batch_to_translate, model, max_output_tokens=current_max_tokens); translated_lines_final.extend(translated_batch_lines)
                if i + batch_size < total_lines and not self.stop_event.is_set() and delay_time > 0: time.sleep(delay_time)
            if self.stop_event.is_set(): return
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with codecs.open(output_file, 'w', encoding='utf-8-sig') as f: f.writelines(translated_lines_final); self.log_message("log_translation_complete_save", os.path.basename(output_file))
        except Exception as e: 
            if not self.stop_event.is_set(): self.log_message("log_file_process_error", self.current_processing_file_for_log, str(e))
        finally: self.current_processing_file_for_log = ""

    def translation_worker(self):
        model = None; completed_count = 0; total_files_to_process = 0
        try:
            self.stop_event.clear(); self.after(0, lambda: self.progress_bar.set(0)) # 프로그레스바 초기화
            api_key = self.api_key_var.get().strip(); selected_model_name = self.model_name_var.get(); genai.configure(api_key=api_key); model = genai.GenerativeModel(selected_model_name)
            self.log_message("log_model_start", selected_model_name)
        except Exception as e: self.log_message("log_api_model_init_fail", str(e)); self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process); return
        try:
            input_dir = self.input_folder_var.get(); output_dir = self.output_folder_var.get(); target_files = []
            target_lang_api_name_for_filename = self.target_lang_for_api_var.get(); target_lang_code_for_filename_output = self.get_language_code(target_lang_api_name_for_filename)
            source_lang_api_name = self.source_lang_for_api_var.get(); source_lang_code = self.get_language_code(source_lang_api_name); file_identifier_for_search = f"l_{source_lang_code}"
            self.log_message("log_search_yml_files", file_identifier_for_search)
            for root_path, _, files_in_dir in os.walk(input_dir):
                if self.stop_event.is_set(): break
                for file_name in files_in_dir:
                    if self.stop_event.is_set(): break
                    if file_identifier_for_search.lower() in file_name.lower() and file_name.lower().endswith(('.yml', '.yaml')): target_files.append(os.path.join(root_path, file_name))
                if self.stop_event.is_set(): break
            if self.stop_event.is_set(): self.log_message("log_translation_stopped_by_user"); self.after(0, self._update_ui_after_translation, completed_count, len(target_files)); return
            total_files_to_process = len(target_files)
            if not target_files: self.log_message("log_no_yml_files_found", input_dir, file_identifier_for_search); self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process); return
            self.log_message("log_total_files_start", total_files_to_process)
            self.after(0, lambda: self.progress_text_var.set(self.texts.get("status_translating_progress").format(0, total_files_to_process)))
            
            def process_single_file_wrapper(input_f):
                if self.stop_event.is_set(): return None
                relative_path = os.path.relpath(input_f, input_dir); output_f_path = os.path.join(output_dir, relative_path)
                if not self.keep_lang_def_unchanged_var.get():
                    base_name = os.path.basename(output_f_path); dir_name = os.path.dirname(output_f_path); identifier_to_replace_in_filename = f"l_{source_lang_code}"; new_target_identifier_for_filename = f"l_{target_lang_code_for_filename_output}"
                    new_base_name, num_replacements = re.subn(re.escape(identifier_to_replace_in_filename), new_target_identifier_for_filename, base_name, flags=re.IGNORECASE)
                    if num_replacements > 0 and new_base_name != base_name: self.log_message("log_output_filename_change", base_name, new_base_name); output_f_path = os.path.join(dir_name, new_base_name)
                self.process_file(input_f, output_f_path, model)
                return os.path.basename(input_f) if not self.stop_event.is_set() else None

            num_workers = self.max_workers_var.get()
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_file = {executor.submit(process_single_file_wrapper, f): f for f in target_files if not self.stop_event.is_set()}
                for future in concurrent.futures.as_completed(future_to_file):
                    if self.stop_event.is_set(): 
                        for f_cancel in future_to_file.keys(): 
                            if not f_cancel.done(): f_cancel.cancel()
                        break 
                    try:
                        completed_filename = future.result()
                        if completed_filename: 
                            completed_count +=1; self.log_message("log_file_completed", completed_filename)
                            progress_value = completed_count / total_files_to_process if total_files_to_process > 0 else 0
                            self.after(0, lambda cc=completed_count, tt=total_files_to_process, pv=progress_value: (
                                self.progress_text_var.set(self.texts.get("status_translating_progress").format(cc,tt)),
                                self.progress_bar.set(pv)
                            ))
                    except concurrent.futures.CancelledError: self.log_message("log_file_task_cancelled", os.path.basename(future_to_file[future]))
                    except Exception as exc: self.log_message("log_parallel_process_error", os.path.basename(future_to_file[future]), str(exc))
            final_log_msg_key = "log_all_translation_done" if not self.stop_event.is_set() else "log_translation_stopped_by_user"
            self.log_message(final_log_msg_key)
        except Exception as e: 
            if not self.stop_event.is_set(): self.log_message("log_translation_process_error", str(e))
        finally:
            self.is_translating = False 
            final_progress = completed_count / total_files_to_process if total_files_to_process > 0 else 0
            if self.stop_event.is_set() and completed_count < total_files_to_process : # 중지되었고, 다 못한 경우
                 pass # 현재 진행률 유지
            elif completed_count == total_files_to_process and total_files_to_process > 0: # 모두 완료
                final_progress = 1.0
            # 그 외 (오류로 0개 완료 등)는 현재 진행률 유지하거나 0으로
            self.after(0, lambda: self.progress_bar.set(final_progress))
            self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process)
            self.current_processing_file_for_log = ""

    def _update_ui_after_translation(self, completed_count, total_files):
        if not self.winfo_exists(): return
        self.translate_btn_widget.configure(state='normal'); self.stop_btn_widget.configure(state='disabled')
        final_message = ""; progress_value = 0.0
        if self.stop_event.is_set() and total_files > 0 : final_message = self.texts.get("status_stopped").format(completed_count, total_files); progress_value = completed_count / total_files if total_files > 0 else 0
        elif total_files == 0: final_message = self.texts.get("status_no_files"); progress_value = 0.0
        elif completed_count == total_files and total_files > 0 : final_message = self.texts.get("status_completed_all").format(completed_count, total_files); progress_value = 1.0
        elif completed_count >= 0 and completed_count < total_files : final_message = self.texts.get("status_completed_some").format(completed_count, total_files); progress_value = completed_count / total_files if total_files > 0 else 0
        else: final_message = self.texts.get("status_waiting"); progress_value = 0.0
        self.progress_text_var.set(final_message); self.progress_bar.set(progress_value)
        self.is_translating = False 

    def start_translation(self):
        if not self.validate_inputs(): return
        if self.is_translating: messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_translating")); return
        self.is_translating = True; self.stop_event.clear(); self.progress_bar.set(0)
        self.translate_btn_widget.configure(state='disabled'); self.stop_btn_widget.configure(state='normal')
        self.progress_text_var.set(self.texts.get("status_preparing"))
        if self.log_text_widget.winfo_exists(): self.log_text_widget.configure(state="normal"); self.log_text_widget.delete("1.0", "end"); self.log_text_widget.configure(state="disabled")
        self._update_glossary_list_ui()
        try: os.makedirs(self.output_folder_var.get(), exist_ok=True)
        except OSError as e: messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_create_output_folder").format(str(e))); self._update_ui_after_translation(0,0); return
        self.translation_thread = threading.Thread(target=self.translation_worker, daemon=True); self.translation_thread.start()

    def stop_translation(self):
        if self.is_translating: 
            self.stop_event.set(); self.log_message("log_stop_requested"); self.stop_btn_widget.configure(state='disabled') 
        else: messagebox.showinfo(self.texts.get("info_title"), self.texts.get("info_no_translation_active"))

def main():
    app = TranslationGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
