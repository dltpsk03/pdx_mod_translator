import customtkinter as ctk # 현대적인 UI를 위한 CustomTkinter 라이브러리
from tkinter import filedialog, messagebox # 파일/폴더 선택 및 메시지 박스를 위한 기본 tkinter 모듈
import os # 운영체제와 상호작용 (파일 경로, 폴더 생성 등)
import threading # 백그라운드 작업을 위한 스레딩
import time # 작업 지연(sleep)을 위한 시간 모듈
import codecs # 특정 인코딩(UTF-8 with BOM)으로 파일을 읽고 쓰기 위함
import concurrent.futures # 여러 파일을 동시에 처리하기 위한 병렬 처리
import google.generativeai as genai # Gemini API 사용
import re # 정규 표현식 (파일 첫 줄 패턴 매칭 등)
import tkinter as tk # Tooltip 클래스에서 tk.Toplevel 등을 사용하기 위해 필요

# --- 언어별 UI 텍스트 및 메시지 ---
# 프로그램에서 사용되는 모든 텍스트를 언어별로 정의합니다.
# 사용자가 UI 언어를 변경하면 해당 언어의 텍스트로 UI가 업데이트됩니다.
# TODO: (개발자 참고) 새로운 UI 요소나 메시지 추가 시 여기에 해당 언어 번역을 추가해야 합니다.
LANGUAGES = {
    "ko": {
        "title": "패독겜 모드번역기",
        "ui_settings_frame_title": "UI 설정",
        "ui_lang_label": "UI 언어:", "ui_lang_tooltip": "프로그램 인터페이스의 표시 언어를 변경합니다.",
        "appearance_mode_label": "모양 모드:", "dark_mode": "어둡게", "light_mode": "밝게", "system_mode": "시스템 기본",
        "color_theme_label": "테마 색상:", "blue_theme": "파랑", "green_theme": "초록", "dark_blue_theme": "어두운 파랑",
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
        "log_search_yml_files": "입력 폴더에서 '{0}' 문자열을 포함하는 YML 파일을 찾고 있습니다...", "log_no_yml_files_found": "입력 폴더 '{0}'에서 '{1}'을(를) 포함하는 YML 파일을 찾지 못했습니다.",
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
    },
    "en": { # Machine Translated from Korean - Needs Review
        "title": "Paradox Mod Translator",
        "ui_settings_frame_title": "UI Settings",
        "ui_lang_label": "UI Language:", "ui_lang_tooltip": "Changes the display language of the program interface.",
        "appearance_mode_label": "Appearance Mode:", "dark_mode": "Dark", "light_mode": "Light", "system_mode": "System Default",
        "color_theme_label": "Theme Color:", "blue_theme": "Blue", "green_theme": "Green", "dark_blue_theme": "Dark Blue",
        "api_settings_frame": "API & Model Settings",
        "api_key_label": "Gemini API Key:", "api_key_tooltip": "Enter the Gemini API key issued by Google AI Studio.\nE.g., AIzaSy...",
        "model_label": "Translation Model:", "model_tooltip": "Select the Gemini model to use for translation.\nPerformance and cost may vary by model.",
        "folder_frame": "Folder Selection",
        "input_folder_label": "Input Folder:", "input_folder_tooltip": "Select the folder containing the original YML files to be translated.",
        "browse_button": "Browse", "input_browse_tooltip": "Opens a browser to select the input folder.",
        "output_folder_label": "Output Folder:", "output_folder_tooltip": "Select the folder where the translated YML files will be saved.",
        "output_browse_tooltip": "Opens a browser to select the output folder.",
        "lang_settings_frame": "Translation Language Settings (for API Request)",
        "source_content_lang_label": "Source Content Language:", "source_content_lang_tooltip": "Select the actual source language of the text within the YML file.\nThis information is passed to the API to improve translation quality.",
        "target_trans_lang_label": "Target Translation Language:", "target_trans_lang_tooltip": "Select the language to translate the text into.\nThe language identifier in the output file (e.g., l_korean) may also change based on this setting.",
        "detailed_settings_frame": "Detailed Translation Settings",
        "batch_size_label": "Batch Size:", "batch_size_tooltip": "The number of text lines to send to the API for translation at one time.\nToo large may cause the API to not respond or error.",
        "concurrent_files_label": "Concurrent Files:", "concurrent_files_tooltip": "When translating multiple files simultaneously, set how many to process in parallel at once.\nAdjust according to your computer's performance.",
        "max_output_tokens_label": "Max Output Tokens:", "max_output_tokens_tooltip": "Limits the maximum length of the translated text (output) in tokens.\nBe careful not to exceed the maximum token limit of the selected model.",
        "batch_delay_label": "Delay Between Batches (sec):", "batch_delay_tooltip": "Sets how long to wait (in seconds) between each translation batch request.\nHelps to avoid exceeding the API's requests per minute limit.",
        "keep_identifier_label": "Keep 'l_english' Identifier", "keep_identifier_tooltip": "If checked: Does not change 'l_english:' in the first line and 'l_english' in filenames, keeping them as is.\nIf unchecked: Changes them according to the 'Target Translation Language' (e.g., l_korean).",
        "translate_button": "Start Translation", "translate_button_tooltip": "Starts the translation of all target files with the entered settings.",
        "stop_button": "Stop", "stop_button_tooltip": "Stops the currently ongoing translation process.\n(Batches already started may complete).",
        "progress_frame": "Progress",
        "status_waiting": "Waiting...", "status_translating": "Translating...", "status_preparing": "Preparing translation...",
        "status_completed_all": "All files translated ({0}/{1} processed)", "status_stopped": "Translation stopped ({0}/{1} processed)",
        "status_completed_some": "Translation completed ({0}/{1} processed)", "status_no_files": "Could not find YML files to process.",
        "log_frame": "Execution Log", "error_title": "Error", "warn_title": "Warning", "info_title": "Information",
        "error_api_key_needed": "Gemini API key must be entered.", "error_model_needed": "A translation model must be selected.",
        "error_input_folder_invalid": "A valid input folder must be selected.", "error_output_folder_needed": "An output folder must be selected.",
        "error_numeric_setting_invalid": "Numeric setting value is incorrect. Please enter a valid number (integer or decimal).",
        "warn_already_translating": "Translation is already in progress. Please wait.", "info_no_translation_active": "No translation process is currently active.",
        "error_create_output_folder": "Cannot create output folder: {0}",
        "log_api_model_init_fail": "API or Model initialization failed: {0}", "log_model_start": "Starting translation using model '{0}'.",
        "log_search_yml_files": "Searching for YML files containing '{0}' in the input folder...", "log_no_yml_files_found": "Could not find YML files containing '{1}' in input folder '{0}'.",
        "log_total_files_start": "Translating a total of {0} files.", "log_file_empty": "File '{0}' is empty, skipping.",
        "log_file_process_start": "Starting translation of file '{0}' ({1} lines).", "log_first_line_keep": "  Keeping original 'l_english:' identifier in the first line.",
        "log_first_line_change": "  Changing first line identifier from '{0}' to '{1}'.", "log_file_only_identifier": "  File '{0}' contains only the identifier line, skipping content translation.",
        "log_file_no_content_to_translate": "  No content to translate in file '{0}'.", "log_batch_translate": "  Translating text part: {0}~{1} / Total {2} lines",
        "log_translation_complete_save": "Translation complete! Saved to file '{0}'.", "log_file_process_error": "Error processing file '{0}': {1}",
        "log_output_filename_change": "  Changing output filename from '{0}' to '{1}'.", "log_file_task_cancelled": "Translation task for file '{0}' cancelled.",
        "log_parallel_process_error": "Error during parallel processing of file '{0}': {1}", "log_all_translation_done": "Translation of all files completed!",
        "log_translation_stopped_by_user": "Translation process stopped by user.", "log_translation_process_error": "Overall error during translation process: {0}",
        "log_stop_requested": "Translation stop requested...", "ui_lang_self_name": "English",
        "log_batch_prompt_blocked": "File '{0}', Batch: API prompt was blocked (Reason: {1}). Returning original content.", "log_batch_token_limit": "File '{0}', Batch: API output token limit reached (Reason Code: {1}). Splitting batch and retrying.",
        "log_batch_single_line_token_limit": "File '{0}', Batch: Content of a single line exceeds token limit. Returning original content.", "log_batch_abnormal_termination": "File '{0}', Batch: Translation terminated abnormally ({1}). Returning original content.",
        "log_batch_empty_response": "File '{0}', Batch: Received empty response from API. Returning original content.", "log_batch_line_mismatch": "File '{0}', Batch: Number of translated lines differs from original. Filling missing parts with original.",
        "log_batch_api_limit_error_split": "File '{0}', Batch: API request limit error ({1}). Splitting batch and retrying.", "log_batch_single_line_api_limit": "File '{0}', Batch: API request limit error for a single line. Returning original content.",
        "log_batch_unknown_error": "File '{0}', Unknown error during batch processing: {1}", "log_file_process_stopped": "Translation stopped while processing file '{0}'.",
        "log_file_completed": "File translation complete: {0}", "status_translating_progress": "Translating... ({0}/{1})",
        "log_no_yml_files_found_short": "No files", "log_search_yml_files_short": "Searching...",
        "status_stopped_short": "Stopped", "status_completed_some_short": "Completed", "status_completed_all_short": "All done",
    },
    "zh_CN": { # Machine Translated from Korean - Needs Review
        "title": "P社Mod翻译器",
        "ui_settings_frame_title": "界面设置",
        "ui_lang_label": "界面语言:", "ui_lang_tooltip": "更改程序界面的显示语言。",
        "appearance_mode_label": "外观模式:", "dark_mode": "深色", "light_mode": "浅色", "system_mode": "系统默认",
        "color_theme_label": "主题颜色:", "blue_theme": "蓝色", "green_theme": "绿色", "dark_blue_theme": "深蓝色",
        "api_settings_frame": "API 及模型设置",
        "api_key_label": "Gemini API 密钥:", "api_key_tooltip": "请输入从 Google AI Studio 获取的 Gemini API 密钥。\n例如：AIzaSy...",
        "model_label": "翻译模型:", "model_tooltip": "选择用于翻译的 Gemini 模型。\n不同模型的性能和费用可能不同。",
        "folder_frame": "文件夹选择",
        "input_folder_label": "输入文件夹:", "input_folder_tooltip": "选择包含待翻译源YML文件的文件夹。",
        "browse_button": "浏览", "input_browse_tooltip": "打开浏览器选择输入文件夹。",
        "output_folder_label": "输出文件夹:", "output_folder_tooltip": "选择用于保存翻译后YML文件的文件夹。",
        "output_browse_tooltip": "打开浏览器选择输出文件夹。",
        "lang_settings_frame": "翻译语言设置 (用于API请求)",
        "source_content_lang_label": "源内容语言:", "source_content_lang_tooltip": "选择YML文件内文本的实际源语言。\n此信息将传递给API以提高翻译质量。",
        "target_trans_lang_label": "目标翻译语言:", "target_trans_lang_tooltip": "选择要将文本翻译成的语言。\n输出文件中的语言标识符（如l_korean）也可能根据此设置更改。",
        "detailed_settings_frame": "详细翻译设置",
        "batch_size_label": "批处理大小:", "batch_size_tooltip": "一次发送给API进行翻译的文本行数。\n设置过大可能导致API无响应或出错。",
        "concurrent_files_label": "并发文件数:", "concurrent_files_tooltip": "同时翻译多个文件时，设置一次并行处理的最大数量。\n请根据您的计算机性能进行调整。",
        "max_output_tokens_label": "最大输出令牌:", "max_output_tokens_tooltip": "限制翻译结果（文本）的最大长度（以令牌为单位）。\n请注意不要超过所选模型的最大令牌限制。",
        "batch_delay_label": "批次间隔(秒):", "batch_delay_tooltip": "设置每个翻译批次请求之间的等待时间（秒）。\n有助于避免超出API的每分钟请求限制。",
        "keep_identifier_label": "保留l_english标识符", "keep_identifier_tooltip": "勾选时：不更改文件首行的“l_english:”和文件名中的“l_english”部分，保持原样。\n取消勾选时：根据“目标翻译语言”进行更改（例如：l_korean）。",
        "translate_button": "开始翻译", "translate_button_tooltip": "使用输入的设置开始翻译所有目标文件。",
        "stop_button": "停止", "stop_button_tooltip": "停止当前正在进行的翻译作业。\n（已开始的批次可能会完成）。",
        "progress_frame": "进度",
        "status_waiting": "等待中...", "status_translating": "翻译中...", "status_preparing": "准备翻译...",
        "status_completed_all": "所有文件翻译完成 ({0}/{1} 已处理)", "status_stopped": "翻译已停止 ({0}/{1} 已处理)",
        "status_completed_some": "翻译已完成 ({0}/{1} 已处理)", "status_no_files": "未找到要处理的YML文件。",
        "log_frame": "运行日志", "error_title": "错误", "warn_title": "警告", "info_title": "信息",
        "error_api_key_needed": "必须输入Gemini API密钥。", "error_model_needed": "必须选择翻译模型。",
        "error_input_folder_invalid": "必须选择有效的输入文件夹。", "error_output_folder_needed": "必须选择输出文件夹。",
        "error_numeric_setting_invalid": "数字设置值不正确。请输入有效的数字（整数或小数）。",
        "warn_already_translating": "翻译任务已在进行中，请稍候。", "info_no_translation_active": "当前没有正在进行的翻译任务。",
        "error_create_output_folder": "无法创建输出文件夹: {0}",
        "log_api_model_init_fail": "API或模型初始化失败: {0}", "log_model_start": "开始使用模型“{0}”进行翻译。",
        "log_search_yml_files": "正在输入文件夹中搜索包含“{0}”字符串的YML文件...", "log_no_yml_files_found": "在输入文件夹“{0}”中未找到包含“{1}”的YML文件。",
        "log_total_files_start": "总共翻译 {0} 个文件。", "log_file_empty": "文件“{0}”为空，已跳过。",
        "log_file_process_start": "开始翻译文件“{0}”（{1}行）。", "log_first_line_keep": "  文件首行的“l_english:”标识符保持不变。",
        "log_first_line_change": "  文件首行标识符从“{0}”更改为“{1}”。", "log_file_only_identifier": "  文件“{0}”仅包含标识符行，跳过内容翻译。",
        "log_file_no_content_to_translate": "  文件“{0}”中没有可翻译的内容。", "log_batch_translate": "  正在翻译部分文本：{0}~{1} / 共 {2}行",
        "log_translation_complete_save": "翻译完成！已保存到文件“{0}”。", "log_file_process_error": "处理文件“{0}”时出错: {1}",
        "log_output_filename_change": "  输出文件名从“{0}”更改为“{1}”。", "log_file_task_cancelled": "文件“{0}”的翻译任务已取消。",
        "log_parallel_process_error": "并行处理文件“{0}”时出错: {1}", "log_all_translation_done": "所有文件的翻译任务已完成！",
        "log_translation_stopped_by_user": "翻译任务已被用户停止。", "log_translation_process_error": "翻译过程中发生整体错误: {0}",
        "log_stop_requested": "已请求停止翻译...", "ui_lang_self_name": "简体中文",
        "log_batch_prompt_blocked": "文件“{0}”，批处理：API提示被阻止（原因：{1}）。返回原始内容。", "log_batch_token_limit": "文件“{0}”，批处理：达到API输出令牌限制（原因代码：{1}）。正在分割批次并重试。",
        "log_batch_single_line_token_limit": "文件“{0}”，批处理：单行内容超出令牌限制。返回原始内容。", "log_batch_abnormal_termination": "文件“{0}”，批处理：翻译异常终止（{1}）。返回原始内容。",
        "log_batch_empty_response": "文件“{0}”，批处理：从API收到空响应。返回原始内容。", "log_batch_line_mismatch": "文件“{0}”，批处理：翻译行数与原文不同。用原文填充缺失部分。",
        "log_batch_api_limit_error_split": "文件“{0}”，批处理：发生API请求限制相关错误（{1}）。正在分割批次并重试。", "log_batch_single_line_api_limit": "文件“{0}”，批处理：单行内容发生API请求限制错误。返回原始内容。",
        "log_batch_unknown_error": "文件“{0}”，批处理期间发生未知错误: {1}", "log_file_process_stopped": "处理文件“{0}”时翻译已停止。",
        "log_file_completed": "文件翻译完成: {0}", "status_translating_progress": "翻译进行中... ({0}/{1})",
        "log_no_yml_files_found_short": "无文件", "log_search_yml_files_short": "搜索中...",
        "status_stopped_short": "已停止", "status_completed_some_short": "已完成", "status_completed_all_short": "全部完成",
    }
}

