# translator_project/translator_app/gui/panels/control_panel.py

import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
from ...utils.localization import get_text


class ControlPanel(ctk.CTkFrame):
    """
    번역 시작/중지, 도구, 새로고침 버튼과 진행률 표시줄을 포함하는 메인 컨트롤 패널.
    향상된 진행 상황 표시 기능 포함.
    """
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color="transparent")
        self.main_app = main_app
        
        # 진행 상황 추적 변수
        self.total_files = 0
        self.completed_files = 0
        self.start_time = None
        self.is_translating = False
        
        # 메인 그리드 설정
        self.grid_rowconfigure(0, weight=0)  # 상단 버튼 행
        self.grid_rowconfigure(1, weight=0)  # 진행률 정보 행
        self.grid_rowconfigure(2, weight=0)  # 진행률 바 행
        self.grid_columnconfigure(0, weight=1)
        
        # 위젯 생성
        self._create_button_row()
        self._create_progress_info_row()
        self._create_progress_bar_row()
        
    def _create_button_row(self):
        """상단 버튼 행 생성"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # 그리드 설정
        button_frame.grid_columnconfigure(0, weight=0)  # 시작 버튼
        button_frame.grid_columnconfigure(1, weight=0)  # 중지 버튼
        button_frame.grid_columnconfigure(2, weight=1)  # 빈 공간
        button_frame.grid_columnconfigure(3, weight=0)  # 도구 버튼
        button_frame.grid_columnconfigure(4, weight=0)  # 새로고침 버튼
        
        # 1. 프리미엄 시작 버튼
        self.start_button = ctk.CTkButton(
            button_frame,
            text="🚀 " + get_text("translate_button", "Start Translation"),
            command=self.start_translation_clicked,
            width=160,
            height=40,
            corner_radius=14,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#10B981", "#059669"),
            hover_color=("#059669", "#047857"),
            border_width=0
        )
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        # 2. 프리미엄 중지 버튼
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="⏹️ " + get_text("stop_button", "Stop"),
            command=self.stop_translation_clicked,
            width=120,
            height=40,
            corner_radius=14,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#EF4444", "#DC2626"),
            hover_color=("#DC2626", "#B91C1C"),
            border_width=0,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5, sticky="w")
        
        # 3. 프리미엄 도구 메뉴 버튼
        self.tools_menu_button = ctk.CTkButton(
            button_frame,
            text="🛠️ " + get_text("tools_menu", "Tools"),
            command=self.main_app.show_tools_menu,
            width=120,
            height=40,
            corner_radius=14,
            font=ctk.CTkFont(size=13, weight="normal"),
            fg_color=("#6366F1", "#4F46E5"),
            hover_color=("#4F46E5", "#4338CA"),
            border_width=0
        )
        self.tools_menu_button.grid(row=0, column=3, padx=5, sticky="e")
        
        # main_app에 참조 저장
        self.main_app.tools_menu_button = self.tools_menu_button
        
        # 4. 프리미엄 새로고침 버튼
        self.refresh_button = ctk.CTkButton(
            button_frame,
            text="🔄",
            width=45,
            height=40,
            corner_radius=14,
            command=self.refresh_ui,
            font=ctk.CTkFont(size=16),
            fg_color=("#8B5CF6", "#7C3AED"),
            hover_color=("#7C3AED", "#6D28D9"),
            border_width=0
        )
        self.refresh_button.grid(row=0, column=4, padx=(5, 0), sticky="e")
        
    def _create_progress_info_row(self):
        """진행률 정보 행 생성"""
        info_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(5, 2))
        info_frame.grid_propagate(False)
        
        # 좌측: 파일 카운터
        self.file_counter_label = ctk.CTkLabel(
            info_frame,
            text=self._get_file_counter_text(),
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        self.file_counter_label.pack(side="left", padx=(5, 0))
        
        # 중앙: 진행률 퍼센트
        self.progress_percent_label = ctk.CTkLabel(
            info_frame,
            text="0%",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1976D2", "#64B5F6")
        )
        self.progress_percent_label.pack(side="left", expand=True)
        
        # 우측: 예상 남은 시간
        self.eta_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=12),
            anchor="e",
            text_color=("gray50", "gray60")
        )
        self.eta_label.pack(side="right", padx=(0, 5))
        
        # 상태 메시지
        self.status_message_label = ctk.CTkLabel(
            info_frame,
            text=get_text("status_waiting", "Ready"),
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        self.status_message_label.pack(side="right", padx=(0, 20))
        
    def _create_progress_bar_row(self):
        """진행률 바 행 생성"""
        progress_container = ctk.CTkFrame(self, fg_color="transparent")
        progress_container.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        
        # 프리미엄 진행률 바
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            height=24,
            corner_radius=12,
            progress_color=("#10B981", "#34D399"),
            fg_color=("#E5E7EB", "#374151"),
            border_width=1,
            border_color=("#D1D5DB", "#4B5563")
        )
        self.progress_bar.pack(fill="x", padx=8)
        self.progress_bar.set(0)
        
    def _get_file_counter_text(self):
        """파일 카운터 텍스트 생성"""
        if self.total_files > 0:
            return get_text(
                "file_progress_format", 
                "Files: {0}/{1}"
            ).format(self.completed_files, self.total_files)
        else:
            return get_text("files_label", "Files: -/-")
    
    def _calculate_eta(self):
        """예상 남은 시간 계산"""
        if not self.is_translating or not self.start_time or self.completed_files == 0:
            return ""
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed == 0:
            return ""
        
        files_per_second = self.completed_files / elapsed
        remaining_files = self.total_files - self.completed_files
        
        if files_per_second > 0:
            eta_seconds = remaining_files / files_per_second
            
            if eta_seconds < 60:
                return get_text("eta_seconds", "~{0}s left").format(int(eta_seconds))
            elif eta_seconds < 3600:
                minutes = int(eta_seconds / 60)
                return get_text("eta_minutes", "~{0}m left").format(minutes)
            else:
                hours = int(eta_seconds / 3600)
                minutes = int((eta_seconds % 3600) / 60)
                return get_text("eta_hours", "~{0}h {1}m left").format(hours, minutes)
        
        return ""
    
    def update_file_progress(self, completed, total):
        """파일 진행 상황 업데이트"""
        self.completed_files = completed
        self.total_files = total
        
        # 파일 카운터 업데이트
        self.file_counter_label.configure(text=self._get_file_counter_text())
        
        # 진행률 계산 및 업데이트
        if total > 0:
            progress = completed / total
            self.set_progress(progress)
            
            # 퍼센트 표시
            percent = int(progress * 100)
            self.progress_percent_label.configure(text=f"{percent}%")
            
            # 진행률에 따른 색상 변경
            if percent < 30:
                color = ("#D32F2F", "#E57373")  # 빨간색
            elif percent < 70:
                color = ("#F57C00", "#FFB74D")  # 주황색
            else:
                color = ("#2E7D32", "#66BB6A")  # 녹색
            
            self.progress_bar.configure(progress_color=color)
            self.progress_percent_label.configure(text_color=color)
        
        # ETA 업데이트
        eta_text = self._calculate_eta()
        self.eta_label.configure(text=eta_text)
    
    def set_translation_status(self, is_active, status_message=None):
        """번역 상태 설정"""
        self.is_translating = is_active
        
        if is_active:
            if not self.start_time:
                self.start_time = datetime.now()
            
            # 버튼 상태
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
            # 진행 중 스타일
            self.start_button.configure(
                fg_color=("gray70", "gray30"),
                text="⏸ " + get_text("translating", "Translating...")
            )
            
            if status_message:
                self.status_message_label.configure(
                    text=status_message,
                    text_color=("#1976D2", "#64B5F6")
                )
        else:
            # 버튼 상태
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            # 일반 스타일로 복원
            self.start_button.configure(
                fg_color="#2E7D32",
                text="▶ " + get_text("translate_button", "Start Translation")
            )
            
            # 완료 메시지
            if self.completed_files > 0 and self.completed_files == self.total_files:
                self.status_message_label.configure(
                    text=get_text("translation_completed", "Completed!"),
                    text_color=("#2E7D32", "#66BB6A")
                )
            else:
                self.status_message_label.configure(
                    text=get_text("status_waiting", "Ready"),
                    text_color=("gray50", "gray60")
                )
            
            # 시작 시간 리셋
            if self.completed_files == 0 or self.completed_files == self.total_files:
                self.start_time = None
    
    def reset_progress(self):
        """진행 상황 초기화"""
        self.total_files = 0
        self.completed_files = 0
        self.start_time = None
        self.is_translating = False
        
        self.progress_bar.set(0)
        self.progress_percent_label.configure(text="0%")
        self.file_counter_label.configure(text=self._get_file_counter_text())
        self.eta_label.configure(text="")
        self.status_message_label.configure(
            text=get_text("status_waiting", "Ready"),
            text_color=("gray50", "gray60")
        )
    
    def refresh_ui(self):
        """UI 새로고침"""
        self.main_app.refresh_ui()
    
    def start_translation_clicked(self):
        """'번역 시작' 버튼 클릭 시 실행되는 로직"""
        self.reset_progress()
        self.main_app.start_translation()
    
    def stop_translation_clicked(self):
        """'중지' 버튼 클릭 시 실행되는 로직"""
        self.main_app.stop_translation()
    
    def update_language(self):
        """UI 언어 변경 시 컨트롤 패널의 위젯 텍스트를 업데이트합니다."""
        if not self.is_translating:
            self.start_button.configure(text="▶ " + get_text("translate_button", "Start Translation"))
        self.stop_button.configure(text="⏹ " + get_text("stop_button", "Stop"))
        self.tools_menu_button.configure(text="🛠 " + get_text("tools_menu", "Tools"))
        self.file_counter_label.configure(text=self._get_file_counter_text())
        
        # 상태 메시지도 업데이트
        if not self.is_translating:
            self.status_message_label.configure(text=get_text("status_waiting", "Ready"))
    
    def set_translate_button_state(self, state):
        """'Start Translation' 버튼의 상태를 변경합니다."""
        if state in ['normal', 'disabled']:
            self.start_button.configure(state=state)
            
            # 번역 중인지 확인하여 상태 업데이트
            if state == 'disabled':
                self.set_translation_status(True)
            else:
                self.set_translation_status(False)
    
    def set_stop_button_state(self, state):
        """'Stop' 버튼의 상태를 변경합니다."""
        if state in ['normal', 'disabled']:
            self.stop_button.configure(state=state)
    
    def set_progress(self, value):
        """ProgressBar의 값을 업데이트합니다."""
        self.progress_bar.set(float(value))
        
        # 퍼센트 텍스트도 업데이트
        percent = int(value * 100)
        self.progress_percent_label.configure(text=f"{percent}%")
        
        # 파일 진행 상황 추정 (정확한 값이 없을 때)
        if self.total_files > 0:
            estimated_completed = int(value * self.total_files)
            if estimated_completed != self.completed_files:
                self.completed_files = estimated_completed
                self.file_counter_label.configure(text=self._get_file_counter_text())
                self.eta_label.configure(text=self._calculate_eta())