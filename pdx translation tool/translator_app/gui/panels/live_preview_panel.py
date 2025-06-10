import customtkinter as ctk
from ...utils.localization import get_text

class LivePreviewPanel(ctk.CTkFrame):
    """
    번역 중인 텍스트의 원본과 번역본을 실시간으로 표시하는 패널.
    """
    def __init__(self, parent, main_app):
        super().__init__(parent, corner_radius=12)
        self.main_app = main_app
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # 원본 텍스트 섹션
        self.original_label = ctk.CTkLabel(
            self, 
            text=get_text("review_original_label") or "Original"
        )
        self.original_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")

        self.original_textbox = ctk.CTkTextbox(
            self, 
            height=150, 
            corner_radius=8, 
            state="disabled"
        )
        self.original_textbox.grid(row=1, column=0, padx=10, pady=(2, 10), sticky="nsew")

        # 번역 텍스트 섹션
        self.translated_label = ctk.CTkLabel(
            self, 
            text=get_text("review_translated_label") or "Translated"
        )
        self.translated_label.grid(row=2, column=0, padx=10, pady=(10, 2), sticky="w")

        self.translated_textbox = ctk.CTkTextbox(
            self, 
            height=150, 
            corner_radius=8, 
            state="disabled"
        )
        self.translated_textbox.grid(row=3, column=0, padx=10, pady=(2, 10), sticky="nsew")

        # 정보 프레임 (품질 점수, 오류 상태)
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

        self.quality_label = ctk.CTkLabel(
            info_frame, 
            text=f"{get_text('col_quality') or 'Quality'}: -"
        )
        self.quality_label.grid(row=0, column=0, sticky="w")

        self.error_label = ctk.CTkLabel(
            info_frame, 
            text=get_text('status_waiting') or 'Waiting...', 
            text_color="gray"
        )
        self.error_label.grid(row=0, column=1, sticky="e")
        
    def clear_preview(self):
        """미리보기 패널을 초기화합니다."""
        self._update_preview_display("", "", 0, False, is_idle=True)

    def add_preview_line(self, original, translated, quality_score=None, has_error=False):
        """
        translator_engine에서 호출하는 메서드.
        실시간으로 번역 결과를 표시합니다.
        """
        if not self.winfo_exists():
            return
            
        if quality_score is None:
            quality_score = 100
        
        self._update_preview_display(original, translated, quality_score, has_error, is_idle=False)

    def _update_preview_display(self, original_text, translated_text, quality_score, has_error, is_idle=False):
        """UI 스레드에서 안전하게 미리보기를 업데이트합니다."""
        def update():
            if not self.winfo_exists():
                return
                
            # 원본 텍스트 업데이트
            self.original_textbox.configure(state="normal")
            self.original_textbox.delete("1.0", "end")
            self.original_textbox.insert("1.0", str(original_text))
            self.original_textbox.configure(state="disabled")

            # 번역 텍스트 업데이트
            self.translated_textbox.configure(state="normal")
            self.translated_textbox.delete("1.0", "end")
            self.translated_textbox.insert("1.0", str(translated_text))
            self.translated_textbox.configure(state="disabled")
            
            if is_idle:
                # 대기 상태
                self.quality_label.configure(
                    text=f"{get_text('col_quality') or 'Quality'}: -", 
                    text_color="gray"
                )
                self.error_label.configure(
                    text=get_text('status_waiting') or 'Waiting...', 
                    text_color="gray"
                )
            else:
                # 품질 점수 표시
                self.quality_label.configure(
                    text=f"{get_text('col_quality') or 'Quality'}: {quality_score:.0f}"
                )
                
                # 품질에 따른 색상
                if quality_score >= 85:
                    self.quality_label.configure(text_color="lightgreen")
                elif quality_score >= 60:
                    self.quality_label.configure(text_color="yellow")
                else:
                    self.quality_label.configure(text_color="lightcoral")

                # 오류 상태 표시
                if has_error:
                    self.error_label.configure(
                        text=get_text("validation_error_regex") or "Format Error", 
                        text_color="red"
                    )
                else:
                    self.error_label.configure(
                        text=get_text("no_errors") or "No Errors", 
                        text_color="green"
                    )

        # UI 스레드에서 실행
        self.after(0, update)

    def update_language(self):
        """UI 언어 변경 시 이 패널의 모든 정적 텍스트를 업데이트합니다."""
        self.original_label.configure(text=get_text("review_original_label") or "Original")
        self.translated_label.configure(text=get_text("review_translated_label") or "Translated")
        
        # 현재 상태에 맞게 라벨 업데이트
        current_quality_text = self.quality_label.cget("text")
        if ": -" in current_quality_text:
            self.quality_label.configure(text=f"{get_text('col_quality') or 'Quality'}: -")
        
        current_error_text = self.error_label.cget("text")
        if current_error_text == (get_text('status_waiting') or 'Waiting...'):
            self.error_label.configure(text=get_text('status_waiting') or 'Waiting...')