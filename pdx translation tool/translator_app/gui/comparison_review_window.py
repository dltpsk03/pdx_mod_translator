# translator_project/translator_app/gui/comparison_review_window.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import codecs
import os
import re

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
        self.geometry("1600x1000")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 데이터 변수들
        self.all_file_pairs = []
        self.current_display_file_pairs_indices = []
        self.current_original_lines = []
        self.current_translated_lines = []
        self.current_selected_pair_paths = None
        self.detected_errors = {}  # 오류 정보 저장

        # UI 상태 변수들
        self.display_mode_var = tk.StringVar(value="all")
        
        # 새로운 오류 타입 체크박스 (기존 것 제거하고 새로 추가)
        self.check_code_block_error_var = tk.BooleanVar(value=True)
        self.check_unclosed_quote_error_var = tk.BooleanVar(value=True)
        self.check_newline_error_var = tk.BooleanVar(value=True)
        self.check_merged_line_error_var = tk.BooleanVar(value=True)
        self.check_source_remnants_var = tk.BooleanVar(value=True)

        # 변수 추적 설정
        self.display_mode_var.trace_add("write", lambda *args: self.redisplay_content_if_loaded())
        self.check_code_block_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_unclosed_quote_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_newline_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_merged_line_error_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))
        self.check_source_remnants_var.trace_add("write", lambda *args: self.filter_and_update_file_listbox(redisplay_current_content=True))

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
        """모던하고 사용자 친화적인 UI 생성"""
        
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # === 상단 헤더 섹션 ===
        self._create_header_section(main_container)
        
        # === 중앙 콘텐츠 섹션 ===
        self._create_content_section(main_container)
        
        # === 하단 액션 섹션 ===
        self._create_action_section(main_container)

    def _create_header_section(self, parent):
        """상단 헤더 섹션 생성"""
        header_frame = ctk.CTkFrame(parent, corner_radius=15, height=120)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        # 헤더 내용
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 제목 및 설명
        title_label = ctk.CTkLabel(
            header_content, 
            text=self.texts.get("comparison_review_window_title", "📄 File Comparison & Review"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            header_content,
            text=self.texts.get("comparison_review_subtitle", "Compare original and translated files with advanced error detection"),
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))
        
        # 통계 정보 프레임
        stats_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        stats_frame.pack(anchor="w", pady=(10, 0))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="📊 Loading files...",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.stats_label.pack(side="left")

    def _create_content_section(self, parent):
        """중앙 콘텐츠 섹션 생성"""
        content_frame = ctk.CTkFrame(parent, corner_radius=15)
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 좌측 패널 (파일 목록 및 필터)
        self._create_left_panel(content_frame)
        
        # 우측 패널 (파일 비교 뷰)
        self._create_right_panel(content_frame)

    def _create_left_panel(self, parent):
        """좌측 패널 (파일 목록 및 필터) 생성"""
        left_panel = ctk.CTkFrame(parent, corner_radius=10, width=400)
        left_panel.pack(side="left", fill="y", padx=(15, 10), pady=15)
        left_panel.pack_propagate(False)
        
        # 패널 제목
        panel_title = ctk.CTkLabel(
            left_panel,
            text="🗂️ " + self.texts.get("comparison_review_file_pairs", "File Pairs"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        panel_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 필터 섹션
        self._create_filter_section(left_panel)
        
        # 파일 목록 섹션
        self._create_file_list_section(left_panel)

    def _create_filter_section(self, parent):
        """필터 섹션 생성"""
        filter_frame = ctk.CTkFrame(parent, corner_radius=8)
        filter_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 필터 제목
        filter_title = ctk.CTkLabel(
            filter_frame,
            text="🔍 " + self.texts.get("comparison_review_filters", "Filters"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        filter_title.pack(anchor="w", padx=12, pady=(12, 8))
        
        # 표시 모드 섹션
        display_section = ctk.CTkFrame(filter_frame, fg_color="transparent")
        display_section.pack(fill="x", padx=12, pady=(0, 8))
        
        mode_label = ctk.CTkLabel(
            display_section,
            text=self.texts.get("comparison_review_display_mode", "Display Mode:"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        mode_label.pack(anchor="w")
        
        # 라디오 버튼들을 세로로 배치
        radio_frame = ctk.CTkFrame(display_section, fg_color="transparent")
        radio_frame.pack(fill="x", pady=(5, 0))
        
        self.all_lines_radio = ctk.CTkRadioButton(
            radio_frame,
            text="📄 " + self.texts.get("comparison_review_display_all_lines", "Show All Lines"),
            variable=self.display_mode_var,
            value="all",
            font=ctk.CTkFont(size=11)
        )
        self.all_lines_radio.pack(anchor="w", pady=2)
        
        self.diff_lines_radio = ctk.CTkRadioButton(
            radio_frame,
            text="⚡ " + self.texts.get("comparison_review_display_errors_only", "Errors Only"),
            variable=self.display_mode_var,
            value="errors",
            font=ctk.CTkFont(size=11)
        )
        self.diff_lines_radio.pack(anchor="w", pady=2)
        
        # 구분선
        separator = ctk.CTkFrame(filter_frame, height=1, fg_color=self.colors['border_color'])
        separator.pack(fill="x", padx=12, pady=8)
        
        # 오류 필터 섹션
        error_section = ctk.CTkFrame(filter_frame, fg_color="transparent")
        error_section.pack(fill="x", padx=12, pady=(0, 12))
        
        error_label = ctk.CTkLabel(
            error_section,
            text=self.texts.get("comparison_review_error_filters", "Error Type Filters:"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        error_label.pack(anchor="w")
        
        # 체크박스들
        checkbox_frame = ctk.CTkFrame(error_section, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(5, 0))
        
        self.code_block_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="📦 " + self.texts.get("comparison_review_error_code_block", "Code Block Errors"),
            variable=self.check_code_block_error_var,
            font=ctk.CTkFont(size=11)
        )
        self.code_block_checkbox.pack(anchor="w", pady=2)
        
        self.unclosed_quote_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="❝ " + self.texts.get("comparison_review_error_unclosed_quote", "Unclosed Quotes"),
            variable=self.check_unclosed_quote_error_var,
            font=ctk.CTkFont(size=11)
        )
        self.unclosed_quote_checkbox.pack(anchor="w", pady=2)
        
        self.newline_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="↵ " + self.texts.get("comparison_review_error_newline", "Newline Errors"),
            variable=self.check_newline_error_var,
            font=ctk.CTkFont(size=11)
        )
        self.newline_checkbox.pack(anchor="w", pady=2)
        
        self.merged_line_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="🔗 " + self.texts.get("comparison_review_error_merged_line", "Merged Lines"),
            variable=self.check_merged_line_error_var,
            font=ctk.CTkFont(size=11)
        )
        self.merged_line_checkbox.pack(anchor="w", pady=2)
        
        self.source_remnants_checkbox = ctk.CTkCheckBox(
            checkbox_frame,
            text="🔄 " + self.texts.get("comparison_review_error_source_remnants", "Source Remnants"),
            variable=self.check_source_remnants_var,
            font=ctk.CTkFont(size=11)
        )
        self.source_remnants_checkbox.pack(anchor="w", pady=2)

    def _create_file_list_section(self, parent):
        """파일 목록 섹션 생성"""
        list_frame = ctk.CTkFrame(parent, corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 목록 제목
        list_title = ctk.CTkLabel(
            list_frame,
            text="📋 " + self.texts.get("comparison_review_file_list", "File List"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_title.pack(anchor="w", padx=12, pady=(12, 8))
        
        # 리스트박스 컨테이너
        listbox_container = ctk.CTkFrame(list_frame, corner_radius=6)
        listbox_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 스크롤바와 리스트박스
        self.file_pair_listbox_scrollbar_x = ctk.CTkScrollbar(
            listbox_container, 
            orientation="horizontal"
        )
        
        # 개선된 리스트박스 스타일
        self.file_pair_listbox = tk.Listbox(
            listbox_container,
            height=12,
            exportselection=False,
            xscrollcommand=self.file_pair_listbox_scrollbar_x.set,
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
        
        # 스크롤바 배치
        self.file_pair_listbox_scrollbar_x.pack(side="bottom", fill="x", padx=5, pady=(0, 5))
        self.file_pair_listbox.pack(fill="both", expand=True, padx=5, pady=(5, 0))
        
        # 스크롤바 설정
        self.file_pair_listbox_scrollbar_x.configure(command=self.file_pair_listbox.xview)
        
        # 이벤트 바인딩
        self.file_pair_listbox.bind("<Double-Button-1>", self._on_listbox_double_click)
        self.file_pair_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
    
    def _on_listbox_double_click(self, event):
        """리스트박스 더블클릭 이벤트 핸들러"""
        self.load_selected_pair_and_display()
    
    def _on_listbox_select(self, event):
        """리스트박스 선택 이벤트 핸들러"""
        self.load_selected_pair_and_display()

    def _create_right_panel(self, parent):
        """우측 패널 (파일 비교 뷰) 생성"""
        right_panel = ctk.CTkFrame(parent, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 15), pady=15)
        
        # 패널 제목
        panel_title = ctk.CTkLabel(
            right_panel,
            text="📝 " + self.texts.get("comparison_review_file_comparison", "File Comparison"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        panel_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 비교 뷰 섹션
        self._create_comparison_view(right_panel)

    def _create_comparison_view(self, parent):
        """비교 뷰 생성"""
        comparison_frame = ctk.CTkFrame(parent, corner_radius=8)
        comparison_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 그리드 설정
        comparison_frame.grid_columnconfigure(0, weight=1)
        comparison_frame.grid_columnconfigure(1, weight=1)
        comparison_frame.grid_rowconfigure(1, weight=1)
        
        # 원본 파일 헤더
        original_header = ctk.CTkFrame(comparison_frame, corner_radius=6, height=40)
        original_header.grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=(12, 5))
        original_header.pack_propagate(False)
        
        original_label = ctk.CTkLabel(
            original_header,
            text="📄 " + self.texts.get("comparison_review_original_file", "Original File"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['accent_blue']
        )
        original_label.pack(expand=True)
        
        # 번역본 파일 헤더
        translated_header = ctk.CTkFrame(comparison_frame, corner_radius=6, height=40)
        translated_header.grid(row=0, column=1, sticky="ew", padx=(6, 12), pady=(12, 5))
        translated_header.pack_propagate(False)
        
        translated_label = ctk.CTkLabel(
            translated_header,
            text="🔄 " + self.texts.get("comparison_review_translated_file", "Translated File (Editable)"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['accent_green']
        )
        translated_label.pack(expand=True)
        
        # 텍스트 위젯들
        self.original_text_widget = ctk.CTkTextbox(
            comparison_frame,
            wrap="word",
            state="disabled",
            undo=True,
            font=("Consolas", 11),
            corner_radius=6
        )
        self.original_text_widget.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        
        self.translated_text_widget = ctk.CTkTextbox(
            comparison_frame,
            wrap="word",
            undo=True,
            font=("Consolas", 11),
            corner_radius=6
        )
        self.translated_text_widget.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        
        # 스크롤 동기화 설정
        self.setup_scroll_sync()

    def _create_action_section(self, parent):
        """하단 액션 섹션 생성"""
        action_frame = ctk.CTkFrame(parent, corner_radius=15, height=70)
        action_frame.pack(fill="x")
        action_frame.pack_propagate(False)
        
        # 액션 컨테이너
        action_container = ctk.CTkFrame(action_frame, fg_color="transparent")
        action_container.pack(expand=True, fill="both", padx=20, pady=15)
        
        # 좌측: 상태 정보
        status_frame = ctk.CTkFrame(action_container, fg_color="transparent")
        status_frame.pack(side="left", fill="y")
        
        self.status_info_label = ctk.CTkLabel(
            status_frame,
            text="💡 " + self.texts.get("comparison_review_select_file", "Select a file pair to begin comparison"),
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_info_label.pack(anchor="w")
        
        # 우측: 액션 버튼들
        button_frame = ctk.CTkFrame(action_container, fg_color="transparent")
        button_frame.pack(side="right", fill="y")
        
        # 저장 버튼
        self.save_button = ctk.CTkButton(
            button_frame,
            text="💾 " + self.texts.get("comparison_review_save_changes_button", "Save Changes"),
            command=self.save_translated_file,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=140,
            height=40,
            corner_radius=8
        )
        self.save_button.pack(side="right", padx=(10, 0))
        
        # 새로고침 버튼
        self.refresh_button = ctk.CTkButton(
            button_frame,
            text="🔄 " + self.texts.get("review_refresh", "Refresh"),
            command=self._refresh_file_list,
            font=ctk.CTkFont(size=12),
            width=100,
            height=40,
            corner_radius=8,
            fg_color=self.colors['accent_orange'],
            hover_color=self._darken_color(self.colors['accent_orange'])
        )
        self.refresh_button.pack(side="right")

    def _darken_color(self, color, factor=0.8):
        """색상을 어둡게 만드는 헬퍼 함수"""
        if color.startswith('#'):
            try:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16) 
                b = int(color[5:7], 16)
                return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"
            except ValueError:
                return color
        return color

    def _refresh_file_list(self):
        """파일 목록 새로고침"""
        self.pre_scan_files_for_errors()
        self.filter_and_update_file_listbox()
        self._update_stats()

    def _update_stats(self):
        """통계 정보 업데이트"""
        total_files = len(self.all_file_pairs)
        error_files = sum(1 for f in self.all_file_pairs if any(f.get(f"has_{err}_error", False) 
                          for err in ["code_block", "unclosed_quote", "newline", "merged_line", "source"]))
        
        stats_text = f"📊 {total_files} " + self.texts.get("comparison_review_file_pairs_found", "file pairs found")
        if error_files > 0:
            stats_text += f" • ⚠️ {error_files} " + self.texts.get("comparison_review_with_errors", "with errors")
        
        self.stats_label.configure(text=stats_text)

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

    def _detect_translation_errors(self, original_line, translated_line, line_idx):
        """번역 오류 검출 - 4가지 주요 패턴"""
        errors = []
        
        # 키-값 쌍 추출
        orig_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"', original_line)
        trans_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"?', translated_line)
        
        if not orig_match:
            return errors  # 원본이 키-값 형식이 아니면 검사 안함
        
        # 오류 1: 코드 블록 (```yml, ```yaml, ```) 검출
        if translated_line.strip().startswith('```'):
            errors.append("code_block")
        
        # 오류 2: 따옴표가 닫히지 않음
        quote_count = translated_line.count('"')
        if quote_count % 2 != 0:
            errors.append("unclosed_quote")
        elif trans_match and not translated_line.rstrip().endswith('"'):
            # 값이 따옴표로 끝나지 않는 경우
            errors.append("unclosed_quote")
        
        # 오류 3: 줄바꿈 문자 누락으로 인한 개행
        if orig_match and trans_match:
            orig_value = orig_match.group(3)
            trans_value = trans_match.group(3) if trans_match else ""
            
            # 원본에 \n이 있는데 번역본에서 실제 개행이 발생한 경우
            orig_newline_count = orig_value.count('\\n')
            if orig_newline_count > 0 and '\n' in translated_line:
                errors.append("newline")
        
        # 오류 4: 다음 라인까지 한줄로 번역됨
        # 번역된 라인에 두 개 이상의 키-값 쌍이 있는지 확인
        key_value_pattern = r'[^:]+:\d*\s*"[^"]*"'
        matches = re.findall(key_value_pattern, translated_line)
        if len(matches) > 1:
            errors.append("merged_line")
        
        return errors

    def _check_source_remnants_optimized(self, value_text, original_value):
        """원본과 동일한 값이 번역 결과에 남아있는지 확인"""
        if value_text is None or original_value is None:
            return False
        
        # 완전히 동일한 경우
        if value_text.strip() == original_value.strip():
            return True
        
        # 영어 패턴 검출 (3글자 이상의 영어 단어가 2개 이상 연속)
        if self.source_lang_api_name.lower() == "english":
            pattern = r'\b[a-zA-Z]{3,}(?:\s+[a-zA-Z]{2,})+\b'
            if re.search(pattern, value_text) and re.search(pattern, original_value):
                # 번역 후에도 상당 부분의 영어가 남아있는지 확인
                if len(value_text) > 10 and value_text.count(' ') > 2:
                    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', value_text)
                    if len(english_words) > len(value_text.split()) * 0.5:
                        return True
        
        return False

    def pre_scan_files_for_errors(self):
        """파일 오류 사전 스캔"""
        self.all_file_pairs.clear()
        
        source_lang_l_prefix_lower = f"l_{self.translator_engine.get_language_code(self.source_lang_api_name).lower()}"
        target_lang_l_prefix_lower = f"l_{self.translator_engine.get_language_code(self.target_lang_api_name).lower()}"
        
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
        orig_name = os.path.basename(original_path)
        trans_name = os.path.basename(translated_path)

        error_tags = []
        if error_info.get("has_code_block_error"):
            error_tags.append("📦")
        if error_info.get("has_unclosed_quote_error"):
            error_tags.append("❝")
        if error_info.get("has_newline_error"):
            error_tags.append("↵")
        if error_info.get("has_merged_line_error"):
            error_tags.append("🔗")
        if error_info.get("has_source_error"):
            error_tags.append("🔄")

        error_suffix = f" {' '.join(error_tags)}" if error_tags else ""

        orig_path_display = f"/{rel_orig_display}" if rel_orig_display != "." else ""
        trans_path_display = f"/{rel_trans_display}" if rel_trans_display != "." else ""

        return f"{orig_name}{orig_path_display} → {trans_name}{trans_path_display}{error_suffix}"

    def scan_single_file_for_errors(self, original_path, translated_path):
        """단일 파일 쌍에 대해 오류 스캔"""
        error_info = {
            "has_code_block_error": False,
            "has_unclosed_quote_error": False,
            "has_newline_error": False,
            "has_merged_line_error": False,
            "has_source_error": False,
            "error_lines": {}  # 라인별 오류 정보 저장
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

        for idx, t_line in enumerate(translated_lines):
            o_line = original_lines[idx] if idx < len(original_lines) else ""
            
            # 번역 오류 검출
            errors = self._detect_translation_errors(o_line, t_line, idx)
            
            # 원본 언어 잔존 검사
            orig_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"', o_line)
            trans_match = re.match(r'^(\s*)([^:]+):\d*\s*"([^"]*)"?', t_line)
            
            if orig_match and trans_match:
                orig_value = orig_match.group(3)
                trans_value = trans_match.group(3) if trans_match else ""
                if self._check_source_remnants_optimized(trans_value, orig_value):
                    errors.append("source")
            
            # 오류 정보 저장
            if errors:
                error_info["error_lines"][idx] = errors
                for error_type in errors:
                    error_info[f"has_{error_type}_error"] = True

        return error_info

    def filter_and_update_file_listbox(self, redisplay_current_content=False):
        """필터링 조건에 맞게 파일 목록 갱신"""
        self.file_pair_listbox.delete(0, tk.END)
        self.current_display_file_pairs_indices.clear()

        # 필터 체크박스 상태 확인
        filters_active = any([
            self.check_code_block_error_var.get(),
            self.check_unclosed_quote_error_var.get(),
            self.check_newline_error_var.get(),
            self.check_merged_line_error_var.get(),
            self.check_source_remnants_var.get()
        ])

        for idx, pair in enumerate(self.all_file_pairs):
            # 필터가 활성화된 경우, 선택된 오류 타입만 표시
            if filters_active:
                show_pair = False
                if self.check_code_block_error_var.get() and pair.get("has_code_block_error"):
                    show_pair = True
                if self.check_unclosed_quote_error_var.get() and pair.get("has_unclosed_quote_error"):
                    show_pair = True
                if self.check_newline_error_var.get() and pair.get("has_newline_error"):
                    show_pair = True
                if self.check_merged_line_error_var.get() and pair.get("has_merged_line_error"):
                    show_pair = True
                if self.check_source_remnants_var.get() and pair.get("has_source_error"):
                    show_pair = True
                
                if not show_pair:
                    continue
            
            self.current_display_file_pairs_indices.append(idx)
            self.file_pair_listbox.insert(tk.END, pair["display"])

        if redisplay_current_content:
            self.redisplay_content_if_loaded()

    def load_selected_pair_and_display(self):
        """선택된 파일 쌍 로드 후 표시"""
        selection = self.file_pair_listbox.curselection()
        if not selection:
            return
        real_index = self.current_display_file_pairs_indices[selection[0]]
        pair = self.all_file_pairs[real_index]
        self.current_selected_pair_paths = (pair["original"], pair["translated"])

        self.current_original_lines = []
        self.current_translated_lines = []
        try:
            with codecs.open(pair["original"], 'r', encoding='utf-8-sig') as fo:
                self.current_original_lines = fo.readlines()
        except Exception:
            pass
        try:
            with codecs.open(pair["translated"], 'r', encoding='utf-8-sig') as ft:
                self.current_translated_lines = ft.readlines()
        except Exception:
            pass

        # 현재 파일의 오류 정보 저장
        self.current_file_errors = pair.get("error_lines", {})
        
        self._display_loaded_content()
        
        # 상태 업데이트
        filename = os.path.basename(pair["translated"])
        error_count = len(self.current_file_errors)
        if error_count > 0:
            status_text = f"⚠️ {filename} - {error_count} " + self.texts.get("comparison_review_errors_found", "errors found")
        else:
            status_text = f"✅ {filename} - " + self.texts.get("comparison_review_no_errors", "No errors detected")
        self.status_info_label.configure(text=status_text)

    # _display_loaded_content 메서드 완전 교체 (약 1100번 줄):
    def _display_loaded_content(self):
        """로드된 콘텐츠 표시"""
        self.original_text_widget.configure(state="normal")
        self.translated_text_widget.configure(state="normal")
        self.original_text_widget.delete("1.0", tk.END)
        self.translated_text_widget.delete("1.0", tk.END)

        mode = self.display_mode_var.get()
        
        if mode == "errors":
            # 활성화된 필터 확인
            active_filters = []
            if self.check_code_block_error_var.get():
                active_filters.append("code_block")
            if self.check_unclosed_quote_error_var.get():
                active_filters.append("unclosed_quote")
            if self.check_newline_error_var.get():
                active_filters.append("newline")
            if self.check_merged_line_error_var.get():
                active_filters.append("merged_line")
            if self.check_source_remnants_var.get():
                active_filters.append("source")
            
            # 오류가 있는 라인만 표시
            for line_idx in sorted(self.current_file_errors.keys()):
                errors = self.current_file_errors[line_idx]
                
                # 필터가 활성화되어 있고, 현재 라인의 오류가 필터와 매치되지 않으면 건너뛰기
                if active_filters and not any(e in active_filters for e in errors):
                    continue
                
                # 원본 라인 표시
                if line_idx < len(self.current_original_lines):
                    o_line = self.current_original_lines[line_idx]
                    self.original_text_widget.insert(tk.END, f"Line {line_idx + 1}: {o_line}")
                
                # 번역 라인 표시 (오류 설명 포함)
                if line_idx < len(self.current_translated_lines):
                    t_line = self.current_translated_lines[line_idx]
                    error_desc = self._get_error_description([e for e in errors if not active_filters or e in active_filters])
                    self.translated_text_widget.insert(tk.END, f"Line {line_idx + 1} [{error_desc}]: {t_line}")
        else:
            # 모든 라인 표시 모드
            for idx, (o_line, t_line) in enumerate(zip(self.current_original_lines, self.current_translated_lines)):
                self.original_text_widget.insert(tk.END, o_line)
                
                if idx in self.current_file_errors:
                    errors = self.current_file_errors[idx]
                    error_desc = self._get_error_description(errors)
                    # 오류 라인 마커 추가
                    self.translated_text_widget.insert(tk.END, f"⚠️ [{error_desc}] ", "error")
                
                self.translated_text_widget.insert(tk.END, t_line)

        self.original_text_widget.configure(state="disabled")
        
        # 오류 태그 스타일 설정
        if hasattr(self.translated_text_widget, '_textbox'):
            self.translated_text_widget._textbox.tag_config("error", foreground=self.colors['accent_red'])

    def _get_error_description(self, errors):
        """오류 타입을 설명 문자열로 변환"""
        error_names = {
            "code_block": self.texts.get("comparison_review_error_code_block", "Code Block"),
            "unclosed_quote": self.texts.get("comparison_review_error_unclosed_quote", "Unclosed Quote"),
            "newline": self.texts.get("comparison_review_error_newline", "Newline"),
            "merged_line": self.texts.get("comparison_review_error_merged_line", "Merged Line"),
            "source": self.texts.get("comparison_review_error_source_lang", "Source Remnant")
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
        new_text = self.translated_text_widget.get("1.0", tk.END)
        try:
            with codecs.open(self.current_selected_pair_paths[1], 'w', encoding='utf-8-sig') as ft:
                ft.write(new_text)
            messagebox.showinfo(
                self.texts.get("info_title", "Info"),
                self.texts.get("review_save_success", "Changes saved successfully.")
            )
            # 저장 후 오류 재스캔
            self._refresh_file_list()
        except Exception as e:
            messagebox.showerror(self.texts.get("error_title", "Error"), str(e))

    def update_language_texts(self, new_texts):
        """언어 텍스트 업데이트"""
        self.texts = new_texts
        self.title(self.texts.get("comparison_review_window_title", "File Comparison and Review"))
        
        # 라디오 버튼
        self.all_lines_radio.configure(text="📄 " + self.texts.get("comparison_review_display_all_lines", "Display All Lines"))
        self.diff_lines_radio.configure(text="⚡ " + self.texts.get("comparison_review_display_errors_only", "Errors Only"))
        
        # 체크박스
        self.code_block_checkbox.configure(text="📦 " + self.texts.get("comparison_review_error_code_block", "Code Block Errors"))
        self.unclosed_quote_checkbox.configure(text="❝ " + self.texts.get("comparison_review_error_unclosed_quote", "Unclosed Quotes"))
        self.newline_checkbox.configure(text="↵ " + self.texts.get("comparison_review_error_newline", "Newline Errors"))
        self.merged_line_checkbox.configure(text="🔗 " + self.texts.get("comparison_review_error_merged_line", "Merged Lines"))
        self.source_remnants_checkbox.configure(text="🔄 " + self.texts.get("comparison_review_error_source_remnants", "Source Remnants"))
        
        # 버튼
        self.save_button.configure(text="💾 " + self.texts.get("comparison_review_save_changes_button", "Save Changes"))
        self.refresh_button.configure(text="🔄 " + self.texts.get("review_refresh", "Refresh"))

    def on_closing(self):
        """창 닫기"""
        self.destroy()