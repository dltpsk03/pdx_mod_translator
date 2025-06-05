# translator_project/translator_app/gui/panels/detailed_settings_panel.py
import customtkinter as ctk
import tkinter as tk # For main_app.split_threshold_var
from ..tooltip import Tooltip

class DetailedSettingsPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.setting_frame_details_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.setting_frame_details_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")

        # Row 1
        self.batch_size_label_widget = ctk.CTkLabel(self)
        self.batch_size_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.batch_size_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.batch_size_var, width=80, justify='center')
        self.batch_size_entry_widget.grid(row=1, column=1, sticky="w", padx=(5,10), pady=5)
        self.batch_size_spinbox_tooltip = Tooltip(self.batch_size_entry_widget, "")

        self.concurrent_files_label_widget = ctk.CTkLabel(self)
        self.concurrent_files_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.max_workers_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.max_workers_var, width=80, justify='center')
        self.max_workers_entry_widget.grid(row=1, column=3, sticky="w", padx=(5,10), pady=5)
        self.max_workers_spinbox_tooltip = Tooltip(self.max_workers_entry_widget, "")

        # Row 2
        self.max_output_tokens_label_widget = ctk.CTkLabel(self)
        self.max_output_tokens_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.max_tokens_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.max_tokens_var, width=80, justify='center')
        self.max_tokens_entry_widget.grid(row=2, column=1, sticky="w", padx=(5,10), pady=5)
        self.max_tokens_spinbox_tooltip = Tooltip(self.max_tokens_entry_widget, "")

        self.batch_delay_label_widget = ctk.CTkLabel(self)
        self.batch_delay_label_widget.grid(row=2, column=2, sticky="w", padx=(20,10), pady=5)
        self.delay_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.delay_between_batches_var, width=80, justify='center')
        self.delay_entry_widget.grid(row=2, column=3, sticky="w", padx=(5,10), pady=5)
        self.delay_spinbox_tooltip = Tooltip(self.delay_entry_widget, "")

        # Row 3 - 파일 분할 임계값 추가
        self.split_threshold_label = ctk.CTkLabel(self) # 텍스트는 update_language에서 설정
        self.split_threshold_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.split_threshold_entry = ctk.CTkEntry(self, textvariable=self.main_app.split_threshold_var, width=80, justify='center')
        self.split_threshold_entry.grid(row=3, column=1, sticky="w", padx=(5,10), pady=5)
        self.split_threshold_tooltip = Tooltip(self.split_threshold_entry, "") # 툴팁 텍스트도 update_language

        # Row 4 (기존 Row 3의 내용)
        self.lang_def_option_check_widget = ctk.CTkCheckBox(self, variable=self.main_app.keep_lang_def_unchanged_var, onvalue=True, offvalue=False)
        self.lang_def_option_check_widget.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.lang_def_option_check_tooltip = Tooltip(self.lang_def_option_check_widget, "")

        self.internal_lang_check_widget = ctk.CTkCheckBox(self, variable=self.main_app.check_internal_lang_var, onvalue=True, offvalue=False)
        self.internal_lang_check_widget.grid(row=4, column=2, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.internal_lang_check_tooltip = Tooltip(self.internal_lang_check_widget, "")


        self.update_language()

    def update_language(self):
        texts = self.main_app.texts
        self.setting_frame_details_title_label.configure(text=texts.get("detailed_settings_frame"))
        self.batch_size_label_widget.configure(text=texts.get("batch_size_label"))
        self.batch_size_spinbox_tooltip.update_text(texts.get("batch_size_tooltip"))
        self.concurrent_files_label_widget.configure(text=texts.get("concurrent_files_label"))
        self.max_workers_spinbox_tooltip.update_text(texts.get("concurrent_files_tooltip"))
        self.max_output_tokens_label_widget.configure(text=texts.get("max_output_tokens_label"))
        self.max_tokens_spinbox_tooltip.update_text(texts.get("max_output_tokens_tooltip"))
        self.batch_delay_label_widget.configure(text=texts.get("batch_delay_label"))
        self.delay_spinbox_tooltip.update_text(texts.get("batch_delay_tooltip"))
        
        self.split_threshold_label.configure(text=texts.get("split_threshold_label", "파일 분할 기준(줄):")) # LANGUAGES에 추가 필요
        self.split_threshold_tooltip.update_text(texts.get("split_threshold_tooltip", "이 줄 수를 초과하는 파일은 분할하여 번역합니다. (0이면 분할 안 함)")) # LANGUAGES에 추가 필요

        self.lang_def_option_check_widget.configure(text=texts.get("keep_identifier_label"))
        self.lang_def_option_check_tooltip.update_text(texts.get("keep_identifier_tooltip"))
        self.internal_lang_check_widget.configure(text=texts.get("check_internal_lang_label"))
        self.internal_lang_check_tooltip.update_text(texts.get("check_internal_lang_tooltip"))