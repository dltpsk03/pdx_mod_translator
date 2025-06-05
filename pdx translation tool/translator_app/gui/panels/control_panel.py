# translator_project/translator_app/gui/panels/control_panel.py
import customtkinter as ctk
import tkinter as tk
from ..tooltip import Tooltip

class ControlPanel(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)
        self.main_app = main_app

        self.grid_columnconfigure(0, weight=1) # 버튼들을 중앙에 배치하기 위함

        button_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_container_frame.pack(pady=5) # pack을 사용하여 중앙 정렬

        # --- 번역 시작 버튼 ---
        self.translate_btn_widget = ctk.CTkButton(button_container_frame,
                                                  command=self.main_app.start_translation,
                                                  width=120, height=32, font=ctk.CTkFont(weight="bold"))
        self.translate_btn_widget.pack(side="left", padx=(0,5))
        self.translate_btn_tooltip = Tooltip(self.translate_btn_widget, "")

        # --- 중지 버튼 ---
        self.stop_btn_widget = ctk.CTkButton(button_container_frame,
                                             command=self.main_app.stop_translation, # 번역/검증 공용 중지
                                             state='disabled', width=120, height=32)
        self.stop_btn_widget.pack(side="left", padx=(5,0))
        self.stop_btn_tooltip = Tooltip(self.stop_btn_widget, "") # 툴팁은 번역 중지용으로 유지

        # 진행 상황 프레임 (이전과 동일)
        self.progress_frame_display = ctk.CTkFrame(self, corner_radius=10)
        self.progress_frame_display.pack(fill="x", padx=0, pady=(10,0)) # 버튼과 간격 추가

        self.progress_frame_display_title_label = ctk.CTkLabel(self.progress_frame_display, font=ctk.CTkFont(size=13, weight="bold"))
        self.progress_frame_display_title_label.pack(side=tk.TOP, anchor="w", padx=10, pady=(7,5))

        self.progress_label_widget = ctk.CTkLabel(self.progress_frame_display, textvariable=self.main_app.progress_text_var, anchor="w")
        self.progress_label_widget.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame_display, mode='determinate', height=10, corner_radius=5)
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(0,10))
        self.progress_bar.set(0)

        self.update_language()

    def set_progress(self, value):
        self.progress_bar.set(value)

    def set_translate_button_state(self, state):
        self.translate_btn_widget.configure(state=state)

    def set_stop_button_state(self, state):
        self.stop_btn_widget.configure(state=state)

    def update_language(self):
        texts = self.main_app.texts
        if hasattr(self.main_app, 'texts') and self.main_app.texts: # self.main_app.texts가 로드되었는지 확인
            self.translate_btn_widget.configure(text=texts.get("translate_button"))
            self.translate_btn_tooltip.update_text(texts.get("translate_button_tooltip"))
            self.stop_btn_widget.configure(text=texts.get("stop_button"))
            self.stop_btn_tooltip.update_text(texts.get("stop_button_tooltip"))
            self.progress_frame_display_title_label.configure(text=texts.get("progress_frame"))