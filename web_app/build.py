#!/usr/bin/env python3
"""
PDX Mod Translator Professional Edition - 빌드 스크립트
이 스크립트는 React 프론트엔드를 빌드하고 PyInstaller를 사용하여 단일 실행 파일을 생성합니다.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json

def print_step(message):
    """빌드 단계를 표시하는 함수"""
    print(f"\n{'='*60}")
    print(f"🚀 {message}")
    print(f"{'='*60}")

def print_error(message):
    """에러 메시지를 표시하는 함수"""
    print(f"\n❌ 오류: {message}")
    sys.exit(1)

def print_success(message):
    """성공 메시지를 표시하는 함수"""
    print(f"✅ {message}")

def run_command(command, cwd=None, check=True):
    """명령어를 실행하고 결과를 반환"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"명령어 실행 실패: {command}")
        print(f"에러 코드: {e.returncode}")
        print(f"에러 메시지: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_requirements():
    """필수 도구들이 설치되어 있는지 확인"""
    print_step("필수 도구 확인")
    
    # Node.js 확인
    try:
        result = run_command("node --version", check=False)
        if result.returncode == 0:
            print_success(f"Node.js 설치됨: {result.stdout.strip()}")
        else:
            print_error("Node.js가 설치되어 있지 않습니다. https://nodejs.org에서 설치해주세요.")
    except:
        print_error("Node.js가 설치되어 있지 않습니다.")
    
    # npm 확인
    try:
        result = run_command("npm --version", check=False)
        if result.returncode == 0:
            print_success(f"npm 설치됨: {result.stdout.strip()}")
        else:
            print_error("npm이 설치되어 있지 않습니다.")
    except:
        print_error("npm이 설치되어 있지 않습니다.")
    
    # PyInstaller 확인
    try:
        result = run_command("pyinstaller --version", check=False)
        if result.returncode == 0:
            print_success(f"PyInstaller 설치됨: {result.stdout.strip()}")
        else:
            print("PyInstaller가 설치되어 있지 않습니다. 설치를 시도합니다...")
            run_command("pip install pyinstaller")
            print_success("PyInstaller 설치 완료")
    except:
        print("PyInstaller 설치를 시도합니다...")
        run_command("pip install pyinstaller")

def build_frontend():
    """React 프론트엔드를 빌드"""
    print_step("React 프론트엔드 빌드")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        print_error("frontend 디렉토리를 찾을 수 없습니다.")
    
    # package.json 확인
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print_error("package.json을 찾을 수 없습니다.")
    
    # node_modules가 없으면 npm install 실행
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("의존성 설치 중...")
        run_command("npm install", cwd=frontend_dir)
        print_success("의존성 설치 완료")
    
    # 기존 빌드 디렉토리 삭제
    dist_dir = frontend_dir / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("기존 빌드 디렉토리 삭제")
    
    # 프론트엔드 빌드
    print("프론트엔드 빌드 중...")
    run_command("npm run build", cwd=frontend_dir)
    
    if not dist_dir.exists():
        print_error("빌드가 실패했습니다. dist 디렉토리가 생성되지 않았습니다.")
    
    print_success("프론트엔드 빌드 완료")
    return dist_dir

def prepare_build_environment():
    """빌드 환경 준비"""
    print_step("빌드 환경 준비")
    
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # 기존 빌드 디렉토리 삭제
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    print_success("빌드 환경 준비 완료")

def build_executable():
    """PyInstaller를 사용하여 실행 파일 빌드"""
    print_step("실행 파일 빌드")
    
    project_root = Path(__file__).parent.parent
    spec_file = Path(__file__).parent / "build_exe.spec"
    
    if not spec_file.exists():
        print_error("build_exe.spec 파일을 찾을 수 없습니다.")
    
    # PyInstaller 실행
    print("실행 파일 생성 중... (시간이 오래 걸릴 수 있습니다)")
    run_command(f"pyinstaller --clean {spec_file}", cwd=project_root)
    
    # 생성된 실행 파일 확인
    exe_path = project_root / "dist" / "PDX_Mod_Translator_Pro.exe"
    if not exe_path.exists():
        print_error("실행 파일 생성에 실패했습니다.")
    
    print_success(f"실행 파일 생성 완료: {exe_path}")
    return exe_path

def create_version_info():
    """버전 정보 파일 생성"""
    print_step("버전 정보 생성")
    
    project_root = Path(__file__).parent.parent
    version_file = project_root / "version_info.txt"
    
    version_info = '''# UTF-8
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'PDX Mod Translator Team'),
           StringStruct('FileDescription', 'PDX Mod Translator Professional Edition'),
           StringStruct('FileVersion', '1.0.0'),
           StringStruct('InternalName', 'PDX_Mod_Translator_Pro'),
           StringStruct('LegalCopyright', '© 2025 PDX Mod Translator Team'),
           StringStruct('OriginalFilename', 'PDX_Mod_Translator_Pro.exe'),
           StringStruct('ProductName', 'PDX Mod Translator Professional'),
           StringStruct('ProductVersion', '1.0.0')])
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)'''
    
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print_success("버전 정보 파일 생성 완료")

def create_installer():
    """설치 프로그램 생성 (선택사항)"""
    print_step("설치 프로그램 생성 확인")
    
    try:
        # NSIS가 설치되어 있는지 확인
        result = run_command("makensis", check=False)
        if result.returncode != 0:  # NSIS가 없으면 0이 아닌 코드 반환
            print("NSIS가 설치되어 있지 않아 설치 프로그램을 생성하지 않습니다.")
            print("NSIS를 설치하면 설치 프로그램도 생성할 수 있습니다.")
            return
    except:
        print("NSIS가 설치되어 있지 않아 설치 프로그램을 생성하지 않습니다.")
        return
    
    # NSIS 스크립트 생성 및 실행
    # TODO: 필요하면 NSIS 스크립트 구현

def cleanup():
    """빌드 후 정리"""
    print_step("빌드 후 정리")
    
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    
    # 임시 빌드 디렉토리 삭제
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print_success("임시 파일 정리 완료")

def main():
    """메인 빌드 프로세스"""
    print("""
██████╗ ██████╗ ██╗  ██╗    ████████╗██████╗  █████╗ ███╗   ███╗███████╗
██╔══██╗██╔══██╗╚██╗██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗████╗ ████║██╔════╝
██████╔╝██║  ██║ ╚███╔╝        ██║   ██████╔╝███████║██╔████╔██║███████╗
██╔═══╝ ██║  ██║ ██╔██╗        ██║   ██╔══██╗██╔══██║██║╚██╔╝██║╚════██║
██║     ██████╔╝██╔╝ ██╗       ██║   ██║  ██║██║  ██║██║ ╚═╝ ██║███████║
╚═╝     ╚═════╝ ╚═╝  ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝
                                                                          
                        Professional Edition - 빌드 도구
                        """)
    
    try:
        # 1. 필수 도구 확인
        check_requirements()
        
        # 2. 버전 정보 생성
        create_version_info()
        
        # 3. 빌드 환경 준비
        prepare_build_environment()
        
        # 4. 프론트엔드 빌드
        frontend_dist = build_frontend()
        
        # 5. 실행 파일 빌드
        exe_path = build_executable()
        
        # 6. 설치 프로그램 생성 (선택사항)
        create_installer()
        
        # 7. 정리
        cleanup()
        
        # 완료 메시지
        print_step("빌드 완료!")
        print(f"""
✅ 빌드가 성공적으로 완료되었습니다!

📁 생성된 파일:
   - 실행 파일: {exe_path}
   - 크기: {exe_path.stat().st_size / (1024*1024):.1f} MB

🚀 사용 방법:
   1. {exe_path.name}를 원하는 위치에 복사하세요
   2. 실행 파일을 더블클릭하면 시스템 트레이에 아이콘이 나타납니다
   3. 트레이 아이콘을 클릭하여 웹 인터페이스를 열 수 있습니다
   4. 브라우저가 자동으로 열리고 번역 도구를 사용할 수 있습니다

📋 참고사항:
   - 첫 실행 시 Windows Defender에서 경고가 나올 수 있습니다
   - "추가 정보" -> "실행"을 클릭하여 실행하세요
   - 방화벽에서 localhost 접근을 허용해주세요
        """)
        
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 빌드가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()