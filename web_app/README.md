# PDX Mod Translator Professional Edition - Web Interface

Paradox Interactive 게임 (Europa Universalis, Hearts of Iron, Crusader Kings, Stellaris 등)의 MOD를 다양한 언어로 번역하는 도구의 웹 인터페이스 버전입니다.

## 🚀 주요 특징

### 하이브리드 아키텍처
- **단일 EXE 배포**: 사용자는 하나의 실행 파일만 실행하면 됩니다
- **웹 기반 UI**: 모던하고 직관적인 웹 인터페이스
- **로컬호스트 서버**: 네트워크 연결 없이 로컬에서 실행
- **시스템 트레이 통합**: 백그라운드에서 실행되며 트레이에서 관리

### 고급 번역 기능
- **다중 AI API 지원**: OpenAI, Anthropic, Google, DeepL, Azure OpenAI
- **실시간 진행상황**: WebSocket을 통한 실시간 로그 및 진행률 표시
- **배치 처리**: 대용량 파일도 효율적으로 처리
- **용어집 지원**: 일관된 번역을 위한 전용 용어집
- **스마트 재시도**: 오류 감지 및 자동 재처리

### 모던 UI/UX
- **다크/라이트 테마**: 시스템 설정에 따른 자동 테마 전환
- **반응형 디자인**: 다양한 화면 크기에 최적화
- **실시간 검증**: 설정 유효성을 실시간으로 확인
- **직관적 네비게이션**: 탭 기반의 체계적인 인터페이스

## 📁 프로젝트 구조

```
web_app/
├── backend/                 # FastAPI 백엔드
│   ├── main.py             # 메인 서버
│   ├── api_routes.py       # API 엔드포인트
│   └── websocket_handler.py # WebSocket 핸들러
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # React 컴포넌트
│   │   ├── stores/         # Zustand 상태 관리
│   │   ├── hooks/          # 커스텀 훅
│   │   └── theme.ts        # Chakra UI 테마
│   ├── package.json        # npm 의존성
│   └── vite.config.ts      # Vite 설정
├── launcher.py             # 시스템 트레이 런처
├── build.py               # 빌드 스크립트
├── build_exe.spec         # PyInstaller 설정
└── README.md              # 이 파일
```

## 🔧 개발 환경 설정

### 필수 요구사항
- Python 3.9+
- Node.js 16+
- npm 또는 yarn

### 백엔드 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 프론트엔드 설정

```bash
cd frontend
npm install
```

## 🚀 개발 실행

### 개발 모드 실행

1. 백엔드 서버 실행:
```bash
cd backend
python main.py
```

2. 프론트엔드 개발 서버 실행:
```bash
cd frontend
npm run dev
```

3. 브라우저에서 `http://localhost:5173` 접속

### 프로덕션 빌드

전체 애플리케이션을 단일 EXE로 빌드:

```bash
python build.py
```

빌드된 실행 파일은 `dist/PDX_Mod_Translator_Pro.exe`에 생성됩니다.

## 🏗️ 아키텍처 개요

### 백엔드 (FastAPI)
- **REST API**: 번역 작업 관리 및 설정
- **WebSocket**: 실시간 로그 및 진행 상황 스트리밍
- **파일 서빙**: React 빌드된 정적 파일 제공
- **기존 엔진 통합**: 기존 번역 엔진 재사용

### 프론트엔드 (React + TypeScript)
- **Chakra UI**: 모던 UI 컴포넌트 라이브러리
- **Zustand**: 경량 상태 관리
- **React Query**: 서버 상태 관리
- **Vite**: 빠른 개발 환경

### 런처 (Python + pystray)
- **시스템 트레이**: 백그라운드 실행 및 관리
- **자동 브라우저 열기**: 서버 시작 시 자동으로 웹 인터페이스 열기
- **포트 관리**: 사용 가능한 포트 자동 감지

## 🔌 API 엔드포인트

### REST API
- `GET /api/config` - 현재 설정 조회
- `POST /api/config` - 설정 업데이트
- `POST /api/translate/start` - 번역 시작
- `POST /api/translate/stop` - 번역 중지
- `GET /api/status` - 번역 상태 조회

### WebSocket
- `/api/ws` - 실시간 로그 및 진행 상황 스트리밍

## 🎯 사용 방법

### 기본 설정
1. **API 설정** 탭에서 사용할 AI 서비스의 API 키 설정
2. **언어 설정**에서 원본 언어와 번역 대상 언어 선택
3. **경로 설정**에서 입력 및 출력 폴더 지정

### 고급 설정
1. **성능 최적화**: 배치 크기, 작업자 수, 지연 시간 조정
2. **번역 옵션**: 언어 파일 보존, 중복 번역 건너뛰기 등
3. **품질 설정**: 검증 수준 및 정확도 설정

### 프롬프트 및 용어집
1. **프롬프트 템플릿**: AI에게 번역 방식을 안내하는 지침 작성
2. **용어집 관리**: 일관된 번역을위한 전용 용어 사전

## 🔒 보안 고려사항

- API 키는 로컬에만 저장되며 외부로 전송되지 않음
- 모든 통신은 localhost 내에서만 이루어짐
- 네트워크 연결 없이 완전히 오프라인으로 실행 가능

## 📈 성능 최적화

### 백엔드
- 비동기 처리로 동시 작업 지원
- 효율적인 배치 처리
- 메모리 사용량 최적화

### 프론트엔드
- 코드 분할 및 레이지 로딩
- 컴포넌트 메모이제이션
- 효율적인 상태 관리

### 빌드
- PyInstaller를 통한 단일 실행 파일
- 불필요한 의존성 제거
- UPX 압축으로 파일 크기 최적화

## 🐛 문제 해결

### 일반적인 문제

1. **포트 충돌**: 다른 애플리케이션이 포트를 사용 중인 경우 자동으로 다른 포트 선택
2. **방화벽 경고**: Windows에서 localhost 접근 허용 필요
3. **브라우저 호환성**: Chrome, Firefox, Edge 최신 버전 권장

### 빌드 문제

1. **Node.js 버전**: 16 이상 필요
2. **Python 의존성**: requirements.txt의 모든 패키지 설치 필요
3. **디스크 공간**: 빌드 시 최소 2GB 여유 공간 필요

## 🤝 기여하기

1. 이 리포지토리를 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👥 제작진

- **개발팀**: PDX Mod Translator Team
- **UI/UX**: Modern Web Technologies
- **번역 엔진**: Enhanced Translation Engine

## 📞 지원

- **이슈**: GitHub Issues 탭에서 버그 리포트 및 기능 요청
- **문서**: 이 README 파일 및 코드 내 주석 참조
- **커뮤니티**: Paradox 게임 모딩 커뮤니티

---

**Made with ❤️ for the Paradox Gaming Community**