"""
FastAPI Backend Server for PDX Mod Translator
하이브리드 웹 앱의 백엔드 서버 - 로컬호스트에서 실행되어 브라우저로 UI 제공
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import webbrowser
import time
import threading

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

# 기존 번역기 모듈들 import
sys.path.append(str(Path(__file__).parent.parent.parent / "pdx translation tool"))
from translator_app.core.enhanced_translator_engine import EnhancedTranslatorEngine
from translator_app.core.settings_manager import SettingsManager
from translator_app.core.api_providers import APIProviderFactory
from translator_app.utils.localization import LANGUAGES, set_language

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDXTranslatorAPI:
    """PDX 번역기의 웹 API 백엔드"""
    
    def __init__(self):
        self.app = FastAPI(
            title="PDX Mod Translator API",
            description="로컬 웹 기반 패독겜 모드 번역기",
            version="1.0.0"
        )
        
        # CORS 설정 (로컬호스트 전용)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", 
                          "http://localhost:8000", "http://127.0.0.1:8000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # WebSocket 연결 관리
        self.websocket_connections: List[WebSocket] = []
        
        # 메인 이벤트 루프 참조 (나중에 설정됨)
        self.main_loop = None
        
        # 번역 엔진 초기화 (나중에)
        self.translator_engine = None
        self.settings_manager = None
        self.stop_event = None
        self.current_config = {}
        self.current_translation_task = None
        self.is_paused = False
        self.translation_state = {
            "is_running": False,
            "is_paused": False,
            "current_file": "",
            "total_files": 0,
            "completed_files": 0,
            "progress": 0
        }
        
        # 로그 배치 처리를 위한 상태
        self.log_batch = []
        self.log_batch_size = 5  # n개 파일 완료마다 로그 전송
        self.last_batch_time = time.time()
        self.batch_timeout = 30  # 30초마다 강제 로그 전송
        self.completed_files_count = 0  # 배치 처리를 위한 완료 파일 카운터
        
        # API 라우터 설정
        self._setup_routes()
        self._setup_api_routes()
        
        # 정적 파일 서빙 설정 (React 앱)
        self._setup_static_files()
    
    def _setup_routes(self):
        """API 엔드포인트 설정"""
        
        @self.app.get("/")
        async def root():
            """루트 경로 - React 앱 index.html 반환"""
            frontend_path = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
            if frontend_path.exists():
                return FileResponse(frontend_path)
            return {"message": "PDX Mod Translator API", "status": "ready"}
        
        @self.app.get("/api/health")
        async def health_check():
            """헬스 체크"""
            return {"status": "healthy", "message": "PDX Translator API is running"}
        
        @self.app.get("/api/config")
        async def get_config():
            """현재 설정 반환"""
            if not self.settings_manager:
                self._initialize_translator()
            
            # 기본 설정 반환
            return {
                "ui_language": "ko",
                "api_provider": "gemini", 
                "available_providers": APIProviderFactory.get_available_providers(),
                "models": APIProviderFactory.MODELS,
                "status": "ready"
            }
        
        @self.app.post("/api/config")
        async def update_config(config: Dict[str, Any]):
            """설정 업데이트"""
            if not self.settings_manager:
                self._initialize_translator()
                
            # 현재 설정 업데이트
            self.current_config.update(config)
            
            # WebSocket으로 설정 변경 알림
            await self._broadcast_message({
                "type": "config_updated",
                "data": config
            })
            
            return {"status": "success", "message": "Configuration updated"}
        
        @self.app.get("/api/languages")
        async def get_languages():
            """번역 지원 언어 목록 (Paradox 게임 표준)"""
            # Paradox 게임에서 지원하는 번역 언어 (정확한 목록)
            translation_languages = [
                "English",
                "French", 
                "German",
                "Japanese",
                "Korean",
                "Polish",
                "Portuguese",
                "Russian",
                "Chinese Simplified",
                "Spanish",
                "Turkish"
            ]
            
            return {
                "languages": translation_languages,
                "ui_languages": list(LANGUAGES.keys()),  # UI 언어는 별도
                "current_ui": "ko"
            }
        
        @self.app.post("/api/translate/start")
        async def start_translation(request: Dict[str, Any]):
            """번역 시작"""
            if not self.translator_engine:
                self._initialize_translator()
            
            # TODO: 번역 시작 로직 구현
            await self._broadcast_message({
                "type": "translation_started",
                "data": {"message": "Translation started"}
            })
            
            return {"status": "started", "message": "Translation process initiated"}
        
        @self.app.post("/api/translate/stop") 
        async def stop_translation():
            """번역 중지"""
            # TODO: 번역 중지 로직 구현
            await self._broadcast_message({
                "type": "translation_stopped", 
                "data": {"message": "Translation stopped"}
            })
            
            return {"status": "stopped", "message": "Translation process stopped"}
        
        @self.app.websocket("/api/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket 연결 - 실시간 로그/진행상황"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            # 첫 WebSocket 연결 시 메인 루프 설정
            if self.main_loop is None:
                try:
                    self.main_loop = asyncio.get_running_loop()
                    logger.info("Main event loop captured for thread-safe callbacks")
                except Exception as e:
                    logger.warning(f"Could not capture main event loop: {e}")
            
            try:
                # 연결 확인 메시지
                await websocket.send_json({
                    "type": "connected",
                    "message": "WebSocket connected successfully"
                })
                
                # 연결 유지
                while True:
                    try:
                        data = await websocket.receive_text()
                        # 클라이언트로부터의 메시지 처리
                        logger.info(f"Received WebSocket message: {data}")
                        
                        # JSON 파싱 및 메시지 처리
                        try:
                            message_data = json.loads(data)
                            await self._handle_websocket_message(message_data)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {data}")
                        except Exception as e:
                            logger.error(f"Error handling WebSocket message: {e}")
                            
                    except WebSocketDisconnect:
                        break
                        
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    def _setup_api_routes(self):
        """외부 API 라우터 포함"""
        try:
            from .api_routes import router as api_router
            self.app.include_router(api_router)
            logger.info("API routes loaded successfully")
        except ImportError as e:
            logger.warning(f"Could not load API routes: {e}")
            # 대안으로 절대 경로 시도
            try:
                import sys
                from pathlib import Path
                sys.path.append(str(Path(__file__).parent))
                from api_routes import router as api_router
                self.app.include_router(api_router)
                logger.info("API routes loaded successfully (fallback)")
            except ImportError as e2:
                logger.error(f"Failed to load API routes with fallback: {e2}")
    
    def _setup_static_files(self):
        """정적 파일 서빙 설정"""
        # React 빌드 결과물 서빙
        frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
        if frontend_dist.exists():
            # assets 폴더만 마운트 (Vite는 static 폴더를 생성하지 않음)
            assets_path = frontend_dist / "assets"
            if assets_path.exists():
                self.app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    def _initialize_translator(self):
        """번역 엔진 초기화"""
        try:
            # 설정 관리자 초기화
            config_path = Path(__file__).parent.parent.parent / "pdx translation tool" / "translation_gui_config.json"
            
            # 기본 프롬프트 템플릿과 사용 가능한 모델 목록 
            default_prompt_template = ""
            default_available_models = [
                "gemini-2.5-flash", "gemini-2.5-pro", "claude-sonnet-4-20250514", 
                "gpt-4.1-2025-04-14", "o3-2025-04-16"
            ]
            
            self.settings_manager = SettingsManager(default_prompt_template, default_available_models)
            
            # 번역 엔진 초기화 (콜백 함수들은 웹소켓으로 대체)
            import threading
            self.stop_event = threading.Event()
            
            # 원본 번역기 엔진 import - 경로 수정
            try:
                from translator_app.core.enhanced_translator_engine import EnhancedTranslatorEngine
                TranslatorEngine = EnhancedTranslatorEngine
            except ImportError:
                # backup 파일에서 import 시도
                import importlib.util
                backup_path = Path(__file__).parent.parent.parent / "pdx translation tool" / "translator_app" / "core" / "translator_engine.py.backup"
                spec = importlib.util.spec_from_file_location("translator_engine_backup", backup_path)
                translator_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(translator_module)
                TranslatorEngine = translator_module.TranslatorEngine
            
            # 번역 엔진 초기화
            self.translator_engine = TranslatorEngine(
                log_callback=self._log_callback,
                progress_callback=self._progress_callback,
                status_callback=self._status_callback,
                stop_event=self.stop_event,
                get_input_folder_callback=lambda: self.current_config.get('inputFolder', '')
            )
            
            logger.info("Translator engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            raise HTTPException(status_code=500, detail=f"Translator initialization failed: {str(e)}")
    
    async def _broadcast_message(self, message: Dict[str, Any]):
        """모든 WebSocket 연결에 메시지 브로드캐스트"""
        if not self.websocket_connections:
            return
            
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket: {e}")
                disconnected.append(websocket)
        
        # 연결이 끊어진 소켓들 제거
        for ws in disconnected:
            self.websocket_connections.remove(ws)
    
    def _log_callback(self, message: str, level: str = "info"):
        """로그 콜백 - 배치 처리로 WebSocket 전송"""
        logger.info(f"[{level.upper()}] {message}")
        
        # 파일 완료 로그인지 확인 (번역 완료 관련 메시지만 배치 처리)
        if any(keyword in message.lower() for keyword in ["번역 완료", "completed", "처리 완료", "finished"]):
            self.log_batch.append({
                "level": level,
                "message": message,
                "timestamp": time.time()
            })
            self.completed_files_count += 1
            
            # 배치 크기에 도달했거나 일정 시간이 지났으면 전송
            current_time = time.time()
            should_send_batch = (
                len(self.log_batch) >= self.log_batch_size or 
                (current_time - self.last_batch_time) > self.batch_timeout
            )
            
            if should_send_batch:
                self._send_batched_logs()
        else:
            # 중요한 로그(오류, 경고, 시작/종료)는 즉시 전송
            if level in ["error", "warning"] or any(keyword in message.lower() for keyword in ["시작", "시작합니다", "완료되었습니다", "중지", "오류"]):
                if self.main_loop and self.websocket_connections:
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_message({
                            "type": "log",
                            "level": level,
                            "message": message,
                            "timestamp": time.time()
                        }),
                        self.main_loop
                    )
    
    def _send_batched_logs(self):
        """배치 로그 전송"""
        if not self.log_batch or not self.main_loop or not self.websocket_connections:
            return
        
        # 배치 요약 메시지 생성
        batch_count = len(self.log_batch)
        summary_message = f"{batch_count}개 파일 처리 완료!"
        
        # 배치 로그 전송
        asyncio.run_coroutine_threadsafe(
            self._broadcast_message({
                "type": "log",
                "level": "info",
                "message": summary_message,
                "batch_details": self.log_batch,
                "batch_count": batch_count,
                "timestamp": time.time()
            }),
            self.main_loop
        )
        
        # 배치 상태 초기화
        self.log_batch.clear()
        self.last_batch_time = time.time()
    
    def _progress_callback(self, progress: float, message: str = ""):
        """진행률 콜백 - WebSocket으로 실시간 전송"""
        logger.info(f"Progress: {progress:.1f}% - {message}")
        
        # 번역 상태 업데이트
        self.translation_state["progress"] = progress
        
        # 진행률 통계 계산
        current_time = time.time()
        completed_files = self.translation_state.get("completed_files", 0)
        total_files = self.translation_state.get("total_files", 0)
        
        # ETA 계산
        if not hasattr(self, '_start_time'):
            self._start_time = current_time
        
        elapsed_time = current_time - self._start_time
        eta_seconds = 0
        translation_speed = 0.0
        
        if completed_files > 0 and elapsed_time > 0:
            avg_time_per_file = elapsed_time / completed_files
            remaining_files = total_files - completed_files
            eta_seconds = remaining_files * avg_time_per_file
            translation_speed = completed_files / (elapsed_time / 60)  # 파일/분
        
        # WebSocket으로 실시간 진행률 전송
        if self.main_loop and self.websocket_connections:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_message({
                    "type": "progress",
                    "progress": progress,
                    "message": message,
                    "current_file": self.translation_state.get("current_file", ""),
                    "completed_files": completed_files,
                    "total_files": total_files,
                    "elapsed_time": elapsed_time,
                    "eta_seconds": eta_seconds,
                    "translation_speed": translation_speed,
                    "timestamp": time.time()
                }),
                self.main_loop
            )
    
    def _status_callback(self, status: str, data: Dict[str, Any] = None):
        """상태 콜백 - WebSocket으로 실시간 전송"""
        logger.info(f"Status: {status} - {data or {}}")
        
        # 파일 정보 업데이트
        if data and "current_file" in data:
            self.translation_state["current_file"] = data["current_file"]
        if data and "total_files" in data:
            self.translation_state["total_files"] = data["total_files"]
        if data and "completed_files" in data:
            self.translation_state["completed_files"] = data["completed_files"]
        
        # WebSocket으로 상태 정보 전송
        if self.main_loop and self.websocket_connections:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_message({
                    "type": "status",
                    "status": status,
                    "data": data or {},
                    "translation_state": self.translation_state.copy(),
                    "timestamp": time.time()
                }),
                self.main_loop
            )
    
    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """WebSocket 메시지 처리"""
        message_type = data.get("type")
        
        if message_type == "ping":
            await self._broadcast_message({"type": "pong", "timestamp": time.time()})
        elif message_type == "start_translation":
            await self._handle_start_translation(data.get("config", {}))
        elif message_type == "stop_translation":
            await self._handle_stop_translation()
        elif message_type == "pause_translation":
            await self._handle_pause_translation()
        elif message_type == "reset_translation":
            await self._handle_reset_translation()
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")
    
    async def _handle_start_translation(self, config: Dict[str, Any]):
        """번역 시작 처리"""
        try:
            # 이미 실행 중인 번역이 있는지 확인
            if self.translation_state["is_running"]:
                await self._broadcast_message({
                    "type": "log",
                    "level": "warning",
                    "message": "번역이 이미 실행 중입니다"
                })
                return
            
            # 번역 엔진 초기화 확인
            if not self.translator_engine:
                self._initialize_translator()
            
            # 설정 업데이트
            self.current_config = config
            
            # 번역 상태 초기화
            self.translation_state.update({
                "is_running": True,
                "is_paused": False,
                "current_file": "",
                "total_files": 0,
                "completed_files": 0,
                "progress": 0
            })
            
            # 시작 시간 초기화 (ETA 계산용)
            self._start_time = time.time()
            
            # 배치 로그 상태 초기화
            self.log_batch.clear()
            self.completed_files_count = 0
            self.last_batch_time = time.time()
            
            # 번역 시작 상태 전송
            await self._broadcast_message({
                "type": "status",
                "status": "translation_started",
                "data": {"message": "번역이 시작되었습니다"}
            })
            
            # 실제 번역 작업을 백그라운드에서 시작
            self.current_translation_task = asyncio.create_task(self._run_translation_task(config))
            
        except Exception as e:
            logger.error(f"Translation start error: {e}")
            self.translation_state["is_running"] = False
            await self._broadcast_message({
                "type": "status",
                "status": "translation_error",
                "data": {"error": str(e)}
            })
    
    async def _run_translation_task(self, config: Dict[str, Any]):
        """실제 번역 작업 실행"""
        try:
            # API 제공자 설정
            success = self.translator_engine.set_api_provider(
                config.get('apiProvider', 'gemini'),
                config.get('apiKey', ''),
                config.get('modelName', 'gemini-2.5-flash')
            )
            
            if not success:
                await self._broadcast_message({
                    "type": "log",
                    "level": "error",
                    "message": "API 제공자 설정에 실패했습니다"
                })
                self.translation_state["is_running"] = False
                return
            
            await self._broadcast_message({
                "type": "log",
                "level": "info", 
                "message": f"번역 설정 로드 완료: {config.get('apiProvider')} / {config.get('modelName')}"
            })
            
            # 입력 폴더 확인
            input_folder = config.get('inputFolder', '')
            if not input_folder or not os.path.exists(input_folder):
                await self._broadcast_message({
                    "type": "log",
                    "level": "error",
                    "message": "입력 폴더가 지정되지 않았거나 존재하지 않습니다"
                })
                self.translation_state["is_running"] = False
                return
            
            # 번역할 파일 검색
            await self._broadcast_message({
                "type": "log",
                "level": "info",
                "message": "번역할 파일을 검색하는 중..."
            })
            
            # 실제 번역기 엔진의 translate_files_from_folder 메서드 호출
            await self._run_actual_translation(config)
            
        except Exception as e:
            logger.error(f"Translation task error: {e}")
            self.translation_state["is_running"] = False
            await self._broadcast_message({
                "type": "status",
                "status": "translation_error",
                "data": {"error": str(e)}
            })
    
    async def _run_actual_translation(self, config: Dict[str, Any]):
        """실제 번역기 엔진을 사용한 번역"""
        try:
            # 번역 파라미터 준비 (원본과 동일한 구조)
            input_folder = config.get('inputFolder', '')
            output_folder = config.get('outputFolder', '') or input_folder
            api_key = config.get('apiKey', '')
            model_name = config.get('modelName', 'gemini-2.5-flash')
            
            # 원본 번역기의 start_translation_process 메서드 사용
            success = self.translator_engine.start_translation_process(
                input_folder,
                output_folder,
                config.get('sourceLang', 'English'),
                config.get('targetLang', 'Korean'),
                batch_size=config.get('batchSize', 50),
                max_workers=config.get('maxWorkers', 100),
                prompt=config.get('promptTemplate', ''),
                glossary_content='',
                # 추가 매개변수는 kwargs로 전달
                api_key=api_key,
                model_name=model_name,
                delay_between_batches=config.get('delayBetweenBatches', 0.8),
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('maxTokens', 65536),
                keep_identifier=config.get('keepLangDefUnchanged', False),
                check_internal_lang=config.get('checkInternalLang', False),
                split_threshold=config.get('splitThreshold', 1000),
                selected_game=config.get('selectedGame', None),
                skip_already_translated=config.get('skipAlreadyTranslated', False),
                max_retries=config.get('maxRetries', 3),
                enable_backup=config.get('enableBackup', False)
            )
            
            if success:
                await self._broadcast_message({
                    "type": "log",
                    "level": "info",
                    "message": "번역 프로세스가 성공적으로 시작되었습니다"
                })
                
                # 번역 스레드가 완료될 때까지 대기
                await self._wait_for_translation_completion()
            else:
                await self._broadcast_message({
                    "type": "log",
                    "level": "error",
                    "message": "번역 프로세스 시작에 실패했습니다"
                })
                self.translation_state["is_running"] = False
            
        except Exception as e:
            logger.error(f"Actual translation error: {e}")
            self.translation_state["is_running"] = False
            await self._broadcast_message({
                "type": "status",
                "status": "translation_error", 
                "data": {"error": str(e)}
            })
    
    async def _wait_for_translation_completion(self):
        """번역 완료까지 대기"""
        try:
            while True:
                # 번역 스레드가 실행 중인지 확인
                if not self.translator_engine.translation_thread or not self.translator_engine.translation_thread.is_alive():
                    break
                
                # 중지 요청 확인
                if self.stop_event and self.stop_event.is_set():
                    break
                
                # 일시정지 처리
                while self.is_paused and self.translation_state["is_running"]:
                    await asyncio.sleep(1)
                
                await asyncio.sleep(1)
            
            # 번역 완료 처리
            if not (self.stop_event and self.stop_event.is_set()):
                # 남은 배치 로그가 있다면 전송
                if self.log_batch:
                    self._send_batched_logs()
                
                await self._broadcast_message({
                    "type": "status",
                    "status": "translation_completed",
                    "data": {"message": "번역이 완료되었습니다"}
                })
                
                await self._broadcast_message({
                    "type": "progress",
                    "progress": 100,
                    "data": {
                        "currentFile": "",
                        "totalFiles": self.translation_state.get("total_files", 0),
                        "completedFiles": self.translation_state.get("total_files", 0)
                    }
                })
            
        except Exception as e:
            logger.error(f"Wait for completion error: {e}")
        finally:
            # 남은 배치 로그가 있다면 전송
            if self.log_batch:
                self._send_batched_logs()
            
            self.translation_state["is_running"] = False
            self.is_paused = False
    
    async def _handle_stop_translation(self):
        """번역 중지 처리"""
        if not self.translation_state["is_running"]:
            await self._broadcast_message({
                "type": "log",
                "level": "warning",
                "message": "실행 중인 번역이 없습니다"
            })
            return
        
        # 번역 엔진의 중지 요청
        if self.translator_engine and hasattr(self.translator_engine, 'request_stop_translation'):
            self.translator_engine.request_stop_translation()
        
        if self.stop_event:
            self.stop_event.set()
        
        # 현재 번역 작업 취소
        if self.current_translation_task and not self.current_translation_task.done():
            self.current_translation_task.cancel()
        
        # 남은 배치 로그가 있다면 전송
        if self.log_batch:
            self._send_batched_logs()
        
        # 번역 상태 리셋
        self.translation_state.update({
            "is_running": False,
            "is_paused": False,
            "current_file": "",
            "progress": 0
        })
        self.is_paused = False
        
        await self._broadcast_message({
            "type": "status",
            "status": "translation_stopped",
            "data": {"message": "번역이 중지되었습니다"}
        })
        
        await self._broadcast_message({
            "type": "log",
            "level": "info",
            "message": "번역이 중지되었습니다"
        })
    
    async def _handle_pause_translation(self):
        """번역 일시정지 처리"""
        if not self.translation_state["is_running"]:
            await self._broadcast_message({
                "type": "log",
                "level": "warning",
                "message": "실행 중인 번역이 없습니다"
            })
            return
            
        self.is_paused = not self.is_paused
        self.translation_state["is_paused"] = self.is_paused
        
        if self.is_paused:
            await self._broadcast_message({
                "type": "status",
                "status": "translation_paused",
                "data": {"message": "번역이 일시정지되었습니다"}
            })
            await self._broadcast_message({
                "type": "log",
                "level": "info",
                "message": "번역이 일시정지되었습니다"
            })
        else:
            await self._broadcast_message({
                "type": "status", 
                "status": "translation_resumed",
                "data": {"message": "번역이 재개되었습니다"}
            })
            await self._broadcast_message({
                "type": "log",
                "level": "info",
                "message": "번역이 재개되었습니다"
            })
    
    async def _handle_reset_translation(self):
        """번역 초기화 처리"""
        # 실행 중인 번역이 있으면 먼저 중지
        if self.translation_state["is_running"]:
            await self._handle_stop_translation()
            # 중지 완료까지 잠시 대기
            await asyncio.sleep(1)
        
        # 모든 상태 초기화
        self.translation_state = {
            "is_running": False,
            "is_paused": False,
            "current_file": "",
            "total_files": 0,
            "completed_files": 0,
            "progress": 0
        }
        self.is_paused = False
        self.current_config = {}
        
        # 번역 엔진 중지 이벤트 클리어
        if self.stop_event:
            self.stop_event.clear()
            
        # 번역기 통계 클리어 (있다면)
        if self.translator_engine and hasattr(self.translator_engine, 'clear_statistics'):
            self.translator_engine.clear_statistics()
        
        await self._broadcast_message({
            "type": "status", 
            "status": "translation_reset",
            "data": {"message": "번역이 초기화되었습니다"}
        })
        
        await self._broadcast_message({
            "type": "progress",
            "progress": 0,
            "data": {
                "currentFile": "",
                "totalFiles": 0,
                "completedFiles": 0
            }
        })
        
        await self._broadcast_message({
            "type": "log",
            "level": "info",
            "message": "번역 상태가 초기화되었습니다"
        })

# 전역 API 인스턴스
api_instance = PDXTranslatorAPI()
app = api_instance.app

def start_server(host: str = "127.0.0.1", port: int = 8000):
    """서버 시작"""
    try:
        logger.info(f"Starting PDX Translator server on {host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == "__main__":
    start_server()