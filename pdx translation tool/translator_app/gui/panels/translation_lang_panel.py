# translator_project/translator_app/gui/panels/translation_lang_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip

class TranslationLangPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)

        self.lang_frame_api_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.lang_frame_api_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(7,10), sticky="w")

        self.source_content_lang_label_widget = ctk.CTkLabel(self)
        self.source_content_lang_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.source_combo_api_widget = ctk.CTkComboBox(self, variable=self.main_app.source_lang_for_api_var, values=self.main_app.api_lang_options_en, state='readonly', width=180)
        self.source_combo_api_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.source_combo_api_tooltip = Tooltip(self.source_combo_api_widget, "")

        self.target_trans_lang_label_widget = ctk.CTkLabel(self)
        self.target_trans_lang_label_widget.grid(row=1, column=2, sticky="w", padx=(20,10), pady=5)
        self.target_combo_api_widget = ctk.CTkComboBox(self, variable=self.main_app.target_lang_for_api_var, values=self.main_app.api_lang_options_en, state='readonly', width=180)
        self.target_combo_api_widget.grid(row=1, column=3, sticky="ew", padx=10, pady=5)
        self.target_combo_api_tooltip = Tooltip(self.target_combo_api_widget, "")

        self.update_language()

    def update_language(self):
        texts = self.main_app.texts
        self.lang_frame_api_title_label.configure(text=texts.get("lang_settings_frame"))
        self.source_content_lang_label_widget.configure(text=texts.get("source_content_lang_label"))
        self.source_combo_api_tooltip.update_text(texts.get("source_content_lang_tooltip"))
        self.target_trans_lang_label_widget.configure(text=texts.get("target_trans_lang_label"))
        self.target_combo_api_tooltip.update_text(texts.get("target_trans_lang_tooltip"))
