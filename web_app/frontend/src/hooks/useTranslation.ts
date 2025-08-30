import { useAppStore } from '../stores/appStore'

interface Translations {
  [key: string]: {
    ko: string
    en: string
  }
}

const translations: Translations = {
  // 헤더
  'header.title': {
    ko: 'PDX Mod Translator',
    en: 'PDX Mod Translator'
  },
  'header.subtitle': {
    ko: 'Professional Edition',
    en: 'Professional Edition'
  },
  'header.connected': {
    ko: '🟢 연결됨',
    en: '🟢 Connected'
  },
  'header.disconnected': {
    ko: '🔴 연결 끊김',
    en: '🔴 Disconnected'
  },
  'header.connecting': {
    ko: '연결 중...',
    en: 'Connecting...'
  },

  // 설정 모달
  'settings.title': {
    ko: '설정',
    en: 'Settings'
  },
  'settings.language.title': {
    ko: '🌍 언어 설정',
    en: '🌍 Language Settings'
  },
  'settings.language.interface': {
    ko: '인터페이스 언어',
    en: 'Interface Language'
  },
  'settings.theme.title': {
    ko: '🎨 테마 설정',
    en: '🎨 Theme Settings'
  },
  'settings.theme.app': {
    ko: '앱 테마',
    en: 'App Theme'
  },
  'settings.theme.light': {
    ko: '라이트 모드',
    en: 'Light Mode'
  },
  'settings.theme.dark': {
    ko: '다크 모드',
    en: 'Dark Mode'
  },
  'settings.theme.system': {
    ko: '🖥️ 시스템',
    en: '🖥️ System'
  },
  'settings.theme.description.system': {
    ko: '시스템 설정에 따라 자동으로 테마가 변경됩니다',
    en: 'Theme automatically changes based on system settings'
  },
  'settings.theme.description.light': {
    ko: '밝은 테마로 고정됩니다',
    en: 'Fixed to light theme'
  },
  'settings.theme.description.dark': {
    ko: '어두운 테마로 고정됩니다',
    en: 'Fixed to dark theme'
  },

  // 기본 설정 패널
  'basic.api.title': {
    ko: '🔧 API 설정',
    en: '🔧 API Settings'
  },
  'basic.api.provider': {
    ko: 'API 제공업체',
    en: 'API Provider'
  },
  'basic.api.provider.helper': {
    ko: '번역에 사용할 AI 서비스를 선택하세요',
    en: 'Select AI service to use for translation'
  },
  'basic.api.model': {
    ko: '모델명',
    en: 'Model Name'
  },
  'basic.api.model.helper': {
    ko: '사용할 AI 모델을 선택하세요',
    en: 'Select AI model to use'
  },
  'basic.api.key': {
    ko: 'API 키',
    en: 'API Key'
  },
  'basic.api.key.placeholder': {
    ko: 'API 키를 입력하세요',
    en: 'Enter your API key'
  },
  'basic.api.key.helper': {
    ko: '선택한 API 제공업체의 인증 키를 입력하세요. 키는 안전하게 저장됩니다.',
    en: 'Enter the authentication key for the selected API provider. Keys are stored securely.'
  },
  'basic.api.test': {
    ko: '연결 테스트',
    en: 'Test Connection'
  },
  'basic.api.testing': {
    ko: '확인 중',
    en: 'Testing'
  },

  // 언어 설정
  'basic.language.title': {
    ko: '🌍 언어 설정',
    en: '🌍 Language Settings'
  },
  'basic.language.source': {
    ko: '원본 언어',
    en: 'Source Language'
  },
  'basic.language.source.helper': {
    ko: 'MOD 파일의 원본 언어를 선택하세요',
    en: 'Select the original language of MOD files'
  },
  'basic.language.target': {
    ko: '번역 대상 언어',
    en: 'Target Language'
  },
  'basic.language.target.helper': {
    ko: '번역할 언어를 선택하세요',
    en: 'Select the language to translate to'
  },

  // 경로 설정
  'basic.path.title': {
    ko: '📁 경로 설정',
    en: '📁 Path Settings'
  },
  'basic.path.input': {
    ko: '입력 폴더',
    en: 'Input Folder'
  },
  'basic.path.input.placeholder': {
    ko: '번역할 MOD 파일이 있는 폴더를 선택하세요',
    en: 'Select folder containing MOD files to translate'
  },
  'basic.path.input.helper': {
    ko: '번역할 MOD의 localisation 폴더 또는 .yml/.txt 파일이 있는 폴더',
    en: 'Folder containing localisation files or .yml/.txt files of the MOD to translate'
  },
  'basic.path.output': {
    ko: '출력 폴더',
    en: 'Output Folder'
  },
  'basic.path.output.placeholder': {
    ko: '번역된 파일을 저장할 폴더를 선택하세요',
    en: 'Select folder to save translated files'
  },
  'basic.path.output.helper': {
    ko: '번역된 파일이 저장될 폴더 (비어있으면 입력 폴더와 동일)',
    en: 'Folder where translated files will be saved (same as input folder if empty)'
  },
  'basic.path.select': {
    ko: '선택',
    en: 'Select'
  },

  // 기본 성능 설정
  'basic.performance.title': {
    ko: '⚡ 기본 성능 설정',
    en: '⚡ Basic Performance Settings'
  },
  'basic.performance.batch': {
    ko: '배치 크기',
    en: 'Batch Size'
  },
  'basic.performance.batch.helper': {
    ko: '한 번에 처리할 번역 항목 수 (1-200)',
    en: 'Number of translation items to process at once (1-200)'
  },
  'basic.performance.workers': {
    ko: '최대 작업자 수',
    en: 'Max Workers'
  },
  'basic.performance.workers.helper': {
    ko: '동시에 실행할 번역 작업 수 (1-500)',
    en: 'Number of translation tasks to run simultaneously (1-500)'
  },
  'basic.performance.delay': {
    ko: '배치 간 지연 시간 (초)',
    en: 'Delay Between Batches (seconds)'
  },
  'basic.performance.delay.helper': {
    ko: 'API 제한을 피하기 위한 지연 시간',
    en: 'Delay time to avoid API limits'
  },
  'basic.performance.context': {
    ko: '컨텍스트 윈도우 크기',
    en: 'Context Window Size'
  },
  'basic.performance.context.helper': {
    ko: 'AI 모델이 한 번에 처리할 수 있는 최대 토큰 수',
    en: 'Maximum number of tokens the AI model can process at once'
  },

  // 버튼
  'button.show': {
    ko: 'API 키 보기',
    en: 'Show API Key'
  },
  'button.hide': {
    ko: 'API 키 숨기기',
    en: 'Hide API Key'
  }
}

export const useTranslation = () => {
  const { config } = useAppStore()
  const currentLanguage = config.uiLanguage || 'ko'
  
  const t = (key: string): string => {
    const translation = translations[key]
    if (!translation) {
      console.warn(`Translation missing for key: ${key}`)
      return key
    }
    return translation[currentLanguage as keyof typeof translation] || translation.ko || key
  }
  
  return { t, currentLanguage }
}