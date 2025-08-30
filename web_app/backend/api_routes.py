"""
기존 번역기 엔진을 REST API로 래핑하는 라우터
기존 코드를 최대한 재활용하여 웹 API로 노출
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import json
import tempfile
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import tkinter as tk
from tkinter import filedialog

# 기존 번역기 모듈들 import - 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent / "pdx translation tool"))
try:
    from translator_app.core.enhanced_translator_engine import EnhancedTranslatorEngine
    from translator_app.core.settings_manager import SettingsManager
    from translator_app.core.api_providers import APIProviderFactory
    from translator_app.utils.localization import LANGUAGES, set_language
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import translator modules: {e}")
    # 기본값으로 처리
    APIProviderFactory = None
    LANGUAGES = {"ko": {"ui_lang_self_name": "한국어"}, "en": {"ui_lang_self_name": "English"}}

# API 모델들
class TranslationRequest(BaseModel):
    input_folder: str
    output_folder: str
    source_lang: str = "English"
    target_lang: str = "Korean" 
    api_provider: str = "gemini"
    model_name: str = "gemini-2.5-flash"
    api_key: str
    batch_size: int = 50
    max_workers: int = 100
    prompt_template: Optional[str] = None
    glossary_content: Optional[str] = None
    validation_level: str = "standard"
    selected_game: Optional[str] = None
    skip_already_translated: bool = False
    enable_backup: bool = False
    split_large_files_threshold: int = 1000
    temperature: float = 0.5
    max_retries: int = 3
    active_glossaries: List[str] = []

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]

# API 라우터 생성
router = APIRouter(prefix="/api", tags=["translation"])

# 전역 변수들 (기존 main_window.py의 역할)
translator_engine: Optional[EnhancedTranslatorEngine] = None
settings_manager: Optional[SettingsManager] = None
current_translation_task: Optional[asyncio.Task] = None

def get_translator_engine() -> EnhancedTranslatorEngine:
    """번역 엔진 인스턴스 가져오기 (싱글톤 패턴)"""
    global translator_engine, settings_manager
    
    if translator_engine is None:
        # 설정 파일 경로
        config_path = Path(__file__).parent.parent.parent / "pdx translation tool" / "translation_gui_config.json"
        
        # 설정 관리자 초기화
        default_prompt_template = ""
        default_available_models = [
            "gemini-2.5-flash", "gemini-2.5-pro", "claude-sonnet-4-20250514", 
            "gpt-4.1-2025-04-14", "o3-2025-04-16"
        ]
        settings_manager = SettingsManager(default_prompt_template, default_available_models)
        
        # 번역 엔진 초기화 (콜백들은 WebSocket을 통해 처리)
        import threading
        stop_event = threading.Event()
        translator_engine = EnhancedTranslatorEngine(
            log_callback=lambda msg, level="info": None,  # WebSocket으로 대체됨
            progress_callback=lambda progress, msg="": None,  # WebSocket으로 대체됨
            status_callback=lambda status, data=None: None,  # WebSocket으로 대체됨
            stop_event=stop_event,
            get_input_folder_callback=lambda: ""
        )
    
    return translator_engine

@router.get("/providers")
async def get_api_providers():
    """사용 가능한 API 제공자 목록"""
    return {
        "providers": APIProviderFactory.get_available_providers(),
        "models": APIProviderFactory.MODELS,
        "test_models": APIProviderFactory.TEST_MODELS
    }

@router.get("/games")
async def get_available_games():
    """지원되는 게임 목록"""
    engine = get_translator_engine()
    # PromptManager 직접 접근으로 임시 수정
    games = ["Victoria 3", "Europa Universalis IV", "Crusader Kings III", "Hearts of Iron IV", "Stellaris", "Imperator: Rome"]
    return {
        "games": games,
        "default": "Victoria 3"
    }

@router.get("/glossaries")
async def get_glossaries():
    """사용 가능한 용어집 목록"""
    engine = get_translator_engine()
    glossaries = engine.prompt_manager.glossary_manager.get_available_glossaries()
    return {
        "glossaries": glossaries,
        "active": engine.prompt_manager.glossary_manager.active_glossaries
    }

@router.post("/glossaries/{name}/activate")
async def activate_glossary(name: str):
    """용어집 활성화"""
    engine = get_translator_engine()
    engine.prompt_manager.glossary_manager.activate_glossary(name)
    return {"status": "success", "message": f"Glossary '{name}' activated"}

@router.post("/glossaries/{name}/deactivate")
async def deactivate_glossary(name: str):
    """용어집 비활성화"""
    engine = get_translator_engine()
    engine.prompt_manager.glossary_manager.deactivate_glossary(name)
    return {"status": "success", "message": f"Glossary '{name}' deactivated"}

@router.post("/glossaries")
async def create_glossary(name: str = Form(...), description: str = Form(""), terms: str = Form(...)):
    """새 용어집 생성"""
    try:
        engine = get_translator_engine()
        # JSON 형태의 terms 파싱
        import json
        terms_dict = json.loads(terms) if terms.strip() else {}
        
        success = engine.prompt_manager.glossary_manager.save_glossary(name, terms_dict, description)
        
        if success:
            return {"status": "success", "message": f"Glossary '{name}' created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create glossary")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/glossaries/{name}")
async def delete_glossary(name: str):
    """용어집 삭제"""
    engine = get_translator_engine()
    success = engine.prompt_manager.glossary_manager.delete_glossary(name)
    
    if success:
        return {"status": "success", "message": f"Glossary '{name}' deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete glossary")

@router.get("/glossaries/{name}")
async def get_glossary(name: str):
    """특정 용어집 정보"""
    engine = get_translator_engine()
    glossary = engine.prompt_manager.glossary_manager.load_glossary(name)
    
    if glossary:
        return glossary
    else:
        raise HTTPException(status_code=404, detail="Glossary not found")

@router.get("/validation/levels")
async def get_validation_levels():
    """유효성 검사 레벨 목록"""
    return {
        "levels": ["off", "basic", "standard", "strict"],
        "descriptions": {
            "off": "유효성 검사 비활성화",
            "basic": "기본 YAML 구문 검사",
            "standard": "표준 번역 품질 검사",
            "strict": "엄격한 검증 및 자동 교정"
        }
    }

@router.post("/providers/{provider}/test")
async def test_api_connection(provider: str, api_key: str = Form(...)):
    """API 연결 테스트"""
    try:
        is_valid, message = APIProviderFactory.validate_provider_setup(provider, api_key)
        return {
            "success": is_valid,
            "message": message,
            "provider": provider
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/folder/select")
async def select_folder():
    """폴더 선택 대화상자 열기"""
    try:
        # Tkinter 루트 창 생성 (숨김)
        root = tk.Tk()
        root.withdraw()  # 메인 창 숨기기
        root.attributes('-topmost', True)  # 최상위로 올리기
        
        # 폴더 선택 대화상자 열기
        folder_path = filedialog.askdirectory(
            title="폴더를 선택하세요",
            parent=root
        )
        
        root.destroy()  # 리소스 정리
        
        if folder_path:
            return {"success": True, "path": folder_path}
        else:
            return {"success": False, "message": "폴더 선택이 취소되었습니다."}
            
    except Exception as e:
        return {"success": False, "message": f"폴더 선택 중 오류 발생: {str(e)}"}

@router.get("/languages")
async def get_supported_languages():
    """지원되는 UI 언어 목록"""
    return {
        "languages": {
            code: lang_data.get("ui_lang_self_name", code) 
            for code, lang_data in LANGUAGES.items()
        },
        "current": "ko"  # TODO: 현재 설정된 언어 반환
    }

@router.get("/config")
async def get_current_config():
    """현재 설정 가져오기"""
    global settings_manager
    
    if settings_manager is None:
        get_translator_engine()  # 초기화
    
    # 기본 설정 반환 (기존 main_window.py의 변수들과 동일)
    config = {
        # UI 설정
        "ui_language": "ko",
        "appearance_mode": "system",
        
        # API 설정  
        "api_provider": "gemini",
        "model_name": "gemini-2.5-flash",
        "api_key": "",
        
        # 번역 설정
        "source_lang": "English",
        "target_lang": "Korean",
        "batch_size": 50,
        "max_workers": 100,
        "delay_between_batches": 0.8,
        
        # 경로 설정
        "input_folder": "",
        "output_folder": "",
        
        # 고급 설정
        "split_threshold": 1000,
        "max_retries": 3,
        "validation_level": "standard",
        "keep_lang_def_unchanged": False,
        "check_internal_lang": False,
        "skip_already_translated": False,
        "enable_backup": False,
        
        # 프롬프트
        "prompt_template": "",
        "glossary_files": []
    }
    
    # TODO: 실제 설정 파일에서 로드
    return {"config": config, "status": "success"}

@router.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """설정 업데이트"""
    global settings_manager
    
    try:
        if settings_manager is None:
            get_translator_engine()  # 초기화
        
        # TODO: 설정을 실제로 저장
        config = request.config
        
        # API 제공자 설정 업데이트
        if all(key in config for key in ["api_provider", "api_key", "model_name"]):
            engine = get_translator_engine()
            success = engine.set_api_provider(
                config["api_provider"],
                config["api_key"], 
                config["model_name"]
            )
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to configure API provider")
        
        return {"status": "success", "message": "Configuration updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/files/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """파일 업로드 (드래그앤드롭 대용)"""
    uploaded_files = []
    
    try:
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp(prefix="pdx_translator_")
        
        for file in files:
            if file.filename:
                file_path = Path(temp_dir) / file.filename
                
                # 파일 저장
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                uploaded_files.append({
                    "filename": file.filename,
                    "path": str(file_path),
                    "size": len(content)
                })
        
        return {
            "status": "success",
            "files": uploaded_files,
            "temp_dir": temp_dir
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate/start")
async def start_translation(request: TranslationRequest, background_tasks: BackgroundTasks):
    """번역 시작"""
    global current_translation_task
    
    try:
        # 이미 실행 중인 번역이 있는지 확인
        if current_translation_task and not current_translation_task.done():
            raise HTTPException(status_code=409, detail="Translation already in progress")
        
        engine = get_translator_engine()
        
        # API 제공자 설정
        success = engine.set_api_provider(
            request.api_provider,
            request.api_key,
            request.model_name
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to configure API provider")
        
        # 백그라운드에서 번역 실행
        async def run_translation():
            try:
                # 활성 용어집 설정
                for glossary_name in request.active_glossaries:
                    engine.prompt_manager.glossary_manager.activate_glossary(glossary_name)
                
                # 실제 번역 프로세스 시작
                success = engine.start_translation_process(
                    input_folder=request.input_folder,
                    output_folder=request.output_folder,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang,
                    batch_size=request.batch_size,
                    max_workers=request.max_workers,
                    prompt=request.prompt_template or "",
                    glossary_content=request.glossary_content or "",
                    # 추가 설정들
                    selected_game=request.selected_game,
                    validation_level=request.validation_level,
                    skip_already_translated=request.skip_already_translated,
                    enable_backup=request.enable_backup,
                    split_large_files_threshold=request.split_large_files_threshold,
                    temperature=request.temperature,
                    max_retries=request.max_retries
                )
                if not success:
                    print("Translation failed to start")
            except Exception as e:
                # 에러 로깅 및 WebSocket으로 전송
                print(f"Translation error: {e}")
        
        # 비동기 작업 시작
        current_translation_task = asyncio.create_task(run_translation())
        background_tasks.add_task(lambda: current_translation_task)
        
        return {
            "status": "started",
            "message": "Translation started successfully",
            "task_id": id(current_translation_task)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate/stop")
async def stop_translation():
    """번역 중지"""
    global current_translation_task
    
    try:
        if current_translation_task and not current_translation_task.done():
            current_translation_task.cancel()
            
            # 번역 엔진에도 중지 신호 전송
            engine = get_translator_engine()
            if hasattr(engine, 'stop_translation'):
                engine.stop_translation()
            
            return {"status": "stopped", "message": "Translation stopped successfully"}
        else:
            return {"status": "not_running", "message": "No translation in progress"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/translate/status")
async def get_translation_status():
    """번역 상태 확인"""
    global current_translation_task
    
    try:
        engine = get_translator_engine()
        
        # 번역 진행 상태 확인
        is_running = current_translation_task and not current_translation_task.done()
        
        # 향상된 통계 정보
        stats = engine.get_translation_statistics()
        
        if current_translation_task is None:
            return {
                "status": "idle", 
                "message": "No translation task",
                "stats": stats,
                "cache_stats": engine.performance_optimizer.get_cache_stats()
            }
        elif current_translation_task.done():
            if current_translation_task.exception():
                return {
                    "status": "error", 
                    "message": str(current_translation_task.exception()),
                    "stats": stats
                }
            else:
                return {
                    "status": "completed", 
                    "message": "Translation completed successfully",
                    "stats": stats
                }
        else:
            return {
                "status": "running", 
                "message": "Translation in progress",
                "stats": stats,
                "cache_stats": engine.performance_optimizer.get_cache_stats(),
                "active_glossaries": engine.prompt_manager.glossary_manager.active_glossaries
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/download/{file_path:path}")
async def download_file(file_path: str):
    """번역된 파일 다운로드"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type='application/octet-stream'
    )

