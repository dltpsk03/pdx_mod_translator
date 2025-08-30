import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '../stores/appStore'

interface WebSocketMessage {
  type: string
  level?: string
  message?: string
  progress?: number
  status?: string
  data?: any
  timestamp?: number
  // 백엔드에서 보내는 progress 메시지의 추가 필드들
  current_file?: string
  completed_files?: number
  total_files?: number
  eta_seconds?: number
  translation_speed?: number
  elapsed_time?: number
}

export const useWebSocket = (url: string = 'ws://localhost:8000/api/ws') => {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const baseReconnectDelay = 1000 // 1초

  const { 
    setConnectionStatus, 
    addLog, 
    setProgress,
    updateConfig
  } = useAppStore()

  // 연결 상태 업데이트
  const updateConnectionStatus = useCallback((isConnected: boolean, status: string) => {
    setConnectionStatus({
      isConnected,
      connectionStatus: status,
      lastPingTime: isConnected ? new Date() : undefined
    })
  }, [setConnectionStatus])

  // WebSocket 메시지 처리
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      switch (message.type) {
        case 'connected':
          updateConnectionStatus(true, '서버에 연결됨')
          reconnectAttempts.current = 0
          addLog({
            level: 'success',
            message: '서버에 성공적으로 연결되었습니다'
          })
          break
          
        case 'log':
          addLog({
            level: message.level as any || 'info',
            message: message.message || '',
            details: message.data?.details || 
              (message.data?.batch_count ? `배치 완료: ${message.data.batch_count}개 파일` : undefined)
          })
          break
          
        case 'progress':
          setProgress({
            progress: message.progress || 0,
            currentFile: message.current_file || message.data?.currentFile || '',
            totalFiles: message.total_files || message.data?.totalFiles || 0,
            completedFiles: message.completed_files || message.data?.completedFiles || 0,
            estimatedTimeRemaining: message.eta_seconds || message.data?.estimatedTime,
            speed: message.translation_speed || message.data?.speed
          })
          break
          
        case 'status':
          if (message.status === 'translation_started') {
            setProgress({
              isRunning: true,
              startTime: new Date(),
              progress: 0
            })
            addLog({
              level: 'info',
              message: '번역이 시작되었습니다'
            })
          } else if (message.status === 'translation_completed') {
            setProgress({
              isRunning: false,
              progress: 100
            })
            addLog({
              level: 'success',
              message: '번역이 완료되었습니다'
            })
          } else if (message.status === 'translation_stopped') {
            setProgress({
              isRunning: false
            })
            addLog({
              level: 'warning',
              message: '번역이 중지되었습니다'
            })
          } else if (message.status === 'translation_error') {
            setProgress({
              isRunning: false
            })
            addLog({
              level: 'error',
              message: `번역 중 오류 발생: ${message.data?.error || '알 수 없는 오류'}`
            })
          }
          break
          
        case 'config_updated':
          if (message.data) {
            updateConfig(message.data)
            addLog({
              level: 'info',
              message: '설정이 업데이트되었습니다'
            })
          }
          break
          
        default:
          console.log('Unknown WebSocket message type:', message.type)
          break
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
      addLog({
        level: 'error',
        message: 'WebSocket 메시지 파싱 오류'
      })
    }
  }, [updateConnectionStatus, addLog, setProgress, updateConfig])

  // WebSocket 연결 함수
  const connect = useCallback(() => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        return // 이미 연결됨
      }

      updateConnectionStatus(false, '서버 연결 시도 중...')
      
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        updateConnectionStatus(true, '서버에 연결됨')
        reconnectAttempts.current = 0
      }

      ws.onmessage = handleMessage

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        updateConnectionStatus(false, '서버 연결 끊어짐')
        
        // 정상적인 닫기가 아닌 경우 재연결 시도
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts.current)
          
          addLog({
            level: 'warning',
            message: `서버 연결이 끊어졌습니다. ${delay / 1000}초 후 재연결 시도... (${reconnectAttempts.current + 1}/${maxReconnectAttempts})`
          })
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          addLog({
            level: 'error',
            message: '서버 재연결에 실패했습니다. 수동으로 새로고침해주세요.'
          })
          updateConnectionStatus(false, '연결 실패 (최대 재시도 횟수 초과)')
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        updateConnectionStatus(false, '연결 오류')
        addLog({
          level: 'error',
          message: 'WebSocket 연결 오류가 발생했습니다'
        })
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      updateConnectionStatus(false, '연결 생성 실패')
      addLog({
        level: 'error',
        message: 'WebSocket 연결을 생성할 수 없습니다'
      })
    }
  }, [url, handleMessage, updateConnectionStatus, addLog])

  // WebSocket 연결 해제
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    
    updateConnectionStatus(false, '연결 해제됨')
  }, [updateConnectionStatus])

  // 수동 재연결
  const reconnect = useCallback(() => {
    disconnect()
    reconnectAttempts.current = 0
    setTimeout(connect, 1000)
  }, [disconnect, connect])

  // 메시지 전송
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    } else {
      addLog({
        level: 'warning',
        message: '서버에 연결되지 않아 메시지를 전송할 수 없습니다'
      })
      return false
    }
  }, [addLog])

  // 핑 전송 (연결 상태 확인)
  const sendPing = useCallback(() => {
    return sendMessage({ type: 'ping', timestamp: Date.now() })
  }, [sendMessage])

  // 컴포넌트 마운트 시 연결
  useEffect(() => {
    connect()
    
    // 주기적으로 핑 전송 (30초마다)
    const pingInterval = setInterval(() => {
      sendPing()
    }, 30000)

    // 클린업
    return () => {
      clearInterval(pingInterval)
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      disconnect()
    }
  }, [connect, disconnect, sendPing])

  // 페이지가 보이지 않을 때 연결 일시정지/재개
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 페이지가 숨겨지면 핑 중지
      } else {
        // 페이지가 다시 보이면 연결 확인
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          connect()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [connect])

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    reconnect,
    disconnect,
    sendMessage,
    sendPing
  }
}