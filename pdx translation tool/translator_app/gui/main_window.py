# translator_project/translator_app/gui/main_window.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading # stop_event용
import time      # log_message용
import codecs    # 프롬프트/용어집 파일 처리용
import tkinter as tk

# --- 내부 모듈 임포트 ---
from ..utils.localization import LANGUAGES
from ..core.translator_engine import TranslatorEngine
from ..core.settings_manager import SettingsManager

from .tooltip import Tooltip
from .panels.ui_config_panel import UIConfigPanel
from .panels.api_model_panel import APIModelPanel
from .panels.folder_panel import FolderPanel
from .panels.translation_lang_panel import TranslationLangPanel
from .panels.detailed_settings_panel import DetailedSettingsPanel
from .panels.prompt_glossary_panel import PromptGlossaryPanel
from .panels.control_panel import ControlPanel
from .panels.log_panel import LogPanel
from .comparison_review_window import ComparisonReviewWindow
from .validation_window import ValidationWindow


class TranslationGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- 1. 애플리케이션 변수 선언 ---
        self.current_lang_code = tk.StringVar(value="ko")
        self.texts = {} # update_ui_texts에서 채워짐

        self.appearance_mode_var = tk.StringVar(value="Dark")
        self.api_key_var = tk.StringVar()
        self.input_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.model_name_var = tk.StringVar()
        self.source_lang_for_api_var = tk.StringVar(value='English')
        self.target_lang_for_api_var = tk.StringVar(value='Korean')
        self.batch_size_var = tk.IntVar(value=25)
        self.max_workers_var = tk.IntVar(value=3)
        self.max_tokens_var = tk.IntVar(value=8192)
        self.delay_between_batches_var = tk.DoubleVar(value=0.8)
        self.keep_lang_def_unchanged_var = tk.BooleanVar(value=False)
        self.check_internal_lang_var = tk.BooleanVar(value=False)
        self.split_threshold_var = tk.IntVar(value=5000)

        self.progress_text_var = tk.StringVar()
        self.glossary_files = []
        self.stop_event = threading.Event()
        self.loaded_prompt_from_config = None
        self.validation_window_instance = None
        self.comparison_review_window_instance = None

        self.api_lang_options_en = ('English', 'Korean', 'Simplified Chinese', 'French', 'German', 'Spanish', 'Japanese', 'Portuguese', 'Russian', 'Turkish')
        self.available_models = ['gemini-2.5-flash-preview-05-20', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
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
        self.texts = LANGUAGES.get(self.current_lang_code.get(), LANGUAGES["ko"])

        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.title(self.texts.get("title", "Paradox Mod Translator"))
        self.geometry("1920x1080")
        self.resizable(True, True)

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
            self.prompt_glossary_panel.set_prompt_text(self.loaded_prompt_from_config)

        self._update_glossary_list_ui_data()
        self._update_status_ui("status_waiting", task_type="system")


    # --- 메서드 정의 시작 ---
    def _on_closing(self):
        self.save_settings()
        if self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive():
            self.translator_engine.request_stop_translation()
        if self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive():
            self.translator_engine.request_stop_validation()
        if self.comparison_review_window_instance and self.comparison_review_window_instance.winfo_exists():
            self.comparison_review_window_instance.destroy()
        if self.validation_window_instance and self.validation_window_instance.winfo_exists():
            self.validation_window_instance.destroy()
        self.destroy()

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
            "check_internal_lang_var": self.check_internal_lang_var,
            "split_threshold_var": self.split_threshold_var,
        }
        # SettingsManager 인스턴스가 __init__에서 이미 생성되었으므로 self.settings_manager 사용
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
            "check_internal_lang_var": self.check_internal_lang_var,
            "split_threshold_var": self.split_threshold_var,
        }
        current_prompt_text = self.prompt_glossary_panel.get_prompt_text() if hasattr(self, 'prompt_glossary_panel') else self.default_prompt_template_str
        current_glossary_paths = [g["path"] for g in self.glossary_files]
        current_appearance_theme = ctk.get_appearance_mode()
        self.settings_manager.save_settings(
            app_vars_for_settings, current_prompt_text, current_glossary_paths, current_appearance_theme
        )
        self.log_message("settings_saved_log")

    def create_widgets(self):
        # 메인 그리드 설정 - 개선된 비율
        self.grid_rowconfigure(0, weight=6)  # 상단 설정 영역 (더 넓게)
        self.grid_rowconfigure(1, weight=0)  # 컨트롤 패널
        self.grid_rowconfigure(2, weight=0)  # 검수 툴 섹션
        self.grid_rowconfigure(3, weight=2)  # 로그 패널 (적당히)
        self.grid_columnconfigure(0, weight=1)

        # === 상단 메인 설정 영역 ===
        top_main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        top_main_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        top_main_frame.grid_columnconfigure(0, weight=5)
        top_main_frame.grid_columnconfigure(1, weight=3)
        top_main_frame.grid_rowconfigure(0, weight=1)

        # 좌측: 설정 패널들
        self.settings_scroll_frame = ctk.CTkScrollableFrame(top_main_frame, corner_radius=12)
        self.settings_scroll_frame.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        self.settings_scroll_frame.grid_columnconfigure(0, weight=1)
        
        current_row = 0
        self.ui_config_panel = UIConfigPanel(self.settings_scroll_frame, main_app=self)
        self.ui_config_panel.grid(row=current_row, column=0, padx=0, pady=(0, 8), sticky="ew")
        current_row += 1
        
        self.api_model_panel = APIModelPanel(self.settings_scroll_frame, main_app=self)
        self.api_model_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew")
        current_row += 1
        
        self.folder_panel = FolderPanel(self.settings_scroll_frame, main_app=self)
        self.folder_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew")
        current_row += 1
        
        self.translation_lang_panel = TranslationLangPanel(self.settings_scroll_frame, main_app=self)
        self.translation_lang_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew")
        current_row += 1
        
        self.detailed_settings_panel = DetailedSettingsPanel(self.settings_scroll_frame, main_app=self)
        self.detailed_settings_panel.grid(row=current_row, column=0, padx=0, pady=8, sticky="ew")
        current_row += 1

        # 우측: 프롬프트 및 용어집 패널
        self.prompt_glossary_panel = PromptGlossaryPanel(top_main_frame, main_app=self)
        self.prompt_glossary_panel.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")

        # === 컨트롤 패널 (번역 시작/중지) ===
        self.control_panel_container = ctk.CTkFrame(self, corner_radius=12)
        self.control_panel_container.grid(row=1, column=0, padx=15, pady=8, sticky="ew")
        self.control_panel = ControlPanel(self.control_panel_container, main_app=self)
        self.control_panel.pack(fill="x", padx=10, pady=10)

        # === 검수 및 검증 도구 섹션 ===
        tools_section_frame = ctk.CTkFrame(self, corner_radius=12)
        tools_section_frame.grid(row=2, column=0, padx=15, pady=8, sticky="ew")
        tools_section_frame.grid_columnconfigure(0, weight=1)
        tools_section_frame.grid_columnconfigure(1, weight=1)

        # 검수 도구 섹션 제목
        tools_title = ctk.CTkLabel(
            tools_section_frame,
            text="🔍 Review & Validation Tools",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        tools_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        # 파일 비교/검수 도구
        self.comparison_review_tool_frame = ctk.CTkFrame(tools_section_frame, corner_radius=8)
        self.comparison_review_tool_frame.grid(row=1, column=0, padx=(15, 8), pady=(0, 15), sticky="ew")
        
        comparison_icon_label = ctk.CTkLabel(
            self.comparison_review_tool_frame,
            text="📄",
            font=ctk.CTkFont(size=24)
        )
        comparison_icon_label.pack(pady=(15, 5))
        
        self.comparison_review_tool_title_label = ctk.CTkLabel(
            self.comparison_review_tool_frame,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.comparison_review_tool_title_label.pack(pady=(0, 5))
        
        comparison_desc_label = ctk.CTkLabel(
            self.comparison_review_tool_frame,
            text="Compare original and translated files\nside by side with error highlighting",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray60")
        )
        comparison_desc_label.pack(pady=(0, 10))
        
        self.open_comparison_review_window_button = ctk.CTkButton(
            self.comparison_review_tool_frame,
            command=self.open_comparison_review_window,
            height=35,
            corner_radius=8
        )
        self.open_comparison_review_window_button.pack(pady=(0, 15), padx=15, fill="x")

        # 파일 검증 도구
        self.validation_main_frame = ctk.CTkFrame(tools_section_frame, corner_radius=8)
        self.validation_main_frame.grid(row=1, column=1, padx=(8, 15), pady=(0, 15), sticky="ew")
        
        validation_icon_label = ctk.CTkLabel(
            self.validation_main_frame,
            text="🔧",
            font=ctk.CTkFont(size=24)
        )
        validation_icon_label.pack(pady=(15, 5))
        
        self.validation_main_title_label = ctk.CTkLabel(
            self.validation_main_frame,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.validation_main_title_label.pack(pady=(0, 5))
        
        validation_desc_label = ctk.CTkLabel(
            self.validation_main_frame,
            text="Validate translated files for\nregex errors and source remnants",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray60")
        )
        validation_desc_label.pack(pady=(0, 10))
        
        self.open_validation_window_button = ctk.CTkButton(
            self.validation_main_frame,
            command=self.open_validation_window,
            height=35,
            corner_radius=8
        )
        self.open_validation_window_button.pack(pady=(0, 15), padx=15, fill="x")

        # === 로그 패널 ===
        self.log_panel = LogPanel(self, main_app=self)
        self.log_panel.grid(row=3, column=0, padx=15, pady=(8, 15), sticky="nsew")

    def update_ui_texts(self):
        current_code = self.current_lang_code.get()
        self.texts = LANGUAGES.get(current_code, LANGUAGES["ko"])
        self.title(self.texts.get("title"))

        if hasattr(self, 'ui_config_panel'): self.ui_config_panel.update_language()
        if hasattr(self, 'api_model_panel'): self.api_model_panel.update_language()
        if hasattr(self, 'folder_panel'): self.folder_panel.update_language()
        if hasattr(self, 'translation_lang_panel'): self.translation_lang_panel.update_language()
        if hasattr(self, 'detailed_settings_panel'): self.detailed_settings_panel.update_language()
        if hasattr(self, 'prompt_glossary_panel'): self.prompt_glossary_panel.update_language()
        if hasattr(self, 'control_panel'): self.control_panel.update_language()
        if hasattr(self, 'log_panel'): self.log_panel.update_language()

        if hasattr(self, 'comparison_review_tool_title_label'): 
            self.comparison_review_tool_title_label.configure(text=self.texts.get("review_section_title", "File Comparison"))
        if hasattr(self, 'open_comparison_review_window_button'): 
            self.open_comparison_review_window_button.configure(text=self.texts.get("review_open_comparison_window_button", "Open Comparison Tool"))
        if hasattr(self, 'validation_main_title_label'): 
            self.validation_main_title_label.configure(text=self.texts.get("validation_section_title", "File Validation"))
        if hasattr(self, 'open_validation_window_button'): 
            self.open_validation_window_button.configure(text=self.texts.get("validation_open_window_button", "Open Validation Tool"))

        if self.comparison_review_window_instance and self.comparison_review_window_instance.winfo_exists():
            self.comparison_review_window_instance.update_language_texts(self.texts)
        if self.validation_window_instance and self.validation_window_instance.winfo_exists():
            self.validation_window_instance.update_language_texts(self.texts)

        is_translation_busy = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        is_validation_busy = self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive()
        if not is_translation_busy and not is_validation_busy:
            self.progress_text_var.set(self.texts.get("status_waiting"))
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
        if hasattr(self, 'control_panel'): self.control_panel.set_progress(progress_value)
        if task_type == "translation":
            if total_items > 0: self.progress_text_var.set(self.texts.get("status_translating_progress").format(current_count, total_items))
        self.update_idletasks()

    def _update_status_ui(self, status_key, *args, task_type="system"):
        if not self.winfo_exists(): return
        is_translation_active = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        is_validation_active = self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive()
        is_any_task_active = is_translation_active or is_validation_active

        # 컨트롤 패널 버튼 상태 관리
        if hasattr(self, 'control_panel'):
            self.control_panel.set_translate_button_state('disabled' if is_any_task_active else 'normal')
            self.control_panel.set_stop_button_state('normal' if is_any_task_active else 'disabled')

        # 검증 도구 버튼 상태 관리
        if hasattr(self, 'open_validation_window_button'):
            self.open_validation_window_button.configure(
                state='normal' if self.output_folder_var.get() and not is_any_task_active else 'disabled'
            )

        # 비교 도구 버튼 상태 관리
        if hasattr(self, 'open_comparison_review_window_button'):
            can_open_comparison = bool(self.input_folder_var.get() and self.output_folder_var.get())
            self.open_comparison_review_window_button.configure(
                state='normal' if can_open_comparison and not is_any_task_active else 'disabled'
            )

        message_to_display = self.texts.get(status_key, status_key)
        try:
            if status_key in ["status_stopped", "status_completed_all", "status_completed_some", "status_translating_progress"] and args:
                message_to_display = message_to_display.format(args[0], args[1])
        except (IndexError, TypeError): pass
        self.progress_text_var.set(message_to_display)

        if hasattr(self, 'control_panel'):
            current_progress_val = 0.0
            if task_type == "translation":
                if status_key == "status_completed_all" and args and len(args) > 1 and args[1] > 0:
                    current_progress_val = 1.0
                    if hasattr(self, 'validation_main_frame'): self.validation_main_frame.grid()
                elif status_key == "status_no_files" or status_key == "status_waiting":
                    current_progress_val = 0.0
                    if hasattr(self, 'validation_main_frame'): self.validation_main_frame.grid()
                elif status_key in ["status_stopped", "status_completed_some"] and args and len(args) > 1 and args[1] > 0:
                     current_progress_val = args[0] / args[1]
                     if hasattr(self, 'validation_main_frame'): self.validation_main_frame.grid()
                self.control_panel.set_progress(current_progress_val)
            elif task_type == "system" and status_key == "status_waiting":
                 self.control_panel.set_progress(0.0)
                 if hasattr(self, 'validation_main_frame'): self.validation_main_frame.grid()
            elif task_type == "validation" and status_key == "validation_completed":
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
            if not (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()) and \
               not (self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive()):
                self._update_status_ui("status_waiting", task_type="system")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title=self.texts.get("output_folder_label")[:-1])
        if folder:
            self.output_folder_var.set(folder)
            if not (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()) and \
               not (self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive()):
                self._update_status_ui("status_waiting", task_type="system")

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

    def open_comparison_review_window(self):
        input_dir = self.input_folder_var.get()
        output_dir = self.output_folder_var.get()
        source_lang = self.source_lang_for_api_var.get()
        target_lang = self.target_lang_for_api_var.get()

        if not input_dir or not os.path.isdir(input_dir) or \
           not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror(self.texts.get("error_title"),
                                 self.texts.get("comparison_review_select_folders_first", "Please select input and output folders first."))
            return
        
        is_any_task_active = (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()) or \
                             (self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive())
        if is_any_task_active:
            messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_processing", "A task is already running."))
            return

        if self.comparison_review_window_instance is None or not self.comparison_review_window_instance.winfo_exists():
            self.comparison_review_window_instance = ComparisonReviewWindow(
                master_window=self,
                translator_engine=self.translator_engine,
                main_texts=self.texts,
                input_folder_path=input_dir,
                output_folder_path=output_dir,
                source_lang_api=source_lang,
                target_lang_api=target_lang
            )
            self.comparison_review_window_instance.focus_set()
        else:
            self.comparison_review_window_instance.deiconify()
            self.comparison_review_window_instance.lift()
            self.comparison_review_window_instance.focus_set()

    def start_translation(self):
        if not self.validate_inputs(): return
        is_translation_busy = self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()
        is_validation_busy = self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive()
        if is_translation_busy or is_validation_busy:
            messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_processing"))
            return

        if hasattr(self, 'log_panel'): self.log_panel.clear_log()
        if hasattr(self, 'validation_main_frame'): self.validation_main_frame.grid()

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
            max_workers_val=self.max_workers_var.get(),
            keep_identifier_val=self.keep_lang_def_unchanged_var.get(),
            check_internal_lang_val=self.check_internal_lang_var.get(),
            split_large_files_threshold=self.split_threshold_var.get()
        )

    def stop_translation(self):
        action_taken = False
        if self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive():
            if self.translator_engine.request_stop_translation():
                action_taken = True
        if self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive():
            if self.translator_engine.request_stop_validation():
                action_taken = True

    def validate_inputs(self):
        def is_valid_int(value_var, min_val, max_val):
            try: val = int(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False
        def is_valid_float(value_var, min_val, max_val):
            try: val = float(value_var.get()); return min_val <= val <= max_val
            except (ValueError, tk.TclError): return False

        if not self.api_key_var.get().strip():
            messagebox.showerror(self.texts.get("error_title"), self.texts.get("error_api_key_needed")); return False
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

        current_prompt = self.prompt_glossary_panel.get_prompt_text() if hasattr(self, 'prompt_glossary_panel') else ""
        required_placeholders = ["{source_lang_for_prompt}", "{target_lang_for_prompt}", "{glossary_section}", "{batch_text}"]
        missing_placeholders = [ph for ph in required_placeholders if ph not in current_prompt]
        if missing_placeholders:
            error_msg_template = self.texts.get("error_prompt_missing_placeholders")
            messagebox.showerror(self.texts.get("error_title"), error_msg_template.format(', '.join(missing_placeholders)))
            return False
        return True

    def open_validation_window(self):
        if self.validation_window_instance is None or not self.validation_window_instance.winfo_exists():
            output_dir = self.output_folder_var.get()
            if not output_dir or not os.path.isdir(output_dir):
                messagebox.showerror(self.texts.get("error_title"), self.texts.get("validation_no_output_folder"))
                return
            is_any_task_active = (self.translator_engine.translation_thread and self.translator_engine.translation_thread.is_alive()) or \
                                 (self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive())
            if is_any_task_active:
                messagebox.showwarning(self.texts.get("warn_title"), self.texts.get("warn_already_processing"))
                return

            self.validation_window_instance = ValidationWindow(
                master_window=self,
                translator_engine=self.translator_engine,
                main_texts=self.texts
            )
            self.validation_window_instance.focus_set()
        else:
            self.validation_window_instance.deiconify()
            self.validation_window_instance.lift()
            self.validation_window_instance.focus_set()