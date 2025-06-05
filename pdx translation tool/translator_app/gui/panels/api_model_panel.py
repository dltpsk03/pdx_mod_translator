# translator_project/translator_app/gui/panels/api_model_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip

class APIModelPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)

        self.api_model_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.api_model_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")

        self.api_key_label_widget = ctk.CTkLabel(self)
        self.api_key_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.api_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.api_key_var, show="*", placeholder_text="Enter API Key")
        self.api_entry_widget.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.api_entry_tooltip = Tooltip(self.api_entry_widget, "")

        self.model_label_widget = ctk.CTkLabel(self)
        self.model_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_combo_widget = ctk.CTkComboBox(self, variable=self.main_app.model_name_var, values=self.main_app.available_models, state='readonly')
        self.model_combo_widget.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_combo_tooltip = Tooltip(self.model_combo_widget, "")

        self.update_language()

    def update_language(self):
        texts = self.main_app.texts
        self.api_model_title_label.configure(text=texts.get("api_settings_frame"))
        self.api_key_label_widget.configure(text=texts.get("api_key_label"))
        self.api_entry_tooltip.update_text(texts.get("api_key_tooltip"))
        self.model_label_widget.configure(text=texts.get("model_label"))
        self.model_combo_tooltip.update_text(texts.get("model_tooltip"))
