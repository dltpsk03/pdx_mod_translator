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

        # Row 3 - 파일 분할 임계값과 온도
        self.split_threshold_label = ctk.CTkLabel(self)
        self.split_threshold_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.split_threshold_entry = ctk.CTkEntry(self, textvariable=self.main_app.split_threshold_var, width=80, justify='center')
        self.split_threshold_entry.grid(row=3, column=1, sticky="w", padx=(5,10), pady=5)
        self.split_threshold_tooltip = Tooltip(self.split_threshold_entry, "")

        self.temperature_label = ctk.CTkLabel(self)
        self.temperature_label.grid(row=3, column=2, sticky="w", padx=(20, 10), pady=5)
        self.temperature_entry = ctk.CTkEntry(
            self,
            textvariable=self.main_app.temperature_var,
            width=80,
            justify='center'
        )
        self.temperature_entry.grid(row=3, column=3, sticky="w", padx=(5, 10), pady=5)
        self.temperature_tooltip = Tooltip(self.temperature_entry, "")

        # Row 4 - 재시도 횟수 추가
        self.max_retries_label = ctk.CTkLabel(self)
        self.max_retries_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.max_retries_entry = ctk.CTkEntry(self, textvariable=self.main_app.max_retries_var, width=80, justify='center')
        self.max_retries_entry.grid(row=4, column=1, sticky="w", padx=(5,10), pady=5)
        self.max_retries_tooltip = Tooltip(self.max_retries_entry, "")

        # Row 5 - 체크박스들
        self.lang_def_option_check_widget = ctk.CTkCheckBox(self, variable=self.main_app.keep_lang_def_unchanged_var, onvalue=True, offvalue=False)
        self.lang_def_option_check_widget.grid(row=5, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.lang_def_option_check_tooltip = Tooltip(self.lang_def_option_check_widget, "")

        self.internal_lang_check_widget = ctk.CTkCheckBox(self, variable=self.main_app.check_internal_lang_var, onvalue=True, offvalue=False)
        self.internal_lang_check_widget.grid(row=5, column=2, columnspan=2, sticky="w", padx=10, pady=(10,5))
        self.internal_lang_check_tooltip = Tooltip(self.internal_lang_check_widget, "")

        # Row 6 - 기번역 건너뛰기
        self.skip_translated_check = ctk.CTkCheckBox(
            self, 
            variable=self.main_app.skip_already_translated_var,
            onvalue=True, 
            offvalue=False
        )
        self.skip_translated_check.grid(row=6, column=0, columnspan=4, sticky="w", padx=10, pady=(10,5))
        self.skip_translated_tooltip = Tooltip(self.skip_translated_check, "")

        self.backup_check = ctk.CTkCheckBox(
            self,
            # text=get_text(...) 대신 빈 텍스트로 초기화
            text="", 
            variable=self.main_app.enable_backup_var,
            onvalue=True,
            offvalue=False
        )
        self.backup_check.grid(row=7, column=0, columnspan=4, sticky="w", padx=10, pady=(10,5))
        # Tooltip도 빈 텍스트로 초기화
        self.backup_tooltip = Tooltip(self.backup_check, "") 

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
        
        self.split_threshold_label.configure(text=texts.get("split_threshold_label"))
        self.split_threshold_tooltip.update_text(texts.get("split_threshold_tooltip"))

        self.temperature_label.configure(text=texts.get("temperature_label"))
        self.temperature_tooltip.update_text(texts.get("temperature_tooltip"))

        self.max_retries_label.configure(text=texts.get("max_retries_label"))
        self.max_retries_tooltip.update_text(texts.get("max_retries_tooltip"))

        self.lang_def_option_check_widget.configure(text=texts.get("keep_identifier_label"))
        self.lang_def_option_check_tooltip.update_text(texts.get("keep_identifier_tooltip"))
        self.internal_lang_check_widget.configure(text=texts.get("check_internal_lang_label"))
        self.internal_lang_check_tooltip.update_text(texts.get("check_internal_lang_tooltip"))
        
        self.skip_translated_check.configure(text=texts.get("skip_already_translated_label"))
        self.skip_translated_tooltip.update_text(texts.get("skip_already_translated_tooltip"))

        self.backup_check.configure(text=texts.get("enable_backup_label"))
        self.backup_tooltip.update_text(texts.get("enable_backup_tooltip"))