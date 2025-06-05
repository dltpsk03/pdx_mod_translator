# translator_project/translator_app/gui/validation_window.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
from .tooltip import Tooltip # tooltip.py가 gui 폴더에 있다고 가정

class ValidationWindow(ctk.CTkToplevel):
    def __init__(self, master_window, translator_engine, main_texts):
        super().__init__(master_window)
        self.master_app = master_window # main_window 참조
        self.translator_engine = translator_engine
        self.texts = main_texts # main_window의 texts 참조 (언어 변경 시 업데이트 필요)

        self.title(self.texts.get("validation_window_title", "Validate Files"))
        self.geometry("800x600")
        self.grab_set() # 모달처럼 동작

        # --- 내부 변수 ---
        self.check_regex_error_var = tk.BooleanVar(value=True)
        self.check_source_lang_remnant_var = tk.BooleanVar(value=True)
        self.current_validation_output_dir = None

        # --- UI 구성 ---
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(pady=10, padx=10, fill="x")

        self.regex_error_checkbox = ctk.CTkCheckBox(options_frame,
                                                    text=self.texts.get("validation_regex_error_check_label", "Regex Check"),
                                                    variable=self.check_regex_error_var)
        self.regex_error_checkbox.pack(side="left", padx=(0, 10))
        self.regex_error_checkbox_tooltip = Tooltip(self.regex_error_checkbox, self.texts.get("validation_regex_error_check_tooltip", "Tooltip"))

        self.source_lang_remnant_checkbox = ctk.CTkCheckBox(options_frame,
                                                            text=self.texts.get("validation_source_lang_check_label", "Source Lang Check"),
                                                            variable=self.check_source_lang_remnant_var)
        self.source_lang_remnant_checkbox.pack(side="left", padx=(0, 10))
        self.source_lang_remnant_checkbox_tooltip = Tooltip(self.source_lang_remnant_checkbox, self.texts.get("validation_source_lang_check_tooltip", "Tooltip"))

        self.start_button = ctk.CTkButton(options_frame,
                                          text=self.texts.get("validation_start_button", "Start Validation"),
                                          command=self.start_validation_in_window)
        self.start_button.pack(side="left", padx=(10, 5))

        self.stop_button = ctk.CTkButton(options_frame,
                                         text=self.texts.get("stop_button", "Stop"), # "중지" 재활용
                                         command=self.stop_validation_in_window,
                                         state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(self, text=self.texts.get("validation_status_idle", "Idle."), anchor="w")
        self.status_label.pack(pady=(0,5), padx=10, fill="x")
        
        self.results_textbox = ctk.CTkTextbox(self, wrap="word", corner_radius=8, border_width=1)
        self.results_textbox.pack(pady=10, padx=10, fill="both", expand=True)
        self.results_textbox.configure(state="disabled")

        # 창 닫기 이벤트 처리
        self.protocol("WM_DELETE_WINDOW", self.on_closing)


    def start_validation_in_window(self):
        output_dir = self.master_app.output_folder_var.get() # main_app에서 출력 폴더 가져오기
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror(self.texts.get("error_title", "Error"),
                                 self.texts.get("validation_no_output_folder", "Output folder not set."))
            return

        check_regex = self.check_regex_error_var.get()
        check_source_lang = self.check_source_lang_remnant_var.get()

        if not check_regex and not check_source_lang:
            messagebox.showinfo(self.texts.get("info_title", "Information"),
                                self.texts.get("validation_select_checks", "Select checks."))
            return

        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", tk.END)
        self.results_textbox.insert("1.0", self.texts.get("validation_running", "Validation running...") + "\n")
        self.results_textbox.configure(state="disabled")

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text=self.texts.get("validation_running", "Validation running..."))
        self.update_idletasks()

        source_lang_ui_selected = self.master_app.source_lang_for_api_var.get() # main_app에서 원본 언어 가져오기

        # TranslatorEngine의 검증 시작 메서드 호출
        # 콜백을 통해 결과를 이 창의 _display_validation_results_in_window 로 전달
        self.translator_engine.start_validation_process(
            output_dir,
            check_regex,
            check_source_lang,
            self._display_validation_results_in_window, # 이 창의 메서드를 콜백으로 전달
            source_lang_ui_selected,
            self._update_validation_progress_in_window, # 진행률 콜백
            self._update_validation_status_in_window # 상태 콜백
        )

    def stop_validation_in_window(self):
        self.translator_engine.request_stop_validation()
        # 버튼 상태 등은 _update_validation_status_in_window 콜백에서 처리될 것

    def _update_validation_progress_in_window(self, current_count, total_items, progress_value, task_type):
        if task_type == "validation": # 이 창은 validation 진행률만 관심
            if total_items > 0:
                status_text = self.texts.get("validation_running_progress", "Validating... ({0}/{1})").format(current_count, total_items)
                self.status_label.configure(text=status_text)
            # progress_bar는 이 창에 없으므로 main_window의 것을 직접 업데이트하지 않음
            self.update_idletasks()


    def _update_validation_status_in_window(self, status_key, *args, task_type):
        if task_type == "validation": # 이 창은 validation 상태만 관심
            current_status_text = self.texts.get(status_key, status_key)
            if status_key in ["status_stopped", "status_completed_all", "status_completed_some"] and args:
                 try: current_status_text = current_status_text.format(args[0], args[1])
                 except IndexError: pass

            self.status_label.configure(text=current_status_text)

            if status_key == "validation_running":
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
            else: # "validation_completed", "status_stopped", "status_no_files_to_validate" 등
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                if status_key == "validation_no_files_to_validate": # 검증할 파일 없음
                    self.results_textbox.configure(state="normal")
                    self.results_textbox.delete("1.0", tk.END)
                    self.results_textbox.insert("1.0", self.texts.get("validation_no_files_in_output", "No files.") + "\n")
                    self.results_textbox.configure(state="disabled")

            self.update_idletasks()


    def _display_validation_results_in_window(self, results_details):
        self.results_textbox.configure(state="normal")
        self.results_textbox.delete("1.0", tk.END) # 이전 결과 지우기

        if not results_details:
            self.results_textbox.insert("1.0", self.texts.get("validation_no_issues_found", "No issues found.") + "\n")
        else:
            for detail in results_details:
                if "message_key" in detail:
                    self.results_textbox.insert(tk.END, self.texts.get(detail["message_key"], detail["message_key"]) + "\n")
                else:
                    file_info = self.master_app.log_message("validation_error_file_line", detail["file"], detail["line_num"], return_formatted=True)
                    type_info = self.texts.get(detail["type_key"], "Unknown Error Type")
                    
                    result_str = f"{file_info}\n  {type_info}\n"
                    if detail.get("original"):
                        result_str += f"{self.master_app.log_message('validation_original_content', detail['original'], return_formatted=True)}\n"
                    if detail.get("translated"):
                        result_str += f"{self.master_app.log_message('validation_translated_content', detail['translated'], return_formatted=True)}\n"
                    result_str += "-"*30 + "\n"
                    self.results_textbox.insert(tk.END, result_str)

        self.results_textbox.configure(state="disabled")
        self.update_idletasks()

    def on_closing(self):
        """창 닫기 버튼 클릭 시, 진행 중인 검증 작업 중지 요청"""
        if self.translator_engine.validation_thread and self.translator_engine.validation_thread.is_alive():
            self.translator_engine.request_stop_validation()
            # 여기서 join을 하면 UI가 멈출 수 있으므로, 엔진에서 알아서 정리하도록 둠
        self.destroy()

    def update_language_texts(self, new_texts):
        self.texts = new_texts
        self.title(self.texts.get("validation_window_title", "Validate Files"))
        self.regex_error_checkbox.configure(text=self.texts.get("validation_regex_error_check_label", "Regex Check"))
        self.regex_error_checkbox_tooltip.update_text(self.texts.get("validation_regex_error_check_tooltip", "Tooltip"))
        self.source_lang_remnant_checkbox.configure(text=self.texts.get("validation_source_lang_check_label", "Source Lang Check"))
        self.source_lang_remnant_checkbox_tooltip.update_text(self.texts.get("validation_source_lang_check_tooltip", "Tooltip"))
        self.start_button.configure(text=self.texts.get("validation_start_button", "Start Validation"))
        self.stop_button.configure(text=self.texts.get("stop_button", "Stop"))
        # status_label은 현재 상태에 따라 동적으로 업데이트되므로, 여기서 직접 설정하지 않거나
        # 현재 상태 키를 저장해두었다가 해당 키로 텍스트를 다시 가져와 설정할 수 있습니다.
        # 예를 들어, self.status_label.configure(text=self.texts.get(self.current_status_key_for_window, "Idle."))