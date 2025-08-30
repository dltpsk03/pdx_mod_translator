import React, { useState } from 'react'
import {
  Box,
  HStack,
  VStack,
  Button,
  Progress,
  Text,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  SimpleGrid,
  Divider,
  IconButton,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertDescription,
  Tooltip,
  useDisclosure,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider
} from '@chakra-ui/react'
import {
  RepeatIcon,
  SettingsIcon,
  InfoIcon,
  ChevronDownIcon,
  ViewIcon,
  DownloadIcon,
  TimeIcon,
  TriangleUpIcon as PlayIcon,
  SmallCloseIcon as StopIcon
} from '@chakra-ui/icons'
import { useAppStore } from '../stores/appStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { TranslationDashboard } from './dashboard/TranslationDashboard'
import { ConsistencyChecker } from './consistency/ConsistencyChecker'
import { LivePreviewPanel } from './preview/LivePreviewPanel'
import { CheckpointManager } from './checkpoint/CheckpointManager'
import { StatisticsExporter } from './statistics/StatisticsExporter'

export const ControlPanel: React.FC = () => {
  const { 
    config, 
    progress, 
    isConnected, 
    connectionStatus,
    isConfigValid,
    isApiConnected,
    apiConnectionStatus,
    apiConnectionMessage
  } = useAppStore()
  
  // 디버깅용
  React.useEffect(() => {
    console.log('ControlPanel state:', {
      isConfigValid,
      isApiConnected,
      apiConnectionStatus,
      apiConnectionMessage,
      hasApiKey: !!config.apiKey,
      hasProvider: !!config.apiProvider,
      hasModel: !!config.modelName
    })
  }, [isConfigValid, isApiConnected, apiConnectionStatus, apiConnectionMessage, config.apiKey, config.apiProvider, config.modelName])
  
  const { sendMessage } = useWebSocket()
  
  // 고급 기능 모달 상태
  const [isDashboardOpen, setIsDashboardOpen] = useState(false)
  const [isConsistencyCheckerOpen, setIsConsistencyCheckerOpen] = useState(false)
  const [isLivePreviewEnabled, setIsLivePreviewEnabled] = useState(false)
  const [isCheckpointManagerOpen, setIsCheckpointManagerOpen] = useState(false)
  const [isStatisticsExporterOpen, setIsStatisticsExporterOpen] = useState(false)
  
  // 스타일 설정
  const panelBg = useColorModeValue('gray.50', 'gray.700')
  const statsBg = useColorModeValue('white', 'gray.800')
  
  // 번역 시작/중지 핸들러
  const handleStart = () => {
    if (!isConnected) {
      alert('서버에 연결되지 않았습니다. 연결을 확인해주세요.')
      return
    }
    
    if (!isConfigValid) {
      alert('설정이 완료되지 않았습니다. API 키와 필수 설정을 확인해주세요.')
      return
    }
    
    sendMessage({
      type: 'start_translation',
      config: config
    })
  }
  
  const handleStop = () => {
    sendMessage({
      type: 'stop_translation'
    })
  }
  
  const handlePause = () => {
    sendMessage({
      type: 'pause_translation'
    })
  }
  
  const handleReset = () => {
    if (confirm('번역 진행 상황을 초기화하시겠습니까?')) {
      sendMessage({
        type: 'reset_translation'
      })
    }
  }
  
  // 시간 포맷팅
  const formatTime = (seconds: number | undefined) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  
  // 경과 시간 계산
  const getElapsedTime = () => {
    if (!progress.startTime) return 0
    return (Date.now() - new Date(progress.startTime).getTime()) / 1000
  }
  
  // 진행률에 따른 색상
  const getProgressColor = () => {
    if (progress.progress < 30) return 'blue'
    if (progress.progress < 70) return 'yellow'
    return 'green'
  }
  
  // 속도 계산
  const getSpeed = () => {
    if (!progress.startTime || progress.completedFiles === 0) return 0
    const elapsedMinutes = getElapsedTime() / 60
    return progress.completedFiles / elapsedMinutes
  }
  
  return (
    <Box>
      <VStack spacing={6}>
        {/* 헤더 */}
        <HStack w="full" justify="space-between" px={6} pt={6}>
          <Text fontSize="xl" fontWeight="bold" color="brand.500">
            🎮 번역 컨트롤 패널
          </Text>
          <HStack>
            <Badge 
              colorScheme={isConnected ? 'green' : 'red'}
              variant="solid"
              px={3} 
              py={1}
              borderRadius="full"
            >
              {connectionStatus}
            </Badge>
            <Tooltip label="설정 확인">
              <IconButton
                aria-label="설정 확인"
                icon={<SettingsIcon />}
                size="sm"
                variant="ghost"
                colorScheme={isConfigValid ? 'green' : 'orange'}
              />
            </Tooltip>
          </HStack>
        </HStack>
        
        <Divider />
        
        {/* 설정 검증 알림 */}
        {!isConfigValid && (
          <Alert status="warning" borderRadius="lg" mx={6}>
            <AlertIcon />
            <AlertDescription>
              번역을 시작하기 전에 API 키와 필수 설정을 완료해주세요.
            </AlertDescription>
          </Alert>
        )}
        
        {/* 컨트롤 버튼 */}
        <HStack spacing={4} px={6}>
          <Button
            leftIcon={<PlayIcon />}
            colorScheme="green"
            size="lg"
            isDisabled={progress.isRunning || !isConnected || !isConfigValid}
            onClick={handleStart}
            flex={1}
          >
            번역 시작
          </Button>
          
          <Button
            leftIcon={<RepeatIcon />}
            colorScheme="yellow"
            variant="outline"
            size="lg"
            isDisabled={!progress.isRunning}
            onClick={handlePause}
            flex={1}
          >
            일시정지
          </Button>
          
          <Button
            leftIcon={<StopIcon />}
            colorScheme="red"
            variant="outline"
            size="lg"
            isDisabled={!progress.isRunning}
            onClick={handleStop}
            flex={1}
          >
            중지
          </Button>
          
          <IconButton
            aria-label="초기화"
            icon={<RepeatIcon />}
            size="lg"
            variant="outline"
            colorScheme="gray"
            isDisabled={progress.isRunning}
            onClick={handleReset}
          />
          
          {/* 고급 도구 메뉴 */}
          <Menu>
            <MenuButton
              as={Button}
              rightIcon={<ChevronDownIcon />}
              size="lg"
              variant="outline"
              colorScheme="blue"
            >
              고급 도구
            </MenuButton>
            <MenuList>
              <MenuItem
                icon={<InfoIcon />}
                onClick={() => setIsDashboardOpen(true)}
              >
                실시간 대시보드
              </MenuItem>
              <MenuItem
                icon={<ViewIcon />}
                onClick={() => setIsLivePreviewEnabled(!isLivePreviewEnabled)}
              >
                {isLivePreviewEnabled ? '미리보기 비활성화' : '실시간 미리보기'}
              </MenuItem>
              <MenuDivider />
              <MenuItem
                icon={<SettingsIcon />}
                onClick={() => setIsConsistencyCheckerOpen(true)}
              >
                용어 일관성 검사
              </MenuItem>
              <MenuItem
                icon={<TimeIcon />}
                onClick={() => setIsCheckpointManagerOpen(true)}
              >
                체크포인트 관리
              </MenuItem>
              <MenuDivider />
              <MenuItem
                icon={<DownloadIcon />}
                onClick={() => setIsStatisticsExporterOpen(true)}
              >
                통계 내보내기
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>
        
        {/* 진행률 표시 */}
        <Box w="full" px={6}>
          <VStack spacing={3}>
            <HStack w="full" justify="space-between">
              <Text fontSize="sm" fontWeight="medium">
                번역 진행률
              </Text>
              <Text fontSize="sm" color="gray.500">
                {progress.progress.toFixed(1)}%
              </Text>
            </HStack>
            
            <Progress
              value={progress.progress}
              size="lg"
              colorScheme={getProgressColor()}
              w="full"
              borderRadius="full"
              bg={useColorModeValue('gray.200', 'gray.600')}
            />
            
            <HStack w="full" justify="space-between" fontSize="sm" color="gray.500">
              <Text>
                {progress.completedFiles} / {progress.totalFiles} 파일
              </Text>
              <Text>
                현재: {progress.currentFile || '대기 중'}
              </Text>
            </HStack>
          </VStack>
        </Box>
        
        {/* 통계 정보 */}
        <Box w="full" px={6} pb={6}>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <Stat bg={statsBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>경과 시간</StatLabel>
              <StatNumber fontSize="lg">
                {formatTime(getElapsedTime())}
              </StatNumber>
              <StatHelpText>
                {progress.startTime ? '진행 중' : '대기'}
              </StatHelpText>
            </Stat>
            
            <Stat bg={statsBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>예상 남은 시간</StatLabel>
              <StatNumber fontSize="lg">
                {formatTime(progress.estimatedTimeRemaining)}
              </StatNumber>
              <StatHelpText>
                {progress.estimatedTimeRemaining ? '추정치' : '계산 중'}
              </StatHelpText>
            </Stat>
            
            <Stat bg={statsBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>번역 속도</StatLabel>
              <StatNumber fontSize="lg">
                {(progress.speed || getSpeed()).toFixed(1)}
              </StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                파일/분
              </StatHelpText>
            </Stat>
            
            <Stat bg={statsBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>상태</StatLabel>
              <StatNumber fontSize="lg">
                <Badge
                  colorScheme={
                    progress.isRunning ? 'green' : 
                    progress.progress > 0 ? 'yellow' : 'gray'
                  }
                  variant="solid"
                  px={2}
                  py={1}
                  borderRadius="md"
                >
                  {progress.isRunning ? '실행 중' : 
                   progress.progress > 0 ? '일시정지' : '대기'}
                </Badge>
              </StatNumber>
              <StatHelpText>
                현재 상태
              </StatHelpText>
            </Stat>
          </SimpleGrid>
        </Box>
        
        {/* 설정 요약 */}
        <Box w="full" px={6} pb={6}>
          <Box bg={panelBg} p={4} borderRadius="lg">
            <HStack justify="space-between" mb={3}>
              <Text fontWeight="medium">현재 설정</Text>
              <Tooltip label="설정 정보">
                <IconButton
                  aria-label="설정 정보"
                  icon={<InfoIcon />}
                  size="xs"
                  variant="ghost"
                />
              </Tooltip>
            </HStack>
            
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} fontSize="sm">
              <VStack align="start" spacing={1}>
                <Text color="gray.500">API 제공업체</Text>
                <Text fontWeight="medium">{config.apiProvider || '미설정'}</Text>
              </VStack>
              
              <VStack align="start" spacing={1}>
                <Text color="gray.500">모델</Text>
                <Text fontWeight="medium">{config.modelName || '미설정'}</Text>
              </VStack>
              
              <VStack align="start" spacing={1}>
                <Text color="gray.500">언어</Text>
                <Text fontWeight="medium">
                  {config.sourceLang} → {config.targetLang}
                </Text>
              </VStack>
              
              <VStack align="start" spacing={1}>
                <Text color="gray.500">배치 크기</Text>
                <Text fontWeight="medium">{config.batchSize} 항목</Text>
              </VStack>
            </SimpleGrid>
          </Box>
        </Box>
        
        {/* 실시간 미리보기 */}
        {isLivePreviewEnabled && (
          <Box w="full" px={6} pb={6}>
            <LivePreviewPanel 
              isEnabled={isLivePreviewEnabled}
              onToggle={() => setIsLivePreviewEnabled(!isLivePreviewEnabled)}
            />
          </Box>
        )}
      </VStack>
      
      {/* 고급 기능 모달들 */}
      <TranslationDashboard 
        isOpen={isDashboardOpen}
        onClose={() => setIsDashboardOpen(false)}
      />
      
      <ConsistencyChecker
        isOpen={isConsistencyCheckerOpen}
        onClose={() => setIsConsistencyCheckerOpen(false)}
      />
      
      {/* 체크포인트 관리자 모달 */}
      {isCheckpointManagerOpen && (
        <Box
          position="fixed"
          top="0"
          left="0"
          right="0"
          bottom="0"
          bg="blackAlpha.600"
          zIndex="1000"
          display="flex"
          alignItems="center"
          justifyContent="center"
          p={4}
        >
          <Box
            bg={useColorModeValue('white', 'gray.800')}
            borderRadius="xl"
            maxW="90vw"
            maxH="90vh"
            overflow="auto"
            p={6}
          >
            <HStack justify="space-between" mb={4}>
              <Text fontSize="lg" fontWeight="bold">체크포인트 관리자</Text>
              <IconButton
                aria-label="닫기"
                icon={<RepeatIcon />}
                onClick={() => setIsCheckpointManagerOpen(false)}
              />
            </HStack>
            <CheckpointManager />
          </Box>
        </Box>
      )}
      
      {/* 통계 내보내기 모달 */}
      {isStatisticsExporterOpen && (
        <Box
          position="fixed"
          top="0"
          left="0"
          right="0"
          bottom="0"
          bg="blackAlpha.600"
          zIndex="1000"
          display="flex"
          alignItems="center"
          justifyContent="center"
          p={4}
        >
          <Box
            bg={useColorModeValue('white', 'gray.800')}
            borderRadius="xl"
            maxW="90vw"
            maxH="90vh"
            overflow="auto"
            p={6}
          >
            <HStack justify="space-between" mb={4}>
              <Text fontSize="lg" fontWeight="bold">통계 내보내기</Text>
              <IconButton
                aria-label="닫기"
                icon={<RepeatIcon />}
                onClick={() => setIsStatisticsExporterOpen(false)}
              />
            </HStack>
            <StatisticsExporter />
          </Box>
        </Box>
      )}
    </Box>
  )
}