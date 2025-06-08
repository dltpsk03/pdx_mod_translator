# translator_project/translator_app/gui/comparison_review_window.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import codecs
import os
import re
import shutil
from datetime import datetime

class ComparisonReviewWindow(ctk.CTkToplevel):
    def __init__(self, master_window, translator_engine, main_texts, input_folder_path, output_folder_path, source_lang_api, target_lang_api):
        super().__init__(master_window)
        
        self.master_app = master_window
        self.translator_engine = translator_engine
        self.texts = main_texts
        self.input_folder = input_folder_path
        self.output_folder = output_folder_path
        self.source_lang_api_name = source_lang_api
        self.target_lang_api_name = target_lang_api

        # 창 설정
        self.title(self.texts.get("comparison_review_window_title", "📄 File Comparison & Review"))
        self.geometry("1600x900")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 데이터 변수들
        self.all_file_pairs = []
        self.current_display_file_pairs_indices = []
        self.current_original_lines = []
        self.current_translated_lines = []
        self.current_selected_pair_paths = None
        self.detected_errors = {}  # 오류 정보 저장
        self.current_file_content = []  # 현재 파일의 실제 내용
        self.display_only_lines = []  # 표시 전용 라인들

        # UI 상태 변수들
        self.display_mode_var = tk.StringVar(value="all")
        
        # 오류 타입 체크박스 (줄바꿈과 원본언어잔존 제거)
        self.check_code_block_error_var = tk.BooleanVar(value=True)
        self.check_unclosed_quote_error_var = tk.BooleanVar(value=True)
        self.check_merged_line_error_var = tk.BooleanVar(value=True)
        self.check_duplicate_key_error_var = tk.BooleanVar(value=True)  # 키 중복 추가

        # 변수 추적 설정
        self.display_mode_var.trace_add("write", lambda *args: self.redisplay_content_if_loaded())
        self.check_code_block_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_unclosed_quote_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_merged_line_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_duplicate_key_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))

        # 테마에 맞는 색상 설정
        self._setup_colors()
        
        # UI 생성
        self._create_modern_ui()
        
        # 데이터 초기화
        self.pre_scan_files_for_errors()
        self.filter_and_update_file_listbox()

    def _setup_colors(self):
        """테마에 맞는 색상 팔레트 설정"""
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            self.colors = {
                'bg_primary': "#1a1a1a",
                'bg_secondary': "#2d2d2d", 
                'bg_tertiary': "#3d3d3d",
                'text_primary': "#ffffff",
                'text_secondary': "#b0b0b0",
                'accent_blue': "#0078d4",
                'accent_green': "#16c60c",
                'accent_orange': "#ff8c00",
                'accent_red': "#d13438",
                'border_color': "#4a4a4a",
                'hover_color': "#404040",
                'error_bg': "#4a1515",
                'error_border': "#d13438"
            }
        else:
            self.colors = {
                'bg_primary': "#ffffff",
                'bg_secondary': "#f8f8f8",
                'bg_tertiary': "#eeeeee", 
                'text_primary': "#000000",
                'text_secondary': "#666666",
                'accent_blue': "#0078d4",
                'accent_green': "#16c60c", 
                'accent_orange': "#ff8c00",
                'accent_red': "#d13438",
                'border_color': "#cccccc",
                'hover_color': "#e5e5e5",
                'error_bg': "#ffe5e5",
                'error_border': "#d13438"
            }

    def _create_modern_ui(self):
        """직관적이고 사용자 친화적인 UI 생성"""
        
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === 상단 툴바 섹션 ===
        self._create_toolbar_section(main_container)
        
        # === 중앙 콘텐츠 섹션 ===
        self._create_content_section(main_container)
        
        # === 하단 상태바 섹션 ===
        self._create_statusbar_section(main_container)

    def _create_toolbar_section(self, parent):
        """상단 툴바 섹션 생성"""
        toolbar_frame = ctk.CTkFrame(parent, corner_radius=15, height=80)
        toolbar_frame.pack(fill="x", pady=(0, 15))
        toolbar_frame.pack_propagate(False)
        
        # 툴바 내용
        toolbar_content = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        toolbar_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 좌측: 제목
        title_frame = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="📄 " + self.texts.get("comparison_review_window_title", "File Comparison & Review"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text=self.texts.get("comparison_review_subtitle", "Compare and fix translation errors"),
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # 우측: 주요 액션 버튼들
        action_frame = ctk.CTkFrame(toolbar_content, fg_color="transparent")
        action_frame.pack(side="right", fill="y")
        
        # 일괄 백업 버튼
        self.bulk_backup_button = ctk.CTkButton(
            action_frame,
            text="📦 " + self.texts.get("bulk_backup_button", "Backup All"),
            command=self.bulk_backup_files,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=self.colors['accent_blue']
        )
        self.bulk_backup_button.pack(side="left", padx=(0, 10))
        
        # Auto Fix 버튼
        self.auto_fix_button = ctk.CTkButton(
            action_frame,
            text="🔧 " + self.texts.get("auto_fix_button", "Auto Fix"),
            command=self.auto_fix_errors,
            width=120,
            height=35,
            corner_radius=8,
            fg_color=self.colors['accent_green']
        )
        self.auto_fix_button.pack(side="left", padx=(0, 10))
        
        # 새로고침 버튼
        self.refresh_button = ctk.CTkButton(
            action_frame,
            text="🔄",
            command=self._refresh_file_list,
            width=35,
            height=35,
            corner_radius=8,
            fg_color=self.colors['accent_orange']
        )
        self.refresh_button.pack(side="left")

    def _create_content_section(self, parent):
        """중앙 콘텐츠 섹션 생성"""
        content_frame = ctk.CTkFrame(parent, corner_radius=15)
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 3-컬럼 레이아웃
        content_frame.grid_columnconfigure(0, weight=2)  # 파일 목록
        content_frame.grid_columnconfigure(1, weight=3)  # 원본
        content_frame.grid_columnconfigure(2, weight=3)  # 번역본
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 좌측: 파일 목록 및 필터
        self._create_file_list_panel(content_frame)
        
        # 중앙: 원본 파일
        self._create_original_panel(content_frame)
        
        # 우측: 번역 파일
        self._create_translated_panel(content_frame)

    def _create_file_list_panel(self, parent):
        """파일 목록 패널 생성"""
        list_panel = ctk.CTkFrame(parent, corner_radius=10)
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)
        
        # 패널 헤더
        header_frame = ctk.CTkFrame(list_panel, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="📁 " + self.texts.get("file_list_header", "Files"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.pack(side="left")
        
        self.file_count_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.file_count_label.pack(side="right")
        
        # 오류 필터 섹션
        filter_frame = ctk.CTkFrame(list_panel, corner_radius=8)
        filter_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        filter_label = ctk.CTkLabel(
            filter_frame,
            text=self.texts.get("error_filter_label", "Error Filters:"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        filter_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # 필터 체크박스들 (2x2 그리드)
        checkbox_container = ctk.CTkFrame(filter_frame, fg_color="transparent")
        checkbox_container.pack(fill="x", padx=10, pady=(0, 10))
        
        # 첫 번째 행
        row1 = ctk.CTkFrame(checkbox_container, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        
        self.code_block_checkbox = ctk.CTkCheckBox(
            row1,
            text="📦 " + self.texts.get("code_block_error", "Code Blocks"),
            variable=self.check_code_block_error_var,
            font=ctk.CTkFont(size=11),
            width=150
        )
        self.code_block_checkbox.pack(side="left", padx=(0, 10))
        
        self.unclosed_quote_checkbox = ctk.CTkCheckBox(
            row1,
            text="❝ " + self.texts.get("unclosed_quote_error", "Unclosed Quotes"),
            variable=self.check_unclosed_quote_error_var,
            font=ctk.CTkFont(size=11),
            width=150
        )
        self.unclosed_quote_checkbox.pack(side="left")
        
        # 두 번째 행
        row2 = ctk.CTkFrame(checkbox_container, fg_color="transparent")
        row2.pack(fill="x", pady=2)
        
        self.merged_line_checkbox = ctk.CTkCheckBox(
            row2,
            text="🔗 " + self.texts.get("merged_line_error", "Merged Lines"),
            variable=self.check_merged_line_error_var,
            font=ctk.CTkFont(size=11),
            width=150
        )
        self.merged_line_checkbox.pack(side="left", padx=(0, 10))
        
        self.duplicate_key_checkbox = ctk.CTkCheckBox(
            row2,
            text="🔑 " + self.texts.get("duplicate_key_error", "Duplicate Keys"),
            variable=self.check_duplicate_key_error_var,
            font=ctk.CTkFont(size=11),
            width=150
        )
        self.duplicate_key_checkbox.pack(side="left")
        
        # 표시 모드
        mode_frame = ctk.CTkFrame(list_panel, corner_radius=8)
        mode_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        mode_label = ctk.CTkLabel(
            mode_frame,
            text=self.texts.get("display_mode_label", "Display Mode:"),
            font=ctk.CTkFont(size=12, weight="bold")
        )
        mode_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        radio_container = ctk.CTkFrame(mode_frame, fg_color="transparent")
        radio_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self.all_lines_radio = ctk.CTkRadioButton(
            radio_container,
            text=self.texts.get("show_all_lines", "Show All Lines"),
            variable=self.display_mode_var,
            value="all",
            font=ctk.CTkFont(size=11)
        )
        self.all_lines_radio.pack(side="left", padx=(0, 20))
        
        self.errors_only_radio = ctk.CTkRadioButton(
            radio_container,
            text=self.texts.get("show_errors_only", "Errors Only"),
            variable=self.display_mode_var,
            value="errors",
            font=ctk.CTkFont(size=11)
        )
        self.errors_only_radio.pack(side="left")
        
        # 파일 리스트
        list_container = ctk.CTkFrame(list_panel, corner_radius=8)
        list_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 스크롤바
        scrollbar = ctk.CTkScrollbar(list_container)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        self.file_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            background=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            selectbackground=self.colors['accent_blue'],
            selectforeground="white",
            borderwidth=0,
            highlightthickness=0,
            activestyle='none',
            font=("Segoe UI", 10),
            relief="flat"
        )
        self.file_listbox.pack(fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.configure(command=self.file_listbox.yview)
        
        # 이벤트 바인딩
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)

    def _create_original_panel(self, parent):
        """원본 파일 패널 생성"""
        original_panel = ctk.CTkFrame(parent, corner_radius=10)
        original_panel.grid(row=0, column=1, sticky="nsew", padx=8, pady=15)
        
        # 헤더
        header_frame = ctk.CTkFrame(original_panel, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="📄 " + self.texts.get("original_file_header", "Original"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['accent_blue']
        )
        header_label.pack(side="left")
        
        # 텍스트 영역
        self.original_text_widget = ctk.CTkTextbox(
            original_panel,
            wrap="word",
            state="disabled",
            font=("Consolas", 11),
            corner_radius=8
        )
        self.original_text_widget.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_translated_panel(self, parent):
        """번역 파일 패널 생성"""
        translated_panel = ctk.CTkFrame(parent, corner_radius=10)
        translated_panel.grid(row=0, column=2, sticky="nsew", padx=(8, 15), pady=15)
        
        # 헤더
        header_frame = ctk.CTkFrame(translated_panel, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="🔄 " + self.texts.get("translated_file_header", "Translated (Editable)"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['accent_green']
        )
        header_label.pack(side="left")
        
        # 저장 버튼
        self.save_button = ctk.CTkButton(
            header_frame,
            text=self.texts.get("save_button", "Save"),
            command=self.save_translated_file,
            width=80,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=12)
        )
        self.save_button.pack(side="right")
        
        # 텍스트 영역
        self.translated_text_widget = ctk.CTkTextbox(
            translated_panel,
            wrap="word",
            font=("Consolas", 11),
            corner_radius=8
        )
        self.translated_text_widget.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 스크롤 동기화
        self.setup_scroll_sync()

    def _create_statusbar_section(self, parent):
        """하단 상태바 섹션 생성"""
        statusbar_frame = ctk.CTkFrame(parent, corner_radius=15, height=50)
        statusbar_frame.pack(fill="x")
        statusbar_frame.pack_propagate(False)
        
        statusbar_content = ctk.CTkFrame(statusbar_frame, fg_color="transparent")
        statusbar_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 상태 정보
        self.status_label = ctk.CTkLabel(
            statusbar_content,
            text=self.texts.get("status_ready", "Ready"),
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(side="left")
        
        # 오류 통계
        self.error_stats_label = ctk.CTkLabel(
            statusbar_content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['accent_red']
        )
        self.error_stats_label.pack(side="right")

    def setup_scroll_sync(self):
        """스크롤 동기화 설정"""
        def _sync_scroll(source_widget, target_widget, *args):
            if hasattr(source_widget, '_textbox') and hasattr(target_widget, '_textbox'):
                try:
                    scroll_info = source_widget.yview()
                    if scroll_info:
                        target_widget.yview_moveto(scroll_info[0])
                except tk.TclError:
                    pass
        
        if hasattr(self.original_text_widget, '_textbox') and hasattr(self.translated_text_widget, '_textbox'):
            try:
                self.original_text_widget._textbox.configure(
                    yscrollcommand=lambda *args: _sync_scroll(self.original_text_widget, self.translated_text_widget, *args)
                )
                self.translated_text_widget._textbox.configure(
                    yscrollcommand=lambda *args: _sync_scroll(self.translated_text_widget, self.original_text_widget, *args)
                )
            except Exception as e:
                print(f"Scroll sync setup failed: {e}")

    def _detect_translation_errors(self, original_line, translated_line, line_idx, all_keys_in_file):
        """번역 오류 검출 - 개선된 버전"""
        errors = []
        
        # 키-값 쌍 추출
        orig_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"', original_line)
        trans_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"?', translated_line)
        
        if not orig_match:
            return errors  # 원본이 키-값 형식이 아니면 검사 안함
        
        # 오류 1: 코드 블록 검출
        if '```' in translated_line:
            errors.append("code_block")
        
        # 오류 2: 따옴표가 닫히지 않음
        # 주석을 고려한 검사
        trans_line_no_comment = translated_line
        if trans_match:
            # 값이 정상적으로 닫혔는지 확인
            value_start = translated_line.find('"', translated_line.find(':') + 1)
            if value_start != -1:
                # 두 번째 따옴표 찾기
                value_end = translated_line.find('"', value_start + 1)
                if value_end != -1:
                    # 값이 닫혔으므로 그 이후는 주석일 수 있음
                    trans_line_no_comment = translated_line[:value_end + 1]
        
        # 따옴표 개수 확인
        quote_count = trans_line_no_comment.count('"')
        if quote_count % 2 != 0:
            errors.append("unclosed_quote")
        elif trans_match and not re.search(r':\d*\s*"[^"]*"\s*(?:#.*)?$', trans_line_no_comment):
            errors.append("unclosed_quote")
        
        # 오류 3: 다음 라인까지 한줄로 번역됨 
        key_value_pattern = r'[^:]+:\d*\s*"[^"]*"'
        matches = re.findall(key_value_pattern, translated_line)
        if len(matches) > 1:
            errors.append("merged_line")
        
        # 오류 4: 키 중복 검사
        if trans_match:
            key = trans_match.group(2).strip()
            if len(all_keys_in_file.get(key, [])) > 1:
                errors.append("duplicate_key")
        
        return errors

    def _detect_duplicate_keys(self, lines):
        """파일 내 중복 키 검출"""
        key_counts = {}
        duplicate_keys = {}
        
        for idx, line in enumerate(lines):
            match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"', line)
            if match:
                key = match.group(2).strip()
                if key not in key_counts:
                    key_counts[key] = []
                key_counts[key].append(idx)
        
        # 중복된 키만 추출
        for key, indices in key_counts.items():
            if len(indices) > 1:
                duplicate_keys[key] = indices
        
        return key_counts, duplicate_keys

    def pre_scan_files_for_errors(self):
        """파일 오류 사전 스캔"""
        self.all_file_pairs.clear()
        
        source_lang_l_prefix_lower = f"l_{self.translator_engine.get_language_code(self.source_lang_api_name).lower()}"
        target_lang_l_prefix_lower = f"l_{self.translator_engine.get_language_code(self.target_lang_api_name).lower()}"
        
        # 입력/출력 파일 매칭 로직은 기존과 동일...
        input_files_info = {}
        
        # 입력 폴더 스캔
        for root_input, _, files_input in os.walk(self.input_folder):
            for file_input_name in files_input:
                if not file_input_name.lower().endswith(('.yml', '.yaml')):
                    continue
                    
                original_full_path = os.path.join(root_input, file_input_name)
                relative_dir_input = os.path.relpath(root_input, self.input_folder)
                if relative_dir_input == ".":
                    relative_dir_input = ""
                
                base_name_no_lang_input = file_input_name.lower()
                if source_lang_l_prefix_lower in base_name_no_lang_input:
                    base_name_no_lang_input = re.sub(
                        re.escape(source_lang_l_prefix_lower), '', 
                        base_name_no_lang_input, 
                        flags=re.IGNORECASE
                    )
                
                input_files_info[(relative_dir_input.replace("\\", "/"), file_input_name.lower())] = original_full_path
                if base_name_no_lang_input != file_input_name.lower():
                    input_files_info[(relative_dir_input.replace("\\", "/"), base_name_no_lang_input)] = original_full_path
        
        # 출력 폴더 스캔 및 매칭
        for root_output, _, files_output in os.walk(self.output_folder):
            for file_output_name in files_output:
                if not file_output_name.lower().endswith(('.yml', '.yaml')):
                    continue
                    
                translated_full_path = os.path.join(root_output, file_output_name)
                relative_dir_output = os.path.relpath(root_output, self.output_folder)
                if relative_dir_output == ".":
                    relative_dir_output = ""
                
                original_path_found = self._find_matching_original_file(
                    file_output_name, relative_dir_output, 
                    input_files_info, target_lang_l_prefix_lower, source_lang_l_prefix_lower
                )
                
                if original_path_found and os.path.exists(original_path_found):
                    is_already_added = any(
                        p["original"] == original_path_found and p["translated"] == translated_full_path 
                        for p in self.all_file_pairs
                    )
                    
                    if not is_already_added:
                        error_info = self.scan_single_file_for_errors(
                            original_path_found, translated_full_path
                        )
                        
                        rel_orig_display = os.path.relpath(original_path_found, self.input_folder)
                        rel_trans_display = os.path.relpath(translated_full_path, self.output_folder)
                        
                        display_name = self._create_display_name(
                            original_path_found, translated_full_path,
                            rel_orig_display, rel_trans_display,
                            error_info
                        )
                        
                        file_pair_info = {
                            "original": original_path_found,
                            "translated": translated_full_path,
                            "display": display_name.strip(),
                        }
                        file_pair_info.update(error_info)
                        
                        self.all_file_pairs.append(file_pair_info)
        
        # 통계 업데이트
        self._update_stats()

    def _find_matching_original_file(self, file_output_name, relative_dir_output, input_files_info, target_lang_l_prefix_lower, source_lang_l_prefix_lower):
        """원본 파일 찾기"""
        original_path_found = None
        
        # 1. 동일한 이름으로 찾기
        key_same_name = (relative_dir_output.replace("\\", "/"), file_output_name.lower())
        if key_same_name in input_files_info:
            original_path_found = input_files_info[key_same_name]
        
        # 2. 언어 코드 제거 후 찾기
        if not original_path_found:
            base_name_output_no_lang = file_output_name.lower()
            if target_lang_l_prefix_lower in base_name_output_no_lang:
                base_name_output_no_lang = re.sub(
                    re.escape(target_lang_l_prefix_lower), '', 
                    base_name_output_no_lang, 
                    flags=re.IGNORECASE
                )
            key_lang_removed = (relative_dir_output.replace("\\", "/"), base_name_output_no_lang)
            if key_lang_removed in input_files_info:
                original_path_found = input_files_info[key_lang_removed]
        
        # 3. 언어 코드 교체해서 찾기
        if not original_path_found and target_lang_l_prefix_lower in file_output_name.lower():
            potential_original_name = re.sub(
                target_lang_l_prefix_lower,
                source_lang_l_prefix_lower,
                file_output_name.lower(),
                flags=re.IGNORECASE,
            )
            key_lang_replaced = (
                relative_dir_output.replace("\\", "/"),
                potential_original_name,
            )
            if key_lang_replaced in input_files_info:
                original_path_found = input_files_info[key_lang_replaced]

        return original_path_found

    def _create_display_name(self, original_path, translated_path, rel_orig_display, rel_trans_display, error_info):
        """파일 목록에 표시할 이름 생성"""
        trans_name = os.path.basename(translated_path)

        error_tags = []
        if error_info.get("has_code_block_error"):
            error_tags.append("📦")
        if error_info.get("has_unclosed_quote_error"):
            error_tags.append("❝")
        if error_info.get("has_merged_line_error"):
            error_tags.append("🔗")
        if error_info.get("has_duplicate_key_error"):
            error_tags.append("🔑")

        error_suffix = f" {' '.join(error_tags)}" if error_tags else ""
        
        # 경로가 길면 파일명만 표시
        if len(rel_trans_display) > 40:
            display_name = f"{trans_name}{error_suffix}"
        else:
            display_name = f"{rel_trans_display}{error_suffix}"

        return display_name

    def scan_single_file_for_errors(self, original_path, translated_path):
        """단일 파일 쌍에 대해 오류 스캔"""
        error_info = {
            "has_code_block_error": False,
            "has_unclosed_quote_error": False,
            "has_merged_line_error": False,
            "has_duplicate_key_error": False,
            "error_lines": {},  # 라인별 오류 정보
            "duplicate_keys": {}  # 중복 키 정보
        }

        translated_lines = []
        try:
            with codecs.open(translated_path, 'r', encoding='utf-8-sig') as ft:
                translated_lines = ft.readlines()
        except Exception:
            return error_info

        original_lines = []
        if os.path.exists(original_path):
            try:
                with codecs.open(original_path, 'r', encoding='utf-8-sig') as fo:
                    original_lines = fo.readlines()
            except Exception:
                original_lines = []

        # 키 중복 검사
        all_keys, duplicate_keys = self._detect_duplicate_keys(translated_lines)
        if duplicate_keys:
            error_info["has_duplicate_key_error"] = True
            error_info["duplicate_keys"] = duplicate_keys

        # 라인별 오류 검사
        for idx, t_line in enumerate(translated_lines):
            o_line = original_lines[idx] if idx < len(original_lines) else ""
            
            # 번역 오류 검출
            errors = self._detect_translation_errors(o_line, t_line, idx, all_keys)
            
            # 오류 정보 저장
            if errors:
                error_info["error_lines"][idx] = errors
                for error_type in errors:
                    error_info[f"has_{error_type}_error"] = True

        return error_info

    def filter_and_update_file_listbox(self, redisplay_current_content=False):
        """필터링 조건에 맞게 파일 목록 갱신"""
        self.file_listbox.delete(0, tk.END)
        self.current_display_file_pairs_indices.clear()

        # 필터 체크박스 상태 확인
        filters_active = any([
            self.check_code_block_error_var.get(),
            self.check_unclosed_quote_error_var.get(),
            self.check_merged_line_error_var.get(),
            self.check_duplicate_key_error_var.get()
        ])

        displayed_count = 0
        for idx, pair in enumerate(self.all_file_pairs):
            # 필터가 활성화된 경우, 선택된 오류 타입만 표시
            if filters_active:
                show_pair = False
                if self.check_code_block_error_var.get() and pair.get("has_code_block_error"):
                    show_pair = True
                if self.check_unclosed_quote_error_var.get() and pair.get("has_unclosed_quote_error"):
                    show_pair = True
                if self.check_merged_line_error_var.get() and pair.get("has_merged_line_error"):
                    show_pair = True
                if self.check_duplicate_key_error_var.get() and pair.get("has_duplicate_key_error"):
                    show_pair = True
                
                if not show_pair:
                    continue
            
            self.current_display_file_pairs_indices.append(idx)
            self.file_listbox.insert(tk.END, pair["display"])
            displayed_count += 1

        # 파일 개수 업데이트
        self.file_count_label.configure(
            text=f"{displayed_count}/{len(self.all_file_pairs)}"
        )

        if redisplay_current_content:
            self.redisplay_content_if_loaded()

    def _on_file_select(self, event):
        """파일 선택 이벤트"""
        self.load_selected_pair_and_display()

    def load_selected_pair_and_display(self):
        """선택된 파일 쌍 로드 후 표시"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        real_index = self.current_display_file_pairs_indices[selection[0]]
        pair = self.all_file_pairs[real_index]
        self.current_selected_pair_paths = (pair["original"], pair["translated"])

        self.current_original_lines = []
        self.current_translated_lines = []
        self.current_file_content = []  # 실제 파일 내용
        
        try:
            with codecs.open(pair["original"], 'r', encoding='utf-8-sig') as fo:
                self.current_original_lines = fo.readlines()
        except Exception:
            pass
            
        try:
            with codecs.open(pair["translated"], 'r', encoding='utf-8-sig') as ft:
                self.current_translated_lines = ft.readlines()
                self.current_file_content = self.current_translated_lines.copy()  # 저장용
        except Exception:
            pass

        # 현재 파일의 오류 정보 저장
        self.current_file_errors = pair.get("error_lines", {})
        self.current_duplicate_keys = pair.get("duplicate_keys", {})
        
        self._display_loaded_content()
        
        # 상태 업데이트
        filename = os.path.basename(pair["translated"])
        error_count = len(self.current_file_errors) + (len(self.current_duplicate_keys) if self.current_duplicate_keys else 0)
        if error_count > 0:
            self.status_label.configure(
                text=f"📄 {filename}"
            )
            self.error_stats_label.configure(
                text=f"⚠️ {error_count} " + self.texts.get("errors_found", "errors found")
            )
        else:
            self.status_label.configure(
                text=f"📄 {filename}"
            )
            self.error_stats_label.configure(
                text="✅ " + self.texts.get("no_errors", "No errors")
            )

    def _display_loaded_content(self):
        """로드된 콘텐츠 표시"""
        self.original_text_widget.configure(state="normal")
        self.translated_text_widget.configure(state="normal")
        self.original_text_widget.delete("1.0", tk.END)
        self.translated_text_widget.delete("1.0", tk.END)
        
        # 표시 전용 라인 초기화
        self.display_only_lines = []

        mode = self.display_mode_var.get()
        
        if mode == "errors":
            # 활성화된 필터 확인
            active_filters = []
            if self.check_code_block_error_var.get():
                active_filters.append("code_block")
            if self.check_unclosed_quote_error_var.get():
                active_filters.append("unclosed_quote")
            if self.check_merged_line_error_var.get():
                active_filters.append("merged_line")
            if self.check_duplicate_key_error_var.get():
                active_filters.append("duplicate_key")
            
            # 중복 키가 있는 라인들
            duplicate_key_lines = set()
            if self.current_duplicate_keys and "duplicate_key" in active_filters:
                for key, line_indices in self.current_duplicate_keys.items():
                    duplicate_key_lines.update(line_indices)
            
            # 오류가 있는 라인만 표시
            displayed_lines = set()
            
            # 일반 오류 라인
            for line_idx in sorted(self.current_file_errors.keys()):
                errors = self.current_file_errors[line_idx]
                if active_filters and not any(e in active_filters for e in errors):
                    continue
                displayed_lines.add(line_idx)
            
            # 중복 키 라인 추가
            displayed_lines.update(duplicate_key_lines)
            
            # 정렬된 순서로 표시
            for line_idx in sorted(displayed_lines):
                # 원본 라인 표시
                if line_idx < len(self.current_original_lines):
                    o_line = self.current_original_lines[line_idx]
                    self.original_text_widget.insert(tk.END, f"Line {line_idx + 1}: {o_line}")
                
                # 번역 라인 표시
                if line_idx < len(self.current_translated_lines):
                    t_line = self.current_translated_lines[line_idx]
                    
                    # 오류 타입 수집
                    error_types = []
                    if line_idx in self.current_file_errors:
                        error_types.extend(self.current_file_errors[line_idx])
                    if line_idx in duplicate_key_lines:
                        error_types.append("duplicate_key")
                    
                    error_desc = self._get_error_description(error_types)
                    
                    # 표시 전용 라인 추가
                    display_line = f"Line {line_idx + 1} [{error_desc}]: {t_line}"
                    self.display_only_lines.append(display_line)
                    self.translated_text_widget.insert(tk.END, display_line)
        else:
            # 모든 라인 표시 모드
            for idx, (o_line, t_line) in enumerate(zip(self.current_original_lines, self.current_translated_lines)):
                self.original_text_widget.insert(tk.END, o_line)
                self.translated_text_widget.insert(tk.END, t_line)

        self.original_text_widget.configure(state="disabled")

    def _get_error_description(self, errors):
        """오류 타입을 설명 문자열로 변환"""
        error_names = {
            "code_block": self.texts.get("code_block_error", "Code Block"),
            "unclosed_quote": self.texts.get("unclosed_quote_error", "Unclosed Quote"),
            "merged_line": self.texts.get("merged_line_error", "Merged Line"),
            "duplicate_key": self.texts.get("duplicate_key_error", "Duplicate Key")
        }
        return ", ".join(error_names.get(e, e) for e in errors)

    def redisplay_content_if_loaded(self):
        """현재 로드된 콘텐츠 재표시"""
        if self.current_selected_pair_paths:
            self._display_loaded_content()

    def save_translated_file(self):
        """번역 파일 저장"""
        if not self.current_selected_pair_paths:
            return
        
        try:
            # 오류만 표시 모드인 경우
            if self.display_mode_var.get() == "errors":
                # 텍스트 위젯의 내용을 파싱하여 원본 파일에 반영
                edited_text = self.translated_text_widget.get("1.0", tk.END)
                edited_lines = edited_text.strip().split('\n')
                
                # 수정된 라인들을 원본에 반영
                for edited_line in edited_lines:
                    if edited_line.startswith("Line "):
                        # Line 번호 추출
                        match = re.match(r'Line (\d+) \[[^\]]+\]: (.+)', edited_line)
                        if match:
                            line_num = int(match.group(1)) - 1
                            new_content = match.group(2)
                            if line_num < len(self.current_file_content):
                                # 줄바꿈 유지
                                if self.current_file_content[line_num].endswith('\n'):
                                    new_content = new_content.rstrip('\n') + '\n'
                                self.current_file_content[line_num] = new_content
                
                # 파일 저장
                with codecs.open(self.current_selected_pair_paths[1], 'w', encoding='utf-8-sig') as ft:
                    ft.writelines(self.current_file_content)
            else:
                # 전체 표시 모드인 경우 그대로 저장
                new_text = self.translated_text_widget.get("1.0", tk.END)
                with codecs.open(self.current_selected_pair_paths[1], 'w', encoding='utf-8-sig') as ft:
                    ft.write(new_text)
            
            messagebox.showinfo(
                self.texts.get("info_title", "Info"),
                self.texts.get("save_success", "File saved successfully.")
            )
            
            # 저장 후 오류 재스캔
            self._refresh_file_list()
            
        except Exception as e:
            messagebox.showerror(
                self.texts.get("error_title", "Error"), 
                f"Failed to save: {str(e)}"
            )

    def bulk_backup_files(self):
        """모든 번역 파일 백업"""
        try:
            # 백업 폴더 생성
            backup_dir = os.path.join(self.output_folder, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            backed_up_count = 0
            for pair in self.all_file_pairs:
                translated_file = pair["translated"]
                if os.path.exists(translated_file):
                    # 상대 경로 유지
                    rel_path = os.path.relpath(translated_file, self.output_folder)
                    backup_path = os.path.join(backup_dir, rel_path)
                    
                    # 백업 파일의 디렉토리 생성
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    
                    # 파일 복사
                    shutil.copy2(translated_file, backup_path)
                    backed_up_count += 1
            
            messagebox.showinfo(
                self.texts.get("info_title", "Info"),
                self.texts.get("bulk_backup_success", f"{backed_up_count} files backed up to 'backup' folder.")
            )
            
        except Exception as e:
            messagebox.showerror(
                self.texts.get("error_title", "Error"),
                f"Backup failed: {str(e)}"
            )

    def auto_fix_errors(self):
        """자동 오류 수정"""
        if not self.current_selected_pair_paths:
            messagebox.showwarning(
                self.texts.get("warn_title", "Warning"),
                self.texts.get("select_file_first", "Please select a file first.")
            )
            return
        
        # 확인 대화상자
        result = messagebox.askyesno(
            self.texts.get("confirm_title", "Confirm"),
            self.texts.get("auto_fix_confirm", "This will attempt to fix detected errors automatically. Continue?")
        )
        
        if not result:
            return
        
        try:
            fixed_count = 0
            modified_lines = self.current_file_content.copy()
            
            # 1. Code Block 오류 수정
            for idx in range(len(modified_lines)):
                if '```' in modified_lines[idx]:
                    # ``` 제거
                    modified_lines[idx] = modified_lines[idx].replace('```yaml', '')
                    modified_lines[idx] = modified_lines[idx].replace('```yml', '')
                    modified_lines[idx] = modified_lines[idx].replace('```', '')
                    fixed_count += 1
            
            # 2. Unclosed Quote 오류 수정
            for idx, errors in self.current_file_errors.items():
                if "unclosed_quote" in errors and idx < len(modified_lines):
                    line = modified_lines[idx]
                    
                    # 여러 줄에 걸친 값 확인
                    if idx + 1 < len(modified_lines):
                        next_line = modified_lines[idx + 1]
                        # 다음 줄이 키-값 형식이 아니면 연결된 것으로 판단
                        if not re.match(r'^\s*[^:]+:\d*\s*"', next_line):
                            # 현재 줄의 값 부분 찾기
                            match = re.match(r'^(\s*[^:]+:\d*\s*"[^"]*)', line)
                            if match:
                                # 다음 줄들을 확인하여 닫는 따옴표 찾기
                                combined_value = ""
                                j = idx + 1
                                while j < len(modified_lines):
                                    if '"' in modified_lines[j]:
                                        # 닫는 따옴표 찾음
                                        quote_pos = modified_lines[j].find('"')
                                        combined_value += modified_lines[j][:quote_pos]
                                        
                                        # 라인들을 하나로 합치기
                                        new_line = match.group(1) + '\\n' + combined_value + '"'
                                        if modified_lines[idx].endswith('\n'):
                                            new_line += '\n'
                                        
                                        modified_lines[idx] = new_line
                                        
                                        # 합쳐진 라인들 제거
                                        for k in range(j, idx, -1):
                                            if k < len(modified_lines):
                                                del modified_lines[k]
                                        
                                        fixed_count += 1
                                        break
                                    else:
                                        combined_value += modified_lines[j].rstrip('\n') + '\\n'
                                        j += 1
                    else:
                        # 단순히 닫는 따옴표만 누락된 경우
                        if not line.rstrip().endswith('"'):
                            line = line.rstrip()
                            if line.endswith('\n'):
                                line = line[:-1] + '"\n'
                            else:
                                line = line + '"'
                            modified_lines[idx] = line
                            fixed_count += 1
            
            # 3. Merged Line 오류 수정
            for idx, errors in self.current_file_errors.items():
                if "merged_line" in errors and idx < len(modified_lines):
                    line = modified_lines[idx]
                    
                    # 여러 키-값 쌍 분리
                    pattern = r'([^:]+:\d*\s*"[^"]*")'
                    matches = re.findall(pattern, line)
                    
                    if len(matches) > 1:
                        # 첫 번째 매치는 현재 라인에 유지
                        modified_lines[idx] = matches[0]
                        if not modified_lines[idx].endswith('\n'):
                            modified_lines[idx] += '\n'
                        
                        # 나머지는 새 라인으로 추가
                        for i, match in enumerate(matches[1:], 1):
                            new_line = match
                            if not new_line.endswith('\n'):
                                new_line += '\n'
                            modified_lines.insert(idx + i, new_line)
                        
                        fixed_count += 1
            
            # 4. Duplicate Key 오류 수정 (마지막 것만 남기기)
            if self.current_duplicate_keys:
                lines_to_remove = []
                for key, indices in self.current_duplicate_keys.items():
                    # 마지막 인덱스를 제외한 나머지를 제거 대상으로 표시
                    for idx in indices[:-1]:
                        lines_to_remove.append(idx)
                
                # 높은 인덱스부터 제거 (인덱스 변경 방지)
                for idx in sorted(lines_to_remove, reverse=True):
                    if idx < len(modified_lines):
                        del modified_lines[idx]
                        fixed_count += 1
            
            # 수정된 내용 저장
            if fixed_count > 0:
                self.current_file_content = modified_lines
                with codecs.open(self.current_selected_pair_paths[1], 'w', encoding='utf-8-sig') as ft:
                    ft.writelines(self.current_file_content)
                
                messagebox.showinfo(
                    self.texts.get("info_title", "Info"),
                    self.texts.get("auto_fix_success", f"Fixed {fixed_count} errors successfully.")
                )
                
                # 파일 다시 로드
                self._refresh_file_list()
                self.load_selected_pair_and_display()
            else:
                messagebox.showinfo(
                    self.texts.get("info_title", "Info"),
                    self.texts.get("no_errors_to_fix", "No errors to fix.")
                )
                
        except Exception as e:
            messagebox.showerror(
                self.texts.get("error_title", "Error"),
                f"Auto fix failed: {str(e)}"
            )

    def _refresh_file_list(self):
        """파일 목록 새로고침"""
        self.pre_scan_files_for_errors()
        self.filter_and_update_file_listbox()
        self._update_stats()

    def _update_stats(self):
        """통계 정보 업데이트"""
        total_files = len(self.all_file_pairs)
        error_files = sum(1 for f in self.all_file_pairs if any(f.get(f"has_{err}_error", False) 
                          for err in ["code_block", "unclosed_quote", "merged_line", "duplicate_key"]))
        
        # 파일 개수는 필터에서 업데이트하므로 여기서는 전체 통계만

    def update_language_texts(self, new_texts):
        """언어 텍스트 업데이트"""
        self.texts = new_texts
        self.title(self.texts.get("comparison_review_window_title", "File Comparison and Review"))
        
        # 모든 UI 텍스트 업데이트...
        # 버튼들
        self.bulk_backup_button.configure(text="📦 " + self.texts.get("bulk_backup_button", "Backup All"))
        self.auto_fix_button.configure(text="🔧 " + self.texts.get("auto_fix_button", "Auto Fix"))
        self.save_button.configure(text=self.texts.get("save_button", "Save"))
        
        # 체크박스들
        self.code_block_checkbox.configure(text="📦 " + self.texts.get("code_block_error", "Code Blocks"))
        self.unclosed_quote_checkbox.configure(text="❝ " + self.texts.get("unclosed_quote_error", "Unclosed Quotes"))
        self.merged_line_checkbox.configure(text="🔗 " + self.texts.get("merged_line_error", "Merged Lines"))
        self.duplicate_key_checkbox.configure(text="🔑 " + self.texts.get("duplicate_key_error", "Duplicate Keys"))
        
        # 라디오 버튼
        self.all_lines_radio.configure(text=self.texts.get("show_all_lines", "Show All Lines"))
        self.errors_only_radio.configure(text=self.texts.get("show_errors_only", "Errors Only"))

    def on_closing(self):
        """창 닫기"""
        self.destroy()