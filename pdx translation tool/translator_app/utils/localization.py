# translator_project/translator_app/utils/localization.py

# --- 언어별 UI 텍스트 및 메시지 ---
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
        "split_threshold_label": "파일 분할 기준(줄):", "split_threshold_tooltip": "이 줄 수를 초과하는 파일은 분할하여 번역합니다. (0이면 분할 안 함)",
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
        "glossary_error_not_found": "파일 없음", "glossary_error_empty": "빈 파일", "glossary_error_no_valid": "유효 항목 없음",
        "log_prompt_loaded_from_custom": "사용자 정의 프롬프트를 사용합니다.",
        "log_prompt_loaded_from_file": "파일 '{0}'에서 프롬프트를 로드했습니다.",
        "log_prompt_saved_to_file": "프롬프트가 파일 '{0}'에 저장되었습니다.",
        "log_prompt_reset_to_default": "프롬프트가 기본값으로 복원되었습니다.",
        "log_glossary_added": "용어집 '{0}' 추가됨.", "log_glossary_removed": "용어집 '{0}' 제거됨.",
        "log_combined_glossary_empty": "병합된 용어집이 비어있습니다.",
        "log_combined_glossary_info": "병합된 용어집에서 {0}개 유효 항목을 사용합니다.",
        "translate_button": "번역 시작", "translate_button_tooltip": "입력된 설정으로 모든 대상 파일의 번역을 시작합니다.",
        "stop_button": "중지", "stop_button_tooltip": "현재 진행 중인 번역 또는 검증 작업을 중지합니다.\n(이미 시작된 배치는 완료될 수 있습니다)",
        "progress_frame": "진행 상황",
        "status_waiting": "대기 중...", "status_translating": "번역 중...", "status_preparing": "준비 중...",
        "status_completed_all": "모든 파일 처리 완료 ({0}/{1})", "status_stopped": "작업 중지됨 ({0}/{1} 처리)",
        "status_completed_some": "일부 파일 처리 완료 ({0}/{1})", "status_no_files": "처리할 YML 파일을 찾지 못했습니다.",
        "log_frame": "실행 로그", "error_title": "오류", "warn_title": "경고", "info_title": "정보",
        "settings_saved_log": "설정이 저장되었습니다.",
        "error_api_key_needed": "Gemini API 키를 입력해야 합니다.", "error_model_needed": "번역 모델을 선택해야 합니다.",
        "error_input_folder_invalid": "올바른 입력 폴더를 선택해야 합니다.", "error_output_folder_needed": "출력 폴더를 선택해야 합니다.",
        "error_numeric_setting_invalid": "숫자 설정값이 올바르지 않습니다. 유효한 숫자를 입력해주세요.",
        "error_prompt_missing_placeholders": "프롬프트에 필수 플레이스홀더가 누락되었습니다: {0}",
        "warn_already_translating": "이미 번역 작업이 진행 중입니다. 기다려 주십시오.",
        "warn_already_validating": "이미 검증 작업이 진행 중입니다. 기다려 주십시오.",
        "warn_already_processing": "다른 작업(번역 또는 검증)이 이미 진행 중입니다.",
        "info_no_translation_active": "현재 진행 중인 번역 작업이 없습니다.",
        "info_no_validation_active": "현재 진행 중인 검증 작업이 없습니다.",
        "error_create_output_folder": "출력 폴더를 만들 수 없습니다: {0}",
        "log_api_model_init_fail": "API 또는 모델 초기화에 실패했습니다: {0}", "log_model_start": "'{0}' 모델을 사용하여 번역을 시작합니다.",
        "log_search_yml_files": "입력 폴더에서 파일명에 '{0}' 문자열을 포함하는 YML 파일을 찾고 있습니다...", "log_no_yml_files_found": "입력 폴더 '{0}'에서 파일명에 '{1}'을(를) 포함하는 YML 파일을 찾지 못했습니다.",
        "log_total_files_start": "총 {0}개의 파일을 번역합니다.", "log_file_empty": "파일 '{0}'이(가) 비어있어 건너<0xE1><0xB9><0xA5>니다.",
        "log_file_process_start": "파일 '{0}' ({1}줄) 처리(번역)를 시작합니다.", "log_first_line_keep": "  파일 첫 줄의 'l_english:' 식별자를 원본 그대로 유지합니다.",
        "log_first_line_change": "  파일 첫 줄 식별자를 '{0}'에서 '{1}'(으)로 변경합니다.", "log_file_only_identifier": "  파일 '{0}'은(는) 식별자 라인만 포함하고 있어, 내용 번역은 건너<0xE1><0xB9><0xA5>니다.",
        "log_file_no_content_to_translate": "  파일 '{0}'에 번역할 내용이 없습니다.", "log_batch_translate": "  텍스트 일부 번역 중: {0}~{1} / 총 {2}줄",
        "log_translation_complete_save": "번역 완료! 파일 '{0}'(으)로 저장되었습니다.", "log_file_process_error": "파일 '{0}' 처리 중 오류 발생: {1}",
        "log_output_filename_change": "  출력 파일명을 '{0}'에서 '{1}'(으)로 변경합니다.", "log_file_task_cancelled": "파일 '{0}' 처리 작업이 취소되었습니다.",
        "log_parallel_process_error": "파일 '{0}' 병렬 처리 중 오류 발생: {1}", "log_all_translation_done": "모든 파일의 번역 작업이 완료되었습니다!",
        "log_translation_stopped_by_user": "사용자에 의해 번역 작업이 중지되었습니다.", "log_translation_process_error": "번역 작업 중 전체 오류 발생: {0}",
        "log_stop_requested": "작업 중지 요청됨...", "ui_lang_self_name": "한국어",
        "log_batch_prompt_blocked": "파일 '{0}', 배치 처리: API 프롬프트가 차단되었습니다 (이유: {1}). 원본 내용을 반환합니다.", "log_batch_token_limit": "파일 '{0}', 배치 처리: API 출력 토큰 한계에 도달했습니다 (사유 코드: {1}). 배치를 나눠 다시 시도합니다.",
        "log_batch_single_line_token_limit": "파일 '{0}', 배치 처리: 한 줄의 내용도 토큰 한계를 초과합니다. 원본 내용을 반환합니다.", "log_batch_abnormal_termination": "파일 '{0}', 배치 처리: 번역이 비정상적으로 종료되었습니다 ({1}). 원본 내용을 반환합니다.",
        "log_batch_empty_response": "파일 '{0}', 배치 처리: API로부터 빈 응답을 받았습니다. 원본 내용을 반환합니다.", "log_batch_line_mismatch": "파일 '{0}', 배치 처리: 번역된 줄 수가 원본과 다릅니다. 부족한 부분은 원본으로 채웁니다.",
        "log_batch_api_limit_error_split": "파일 '{0}', 배치 처리: API 요청 제한 관련 오류 발생 ({1}). 배치를 나눠 다시 시도합니다.", "log_batch_single_line_api_limit": "파일 '{0}', 배치 처리: 한 줄의 내용도 API 요청 제한 오류가 발생했습니다. 원본 내용을 반환합니다.",
        "log_batch_unknown_error": "파일 '{0}', 배치 처리 중 알 수 없는 오류 발생: {1}", "log_file_process_stopped": "파일 '{0}' 처리 중 작업이 중지되었습니다.",
        "log_file_completed": "파일 처리 완료: {0}", "status_translating_progress": "번역 진행 중... ({0}/{1})",
        "log_no_yml_files_found_short": "파일 없음", "log_search_yml_files_short": "파일 검색 중...",
        "status_stopped_short": "중지됨", "status_completed_some_short": "일부 완료", "status_completed_all_short": "모두 완료",
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
        "log_glossary_error": "용어집 파일 '{0}' 로드 중 오류: {1}",

        # 검수 기능 텍스트
        "review_section_title": "번역 검수 대상 파일",
        "review_open_button": "선택 파일 검수",
        "review_hide_button": "검수 창 닫기",
        "review_no_files": "검수할 파일이 없습니다.",
        "review_select_file_first": "먼저 검수할 파일을 선택하세요.",
        "review_file_info_error": "선택된 파일 정보를 찾을 수 없습니다.",
        "review_window_title": "번역 검수",
        "review_original_label": "원본 (Original)",
        "review_translated_label": "번역본 (Translated)",
        "review_load_error_original": "원본 파일 로드 오류",
        "review_load_error_translated": "번역 파일 로드 오류",
        "review_load_error_placeholder": "# 번역 파일 로드 실패",
        "review_save_button": "저장",
        "review_save_as_button": "다른 이름으로 저장",
        "review_close_button": "닫기",
        "review_save_success": "변경 사항이 저장되었습니다.",
        "review_save_as_title": "다른 이름으로 저장",
        "review_save_as_success": "파일이 다음으로 저장되었습니다:",
        "review_save_error": "저장 중 오류 발생",

        # 파일 분할 번역 로그
        "log_file_split_start": "파일 '{0}'({1}줄)이 너무 커서 {2}줄 단위로 분할하여 번역합니다.",
        "log_processing_chunk": "청크 {0}/{1} ('{2}') 처리 중...",
        "log_merging_chunks": "번역된 청크들을 최종 파일 '{0}'(으)로 병합 중...",
        "log_chunk_processing_stopped": "파일 '{0}'의 청크 처리 중 중단되었습니다.",
        "log_chunk_processing_failed": "파일 '{0}'의 일부 청크 처리에 실패했습니다.",
        "log_temp_dir_created": "임시 청크 디렉토리 생성: {0}",
        "log_temp_dir_removed": "임시 청크 디렉토리 삭제: {0}",
        "log_temp_dir_remove_fail": "임시 청크 디렉토리 '{0}' 삭제 실패: {1}",

        
        "validation_section_title": "번역 후 검증 도구",
        "validation_open_window_button": "검증 창 열기",
        "validation_window_title": "번역 파일 검증",
        "validation_regex_error_check_label": "따옴표 형식 오류 검사",
        "validation_regex_error_check_tooltip": "잘못된 따옴표 사용 패턴을 검사합니다.\n(예: 값 내부의 홀따옴표, 공백 없이 이어지는 이중따옴표)",
        "validation_source_lang_check_label": "원본 언어 잔존 검사",
        "validation_source_lang_check_tooltip": "번역된 파일에 원본 언어의 텍스트가 그대로 남아있는지 검사합니다.",
        "validation_start_button": "검증 시작",
        "validation_no_output_folder": "출력 폴더가 설정되지 않아 검증할 수 없습니다.",
        "validation_no_files_in_output": "출력 폴더에 검증할 YML 파일이 없습니다.",
        "validation_running": "검증 진행 중...",
        "validation_running_progress": "검증 진행 중... ({0}/{1})",
        "validation_completed": "검증 완료.",
        "validation_error_file_line": "파일: {0}, 라인: {1}",
        "validation_error_regex": "  오류 유형: 따옴표 형식 오류 의심",
        "validation_error_source_lang_remaining": "  오류 유형: 원본 언어 잔존 의심",
        "validation_original_content": "    원본 내용: {0}",
        "validation_translated_content": "    번역 내용: {0}",
        "validation_no_issues_found": "선택된 검사에서 문제를 찾지 못했습니다.",
        "validation_select_checks": "하나 이상의 검증 항목을 선택하세요.",
        "validation_error_file_read": "파일 읽기 오류",
        "validation_status_idle": "검증 대기 중. 옵션을 선택하고 시작하세요.",
        "validation_status_no_output_folder_selected": "출력 폴더를 먼저 선택해주세요.",
        "validation_status_no_files_to_validate": "선택된 출력 폴더에 검증할 파일이 없습니다.",
        "warn_already_validating": "이미 검증 작업이 진행 중입니다. 기다려 주십시오.", # 이전 답변에 있었음
        "warn_already_processing": "다른 작업(번역 또는 검증)이 이미 진행 중입니다.", # 이전 답변에 있었음
        "info_no_validation_active": "현재 진행 중인 검증 작업이 없습니다.", # 이전 답변에 있었음
        "settings_saved_log": "설정이 저장되었습니다.", # 이전 답변에 있었음
        "review_section_title": "파일 비교/검수 도구", 
        "review_open_comparison_window_button": "파일 비교/검수 창 열기",
        "comparison_review_window_title": "파일 비교 및 검수",
        "comparison_review_select_folders_first": "원본 및 번역본 폴더를 모두 선택해주세요.",
        "comparison_review_no_matching_files": "두 폴더에서 이름이 유사한 파일 쌍을 찾을 수 없습니다.\n(예: l_english 와 l_korean)",
        "comparison_review_file_pair_list_label": "비교할 파일 쌍:",
        "comparison_review_load_pair_button": "선택 파일 쌍 로드",
        "comparison_review_display_all_lines": "모든 라인 표시",
        "comparison_review_display_diff_only": "차이점/오류 의심 라인만 표시",
        "comparison_review_diff_calculating": "차이점 계산 중...",
        "comparison_review_no_differences_found": "차이점을 찾지 못했습니다 (선택된 기준).",
        "comparison_review_original_content_label": "원본 파일 내용:",
        "comparison_review_translated_content_label": "번역 파일 내용 (수정 가능):",
        "comparison_review_save_changes_button": "변경 사항 저장 (번역 파일)",
        "comparison_review_line_num_prefix": "라인 {0}: ",
        "comparison_review_error_type_prefix": " [오류 의심: {0}]",
        "comparison_review_error_regex": "따옴표 형식",
        "comparison_review_error_source_lang": "원본 언어 잔존"
    },
    "en": {
        # title, ui_settings_frame_title, ... (기존 모든 영어 텍스트)
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
        "split_threshold_label": "File Split Threshold (lines):", "split_threshold_tooltip": "Files exceeding this line count will be split for translation. (0 for no split)",
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
        "glossary_error_not_found": "File Not Found", "glossary_error_empty": "Empty File", "glossary_error_no_valid": "No Valid Entries",
        "log_prompt_loaded_from_custom": "Using custom prompt.",
        "log_prompt_loaded_from_file": "Prompt loaded from file '{0}'.",
        "log_prompt_saved_to_file": "Prompt saved to file '{0}'.",
        "log_prompt_reset_to_default": "Prompt reset to default.",
        "log_glossary_added": "Glossary '{0}' added.", "log_glossary_removed": "Glossary '{0}' removed.",
        "log_combined_glossary_empty": "Combined glossary is empty.",
        "log_combined_glossary_info": "Using {0} valid items from the combined glossary.",
        "translate_button": "Start Translation", "translate_button_tooltip": "Starts translating all target files with the entered settings.",
        "stop_button": "Stop", "stop_button_tooltip": "Stops the currently ongoing translation or validation process.\n(Batches already started may complete)",
        "progress_frame": "Progress",
        "status_waiting": "Waiting...", "status_translating": "Translating...", "status_preparing": "Preparing...",
        "status_completed_all": "All files processed ({0}/{1})", "status_stopped": "Process stopped ({0}/{1} processed)",
        "status_completed_some": "Some files processed ({0}/{1})", "status_no_files": "No YML files found to process.",
        "log_frame": "Execution Log", "error_title": "Error", "warn_title": "Warning", "info_title": "Information",
        "settings_saved_log": "Settings have been saved.",
        "error_api_key_needed": "Gemini API key is required.", "error_model_needed": "A translation model must be selected.",
        "error_input_folder_invalid": "A valid input folder must be selected.", "error_output_folder_needed": "An output folder must be selected.",
        "error_numeric_setting_invalid": "Numeric setting is invalid. Please enter a valid number.",
        "error_prompt_missing_placeholders": "The prompt is missing required placeholders: {0}",
        "warn_already_translating": "Translation is already in progress. Please wait.",
        "warn_already_validating": "Validation is already in progress. Please wait.",
        "warn_already_processing": "Another process (translation or validation) is already in progress.",
        "info_no_translation_active": "No translation process is currently active.",
        "info_no_validation_active": "No validation process is currently active.",
        "error_create_output_folder": "Could not create output folder: {0}",
        "log_api_model_init_fail": "API or model initialization failed: {0}", "log_model_start": "Starting translation using '{0}' model.",
        "log_search_yml_files": "Searching for YML files containing '{0}' in their filename in the input folder...", "log_no_yml_files_found": "No YML files containing '{1}' in their filename found in input folder '{0}'.",
        "log_total_files_start": "Processing a total of {0} files (for translation).", "log_file_empty": "File '{0}' is empty, skipping.",
        "log_file_process_start": "Starting processing (translation) of file '{0}' ({1} lines).", "log_first_line_keep": "  Keeping the 'l_english:' identifier in the first line of the file as original.",
        "log_first_line_change": "  Changing the first line identifier from '{0}' to '{1}'.", "log_file_only_identifier": "  File '{0}' only contains the identifier line, skipping content translation.",
        "log_file_no_content_to_translate": "  File '{0}' has no content to translate.", "log_batch_translate": "  Translating text batch: lines {0}~{1} / total {2} lines",
        "log_translation_complete_save": "Translation complete! Saved to file '{0}'.", "log_file_process_error": "Error processing file '{0}': {1}",
        "log_output_filename_change": "  Changing output filename from '{0}' to '{1}'.", "log_file_task_cancelled": "Processing task for file '{0}' was cancelled.",
        "log_parallel_process_error": "Error during parallel processing of file '{0}': {1}", "log_all_translation_done": "Translation of all files completed!",
        "log_translation_stopped_by_user": "Translation process stopped by user.", "log_translation_process_error": "Global error during translation process: {0}",
        "log_stop_requested": "Stop process requested...", "ui_lang_self_name": "English",
        "log_batch_prompt_blocked": "File '{0}', batch processing: API prompt blocked (reason: {1}). Returning original content.", "log_batch_token_limit": "File '{0}', batch processing: API output token limit reached (reason code: {1}). Splitting batch and retrying.",
        "log_batch_single_line_token_limit": "File '{0}', batch processing: Single line content exceeds token limit. Returning original content.", "log_batch_abnormal_termination": "File '{0}', batch processing: Translation terminated abnormally ({1}). Returning original content.",
        "log_batch_empty_response": "File '{0}', batch processing: Received empty response from API. Returning original content.", "log_batch_line_mismatch": "File '{0}', batch processing: Translated line count differs from original. Missing lines filled with original content.",
        "log_batch_api_limit_error_split": "File '{0}', batch processing: API request limit error ({1}). Splitting batch and retrying.", "log_batch_single_line_api_limit": "File '{0}', batch processing: Single line content caused API request limit error. Returning original content.",
        "log_batch_unknown_error": "File '{0}', unknown error during batch processing: {1}", "log_file_process_stopped": "Processing stopped for file '{0}'.",
        "log_file_completed": "File processing completed: {0}", "status_translating_progress": "Translating... ({0}/{1})",
        "log_no_yml_files_found_short": "No files", "log_search_yml_files_short": "Searching files...",
        "status_stopped_short": "Stopped", "status_completed_some_short": "Partial", "status_completed_all_short": "All Done",
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
        "log_glossary_error": "Error loading glossary file '{0}': {1}",

        # Review feature texts
        "review_section_title": "Files for Translation Review",
        "review_open_button": "Review Selected File",
        "review_hide_button": "Close Review Pane",
        "review_no_files": "No files to review.",
        "review_select_file_first": "Please select a file to review first.",
        "review_file_info_error": "Could not find information for the selected file.",
        "review_window_title": "Translation Review",
        "review_original_label": "Original",
        "review_translated_label": "Translated",
        "review_load_error_original": "Error loading original file",
        "review_load_error_translated": "Error loading translated file",
        "review_load_error_placeholder": "# Failed to load translated file",
        "review_save_button": "Save",
        "review_save_as_button": "Save As",
        "review_close_button": "Close",
        "review_save_success": "Changes saved successfully.",
        "review_save_as_title": "Save As",
        "review_save_as_success": "File saved as:",
        "review_save_error": "Error saving file",
        "review_open_comparison_window_button": "Open File Comparison/Review Window",
        "comparison_review_window_title": "File Comparison and Review",
        "comparison_review_select_folders_first": "Please select both source and target folders.",
        "comparison_review_no_matching_files": "No similarly named file pairs found in the two folders.\n(e.g., l_english vs l_korean)",
        "comparison_review_file_pair_list_label": "File Pairs to Compare:",
        "comparison_review_load_pair_button": "Load Selected File Pair",
        "comparison_review_display_all_lines": "Display All Lines",
        "comparison_review_display_diff_only": "Display Differences/Suspected Errors Only",
        "comparison_review_diff_calculating": "Calculating differences...",
        "comparison_review_no_differences_found": "No differences found (based on selected criteria).",
        "comparison_review_original_content_label": "Original File Content:",
        "comparison_review_translated_content_label": "Translated File Content (Editable):",
        "comparison_review_save_changes_button": "Save Changes (to Translated File)",
        "comparison_review_line_num_prefix": "Line {0}: ",
        "comparison_review_error_type_prefix": " [Suspected Error: {0}]",
        "comparison_review_error_regex": "Quotation Format",
        "comparison_review_error_source_lang": "Source Language Remnant",

        # File splitting logs
        "log_file_split_start": "File '{0}' ({1} lines) is too large, splitting and translating in chunks of {2} lines.",
        "log_processing_chunk": "Processing chunk {0}/{1} ('{2}')...",
        "log_merging_chunks": "Merging translated chunks into final file '{0}'...",
        "log_chunk_processing_stopped": "Chunk processing stopped for file '{0}'.",
        "log_chunk_processing_failed": "Failed to process some chunks for file '{0}'.",
        "log_temp_dir_created": "Temporary chunk directory created: {0}",
        "log_temp_dir_removed": "Temporary chunk directory removed: {0}",
        "log_temp_dir_remove_fail": "Failed to remove temporary chunk directory '{0}': {1}",

         # Validation feature texts
        "validation_section_title": "Post-Translation Validation Tools",
        "validation_open_window_button": "Open Validation Window",
        "validation_window_title": "Validate Translated Files",
        "validation_regex_error_check_label": "Quotation Format Error Check",
        "validation_regex_error_check_tooltip": "Checks for incorrect quotation usage patterns.\n(e.g., lone quotes within values, double quotes without preceding space)",
        "validation_source_lang_check_label": "Source Language Remnants Check",
        "validation_source_lang_check_tooltip": "Checks if text from the source language remains in the translated file.",
        "validation_start_button": "Start Validation",
        "validation_no_output_folder": "Output folder is not set for validation.",
        "validation_no_files_in_output": "No YML files found in the output folder to validate.",
        "validation_running": "Validation in progress...",
        "validation_running_progress": "Validation in progress... ({0}/{1})",
        "validation_completed": "Validation completed.",
        "validation_error_file_line": "File: {0}, Line: {1}",
        "validation_error_regex": "  Error Type: Suspected quotation format error",
        "validation_error_source_lang_remaining": "  Error Type: Suspected source language remnants",
        "validation_original_content": "    Original: {0}",
        "validation_translated_content": "    Translated: {0}",
        "validation_no_issues_found": "No issues found with the selected checks.",
        "validation_select_checks": "Please select at least one validation check.",
        "validation_error_file_read": "Error reading file",
        "validation_status_idle": "Waiting for validation. Select options and start.",
        "validation_status_no_output_folder_selected": "Please select an output folder first.",
        "validation_status_no_files_to_validate": "No files to validate in the selected output folder.",
        "warn_already_validating": "Validation is already in progress. Please wait.", # Was in previous answers
        "warn_already_processing": "Another process (translation or validation) is already in progress.", # Was in previous answers
        "info_no_validation_active": "No validation process is currently active.", # Was in previous answers
        "settings_saved_log": "Settings have been saved.", # Was in previous answers
        "review_section_title": "File Comparison/Review Tool",
        "review_open_comparison_window_button": "Open File Comparison/Review Window",
        "comparison_review_window_title": "File Comparison and Review",
        "comparison_review_select_folders_first": "Please select both source and target folders.",
        "comparison_review_no_matching_files": "No similarly named file pairs found in the two folders.\n(e.g., l_english vs l_korean)",
        "comparison_review_file_pair_list_label": "File Pairs to Compare:",
        "comparison_review_load_pair_button": "Load Selected File Pair",
        "comparison_review_display_all_lines": "Display All Lines",
        "comparison_review_display_diff_only": "Display Differences/Suspected Errors Only",
        "comparison_review_diff_calculating": "Calculating differences...",
        "comparison_review_no_differences_found": "No differences found (based on selected criteria).",
        "comparison_review_original_content_label": "Original File Content:",
        "comparison_review_translated_content_label": "Translated File Content (Editable):",
        "comparison_review_save_changes_button": "Save Changes (to Translated File)",
        "comparison_review_line_num_prefix": "Line {0}: ",
        "comparison_review_error_type_prefix": " [Suspected Error: {0}]",
        "comparison_review_error_regex": "Quotation Format",
        "comparison_review_error_source_lang": "Source Language Remnant"
    },
      "zh_CN": {
        "title": "P社游戏模组翻译器 v0.3", # 이전과 동일
        "ui_settings_frame_title": "界面设置", # 이전과 동일
        "ui_lang_label": "界面语言：", "ui_lang_tooltip": "更改程序界面的显示语言。", # 이전과 동일
        "appearance_mode_label": "主题模式：", "dark_mode": "深色", "light_mode": "浅色", "system_mode": "系统默认", # 이전과 동일
        "api_settings_frame": "API 及模型设置", # 이전과 동일
        "api_key_label": "Gemini API 密钥：", "api_key_tooltip": "请输入从 Google AI Studio 获取的 Gemini API 密钥。\n例如：AIzaSy...", # 이전과 동일
        "model_label": "翻译模型：", "model_tooltip": "选择用于翻译的 Gemini 模型。\n不同模型的性能和成本可能有所不同。", # 이전과 동일
        "folder_frame": "文件夹选择", # 이전과 동일
        "input_folder_label": "输入文件夹：", "input_folder_tooltip": "选择包含待翻译的原始 YML 文件的文件夹。", # 이전과 동일
        "browse_button": "浏览", "input_browse_tooltip": "打开文件浏览器以选择输入文件夹。", # 이전과 동일
        "output_folder_label": "输出文件夹：", "output_folder_tooltip": "选择用于保存已翻译 YML 文件的文件夹。", # 이전과 동일
        "output_browse_tooltip": "打开文件浏览器以选择输出文件夹。", # 이전과 동일
        "lang_settings_frame": "翻译语言设置 (用于 API 请求)", # 이전과 동일
        "source_content_lang_label": "源内容语言：", "source_content_lang_tooltip": "选择 YML 文件内文本的实际源语言。\n此信息将传递给 API 以提高翻译质量。", # 이전과 동일
        "target_trans_lang_label": "目标翻译语言：", "target_trans_lang_tooltip": "选择要将文本翻译成的语言。\n输出文件的语言标识符（例如 l_korean）也可能根据此设置更改。", # 이전과 동일
        "detailed_settings_frame": "翻译详细设置", # 이전과 동일
        "batch_size_label": "批处理大小：", "batch_size_tooltip": "一次发送到 API 进行翻译的文本行数。\n如果设置过大，API 可能无响应或发生错误。", # 이전과 동일
        "concurrent_files_label": "并发文件数：", "concurrent_files_tooltip": "同时翻译多个文件时，设置一次并行处理的文件数量。\n请根据您的计算机性能进行调整。", # 이전과 동일
        "max_output_tokens_label": "最大输出令牌数：", "max_output_tokens_tooltip": "以令牌为单位限制翻译结果（文本）的最大长度。\n请注意不要超过所选模型的最大令牌限制。", # 이전과 동일
        "batch_delay_label": "批次间延迟（秒）：", "batch_delay_tooltip": "设置每个翻译批处理请求之间的等待时间（以秒为单位）。\n有助于避免超出 API 每分钟请求限制。", # 이전과 동일
        "split_threshold_label": "文件拆分阈值(行)：", "split_threshold_tooltip": "超过此行数的文件将被拆分翻译。(0表示不拆分)", # 신규
        "keep_identifier_label": "保留原始 l_english 标识符", "keep_identifier_tooltip": "选中时：文件首行的 'l_english:' 及文件名中的 'l_english' 部分保持不变。\n未选中时：根据“目标翻译语言”进行更改（例如：l_korean）。", # 이전과 동일
        "check_internal_lang_label": "当内部语言与文件名不同时，优先使用UI设置",
        "check_internal_lang_tooltip": "选中时：如果文件名或文件首行的语言标识符与UI“源内容语言”设置不同，则优先使用UI设置传递给翻译API。\n（例如：l_english 文件但内容为中文时，若UI源语言设置为中文，则视为中文）。\n相关信息会记录在日志中。", # 이전과 동일
        "prompt_glossary_frame_title": "提示词与术语表管理", # 이전과 동일
        "prompt_edit_frame_title": "编辑提示词", # 이전과 동일
        "prompt_edit_textbox_tooltip": "这是将传递给翻译 API 的提示词。\n必须保留 {source_lang_for_prompt}、{target_lang_for_prompt}、{glossary_section}、{batch_text} 这些占位符。", # 이전과 동일
        "load_prompt_button": "从文件加载", "load_prompt_button_tooltip": "从文本文件加载提示词。", # 이전과 동일
        "save_prompt_button": "保存到文件", "save_prompt_button_tooltip": "将当前提示词保存到文本文件。", # 이전과 동일
        "reset_prompt_button": "恢复默认值", "reset_prompt_button_tooltip": "将提示词重置为程序默认值。", # 이전과 동일
        "prompt_file_load_title": "加载提示词文件", # 이전과 동일
        "prompt_file_save_title": "保存提示词文件", # 이전과 동일
        "glossary_management_frame_title": "术语表管理", # 이전과 동일
        "add_glossary_button": "添加术语表", "add_glossary_button_tooltip": "将新的术语表文件添加到列表中。", # 이전과 동일
        "remove_glossary_button": "移除选定术语表", "remove_glossary_button_tooltip": "从列表中移除选定的术语表文件。", # 이전과 동일 (UI에 직접 버튼이 없으므로 사용되지 않을 수 있음)
        "glossary_list_tooltip": "已激活的术语表列表。用于翻译。", # 이전과 동일
        "glossary_file_select_title": "选择术语表文件", # 이전과 동일
        "glossary_item_loaded": "已加载: {0} ({1} 个条目)", "glossary_item_error": "错误: {0}", "glossary_item_empty": "为空: {0}", # 이전과 동일
        "glossary_error_not_found": "文件未找到", "glossary_error_empty": "空文件", "glossary_error_no_valid": "无有效条目", # 신규
        "log_prompt_loaded_from_custom": "正在使用自定义提示词。", # 이전과 동일
        "log_prompt_loaded_from_file": "已从文件 '{0}' 加载提示词。", # 이전과 동일
        "log_prompt_saved_to_file": "提示词已保存到文件 '{0}'。", # 이전과 동일
        "log_prompt_reset_to_default": "提示词已重置为默认值。", # 이전과 동일
        "log_glossary_added": "已添加术语表 '{0}'。", # 이전과 동일
        "log_glossary_removed": "已移除术语表 '{0}'。", # 이전과 동일
        "log_combined_glossary_empty": "合并后的术语表为空。", # 이전과 동일
        "log_combined_glossary_info": "正在使用合并后术语表中的 {0} 个有效条目。", # 이전과 동일
        "translate_button": "开始翻译", "translate_button_tooltip": "使用输入的设置开始翻译所有目标文件。", # 이전과 동일
        "stop_button": "停止", "stop_button_tooltip": "停止当前正在进行的翻译或验证任务。\n（已开始的批处理可能会完成）", # 수정됨
        "progress_frame": "进度", # 이전과 동일
        "status_waiting": "等待中...", "status_translating": "翻译中...", "status_preparing": "准备中...", # 수정됨
        "status_completed_all": "所有文件处理完成 ({0}/{1})", "status_stopped": "任务已停止 ({0}/{1} 已处理)", # 수정됨
        "status_completed_some": "部分文件处理完成 ({0}/{1})", "status_no_files": "未找到要处理的 YML 文件。", # 수정됨
        "log_frame": "运行日志", "error_title": "错误", "warn_title": "警告", "info_title": "信息", # 이전과 동일
        "settings_saved_log": "设置已保存。", # 신규
        "error_api_key_needed": "需要输入 Gemini API 密钥。", "error_model_needed": "必须选择翻译模型。", # 이전과 동일
        "error_input_folder_invalid": "必须选择一个有效的输入文件夹。", "error_output_folder_needed": "必须选择输出文件夹。", # 이전과 동일
        "error_numeric_setting_invalid": "数字设置无效。请输入一个有效的数字。", # 이전과 동일
        "error_prompt_missing_placeholders": "提示词中缺少必要的占位符：{0}", # 신규
        "warn_already_translating": "翻译任务已在进行中。请稍候。", # 이전과 동일
        "warn_already_validating": "验证任务已在进行中。请稍候。", # 신규
        "warn_already_processing": "其他任务（翻译或验证）已在进行中。", # 신규
        "info_no_translation_active": "当前没有正在进行的翻译任务。", # 이전과 동일
        "info_no_validation_active": "当前没有正在进行的验证任务。", # 신규
        "error_create_output_folder": "无法创建输出文件夹：{0}", # 이전과 동일
        "log_api_model_init_fail": "API 或模型初始化失败：{0}", "log_model_start": "开始使用 '{0}' 模型进行翻译。", # 이전과 동일
        "log_search_yml_files": "正在输入文件夹中搜索文件名包含 '{0}' 字符串的 YML 文件...", "log_no_yml_files_found": "在输入文件夹 '{0}' 中未找到文件名包含 '{1}' 的 YML 文件。", # 이전과 동일
        "log_total_files_start": "共处理 {0} 个文件 (用于翻译)。", "log_file_empty": "文件 '{0}' 为空，已跳过。", # 수정됨
        "log_file_process_start": "开始处理 (翻译) 文件 '{0}' ({1} 行)。", "log_first_line_keep": "  文件首行的 'l_english:' 标识符将保持原始状态。", # 수정됨
        "log_first_line_change": "  将文件首行标识符从 '{0}' 更改为 '{1}'。", "log_file_only_identifier": "  文件 '{0}' 仅包含标识符行，跳过内容翻译。", # 이전과 동일
        "log_file_no_content_to_translate": "  文件 '{0}' 没有可翻译的内容。", "log_batch_translate": "  正在翻译部分文本：{0}~{1} 行 / 共 {2} 行", # 이전과 동일
        "log_translation_complete_save": "翻译完成！已保存到文件 '{0}'。", "log_file_process_error": "处理文件 '{0}' 时发生错误：{1}", # 이전과 동일
        "log_output_filename_change": "  将输出文件名从 '{0}' 更改为 '{1}'。", "log_file_task_cancelled": "文件 '{0}' 的处理任务已取消。", # 수정됨
        "log_parallel_process_error": "并行处理文件 '{0}' 时发生错误：{1}", "log_all_translation_done": "所有文件的翻译任务已完成！", # 이전과 동일
        "log_translation_stopped_by_user": "翻译任务已被用户停止。", "log_translation_process_error": "翻译过程中发生全局错误：{0}", # 이전과 동일
        "log_stop_requested": "已请求停止任务...", "ui_lang_self_name": "简体中文", # 수정됨
        "log_batch_prompt_blocked": "文件 '{0}', 批处理：API 提示词被阻止 (原因: {1})。返回原始内容。", "log_batch_token_limit": "文件 '{0}', 批处理：已达到 API 输出令牌限制 (原因代码: {1})。将拆分批次并重试。", # 이전과 동일
        "log_batch_single_line_token_limit": "文件 '{0}', 批处理：单行内容也超出令牌限制。返回原始内容。", "log_batch_abnormal_termination": "文件 '{0}', 批处理：翻译异常终止 ({1})。返回原始内容。", # 이전과 동일
        "log_batch_empty_response": "文件 '{0}', 批处理：从 API 收到空响应。返回原始内容。", "log_batch_line_mismatch": "文件 '{0}', 批处理：翻译后的行数与原始行数不符。缺失部分将用原始内容填充。", # 이전과 동일
        "log_batch_api_limit_error_split": "文件 '{0}', 批处理：发生 API 请求限制相关错误 ({1})。将拆分批次并重试。", "log_batch_single_line_api_limit": "文件 '{0}', 批处理：单行内容也发生 API 请求限制错误。返回原始内容。", # 이전과 동일
        "log_batch_unknown_error": "文件 '{0}', 批处理过程中发生未知错误: {1}", "log_file_process_stopped": "处理文件 '{0}' 时任务已停止。", # 수정됨
        "log_file_completed": "文件处理完成: {0}", "status_translating_progress": "翻译进行中... ({0}/{1})", # 수정됨
        "log_no_yml_files_found_short": "无文件", "log_search_yml_files_short": "正在搜索文件...", # 이전과 동일
        "status_stopped_short": "已停止", "status_completed_some_short": "部分完成", "status_completed_all_short": "全部完成", # 수정됨
        "log_internal_lang_mismatch_using_ui": "文件 '{0}' 中的首行标识符 '{1}' 与 UI 中设置的源语言 '{2}' 不同。将使用 UI 设置进行翻译。",
        "log_internal_lang_no_identifier_using_ui": "在文件 '{0}' 中找不到语言标识符。将使用 UI 中设置的源语言 '{1}' 进行翻译。", # 이전과 동일
        "prompt_template_file_label": "提示词模板文件：",
        "prompt_template_file_tooltip": "包含传递给 API 的翻译指令的文本文件。\n（默认值：程序文件夹内的 'prompt_template.txt'）", # 이전과 동일
        "prompt_file_status_ok": "正在使用 '{0}'",
        "prompt_file_status_default": "正在使用默认提示词",
        "prompt_file_status_error": "文件错误！使用默认提示词", # 이전과 동일
        "glossary_file_label": "术语表文件 (可选)：",
        "glossary_file_tooltip": "包含翻译时参考的专有名词列表的文本文件。\n每行以“英语单词:翻译后单词”格式编写。", # 이전과 동일
        "browse_glossary_button_tooltip": "打开文件浏览器以选择术语表文件。", # 이전과 동일
        "glossary_file_status_ok": "正在使用 '{0}' ({1} 个条目)",
        "glossary_file_status_not_used": "未使用术语表",
        "glossary_file_status_empty": "术语表为空", # 이전과 동일
        "select_glossary_file_title": "选择术语表文件", # 이전과 동일
        "log_prompt_file_loaded": "已从提示词模板文件 '{0}' 加载。",
        "log_prompt_file_not_found_using_default": "找不到提示词模板文件 '{0}'。将使用内置的默认提示词。",
        "log_prompt_file_error_using_default": "加载提示词模板文件 '{0}' 时出错 ({1})。将使用内置的默认提示词。", # 이전과 동일
        "log_glossary_loaded": "已从术语表文件 '{0}' 加载 {1} 个条目。",
        "log_glossary_not_selected_or_empty": "未选择术语表文件或文件为空，不使用。",
        "log_glossary_error": "加载术语表文件 '{0}' 时出错：{1}", # 이전과 동일

        # 검수 기능 텍스트
        "review_section_title": "翻译校对文件列表",
        "review_open_button": "校对选定文件",
        "review_hide_button": "关闭校对窗口",
        "review_no_files": "没有可校对的文件。",
        "review_select_file_first": "请先选择要校对的文件。",
        "review_file_info_error": "找不到所选文件的信息。",
        "review_window_title": "翻译校对",
        "review_original_label": "原文 (Original)",
        "review_translated_label": "译文 (Translated)",
        "review_load_error_original": "加载原文文件出错",
        "review_load_error_translated": "加载译文文件出错",
        "review_load_error_placeholder": "# 加载译文文件失败",
        "review_save_button": "保存",
        "review_save_as_button": "另存为",
        "review_close_button": "关闭",
        "review_save_success": "更改已保存。",
        "review_save_as_title": "另存为",
        "review_save_as_success": "文件已另存为：",
        "review_save_error": "保存文件时出错",

        # 파일 분할 번역 로그
        "log_file_split_start": "文件 '{0}' ({1}行) 过大，将按 {2} 行拆分翻译。",
        "log_processing_chunk": "正在处理分块 {0}/{1} ('{2}')...",
        "log_merging_chunks": "正在将翻译后的分块合并到最终文件 '{0}'...",
        "log_chunk_processing_stopped": "文件 '{0}' 的分块处理已停止。",
        "log_chunk_processing_failed": "文件 '{0}' 的部分分块处理失败。",
        "log_temp_dir_created": "已创建临时分块目录：{0}",
        "log_temp_dir_removed": "已删除临时分块目录：{0}",
        "log_temp_dir_remove_fail": "删除临时分块目录 '{0}' 失败：{1}",

        # Validation feature texts (验证功能文本)
        "validation_section_title": "翻译后验证工具",
        "validation_open_window_button": "打开验证窗口",
        "validation_window_title": "验证翻译文件",
        "validation_regex_error_check_label": "引号格式错误检查",
        "validation_regex_error_check_tooltip": "检查不正确的引号使用模式。\n（例如：值内部的单个引号，前面没有空格的双引号）",
        "validation_source_lang_check_label": "原文残留检查",
        "validation_source_lang_check_tooltip": "检查翻译后的文件中是否残留原文文本。",
        "validation_start_button": "开始验证",
        "validation_no_output_folder": "未设置输出文件夹，无法验证。",
        "validation_no_files_in_output": "输出文件夹中没有可验证的 YML 文件。",
        "validation_running": "验证进行中...",
        "validation_running_progress": "验证进行中... ({0}/{1})",
        "validation_completed": "验证完成。",
        "validation_error_file_line": "文件：{0}，行：{1}",
        "validation_error_regex": "  错误类型：疑似引号格式错误",
        "validation_error_source_lang_remaining": "  错误类型：疑似原文残留",
        "validation_original_content": "    原文内容：{0}",
        "validation_translated_content": "    译文内容：{0}",
        "validation_no_issues_found": "选定的检查未发现问题。",
        "validation_select_checks": "请至少选择一个验证项。",
        "validation_error_file_read": "读取文件错误",
        "validation_status_idle": "等待验证。请选择选项并开始。",
        "validation_status_no_output_folder_selected": "请先选择输出文件夹。",
        "validation_status_no_files_to_validate": "所选输出文件夹中没有可验证的文件。",
        "warn_already_validating": "验证任务已在进行中。请稍候。", # 之前答案中已有
        "warn_already_processing": "其他任务（翻译或验证）已在进行中。", # 之前答案中已有
        "info_no_validation_active": "当前没有正在进行的验证任务。", # 之前答案中已有
        "settings_saved_log": "设置已保存。", # 之前答案中已有
        "review_section_title": "文件比较/校对工具",
        "review_open_comparison_window_button": "打开文件比较/校对窗口",
        "comparison_review_window_title": "文件比较与校对",
        "comparison_review_select_folders_first": "请同时选择源文件夹和目标文件夹。",
        "comparison_review_no_matching_files": "在两个文件夹中找不到名称相似的文件对。\n（例如：l_english 与 l_korean）",
        "comparison_review_file_pair_list_label": "待比较文件对：",
        "comparison_review_load_pair_button": "加载选定文件对",
        "comparison_review_display_all_lines": "显示所有行",
        "comparison_review_display_diff_only": "仅显示差异/疑似错误行",
        "comparison_review_diff_calculating": "正在计算差异...",
        "comparison_review_no_differences_found": "未找到差异（根据所选标准）。",
        "comparison_review_original_content_label": "原文文件内容：",
        "comparison_review_translated_content_label": "译文文件内容（可编辑）：",
        "comparison_review_save_changes_button": "保存更改（至译文文件）",
        "comparison_review_line_num_prefix": "行 {0}: ",
        "comparison_review_error_type_prefix": " [疑似错误: {0}]",
        "comparison_review_error_regex": "引号格式",
        "comparison_review_error_source_lang": "原文残留"
    }
}

def get_language_code(lang_name_en):
    """Converts English language name to Paradox-style language code."""
    mapping = {
        'English': "english",
        'Korean': "korean",
        'Simplified Chinese': "simp_chinese",
        'French': "french",
        'German': "german",
        'Spanish': "spanish",
        'Japanese': "japanese",
        'Portuguese': "portuguese",
        'Russian': "russian",
        'Turkish': "turkish"
    }
    return mapping.get(lang_name_en, "english")

def get_language_name(lang_code):
    """Converts Paradox-style language code back to its English language name."""
    mapping = {
        "english": 'English',
        "korean": 'Korean',
        "simp_chinese": 'Simplified Chinese',
        "french": 'French',
        "german": 'German',
        "spanish": 'Spanish',
        "japanese": 'Japanese',
        "portuguese": 'Portuguese',
        "russian": 'Russian',
        "turkish": 'Turkish'
    }
    return mapping.get(lang_code.lower(), 'English')