# Translation Dashboard and Statistics
@router.get("/statistics/dashboard")
async def get_translation_statistics():
    """번역 대시보드 통계 데이터 가져오기"""
    try:
        engine = get_translator_engine()
        
        # 기본 통계 데이터 구조
        stats = {
            "session_stats": {
                "files_translated": 0,
                "lines_translated": 0,
                "total_translation_time": 0,
                "average_speed": 0,
                "success_rate": 0,
                "errors_detected": 0,
                "errors_corrected": 0
            },
            "api_usage": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "cache_hits": 0,
                "cache_misses": 0
            },
            "quality_metrics": {
                "validation_level": "standard",
                "auto_corrections": 0,
                "quality_score": 0.0,
                "duplicate_removals": 0
            },
            "performance_metrics": {
                "average_batch_size": 0,
                "concurrent_files": 0,
                "memory_usage": 0,
                "processing_speed": 0
            }
        }
        
        # 실제 엔진에서 통계 가져오기 (있으면)
        if hasattr(engine, 'get_statistics'):
            actual_stats = engine.get_statistics()
            stats.update(actual_stats)
        
        return {"status": "success", "data": stats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/statistics/export")
async def export_statistics(format: str = "json"):
    """통계 데이터 내보내기"""
    try:
        stats_response = await get_translation_statistics()
        stats = stats_response["data"]
        
        if format.lower() == "csv":
            # CSV 형태로 변환
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 헤더 작성
            writer.writerow(["Category", "Metric", "Value"])
            
            # 데이터 작성
            for category, metrics in stats.items():
                for metric, value in metrics.items():
                    writer.writerow([category, metric, value])
            
            return {"status": "success", "data": output.getvalue(), "format": "csv"}
        else:
            # JSON 형태로 반환
            return {"status": "success", "data": stats, "format": "json"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Game Prompts Management
@router.get("/prompts/games")
async def get_available_games():
    """사용 가능한 게임 목록과 프롬프트 가져오기"""
    try:
        from translator_app.core.game_prompts import get_enhanced_prompt, GAME_PROMPTS
        
        games = {}
        for game_key in GAME_PROMPTS.keys():
            prompt = get_enhanced_prompt(game_key, "English", "Korean")
            games[game_key] = {
                "name": game_key.replace("_", " ").title(),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt
            }
        
        return {"status": "success", "games": games}
        
    except Exception as e:
        return {"status": "success", "games": {
            "eu4": {"name": "Europa Universalis IV", "prompt_preview": "Default EU4 translation prompt..."},
            "ck3": {"name": "Crusader Kings III", "prompt_preview": "Default CK3 translation prompt..."},
            "hoi4": {"name": "Hearts of Iron IV", "prompt_preview": "Default HOI4 translation prompt..."},
            "stellaris": {"name": "Stellaris", "prompt_preview": "Default Stellaris translation prompt..."}
        }}

@router.get("/prompts/games/{game_id}")
async def get_game_prompt(game_id: str):
    """특정 게임의 프롬프트 가져오기"""
    try:
        from translator_app.core.game_prompts import get_enhanced_prompt
        
        prompt = get_enhanced_prompt(game_id, "English", "Korean")
        return {"status": "success", "game_id": game_id, "prompt": prompt}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Checkpoint Management
@router.get("/checkpoints")
async def list_checkpoints():
    """사용 가능한 체크포인트 목록 가져오기"""
    try:
        checkpoint_dir = Path(__file__).parent.parent.parent / "pdx translation tool" / "checkpoints"
        if not checkpoint_dir.exists():
            return {"status": "success", "checkpoints": []}
        
        checkpoints = []
        for checkpoint_file in checkpoint_dir.glob("*.checkpoint"):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    "filename": checkpoint_file.stem,
                    "file_path": data.get("file_path", ""),
                    "completed_lines": data.get("completed_lines", 0),
                    "total_lines": data.get("total_lines", 0),
                    "progress": (data.get("completed_lines", 0) / max(data.get("total_lines", 1), 1)) * 100,
                    "timestamp": data.get("timestamp", 0),
                    "api_provider": data.get("api_provider", ""),
                    "schema_version": data.get("schema_version", "1.0")
                })
            except Exception as e:
                continue
        
        # 타임스탬프로 정렬 (최신순)
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"status": "success", "checkpoints": checkpoints}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/checkpoints/{filename}")
async def delete_checkpoint(filename: str):
    """체크포인트 파일 삭제"""
    try:
        checkpoint_dir = Path(__file__).parent.parent.parent / "pdx translation tool" / "checkpoints"
        checkpoint_file = checkpoint_dir / f"{filename}.checkpoint"
        
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            return {"status": "success", "message": "Checkpoint deleted"}
        else:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkpoints/{filename}/restore")
