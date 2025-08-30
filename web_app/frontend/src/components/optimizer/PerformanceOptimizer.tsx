import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Switch,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Progress,
  Alert,
  AlertIcon,
  AlertDescription,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Badge,
  Tooltip,
  Card,
  CardBody,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon
} from '@chakra-ui/react'
import { useAppStore } from '../../stores/appStore'

interface PerformanceSettings {
  enableCaching: boolean
  maxConcurrentRequests: number
  adaptiveBatching: boolean
  asyncProcessing: boolean
  maxMemoryUsageMB: number
  maxBatchSize: number
  maxFileSizeMB: number
  maxConcurrentFiles: number
  enableFastMode: boolean
  emergencyStopMemoryMB: number
  resourceMonitoring: boolean
  autoOptimization: boolean
  batchOptimizationLevel: 'conservative' | 'balanced' | 'aggressive'
  memoryCleanupInterval: number
}

export const PerformanceOptimizer: React.FC = () => {
  const { config, updateConfig } = useAppStore()
  
  const [performanceSettings, setPerformanceSettings] = useState<PerformanceSettings>({
    enableCaching: true,
    maxConcurrentRequests: 5,
    adaptiveBatching: true,
    asyncProcessing: true,
    maxMemoryUsageMB: 1024,
    maxBatchSize: 100,
    maxFileSizeMB: 100,
    maxConcurrentFiles: 10,
    enableFastMode: false,
    emergencyStopMemoryMB: 2048,
    resourceMonitoring: true,
    autoOptimization: false,
    batchOptimizationLevel: 'balanced',
    memoryCleanupInterval: 300
  })
  
  const [systemInfo, setSystemInfo] = useState({
    availableMemoryMB: 8192,
    cpuCores: 8,
    currentMemoryUsage: 45,
    networkLatency: 120,
    diskSpeed: 'SSD'
  })
  
  const [optimizationSuggestions, setOptimizationSuggestions] = useState<string[]>([])
  
  // 색상 테마
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const cardBg = useColorModeValue('white', 'gray.800')
  const statBg = useColorModeValue('white', 'gray.800')
  
  // 설정 업데이트
  const updatePerformanceSettings = (updates: Partial<PerformanceSettings>) => {
    const newSettings = { ...performanceSettings, ...updates }
    setPerformanceSettings(newSettings)
    
    // 메인 설정에 통합
    updateConfig({
      performanceSettings: newSettings
    } as any)
    
    // 최적화 제안 업데이트
    generateOptimizationSuggestions(newSettings)
  }
  
  // 최적화 제안 생성
  const generateOptimizationSuggestions = (settings: PerformanceSettings) => {
    const suggestions: string[] = []
    
    if (!settings.enableCaching) {
      suggestions.push("캐싱을 활성화하면 반복 번역 속도가 크게 향상됩니다.")
    }
    
    if (settings.maxConcurrentRequests < systemInfo.cpuCores / 2) {
      suggestions.push(`CPU 코어가 ${systemInfo.cpuCores}개인데 동시 요청 수가 적습니다. ${Math.floor(systemInfo.cpuCores / 2)}개 이상으로 설정해보세요.`)
    }
    
    if (settings.maxMemoryUsageMB > systemInfo.availableMemoryMB * 0.8) {
      suggestions.push("메모리 사용량이 너무 높습니다. 시스템 안정성을 위해 낮추는 것을 권장합니다.")
    }
    
    if (!settings.adaptiveBatching) {
      suggestions.push("적응형 배칭을 활성화하면 API 효율성이 향상됩니다.")
    }
    
    if (settings.batchOptimizationLevel === 'conservative' && systemInfo.networkLatency < 100) {
      suggestions.push("네트워크 지연이 낮으므로 배치 최적화 수준을 '균형' 또는 '공격적'으로 올릴 수 있습니다.")
    }
    
    setOptimizationSuggestions(suggestions)
  }
  
  // 자동 최적화
  const applyAutoOptimization = () => {
    const optimizedSettings: Partial<PerformanceSettings> = {}
    
    // CPU 기반 최적화
    optimizedSettings.maxConcurrentRequests = Math.min(systemInfo.cpuCores, 10)
    optimizedSettings.maxConcurrentFiles = Math.min(systemInfo.cpuCores * 2, 20)
    
    // 메모리 기반 최적화
    optimizedSettings.maxMemoryUsageMB = Math.floor(systemInfo.availableMemoryMB * 0.6)
    optimizedSettings.emergencyStopMemoryMB = Math.floor(systemInfo.availableMemoryMB * 0.8)
    
    // 네트워크 기반 최적화
    if (systemInfo.networkLatency < 100) {
      optimizedSettings.batchOptimizationLevel = 'aggressive'
      optimizedSettings.maxBatchSize = 150
    } else if (systemInfo.networkLatency < 200) {
      optimizedSettings.batchOptimizationLevel = 'balanced'
      optimizedSettings.maxBatchSize = 100
    } else {
      optimizedSettings.batchOptimizationLevel = 'conservative'
      optimizedSettings.maxBatchSize = 50
    }
    
    // 디스크 기반 최적화
    if (systemInfo.diskSpeed === 'SSD') {
      optimizedSettings.maxFileSizeMB = 200
    } else {
      optimizedSettings.maxFileSizeMB = 100
    }
    
    updatePerformanceSettings(optimizedSettings)
  }
  
  // 성능 점수 계산
  const calculatePerformanceScore = () => {
    let score = 0
    
    // 캐싱 (+20점)
    if (performanceSettings.enableCaching) score += 20
    
    // 적응형 배칭 (+15점)
    if (performanceSettings.adaptiveBatching) score += 15
    
    // 비동기 처리 (+15점)
    if (performanceSettings.asyncProcessing) score += 15
    
    // 동시 요청 수 최적화 (+20점)
    const optimalConcurrent = Math.floor(systemInfo.cpuCores / 2)
    if (performanceSettings.maxConcurrentRequests >= optimalConcurrent) score += 20
    
    // 메모리 사용률 (+15점)
    const memoryUsageRatio = performanceSettings.maxMemoryUsageMB / systemInfo.availableMemoryMB
    if (memoryUsageRatio > 0.3 && memoryUsageRatio < 0.7) score += 15
    
    // 리소스 모니터링 (+10점)
    if (performanceSettings.resourceMonitoring) score += 10
    
    // 빠른 모드 보너스 (+5점)
    if (performanceSettings.enableFastMode) score += 5
    
    return Math.min(score, 100)
  }
  
  const performanceScore = calculatePerformanceScore()
  
  // 설정 프리셋 적용
  const applyPreset = (preset: 'speed' | 'balanced' | 'quality') => {
    let presetSettings: Partial<PerformanceSettings> = {}
    
    switch (preset) {
      case 'speed':
        presetSettings = {
          enableFastMode: true,
          maxConcurrentRequests: Math.min(systemInfo.cpuCores * 2, 20),
          maxBatchSize: 200,
          batchOptimizationLevel: 'aggressive',
          asyncProcessing: true,
          adaptiveBatching: true,
          enableCaching: true
        }
        break
      case 'balanced':
        presetSettings = {
          enableFastMode: false,
          maxConcurrentRequests: Math.floor(systemInfo.cpuCores),
          maxBatchSize: 100,
          batchOptimizationLevel: 'balanced',
          asyncProcessing: true,
          adaptiveBatching: true,
          enableCaching: true
        }
        break
      case 'quality':
        presetSettings = {
          enableFastMode: false,
          maxConcurrentRequests: Math.max(2, Math.floor(systemInfo.cpuCores / 2)),
          maxBatchSize: 50,
          batchOptimizationLevel: 'conservative',
          asyncProcessing: true,
          adaptiveBatching: false,
          enableCaching: true
        }
        break
    }
    
    updatePerformanceSettings(presetSettings)
  }
  
  useEffect(() => {
    generateOptimizationSuggestions(performanceSettings)
  }, [])
  
  return (
    <VStack spacing={8} align="stretch">
      {/* 성능 개요 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={4}>
          <HStack justify="space-between" w="full">
            <Text fontSize="lg" fontWeight="semibold" color="brand.500">
              ⚡ 성능 최적화 개요
            </Text>
            <Badge 
              colorScheme={performanceScore >= 80 ? 'green' : performanceScore >= 60 ? 'yellow' : 'red'}
              fontSize="md" 
              px={3} 
              py={1}
            >
              성능 점수: {performanceScore}/100
            </Badge>
          </HStack>
          
          <Progress value={performanceScore} w="full" size="lg" colorScheme="brand" />
          
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} w="full">
            <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>사용 가능 메모리</StatLabel>
              <StatNumber fontSize="lg">{(systemInfo.availableMemoryMB / 1024).toFixed(1)}GB</StatNumber>
              <StatHelpText>총 시스템 메모리</StatHelpText>
            </Stat>
            
            <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>CPU 코어</StatLabel>
              <StatNumber fontSize="lg">{systemInfo.cpuCores}개</StatNumber>
              <StatHelpText>논리 프로세서</StatHelpText>
            </Stat>
            
            <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>네트워크 지연</StatLabel>
              <StatNumber fontSize="lg">{systemInfo.networkLatency}ms</StatNumber>
              <StatHelpText>평균 응답 시간</StatHelpText>
            </Stat>
            
            <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
              <StatLabel>저장소 타입</StatLabel>
              <StatNumber fontSize="lg">{systemInfo.diskSpeed}</StatNumber>
              <StatHelpText>디스크 성능</StatHelpText>
            </Stat>
          </SimpleGrid>
        </VStack>
      </Box>
      
      {/* 빠른 설정 프리셋 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={4}>
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🚀 빠른 설정 프리셋
          </Text>
          
          <HStack spacing={4} wrap="wrap" justify="center">
            <Card 
              as="button" 
              onClick={() => applyPreset('speed')} 
              cursor="pointer"
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              transition="all 0.2s"
              minW="150px"
            >
              <CardBody textAlign="center">
                <Text fontSize="xl" mb={2}>🏃‍♂️</Text>
                <Text fontWeight="bold">속도 우선</Text>
                <Text fontSize="sm" color="gray.500">빠른 번역</Text>
              </CardBody>
            </Card>
            
            <Card 
              as="button" 
              onClick={() => applyPreset('balanced')} 
              cursor="pointer"
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              transition="all 0.2s"
              minW="150px"
            >
              <CardBody textAlign="center">
                <Text fontSize="xl" mb={2}>⚖️</Text>
                <Text fontWeight="bold">균형</Text>
                <Text fontSize="sm" color="gray.500">속도와 품질 균형</Text>
              </CardBody>
            </Card>
            
            <Card 
              as="button" 
              onClick={() => applyPreset('quality')} 
              cursor="pointer"
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              transition="all 0.2s"
              minW="150px"
            >
              <CardBody textAlign="center">
                <Text fontSize="xl" mb={2}>💎</Text>
                <Text fontWeight="bold">품질 우선</Text>
                <Text fontSize="sm" color="gray.500">정확한 번역</Text>
              </CardBody>
            </Card>
            
            <Card 
              as="button" 
              onClick={applyAutoOptimization} 
              cursor="pointer"
              _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
              transition="all 0.2s"
              minW="150px"
            >
              <CardBody textAlign="center">
                <Text fontSize="xl" mb={2}>🤖</Text>
                <Text fontWeight="bold">자동 최적화</Text>
                <Text fontSize="sm" color="gray.500">시스템 기반</Text>
              </CardBody>
            </Card>
          </HStack>
        </VStack>
      </Box>
      
      {/* 최적화 제안 */}
      {optimizationSuggestions.length > 0 && (
        <Alert status="info" borderRadius="lg">
          <AlertIcon />
          <Box>
            <Text fontWeight="medium" mb={2}>💡 최적화 제안</Text>
            <VStack align="start" spacing={1}>
              {optimizationSuggestions.map((suggestion, index) => (
                <Text key={index} fontSize="sm">• {suggestion}</Text>
              ))}
            </VStack>
          </Box>
        </Alert>
      )}
      
      <Accordion allowMultiple defaultIndex={[0]}>
        {/* 핵심 성능 설정 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">🔥 핵심 성능 설정</Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6}>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="full">
                <FormControl>
                  <FormLabel fontWeight="medium">
                    최대 동시 요청 수: {performanceSettings.maxConcurrentRequests}
                  </FormLabel>
                  <Slider
                    value={performanceSettings.maxConcurrentRequests}
                    onChange={(value) => updatePerformanceSettings({ maxConcurrentRequests: value })}
                    min={1}
                    max={20}
                    step={1}
                    colorScheme="brand"
                  >
                    <SliderTrack><SliderFilledTrack /></SliderTrack>
                    <Tooltip label={`${performanceSettings.maxConcurrentRequests}개`}>
                      <SliderThumb />
                    </Tooltip>
                  </Slider>
                  <FormHelperText>
                    권장값: {Math.floor(systemInfo.cpuCores / 2)}-{systemInfo.cpuCores}개
                  </FormHelperText>
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">
                    최대 배치 크기: {performanceSettings.maxBatchSize}
                  </FormLabel>
                  <Slider
                    value={performanceSettings.maxBatchSize}
                    onChange={(value) => updatePerformanceSettings({ maxBatchSize: value })}
                    min={10}
                    max={200}
                    step={10}
                    colorScheme="green"
                  >
                    <SliderTrack><SliderFilledTrack /></SliderTrack>
                    <Tooltip label={`${performanceSettings.maxBatchSize}개`}>
                      <SliderThumb />
                    </Tooltip>
                  </Slider>
                  <FormHelperText>
                    한 번에 처리할 번역 항목 수
                  </FormHelperText>
                </FormControl>
              </SimpleGrid>
              
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="full">
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <FormLabel mb={0} fontWeight="medium">번역 캐시 활성화</FormLabel>
                    <FormHelperText>반복 번역 속도 향상</FormHelperText>
                  </Box>
                  <Switch
                    isChecked={performanceSettings.enableCaching}
                    onChange={(e) => updatePerformanceSettings({ enableCaching: e.target.checked })}
                    colorScheme="brand"
                  />
                </FormControl>
                
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <FormLabel mb={0} fontWeight="medium">적응형 배칭</FormLabel>
                    <FormHelperText>API 효율성 자동 조절</FormHelperText>
                  </Box>
                  <Switch
                    isChecked={performanceSettings.adaptiveBatching}
                    onChange={(e) => updatePerformanceSettings({ adaptiveBatching: e.target.checked })}
                    colorScheme="brand"
                  />
                </FormControl>
              </SimpleGrid>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
        
        {/* 메모리 및 리소스 관리 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">💾 메모리 및 리소스 관리</Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6}>
              <FormControl>
                <FormLabel fontWeight="medium">
                  최대 메모리 사용량: {performanceSettings.maxMemoryUsageMB}MB
                </FormLabel>
                <Slider
                  value={performanceSettings.maxMemoryUsageMB}
                  onChange={(value) => updatePerformanceSettings({ maxMemoryUsageMB: value })}
                  min={256}
                  max={Math.floor(systemInfo.availableMemoryMB * 0.8)}
                  step={128}
                  colorScheme="orange"
                >
                  <SliderTrack><SliderFilledTrack /></SliderTrack>
                  <Tooltip label={`${performanceSettings.maxMemoryUsageMB}MB`}>
                    <SliderThumb />
                  </Tooltip>
                </Slider>
                <FormHelperText>
                  사용률: {((performanceSettings.maxMemoryUsageMB / systemInfo.availableMemoryMB) * 100).toFixed(1)}%
                </FormHelperText>
              </FormControl>
              
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="full">
                <FormControl>
                  <FormLabel fontWeight="medium">메모리 정리 간격 (초)</FormLabel>
                  <NumberInput
                    value={performanceSettings.memoryCleanupInterval}
                    onChange={(_, value) => updatePerformanceSettings({ memoryCleanupInterval: value || 300 })}
                    min={60}
                    max={600}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">최대 파일 크기 (MB)</FormLabel>
                  <NumberInput
                    value={performanceSettings.maxFileSizeMB}
                    onChange={(_, value) => updatePerformanceSettings({ maxFileSizeMB: value || 100 })}
                    min={10}
                    max={500}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </SimpleGrid>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
        
        {/* 고급 최적화 옵션 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">⚙️ 고급 최적화 옵션</Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6}>
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="full">
                <FormControl>
                  <FormLabel fontWeight="medium">배치 최적화 수준</FormLabel>
                  <Select
                    value={performanceSettings.batchOptimizationLevel}
                    onChange={(e) => updatePerformanceSettings({ 
                      batchOptimizationLevel: e.target.value as any 
                    })}
                  >
                    <option value="conservative">보수적 (안정성 우선)</option>
                    <option value="balanced">균형 (속도와 안정성)</option>
                    <option value="aggressive">공격적 (속도 우선)</option>
                  </Select>
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">최대 동시 파일 처리</FormLabel>
                  <NumberInput
                    value={performanceSettings.maxConcurrentFiles}
                    onChange={(_, value) => updatePerformanceSettings({ maxConcurrentFiles: value || 10 })}
                    min={1}
                    max={50}
                  >
                    <NumberInputField />
                    <NumberInputStepper>
                      <NumberIncrementStepper />
                      <NumberDecrementStepper />
                    </NumberInputStepper>
                  </NumberInput>
                </FormControl>
              </SimpleGrid>
              
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6} w="full">
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <FormLabel mb={0} fontWeight="medium">빠른 모드</FormLabel>
                    <FormHelperText>일부 검증을 생략하여 속도 향상</FormHelperText>
                  </Box>
                  <Switch
                    isChecked={performanceSettings.enableFastMode}
                    onChange={(e) => updatePerformanceSettings({ enableFastMode: e.target.checked })}
                    colorScheme="red"
                  />
                </FormControl>
                
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <FormLabel mb={0} fontWeight="medium">리소스 모니터링</FormLabel>
                    <FormHelperText>실시간 성능 추적</FormHelperText>
                  </Box>
                  <Switch
                    isChecked={performanceSettings.resourceMonitoring}
                    onChange={(e) => updatePerformanceSettings({ resourceMonitoring: e.target.checked })}
                    colorScheme="blue"
                  />
                </FormControl>
              </SimpleGrid>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </VStack>
  )
}