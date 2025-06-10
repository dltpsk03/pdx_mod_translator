# translator_project/translator_app/gui/windows/translation_dashboard.py

import customtkinter as ctk
import os
import sys
import json
import subprocess
import threading
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog
import tkinter as tk
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple, Any
import time

# Localization helper (fallback if import fails)
try:
    from ...utils.localization import get_text
except:
    def get_text(key: str, default: str) -> str:
        return default


class StatisticsData:
    """통계 데이터 관리 클래스"""
    def __init__(self):
        self.all_stats: List[Dict[str, Any]] = []
        self.session_start_time: datetime = datetime.now()
        self._lock = threading.Lock()
        
    def add_stat(self, stat_entry: Dict[str, Any]) -> bool:
        """통계 추가 (중복 체크 포함)"""
        with self._lock:
            # 중복 체크
            for existing in self.all_stats:
                if existing['file_path'] == stat_entry['file_path']:
                    # 같은 파일이면 업데이트
                    existing.update(stat_entry)
                    return False
            
            self.all_stats.append(stat_entry)
            return True
    
    def get_stats(self) -> List[Dict[str, Any]]:
        """통계 리스트 반환 (스레드 안전)"""
        with self._lock:
            return self.all_stats.copy()
    
    def clear(self):
        """통계 초기화"""
        with self._lock:
            self.all_stats.clear()
            self.session_start_time = datetime.now()
    
    def get_summary(self) -> Dict[str, Any]:
        """요약 통계 계산"""
        with self._lock:
            if not self.all_stats:
                return {
                    'total_files': 0,
                    'avg_quality': 0,
                    'total_lines': 0,
                    'total_time': 0,
                    'lines_per_minute': 0
                }
            
            total_files = len(self.all_stats)
            
            # None 값 처리하여 안전하게 계산
            valid_qualities = [s.get('quality', 0) for s in self.all_stats if s.get('quality') is not None]
            avg_quality = sum(valid_qualities) / len(valid_qualities) if valid_qualities else 0
            
            valid_lines = [s.get('lines', 0) for s in self.all_stats if s.get('lines') is not None]
            total_lines = sum(valid_lines)
            
            valid_times = [s.get('time', 0) for s in self.all_stats if s.get('time') is not None]
            total_time = sum(valid_times)
            
            # 분당 라인 수
            elapsed_minutes = (datetime.now() - self.session_start_time).total_seconds() / 60
            lines_per_minute = total_lines / elapsed_minutes if elapsed_minutes > 0 else 0
            
            return {
                'total_files': total_files,
                'avg_quality': avg_quality,
                'total_lines': total_lines,
                'total_time': total_time,
                'lines_per_minute': lines_per_minute
            }


