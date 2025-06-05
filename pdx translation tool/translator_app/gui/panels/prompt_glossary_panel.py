# translator_project/translator_app/gui/panels/prompt_glossary_panel.py
import customtkinter as ctk
import tkinter as tk
import os
from ..tooltip import Tooltip

class PromptGlossaryPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=2)

        self.pg_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=14, weight="bold"))
        self.pg_title_label.grid(row=0, column=0, padx=10, pady=(7,10), sticky="w")

        prompt_edit_subframe = ctk.CTkFrame(self)
        prompt_edit_subframe.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        prompt_edit_subframe.grid_columnconfigure(0, weight=1)
        prompt_edit_subframe.grid_rowconfigure(1, weight=1)

        self.prompt_edit_title_label = ctk.CTkLabel(prompt_edit_subframe, font=ctk.CTkFont(size=13, weight="bold"))
        self.prompt_edit_title_label.grid(row=0, column=0, columnspan=3, padx=5, pady=(5,0), sticky="w")

        self.prompt_textbox = ctk.CTkTextbox(prompt_edit_subframe, wrap="word")
        self.prompt_textbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.prompt_textbox_tooltip = Tooltip(self.prompt_textbox, "")
        self.prompt_textbox.insert("1.0", self.main_app.default_prompt_template_str)

        prompt_button_frame = ctk.CTkFrame(prompt_edit_subframe, fg_color="transparent")
        prompt_button_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=(0,5), sticky="ew")

        self.load_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self.main_app._load_prompt_from_file)
        self.load_prompt_btn.pack(side="left", padx=(0,5))
        self.load_prompt_btn_tooltip = Tooltip(self.load_prompt_btn, "")

        self.save_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self.main_app._save_prompt_to_file)
        self.save_prompt_btn.pack(side="left", padx=5)
        self.save_prompt_btn_tooltip = Tooltip(self.save_prompt_btn, "")

        self.reset_prompt_btn = ctk.CTkButton(prompt_button_frame, command=self.main_app._reset_default_prompt)
        self.reset_prompt_btn.pack(side="left", padx=5)
        self.reset_prompt_btn_tooltip = Tooltip(self.reset_prompt_btn, "")

        glossary_manage_subframe = ctk.CTkFrame(self)
        glossary_manage_subframe.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        glossary_manage_subframe.grid_columnconfigure(0, weight=1)
        glossary_manage_subframe.grid_rowconfigure(1, weight=1)

        self.glossary_manage_title_label = ctk.CTkLabel(glossary_manage_subframe, font=ctk.CTkFont(size=13, weight="bold"))
        self.glossary_manage_title_label.grid(row=0, column=0, columnspan=2, padx=5, pady=(5,0), sticky="w")

        self.glossary_list_frame = ctk.CTkScrollableFrame(glossary_manage_subframe, label_text="")
        self.glossary_list_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.glossary_list_frame.grid_columnconfigure(0, weight=1)

        glossary_button_frame = ctk.CTkFrame(glossary_manage_subframe, fg_color="transparent")
        glossary_button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")

        self.add_glossary_btn = ctk.CTkButton(glossary_button_frame, command=self.main_app._add_glossary_file)
        self.add_glossary_btn.pack(side="left", padx=(0,5))
        self.add_glossary_btn_tooltip = Tooltip(self.add_glossary_btn, "")

        self.update_language()

    def get_prompt_text(self):
        return self.prompt_textbox.get("1.0", "end-1c")

    def set_prompt_text(self, text):
        self.prompt_textbox.delete("1.0", "end")
        self.prompt_textbox.insert("1.0", text)

    def update_glossary_list_display(self, glossary_data_list):
        for widget in self.glossary_list_frame.winfo_children():
            widget.destroy()
        if not glossary_data_list:
            no_glossary_label = ctk.CTkLabel(self.glossary_list_frame, text=self.main_app.texts.get("glossary_file_status_not_used","용어집 사용 안 함"))
            no_glossary_label.pack(pady=5)
            return
        for i, glossary_item_info in enumerate(glossary_data_list):
            item_frame = ctk.CTkFrame(self.glossary_list_frame, fg_color="transparent")
            item_frame.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)
            file_path = glossary_item_info["path"]
            base_name = os.path.basename(file_path)
            entry_count = glossary_item_info.get("entry_count", 0)
            error_msg_key = glossary_item_info.get("error_key") # 오류 메시지 키 (예: "glossary_error_not_found")
            error_detail = glossary_item_info.get("error_detail") # 실제 오류 내용 (예: 예외 메시지)
            texts = self.main_app.texts

            display_text = base_name
            if error_msg_key:
                error_text_template = texts.get(error_msg_key, "{0}") # 기본 템플릿
                display_text += f" ({error_text_template.format(error_detail if error_detail else '')})"
            elif entry_count > 0:
                 display_text += f" ({texts.get('glossary_item_loaded','{1}개 항목').format('', entry_count).split(': ')[-1].strip()})"
            elif os.path.exists(file_path): # 파일은 있지만 항목이 0개 또는 유효한 항목 없음
                 display_text += f" ({texts.get('glossary_item_empty','비어있음')})"

            status_label = ctk.CTkLabel(item_frame, text=display_text, anchor="w", wraplength=self.glossary_list_frame.winfo_width() - 60 if self.glossary_list_frame.winfo_width() > 60 else 150)
            status_label.grid(row=0, column=0, sticky="ew", padx=(0,5))
            remove_btn = ctk.CTkButton(item_frame, text="X", width=30, height=20, command=lambda fp=file_path: self.main_app._remove_glossary_file(fp))
            remove_btn.grid(row=0, column=1, sticky="e")

    def update_language(self):
        texts = self.main_app.texts
        self.pg_title_label.configure(text=texts.get("prompt_glossary_frame_title"))
        self.prompt_edit_title_label.configure(text=texts.get("prompt_edit_frame_title"))
        self.prompt_textbox_tooltip.update_text(texts.get("prompt_edit_textbox_tooltip"))
        self.load_prompt_btn.configure(text=texts.get("load_prompt_button"))
        self.load_prompt_btn_tooltip.update_text(texts.get("load_prompt_button_tooltip"))
        self.save_prompt_btn.configure(text=texts.get("save_prompt_button"))
        self.save_prompt_btn_tooltip.update_text(texts.get("save_prompt_button_tooltip"))
        self.reset_prompt_btn.configure(text=texts.get("reset_prompt_button"))
        self.reset_prompt_btn_tooltip.update_text(texts.get("reset_prompt_button_tooltip"))
        self.glossary_manage_title_label.configure(text=texts.get("glossary_management_frame_title"))
        self.add_glossary_btn.configure(text=texts.get("add_glossary_button"))
        self.add_glossary_btn_tooltip.update_text(texts.get("add_glossary_button_tooltip"))
        # 용어집 목록 자체는 main_app._update_glossary_list_ui_data() -> self.update_glossary_list_display() 를 통해 업데이트