# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리
block_cipher = None
project_root = Path(SPECPATH).parent

# 필요한 데이터 파일들
datas = [
    # React 빌드된 정적 파일들
    (str(project_root / 'web_app' / 'frontend' / 'dist'), 'frontend/dist'),
    
    # 백엔드 파일들
    (str(project_root / 'web_app' / 'backend'), 'backend'),
    
    # 기존 번역 엔진 파일들
    (str(project_root / 'enhanced_translator_engine.py'), '.'),
    (str(project_root / 'settings_manager.py'), '.'),
    (str(project_root / 'api_providers'), 'api_providers'),
    
    # 설정 파일들
    (str(project_root / 'config'), 'config'),
    
    # 언어 파일들 (있다면)
    (str(project_root / 'languages'), 'languages') if (project_root / 'languages').exists() else None,
    
    # 리소스 파일들
    (str(project_root / 'resources'), 'resources') if (project_root / 'resources').exists() else None,
]

# None 제거
datas = [d for d in datas if d is not None]

# 히든 임포트들
hiddenimports = [
    # FastAPI 관련
    'fastapi',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    
    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic.main',
    'pydantic.typing',
    'pydantic.json',
    
    # Starlette
    'starlette',
    'starlette.applications',
    'starlette.routing',
    'starlette.responses',
    'starlette.staticfiles',
    'starlette.websockets',
    'starlette.middleware',
    'starlette.middleware.cors',
    
    # 시스템 트레이
    'pystray',
    'pystray._win32',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    
    # HTTP 클라이언트
    'httpx',
    'requests',
    'aiohttp',
    
    # JSON 처리
    'json',
    'yaml',
    
    # AI API 클라이언트들
    'openai',
    'anthropic',
    'google.generativeai',
    'deepl',
    
    # 유틸리티
    'threading',
    'multiprocessing',
    'concurrent.futures',
    'asyncio',
    'websockets',
    
    # 기존 번역 엔진 의존성들
    'tkinter',
    'customtkinter',  # 만약 일부 유틸리티를 재사용한다면
]

# 메인 애플리케이션 분석
a = Analysis(
    [str(project_root / 'web_app' / 'launcher.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 패키지 제외
        'matplotlib',
        'numpy.random._pickle',
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
    optimize=0,
)

# 불필요한 DLL 제거
def remove_from_list(input_list, item_name):
    return [item for item in input_list if not item[0].lower().endswith(item_name.lower())]

# 큰 불필요한 라이브러리들 제거
a.binaries = remove_from_list(a.binaries, 'Qt5Core.dll')
a.binaries = remove_from_list(a.binaries, 'Qt5Gui.dll')
a.binaries = remove_from_list(a.binaries, 'Qt5Widgets.dll')
a.binaries = remove_from_list(a.binaries, 'libcrypto-1_1-x64.dll')
a.binaries = remove_from_list(a.binaries, 'libssl-1_1-x64.dll')

# PYZ 및 EXE 생성
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDX_Mod_Translator_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 압축 사용 (설치되어 있다면)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 콘솔 창 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'resources' / 'icon.ico') if (project_root / 'resources' / 'icon.ico').exists() else None,
    version_file=str(project_root / 'version_info.txt') if (project_root / 'version_info.txt').exists() else None,
)

# 추가 최적화를 위한 압축
if upx:
    exe.upx = True
    exe.upx_exclude = [
        'vcruntime140.dll',
        'msvcp140.dll',
        'api-ms-win-*.dll',
    ]