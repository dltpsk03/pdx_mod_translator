# PDX Mod Translator

[English](README_EN.md) | [中文](README_ZH.md) | 한국어

Paradox 게임 모드 번역을 위한 강력한 GUI 애플리케이션입니다. Google Gemini API를 활용하여 YAML 현지화 파일을 효율적으로 번역합니다.

![UI 설정](asset/image%201%20-%20ui%20setting.png)

## 주요 기능

### 🌍 다국어 지원
- 실시간 UI 언어 전환
- 시스템 언어 자동 감지
- 한국어, 영어, 중국어 지원

### 🔧 고급 번역 기능
- **Google Gemini API 통합**: 고품질 AI 번역
- **배치 처리**: 대용량 파일을 청크 단위로 분할 처리
- **복구 시스템**: 체크포인트 기반 중단 번역 복구
- **품질 검증**: YAML 구문 검사 및 번역 품질 확인

### 🎮 게임별 최적화
- 각 Paradox 게임에 특화된 번역 프롬프트
- 게임별 용어집 지원
- Europa Universalis IV, Crusader Kings III, Hearts of Iron IV 등 지원

### 📊 분석 및 모니터링
- **실시간 미리보기**: 번역 진행 상황 실시간 확인
- **통계 대시보드**: 번역 분석 및 진행률 추적
- **일관성 검사기**: 번역 용어 일관성 검증

## 스크린샷

### API 설정
![API 설정](asset/image%202%20-%20API%20setting.png)

- 현재 5개의 API를 선택할 수 있습니다
- 2.5 Flash : 기본
- 2.0 Flash : 검열을 피하기 위한 선택
- 1.5 시리즈 : 비용이 부담될 때
- 2.5 Pro : 높은 품질을 원할 때 (매우 비싸고 제한이 빡빡함!!)

### 폴더 선택
![폴더 선택](asset/image%203%20-%20Floder%20Selection.png)

### 언어 설정
![언어 설정](asset/image%204%20-%20Language%20Setting.png)

- 현재 영어, 한국어, 중국어(간체), 프랑스어, 독일어, 스페인어, 포르투갈어, 일본어, 러시아어, 튀르키예어 지원중

### 번역 설정
![번역 설정](asset/image%205%20-%20Translation%20Setting.png)

- Batch Size: 한번에 몇 줄(line)을 번역할지
- Concurrent Files: 한번에 몇 개의 파일을 번역할지
- Max Output Tokens: 최대 토큰 수 제어 (2.5는 65536으로, 나머지는 8192로 설정)
- Delay Between Batch: 응답 사이의 시간 설정
- File Split Threshold: 긴 파일을 나눠서 번역하는 기능 (30000줄의 파일을 1000으로 설정하면 30개로 나눠서 번역함)
- Temparature: 얼마나 창의적인 대답을 원하는지 (0에 가까울수록 딱딱하고 2.0에 가까울수록 기상천외함)
- Max Retries: 번역중 Batch에 오류가 나면 재시도 하는데, 몇번까지 재시도할지

- Keep Original l_english identifier: 자신의 언어가 게임에서 미지원할 시 체크
- Prioritize UI setting .... : 번역하고자 하는 파일의 언어도 게임에서 미지원할지 체크. (예 : 유로파에서 중국어 -> 한국어 번역)
- Skip Already Translated Lines: 일부 번역된 모드를 번역할 때 사용

### 프롬프트 편집
![프롬프트 편집](asset/image%206%20-%20Edit%20Prompt.png)

### 용어집 관리
![용어집 관리](asset/image%207%20-%20glossary%20management.png)

### 제어 패널
![시작/정지 버튼](asset/image%208%20-%20start%20and%20stop%20button.png)

### 로그 패널
![로그 패널](asset/image%209%20-%20File%20Comparison%20Review%20Tool.png)

### 라이브 프리뷰 패널
![라이브 프리뷰 패널](asset/image%2010%20-%20File%20Comparison%20Review%20Tool%20Window.png)

## 설치 및 실행

### 필수 요구사항
```bash
pip install customtkinter google-generativeai
```

### 실행 방법
```bash
python "pdx translation tool/run_translator.py"
```

