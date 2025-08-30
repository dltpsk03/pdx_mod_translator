import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

// 타입 정의
export interface TranslationConfig {
  // UI 설정
  uiLanguage: string
  appearanceMode: 'light' | 'dark' | 'system'
  
  // API 설정
  apiProvider: string
  modelName: string
  apiKey: string
  
  // 번역 설정 (원본 파일과 동일한 11개 언어 지원)
  sourceLang: string
  targetLang: string
  batchSize: number
  maxWorkers: number
  delayBetweenBatches: number
  
  // 경로 설정
  inputFolder: string
  outputFolder: string
  
  // 고급 설정
  splitThreshold: number
  maxRetries: number
  validationLevel: string
  keepLangDefUnchanged: boolean
  checkInternalLang: boolean
  skipAlreadyTranslated: boolean
  enableBackup: boolean
  
  // 프롬프트 및 용어집
  promptTemplate: string
  glossaryFiles: Array<{ path: string; name: string; size: number }>
  selectedGame?: string
  
  // 생성 매개변수
  temperature: number
  topP: number
  topK: number
  maxTokens: number
}

export interface TranslationProgress {
  isRunning: boolean
  progress: number
  currentFile: string
  totalFiles: number
  completedFiles: number
  startTime?: Date
  estimatedTimeRemaining?: number
  speed?: number // files per second
}

export interface LogMessage {
  id: string
  timestamp: Date
  level: 'info' | 'warning' | 'error' | 'success'
  message: string
  details?: string
}

export interface ConnectionStatus {
  isConnected: boolean
  connectionStatus: string
  lastPingTime?: Date
  serverUrl: string
}

export interface AppState {
  // 연결 상태
  isConnected: boolean
  connectionStatus: string
  lastPingTime?: Date
  
  // API 연결 상태
  isApiConnected: boolean
  apiConnectionStatus: 'idle' | 'testing' | 'success' | 'error'
  apiConnectionMessage: string
  
  // 설정
  config: TranslationConfig
  
  // 번역 진행 상태
  progress: TranslationProgress
  
  // 로그
  logs: LogMessage[]
  maxLogs: number
  
  // UI 상태
  activeTab: string
  isConfigValid: boolean
  
  // Actions
  setConnectionStatus: (status: Partial<ConnectionStatus>) => void
  setApiConnectionStatus: (status: 'idle' | 'testing' | 'success' | 'error', message?: string) => void
  updateConfig: (updates: Partial<TranslationConfig>) => void
  setProgress: (progress: Partial<TranslationProgress>) => void
  addLog: (log: Omit<LogMessage, 'id' | 'timestamp'>) => void
  clearLogs: () => void
  setActiveTab: (tab: string) => void
  validateConfig: () => boolean
}

// 기본 설정값
const defaultConfig: TranslationConfig = {
  // UI 설정
  uiLanguage: 'ko',
  appearanceMode: 'system',
  
  // API 설정
  apiProvider: 'gemini',
  modelName: 'gemini-2.5-flash',
  apiKey: '',
  
  // 번역 설정
  sourceLang: 'English',
  targetLang: 'Korean',
  batchSize: 50,
  maxWorkers: 100,
  delayBetweenBatches: 0.8,
  
  // 경로 설정
  inputFolder: '',
  outputFolder: '',
  
  // 고급 설정
  splitThreshold: 1000,
  maxRetries: 3,
  validationLevel: 'standard',
  keepLangDefUnchanged: false,
  checkInternalLang: false,
  skipAlreadyTranslated: false,
  enableBackup: false,
  
  // 프롬프트 및 용어집
  promptTemplate: '',
  glossaryFiles: [],
  
  // 생성 매개변수 기본값
  temperature: 0.7,
  topP: 0.9,
  topK: 40,
  maxTokens: 65536
}

const defaultProgress: TranslationProgress = {
  isRunning: false,
  progress: 0,
  currentFile: '',
  totalFiles: 0,
  completedFiles: 0
}