async def restore_from_checkpoint(filename: str):
    """체크포인트에서 번역 복원"""
    try:
        checkpoint_dir = Path(__file__).parent.parent.parent / "pdx translation tool" / "checkpoints"
        checkpoint_file = checkpoint_dir / f"{filename}.checkpoint"
        
        if not checkpoint_file.exists():
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)
        
        # 체크포인트 데이터를 현재 설정으로 로드
        restore_config = {
            "inputFolder": checkpoint_data.get("file_path", ""),
            "apiProvider": checkpoint_data.get("api_provider", "gemini"),
            "resumeFromCheckpoint": True,
            "checkpointData": checkpoint_data
        }
        
        return {"status": "success", "message": "Checkpoint loaded", "config": restore_config}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Term Consistency Management
@router.post("/consistency/check")
async def check_term_consistency(request: Dict[str, Any]):
    """용어 일관성 검사"""
    try:
        input_folder = request.get("input_folder", "")
        glossary_terms = request.get("glossary_terms", [])
        
        if not input_folder or not os.path.exists(input_folder):
            raise HTTPException(status_code=400, detail="Invalid input folder")
        
        # 일관성 검사 결과 (예시)
        consistency_results = {
            "total_files_checked": 0,
            "total_terms_found": 0,
            "inconsistent_terms": [],
            "suggestions": []
        }
        
        # 실제 일관성 검사 로직은 여기에 구현
        # 현재는 기본 구조만 반환
        
        return {"status": "success", "results": consistency_results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Live Preview Management  
@router.get("/preview/current")
async def get_live_preview():
    """현재 번역 미리보기 데이터"""
    try:
        # 현재 번역 중인 파일의 미리보기 데이터
        preview_data = {
            "current_file": "",
            "source_lines": [],
            "translated_lines": [],
            "progress": 0,
            "is_translating": False
        }
        
        # 실제 번역 엔진에서 미리보기 데이터 가져오기
        engine = get_translator_engine()
        if hasattr(engine, 'get_current_preview'):
            preview_data = engine.get_current_preview()
        
        return {"status": "success", "preview": preview_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# UI Configuration
@router.get("/ui/themes")
async def get_available_themes():
    """사용 가능한 UI 테마 목록"""
    return {
        "status": "success", 
        "themes": [
            {"id": "light", "name": "Light", "description": "밝은 테마"},
            {"id": "dark", "name": "Dark", "description": "어두운 테마"},
            {"id": "system", "name": "System", "description": "시스템 설정 따름"}
        ]
    }

@router.post("/ui/theme")
async def set_theme(theme_data: Dict[str, str]):
    """UI 테마 설정"""
    theme_id = theme_data.get("theme_id", "system")
    
    # 테마 설정 저장 로직 (설정 파일에 저장)
    return {"status": "success", "message": f"Theme set to {theme_id}"}

# Validation and Error Correction Settings
@router.get("/validation/levels")
async def get_validation_levels():
    """사용 가능한 검증 레벨"""
    return {
        "status": "success",
        "levels": [
            {"id": "off", "name": "Off", "description": "검증 비활성화"},
            {"id": "basic", "name": "Basic", "description": "기본 검증"},
            {"id": "standard", "name": "Standard", "description": "표준 검증"},
            {"id": "strict", "name": "Strict", "description": "엄격한 검증"}
        ]
    }

@router.get("/validation/settings")
async def get_validation_settings():
    """현재 검증 설정"""
    return {
        "status": "success",
        "settings": {
            "validation_level": "standard",
            "auto_threshold": 0.2,
            "fix_yaml": True,
            "preserve_format": True,
            "remove_duplicates": True,
            "fix_incomplete": False,
            "duplicate_strategy": "keep_first",
            "quality_thresholds": {
                "min_length_ratio": 0.3,
                "max_length_ratio": 3.0,
                "similarity_threshold": 0.8
            }
        }
    }

@router.post("/validation/settings")
async def update_validation_settings(settings: Dict[str, Any]):
    """검증 설정 업데이트"""
    try:
        # 검증 설정 저장 로직
        return {"status": "success", "message": "Validation settings updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))