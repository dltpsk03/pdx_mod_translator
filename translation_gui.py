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
import json  # 설정 저장/로드용

current_dir = os.path.dirname(os.path.abspath(__file__))
translator_pkg_dir = os.path.join(current_dir, "pdx translation tool")
if translator_pkg_dir not in sys.path:
    sys.path.insert(0, translator_pkg_dir)

from translator_app.utils.localization import LANGUAGES, get_language_code

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
        
        # UI 업데이트 (용어집 항목 수 등) - 이 함수 호출 후 _update_glossary_list_ui를 다시 호출할 수도 있음
        # self.after(0, self._update_glossary_list_ui) # 필요하다면, 하지만 현재는 상태 텍스트만 사용

        if not combined_glossary_for_prompt:
            # self.log_message("log_combined_glossary_empty") # <<< 이 로그 메시지 제거 또는 주석 처리
            return ""
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


    def translate_batch(self, text_batch, model, temperature=0.2, max_output_tokens=8192):
        batch_text_content = "\n".join([line.rstrip('\n') for line in text_batch])
        source_lang_for_prompt = self.source_lang_for_api_var.get(); target_lang_for_prompt = self.target_lang_for_api_var.get()
        prompt_template_str = self.prompt_textbox.get("1.0", "end-1c"); glossary_str_for_prompt = self._get_combined_glossary_content()
        try: final_prompt = prompt_template_str.format(source_lang_for_prompt=source_lang_for_prompt, target_lang_for_prompt=target_lang_for_prompt, glossary_section=glossary_str_for_prompt, batch_text=batch_text_content)
        except KeyError as e: self.log_message("log_batch_unknown_error", self.current_processing_file_for_log, f"Prompt formatting error (KeyError: {e}). Using default structure."); final_prompt = self.default_prompt_template_str.format(source_lang_for_prompt=source_lang_for_prompt, target_lang_for_prompt=target_lang_for_prompt, glossary_section=glossary_str_for_prompt, batch_text=batch_text_content)
        try:
            if self.stop_event.is_set(): return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 중지 시 원본 반환
            response = model.generate_content(final_prompt, generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_output_tokens))
            translated_text = ""; finish_reason_val = 0
            if response.candidates: candidate = response.candidates[0];
            if candidate.content and candidate.content.parts: translated_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
            if hasattr(candidate, 'finish_reason'): finish_reason_val = candidate.finish_reason
            elif hasattr(response, 'text') and response.text: translated_text = response.text

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                self.log_message("log_batch_prompt_blocked", self.current_processing_file_for_log, response.prompt_feedback.block_reason)
                return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 프롬프트 차단 시 원본 반환

            if finish_reason_val not in [0, 1]: # 0: unspecified, 1: STOP (성공)
                if finish_reason_val == 2: # MAX_TOKENS
                    self.log_message("log_batch_token_limit", self.current_processing_file_for_log, finish_reason_val)
                    if len(text_batch) > 1:
                        mid = len(text_batch) // 2
                        first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens)
                        second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens)
                        return first_half + second_half
                    else:
                        self.log_message("log_batch_single_line_token_limit", self.current_processing_file_for_log)
                        return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 단일 라인 토큰 초과 시 원본 반환
                else: # SAFETY, RECITATION, OTHER
                    reason_str = f"Reason Code: {finish_reason_val}"
                    if response.candidates and response.candidates[0].safety_ratings:
                        safety_str = "; ".join([f"{sr.category.name}: {sr.probability.name}" for sr in response.candidates[0].safety_ratings])
                        reason_str += f" (Safety: {safety_str})"
                    self.log_message("log_batch_abnormal_termination", self.current_processing_file_for_log, reason_str)
                    return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 비정상 종료 시 원본 반환

            if not translated_text.strip():
                self.log_message("log_batch_empty_response", self.current_processing_file_for_log)
                return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 빈 응답 시 원본 반환

            # ```yaml 과 ``` 제거 (이전과 동일)
            if translated_text.startswith("```yaml\n"): translated_text = translated_text[len("```yaml\n"):]
            if translated_text.endswith("\n```"): translated_text = translated_text[:-len("\n```")]
            if translated_text.startswith("```\n"): translated_text = translated_text[len("```\n"):]
            if translated_text.endswith("```"): translated_text = translated_text[:-len("```")]

            translated_lines_raw = translated_text.split('\n')
            processed_lines = []

            # log_batch_line_mismatch 관련 if문 및 log_message 호출 완전 제거됨

            # 번역된 라인 수만큼만 반복하여 처리
            for i in range(len(translated_lines_raw)):
                api_translated_line = translated_lines_raw[i]

                # 원본 라인이 존재하는 경우에만 원본의 개행 상태를 참고
                if i < len(text_batch):
                    original_line_content = text_batch[i]
                    original_ends_with_newline = original_line_content.endswith('\n')

                    if original_ends_with_newline and not api_translated_line.endswith('\n'):
                        processed_lines.append(api_translated_line + '\n')
                    elif not original_ends_with_newline and api_translated_line.endswith('\n'):
                        processed_lines.append(api_translated_line.rstrip('\n'))
                    else:
                        processed_lines.append(api_translated_line if api_translated_line.endswith('\n') else api_translated_line + '\n')
                else:
                    # 번역된 라인이 원본보다 많을 경우 (프롬프트 규칙상 거의 발생 안함)
                    # 일단 번역된 그대로 추가 (개행은 API가 준 대로, 없으면 추가)
                    processed_lines.append(api_translated_line if api_translated_line.endswith('\n') else api_translated_line + '\n')

            return processed_lines

        except Exception as e:
            if self.stop_event.is_set(): return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 중지 시 원본 반환
            error_str = str(e).lower()
            # API 제한 관련 오류 처리 (이전과 동일)
            if ("token" in error_str and ("limit" in error_str or "exceeded" in error_str or "max" in error_str)) or \
               ("429" in error_str) or ("resource has been exhausted" in error_str) or \
               ("quota" in error_str) or ("rate limit" in error_str) or ("rpm" in error_str and "limit" in error_str) or \
               ("user_location" in error_str and "blocked" in error_str) or ("permission_denied" in error_str):
                self.log_message("log_batch_api_limit_error_split", self.current_processing_file_for_log, str(e))
                if len(text_batch) > 1:
                    mid = len(text_batch) // 2
                    first_half = self.translate_batch(text_batch[:mid], model, temperature, max_output_tokens)
                    second_half = self.translate_batch(text_batch[mid:], model, temperature, max_output_tokens)
                    return first_half + second_half
                else:
                    self.log_message("log_batch_single_line_api_limit", self.current_processing_file_for_log)
                    return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 단일 라인 API 제한 시 원본 반환
            self.log_message("log_batch_unknown_error", self.current_processing_file_for_log, str(e))
            return [line if line.endswith('\n') else line + '\n' for line in text_batch] # 알 수 없는 오류 시 원본 반환

    def process_file(self, input_file, output_file, model):
        self.current_processing_file_for_log = os.path.basename(input_file)
        try:
            with codecs.open(input_file, 'r', encoding='utf-8-sig') as f: lines = f.readlines()
            if not lines: self.log_message("log_file_empty", self.current_processing_file_for_log); return
            total_lines = len(lines); translated_lines_final = []; self.log_message("log_file_process_start", self.current_processing_file_for_log, total_lines)
            start_index = 0; first_line_lang_pattern = re.compile(r"^\s*l_([a-zA-Z_]+)\s*:", re.IGNORECASE)
            if self.check_internal_lang_var.get() and lines:
                first_line_match_check = first_line_lang_pattern.match(lines[0]); source_lang_ui_selected_api_name = self.source_lang_for_api_var.get(); source_lang_code_from_ui = get_language_code(source_lang_ui_selected_api_name) 
                if first_line_match_check:
                    actual_lang_code_in_file = first_line_match_check.group(1).lower()
                    if actual_lang_code_in_file != source_lang_code_from_ui: self.log_message("log_internal_lang_mismatch_using_ui", self.current_processing_file_for_log, f"l_{actual_lang_code_in_file}", f"l_{source_lang_code_from_ui}")
                else: self.log_message("log_internal_lang_no_identifier_using_ui", self.current_processing_file_for_log, f"l_{source_lang_code_from_ui}")
            first_line_match_for_change = first_line_lang_pattern.match(lines[0])
            if first_line_match_for_change:
                original_first_line_content = lines[0]; original_lang_identifier_in_file = first_line_match_for_change.group(0).strip() 
                if self.keep_lang_def_unchanged_var.get(): translated_lines_final.append(original_first_line_content); self.log_message("log_first_line_keep") 
                else: target_lang_code_str = get_language_code(self.target_lang_for_api_var.get()); new_first_line_content = first_line_lang_pattern.sub(f"l_{target_lang_code_str}:", original_first_line_content, count=1); translated_lines_final.append(new_first_line_content); self.log_message("log_first_line_change", original_lang_identifier_in_file, f"l_{target_lang_code_str}:")
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
            target_lang_api_name_for_filename = self.target_lang_for_api_var.get(); target_lang_code_for_filename_output = get_language_code(target_lang_api_name_for_filename)
            source_lang_api_name = self.source_lang_for_api_var.get(); source_lang_code = get_language_code(source_lang_api_name); file_identifier_for_search = f"l_{source_lang_code}"
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