# translator_project/translator_app/core/settings_manager.py
import json
import os
from .config import CONFIG_FILE

class SettingsManager:
    def __init__(self, default_prompt_template, default_available_models):
        self.default_prompt_template = default_prompt_template
        self.default_model = default_available_models[0] if default_available_models else ""

    def load_settings(self, app_vars):
        """
        app_vars: UI의 StringVar/IntVar 등을 담은 딕셔너리
        예: {"api_key_var": api_key_var, "input_folder_var": input_folder_var, ...}
        반환값: loaded_prompt_from_config, loaded_glossaries
        """
        loaded_prompt = None
        loaded_glossaries_paths = []
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                app_vars["ui_lang_var"].set(config.get("ui_language", "ko"))
                app_vars["appearance_mode_var"].set(config.get("appearance_mode", "Dark"))
                app_vars["api_key_var"].set(config.get("api_key", ""))
                app_vars["input_folder_var"].set(config.get("input_folder", ""))
                app_vars["output_folder_var"].set(config.get("output_folder", ""))
                app_vars["model_name_var"].set(config.get("model_name", self.default_model))
                app_vars["source_lang_api_var"].set(config.get("source_lang_api", "English"))
                app_vars["target_lang_api_var"].set(config.get("target_lang_api", "Korean"))
                app_vars["batch_size_var"].set(config.get("batch_size", 25))
                app_vars["max_workers_var"].set(config.get("max_workers", 3))
                app_vars["max_tokens_var"].set(config.get("max_tokens", 8192))
                app_vars["delay_between_batches_var"].set(config.get("delay_between_batches", 0.8))
                app_vars["keep_identifier_var"].set(config.get("keep_identifier", False))
                app_vars["check_internal_lang_var"].set(config.get("check_internal_lang", False))

                prompt_str = config.get("custom_prompt", self.default_prompt_template)
                if prompt_str != self.default_prompt_template:
                    loaded_prompt = prompt_str

                loaded_glossaries_paths = config.get("glossaries", [])

        except Exception as e:
            print(f"설정 로드 오류: {e}") # GUI log_message 대신 print 사용
        return loaded_prompt, loaded_glossaries_paths

    def save_settings(self, app_vars, current_prompt, glossary_file_paths, current_appearance_mode):
        """
        app_vars: UI의 StringVar/IntVar 등을 담은 딕셔너리
        current_prompt: 현재 프롬프트 텍스트
        glossary_file_paths: 현재 용어집 파일 경로 리스트
        current_appearance_mode: 현재 테마 모드 (ctk.get_appearance_mode() 값)
        """
        config = {
            "ui_language": app_vars["ui_lang_var"].get(),
            "appearance_mode": current_appearance_mode,
            "api_key": app_vars["api_key_var"].get(),
            "input_folder": app_vars["input_folder_var"].get(),
            "output_folder": app_vars["output_folder_var"].get(),
            "model_name": app_vars["model_name_var"].get(),
            "source_lang_api": app_vars["source_lang_api_var"].get(),
            "target_lang_api": app_vars["target_lang_api_var"].get(),
            "batch_size": app_vars["batch_size_var"].get(),
            "max_workers": app_vars["max_workers_var"].get(),
            "max_tokens": app_vars["max_tokens_var"].get(),
            "delay_between_batches": app_vars["delay_between_batches_var"].get(),
            "keep_identifier": app_vars["keep_identifier_var"].get(),
            "check_internal_lang": app_vars["check_internal_lang_var"].get(),
            "custom_prompt": current_prompt,
            "glossaries": glossary_file_paths
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            # print("설정이 저장되었습니다.") # main_app에서 로그 처리
        except Exception as e:
            print(f"설정 저장 오류: {e}") # main_app에서 로그 처리