class FileListItem(ctk.CTkFrame):
    """파일 리스트 아이템 위젯"""
    def __init__(self, parent, stat_entry: Dict[str, Any], on_click_callback=None):
        super().__init__(parent, height=50, corner_radius=8)
        self.stat_entry = stat_entry
        self.on_click_callback = on_click_callback
        
        self.grid_columnconfigure(0, weight=2)  # 파일명
        self.grid_columnconfigure(1, weight=1)  # 상태
        self.grid_columnconfigure(2, weight=1)  # 품질
        self.grid_columnconfigure(3, weight=1)  # 시간
        self.grid_columnconfigure(4, weight=1)  # 라인
        
        # 파일명
        self.filename_label = ctk.CTkLabel(
            self,
            text=stat_entry['filename'],
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.filename_label.grid(row=0, column=0, padx=(15, 5), pady=10, sticky="w")
        
        # 상태
        self.status_label = ctk.CTkLabel(
            self,
            text="✅",
            font=ctk.CTkFont(size=14),
            text_color="green"
        )
        self.status_label.grid(row=0, column=1, padx=5, pady=10)
        
        # 품질
        quality = stat_entry.get('quality', 0) or 0
        quality_color = self._get_quality_color(quality)
        self.quality_label = ctk.CTkLabel(
            self,
            text=f"{quality:.1f}%",
            text_color=quality_color,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.quality_label.grid(row=0, column=2, padx=5, pady=10)
        
        # 시간
        time_value = stat_entry.get('time', 0) or 0
        self.time_label = ctk.CTkLabel(
            self,
            text=f"{time_value:.1f}s",
            font=ctk.CTkFont(size=12)
        )
        self.time_label.grid(row=0, column=3, padx=5, pady=10)
        
        # 라인 수
        lines_value = stat_entry.get('lines', 0) or 0
        self.lines_label = ctk.CTkLabel(
            self,
            text=str(lines_value),
            font=ctk.CTkFont(size=12)
        )
        self.lines_label.grid(row=0, column=4, padx=(5, 15), pady=10)
        
        # 호버 효과
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        for widget in self.winfo_children():
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
            widget.bind("<Button-1>", self._on_click)
    
    def _get_quality_color(self, quality: float) -> str:
        """품질에 따른 색상 반환"""
        if quality >= 90:
            return "#00ff00"  # 밝은 녹색
        elif quality >= 80:
            return "#90EE90"  # 연한 녹색
        elif quality >= 70:
            return "#FFD700"  # 금색
        elif quality >= 60:
            return "#FFA500"  # 주황색
        else:
            return "#FF6B6B"  # 연한 빨간색
    
    def _on_enter(self, event):
        """마우스 호버 시작"""
        self.configure(fg_color=("gray85", "gray25"))
    
    def _on_leave(self, event):
        """마우스 호버 종료"""
        self.configure(fg_color=("gray92", "gray14"))
    
    def _on_click(self, event):
        """클릭 이벤트"""
        if self.on_click_callback:
            self.on_click_callback(self.stat_entry)


class TranslationDashboard(ctk.CTkToplevel):
    """실시간 번역 진행 상황과 통계를 표시하는 대시보드"""
    
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app
        
        # 데이터 관리
        self.stats_data = StatisticsData()
        self.is_translation_active = False
        self.file_items: List[FileListItem] = []
        self.update_job = None
        
        # 필터/정렬 상태
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="newest")
        
        # 창 설정
        self.title(get_text("dashboard_title", "Translation Dashboard"))
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        # 메인 레이아웃 설정
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # UI 구성
        self._setup_ui()
        
        # 기존 통계 로드
        self._load_existing_stats()
        
        # 실시간 업데이트 시작
        self._start_live_updates()
        
        # 창 포커스
        self.lift()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
    
    def _setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        main_container = ctk.CTkFrame(self, corner_radius=0)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # 1. 툴바
        self._create_toolbar(main_container)
        
        # 2. 콘텐츠 영역
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0)  # 좌측 패널
        content_frame.grid_columnconfigure(1, weight=1)  # 우측 패널
        
        # 좌측 패널
        self._create_left_panel(content_frame)
        
        # 우측 패널
        self._create_right_panel(content_frame)
    
    def _create_toolbar(self, parent):
        """상단 툴바 생성"""
        toolbar = ctk.CTkFrame(parent, height=60, corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)
        
        # 제목
        title_label = ctk.CTkLabel(
            toolbar,
            text=get_text("dashboard_title", "Translation Dashboard"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # 버튼 컨테이너
        btn_container = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_container.pack(side="right", padx=20, pady=15)
        
        # 새로고침 버튼
        self.refresh_btn = ctk.CTkButton(
            btn_container,
            text="🔄 " + get_text("refresh", "Refresh"),
            command=self._refresh_display,
            width=110,
            height=32
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        # 내보내기 버튼
        self.export_btn = ctk.CTkButton(
            btn_container,
            text="📥 " + get_text("export", "Export"),
            command=self._export_stats,
            width=110,
            height=32
        )
        self.export_btn.pack(side="left", padx=5)
        
        # 지우기 버튼
        self.clear_btn = ctk.CTkButton(
            btn_container,
            text="🗑️ " + get_text("clear", "Clear"),
            command=self._clear_all,
            width=110,
            height=32,
            fg_color="#DC143C",
            hover_color="#B22222"
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def _create_left_panel(self, parent):
        """좌측 패널 생성"""
        left_panel = ctk.CTkFrame(parent, width=320)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_panel.grid_propagate(False)
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
        # 요약 정보
        self._create_summary_section(left_panel)
        
        # 진행 상황
        self._create_progress_section(left_panel)
    
    def _create_summary_section(self, parent):
        """요약 정보 섹션"""
        summary_frame = ctk.CTkFrame(parent, corner_radius=10)
        summary_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # 제목
        title = ctk.CTkLabel(
            summary_frame,
            text=get_text("summary_title", "Summary"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 20))
        
        # 통계 카드들
        self.stat_cards = {}
        
        stats_info = [
            ("session_time", get_text("session_time", "Session Time"), "00:00:00"),
            ("total_files", get_text("total_files", "Total Files"), "0"),
            ("avg_quality", get_text("avg_quality", "Avg. Quality"), "0%"),
            ("total_lines", get_text("total_lines", "Total Lines"), "0"),
            ("lines_per_min", get_text("lines_per_min", "Lines/Min"), "0"),
            ("total_time", get_text("total_time", "Total Time"), "0s")
        ]
        
        for key, label, default_value in stats_info:
            card_frame = ctk.CTkFrame(summary_frame, height=50, corner_radius=8)
            card_frame.pack(fill="x", padx=15, pady=4)
            card_frame.pack_propagate(False)
            
            label_widget = ctk.CTkLabel(
                card_frame,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color=("gray60", "gray40")
            )
            label_widget.pack(side="left", padx=15)
            
            value_widget = ctk.CTkLabel(
                card_frame,
                text=default_value,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            value_widget.pack(side="right", padx=15)
            
            self.stat_cards[key] = value_widget
        
        # 하단 여백
        ctk.CTkLabel(summary_frame, text="").pack(pady=5)
    
    def _create_progress_section(self, parent):
        """진행 상황 섹션"""
        progress_frame = ctk.CTkFrame(parent, corner_radius=10)
        progress_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        # 제목
        title = ctk.CTkLabel(
            progress_frame,
            text=get_text("current_progress", "Current Progress"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(15, 20))
        
        # 현재 파일
        self.current_file_label = ctk.CTkLabel(
            progress_frame,
            text=get_text("no_active_translation", "No active translation"),
            font=ctk.CTkFont(size=13),
            wraplength=280
        )
        self.current_file_label.pack(pady=10, padx=15)
        
        # 진행률 바
        self.file_progress = ctk.CTkProgressBar(progress_frame, width=260, height=15)
        self.file_progress.pack(pady=10)
        self.file_progress.set(0)
        
        # 진행률 텍스트
        self.progress_text = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=12)
        )
        self.progress_text.pack(pady=5)
        
        # 상태
        self.status_label = ctk.CTkLabel(
            progress_frame,
            text=get_text("status_idle", "Idle"),
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        self.status_label.pack(pady=(10, 20))
    
    def _create_right_panel(self, parent):
        """우측 패널 생성"""
        right_panel = ctk.CTkFrame(parent)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)
        
        # 탭뷰
        self.tabview = ctk.CTkTabview(right_panel, corner_radius=10)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 파일 목록 탭
        self.files_tab = self.tabview.add(get_text("files_tab", "Files"))
        self._create_files_list(self.files_tab)
        
        # 통계 탭
        self.stats_tab = self.tabview.add(get_text("stats_tab", "Statistics"))
        self._create_statistics_view(self.stats_tab)
        
        # 로그 탭
        self.log_tab = self.tabview.add(get_text("log_tab", "Log"))
        self._create_log_view(self.log_tab)
    
    def _create_files_list(self, parent):
        """파일 목록 생성"""
        # 필터/검색 바
        filter_frame = ctk.CTkFrame(parent, height=45)
        filter_frame.pack(fill="x", padx=5, pady=5)
        filter_frame.pack_propagate(False)
        
        # 검색 입력
        self.search_var.trace('w', lambda *args: self._filter_files())
        search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text=get_text("search_placeholder", "Search files..."),
            textvariable=self.search_var,
            height=35
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # 정렬 옵션
        sort_options = [
            get_text("sort_newest", "Newest First"),
            get_text("sort_oldest", "Oldest First"),
            get_text("sort_quality_high", "Quality (High)"),
            get_text("sort_quality_low", "Quality (Low)"),
            get_text("sort_time_fast", "Time (Fast)"),
            get_text("sort_time_slow", "Time (Slow)")
        ]
        
        sort_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=sort_options,
            command=self._sort_files,
            variable=self.sort_var,
            width=150,
            height=35
        )
        sort_menu.pack(side="right", padx=5, pady=5)
        
        # 파일 리스트 컨테이너
        list_container = ctk.CTkFrame(parent)
        list_container.pack(fill="both", expand=True, padx=5, pady=5)
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # 헤더
        header_frame = ctk.CTkFrame(list_container, height=35)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=2)  # 파일명
        header_frame.grid_columnconfigure(1, weight=1)  # 상태
        header_frame.grid_columnconfigure(2, weight=1)  # 품질
        header_frame.grid_columnconfigure(3, weight=1)  # 시간
        header_frame.grid_columnconfigure(4, weight=1)  # 라인
        
        headers = [
            (get_text("col_filename", "Filename"), 0),
            (get_text("col_status", "Status"), 1),
            (get_text("col_quality", "Quality"), 2),
            (get_text("col_time", "Time"), 3),
            (get_text("col_lines", "Lines"), 4)
        ]
        
        for text, col in headers:
            label = ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(weight="bold")
            )
            label.grid(row=0, column=col, padx=5, pady=5)
        
        # 스크롤 가능한 파일 리스트
        self.files_scroll = ctk.CTkScrollableFrame(list_container)
        self.files_scroll.grid(row=1, column=0, sticky="nsew")
        self.files_scroll.grid_columnconfigure(0, weight=1)
    
    def _create_statistics_view(self, parent):
        """통계 뷰 생성"""
        stats_scroll = ctk.CTkScrollableFrame(parent)
        stats_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 품질 분포
        quality_frame = ctk.CTkFrame(stats_scroll, corner_radius=10)
        quality_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            quality_frame,
            text=get_text("quality_distribution", "Quality Distribution"),
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15)
        
        # 품질 분포 바들
        self.quality_bars = {}
        ranges = ["90-100%", "80-89%", "70-79%", "60-69%", "<60%"]
        colors = ["#00ff00", "#90EE90", "#FFD700", "#FFA500", "#FF6B6B"]
        
        for i, (range_text, color) in enumerate(zip(ranges, colors)):
            bar_container = ctk.CTkFrame(quality_frame, fg_color="transparent")
            bar_container.pack(fill="x", padx=20, pady=3)
            
            # 라벨
            label = ctk.CTkLabel(bar_container, text=range_text, width=80)
            label.pack(side="left", padx=(0, 10))
            
            # 진행 바
            progress = ctk.CTkProgressBar(
                bar_container, 
                progress_color=color,
                height=20
            )
            progress.pack(side="left", fill="x", expand=True)
            progress.set(0)
            
            # 개수
            count_label = ctk.CTkLabel(bar_container, text="0", width=50)
            count_label.pack(side="right", padx=(10, 0))
            
            self.quality_bars[range_text] = {
                'bar': progress,
                'count': count_label
            }
        
        ctk.CTkLabel(quality_frame, text="").pack(pady=10)
        
        # 시간 통계
        time_frame = ctk.CTkFrame(stats_scroll, corner_radius=10)
        time_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            time_frame,
            text=get_text("time_statistics", "Time Statistics"),
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=15)
        
        self.time_stats_text = ctk.CTkTextbox(time_frame, height=200)
        self.time_stats_text.pack(fill="x", padx=20, pady=(0, 20))
    
    def _create_log_view(self, parent):
        """로그 뷰 생성"""
        log_container = ctk.CTkFrame(parent)
        log_container.pack(fill="both", expand=True, padx=5, pady=5)
        log_container.grid_rowconfigure(0, weight=1)
        log_container.grid_columnconfigure(0, weight=1)
        
        # 로그 텍스트박스
        self.log_text = ctk.CTkTextbox(log_container, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 컨트롤 바
        control_bar = ctk.CTkFrame(log_container, height=40)
        control_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        ctk.CTkButton(
            control_bar,
            text=get_text("clear_log", "Clear Log"),
            command=self._clear_log,
            width=100
        ).pack(side="right", padx=5, pady=5)
    
    def _load_existing_stats(self):
        """기존 통계 로드"""
        try:
            # main_app에서 기존 통계 가져오기
            if hasattr(self.main_app, 'translation_stats') and self.main_app.translation_stats:
                session_start = getattr(self.main_app, 'translation_session_start', None)
                if session_start:
                    self.stats_data.session_start_time = session_start
                
                # 통계 추가
                for stat in self.main_app.translation_stats:
                    if self.stats_data.add_stat(stat):
                        self._add_file_item(stat)
                
                # UI 업데이트
                self._update_summary_stats()
                self._update_statistics_view()
                
                self._add_log(f"Loaded {len(self.main_app.translation_stats)} existing statistics")
                
        except Exception as e:
            self._add_log(f"Error loading existing stats: {str(e)}")
    
    def _start_live_updates(self):
        """실시간 업데이트 시작"""
        self._update_live_stats()
    
    def _update_live_stats(self):
        """실시간 통계 업데이트"""
        try:
            # 번역 진행 상태 확인
            is_active = False
            current_file = ""
            progress = 0.0
            
            if hasattr(self.main_app, 'translator_engine'):
                engine = self.main_app.translator_engine
                is_active = engine.translation_thread and engine.translation_thread.is_alive()
                
                if is_active:
                    current_file = engine._get_current_file_for_log()
                    
                    # 진행률 가져오기
                    if hasattr(self.main_app, 'control_panel'):
                        try:
                            progress = self.main_app.control_panel.progress_bar.get()
                        except:
                            progress = 0.0
            
            # UI 업데이트
            if is_active:
                self.current_file_label.configure(
                    text=f"{get_text('translating', 'Translating')}: {current_file}" if current_file else get_text('processing', 'Processing...')
                )
                self.status_label.configure(
                    text=get_text("status_active", "Active"),
                    text_color="#00ff00"
                )
                self.file_progress.set(progress)
                self.progress_text.configure(text=f"{int(progress * 100)}%")
            else:
                if self.is_translation_active:
                    # 번역이 막 끝남
                    self.current_file_label.configure(
                        text=get_text("translation_completed", "Translation completed")
                    )
                    self.status_label.configure(
                        text=get_text("status_completed", "Completed"),
                        text_color="#4169E1"
                    )
                    self.file_progress.set(1.0)
                    self.progress_text.configure(text="100%")
                else:
                    # 유휴 상태
                    self.current_file_label.configure(
                        text=get_text("no_active_translation", "No active translation")
                    )
                    self.status_label.configure(
                        text=get_text("status_idle", "Idle"),
                        text_color=("gray60", "gray40")
                    )
            
            self.is_translation_active = is_active
            
            # 요약 통계 업데이트
            self._update_summary_stats()
            
        except Exception as e:
            self._add_log(f"Live update error: {str(e)}")
        
        # 다음 업데이트 예약
        self.update_job = self.after(1000, self._update_live_stats)
    
    def _update_summary_stats(self):
        """요약 통계 업데이트"""
        try:
            # 세션 시간
            elapsed = datetime.now() - self.stats_data.session_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stat_cards['session_time'].configure(
                text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            )
            
            # 통계 요약
            summary = self.stats_data.get_summary()
            
            self.stat_cards['total_files'].configure(text=str(summary['total_files']))
            self.stat_cards['avg_quality'].configure(text=f"{summary['avg_quality']:.1f}%")
            self.stat_cards['total_lines'].configure(text=str(summary['total_lines']))
            self.stat_cards['lines_per_min'].configure(text=f"{summary['lines_per_minute']:.1f}")
            self.stat_cards['total_time'].configure(text=f"{summary['total_time']:.1f}s")
            
            # 품질에 따른 색상
            avg_quality = summary['avg_quality']
            if avg_quality >= 90:
                self.stat_cards['avg_quality'].configure(text_color="#00ff00")
            elif avg_quality >= 80:
                self.stat_cards['avg_quality'].configure(text_color="#90EE90")
            elif avg_quality >= 70:
                self.stat_cards['avg_quality'].configure(text_color="#FFD700")
            else:
                self.stat_cards['avg_quality'].configure(text_color="#FF6B6B")
                
        except Exception as e:
            self._add_log(f"Summary update error: {str(e)}")
    
    def _update_statistics_view(self):
        """통계 뷰 업데이트"""
        try:
            stats = self.stats_data.get_stats()
            if not stats:
                return
            
            # 품질 분포 계산
            quality_dist = defaultdict(int)
            for stat in stats:
                q = stat.get('quality', 0)
                if q is not None:
                    if q >= 90:
                        quality_dist["90-100%"] += 1
                    elif q >= 80:
                        quality_dist["80-89%"] += 1
                    elif q >= 70:
                        quality_dist["70-79%"] += 1
                    elif q >= 60:
                        quality_dist["60-69%"] += 1
                    else:
                        quality_dist["<60%"] += 1
            
            # 품질 바 업데이트
            total = len(stats)
            for range_text, widgets in self.quality_bars.items():
                count = quality_dist[range_text]
                percentage = (count / total) if total > 0 else 0
                widgets['bar'].set(percentage)
                widgets['count'].configure(text=str(count))
            
            # 시간 통계
            if stats:
                # None 값 처리하여 안전하게 계산
                valid_times = [s.get('time', 0) for s in stats if s.get('time') is not None]
                valid_lines = [s.get('lines', 0) for s in stats if s.get('lines') is not None]
                valid_qualities = [s.get('quality', 0) for s in stats if s.get('quality') is not None]
                
                total_time = sum(valid_times) if valid_times else 0
                avg_time = total_time / len(valid_times) if valid_times else 0
                max_time = max(valid_times) if valid_times else 0
                min_time = min(valid_times) if valid_times else 0
                total_lines = sum(valid_lines) if valid_lines else 0
                avg_lines = total_lines / len(valid_lines) if valid_lines else 0
                
                time_stats_text = f"""📊 Translation Statistics
                
Total Processing Time: {total_time:.1f} seconds
Average Time per File: {avg_time:.1f} seconds
Fastest File: {min_time:.1f} seconds
Slowest File: {max_time:.1f} seconds

📄 File Statistics

Files Processed: {len(stats)}
Total Lines: {total_lines:,}
Average Lines per File: {avg_lines:.1f}

⚡ Performance

Processing Speed: {(total_lines / total_time if total_time > 0 else 0):.1f} lines/second
Average Quality: {(sum(valid_qualities) / len(valid_qualities) if valid_qualities else 0):.1f}%
"""
                
                self.time_stats_text.delete("1.0", "end")
                self.time_stats_text.insert("1.0", time_stats_text)
                
        except Exception as e:
            self._add_log(f"Statistics view update error: {str(e)}")
    
    def add_file_stat(self, file_path: str, stats_dict: Dict[str, Any]):
        """파일 통계 추가 (외부에서 호출)"""
        if not self.winfo_exists():
            return
        
        stat_entry = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'timestamp': datetime.now(),
            'status': 'completed',
            'time': stats_dict.get('time', 0),
            'quality': stats_dict.get('quality', 100),
            'lines': stats_dict.get('lines', 0),
            'errors': stats_dict.get('errors', 0),
            'original_file': stats_dict.get('original_file', ''),
            'batch_qualities': stats_dict.get('batch_qualities', [])
        }
        
        # 메인 스레드에서 실행
        self.after(0, self._safe_add_stat, stat_entry)
    
    def add_file_stat_direct(self, stat_entry: Dict[str, Any]):
        """통계 데이터를 직접 추가 (main_window에서 호출)"""
        if not self.winfo_exists():
            return
        
        # 메인 스레드에서 실행
        self.after(0, self._safe_add_stat, stat_entry)
    
    def _safe_add_stat(self, stat_entry: Dict[str, Any]):
        """안전하게 통계 추가"""
        try:
            if self.stats_data.add_stat(stat_entry):
                self._add_file_item(stat_entry)
                self._update_summary_stats()
                self._update_statistics_view()
                
                self._add_log(
                    f"✅ {stat_entry['filename']} - "
                    f"Quality: {stat_entry['quality']:.1f}%, "
                    f"Time: {stat_entry['time']:.1f}s, "
                    f"Lines: {stat_entry['lines']}"
                )
        except Exception as e:
            self._add_log(f"Error adding stat: {str(e)}")
    
    def _add_file_item(self, stat_entry: Dict[str, Any]):
        """파일 아이템 추가"""
        item = FileListItem(
            self.files_scroll,
            stat_entry,
            on_click_callback=self._show_file_details
        )
        item.pack(fill="x", pady=2)
        self.file_items.append(item)
        
        # 정렬 적용
        self._apply_current_sort()
    
    def _show_file_details(self, stat_entry: Dict[str, Any]):
        """파일 상세 정보 표시"""
        detail_window = ctk.CTkToplevel(self)
        detail_window.title(stat_entry['filename'])
        detail_window.geometry("550x450")
        detail_window.resizable(False, False)
        
        # 메인 프레임
        main_frame = ctk.CTkFrame(detail_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 제목
        title_label = ctk.CTkLabel(
            main_frame,
            text=stat_entry['filename'],
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 상세 정보
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="both", expand=True)
        
        details = [
            (get_text("full_path", "Full Path"), stat_entry['file_path']),
            (get_text("original_file", "Original"), stat_entry.get('original_file', 'N/A')),
            (get_text("time_taken", "Time Taken"), f"{stat_entry['time']:.2f} seconds"),
            (get_text("lines_translated", "Lines"), f"{stat_entry['lines']:,}"),
            (get_text("quality_score", "Quality"), f"{stat_entry['quality']:.1f}%"),
            (get_text("errors_found", "Errors"), str(stat_entry['errors'])),
            (get_text("completed_at", "Completed"), stat_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
        ]
        
        for label, value in details:
            row_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row_frame,
                text=f"{label}:",
                font=ctk.CTkFont(weight="bold"),
                width=140,
                anchor="w"
            ).pack(side="left", padx=(20, 10))
            
            ctk.CTkLabel(
                row_frame,
                text=value,
                anchor="w"
            ).pack(side="left", fill="x", expand=True)
        
        # 버튼
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(
            btn_frame,
            text=get_text("open_folder", "Open Folder"),
            command=lambda: self._open_file_location(stat_entry['file_path']),
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text=get_text("close", "Close"),
            command=detail_window.destroy,
            width=120
        ).pack(side="right", padx=5)
        
        # 포커스
        detail_window.lift()
        detail_window.attributes('-topmost', True)
        detail_window.after(100, lambda: detail_window.attributes('-topmost', False))
    
    def _open_file_location(self, file_path: str):
        """파일 위치 열기"""
        try:
            directory = os.path.dirname(file_path)
            if sys.platform == "win32":
                os.startfile(directory)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", directory])
            else:
                subprocess.Popen(["xdg-open", directory])
        except Exception as e:
            messagebox.showerror(
                get_text("error", "Error"),
                f"Could not open location: {e}"
            )
    
    def _filter_files(self):
        """파일 검색/필터링"""
        search_term = self.search_var.get().lower()
        
        for item in self.file_items:
            if search_term in item.stat_entry['filename'].lower():
                item.pack(fill="x", pady=2)
            else:
                item.pack_forget()
    
    def _sort_files(self, choice: str):
        """파일 정렬"""
        self._apply_current_sort()
    
    def _apply_current_sort(self):
        """현재 정렬 기준 적용"""
        sort_choice = self.sort_var.get()
        
        # 정렬 함수 매핑
        if "newest" in sort_choice.lower() or sort_choice == "newest":
            self.file_items.sort(key=lambda x: x.stat_entry['timestamp'], reverse=True)
        elif "oldest" in sort_choice.lower():
            self.file_items.sort(key=lambda x: x.stat_entry['timestamp'])
        elif "quality" in sort_choice.lower() and "high" in sort_choice.lower():
            self.file_items.sort(key=lambda x: x.stat_entry['quality'], reverse=True)
        elif "quality" in sort_choice.lower() and "low" in sort_choice.lower():
            self.file_items.sort(key=lambda x: x.stat_entry['quality'])
        elif "time" in sort_choice.lower() and "fast" in sort_choice.lower():
            self.file_items.sort(key=lambda x: x.stat_entry['time'])
        elif "time" in sort_choice.lower() and "slow" in sort_choice.lower():
            self.file_items.sort(key=lambda x: x.stat_entry['time'], reverse=True)
        
        # 재배치
        for item in self.file_items:
            item.pack_forget()
        for item in self.file_items:
            item.pack(fill="x", pady=2)
    
    def _refresh_display(self):
        """화면 새로고침"""
        self._update_summary_stats()
        self._update_statistics_view()
        self._filter_files()
        self._add_log(get_text("display_refreshed", "Display refreshed"))
    
    def _export_stats(self):
        """통계 내보내기"""
        stats = self.stats_data.get_stats()
        if not stats:
            messagebox.showwarning(
                get_text("warning", "Warning"),
                get_text("no_data_to_export", "No data to export")
            )
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt")
            ]
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.json'):
                self._export_json(filepath, stats)
            elif filepath.endswith('.csv'):
                self._export_csv(filepath, stats)
            else:
                self._export_text(filepath, stats)
            
            messagebox.showinfo(
                get_text("success", "Success"),
                get_text("export_success", "Statistics exported successfully")
            )
            self._add_log(f"Statistics exported to: {filepath}")
            
        except Exception as e:
            messagebox.showerror(
                get_text("error", "Error"),
                f"Export failed: {str(e)}"
            )
    
    def _export_json(self, filepath: str, stats: List[Dict[str, Any]]):
        """JSON 형식으로 내보내기"""
        export_data = {
            'session_info': {
                'start_time': self.stats_data.session_start_time.isoformat(),
                'export_time': datetime.now().isoformat(),
                'total_files': len(stats)
            },
            'summary': self.stats_data.get_summary(),
            'statistics': []
        }
        
        for stat in stats:
            export_stat = stat.copy()
            export_stat['timestamp'] = stat['timestamp'].isoformat()
            export_data['statistics'].append(export_stat)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, filepath: str, stats: List[Dict[str, Any]]):
        """CSV 형식으로 내보내기"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 헤더
            writer.writerow([
                'Filename', 'Status', 'Quality(%)', 'Time(s)',
                'Lines', 'Errors', 'Timestamp', 'Original File'
            ])
            
            # 데이터
            for stat in stats:
                writer.writerow([
                    stat['filename'],
                    stat['status'],
                    f"{stat['quality']:.1f}",
                    f"{stat['time']:.2f}",
                    stat['lines'],
                    stat['errors'],
                    stat['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    stat.get('original_file', '')
                ])
    
    def _export_text(self, filepath: str, stats: List[Dict[str, Any]]):
        """텍스트 형식으로 내보내기"""
        with open(filepath, 'w', encoding='utf-8') as f:
            summary = self.stats_data.get_summary()
            
            f.write("=" * 80 + "\n")
            f.write("TRANSLATION STATISTICS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Session Started: {self.stats_data.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n{'-'*80}\n\n")
            
            f.write("SUMMARY\n")
            f.write(f"Total Files: {summary['total_files']}\n")
            f.write(f"Average Quality: {summary['avg_quality']:.1f}%\n")
            f.write(f"Total Time: {summary['total_time']:.1f} seconds\n")
            f.write(f"Total Lines: {summary['total_lines']:,}\n")
            f.write(f"Processing Speed: {summary['lines_per_minute']:.1f} lines/minute\n")
            
            f.write(f"\n{'-'*80}\n\n")
            f.write("DETAILED RESULTS\n\n")
            
            for i, stat in enumerate(stats, 1):
                f.write(f"{i}. {stat['filename']}\n")
                f.write(f"   Quality: {stat['quality']:.1f}%\n")
                f.write(f"   Time: {stat['time']:.2f} seconds\n")
                f.write(f"   Lines: {stat['lines']}\n")
                f.write(f"   Errors: {stat['errors']}\n")
                f.write(f"   Completed: {stat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"   Path: {stat['file_path']}\n")
                f.write("\n")
    
    def _clear_all(self):
        """모든 데이터 지우기"""
        if not self.stats_data.get_stats():
            return
        
        if messagebox.askyesno(
            get_text("confirm", "Confirm"),
            get_text("confirm_clear_all", "Clear all statistics?")
        ):
            # 데이터 초기화
            self.stats_data.clear()
            
            # UI 초기화
            for item in self.file_items:
                item.destroy()
            self.file_items.clear()
            
            # 통계 초기화
            self._update_summary_stats()
            self._update_statistics_view()
            
            # 로그 초기화
            self._clear_log()
            self._add_log(get_text("all_data_cleared", "All data cleared"))
    
    def _add_log(self, message: str):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
    
    def _clear_log(self):
        """로그 지우기"""
        self.log_text.delete("1.0", "end")
    
    def clear_dashboard(self):
        """대시보드 초기화 (번역 시작 시 호출)"""
        # 진행 상황만 리셋
        self.file_progress.set(0)
        self.progress_text.configure(text="0%")
        self.current_file_label.configure(
            text=get_text("starting_translation", "Starting translation...")
        )
        self.status_label.configure(
            text=get_text("status_preparing", "Preparing"),
            text_color="#FFA500"
        )
        
        self._add_log(get_text("new_translation_started", "New translation session started"))
    
    def update_language(self):
        """언어 업데이트"""
        self.title(get_text("dashboard_title", "Translation Dashboard"))
        self._refresh_display()
    
    def on_close(self):
        """창 닫기"""
        # 업데이트 작업 취소
        if self.update_job:
            self.after_cancel(self.update_job)
        
        self.destroy()