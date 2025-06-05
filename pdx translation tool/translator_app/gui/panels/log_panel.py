# translator_project/translator_app/gui/panels/log_panel.py
import customtkinter as ctk

class LogPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.main_app = main_app

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.log_frame_display_title_label = ctk.CTkLabel(self, font=ctk.CTkFont(size=13, weight="bold"))
        self.log_frame_display_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(7,5))

        self.log_text_widget = ctk.CTkTextbox(self, wrap="word", corner_radius=8, border_width=1)
        self.log_text_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.log_text_widget.configure(state="disabled")

        self.update_language()

    def add_log_message(self, message_with_timestamp):
        if self.winfo_exists(): # 위젯이 파괴되지 않았는지 확인
            self.log_text_widget.configure(state="normal")
            self.log_text_widget.insert("end", message_with_timestamp) # 이미 포맷된 메시지 (타임스탬프 포함)
            self.log_text_widget.see("end")
            self.log_text_widget.configure(state="disabled")
            self.update_idletasks()

    def clear_log(self):
        if self.winfo_exists():
            self.log_text_widget.configure(state="normal")
            self.log_text_widget.delete("1.0", "end")
            self.log_text_widget.configure(state="disabled")

    def update_language(self):
        texts = self.main_app.texts
        self.log_frame_display_title_label.configure(text=texts.get("log_frame"))
