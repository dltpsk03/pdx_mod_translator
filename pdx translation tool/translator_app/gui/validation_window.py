# translator_project/translator_app/gui/validation_window.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
import codecs
import re
import threading
import google.generativeai as genai
from .tooltip import Tooltip
import time

class ValidationWindow(ctk.CTkToplevel):
    """미번역 항목 검출 및 재번역 도구"""
    def __init__(self, master_window, translator_engine, main_texts):
        super().__init__(master_window)
        self.master_app = master_window
        self.translator_engine = translator_engine
        self.texts = main_texts

        self.title(self.texts.get("retranslation_window_title", "Retranslation Tool"))
        self.geometry("1200x800")
        self.grab_set()

        # 내부 변수
        self.untranslated_items = []  # 미번역 항목 리스트
        self.selected_items_for_retranslation = []
        self.is_scanning = False
        self.is_retranslating = False
        self.stop_event = threading.Event()
        
        # 테마 색상
        self._setup_colors()
        
        # UI 구성
        self._create_ui()
        
        # 창 닫기 이벤트 처리
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_colors(self):
        """테마에 맞는 색상 설정"""
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            self.colors = {
                'bg_primary': "#1a1a1a",
                'bg_secondary': "#2d2d2d",
                'text_primary': "#ffffff",
                'text_secondary': "#b0b0b0",
                'accent_blue': "#0078d4",
                'accent_green': "#16c60c",
                'accent_red': "#d13438",
                'border_color': "#4a4a4a"
            }
        else:
            self.colors = {
                'bg_primary': "#ffffff",
                'bg_secondary': "#f8f8f8",
                'text_primary': "#000000",
                'text_secondary': "#666666",
                'accent_blue': "#0078d4",
                'accent_green': "#16c60c",
                'accent_red': "#d13438",
                'border_color': "#cccccc"
            }

    def _create_ui(self):
        """UI 생성"""
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 헤더
        self._create_header(main_container)
        
        # 콘텐츠 영역
        content_frame = ctk.CTkFrame(main_container, corner_radius=15)
        content_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        # 좌측: 파일 목록 및 스캔 결과
        self._create_left_panel(content_frame)
        
        # 우측: 미번역 항목 상세 보기
        self._create_right_panel(content_frame)
        
        # 하단: 액션 버튼들
        self._create_action_panel(main_container)

    def _create_header(self, parent):
        """헤더 섹션 생성"""
        header_frame = ctk.CTkFrame(parent, corner_radius=15, height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # 제목
        title_label = ctk.CTkLabel(
            header_content,
            text="🔧 " + self.texts.get("retranslation_window_title", "Retranslation Tool"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # 설명
        desc_label = ctk.CTkLabel(
            header_content,
            text=self.texts.get("retranslation_window_description", "Detect and retranslate untranslated text segments"),
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        desc_label.pack(anchor="w", pady=(5, 0))
        
        # 통계
        self.stats_label = ctk.CTkLabel(
            header_content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.stats_label.pack(anchor="w", pady=(5, 0))

    import re

    def _is_paradox_tag(self, text):
        """
        Paradox 게임의 복합적인 태그 및 포맷팅 코드인지 확인합니다.
        
        접근 방식:
        1. 문자열에서 알려진 모든 태그 패턴을 찾아 제거합니다.
        2. 태그 제거 후 남은 문자열에서 공백, 특수기호 등 번역 불필요한 요소를 제거합니다.
        3. 최종적으로 번역해야 할 알파벳 문자가 남아있는지 확인합니다.
        - 아무것도 남지 않거나, 숫자/기호만 남았다면 -> 태그로 간주 (True)
        - 알파벳이 남아있다면 -> 번역 대상 텍스트가 포함된 것으로 간주 (False)
        """
        if not text:
            return True
        
        # 원본 문자열 복사
        processed_text = text
        
        # 1. 제거할 태그 패턴 목록 (더욱 유연하게 수정)
        #    [any thing], $any thing$, #any thing# or #any thing!, 등
        tag_patterns = [
            r'\[[^\]]*\]',      # 대괄호 [...] 안의 모든 내용 (줄바꿈 문자 제외)
            r'\$[^\$]*\$',      # 달러 기호 $...$ 안의 모든 내용
            r'#[^#\!]*[#!]',    # 해시 기호 #...# 또는 #...! 안의 모든 내용
            r'£[^£]*£',        # £...£ 안의 모든 내용
            r'@[^!]*!',         # @...! 안의 모든 내용
            r'§[\w!]',          # 색상 코드 등 (예: §Y, §!)
        ]
        
        # 2. 모든 태그 패턴을 문자열에서 제거
        for pattern in tag_patterns:
            processed_text = re.sub(pattern, '', processed_text)
            
        # 3. 태그 제거 후, 남은 문자열에 번역이 필요한 '알파벳'이 있는지 확인
        #    공백, 줄바꿈, 숫자, '+' 같은 기호는 무시합니다.
        if re.search(r'[a-zA-Z]', processed_text):
            # 번역해야 할 영어 알파벳이 남아있다면, 순수 태그가 아님
            return False
        else:
            # 알파벳 없이 공백, 숫자, 기호만 남았거나 아무것도 남지 않았다면, 태그로 간주
            return True

    def _create_left_panel(self, parent):
        """좌측 패널 - 파일 목록"""
        left_panel = ctk.CTkFrame(parent, corner_radius=10, width=400)
        left_panel.pack(side="left", fill="y", padx=(15, 10), pady=15)
        left_panel.pack_propagate(False)
        
        # 패널 제목
        panel_title = ctk.CTkLabel(
            left_panel,
            text="📁 " + self.texts.get("retranslation_file_list", "Translated Files"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        panel_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 스캔 버튼
        self.scan_button = ctk.CTkButton(
            left_panel,
            text="🔍 " + self.texts.get("retranslation_scan_button", "Scan for Untranslated Text"),
            command=self.start_scanning,
            height=35,
            corner_radius=8
        )
        self.scan_button.pack(fill="x", padx=15, pady=(0, 10))
        
        # 파일 리스트박스
        listbox_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        listbox_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 스크롤바
        scrollbar = ctk.CTkScrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
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
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.configure(command=self.file_listbox.yview)
        
        # 리스트박스 이벤트
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)

    def _create_right_panel(self, parent):
        """우측 패널 - 미번역 항목 상세"""
        right_panel = ctk.CTkFrame(parent, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 15), pady=15)
        
        # 패널 제목
        panel_title = ctk.CTkLabel(
            right_panel,
            text="📝 " + self.texts.get("retranslation_untranslated_items", "Untranslated Items"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        panel_title.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 선택 도구
        tools_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        tools_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.select_all_button = ctk.CTkButton(
            tools_frame,
            text=self.texts.get("retranslation_select_all", "Select All"),
            command=self._select_all_items,
            width=100,
            height=28
        )
        self.select_all_button.pack(side="left", padx=(0, 5))
        
        self.deselect_all_button = ctk.CTkButton(
            tools_frame,
            text=self.texts.get("retranslation_deselect_all", "Deselect All"),
            command=self._deselect_all_items,
            width=100,
            height=28
        )
        self.deselect_all_button.pack(side="left", padx=5)
        
        self.selected_count_label = ctk.CTkLabel(
            tools_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.selected_count_label.pack(side="right", padx=(10, 0))
        
        # 미번역 항목 표시 영역
        self.items_frame = ctk.CTkScrollableFrame(
            right_panel,
            corner_radius=8,
            label_text="",
            label_font=ctk.CTkFont(size=12)
        )
        self.items_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 진행률 표시
        self.progress_frame = ctk.CTkFrame(right_panel, height=30)
        self.progress_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.progress_frame.pack_propagate(False)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack(side="left", padx=(10, 0))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            mode='determinate',
            height=10,
            corner_radius=5
        )
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(10, 10))
        self.progress_bar.set(0)

    def _create_action_panel(self, parent):
        """하단 액션 패널"""
        action_frame = ctk.CTkFrame(parent, corner_radius=15, height=70)
        action_frame.pack(fill="x", pady=(15, 0))
        action_frame.pack_propagate(False)
        
        action_content = ctk.CTkFrame(action_frame, fg_color="transparent")
        action_content.pack(expand=True, fill="both", padx=20, pady=15)
        
        # 상태 표시
        self.status_label = ctk.CTkLabel(
            action_content,
            text=self.texts.get("retranslation_status_ready", "Ready to scan"),
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.status_label.pack(side="left")
        
        # 버튼들
        button_frame = ctk.CTkFrame(action_content, fg_color="transparent")
        button_frame.pack(side="right")
        
        self.retranslate_button = ctk.CTkButton(
            button_frame,
            text="🔄 " + self.texts.get("retranslation_retranslate_button", "Retranslate Selected"),
            command=self.start_retranslation,
            state="disabled",
            width=150,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.retranslate_button.pack(side="right", padx=(10, 0))
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text=self.texts.get("stop_button", "Stop"),
            command=self.stop_process,
            state="disabled",
            width=100,
            height=40,
            corner_radius=8,
            fg_color=self.colors['accent_red']
        )
        self.stop_button.pack(side="right")

    def start_scanning(self):
        """미번역 항목 스캔 시작"""
        if self.is_scanning or self.is_retranslating:
            return
            
        output_dir = self.master_app.output_folder_var.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror(
                self.texts.get("error_title", "Error"),
                self.texts.get("retranslation_no_output_folder", "Output folder not set")
            )
            return
        
        self.is_scanning = True
        self.stop_event.clear()
        self.scan_button.configure(state="disabled")
        self.retranslate_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text=self.texts.get("retranslation_scanning", "Scanning files..."))
        
        # 스캔 스레드 시작
        scan_thread = threading.Thread(target=self._scan_worker, daemon=True)
        scan_thread.start()

    def _scan_worker(self):
        """백그라운드 스캔 작업"""
        try:
            output_dir = self.master_app.output_folder_var.get()
            input_dir = self.master_app.input_folder_var.get()
            source_lang = self.master_app.source_lang_for_api_var.get()
            target_lang = self.master_app.target_lang_for_api_var.get()
            
            # 언어 코드 가져오기
            source_lang_code = self.translator_engine.get_language_code(source_lang).lower()
            target_lang_code = self.translator_engine.get_language_code(target_lang).lower()
            
            self.untranslated_items.clear()
            self.file_listbox.delete(0, tk.END)
            
            # 번역된 파일들 스캔
            translated_files = []
            for root, _, files in os.walk(output_dir):
                if self.stop_event.is_set():
                    break
                for file in files:
                    if file.lower().endswith(('.yml', '.yaml')):
                        translated_files.append(os.path.join(root, file))
            
            total_files = len(translated_files)
            self.after(0, lambda: self.stats_label.configure(
                text=f"📊 {self.texts.get('retranslation_found_files', 'Found {0} translated files').format(total_files)}"
            ))
            
            # 각 파일 검사
            for idx, trans_file in enumerate(translated_files):
                if self.stop_event.is_set():
                    break
                    
                # 진행률 업데이트
                progress = (idx + 1) / total_files
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                self.after(0, lambda i=idx+1, t=total_files: self.progress_label.configure(
                    text=f"{i}/{t}"
                ))
                
                # 원본 파일 찾기
                rel_path = os.path.relpath(trans_file, output_dir)
                base_name = os.path.basename(trans_file)
                
                # 언어 코드 교체하여 원본 파일 경로 추정
                original_base = base_name.replace(f"l_{target_lang_code}", f"l_{source_lang_code}")
                original_file = os.path.join(input_dir, os.path.dirname(rel_path), original_base)
                
                if not os.path.exists(original_file):
                    # 다른 방법으로 원본 파일 찾기
                    original_file = self._find_original_file(trans_file, input_dir, output_dir, source_lang_code, target_lang_code)
                
                if original_file and os.path.exists(original_file):
                    # 파일 내용 검사
                    untranslated = self._check_file_for_untranslated(original_file, trans_file, source_lang)
                    
                    if untranslated:
                        file_info = {
                            'translated_file': trans_file,
                            'original_file': original_file,
                            'display_name': os.path.basename(trans_file),
                            'untranslated_count': len(untranslated),
                            'untranslated_items': untranslated
                        }
                        self.untranslated_items.append(file_info)
                        
                        # UI 업데이트
                        display_text = f"{file_info['display_name']} ({file_info['untranslated_count']} items)"
                        self.after(0, lambda t=display_text: self.file_listbox.insert(tk.END, t))
            
            # 스캔 완료
            total_untranslated = sum(f['untranslated_count'] for f in self.untranslated_items)
            self.after(0, lambda: self._scan_complete(total_untranslated))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                self.texts.get("error_title", "Error"),
                f"Scan error: {str(e)}"
            ))
        finally:
            self.is_scanning = False
            self.after(0, self._update_ui_state)

    def _find_original_file(self, trans_file, input_dir, output_dir, source_lang_code, target_lang_code):
        """원본 파일 찾기"""
        # 여러 방법으로 원본 파일 찾기 시도
        rel_path = os.path.relpath(trans_file, output_dir)
        base_name = os.path.basename(trans_file)
        dir_path = os.path.dirname(rel_path)
        
        # 1. 언어 코드만 교체
        test_name = base_name.replace(f"l_{target_lang_code}", f"l_{source_lang_code}")
        test_path = os.path.join(input_dir, dir_path, test_name)
        if os.path.exists(test_path):
            return test_path
        
        # 2. l_english로 시도
        if source_lang_code == "english":
            test_name = base_name.replace(f"l_{target_lang_code}", "l_english")
            test_path = os.path.join(input_dir, dir_path, test_name)
            if os.path.exists(test_path):
                return test_path
        
        return None

    def _check_file_for_untranslated(self, original_file, translated_file, source_lang):
        """파일에서 미번역 항목 검사"""
        untranslated = []
        
        try:
            # 파일 읽기
            with codecs.open(original_file, 'r', encoding='utf-8-sig') as fo:
                original_lines = fo.readlines()
            with codecs.open(translated_file, 'r', encoding='utf-8-sig') as ft:
                translated_lines = ft.readlines()
            
            # 키-값 쌍 추출
            original_dict = {}
            translated_dict = {}
            
            key_value_pattern = r'^(\s*)([^:]+):\d*\s*"([^"]*)"'
            
            for idx, line in enumerate(original_lines):
                match = re.match(key_value_pattern, line)
                if match:
                    key = match.group(2).strip()
                    value = match.group(3)
                    original_dict[key] = {'value': value, 'line': idx, 'full_line': line}
            
            for idx, line in enumerate(translated_lines):
                match = re.match(key_value_pattern, line)
                if match:
                    key = match.group(2).strip()
                    value = match.group(3)
                    translated_dict[key] = {'value': value, 'line': idx, 'full_line': line}
            
            # 미번역 항목 찾기
            for key, orig_data in original_dict.items():
                # 번역 파일에 해당 키가 있는지 먼저 확인
                if key in translated_dict:
                    trans_data = translated_dict[key]
                    
                    # --- [수정된 핵심 로직] ---
                    # 원본 또는 번역본 값이 Paradox 태그인 경우, 검사에서 완전히 제외
                    if self._is_paradox_tag(orig_data['value']) or self._is_paradox_tag(trans_data['value']):
                        continue  # 이 키에 대한 비교를 중단하고 다음 키로 넘어감
                    # --- [수정 끝] ---
                    
                    # 이제 Paradox 태그가 아닌 항목들만 아래 로직으로 비교합니다.
                    
                    # 1. 완전히 동일한 경우 (미번역으로 간주)
                    if orig_data['value'] == trans_data['value']:
                        untranslated.append({
                            'key': key,
                            'original_value': orig_data['value'],
                            'translated_value': trans_data['value'],
                            'original_line': orig_data['line'],
                            'translated_line': trans_data['line'],
                            'reason': 'identical'
                        })
                    
                    # 2. 영어 패턴 검출 (원본이 영어인 경우, 미번역으로 간주)
                    elif source_lang.lower() == "english" and self._contains_english_pattern(trans_data['value']):
                        untranslated.append({
                            'key': key,
                            'original_value': orig_data['value'],
                            'translated_value': trans_data['value'],
                            'original_line': orig_data['line'],
                            'translated_line': trans_data['line'],
                            'reason': 'english_pattern'
                        })
            
        except Exception as e:
            print(f"Error checking file {translated_file}: {e}")
        
        return untranslated

    def _contains_english_pattern(self, text):
        """영어 패턴 포함 여부 확인"""
        # 3글자 이상의 영어 단어가 연속으로 나타나는 패턴
        pattern = r'\b[a-zA-Z]{3,}(?:\s+[a-zA-Z]{2,})+\b'
        if re.search(pattern, text):
            # 텍스트의 50% 이상이 영어인지 확인
            words = text.split()
            english_words = [w for w in words if re.match(r'^[a-zA-Z]+$', w)]
            if len(english_words) > len(words) * 0.5:
                return True
        return False

    def _scan_complete(self, total_untranslated):
        """스캔 완료 처리"""
        self.progress_bar.set(1.0)
        self.progress_label.configure(text=self.texts.get("retranslation_scan_complete", "Complete"))
        
        if total_untranslated > 0:
            self.status_label.configure(
                text=f"✅ {self.texts.get('retranslation_found_untranslated', 'Found {0} untranslated items').format(total_untranslated)}"
            )
            self.retranslate_button.configure(state="normal")
        else:
            self.status_label.configure(
                text="✅ " + self.texts.get("retranslation_no_untranslated", "No untranslated items found")
            )
        
        self._update_ui_state()

    def _on_file_select(self, event):
        """파일 선택 이벤트"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        # 기존 항목들 제거
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        
        # 선택된 파일의 미번역 항목 표시
        file_info = self.untranslated_items[selection[0]]
        
        for item in file_info['untranslated_items']:
            self._create_item_widget(item, file_info)
        
        self._update_selected_count()

    def _create_item_widget(self, item, file_info):
        """미번역 항목 위젯 생성"""
        # 항목 프레임
        item_frame = ctk.CTkFrame(self.items_frame, corner_radius=8)
        item_frame.pack(fill="x", padx=5, pady=5)
        
        # 체크박스
        var = tk.BooleanVar(value=True)
        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            variable=var,
            width=20,
            command=self._update_selected_count
        )
        checkbox.pack(side="left", padx=(10, 5), pady=10)
        
        # 콘텐츠
        content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)
        
        # 키 표시
        key_label = ctk.CTkLabel(
            content_frame,
            text=f"🔑 {item['key']}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        key_label.pack(fill="x")
        
        # 원본 텍스트
        orig_label = ctk.CTkLabel(
            content_frame,
            text=f"📄 {self.texts.get('retranslation_original', 'Original')}: {item['original_value'][:10000]}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary'],
            anchor="w",
            wraplength=600
        )
        orig_label.pack(fill="x", pady=(5, 0))
        
        # 현재 번역
        trans_label = ctk.CTkLabel(
            content_frame,
            text=f"🔄 {self.texts.get('retranslation_current', 'Current')}: {item['translated_value'][:10000]}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['accent_red'],
            anchor="w",
            wraplength=600
        )
        trans_label.pack(fill="x", pady=(5, 0))
        
        # 이유
        reason_text = {
            'identical': self.texts.get('retranslation_reason_identical', 'Identical to original'),
            'english_pattern': self.texts.get('retranslation_reason_english', 'Contains English text')
        }.get(item['reason'], item['reason'])
        
        reason_label = ctk.CTkLabel(
            content_frame,
            text=f"⚠️ {reason_text}",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['accent_orange'],
            anchor="w"
        )
        reason_label.pack(fill="x", pady=(5, 0))
        
        # 데이터 저장
        checkbox.item_data = item
        checkbox.file_info = file_info

    def _update_selected_count(self):
        """선택된 항목 수 업데이트"""
        count = 0
        self.selected_items_for_retranslation.clear()
        
        for widget in self.items_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox) and child.get():
                        count += 1
                        self.selected_items_for_retranslation.append({
                            'item': child.item_data,
                            'file_info': child.file_info
                        })
        
        self.selected_count_label.configure(
            text=f"{count} {self.texts.get('retranslation_items_selected', 'items selected')}"
        )
        
        # 재번역 버튼 상태 업데이트
        if count > 0 and not self.is_retranslating:
            self.retranslate_button.configure(state="normal")
        else:
            self.retranslate_button.configure(state="disabled")

    def _select_all_items(self):
        """모든 항목 선택"""
        for widget in self.items_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.select()
        self._update_selected_count()

    def _deselect_all_items(self):
        """모든 항목 선택 해제"""
        for widget in self.items_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.deselect()
        self._update_selected_count()

    def start_retranslation(self):
        """재번역 시작"""
        if not self.selected_items_for_retranslation:
            return
        
        # API 설정 확인
        api_key = self.master_app.api_key_var.get().strip()
        model_name = self.master_app.model_name_var.get()
        
        if not api_key or not model_name:
            messagebox.showerror(
                self.texts.get("error_title", "Error"),
                self.texts.get("retranslation_api_error", "API key and model must be configured")
            )
            return
        
        self.is_retranslating = True
        self.stop_event.clear()
        self.retranslate_button.configure(state="disabled")
        self.scan_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text=self.texts.get("retranslation_in_progress", "Retranslating..."))
        
        # 재번역 스레드 시작
        retranslate_thread = threading.Thread(target=self._retranslate_worker, daemon=True)
        retranslate_thread.start()

    def _retranslate_worker(self):
        """백그라운드 재번역 작업"""
        try:
            # API 초기화
            api_key = self.master_app.api_key_var.get().strip()
            model_name = self.master_app.model_name_var.get()
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # 프롬프트 및 용어집 가져오기
            prompt_template = self.master_app.prompt_glossary_panel.get_prompt_text()
            glossary = self.master_app._get_combined_glossary_content()
            
            source_lang = self.master_app.source_lang_for_api_var.get()
            target_lang = self.master_app.target_lang_for_api_var.get()
            
            # 메인 창의 상세 설정 가져오기
            batch_size = self.master_app.batch_size_var.get()
            max_tokens = self.master_app.max_tokens_var.get()
            temperature = self.master_app.temperature_var.get()
            delay_between_batches = self.master_app.delay_between_batches_var.get()
            
            # 파일별로 그룹화
            files_to_update = {}
            for selected in self.selected_items_for_retranslation:
                file_path = selected['file_info']['translated_file']
                if file_path not in files_to_update:
                    files_to_update[file_path] = []
                files_to_update[file_path].append(selected['item'])
            
            total_items = len(self.selected_items_for_retranslation)
            processed = 0
            
            # 각 파일 처리
            for file_path, items in files_to_update.items():
                if self.stop_event.is_set():
                    break
                
                # 파일 읽기
                with codecs.open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                # ── 배치 단위로 묶어서 처리 ──
                if len(items) > batch_size:
                    # batch_size 단위로 나누어서 처리
                    for i in range(0, len(items), batch_size):
                        batch_items = items[i:i+batch_size]
                        
                        # ── 배치 내에서 각 항목 재번역 ──
                        for item in batch_items:
                            if self.stop_event.is_set():
                                break
                            
                            try:
                                # 재번역 수행
                                new_translation = self._retranslate_single_item(
                                    item, model, prompt_template, glossary, source_lang, target_lang
                                )
                                
                                if new_translation:
                                    # 파일에서 해당 라인 업데이트
                                    line_idx = item['translated_line']
                                    if line_idx < len(lines):
                                        old_line = lines[line_idx]
                                        match = re.match(r'^(\s*[^:]+:\d*\s*)"[^"]*"(.*)', old_line)
                                        if match:
                                            new_line = f'{match.group(1)}"{new_translation}"{match.group(2)}'
                                            if not new_line.endswith('\n'):
                                                new_line += '\n'
                                            lines[line_idx] = new_line
                            
                            except Exception as e:
                                print(f"Error retranslating item: {e}")
                            
                            # 진행률 업데이트
                            processed += 1
                            progress = processed / total_items
                            self.after(0, lambda p=progress: self.progress_bar.set(p))
                            self.after(0, lambda pr=processed, t=total_items: self.progress_label.configure(
                                text=f"{pr}/{t}"
                            ))
                        
                        # ── 배치 간 대기 ──
                        if i + batch_size < len(items) and not self.stop_event.is_set():
                            time.sleep(delay_between_batches)
                
                else:
                    # items 개수가 batch_size 이하라면 한 번에 처리
                    for item in items:
                        if self.stop_event.is_set():
                            break
                        
                        try:
                            # 재번역 수행
                            new_translation = self._retranslate_single_item(
                                item, model, prompt_template, glossary, source_lang, target_lang
                            )
                            
                            if new_translation:
                                # 파일에서 해당 라인 업데이트
                                line_idx = item['translated_line']
                                if line_idx < len(lines):
                                    old_line = lines[line_idx]
                                    match = re.match(r'^(\s*[^:]+:\d*\s*)"[^"]*"(.*)', old_line)
                                    if match:
                                        new_line = f'{match.group(1)}"{new_translation}"{match.group(2)}'
                                        if not new_line.endswith('\n'):
                                            new_line += '\n'
                                        lines[line_idx] = new_line
                            
                        except Exception as e:
                            print(f"Error retranslating item: {e}")
                        
                        # 진행률 업데이트
                        processed += 1
                        progress = processed / total_items
                        self.after(0, lambda p=progress: self.progress_bar.set(p))
                        self.after(0, lambda pr=processed, t=total_items: self.progress_label.configure(
                            text=f"{pr}/{t}"
                        ))
                
                # 파일 저장
                if not self.stop_event.is_set():
                    with codecs.open(file_path, 'w', encoding='utf-8-sig') as f:
                        f.writelines(lines)
            
            # 완료
            self.after(0, self._retranslation_complete)

            
            

        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                self.texts.get("error_title", "Error"),
                f"Retranslation error: {str(e)}"
            ))
        finally:
            self.is_retranslating = False
            self.after(0, self._update_ui_state)

    def _retranslate_single_item(self, item, model, prompt_template, glossary, source_lang, target_lang):
        """단일 항목 재번역"""
        try:
            # 배치 텍스트 준비
            batch_text = f'{item["key"]}:0 "{item["original_value"]}"'
            
            # 프롬프트 생성
            prompt = prompt_template.format(
                source_lang_for_prompt=source_lang,
                target_lang_for_prompt=target_lang,
                glossary_section=glossary,
                batch_text=batch_text
            )
            
            # API 호출
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.master_app.temperature_var.get(),
                    max_output_tokens=self.master_app.max_tokens_var.get()
                )
            )
            
            if response.text:
                # 응답에서 번역된 값 추출
                match = re.search(r':\d*\s*"([^"]*)"', response.text)
                if match:
                    return match.group(1)
            
        except Exception as e:
            print(f"Error in retranslation API call: {e}")
        
        return None

    def _retranslation_complete(self):
        """재번역 완료 처리"""
        self.progress_bar.set(1.0)
        self.status_label.configure(
            text="✅ " + self.texts.get("retranslation_complete", "Retranslation completed")
        )
        
        # 다시 스캔 권장
        response = messagebox.askyesno(
            self.texts.get("info_title", "Information"),
            self.texts.get("retranslation_rescan_prompt", "Retranslation completed. Would you like to scan again?")
        )
        
        if response:
            self.start_scanning()

    def stop_process(self):
        """진행 중인 작업 중지"""
        self.stop_event.set()
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text=self.texts.get("retranslation_stopping", "Stopping..."))

    def _update_ui_state(self):
        """UI 상태 업데이트"""
        if not self.is_scanning and not self.is_retranslating:
            self.scan_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            if self.selected_items_for_retranslation:
                self.retranslate_button.configure(state="normal")

    def update_language_texts(self, new_texts):
        """언어 텍스트 업데이트"""
        self.texts = new_texts
        self.title(self.texts.get("retranslation_window_title", "Retranslation Tool"))
        
        # 버튼 텍스트 업데이트
        self.scan_button.configure(text="🔍 " + self.texts.get("retranslation_scan_button", "Scan for Untranslated Text"))
        self.retranslate_button.configure(text="🔄 " + self.texts.get("retranslation_retranslate_button", "Retranslate Selected"))
        self.stop_button.configure(text=self.texts.get("stop_button", "Stop"))
        self.select_all_button.configure(text=self.texts.get("retranslation_select_all", "Select All"))
        self.deselect_all_button.configure(text=self.texts.get("retranslation_deselect_all", "Deselect All"))

    def on_closing(self):
        """창 닫기"""
        if self.is_scanning or self.is_retranslating:
            self.stop_event.set()
        self.destroy()