// Zustand 스토어 생성
export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // 초기 상태
        isConnected: false,
        connectionStatus: '연결 중...',
        isApiConnected: false,
        apiConnectionStatus: 'idle' as const,
        apiConnectionMessage: '',
        config: defaultConfig,
        progress: defaultProgress,
        logs: [],
        maxLogs: 1000,
        activeTab: 'basic',
        isConfigValid: false,
        
        // Actions
        setConnectionStatus: (status) =>
          set((state) => ({
            ...state,
            isConnected: status.isConnected ?? state.isConnected,
            connectionStatus: status.connectionStatus ?? state.connectionStatus,
            lastPingTime: status.lastPingTime ?? state.lastPingTime,
          })),
        
        setApiConnectionStatus: (status, message = '') =>
          set((state) => {
            const isApiConnected = status === 'success'
            const isConfigValid = validateConfiguration(state.config, isApiConnected)
            
            console.log('setApiConnectionStatus called:', {
              status,
              message,
              isApiConnected,
              isConfigValid,
              currentConfig: state.config
            })
            
            return {
              ...state,
              isApiConnected,
              apiConnectionStatus: status,
              apiConnectionMessage: message,
              isConfigValid
            }
          }),
        
        updateConfig: (updates) =>
          set((state) => {
            const newConfig = { ...state.config, ...updates }
            // API 관련 설정이 변경되면 API 연결 상태 리셋
            let newApiState = state
            if (updates.apiProvider || updates.apiKey || updates.modelName) {
              newApiState = {
                ...state,
                isApiConnected: false,
                apiConnectionStatus: 'idle' as const,
                apiConnectionMessage: ''
              }
            }
            
            return {
              ...newApiState,
              config: newConfig,
              isConfigValid: validateConfiguration(newConfig, newApiState.isApiConnected)
            }
          }),
        
        setProgress: (progressUpdates) =>
          set((state) => ({
            ...state,
            progress: { ...state.progress, ...progressUpdates }
          })),
        
        addLog: (log) =>
          set((state) => {
            const newLog: LogMessage = {
              ...log,
              id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              timestamp: new Date()
            }
            
            const newLogs = [newLog, ...state.logs]
            
            // 최대 로그 수 제한
            if (newLogs.length > state.maxLogs) {
              newLogs.splice(state.maxLogs)
            }
            
            return { ...state, logs: newLogs }
          }),
        
        clearLogs: () =>
          set((state) => ({
            ...state,
            logs: []
          })),
        
        setActiveTab: (tab) =>
          set((state) => ({
            ...state,
            activeTab: tab
          })),
        
        validateConfig: () => {
          const state = get()
          const isValid = validateConfiguration(state.config, state.isApiConnected)
          set((s) => ({
            ...s,
            isConfigValid: isValid
          }))
          return isValid
        }
      }),
      {
        name: 'pdx-translator-store',
        partialize: (state) => ({
          config: state.config,
          activeTab: state.activeTab
        })
      }
    ),
    {
      name: 'PDX Translator Store'
    }
  )
)

// 설정 검증 함수
function validateConfiguration(config: TranslationConfig, isApiConnected: boolean = false): boolean {
  const hasBasicConfig = !!(
    config.apiProvider &&
    config.apiKey &&
    config.modelName &&
    config.sourceLang &&
    config.targetLang &&
    config.inputFolder
  )
  
  const result = hasBasicConfig && isApiConnected
  
  // 디버깅용
  console.log('validateConfiguration:', {
    hasBasicConfig,
    isApiConnected,
    result,
    config: {
      apiProvider: config.apiProvider,
      hasApiKey: !!config.apiKey,
      modelName: config.modelName,
      sourceLang: config.sourceLang,
      targetLang: config.targetLang
    }
  })
  
  return result
}

// 편의 함수들
export const useTranslationConfig = () => useAppStore((state) => state.config)
export const useTranslationProgress = () => useAppStore((state) => state.progress)
export const useLogs = () => useAppStore((state) => state.logs)
export const useConnectionStatus = () => useAppStore((state) => ({ 
  isConnected: state.isConnected, 
  status: state.connectionStatus 
}))