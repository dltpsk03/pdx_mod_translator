# translator_project/translator_app/gui/panels/ui_config_panel.py
import customtkinter as ctk
import tkinter as tk
from ..tooltip import Tooltip
from ...utils.localization import LANGUAGES

class UIConfigPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, minsize=130)
        self.grid_columnconfigure(3, minsize=130)

        self.ui_settings_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=14, weight="bold"))
        self.ui_settings_title_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(5, 10), sticky="w")

        self.ui_lang_label_widget = ctk.CTkLabel(self)
        self.ui_lang_label_widget.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")

        ui_lang_combo_values = [LANGUAGES[code].get("ui_lang_self_name", code) for code in LANGUAGES.keys()]
        self.ui_lang_combo_widget = ctk.CTkComboBox(self,
                                                    variable=self.main_app.current_lang_code,
                                                    values=ui_lang_combo_values,
                                                    command=self.main_app._on_ui_lang_selected,
                                                    width=120)
        self.ui_lang_combo_widget.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.ui_lang_combo_tooltip = Tooltip(self.ui_lang_combo_widget, "")

        self.appearance_mode_label_widget = ctk.CTkLabel(self)
        self.appearance_mode_label_widget.grid(row=1, column=2, padx=(20, 5), pady=5, sticky="w")

        self.appearance_mode_optionmenu = ctk.CTkOptionMenu(self,
                                                            variable=self.main_app.appearance_mode_var,
                                                            command=self.main_app.change_appearance_mode_event,
                                                            width=120)
        self.appearance_mode_optionmenu.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.update_language()

    def update_language(self):
        texts = self.main_app.texts
        self.ui_settings_title_label.configure(text=texts.get("ui_settings_frame_title"))
        self.ui_lang_label_widget.configure(text=texts.get("ui_lang_label"))
        self.ui_lang_combo_tooltip.update_text(texts.get("ui_lang_tooltip"))
        self.appearance_mode_label_widget.configure(text=texts.get("appearance_mode_label"))

        appearance_mode_values = [texts.get("dark_mode"), texts.get("light_mode"), texts.get("system_mode")]
        self.appearance_mode_optionmenu.configure(values=appearance_mode_values)
        current_appearance_key = self.main_app.appearance_mode_var.get()
        if current_appearance_key == "Dark":
            self.appearance_mode_optionmenu.set(texts.get("dark_mode"))
        elif current_appearance_key == "Light":
            self.appearance_mode_optionmenu.set(texts.get("light_mode"))
        else:
            self.appearance_mode_optionmenu.set(texts.get("system_mode"))
