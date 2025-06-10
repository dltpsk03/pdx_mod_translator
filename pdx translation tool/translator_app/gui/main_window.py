# translator_project/translator_app/gui/main_window.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading # stop_event용
import time      # log_message용
import codecs    # 프롬프트/용어집 파일 처리용
import tkinter as tk
import locale    # 시스템 언어 감지용
from datetime import datetime

# --- 내부 모듈 임포트 ---
from ..utils.localization import LANGUAGES, set_language
from ..core.translator_engine import TranslatorEngine
from ..core.settings_manager import SettingsManager

from .panels.ui_config_panel import UIConfigPanel
from .panels.api_model_panel import APIModelPanel
from .panels.folder_panel import FolderPanel
from .panels.translation_lang_panel import TranslationLangPanel
from .panels.detailed_settings_panel import DetailedSettingsPanel
from .panels.prompt_glossary_panel import PromptGlossaryPanel
from .panels.control_panel import ControlPanel
from .panels.log_panel import LogPanel

from .windows.translation_dashboard import TranslationDashboard
from .windows.term_consistency_checker import TermConsistencyChecker
from .panels.live_preview_panel import LivePreviewPanel

def detect_system_language():
    """시스템 언어 자동 감지"""
    try:
        system_lang = locale.getdefaultlocale()[0]
        lang_map = {
            'ko_KR': 'ko',
            'en_US': 'en',
            'en_GB': 'en',
            'zh_CN': 'zh_CN',
            'zh_TW': 'zh_CN',
        }
        return lang_map.get(system_lang, 'en')
    except:
        return 'en'


class TranslationGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- 1. 애플리케이션 변수 선언 ---
        # 시스템 언어 자동 감지
        detected_lang = detect_system_language()
        self.current_lang_code = tk.StringVar(value=detected_lang)
        self.texts = {} # update_ui_texts에서 채워짐

        self.appearance_mode_var = tk.StringVar(value="Dark")
        self.api_key_var = tk.StringVar()
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.model_name_var = tk.StringVar()
        self.source_lang_for_api_var = tk.StringVar(value='English')
        self.target_lang_for_api_var = tk.StringVar(value='Korean')
        self.batch_size_var = tk.IntVar(value=50)
        self.max_workers_var = tk.IntVar(value=100)
        self.max_tokens_var = tk.IntVar(value=65536)
        self.delay_between_batches_var = tk.DoubleVar(value=0.8)
        self.temperature_var = tk.DoubleVar(value=0.5)
        self.keep_lang_def_unchanged_var = tk.BooleanVar(value=False)
        self.check_internal_lang_var = tk.BooleanVar(value=False)
        self.split_threshold_var = tk.IntVar(value=1000)
        self.enable_backup_var = tk.BooleanVar(value=False)
        
        # 새로운 변수들
        self.selected_game_var = tk.StringVar(value="None")
        self.skip_already_translated_var = tk.BooleanVar(value=False)
        self.max_retries_var = tk.IntVar(value=3)
        self.enable_live_preview = tk.BooleanVar(value=False)  # 실시간 미리보기 활성화 옵션

        self.progress_text_var = tk.StringVar()
        self.glossary_files = []
        self.stop_event = threading.Event()
        self.loaded_prompt_from_config = None

        self.translation_stats = []  # 대시보드가 닫혀있어도 통계 수집
        self.translation_session_start = None

        self.dashboard_window = None  # 대시보드 창 참조
        self.consistency_window = None  # 일관성 검사기 창 참조

        self.api_lang_options_en = ('English', 'Korean', 'Simplified Chinese', 'French', 'German', 'Spanish', 'Japanese', 'Portuguese', 'Russian', 'Turkish')
        self.available_models = ['gemini-2.5-flash-preview-05-20', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash','gemini-2.5-pro-preview-06-05']
        if self.available_models:
            self.model_name_var.set(self.available_models[0])

        self.default_prompt_template_str = """Please translate the following YML formatted text from '{source_lang_for_prompt}' to '{target_lang_for_prompt}'.
{glossary_section}
You MUST adhere to the following rules strictly:
1. Only translate the text enclosed in double quotes after a colon (:). (e.g., `key: "text to translate"`)
2. Do NOT translate code-like strings, variable names (e.g., `$variable$`, `[variable]`, `<variable>`), special tags (e.g., `§Y`, `£gold£`), file paths, or URLs.
3. **CRITICAL**: You MUST preserve all original newline characters (\\n) and leading whitespace (indentation) for each line. Do NOT change or remove them. Each translated line must retain its original line break.
4. Provide ONLY the translated text. Do NOT include any other explanations, headers, or footers.
5. Translate all personal names and proper nouns according to the context.
6. If the content within quotes is a number, consists only of special characters, or is a simple path string, do NOT translate it.
7. Do NOT translate YML comments (lines starting with '#'). Keep them as they are.
8. For each input line, you MUST output exactly one translated line.
9. **ABSOLUTE REQUIREMENT**: When translating from {source_lang_for_prompt} to {target_lang_for_prompt}, you MUST completely translate ALL {source_lang_for_prompt} words and phrases. Do NOT leave any {source_lang_for_prompt} text untranslated. Every single {source_lang_for_prompt} word must be converted to {target_lang_for_prompt}.
10. **STRICT VALIDATION**: If any {source_lang_for_prompt} words remain in your translation, it is considered a FAILED translation. Retry until ALL {source_lang_for_prompt} is properly translated to {target_lang_for_prompt}.

Text to translate:
```yaml
{batch_text}
```"""
        # --- 2. SettingsManager 초기화 (load_settings 전에 필요) ---
        self.settings_manager = SettingsManager(
            default_prompt_template=self.default_prompt_template_str,
            default_available_models=self.available_models
        )

        # --- 3. 설정 로드 및 기본 UI 설정 ---
        self.load_settings() # 이제 SettingsManager 인스턴스가 존재함
        ctk.set_appearance_mode(self.appearance_mode_var.get())
        current_code = self.current_lang_code.get()
        self.texts = LANGUAGES.get(current_code, LANGUAGES["ko"])
        # 전역 언어 설정 초기화
        set_language(current_code)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.title(self.texts.get("title", "Paradox Mod Translator"))
        self.geometry("1920x1080")
        self.resizable(True, True)
        
        # 키보드 단축키 설정
        self.setup_shortcuts()

        # --- 4. TranslatorEngine 초기화 (콜백으로 전달할 메서드들이 self에 바인딩 된 후) ---
        self.translator_engine = TranslatorEngine(
            log_callback=self.log_message,
            progress_callback=self._update_progress_ui,
            status_callback=self._update_status_ui,
            stop_event=self.stop_event,
            get_input_folder_callback=self.input_folder_var.get
        )

        # --- 5. UI 위젯 생성 및 최종 초기화 ---
        self.create_widgets()
        self.update_ui_texts()

        if self.loaded_prompt_from_config:
            # 지연 호출을 통해 UI가 완전히 렌더링된 후 프롬프트 설정
            self.after(100, lambda: self.prompt_glossary_panel.set_prompt_text(self.loaded_prompt_from_config))

        self._update_glossary_list_ui_data()
        self._update_status_ui("status_waiting", task_type="system")
        
        self.dashboard_window = None  # 대시보드 창 참조
        self.consistency_window = None  # 일관성 검사기 창 참조

    def setup_shortcuts(self):
        """키보드 단축키 설정"""
        self.bind("<Control-t>", lambda e: self.start_translation())
        self.bind("<Control-s>", lambda e: self.save_settings())
        self.bind("<F5>", lambda e: self.refresh_ui())
        self.bind("<Escape>", lambda e: self.stop_translation())
        self.bind("<Control-o>", lambda e: self.select_input_folder())
        self.bind("<Control-Shift-o>", lambda e: self.select_output_folder())

    def on_drop(self, event):
        """드래그 앤 드롭 이벤트 처리"""
        files = self.tk.splitlist(event.data)
        yml_files = [f for f in files if f.lower().endswith(('.yml', '.yaml'))]
        
        if yml_files:
            # 첫 번째 YML 파일의 폴더를 입력 폴더로 설정
            first_file_dir = os.path.dirname(yml_files[0])
            self.input_folder_var.set(first_file_dir)
            self.log_message("log_drag_drop_folder_set", first_file_dir)
        
        # 텍스트 파일은 용어집으로 추가
        txt_files = [f for f in files if f.lower().endswith('.txt')]
        for txt_file in txt_files:
            if not any(g["path"] == txt_file for g in self.glossary_files):
                self.glossary_files.append({"path": txt_file, "entry_count": 0, "error": None, "error_key": None})
                self.log_message("log_glossary_added", os.path.basename(txt_file))
        
        if txt_files:
            self._update_glossary_list_ui_data()

    # --- 메서드 정의 시작 ---
    def _on_closing(self):
        """향상된 애플리케이션 종료 처리"""
        try:
            # 설정 저장
            self.save_settings()
            
            # 모든 활성 작업 중지
            if hasattr(self, 'translator_engine'):
                if self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive():
                    self.translator_engine.request_stop_translation()
                    # 스레드 종료 대기 (타임아웃 포함)
                    self.translator_engine.translation_thread.join(timeout=5.0)
                
                # TranslatorEngine 리소스 정리
                self.translator_engine.cleanup_resources()
            
            # 열려있는 도구 창 모두 닫기
            tool_windows = [self.dashboard_window, self.consistency_window]
            for window in tool_windows:
                if window and window.winfo_exists():
                    try:
                        window.destroy()
                    except Exception:
                        pass
            
            # 창 참조 정리
            self.dashboard_window = None
            self.consistency_window = None
            
            # 통계 데이터 정리
            if hasattr(self, 'translation_stats'):
                self.translation_stats.clear()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            self.destroy()

    def refresh_ui(self):
        """UI 텍스트와 상태를 새로고침"""
        self.update_ui_texts()
        self._update_status_ui("status_waiting", task_type="system")

    def load_settings(self):
        app_vars_for_settings = {
            "ui_lang_var": self.current_lang_code,
            "appearance_mode_var": self.appearance_mode_var,
            "api_key_var": self.api_key_var,
            "input_folder_var": self.input_folder_var,
            "output_folder_var": self.output_folder_var,
            "model_name_var": self.model_name_var,
            "source_lang_api_var": self.source_lang_for_api_var,
            "target_lang_api_var": self.target_lang_for_api_var,
            "batch_size_var": self.batch_size_var,
            "max_workers_var": self.max_workers_var,
            "max_tokens_var": self.max_tokens_var,
            "delay_between_batches_var": self.delay_between_batches_var,
            "keep_identifier_var": self.keep_lang_def_unchanged_var,
            "temperature_var": self.temperature_var,
            "check_internal_lang_var": self.check_internal_lang_var,
            "split_threshold_var": self.split_threshold_var,
            "skip_already_translated_var": self.skip_already_translated_var,
            "max_retries_var": self.max_retries_var,
            "selected_game_var": self.selected_game_var,
            "enable_live_preview_var": self.enable_live_preview,
        }
        loaded_prompt, loaded_glossary_paths = self.settings_manager.load_settings(app_vars_for_settings)
        self.loaded_prompt_from_config = loaded_prompt
        self.glossary_files = []
        for g_path in loaded_glossary_paths:
            if os.path.exists(g_path):
                self.glossary_files.append({"path": g_path, "entry_count": 0, "error": None, "error_key": None})

    def save_settings(self):
        app_vars_for_settings = {
            "ui_lang_var": self.current_lang_code,
            "appearance_mode_var": self.appearance_mode_var,
            "api_key_var": self.api_key_var,
            "input_folder_var": self.input_folder_var,
            "output_folder_var": self.output_folder_var,
            "model_name_var": self.model_name_var,
            "source_lang_api_var": self.source_lang_for_api_var,
            "target_lang_api_var": self.target_lang_for_api_var,
            "batch_size_var": self.batch_size_var,
            "max_workers_var": self.max_workers_var,
            "max_tokens_var": self.max_tokens_var,
            "delay_between_batches_var": self.delay_between_batches_var,
            "keep_identifier_var": self.keep_lang_def_unchanged_var,
            "temperature_var": self.temperature_var,
            "check_internal_lang_var": self.check_internal_lang_var,
            "split_threshold_var": self.split_threshold_var,
            "skip_already_translated_var": self.skip_already_translated_var,
            "max_retries_var": self.max_retries_var,
            "selected_game_var": self.selected_game_var,
            "enable_live_preview_var": self.enable_live_preview,
        }
        current_prompt_text = self.prompt_glossary_panel.get_prompt_text() if hasattr(self, 'prompt_glossary_panel') else self.default_prompt_template_str
        current_glossary_paths = [g["path"] for g in self.glossary_files]
        current_appearance_theme = ctk.get_appearance_mode()
        self.settings_manager.save_settings(
            app_vars_for_settings, current_prompt_text, current_glossary_paths, current_appearance_theme
        )
        self.log_message("settings_saved_log")

    # main_window.py의 create_widgets 메서드

    def create_widgets(self):
        """위젯 생성 및 초기 레이아웃 설정"""
        # 메인 그리드 설정
        self.grid_rowconfigure(0, weight=6)  # 상단 설정 영역
        self.grid_rowconfigure(1, weight=0)  # 컨트롤 패널
        self.grid_rowconfigure(2, weight=2)  # 로그 패널
        self.grid_columnconfigure(0, weight=1)

        # === 상단 메인 설정 영역 ===
        # top_main_frame을 인스턴스 속성(self)으로 만들어 다른 메서드에서 접근 가능하게 함
        self.top_main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.top_main_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        self.top_main_frame.grid_rowconfigure(0, weight=1)

        # 좌측: 설정 패널들
        self.settings_scroll_frame = ctk.CTkScrollableFrame(self.top_main_frame, corner_radius=12)
        self.settings_scroll_frame.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        self.settings_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # 설정 패널들 추가
        current_row = 0
        self.ui_config_panel = UIConfigPanel(self.settings_scroll_frame, main_app=self)
        self.ui_config_panel.grid(row=current_row, column=0, padx=0, pady=(0, 8), sticky="ew"); current_row += 1
        
        self.api_model_panel = APIModelPanel(self.settings_scroll_frame, main_app=self)
        self.api_model_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew"); current_row += 1
        
        self.folder_panel = FolderPanel(self.settings_scroll_frame, main_app=self)
        self.folder_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew"); current_row += 1
        
        self.translation_lang_panel = TranslationLangPanel(self.settings_scroll_frame, main_app=self)
        self.translation_lang_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew"); current_row += 1
        
        self.detailed_settings_panel = DetailedSettingsPanel(self.settings_scroll_frame, main_app=self)
        self.detailed_settings_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew"); current_row += 1

        # 중앙: 프롬프트 및 용어집 패널
        self.prompt_glossary_panel = PromptGlossaryPanel(self.top_main_frame, main_app=self)
        self.prompt_glossary_panel.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        
        # 우측: LivePreviewPanel은 항상 생성하고, 초기에는 숨겨둠
        self.live_preview_panel = LivePreviewPanel(self.top_main_frame, main_app=self)
        self.live_preview_panel.grid(row=0, column=2, padx=(8, 0), pady=0, sticky="nsew")
        self.live_preview_panel.grid_remove() # 시작 시 화면에서 숨김

        # === 컨트롤 패널 ===
        self.control_panel_container = ctk.CTkFrame(self, corner_radius=12)
        self.control_panel_container.grid(row=1, column=0, padx=15, pady=8, sticky="ew")
        self.control_panel_container.grid_columnconfigure(0, weight=1)
        
        self.control_panel = ControlPanel(self.control_panel_container, main_app=self)
        self.control_panel.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # === 로그 패널 ===
        self.log_panel = LogPanel(self, main_app=self)
        self.log_panel.grid(row=2, column=0, padx=15, pady=(8, 15), sticky="nsew")
        
        # 초기 레이아웃 상태를 현재 설정값에 맞게 조정
        self.toggle_live_preview(initial_load=True)

    def update_ui_texts(self):
        current_code = self.current_lang_code.get()
        self.texts = LANGUAGES.get(current_code, LANGUAGES["ko"])
        # 전역 언어 설정도 업데이트 (대시보드 등에서 get_text() 사용을 위해)
        set_language(current_code)
        self.title(self.texts.get("title"))

        if hasattr(self, 'ui_config_panel'): self.ui_config_panel.update_language()
        if hasattr(self, 'api_model_panel'): self.api_model_panel.update_language()
        if hasattr(self, 'folder_panel'): self.folder_panel.update_language()
        if hasattr(self, 'translation_lang_panel'): self.translation_lang_panel.update_language()
        if hasattr(self, 'detailed_settings_panel'): self.detailed_settings_panel.update_language()
        if hasattr(self, 'prompt_glossary_panel'): self.prompt_glossary_panel.update_language()
        if hasattr(self, 'control_panel'): self.control_panel.update_language()
        if hasattr(self, 'log_panel'): self.log_panel.update_language()
        if hasattr(self, 'live_preview_panel'): self.live_preview_panel.update_language() # 이 라인도 필요할 수 있습니다.
        if hasattr(self, 'translation_dashboard'): self.translation_dashboard.update_language() # 이 라인도 필요할 수 있습니다.

        is_translation_busy = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        if not is_translation_busy:
            self.progress_text_var.set(self.texts.get("status_waiting"))

        if hasattr(self, 'tools_menu_button'):
            self.tools_menu_button.configure(text=self.texts.get("tools_menu", "Tools"))

        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.update_language()
        
        if self.consistency_window and self.consistency_window.winfo_exists():
            self.consistency_window.update_language()
        
        # 실시간 미리보기 패널이 있으면 업데이트
        if hasattr(self, 'live_preview_panel'):
            self.live_preview_panel.update_language()

        self._update_glossary_list_ui_data()

    def log_message(self, message_key, *args, return_formatted=False):
        current_texts = self.texts if hasattr(self, 'texts') and self.texts else LANGUAGES.get(self.current_lang_code.get() or "ko", LANGUAGES["ko"])
        log_text_template = current_texts.get(message_key, str(message_key))
        try: formatted_message = log_text_template.format(*args)
        except (IndexError, KeyError, TypeError) as e: formatted_message = f"{log_text_template} (Args: {args}, Error: {e})"
        if return_formatted: return formatted_message
        full_log = f"{time.strftime('%H:%M:%S')} - {formatted_message}\n"
        if hasattr(self, 'log_panel') and self.log_panel.winfo_exists(): self.log_panel.add_log_message(full_log)
        else: print(full_log.strip())

    def _update_progress_ui(self, current_count, total_items, progress_value, task_type="translation"):
        if not self.winfo_exists(): return
        if hasattr(self, 'control_panel'): 
            self.control_panel.update_file_progress(current_count, total_items)
            self.control_panel.set_progress(progress_value)
        if task_type == "translation":
            if total_items > 0: 
                self.progress_text_var.set(self.texts.get("status_translating_progress").format(current_count, total_items))
        self.update_idletasks()

    def _update_status_ui(self, status_key, *args, task_type="system"):
        if not self.winfo_exists(): return
        is_translation_active = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        is_any_task_active = is_translation_active

        # 컨트롤 패널 버튼 상태 관리
        if hasattr(self, 'control_panel'):
            self.control_panel.set_translate_button_state('disabled' if is_any_task_active else 'normal')
            self.control_panel.set_stop_button_state('normal' if is_any_task_active else 'disabled')

        message_to_display = self.texts.get(status_key, status_key)
        try:
            if status_key in ["status_stopped", "status_completed_all", "status_completed_some", "status_translating_progress", "status_chunk_progress"] and args:
                message_to_display = message_to_display.format(args[0], args[1])
        except (IndexError, TypeError): pass
        self.progress_text_var.set(message_to_display)

        if hasattr(self, 'control_panel'):
            current_progress_val = 0.0
            if task_type == "translation":
                if status_key == "status_completed_all" and args and len(args) > 1 and args[1] > 0:
                    current_progress_val = 1.0
                elif status_key == "status_no_files" or status_key == "status_waiting":
                    current_progress_val = 0.0
                elif status_key in ["status_stopped", "status_completed_some"] and args and len(args) > 1 and args[1] > 0:
                    current_progress_val = args[0] / args[1]
                self.control_panel.set_progress(current_progress_val)
            elif task_type == "system" and status_key == "status_waiting":
                self.control_panel.set_progress(0.0)
        self.update_idletasks()

    def _on_ui_lang_selected(self, choice_code_or_display_name):
        selected_code = self.current_lang_code.get()
        for code, names in LANGUAGES.items():
            if names.get("ui_lang_self_name", code) == choice_code_or_display_name:
                selected_code = code; break
        self.current_lang_code.set(selected_code)
        self.update_ui_texts()

    def change_appearance_mode_event(self, new_appearance_mode_str_display):
        mode_to_set = "System"
        if hasattr(self, 'texts') and self.texts:
            if new_appearance_mode_str_display == self.texts.get("dark_mode"): mode_to_set = "Dark"
            elif new_appearance_mode_str_display == self.texts.get("light_mode"): mode_to_set = "Light"
        self.appearance_mode_var.set(mode_to_set)
        ctk.set_appearance_mode(mode_to_set)

    def select_input_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("input_folder_label")[:-1])
        if folder:
            self.input_folder_var.set(folder)
            if not (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()):
                self._update_status_ui("status_waiting", task_type="system")
            
            # 입력 폴더의 YML 파일 검증
            self._validate_input_folder(folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("output_folder_label")[:-1])
        if folder:
            self.output_folder_var.set(folder)
            if not (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()):
                self._update_status_ui("status_waiting", task_type="system")

    def _validate_input_folder(self, folder_path):
        """입력 폴더의 YML 파일들을 검증"""
        yml_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.yml', '.yaml')):
                    yml_files.append(os.path.join(root, file))
        
        if yml_files:
            self.log_message("log_found_yml_files", len(yml_files))
            
            # 첫 몇 개 파일 샘플 검증
            sample_size = min(5, len(yml_files))
            total_errors = 0
            
            for i in range(sample_size):
                errors = self.translator_engine.validate_yml_file(yml_files[i])
                if errors:
                    total_errors += len(errors)
                    self.log_message("log_yml_validation_errors", os.path.basename(yml_files[i]), len(errors))
            
            if total_errors > 0:
                self.log_message("log_yml_validation_summary", total_errors, sample_size)

    def _load_prompt_from_file(self):
        filepath = filedialog.askopenfilename(title=self.texts.get("prompt_file_load_title"), filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath and hasattr(self, 'prompt_glossary_panel'):
            try:
                with codecs.open(filepath, 'r', encoding='utf-8-sig') as f: prompt_content = f.read()
                self.prompt_glossary_panel.set_prompt_text(prompt_content)
                self.log_message("log_prompt_loaded_from_file", os.path.basename(filepath))
            except Exception as e:
                messagebox.showerror(self.texts.get("error_title"), f"Error loading prompt file: {e}")
                self.log_message("log_prompt_file_error_using_default", os.path.basename(filepath), str(e))

    def _save_prompt_to_file(self):
        filepath = filedialog.asksaveasfilename(title=self.texts.get("prompt_file_save_title"), defaultextension=".txt", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath and hasattr(self, 'prompt_glossary_panel'):
            try:
                prompt_content = self.prompt_glossary_panel.get_prompt_text()
                with codecs.open(filepath, 'w', encoding='utf-8-sig') as f: f.write(prompt_content)
                self.log_message("log_prompt_saved_to_file", os.path.basename(filepath))
            except Exception as e:
                messagebox.showerror(self.texts.get("error_title"), f"Error saving prompt file: {e}")

    def _reset_default_prompt(self):
        if hasattr(self, 'prompt_glossary_panel'):
            self.prompt_glossary_panel.set_prompt_text(self.default_prompt_template_str)
            self.log_message("log_prompt_reset_to_default")

    def _add_glossary_file(self):
        filepaths = filedialog.askopenfilenames(title=self.texts.get("glossary_file_select_title"), filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        newly_added_count = 0
        if filepaths:
            for fp in filepaths:
                if not any(g["path"] == fp for g in self.glossary_files):
                    self.glossary_files.append({"path": fp, "entry_count": 0, "error": None, "error_key": None})
                    self.log_message("log_glossary_added", os.path.basename(fp))
                    newly_added_count +=1
            if newly_added_count > 0: self._update_glossary_list_ui_data()

    def _remove_glossary_file(self, file_path_to_remove):
        self.glossary_files = [g for g in self.glossary_files if g["path"] != file_path_to_remove]
        self.log_message("log_glossary_removed", os.path.basename(file_path_to_remove))
        self._update_glossary_list_ui_data()

    def _update_glossary_list_ui_data(self):
        if not hasattr(self, 'prompt_glossary_panel'): return
        for g_item in self.glossary_files:
            path = g_item["path"]
            g_item["entry_count"] = 0
            g_item["error"] = None
            g_item["error_key"] = None
            g_item["error_detail"] = None
            if not os.path.exists(path):
                g_item["error_key"] = "glossary_error_not_found"
            else:
                try:
                    with codecs.open(path, 'r', encoding='utf-8-sig') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    if not lines:
                        g_item["error_key"] = "glossary_error_empty"
                    else:
                        count = 0
                        for line in lines:
                            if ':' in line:
                                parts = line.split(':', 1)
                                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                                    count += 1
                        g_item["entry_count"] = count
                        if count == 0: g_item["error_key"] = "glossary_error_no_valid"
                except Exception as e:
                    g_item["error_key"] = "glossary_item_error"
                    g_item["error_detail"] = str(e)
                    self.log_message("log_glossary_error", os.path.basename(path), str(e))
        self.prompt_glossary_panel.update_glossary_list_display(self.glossary_files)

    def _get_combined_glossary_content(self):
        combined_glossary_for_prompt = []
        total_valid_entries = 0
        for glossary_item_info in self.glossary_files:
            if glossary_item_info.get("entry_count", 0) > 0 and not glossary_item_info.get("error_key"):
                filepath = glossary_item_info["path"]
                try:
                    with codecs.open(filepath, 'r', encoding='utf-8-sig') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    current_file_entries = 0
                    for line in lines:
                        if ':' in line:
                            parts = line.split(':', 1)
                            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                                combined_glossary_for_prompt.append(f"- \"{parts[0].strip()}\" should be translated as \"{parts[1].strip()}\"")
                                current_file_entries +=1
                    total_valid_entries += current_file_entries
                except Exception: pass
        if not combined_glossary_for_prompt: return ""
        self.log_message("log_combined_glossary_info", total_valid_entries)
        header = "Please refer to the following glossary for translation. Ensure these terms are translated as specified:\n"
        return header + "\n".join(combined_glossary_for_prompt) + "\n\n"


    def collect_translation_stats(self, file_path, stats_dict):
        """번역 통계 수집 (항상 실행)"""
        # 세션 시작 시간 기록
        if self.translation_session_start is None:
            self.translation_session_start = datetime.now()
        
        # 통계 데이터 생성
        stat_entry = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'timestamp': datetime.now(),
            'status': 'completed',
            'time': stats_dict.get('time', 0),
            'quality': stats_dict.get('quality', 100),
            'lines': stats_dict.get('lines', 0),
            'errors': stats_dict.get('errors', 0),
            'original_file': stats_dict.get('original_file', ''),
            'batch_qualities': stats_dict.get('batch_qualities', [])
        }
        
        # 메인 윈도우에 저장
        self.translation_stats.append(stat_entry)
        
        # 로그 출력 (디버깅용)
        self.log_message("log_stats_collected", stat_entry['filename'], stat_entry['quality'])
        
        # 대시보드가 열려있으면 실시간 전달
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            try:
                # 직접 호출하여 즉시 업데이트
                self.dashboard_window.add_file_stat_direct(stat_entry)
            except Exception as e:
                self.log_message("log_dashboard_update_error", str(e))

    def start_translation(self):
        if not self.validate_inputs(): return
        is_translation_busy = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        if is_translation_busy:
            messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_processing"))
            return

        if hasattr(self, 'log_panel'): self.log_panel.clear_log()

        # 새 번역 시작 시 통계 초기화 (선택적)
        # self.translation_stats.clear()  # 이전 통계를 유지하려면 주석 처리
        # self.translation_session_start = None
        
        # 대시보드가 열려있으면 초기화
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.clear_dashboard()

        # Live Preview가 활성화되어 있으면 콜백 설정
        if hasattr(self, 'live_preview_panel') and self.enable_live_preview.get():
            self.live_preview_panel.clear_preview()
            self.translator_engine.preview_callback = self.add_preview_line
        else:
            self.translator_engine.preview_callback = None

        self._update_glossary_list_ui_data()
        combined_glossary = self._get_combined_glossary_content()
        output_dir = self.output_folder_var.get()
        if not output_dir:
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_output_folder_needed"))
            return
        try: os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_create_output_folder").format(str(e)))
            self._update_status_ui("status_waiting", task_type="system")
            return

        prompt_text_to_use = self.prompt_glossary_panel.get_prompt_text() if hasattr(self, 'prompt_glossary_panel') else self.default_prompt_template_str

        # 항상 stats_callback을 설정 (main_window의 메서드로)
        success = self.translator_engine.start_translation_process(
            api_key=self.api_key_var.get().strip(),
            selected_model_name=self.model_name_var.get(),
            input_folder=self.input_folder_var.get(),
            output_folder=output_dir,
            source_lang_api=self.source_lang_for_api_var.get(),
            target_lang_api=self.target_lang_for_api_var.get(),
            prompt_template=prompt_text_to_use,
            glossary_content=combined_glossary,
            batch_size_val=self.batch_size_var.get(),
            max_tokens_val=self.max_tokens_var.get(),
            delay_val=self.delay_between_batches_var.get(),
            temperature_val=self.temperature_var.get(),
            max_workers_val=self.max_workers_var.get(),
            keep_identifier_val=self.keep_lang_def_unchanged_var.get(),
            check_internal_lang_val=self.check_internal_lang_var.get(),
            split_large_files_threshold=self.split_threshold_var.get(),
            selected_game=self.selected_game_var.get(),
            skip_already_translated=self.skip_already_translated_var.get(),
            max_retries=self.max_retries_var.get(),
            preview_callback=self.add_preview_line if (hasattr(self, 'live_preview_panel') and self.enable_live_preview.get()) else None,
            stats_callback=self.collect_translation_stats,  # 항상 메인 윈도우의 메서드 사용
            enable_backup=self.enable_backup_var.get()
        )

    def stop_translation(self):
        action_taken = False
        if self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive():
            if self.translator_engine.request_stop_translation():
                action_taken = True

    def validate_inputs(self):
        def is_valid_int(value_var, min_val, max_val):
            try: val = int(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False
        def is_valid_float(value_var, min_val, max_val):
            try: val = float(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False

        # API 키 검증 강화
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_api_key_needed")); return False
        
        # API 키 형식 검증 (Gemini API 키는 'AIza'로 시작)
        if not api_key.startswith('AIza') or len(api_key) < 30:
            messagebox.showerror(self.texts.get("error_title"), "Invalid API key format. Gemini API keys should start with 'AIza' and be at least 30 characters long."); return False
        if not self.model_name_var.get():
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_model_needed")); return False
        if not self.input_folder_var.get() or not os.path.isdir(self.input_folder_var.get()):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_input_folder_invalid")); return False

        if not is_valid_int(self.batch_size_var, 1, 500):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_size_label')[:-1]})"); return False
        if not is_valid_int(self.max_workers_var, 1, 256):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('concurrent_files_label')[:-1]})"); return False
        if not is_valid_int(self.max_tokens_var, 100, 65536): # Gemini 모델 최대값 고려 (flash 모델은 더 높음)
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('max_output_tokens_label')[:-1]})"); return False
        if not is_valid_float(self.delay_between_batches_var, 0.0, 60.0):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('batch_delay_label')[:-1]})"); return False
        if not is_valid_int(self.split_threshold_var, 0, 200000): # 0은 분할 안함
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('split_threshold_label')[:-1]})"); return False
        if not is_valid_float(self.temperature_var, 0.0, 2.0):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('temperature_label')[:-1]})"); return False
        if not is_valid_int(self.max_retries_var, 1, 10):
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_numeric_setting_invalid") + f" ({self.texts.get('max_retries_label')[:-1]})"); return False

        current_prompt = self.prompt_glossary_panel.get_prompt_text() if hasattr(self, 'prompt_glossary_panel') else ""
        required_placeholders = ["{source_lang_for_prompt}", "{target_lang_for_prompt}", "{glossary_section}", "{batch_text}"]
        missing_placeholders = [ph for ph in required_placeholders if ph not in current_prompt]
        if missing_placeholders:
            error_msg_template = self.texts.get("error_prompt_missing_placeholders")
            messagebox.showerror(self.texts.get("error_title"), error_msg_template.format(', '.join(missing_placeholders)))
            return False
        return True
    
    def show_tools_menu(self):
        """도구 메뉴 표시"""
        # 드롭다운 메뉴 생성
        menu = tk.Menu(self, tearoff=0)
        
        # 번역 통계 대시보드
        menu.add_command(
            label=self.texts.get("open_dashboard", "Translation Dashboard"),
            command=self.open_dashboard
        )
        
        # 용어 일관성 검사기
        menu.add_command(
            label=self.texts.get("open_consistency_checker", "Term Consistency Checker"),
            command=self.open_consistency_checker
        )
        
        menu.add_separator()
        
        # 실시간 미리보기 토글
        menu.add_checkbutton(
            label=self.texts.get("toggle_live_preview", "Live Preview"),
            variable=self.enable_live_preview,
            command=self.toggle_live_preview
        )
        
        # 메뉴 표시
        try:
            menu.post(
                self.tools_menu_button.winfo_rootx(),
                self.tools_menu_button.winfo_rooty() + self.tools_menu_button.winfo_height()
            )
        except:
            # 대체 위치
            menu.post(self.winfo_pointerx(), self.winfo_pointery())

    def open_dashboard(self):
        """번역 통계 대시보드 열기"""
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.lift()
            self.dashboard_window.focus_force()
            return
        
        self.dashboard_window = TranslationDashboard(self, self)
        
        # 기존에 수집된 통계가 있으면 전달
        if self.translation_stats:
            self.dashboard_window.load_existing_stats(
                self.translation_stats, 
                self.translation_session_start
            )
        
        # 현재 번역 중이면 stats_callback 업데이트 (실시간 업데이트용)
        if self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive():
            # 이미 collect_translation_stats가 설정되어 있으므로 추가 작업 불필요
            pass

        # 창이 닫힐 때 참조 제거
        def on_close():
            self.dashboard_window.destroy()
            self.dashboard_window = None
        
        self.dashboard_window.protocol("WM_DELETE_WINDOW", on_close)
        
    def clear_translation_stats(self):
        """번역 통계 초기화 (필요시 호출)"""
        self.translation_stats.clear()
        self.translation_session_start = None
        
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.clear_all()

    def open_consistency_checker(self):
        """용어 일관성 검사기 열기"""
        # 이미 열려있으면 포커스만 이동
        if self.consistency_window and self.consistency_window.winfo_exists():
            self.consistency_window.lift()
            self.consistency_window.focus_force()
            return
        
        # 새 창 생성
        self.consistency_window = TermConsistencyChecker(self, self)
        
        # 창이 닫힐 때 참조 제거
        def on_close():
            self.consistency_window.destroy()
            self.consistency_window = None
        
        self.consistency_window.protocol("WM_DELETE_WINDOW", on_close)

    def toggle_live_preview(self, initial_load=False):
        """실시간 미리보기 토글 및 레이아웃 동적 조정"""
        
        # initial_load가 True일 때는 변수 값 변경 없이 현재 상태에 맞게 레이아웃만 조정
        is_enabled = self.enable_live_preview.get()
        
        if is_enabled:
            # 패널 보이기
            self.live_preview_panel.grid()
            # 3단 레이아웃 가중치 설정
            self.top_main_frame.grid_columnconfigure(0, weight=2) # 설정
            self.top_main_frame.grid_columnconfigure(1, weight=3) # 프롬프트
            self.top_main_frame.grid_columnconfigure(2, weight=2) # 미리보기
        else:
            # 패널 숨기기
            self.live_preview_panel.grid_remove()
            # 2단 레이아웃 가중치 설정
            self.top_main_frame.grid_columnconfigure(0, weight=2) # 설정
            self.top_main_frame.grid_columnconfigure(1, weight=5) # 프롬프트 (확장)
            self.top_main_frame.grid_columnconfigure(2, weight=0) # 미리보기 (공간 차지 안함)

    def add_preview_line(self, original, translated, quality_score=None, has_error=False):
        """실시간 미리보기에 라인 추가 (translator_engine에서 호출)"""
        if hasattr(self, 'live_preview_panel') and self.live_preview_panel.winfo_viewable():
            self.live_preview_panel.add_preview_line(original, translated, quality_score, has_error)

    def update_translation_stats(self, filename, stats):
        """번역 통계 업데이트 (레거시 지원용)"""
        # 대시보드가 열려있으면 전달
        if self.dashboard_window and self.dashboard_window.winfo_exists():
            self.dashboard_window.add_file_stat(filename, stats)