# --- Tooltip Helper Class (이전 답변과 동일, Tkinter 위젯 기준) ---
# CustomTkinter 환경에서는 CTkToolTip (외부 라이브러리) 또는 직접 구현을 고려할 수 있습니다.
# 여기서는 간단한 tk.Toplevel 기반 툴팁을 유지합니다.
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
        
        # 위젯의 스크린 좌표를 사용하여 툴팁 위치 계산
        # CTk 위젯은 master를 통해 root 좌표를 얻는 것이 더 안정적일 수 있음
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except tk.TclError: # 위젯이 아직 완전히 그려지지 않은 경우 대비
            x = self.widget.master.winfo_rootx() + self.widget.winfo_x() + self.widget.winfo_width() // 2
            y = self.widget.master.winfo_rooty() + self.widget.winfo_y() + self.widget.winfo_height() + 5

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        
        current_mode = ctk.get_appearance_mode()
        bg_color = "#2B2B2B" if current_mode == "Dark" else "#FFFFE0"
        fg_color = "#DCE4EE" if current_mode == "Dark" else "#000000"
        border_color = "#555555" if current_mode == "Dark" else "#AAAAAA"

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background=bg_color, foreground=fg_color, relief='solid', borderwidth=1,
                         highlightbackground=border_color, highlightthickness=0, # 테두리 색상 명시
                         font=("Arial", 9, "normal")) # 시스템에 따라 적절한 폰트 선택
        label.pack(ipadx=3, ipady=3)
        
        self.tooltip_window.update_idletasks() 
        tooltip_width = self.tooltip_window.winfo_width()
        screen_width = self.widget.winfo_screenwidth()
        if x + tooltip_width > screen_width - 5: # 화면 가장자리 여백
            x = screen_width - tooltip_width - 10
        if x < 5: # 화면 왼쪽 가장자리
            x = 5
        
        self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")

    def leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None
    
    def update_text(self, new_text):
        self.text = new_text
        if self.tooltip_window and self.tooltip_window.winfo_exists():
            for child_widget in self.tooltip_window.winfo_children():
                if isinstance(child_widget, tk.Label):
                    child_widget.configure(text=new_text)
                    break

