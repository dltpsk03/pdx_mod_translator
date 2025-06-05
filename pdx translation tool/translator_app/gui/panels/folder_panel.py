# translator_project/translator_app/gui/panels/folder_panel.py
import customtkinter as ctk
from ..tooltip import Tooltip

class FolderPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(1, weight=1)

        self.folder_frame_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.folder_frame_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(7,10), sticky="w")

        self.input_folder_label_widget = ctk.CTkLabel(self)
        self.input_folder_label_widget.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.input_folder_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.input_folder_var, placeholder_text="Input folder")
        self.input_folder_entry_widget.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        self.input_folder_entry_tooltip = Tooltip(self.input_folder_entry_widget, "")
        self.input_folder_button_widget = ctk.CTkButton(self, command=self.main_app.select_input_folder, width=100)
        self.input_folder_button_widget.grid(row=1, column=2, padx=(5,10), pady=5)
        self.input_folder_button_tooltip = Tooltip(self.input_folder_button_widget, "")

        self.output_folder_label_widget = ctk.CTkLabel(self)
        self.output_folder_label_widget.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.output_folder_entry_widget = ctk.CTkEntry(self, textvariable=self.main_app.output_folder_var, placeholder_text="Output folder")
        self.output_folder_entry_widget.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.output_folder_entry_tooltip = Tooltip(self.output_folder_entry_widget, "")
        self.output_folder_button_widget = ctk.CTkButton(self, command=self.main_app.select_output_folder, width=100)
        self.output_folder_button_widget.grid(row=2, column=2, padx=(5,10), pady=5)
        self.output_folder_button_tooltip = Tooltip(self.output_folder_button_widget, "")

        self.update_language()

    def update_language(self):
        texts = self.main_app.texts
        self.folder_frame_title_label.configure(text=texts.get("folder_frame"))
        self.input_folder_label_widget.configure(text=texts.get("input_folder_label"))
        self.input_folder_entry_tooltip.update_text(texts.get("input_folder_tooltip"))
        self.input_folder_button_widget.configure(text=texts.get("browse_button"))
        self.input_folder_button_tooltip.update_text(texts.get("input_browse_tooltip"))
        self.output_folder_label_widget.configure(text=texts.get("output_folder_label"))
        self.output_folder_entry_tooltip.update_text(texts.get("output_folder_tooltip"))
        self.output_folder_button_widget.configure(text=texts.get("browse_button"))
        self.output_folder_button_tooltip.update_text(texts.get("output_browse_tooltip"))
