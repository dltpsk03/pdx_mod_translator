"""
PDX Mod Translator - 하이브리드 웹 앱 런처
사용자가 EXE를 실행하면 localhost 서버를 시작하고 브라우저로 UI를 표시
시스템 트레이에서 앱을 관리할 수 있음
"""

import os
import sys
import time
import threading
import webbrowser
import logging
from pathlib import Path
from typing import Optional
import subprocess
import socket
import requests

# GUI 관련 import
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw

# 백엔드 서버 import
from backend.main import start_server, api_instance

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDXTranslatorLauncher:
    """PDX 번역기 하이브리드 앱 런처"""
    
    def __init__(self):
        self.server_thread: Optional[threading.Thread] = None
        self.server_port = 8000
        self.server_host = "127.0.0.1"
        self.server_url = f"http://{self.server_host}:{self.server_port}"
        self.tray_icon: Optional[pystray.Icon] = None
        self.is_server_running = False
        
        # 런타임 경로 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller로 번들된 경우
            self.app_path = Path(sys.executable).parent
        else:
            # 개발 환경
            self.app_path = Path(__file__).parent
    
    def check_port_available(self, port: int) -> bool:
        """포트 사용 가능 여부 확인"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    def find_available_port(self, start_port: int = 8000) -> int:
        """사용 가능한 포트 찾기"""
        for port in range(start_port, start_port + 100):
            if self.check_port_available(port):
                return port
        raise RuntimeError("No available ports found")
    
    def start_backend_server(self):
        """백엔드 서버 시작"""
        try:
            # 사용 가능한 포트 찾기
            self.server_port = self.find_available_port()
            self.server_url = f"http://{self.server_host}:{self.server_port}"
            
            logger.info(f"Starting server on {self.server_url}")
            
            # 서버를 별도 스레드에서 실행
            self.server_thread = threading.Thread(
                target=start_server,
                args=(self.server_host, self.server_port),
                daemon=True
            )
            self.server_thread.start()
            
            # 서버 시작 대기
            self.wait_for_server()
            self.is_server_running = True
            
            logger.info("Backend server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            self.show_error_dialog("서버 시작 실패", f"백엔드 서버 시작에 실패했습니다:\n{str(e)}")
            raise
    
    def wait_for_server(self, timeout: int = 30):
        """서버가 완전히 시작될 때까지 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.server_url}/api/health", timeout=2)
                if response.status_code == 200:
                    logger.info("Server is ready")
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(0.5)
        
        raise TimeoutError("Server failed to start within timeout period")
    
    def open_browser(self):
        """브라우저에서 앱 열기"""
        try:
            logger.info(f"Opening browser to {self.server_url}")
            webbrowser.open(self.server_url)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            self.show_error_dialog("브라우저 열기 실패", f"브라우저 열기에 실패했습니다:\n{str(e)}")
    
    def create_tray_icon(self) -> pystray.Icon:
        """시스템 트레이 아이콘 생성"""
        # 간단한 아이콘 생성 (실제로는 ico 파일 사용 권장)
        def create_image():
            width = 64
            height = 64
            image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 간단한 원형 아이콘
            draw.ellipse([8, 8, width-8, height-8], fill=(59, 130, 246), outline=(37, 99, 235))
            draw.text((width//2-8, height//2-8), "PDX", fill=(255, 255, 255))
            
            return image
        
        # 트레이 메뉴 생성
        menu = pystray.Menu(
            pystray.MenuItem("열기", self.open_browser),
            pystray.MenuItem("새로고침", self.refresh_browser),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("서버 상태", lambda: self.show_server_status()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self.quit_application)
        )
        
        # 아이콘 생성
        icon = pystray.Icon(
            "PDX Translator",
            create_image(),
            "PDX Mod Translator - Professional Edition",
            menu
        )
        
        return icon
    
    def refresh_browser(self):
        """브라우저 새로고침 (새 탭 열기)"""
        self.open_browser()
    
    def show_server_status(self):
        """서버 상태 표시"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=5)
            if response.status_code == 200:
                status = "🟢 서버 실행 중"
                details = f"주소: {self.server_url}\n상태: 정상"
            else:
                status = "🟡 서버 응답 오류"
                details = f"주소: {self.server_url}\n상태 코드: {response.status_code}"
        except requests.exceptions.RequestException as e:
            status = "🔴 서버 연결 실패"
            details = f"오류: {str(e)}"
        
        self.show_info_dialog("서버 상태", f"{status}\n\n{details}")
    
    def show_loading_window(self):
        """로딩 화면 표시"""
        loading_window = tk.Tk()
        loading_window.title("PDX Mod Translator")
        loading_window.geometry("400x200")
        loading_window.resizable(False, False)
        
        # 중앙 정렬
        loading_window.eval('tk::PlaceWindow . center')
        
        # 로딩 메시지
        label = tk.Label(
            loading_window, 
            text="🚀 PDX Mod Translator 시작 중...\n\n서버를 초기화하고 있습니다.",
            font=("맑은 고딕", 12),
            pady=20
        )
        label.pack(expand=True)
        
        # 진행률 표시 (간단한 텍스트)
        progress_label = tk.Label(loading_window, text="잠시만 기다려주세요...", font=("맑은 고딕", 10))
        progress_label.pack()
        
        loading_window.update()
        
        # 3초 후 자동으로 창 닫기
        loading_window.after(3000, loading_window.destroy)
        
        return loading_window
    
    def show_error_dialog(self, title: str, message: str):
        """에러 대화상자 표시"""
        root = tk.Tk()
        root.withdraw()  # 메인 창 숨기기
        messagebox.showerror(title, message)
        root.destroy()
    
    def show_info_dialog(self, title: str, message: str):
        """정보 대화상자 표시"""
        root = tk.Tk()
        root.withdraw()  # 메인 창 숨기기
        messagebox.showinfo(title, message)
        root.destroy()
    
    def quit_application(self):
        """애플리케이션 종료"""
        logger.info("Shutting down PDX Translator")
        
        # 트레이 아이콘 제거
        if self.tray_icon:
            self.tray_icon.stop()
        
        # 서버 종료는 자동으로 됨 (daemon thread)
        sys.exit(0)
    
    def run(self):
        """메인 실행 함수"""
        try:
            logger.info("Starting PDX Mod Translator Hybrid App")
            
            # 로딩 화면 표시
            loading_window = self.show_loading_window()
            
            # 백엔드 서버 시작
            self.start_backend_server()
            
            # 로딩 화면 닫기
            try:
                loading_window.destroy()
            except:
                pass
            
            # 브라우저 열기
            self.open_browser()
            
            # 시스템 트레이 아이콘 생성 및 실행
            self.tray_icon = self.create_tray_icon()
            
            logger.info("Application started successfully, running in system tray")
            
            # 트레이에서 실행 (메인 루프)
            self.tray_icon.run()
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            self.quit_application()
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            self.show_error_dialog(
                "시작 실패", 
                f"PDX Mod Translator 시작에 실패했습니다:\n\n{str(e)}\n\n문제가 지속되면 개발자에게 문의해주세요."
            )
            sys.exit(1)

def main():
    """메인 진입점"""
    launcher = PDXTranslatorLauncher()
    launcher.run()

if __name__ == "__main__":
    main()