# --- Main Application Class (CustomTkinter 기반) ---
class TranslationGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CustomTkinter 기본 모양 및 테마 설정
        ctk.set_appearance_mode("Dark")  # "Light", "Dark", "System" 중 선택
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue" 중 선택

        self.current_lang_code = tk.StringVar(value="ko") # UI 언어 코드 (예: "ko", "en", "zh_CN")
        self.texts = LANGUAGES[self.current_lang_code.get()] # 현재 언어의 텍스트 리소스

        self.title(self.texts.get("title")) # 창 제목 설정
        self.geometry("850x900") # 창 크기 설정 (세로 약간 늘림)
        self.resizable(True, True) # 창 크기 조절 가능

        # 프로그램 데이터 저장을 위한 변수들
        self.api_key_var = tk.StringVar()
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        
        # API 요청 시 사용할 언어 목록 (항상 영어로 표시)
        self.api_lang_options_en = (
            'English', 'French', 'German', 'Spanish', 'Japanese', 
            'Korean', 'Portuguese', 'Russian', 'Simplified Chinese', 'Turkish'
        )
        self.source_lang_for_api_var = tk.StringVar(value='English') # API용 원본 언어 (기본값 영어)
        self.target_lang_for_api_var = tk.StringVar(value='Korean') # API용 대상 언어 (기본값 한국어)
        
        # 번역 설정값 변수
        self.batch_size_var = tk.IntVar(value=25)
        self.max_workers_var = tk.IntVar(value=3)
        self.keep_lang_def_unchanged_var = tk.BooleanVar(value=False)
        self.max_tokens_var = tk.IntVar(value=8192)
        self.delay_between_batches_var = tk.DoubleVar(value=0.8)

        # 사용 가능한 Gemini 모델 목록
        self.available_models = [
            'gemini-2.5-flash-preview-05-20', 'gemini-2.0-flash', 'gemini-1.5-pro', 
            'gemini-1.5-flash'  # 이전 사용 모델 포함
        ]
        self.model_name_var = tk.StringVar(value=self.available_models[0]) # 기본 모델 선택

        # 번역 작업 상태 관리 변수
        self.is_translating = False
        self.current_processing_file_for_log = "" # 로그에 현재 처리 중인 파일명 표시용
        self.translation_thread = None # 번역 작업을 수행할 스레드 객체

        # UI 위젯 생성 및 초기 텍스트 설정
        self.create_widgets()
        self.update_ui_texts() # 생성된 위젯에 현재 언어의 텍스트 적용

    # --- UI 언어 및 테마 변경 콜백 함수 ---
    def _on_ui_lang_selected(self, choice_display_name):
        """UI 언어 콤보박스에서 언어가 선택되었을 때 호출됩니다."""
        for code, names in LANGUAGES.items():
            if names.get("ui_lang_self_name", code) == choice_display_name:
                self.current_lang_code.set(code)
                break
        self.update_ui_texts()

    def change_appearance_mode_event(self, new_appearance_mode_str_display):
        """모양 모드 옵션 메뉴 변경 시 호출됩니다."""
        mode_to_set = "System" # 기본값
        if new_appearance_mode_str_display == self.texts.get("dark_mode"): mode_to_set = "Dark"
        elif new_appearance_mode_str_display == self.texts.get("light_mode"): mode_to_set = "Light"
        ctk.set_appearance_mode(mode_to_set)

    def change_color_theme_event(self, new_color_theme_str_display):
        """테마 색상 옵션 메뉴 변경 시 호출됩니다."""
        theme_to_set = "blue" # 기본값
        if new_color_theme_str_display == self.texts.get("green_theme"): theme_to_set = "green"
        elif new_color_theme_str_display == self.texts.get("dark_blue_theme"): theme_to_set = "dark-blue"
        ctk.set_default_color_theme(theme_to_set)
        # 테마 변경 후 UI를 다시 그릴 필요는 없음 (CustomTkinter가 자동으로 처리)

    # --- 위젯 생성 함수 ---
    def create_widgets(self):
        """프로그램의 모든 UI 위젯을 생성하고 배치합니다."""
        self.grid_rowconfigure(8, weight=1) # 로그 프레임이 세로로 확장되도록 (row 인덱스 확인 필요)
        self.grid_columnconfigure(0, weight=1) # 전체 가로 확장

        # --- UI 설정 (언어, 모양, 테마) ---
        # 각 설정 그룹을 프레임으로 묶어 관리합니다.
        # CTkFrame의 corner_radius로 둥근 모서리 효과를 줄 수 있습니다.
        # fg_color="transparent"는 부모 프레임의 배경색을 따르도록 합니다.
        self.ui_settings_frame = ctk.CTkFrame(self, corner_radius=10)
        self.ui_settings_frame.grid(row=0, column=0, padx=10, pady=(10,7), sticky="ew")
        # 내부 그리드 컬럼 가중치 설정 (옵션 메뉴 등이 적절히 배치되도록)
        self.ui_settings_frame.grid_columnconfigure(1, minsize=130) 
        self.ui_settings_frame.grid_columnconfigure(3, minsize=130)
        self.ui_settings_frame.grid_columnconfigure(5, minsize=130)


        self.ui_settings_title_label = ctk.CTkLabel(self.ui_settings_frame, font=ctk.CTkFont(size=14, weight="bold"))
        self.ui_settings_title_label.grid(row=0, column=0, columnspan=6, padx=10, pady=(5,10), sticky="w")

        self.ui_lang_label_widget = ctk.CTkLabel(self.ui_settings_frame)
        self.ui_lang_label_widget.grid(row=1, column=0, padx=(10,5), pady=5, sticky="w")
        ui_lang_combo_values = [LANGUAGES[code].get("ui_lang_self_name", code) for code in LANGUAGES.keys()]
        self.ui_lang_combo_widget = ctk.CTkComboBox(self.ui_settings_frame, values=ui_lang_combo_values, command=self._on_ui_lang_selected, width=120)
        self.ui_lang_combo_widget.set(LANGUAGES[self.current_lang_code.get()].get("ui_lang_self_name", self.current_lang_code.get()))
        self.ui_lang_combo_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.ui_lang_combo_tooltip = Tooltip(self.ui_lang_combo_widget, "")

        self.appearance_mode_label_widget = ctk.CTkLabel(self.ui_settings_frame)
        self.appearance_mode_label_widget.grid(row=1, column=2, padx=(20,5), pady=5, sticky="w")
        self.appearance_mode_optionmenu = ctk.CTkOptionMenu(self.ui_settings_frame, command=self.change_appearance_mode_event, width=120) # values는 update_ui_texts에서 설정
        self.appearance_mode_optionmenu.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.color_theme_label_widget = ctk.CTkLabel(self.ui_settings_frame)
        self.color_theme_label_widget.grid(row=1, column=4, padx=(20,5), pady=5, sticky="w")
        self.color_theme_optionmenu = ctk.CTkOptionMenu(self.ui_settings_frame, command=self.change_color_theme_event, width=120) # values는 update_ui_texts에서 설정
        self.color_theme_optionmenu.grid(row=1, column=5, padx=5, pady=5, sticky="w")


        # --- API 및 모델 설정 ---
        # 각 설정 그룹에 대한 프레임과 제목 라벨
        self.api_model_frame = ctk.CTkFrame(self, corner_radius=10)
        self.api_model_frame.grid(row=1, column=0, padx=10, pady=7, sticky="ew")
        self.api_model_frame.grid_columnconfigure(1, weight=1)
        self.api_model_title_label = ctk.CTkLabel(self.api_model_frame, font=ctk.CTkFont(size=13, weight="bold"))
        self.api_model_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")

        # API 키 입력 필드
        self.api_key_label_widget = ctk.CTkLabel(self.api_model_frame)
        self.api_key_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.api_entry_widget = ctk.CTkEntry(self.api_model_frame, textvariable=self.api_key_var, show="*", placeholder_text="Enter API Key (e.g., AIzaSy...)") # placeholder 추가
        self.api_entry_widget.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.api_entry_tooltip = Tooltip(self.api_entry_widget, "")

        # 번역 모델 선택 콤보박스
        self.model_label_widget = ctk.CTkLabel(self.api_model_frame)
        self.model_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_combo_widget = ctk.CTkComboBox(self.api_model_frame, variable=self.model_name_var, values=self.available_models, state='readonly')
        self.model_combo_widget.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_combo_tooltip = Tooltip(self.model_combo_widget, "")

        # --- 폴더 선택 ---
        self.folder_frame = ctk.CTkFrame(self, corner_radius=10)
        self.folder_frame.grid(row=2, column=0, padx=10, pady=7, sticky="ew")
        self.folder_frame.grid_columnconfigure(1, weight=1)
        self.folder_frame_title_label = ctk.CTkLabel(self.folder_frame, font=ctk.CTkFont(size=13, weight="bold"))
        self.folder_frame_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")

        # 입력 폴더
        self.input_folder_label_widget = ctk.CTkLabel(self.folder_frame)
        self.input_folder_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.input_folder_entry_widget = ctk.CTkEntry(self.folder_frame, textvariable=self.input_folder_var, placeholder_text="Path to input folder")
        self.input_folder_entry_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.input_folder_entry_tooltip = Tooltip(self.input_folder_entry_widget, "")
        self.input_folder_button_widget = ctk.CTkButton(self.folder_frame, command=self.select_input_folder, width=100)
        self.input_folder_button_widget.grid(row=1, column=2, padx=(5,10), pady=5)
        self.input_folder_button_tooltip = Tooltip(self.input_folder_button_widget, "")
        
        # 출력 폴더
        self.output_folder_label_widget = ctk.CTkLabel(self.folder_frame)
        self.output_folder_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.output_folder_entry_widget = ctk.CTkEntry(self.folder_frame, textvariable=self.output_folder_var, placeholder_text="Path to output folder")
        self.output_folder_entry_widget.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.output_folder_entry_tooltip = Tooltip(self.output_folder_entry_widget, "")
        self.output_folder_button_widget = ctk.CTkButton(self.folder_frame, command=self.select_output_folder, width=100)
        self.output_folder_button_widget.grid(row=2, column=2, padx=(5,10), pady=5)
        self.output_folder_button_tooltip = Tooltip(self.output_folder_button_widget, "")

        # --- API 언어 설정 (항상 영어로 표시) ---
        self.lang_frame_api = ctk.CTkFrame(self, corner_radius=10)
        self.lang_frame_api.grid(row=3, column=0, padx=10, pady=7, sticky="ew")
        self.lang_frame_api.grid_columnconfigure(1, weight=1) # 콤보박스 영역 확보
        self.lang_frame_api.grid_columnconfigure(3, weight=1) # 콤보박스 영역 확보
        self.lang_frame_api_title_label = ctk.CTkLabel(self.lang_frame_api, font=ctk.CTkFont(size=13, weight="bold"))
        self.lang_frame_api_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")

        self.source_content_lang_label_widget = ctk.CTkLabel(self.lang_frame_api)
        self.source_content_lang_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.source_combo_api_widget = ctk.CTkComboBox(self.lang_frame_api, variable=self.source_lang_for_api_var, 
                                                       values=self.api_lang_options_en, state='readonly', width=180)
        self.source_combo_api_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.source_combo_api_tooltip = Tooltip(self.source_combo_api_widget, "")
        
        self.target_trans_lang_label_widget = ctk.CTkLabel(self.lang_frame_api)
        self.target_trans_lang_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.target_combo_api_widget = ctk.CTkComboBox(self.lang_frame_api, variable=self.target_lang_for_api_var, 
                                                       values=self.api_lang_options_en, state='readonly', width=180)
        self.target_combo_api_widget.grid(row=1, column=3, sticky="ew", padx=10, pady=5)
        self.target_combo_api_tooltip = Tooltip(self.target_combo_api_widget, "")

        # --- 번역 상세 설정 ---
        self.setting_frame_details = ctk.CTkFrame(self, corner_radius=10)
        self.setting_frame_details.grid(row=4, column=0, padx=10, pady=7, sticky="ew")
        # 내부 그리드 컬럼 가중치 (Entry 위젯들이 공간을 나눠 갖도록)
        self.setting_frame_details.grid_columnconfigure(1, weight=1) 
        self.setting_frame_details.grid_columnconfigure(3, weight=1)
        self.setting_frame_details_title_label = ctk.CTkLabel(self.setting_frame_details, font=ctk.CTkFont(size=13, weight="bold"))
        self.setting_frame_details_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")

        # 배치 크기 (Spinbox 대신 CTkEntry 사용)
        self.batch_size_label_widget = ctk.CTkLabel(self.setting_frame_details)
        self.batch_size_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.batch_size_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.batch_size_var, width=80, justify='center')
        self.batch_size_entry_widget.grid(row=1, column=1, sticky="w", padx=(5,10), pady=5)
        self.batch_size_spinbox_tooltip = Tooltip(self.batch_size_entry_widget, "")
        
        # 동시 파일 수
        self.concurrent_files_label_widget = ctk.CTkLabel(self.setting_frame_details)
        self.concurrent_files_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.max_workers_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.max_workers_var, width=80, justify='center')
        self.max_workers_entry_widget.grid(row=1, column=3, sticky="w", padx=(5,10), pady=5)
        self.max_workers_spinbox_tooltip = Tooltip(self.max_workers_entry_widget, "")

        # 최대 출력 토큰
        self.max_output_tokens_label_widget = ctk.CTkLabel(self.setting_frame_details)
        self.max_output_tokens_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.max_tokens_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.max_tokens_var, width=80, justify='center')
        self.max_tokens_entry_widget.grid(row=2, column=1, sticky="w", padx=(5,10), pady=5)
        self.max_tokens_spinbox_tooltip = Tooltip(self.max_tokens_entry_widget, "")

        # 배치 간 대기
        self.batch_delay_label_widget = ctk.CTkLabel(self.setting_frame_details)
        self.batch_delay_label_widget.grid(row=2, column=2, sticky="w", padx=(20,10), pady=5)
        self.delay_entry_widget = ctk.CTkEntry(self.setting_frame_details, textvariable=self.delay_between_batches_var, width=80, justify='center')
        self.delay_entry_widget.grid(row=2, column=3, sticky="w", padx=(5,10), pady=5)
        self.delay_spinbox_tooltip = Tooltip(self.delay_entry_widget, "")
        
        # l_english 식별자 유지 옵션 (CTkCheckBox)
        self.lang_def_option_check_widget = ctk.CTkCheckBox(self.setting_frame_details, variable=self.keep_lang_def_unchanged_var, onvalue=True, offvalue=False)
        self.lang_def_option_check_widget.grid(row=3, column=0, columnspan=4, sticky="w", padx=10, pady=(10,5))
        self.lang_def_option_check_tooltip = Tooltip(self.lang_def_option_check_widget, "")

        # --- 번역 버튼 ---
        # 버튼들을 중앙에 배치하기 위해 별도 프레임 사용 및 grid 설정
        button_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_container_frame.grid(row=5, column=0, padx=10, pady=15, sticky="ew")
        button_container_frame.grid_columnconfigure(0, weight=1) # 빈 컬럼
        button_container_frame.grid_columnconfigure(1, weight=0) # 번역 버튼
        button_container_frame.grid_columnconfigure(2, weight=0) # 중지 버튼
        button_container_frame.grid_columnconfigure(3, weight=1) # 빈 컬럼

        self.translate_btn_widget = ctk.CTkButton(button_container_frame, command=self.start_translation, width=120, height=32, font=ctk.CTkFont(weight="bold"))
        self.translate_btn_widget.grid(row=0, column=1, padx=(0,5))
        self.translate_btn_tooltip = Tooltip(self.translate_btn_widget, "")

        self.stop_btn_widget = ctk.CTkButton(button_container_frame, command=self.stop_translation, state='disabled', width=120, height=32)
        self.stop_btn_widget.grid(row=0, column=2, padx=(5,0))
        self.stop_btn_tooltip = Tooltip(self.stop_btn_widget, "")
        
        # --- 진행 상황 ---
        self.progress_frame_display = ctk.CTkFrame(self, corner_radius=10)
        self.progress_frame_display.grid(row=6, column=0, padx=10, pady=7, sticky="ew")
        self.progress_frame_display.grid_columnconfigure(0, weight=1) # 내부 라벨 확장
        self.progress_frame_display_title_label = ctk.CTkLabel(self.progress_frame_display, font=ctk.CTkFont(size=13, weight="bold"))
        self.progress_frame_display_title_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(7,5)) # pack 사용

        self.progress_text_var = tk.StringVar()
        self.progress_label_widget = ctk.CTkLabel(self.progress_frame_display, textvariable=self.progress_text_var, anchor="w")
        self.progress_label_widget.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame_display, mode='indeterminate', height=10, corner_radius=5)
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,10))
        # indeterminate 모드에서는 progress_bar.start(), stop() 없음, 자동으로 움직임

        # --- 로그 출력 ---
        self.log_frame_display = ctk.CTkFrame(self, corner_radius=10)
        self.log_frame_display.grid(row=7, column=0, padx=10, pady=(7,10), sticky="nsew") # sticky "nsew"로 확장
        self.log_frame_display.grid_rowconfigure(1, weight=1) # Textbox가 확장되도록
        self.log_frame_display.grid_columnconfigure(0, weight=1) # Textbox가 확장되도록
        self.log_frame_display_title_label = ctk.CTkLabel(self.log_frame_display, font=ctk.CTkFont(size=13, weight="bold"))
        self.log_frame_display_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(7,5))

        self.log_text_widget = ctk.CTkTextbox(self.log_frame_display, wrap="word", corner_radius=8, border_width=1)
        self.log_text_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.log_text_widget.configure(state="disabled") # 초기에는 읽기 전용

    # --- update_ui_texts 함수 (이전 답변의 내용과 거의 동일, 위젯명 및 configure 사용) ---
    def update_ui_texts(self):
        current_code = self.current_lang_code.get()
        if current_code not in LANGUAGES: 
            current_code = "ko" 
            self.current_lang_code.set(current_code)
        self.texts = LANGUAGES[current_code]
        
        self.title(self.texts.get("title"))

        # UI 설정 프레임
        self.ui_settings_title_label.configure(text=self.texts.get("ui_settings_frame_title"))
        self.ui_lang_label_widget.configure(text=self.texts.get("ui_lang_label"))
        self.ui_lang_combo_tooltip.update_text(self.texts.get("ui_lang_tooltip"))
        
        self.appearance_mode_label_widget.configure(text=self.texts.get("appearance_mode_label"))
        appearance_mode_values = [self.texts.get("dark_mode"), self.texts.get("light_mode"), self.texts.get("system_mode")]
        self.appearance_mode_optionmenu.configure(values=appearance_mode_values)
        current_appearance = ctk.get_appearance_mode()
        if current_appearance == "Dark": self.appearance_mode_optionmenu.set(self.texts.get("dark_mode"))
        elif current_appearance == "Light": self.appearance_mode_optionmenu.set(self.texts.get("light_mode"))
        else: self.appearance_mode_optionmenu.set(self.texts.get("system_mode"))

        self.color_theme_label_widget.configure(text=self.texts.get("color_theme_label"))
        color_theme_values = [self.texts.get("blue_theme"), self.texts.get("green_theme"), self.texts.get("dark_blue_theme")]
        self.color_theme_optionmenu.configure(values=color_theme_values)
        # 현재 테마에 맞는 표시 텍스트 설정 (CustomTkinter는 현재 테마 '색상명'을 직접 가져오는 API가 명확하지 않음)
        # 여기서는 기본적으로 첫 번째 옵션(파랑)으로 설정하거나, 마지막으로 선택한 값을 저장/로드해야 함.
        # 지금은 간단히 첫 번째 값으로 설정.
        self.color_theme_optionmenu.set(color_theme_values[0])


        # 각 프레임 제목
        self.api_model_title_label.configure(text=self.texts.get("api_settings_frame"))
        self.folder_frame_title_label.configure(text=self.texts.get("folder_frame"))
        self.lang_frame_api_title_label.configure(text=self.texts.get("lang_settings_frame"))
        self.setting_frame_details_title_label.configure(text=self.texts.get("detailed_settings_frame"))
        self.progress_frame_display_title_label.configure(text=self.texts.get("progress_frame"))
        self.log_frame_display_title_label.configure(text=self.texts.get("log_frame"))

        # API 키 및 모델
        self.api_key_label_widget.configure(text=self.texts.get("api_key_label"))
        self.api_entry_tooltip.update_text(self.texts.get("api_key_tooltip"))
        self.model_label_widget.configure(text=self.texts.get("model_label"))
        self.model_combo_tooltip.update_text(self.texts.get("model_tooltip"))
        
        # 폴더 선택
        self.input_folder_label_widget.configure(text=self.texts.get("input_folder_label"))
        self.input_folder_entry_tooltip.update_text(self.texts.get("input_folder_tooltip"))
        self.input_folder_button_widget.configure(text=self.texts.get("browse_button"))
        self.input_folder_button_tooltip.update_text(self.texts.get("input_browse_tooltip"))
        self.output_folder_label_widget.configure(text=self.texts.get("output_folder_label"))
        self.output_folder_entry_tooltip.update_text(self.texts.get("output_folder_tooltip"))
        self.output_folder_button_widget.configure(text=self.texts.get("browse_button"))
        self.output_folder_button_tooltip.update_text(self.texts.get("output_browse_tooltip"))

        # API 언어 설정
        self.source_content_lang_label_widget.configure(text=self.texts.get("source_content_lang_label"))
        self.source_combo_api_tooltip.update_text(self.texts.get("source_content_lang_tooltip"))
        self.target_trans_lang_label_widget.configure(text=self.texts.get("target_trans_lang_label"))
        self.target_combo_api_tooltip.update_text(self.texts.get("target_trans_lang_tooltip"))
        
        # 번역 상세 설정
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

        # 버튼
        self.translate_btn_widget.configure(text=self.texts.get("translate_button"))
        self.translate_btn_tooltip.update_text(self.texts.get("translate_button_tooltip"))
        self.stop_btn_widget.configure(text=self.texts.get("stop_button"))
        self.stop_btn_tooltip.update_text(self.texts.get("stop_button_tooltip"))
        
        # 상태 메시지
        if not self.is_translating: # 번역 중이 아닐 때만 업데이트
            self.progress_text_var.set(self.texts.get("status_waiting"))

    # --- 나머지 함수들 (이전 답변의 로직을 기반으로, 문자열은 self.texts.get() 사용) ---
    # select_input_folder, select_output_folder, get_language_code, validate_inputs,
    # translate_batch, process_file, translation_worker, _update_ui_after_translation,
    # start_translation, stop_translation
    # 이 함수들 내에서 사용자에게 보여지는 모든 문자열(messagebox, 로그 등)은
    # self.texts.get("키", "기본값") 또는 self.log_message("로그키", arg1, ...) 형태로 변경해야 합니다.
    # (구현은 이전 답변을 참고하여 각 함수별로 적용 필요)

    # 예시: log_message, validate_inputs, start_translation, _update_ui_after_translation, stop_translation
    # (이전 답변에서 이 함수들의 다국어 처리 예시가 이미 제공되었으므로, 해당 부분을 참고하여 적용)
    # CTkProgressBar는 indeterminate 모드일 때 start/stop이 없으므로 해당 라인 제거 또는 주석 처리.

    # --- 이전 답변에서 가져온 함수들 (다국어 문자열 적용 필요) ---
    def select_input_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("select_input_folder_title", "입력 폴더 선택")) # 파일 다이얼로그 제목도 국제화 가능
        if folder:
            self.input_folder_var.set(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("select_output_folder_title", "출력 폴더 선택"))
        if folder:
            self.output_folder_var.set(folder)

    def log_message(self, message_key, *args):
        log_text_template = self.texts.get(message_key, message_key)
        try:
            formatted_message = log_text_template.format(*args)
        except (IndexError, KeyError, TypeError): # TypeError 추가
            formatted_message = log_text_template
            if args: formatted_message += " " + str(args)

        if hasattr(self, 'log_text_widget') and self.log_text_widget:
            self.log_text_widget.configure(state="normal")
            self.log_text_widget.insert("end", f"{time.strftime('%H:%M:%S')} - {formatted_message}\n") # tk.END 대신 "end"
            self.log_text_widget.see("end")
            self.log_text_widget.configure(state="disabled")
            self.update_idletasks()

    def validate_inputs(self):
        # 숫자 입력 필드 (Spinbox 대체된 CTkEntry) 값 검증 강화
        def is_valid_int(value_str, min_val, max_val):
            try:
                val = int(value_str)
                return min_val <= val <= max_val
            except ValueError: return False
        
        def is_valid_float(value_str, min_val, max_val):
            try:
                val = float(value_str)
                return min_val <= val <= max_val
            except ValueError: return False

        if not self.api_key_var.get().strip():
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_api_key_needed"))
            return False
        if not self.model_name_var.get(): # CTkComboBox는 variable로 직접 값을 가져옴
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_model_needed"))
            return False
        if not self.input_folder_var.get() or not os.path.exists(self.input_folder_var.get()):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_input_folder_invalid"))
            return False
        if not self.output_folder_var.get():
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_output_folder_needed"))
            return False
        
        # 숫자 입력 필드 값 검증
        if not is_valid_int(self.batch_size_var.get(), 1, 100):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_size_label')[:-1]})")
            return False
        if not is_valid_int(self.max_workers_var.get(), 1, 10):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('concurrent_files_label')[:-1]})")
            return False
        if not is_valid_int(self.max_tokens_var.get(), 1024, 32768):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('max_output_tokens_label')[:-1]})")
            return False
        if not is_valid_float(self.delay_between_batches_var.get(), 0.0, 5.0):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_delay_label')[:-1]})")
            return False
        return True

    # translate_batch, process_file, translation_worker, _update_ui_after_translation, start_translation, stop_translation 함수는
    # 이전 답변의 로직을 기반으로 하되, 모든 사용자에게 보여지는 문자열은 self.texts.get() 또는 self.log_message("키", ...) 사용
    # CTk 위젯에 맞게 상태 변경 (예: self.progress_bar는 indeterminate 모드이므로 start/stop 없음)
    # self.after() 를 사용하여 메인 스레드에서 UI 업데이트 (ctk.CTk 클래스는 self.after 사용 가능)
    
    # (이하 함수들은 이전 답변의 코드를 CustomTkinter 환경에 맞게 수정했다고 가정합니다.
    #  핵심은 UI 위젯 접근 방식과 상태 변경 방식, 그리고 모든 문자열의 국제화입니다.)
    #  get_language_code는 API용 영어 이름을 받으므로 변경 없음
    def get_language_code(self, lang_name_en):
        mapping = {'English':"english", 'French':"french", 'German':"german", 'Spanish':"spanish", 
                   'Japanese':"japanese", 'Korean':"korean", 'Portuguese':"portuguese", 
                   'Russian':"russian", 'Simplified Chinese':"simp_chinese", 'Turkish':"turkish"}
        return mapping.get(lang_name_en, "english")

    def translate_batch(self, text_batch, model, temperature=0.2, max_output_tokens=8192):
        batch_text = "\n".join([line.rstrip('\n') for line in text_batch])
        
        # API 프롬프트에 사용될 언어 이름 (항상 영어로 전달)
        source_lang_for_prompt = self.source_lang_for_api_var.get() # 예: "English"
        target_lang_for_prompt = self.target_lang_for_api_var.get() # 예: "Korean"

        # --- 영문 프롬프트 ---
        prompt = f"""Please translate the following YML formatted text from '{source_lang_for_prompt}' to '{target_lang_for_prompt}'.

You MUST adhere to the following rules strictly:
1. Only translate the text enclosed in double quotes after a colon (:). (e.g., `key: "text to translate"`)
2. Do NOT translate code-like strings, variable names (e.g., `$variable$`, `[variable]`, `<variable>`), special tags (e.g., `§Y`, `£gold£`), file paths, or URLs.
3. **CRITICAL**: You MUST preserve all original newline characters (\\n) and leading whitespace (indentation) for each line. Do NOT change or remove them. Each translated line must retain its original line break.
   Example:
   Original:
     key1: "First line\\nSecond line"
     key2: "  Indented text"
   Translation (assuming target is Korean):
     key1: "번역된 첫 번째 줄\\n번역된 두 번째 줄"
     key2: "  번역된 들여쓰기 텍스트"
4. Provide ONLY the translated text. Do NOT include any other explanations, headers, or footers.
5. Translate all personal names and proper nouns according to the context. (However, specific in-game unique item or skill names might be considered for keeping in original form).
6. If the content within quotes is a number, consists only of special characters, or is a simple path string (e.g., `gfx/interface/...`), do NOT translate it.
7. Do NOT translate YML comments (lines starting with '#'). Keep them as they are.
8. For each input line, you MUST output exactly one translated line. (Number of input lines = Number of output lines)

Text to translate:
```yaml
{batch_text}
```"""
        # --- 프롬프트 끝 ---

        try:
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_output_tokens))
            translated_text = ""
            finish_reason_val = 0 
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts: translated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                finish_reason_val = candidate.finish_reason
            elif hasattr(response, 'text') and response.text: translated_text = response.text
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                 self.log_message("log_batch_prompt_blocked", self.current_processing_file_for_log, response.prompt_feedback.block_reason)
                 return [line + '\n' if not line.endswith('\n') else line for line in text_batch]
            if finish_reason_val not in [0, 1]: 
                if finish_reason_val == 2: 
                    self.log_message("log_batch_token_limit", self.current_processing_file_for_log, finish_reason_val)
                    if len(text_batch) > 1:
                        mid = len(text_batch) // 2
                        first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens)
                        second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens)
                        return first_half + second_half
                    else:
                        self.log_message("log_batch_single_line_token_limit", self.current_processing_file_for_log)
                        return [line + '\n' if not line.endswith('\n') else line for line in text_batch]
                else: 
                    reason_str = f"Reason Code: {finish_reason_val}"
                    if response.candidates and response.candidates[0].safety_ratings: safety_str = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in response.candidates[0].safety_ratings]); reason_str += f" (Safety: {safety_str})"
                    self.log_message("log_batch_abnormal_termination", self.current_processing_file_for_log, reason_str)
                    return [line + '\n' if not line.endswith('\n') else line for line in text_batch]
            if not translated_text.strip():
                self.log_message("log_batch_empty_response", self.current_processing_file_for_log)
                return [line + '\n' if not line.endswith('\n') else line for line in text_batch]
            if translated_text.startswith("```yaml\n"): translated_text = translated_text[len("```yaml\n"):]
            if translated_text.endswith("\n```"): translated_text = translated_text[:-len("\n```")]
            if translated_text.startswith("```\n"): translated_text = translated_text[len("```\n"):]
            translated_lines_raw = translated_text.split('\n')
            processed_lines = []
            for i, translated_line_content in enumerate(translated_lines_raw):
                if i < len(text_batch):
                    original_line_ending = '\n' if text_batch[i].endswith('\n') else ''
                    current_line = translated_line_content
                    if not current_line.endswith('\n') and original_line_ending == '\n': current_line += '\n'
                    processed_lines.append(current_line)
            if len(processed_lines) < len(text_batch):
                self.log_message("log_batch_line_mismatch", self.current_processing_file_for_log)
                processed_lines.extend(text_batch[len(processed_lines):])
            return processed_lines
        except Exception as e:
            error_str = str(e).lower()
            if ("token" in error_str and ("limit" in error_str or "exceeded" in error_str or "max" in error_str)) or ("429" in error_str) or ("resource has been exhausted" in error_str):
                self.log_message("log_batch_api_limit_error_split", self.current_processing_file_for_log, str(e))
                if len(text_batch) > 1:
                    mid = len(text_batch) // 2
                    first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens)
                    second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens)
                    return first_half + second_half
                else:
                    self.log_message("log_batch_single_line_api_limit", self.current_processing_file_for_log)
                    return [line + '\n' if not line.endswith('\n') else line for line in text_batch]
            self.log_message("log_batch_unknown_error", self.current_processing_file_for_log, str(e))
            return [line + '\n' if not line.endswith('\n') else line for line in text_batch]

    def process_file(self, input_file, output_file, model):
        # (이전 답변의 process_file 로직, log_message 키 사용)
        self.current_processing_file_for_log = os.path.basename(input_file)
        try:
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f: lines = f.readlines()
            if not lines: self.log_message("log_file_empty", self.current_processing_file_for_log); return
            total_lines = len(lines); translated_lines_final = []
            self.log_message("log_file_process_start", self.current_processing_file_for_log, total_lines)
            start_index = 0
            first_line_identifier_pattern = re.compile(r"^\s*l_english\s*:", re.IGNORECASE)
            if first_line_identifier_pattern.match(lines[0]):
                original_first_line = lines[0]
                if self.keep_lang_def_unchanged_var.get():
                    translated_lines_final.append(original_first_line)
                    self.log_message("log_first_line_keep")
                else:
                    target_lang_code_str = self.get_language_code(self.target_lang_for_api_var.get())
                    new_first_line = first_line_identifier_pattern.sub(f"l_{target_lang_code_str}:", original_first_line)
                    translated_lines_final.append(new_first_line)
                    self.log_message("log_first_line_change", original_first_line.strip(), new_first_line.strip())
                start_index = 1
            if start_index >= total_lines and len(translated_lines_final) > 0 : self.log_message("log_file_only_identifier", self.current_processing_file_for_log)
            elif start_index >= total_lines and len(translated_lines_final) == 0: self.log_message("log_file_no_content_to_translate", self.current_processing_file_for_log)
            batch_size = self.batch_size_var.get(); current_max_tokens = self.max_tokens_var.get(); delay_time = self.delay_between_batches_var.get()
            for i in range(start_index, total_lines, batch_size):
                if not self.is_translating: self.log_message("log_file_process_stopped", self.current_processing_file_for_log); return
                batch_to_translate = lines[i:i+batch_size]
                self.log_message("log_batch_translate", i+1, min(i+batch_size, total_lines), total_lines)
                translated_batch_lines = self.translate_batch(batch_to_translate, model, max_output_tokens=current_max_tokens)
                translated_lines_final.extend(translated_batch_lines)
                if i + batch_size < total_lines and self.is_translating: time.sleep(delay_time)
            if not self.is_translating: return
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with codecs.open(output_file, 'w', encoding='utf-8-sig') as f: f.writelines(translated_lines_final)
            self.log_message("log_translation_complete_save", os.path.basename(output_file))
        except Exception as e: self.log_message("log_file_process_error", self.current_processing_file_for_log, str(e))
        finally: self.current_processing_file_for_log = ""

    def translation_worker(self):
        # (이전 답변의 translation_worker 로직, log_message 키 사용, self.after() 사용)
        model = None; completed_count = 0; total_files_to_process = 0
        try:
            api_key = self.api_key_var.get().strip(); selected_model_name = self.model_name_var.get()
            genai.configure(api_key=api_key); model = genai.GenerativeModel(selected_model_name)
            self.log_message("log_model_start", selected_model_name)
        except Exception as e:
            self.log_message("log_api_model_init_fail", str(e))
            self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process); return
        try:
            input_dir = self.input_folder_var.get(); output_dir = self.output_folder_var.get(); target_files = []
            file_identifier_for_search = "l_english"
            self.log_message("log_search_yml_files", file_identifier_for_search)
            for root_path, _, files_in_dir in os.walk(input_dir):
                for file_name in files_in_dir:
                    if file_identifier_for_search in file_name and file_name.endswith(('.yml', '.yaml')):
                        target_files.append(os.path.join(root_path, file_name))
            total_files_to_process = len(target_files)
            if not target_files:
                self.log_message("log_no_yml_files_found", input_dir, file_identifier_for_search)
                self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process); return
            self.log_message("log_total_files_start", total_files_to_process)
            self.after(0, lambda: self.progress_text_var.set(self.texts.get("status_translating_progress").format(0, total_files_to_process)))
            def process_single_file_wrapper(input_f):
                if not self.is_translating: return None
                relative_path = os.path.relpath(input_f, input_dir); output_f_path = os.path.join(output_dir, relative_path)
                if not self.keep_lang_def_unchanged_var.get():
                    base_name = os.path.basename(output_f_path); dir_name = os.path.dirname(output_f_path)
                    target_lang_code_for_filename = self.get_language_code(self.target_lang_for_api_var.get())
                    if "l_english" in base_name:
                        new_base_name = base_name.replace("l_english", f"l_{target_lang_code_for_filename}")
                        self.log_message("log_output_filename_change", base_name, new_base_name)
                        output_f_path = os.path.join(dir_name, new_base_name)
                self.process_file(input_f, output_f_path, model)
                return os.path.basename(input_f) if self.is_translating else None
            num_workers = self.max_workers_var.get()
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_file = {executor.submit(process_single_file_wrapper, f): f for f in target_files}
                for future in concurrent.futures.as_completed(future_to_file):
                    if not self.is_translating:
                        for f_cancel in future_to_file.keys():
                            if not f_cancel.done(): f_cancel.cancel()
                        break
                    try:
                        completed_filename = future.result()
                        if completed_filename:
                            completed_count +=1
                            self.log_message("log_file_completed", completed_filename)
                            self.after(0, lambda cc=completed_count, tt=total_files_to_process: self.progress_text_var.set(self.texts.get("status_translating_progress").format(cc,tt)))
                    except concurrent.futures.CancelledError: self.log_message("log_file_task_cancelled", os.path.basename(future_to_file[future]))
                    except Exception as exc: self.log_message("log_parallel_process_error", os.path.basename(future_to_file[future]), str(exc))
            final_log_msg_key = "log_all_translation_done" if self.is_translating else "log_translation_stopped_by_user"
            self.log_message(final_log_msg_key)
        except Exception as e: self.log_message("log_translation_process_error", str(e))
        finally:
            self.is_translating = False
            self.after(0, self._update_ui_after_translation, completed_count, total_files_to_process)
            self.current_processing_file_for_log = ""
    
    def _update_ui_after_translation(self, completed_count, total_files):
        # (이전 답변의 _update_ui_after_translation 로직, self.texts.get() 사용)
        self.translate_btn_widget.configure(state='normal')
        self.stop_btn_widget.configure(state='disabled')
        # self.progress_bar indeterminate 모드는 자동으로 멈춤 (별도 stop 없음)
        current_status = self.progress_text_var.get()
        no_files_text = self.texts.get("status_no_files")
        if total_files == 0 and (self.texts.get("log_no_yml_files_found_short") in current_status or self.texts.get("log_search_yml_files_short") in current_status) :
             final_message = no_files_text
        elif completed_count == total_files and total_files > 0 :
             final_message = self.texts.get("status_completed_all").format(completed_count, total_files)
        elif not self.is_translating and \
             self.texts.get("status_stopped_short") not in current_status and \
             self.texts.get("status_completed_some_short") not in current_status and \
             self.texts.get("status_completed_all_short") not in current_status:
             final_message = self.texts.get("status_stopped").format(completed_count, total_files)
        elif total_files > 0:
             final_message = self.texts.get("status_completed_some").format(completed_count, total_files)
        else: 
            final_message = self.texts.get("status_waiting")
        self.progress_text_var.set(final_message)

    def start_translation(self):
        # (이전 답변의 start_translation 로직, messagebox 및 로그 국제화)
        if not self.validate_inputs(): return
        if self.is_translating:
            messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_translating"))
            return
        self.is_translating = True
        self.translate_btn_widget.configure(state='disabled')
        self.stop_btn_widget.configure(state='normal')
        self.progress_text_var.set(self.texts.get("status_preparing"))
        self.log_text_widget.configure(state="normal"); self.log_text_widget.delete("1.0", "end"); self.log_text_widget.configure(state="disabled")
        try: os.makedirs(self.output_folder_var.get(), exist_ok=True)
        except OSError as e:
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_create_output_folder").format(str(e)))
            self.after(0, self._update_ui_after_translation, 0,0); self.is_translating = False; return
        self.translation_thread = threading.Thread(target=self.translation_worker, daemon=True)
        self.translation_thread.start()

    def stop_translation(self):
        # (이전 답변의 stop_translation 로직, messagebox 및 로그 국제화)
        if self.is_translating:
            self.is_translating = False
            self.log_message("log_stop_requested")
            self.stop_btn_widget.configure(state='disabled') 
        else:
            messagebox.showinfo(self.texts.get("info_title"), self.texts.get("info_no_translation_active"))

def main():
    # LANGUAGES 딕셔너리에 필요한 모든 키가 채워져 있다고 가정하고 실행
    # (실제로는 모든 키를 채우는 작업이 선행되어야 함)
    app = TranslationGUI()
    app.mainloop()

if __name__ == "__main__":
    main()