# translator_project/translator_app/gui/panels/translation_lang_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip

class TranslationLangPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app
        
        self.grid_columnconfigure(1, weight=1)
        
        # Title
        self.lang_frame_title_label = ctk.CTkLabel(
            self, 
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lang_frame_title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(7,10), sticky="w")
        
        # Row 1: Source Language
        self.source_lang_label = ctk.CTkLabel(self)
        self.source_lang_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.source_lang_menu = ctk.CTkOptionMenu(
            self, 
            values=self.main_app.api_lang_options_en,
            variable=self.main_app.source_lang_for_api_var
        )
        self.source_lang_menu.grid(row=1, column=1, sticky="ew", padx=(5,10), pady=5)
        self.source_lang_tooltip = Tooltip(self.source_lang_menu, "")
        
        # Row 2: Target Language
        self.target_lang_label = ctk.CTkLabel(self)
        self.target_lang_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        self.target_lang_menu = ctk.CTkOptionMenu(
            self, 
            values=self.main_app.api_lang_options_en,
            variable=self.main_app.target_lang_for_api_var
        )
        self.target_lang_menu.grid(row=2, column=1, sticky="ew", padx=(5,10), pady=5)
        self.target_lang_tooltip = Tooltip(self.target_lang_menu, "")
        
        # Row 3: Game Selection (새로 추가)
        self.game_type_label = ctk.CTkLabel(self)
        self.game_type_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        
        self.game_type_menu = ctk.CTkOptionMenu(
            self, 
            values=["None", "Crusader Kings 3", "Stellaris", "Hearts of Iron 4", 
                    "Europa Universalis IV", "Victoria 3", "Imperator: Rome"],
            variable=self.main_app.selected_game_var
        )
        self.game_type_menu.grid(row=3, column=1, sticky="ew", padx=(5,10), pady=5)
        self.game_type_tooltip = Tooltip(self.game_type_menu, "")
        
        self.update_language()
    
    def update_language(self):
        texts = self.main_app.texts
        self.lang_frame_title_label.configure(text=texts.get("lang_settings_frame"))
        self.source_lang_label.configure(text=texts.get("source_content_lang_label"))
        self.source_lang_tooltip.update_text(texts.get("source_content_lang_tooltip"))
        self.target_lang_label.configure(text=texts.get("target_trans_lang_label"))
        self.target_lang_tooltip.update_text(texts.get("target_trans_lang_tooltip"))
        self.game_type_label.configure(text=texts.get("game_type_label"))
        self.game_type_tooltip.update_text(texts.get("game_type_tooltip"))