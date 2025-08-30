import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Switch,
  Text,
  Divider,
  SimpleGrid,
  Alert,
  AlertIcon,
  AlertDescription,
  Badge,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Textarea,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Tooltip
} from '@chakra-ui/react'
import { useAppStore } from '../../stores/appStore'

interface ErrorCorrectionSettings {
  validationLevel: 'off' | 'basic' | 'standard' | 'strict'
  autoActivationThreshold: number
  autoFix: {
    yamlSyntax: boolean
    paradoxFormat: boolean
    removeDuplicates: boolean
    fixIncomplete: boolean
  }
  duplicateStrategy: 'keep_first' | 'keep_last' | 'keep_longest' | 'keep_shortest'
  qualityThreshold: {
    minLengthRatio: number
    maxLengthRatio: number
  }
  performanceMode: boolean
  reportLevel: 'minimal' | 'detailed' | 'verbose'
}

export const ErrorCorrectionPanel: React.FC = () => {
  const { config, updateConfig } = useAppStore()
  
  // 오류 교정 설정 상태
  const [errorSettings, setErrorSettings] = useState<ErrorCorrectionSettings>({
    validationLevel: 'standard',
    autoActivationThreshold: 0.2,
    autoFix: {
      yamlSyntax: true,
      paradoxFormat: true,
      removeDuplicates: true,
      fixIncomplete: false
    },
    duplicateStrategy: 'keep_first',
    qualityThreshold: {
      minLengthRatio: 0.3,
      maxLengthRatio: 3.0
    },
    performanceMode: false,
    reportLevel: 'detailed'
  })
  
  // 통계 데이터
  const [errorStats, setErrorStats] = useState({
    totalErrors: 0,
    fixedErrors: 0,
    yamlErrors: 0,
    formatErrors: 0,
    duplicates: 0,
    qualityIssues: 0
  })
  
  // 스타일 설정
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const inputBg = useColorModeValue('white', 'gray.600')
  const statBg = useColorModeValue('white', 'gray.800')
  
  // 설정 업데이트 핸들러
  const updateErrorSettings = (updates: Partial<ErrorCorrectionSettings>) => {
    const newSettings = { ...errorSettings, ...updates }
    setErrorSettings(newSettings)
    
    // 메인 설정에 통합
    updateConfig({
      errorCorrectionSettings: newSettings
    } as any)
  }
  
  // 검증 수준별 설명
  const getValidationDescription = (level: string) => {
    switch (level) {
      case 'off':
        return '오류 검증을 사용하지 않습니다. 가장 빠르지만 품질이 보장되지 않습니다.'
      case 'basic':
        return '기본적인 YAML 문법 오류만 검사합니다. 빠른 처리가 가능합니다.'
      case 'standard':
        return '표준 검증으로 대부분의 오류를 감지하고 수정합니다. 권장 설정입니다.'
      case 'strict':
        return '엄격한 검증으로 모든 오류를 감지합니다. 처리 시간이 길어질 수 있습니다.'
      default:
        return ''
    }
  }
  
  // 중복 처리 전략 설명
  const getDuplicateStrategyDescription = (strategy: string) => {
    switch (strategy) {
      case 'keep_first':
        return '첫 번째로 발견된 번역을 유지합니다.'
      case 'keep_last':
        return '마지막으로 발견된 번역을 유지합니다.'
      case 'keep_longest':
        return '가장 긴 번역을 유지합니다.'
      case 'keep_shortest':
        return '가장 짧은 번역을 유지합니다.'
      default:
        return ''
    }
  }
  
  return (
    <VStack spacing={6} align="stretch">
      {/* 활성화 상태 표시 */}
      <Alert 
        status={errorSettings.validationLevel === 'off' ? 'warning' : 'info'} 
        borderRadius="lg"
      >
        <AlertIcon />
        <AlertDescription>
          {errorSettings.validationLevel === 'off' 
            ? '오류 교정이 비활성화되어 있습니다. 번역 품질이 보장되지 않을 수 있습니다.'
            : `${errorSettings.validationLevel} 수준의 오류 검증이 활성화되어 있습니다.`
          }
        </AlertDescription>
      </Alert>
      
      <Accordion allowMultiple defaultIndex={[0, 1]}>
        {/* 기본 설정 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">
                🔍 검증 및 교정 설정
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6} align="stretch">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl>
                  <FormLabel fontWeight="medium">검증 수준</FormLabel>
                  <Select
                    value={errorSettings.validationLevel}
                    onChange={(e) => updateErrorSettings({ 
                      validationLevel: e.target.value as any 
                    })}
                    bg={inputBg}
                    borderRadius="lg"
                  >
                    <option value="off">끄기 (Off)</option>
                    <option value="basic">기본 (Basic)</option>
                    <option value="standard">표준 (Standard)</option>
                    <option value="strict">엄격 (Strict)</option>
                  </Select>
                  <FormHelperText>
                    {getValidationDescription(errorSettings.validationLevel)}
                  </FormHelperText>
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">중복 처리 전략</FormLabel>
                  <Select
                    value={errorSettings.duplicateStrategy}
                    onChange={(e) => updateErrorSettings({ 
                      duplicateStrategy: e.target.value as any 
                    })}
                    bg={inputBg}
                    borderRadius="lg"
                  >
                    <option value="keep_first">첫 번째 유지</option>
                    <option value="keep_last">마지막 유지</option>
                    <option value="keep_longest">가장 긴 것 유지</option>
                    <option value="keep_shortest">가장 짧은 것 유지</option>
                  </Select>
                  <FormHelperText>
                    {getDuplicateStrategyDescription(errorSettings.duplicateStrategy)}
                  </FormHelperText>
                </FormControl>
              </SimpleGrid>
              
              <FormControl>
                <FormLabel fontWeight="medium">
                  자동 활성화 임계값: {(errorSettings.autoActivationThreshold * 100).toFixed(0)}%
                </FormLabel>
                <Slider
                  value={errorSettings.autoActivationThreshold}
                  onChange={(value) => updateErrorSettings({ autoActivationThreshold: value })}
                  min={0.05}
                  max={0.5}
                  step={0.05}
                  colorScheme="brand"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <Tooltip label={`${(errorSettings.autoActivationThreshold * 100).toFixed(0)}%`}>
                    <SliderThumb />
                  </Tooltip>
                </Slider>
                <FormHelperText>
                  오류율이 이 값을 초과하면 자동으로 더 엄격한 검증을 활성화합니다.
                </FormHelperText>
              </FormControl>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
        
        {/* 자동 수정 옵션 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">
                🔧 자동 수정 옵션
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={4} align="stretch">
              <FormControl display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <FormLabel mb={0} fontWeight="medium">
                    YAML 문법 오류 수정
                  </FormLabel>
                  <FormHelperText mt={1}>
                    잘못된 YAML 문법을 자동으로 감지하고 수정합니다
                  </FormHelperText>
                </Box>
                <Switch
                  isChecked={errorSettings.autoFix.yamlSyntax}
                  onChange={(e) => updateErrorSettings({
                    autoFix: {
                      ...errorSettings.autoFix,
                      yamlSyntax: e.target.checked
                    }
                  })}
                  colorScheme="brand"
                />
              </FormControl>
              
              <FormControl display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <FormLabel mb={0} fontWeight="medium">
                    Paradox 형식 보존
                  </FormLabel>
                  <FormHelperText mt={1}>
                    변수, 색상 태그, 아이콘 등 게임 형식을 보존합니다
                  </FormHelperText>
                </Box>
                <Switch
                  isChecked={errorSettings.autoFix.paradoxFormat}
                  onChange={(e) => updateErrorSettings({
                    autoFix: {
                      ...errorSettings.autoFix,
                      paradoxFormat: e.target.checked
                    }
                  })}
                  colorScheme="brand"
                />
              </FormControl>
              
              <FormControl display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <FormLabel mb={0} fontWeight="medium">
                    중복 항목 제거
                  </FormLabel>
                  <FormHelperText mt={1}>
                    동일한 키의 중복 번역을 자동으로 제거합니다
                  </FormHelperText>
                </Box>
                <Switch
                  isChecked={errorSettings.autoFix.removeDuplicates}
                  onChange={(e) => updateErrorSettings({
                    autoFix: {
                      ...errorSettings.autoFix,
                      removeDuplicates: e.target.checked
                    }
                  })}
                  colorScheme="brand"
                />
              </FormControl>
              
              <FormControl display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <FormLabel mb={0} fontWeight="medium">
                    불완전한 번역 수정
                  </FormLabel>
                  <FormHelperText mt={1}>
                    부분적으로만 번역된 텍스트를 재처리합니다 (시간이 걸림)
                  </FormHelperText>
                </Box>
                <Switch
                  isChecked={errorSettings.autoFix.fixIncomplete}
                  onChange={(e) => updateErrorSettings({
                    autoFix: {
                      ...errorSettings.autoFix,
                      fixIncomplete: e.target.checked
                    }
                  })}
                  colorScheme="brand"
                />
              </FormControl>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
        
        {/* 품질 임계값 설정 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">
                🎯 품질 임계값 설정
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6} align="stretch">
              <FormControl>
                <FormLabel fontWeight="medium">
                  최소 번역 길이 비율: {(errorSettings.qualityThreshold.minLengthRatio * 100).toFixed(0)}%
                </FormLabel>
                <Slider
                  value={errorSettings.qualityThreshold.minLengthRatio}
                  onChange={(value) => updateErrorSettings({
                    qualityThreshold: {
                      ...errorSettings.qualityThreshold,
                      minLengthRatio: value
                    }
                  })}
                  min={0.1}
                  max={0.8}
                  step={0.05}
                  colorScheme="green"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <Tooltip label={`${(errorSettings.qualityThreshold.minLengthRatio * 100).toFixed(0)}%`}>
                    <SliderThumb />
                  </Tooltip>
                </Slider>
                <FormHelperText>
                  원문 대비 번역문이 이 비율보다 짧으면 품질 문제로 간주합니다.
                </FormHelperText>
              </FormControl>
              
              <FormControl>
                <FormLabel fontWeight="medium">
                  최대 번역 길이 비율: {errorSettings.qualityThreshold.maxLengthRatio.toFixed(1)}배
                </FormLabel>
                <Slider
                  value={errorSettings.qualityThreshold.maxLengthRatio}
                  onChange={(value) => updateErrorSettings({
                    qualityThreshold: {
                      ...errorSettings.qualityThreshold,
                      maxLengthRatio: value
                    }
                  })}
                  min={2.0}
                  max={5.0}
                  step={0.1}
                  colorScheme="orange"
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <Tooltip label={`${errorSettings.qualityThreshold.maxLengthRatio.toFixed(1)}배`}>
                    <SliderThumb />
                  </Tooltip>
                </Slider>
                <FormHelperText>
                  원문 대비 번역문이 이 비율보다 길면 품질 문제로 간주합니다.
                </FormHelperText>
              </FormControl>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
        
        {/* 고급 설정 */}
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">
                ⚙️ 고급 설정
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={4} align="stretch">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <FormLabel mb={0} fontWeight="medium">
                      성능 우선 모드
                    </FormLabel>
                    <FormHelperText mt={1}>
                      속도를 위해 일부 검증을 생략합니다
                    </FormHelperText>
                  </Box>
                  <Switch
                    isChecked={errorSettings.performanceMode}
                    onChange={(e) => updateErrorSettings({ performanceMode: e.target.checked })}
                    colorScheme="brand"
                  />
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">리포트 수준</FormLabel>
                  <Select
                    value={errorSettings.reportLevel}
                    onChange={(e) => updateErrorSettings({ 
                      reportLevel: e.target.value as any 
                    })}
                    bg={inputBg}
                    borderRadius="lg"
                  >
                    <option value="minimal">최소</option>
                    <option value="detailed">상세</option>
                    <option value="verbose">매우 상세</option>
                  </Select>
                  <FormHelperText>
                    오류 리포트의 상세함 수준을 설정합니다
                  </FormHelperText>
                </FormControl>
              </SimpleGrid>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
      
      {/* 실시간 통계 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <Text fontSize="lg" fontWeight="semibold" color="brand.500" mb={4}>
          📊 오류 교정 통계
        </Text>
        
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
          <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
            <StatLabel>총 오류</StatLabel>
            <StatNumber color="red.500">{errorStats.totalErrors}</StatNumber>
            <StatHelpText>감지됨</StatHelpText>
          </Stat>
          
          <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
            <StatLabel>수정됨</StatLabel>
            <StatNumber color="green.500">{errorStats.fixedErrors}</StatNumber>
            <StatHelpText>자동 수정</StatHelpText>
          </Stat>
          
          <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
            <StatLabel>중복</StatLabel>
            <StatNumber color="orange.500">{errorStats.duplicates}</StatNumber>
            <StatHelpText>제거됨</StatHelpText>
          </Stat>
          
          <Stat bg={statBg} p={4} borderRadius="lg" textAlign="center">
            <StatLabel>품질 문제</StatLabel>
            <StatNumber color="blue.500">{errorStats.qualityIssues}</StatNumber>
            <StatHelpText>재처리됨</StatHelpText>
          </Stat>
        </SimpleGrid>
        
        {/* 성공률 표시 */}
        {errorStats.totalErrors > 0 && (
          <Box mt={4}>
            <HStack justify="space-between" mb={2}>
              <Text fontSize="sm" fontWeight="medium">수정 성공률</Text>
              <Badge colorScheme="green" px={2} py={1} borderRadius="full">
                {((errorStats.fixedErrors / errorStats.totalErrors) * 100).toFixed(1)}%
              </Badge>
            </HStack>
            <Progress
              value={(errorStats.fixedErrors / errorStats.totalErrors) * 100}
              colorScheme="green"
              size="lg"
              borderRadius="full"
            />
          </Box>
        )}
      </Box>
    </VStack>
  )
}