-혹은 Release에서 .EXE파일을 받아 실행

## 사용 방법

### 1. API 설정
- Google Gemini API 키 입력
- 사용할 모델 선택 (gemini-1.5-pro, gemini-1.5-flash 등)

### 2. 폴더 설정
- **입력 폴더**: 번역할 YAML 파일이 있는 폴더 선택
- **출력 폴더**: 번역된 파일을 저장할 폴더 선택

### 3. 언어 설정
- **소스 언어**: 원본 파일의 언어
- **대상 언어**: 번역할 언어

### 4. 고급 설정
- **배치 크기**: 한 번에 처리할 텍스트 양
- **동시 작업자 수**: 병렬 처리 스레드 수
- **재시도 횟수**: API 오류 시 재시도 횟수

### 5. 번역 실행
- "번역 시작" 버튼 클릭
- 실시간 진행 상황 모니터링
- 완료 후 결과 검토

## 아키텍처

### 핵심 구성요소

#### TranslatorEngine (`translator_app/core/translator_engine.py`)
- API 호출 및 파일 처리 담당
- 배치 번역 및 복구 메커니즘 구현

#### TranslationGUI (`translator_app/gui/main_window.py`)
- 메인 애플리케이션 창
- 모든 UI 패널 조율 및 애플리케이션 상태 관리

#### SettingsManager (`translator_app/core/settings_manager.py`)
- 설정 지속성 및 로딩 처리

### GUI 패널 구조

#### 설정 패널들 (`translator_app/gui/panels/`)
- `api_model_panel.py`: API 키 및 모델 선택
- `folder_panel.py`: 입력/출력 폴더 선택
- `translation_lang_panel.py`: 소스/대상 언어 설정
- `detailed_settings_panel.py`: 고급 번역 매개변수
- `prompt_glossary_panel.py`: 사용자 정의 프롬프트 및 용어집 관리
- `control_panel.py`: 번역 시작/정지 제어
- `log_panel.py`: 번역 진행 로깅
- `live_preview_panel.py`: 실시간 번역 미리보기

#### 도구 창들 (`translator_app/gui/windows/`)
- `translation_dashboard.py`: 번역 통계 및 분석
- `term_consistency_checker.py`: 번역 일관성 검증

## 번역 워크플로우

1. **파일 탐색**: 입력 폴더에서 YAML 파일 스캔 (.yml/.yaml)
2. **배치 처리**: 설정 가능한 임계값에 따라 대용량 파일 분할
3. **API 번역**: 사용자 정의 프롬프트 및 용어집과 함께 Google Gemini API 사용
4. **복구 시스템**: 중단된 번역을 위한 체크포인트 기반 복구
5. **품질 검증**: 내장 YAML 구문 검증 및 번역 품질 확인

## 주요 특징

### 🔄 멀티스레드 처리
- 설정 가능한 작업자 제한으로 동시 파일 처리

### 🎯 게임별 프롬프트
- 다양한 Paradox 게임을 위한 향상된 프롬프트

### 📚 용어집 지원
- 일관된 용어 사용을 위한 외부 용어집 파일

### 👀 라이브 미리보기
- 처리 중 실시간 번역 미리보기

### 📈 통계 대시보드
- 포괄적인 번역 분석

### 💾 백업 시스템
- 번역 전 선택적 파일 백업

## 설정 파일

- **메인 설정**: `translation_gui_config.json`
- **체크포인트 디렉토리**: `checkpoints/` (복구용)
- 애플리케이션 종료 시 설정 자동 저장

## 개발 정보

### 기술 스택
- **GUI**: CustomTkinter (모던 UI 스타일링)
- **API**: Google Generative AI
- **언어**: Python 3.7+
- **인코딩**: UTF-8-BOM (호환성)

### 언어 파일
- 위치: `translator_app/utils/localization.py`
- 자동 시스템 언어 감지 지원

### 기여하기
1. 이 저장소를 포크하세요
2. 기능 브랜치를 만드세요 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/AmazingFeature`)
5. Pull Request를 열어주세요

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 지원

문제가 발생하거나 기능 요청이 있으시면 GitHub Issues를 통해 알려주세요.

---

**즐거운 번역 되세요! 🎮🌍**
