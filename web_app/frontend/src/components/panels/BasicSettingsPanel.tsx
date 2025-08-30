import React, { useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Select,
  Text,
  Button,
  Divider,
  SimpleGrid,
  InputGroup,
  InputRightElement,
  IconButton,
  useColorModeValue,
  Badge,
  Spinner
} from '@chakra-ui/react'
import { ViewIcon, ViewOffIcon, AddIcon, CheckIcon, WarningIcon } from '@chakra-ui/icons'
import { useAppStore } from '../../stores/appStore'
import { useTranslation } from '../../hooks/useTranslation'

export const BasicSettingsPanel: React.FC = () => {
  const { 
    config, 
    updateConfig, 
    setApiConnectionStatus,
    apiConnectionStatus,
    apiConnectionMessage
  } = useAppStore()
  const { t } = useTranslation()
  const [showApiKey, setShowApiKey] = useState(false)
  
  // 스타일 설정
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const inputBg = useColorModeValue('white', 'gray.600')
  
  // 폴더 선택 핸들러
  const handleFolderSelect = async (type: 'input' | 'output') => {
    try {
      const response = await fetch('/api/folder/select', {
        method: 'POST'
      })
      
      const result = await response.json()
      
      if (result.success && result.path) {
        if (type === 'input') {
          updateConfig({ inputFolder: result.path })
        } else {
          updateConfig({ outputFolder: result.path })
        }
      } else {
        console.log(result.message || '폴더 선택이 취소되었습니다.')
      }
    } catch (error) {
      console.error('폴더 선택 중 오류:', error)
      alert('폴더 선택 중 오류가 발생했습니다.')
    }
  }
  
  // API 키 연결 테스트 함수
  const testApiConnection = async () => {
    if (!config.apiProvider || !config.apiKey) {
      setApiConnectionStatus('error', 'API 제공업체와 키를 먼저 설정해주세요.')
      return
    }

    setApiConnectionStatus('testing', '연결을 확인하는 중...')

    try {
      const formData = new FormData()
      formData.append('api_key', config.apiKey)
      
      const response = await fetch(`/api/providers/${config.apiProvider}/test`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()

      if (result.success) {
        console.log('API test successful, updating status...')
        setApiConnectionStatus('success', result.message || '연결 성공')
        
        // 상태 업데이트 후 검증 함수도 호출
        setTimeout(() => {
          const { validateConfig } = useAppStore.getState()
          validateConfig()
        }, 100)
      } else {
        console.log('API test failed:', result.message)
        setApiConnectionStatus('error', result.message || '연결 실패')
      }
    } catch (error) {
      setApiConnectionStatus('error', '연결 테스트 중 오류가 발생했습니다.')
    }
  }
  
  // API provider가 변경될 때 연결 상태는 이미 updateConfig에서 리셋됨
  
  return (
    <VStack spacing={8} align="stretch">
      {/* API 설정 섹션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            {t('basic.api.title')}
          </Text>
          
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            <FormControl>
              <FormLabel fontWeight="medium">{t('basic.api.provider')}</FormLabel>
              <Select
                value={config.apiProvider}
                onChange={(e) => updateConfig({ apiProvider: e.target.value })}
                bg={inputBg}
                borderRadius="lg"
              >
                <option value="gemini">Google Gemini</option>
                <option value="claude">Anthropic Claude</option>
                <option value="openai">OpenAI</option>
              </Select>
              <FormHelperText>{t('basic.api.provider.helper')}</FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">모델명</FormLabel>
              <Select
                value={config.modelName}
                onChange={(e) => updateConfig({ modelName: e.target.value })}
                bg={inputBg}
                borderRadius="lg"
              >
                {config.apiProvider === 'gemini' && (
                  <>
                    <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                    <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                    <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash-Lite</option>
                    <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                    <option value="gemini-2.0-flash-lite">Gemini 2.0 Flash-Lite</option>
                  </>
                )}
                {config.apiProvider === 'claude' && (
                  <>
                    <option value="claude-opus-4-1-20250805">Claude Opus 4.1 (2025-08-05)</option>
                    <option value="claude-opus-4-20250514">Claude Opus 4 (2025-05-14)</option>
                    <option value="claude-sonnet-4-20250514">Claude Sonnet 4 (2025-05-14)</option>
                    <option value="claude-3-7-sonnet-latest">Claude 3.7 Sonnet (Latest)</option>
                    <option value="claude-3-5-haiku-latest">Claude 3.5 Haiku (Latest)</option>
                  </>
                )}
                {config.apiProvider === 'openai' && (
                  <>
                    <option value="gpt-5-2025-08-07">GPT-5</option>
                    <option value="gpt-5-mini-2025-08-07">GPT-5 Mini</option>
                    <option value="gpt-5-nano-2025-08-07">GPT-5 Nano</option>
                    <option value="gpt-4.1-2025-04-14">GPT-4.1</option>
                    <option value="o3-2025-04-16">O3</option>
                  </>
                )}
              </Select>
              <FormHelperText>사용할 AI 모델을 선택하세요</FormHelperText>
            </FormControl>
          </SimpleGrid>
          
          <FormControl>
            <HStack align="start" spacing={4}>
              <VStack flex={1} align="stretch" spacing={3}>
                <FormLabel fontWeight="medium">API 키</FormLabel>
                <InputGroup>
                  <Input
                    type={showApiKey ? 'text' : 'password'}
                    value={config.apiKey}
                    onChange={(e) => updateConfig({ apiKey: e.target.value })}
                    placeholder="API 키를 입력하세요"
                    bg={inputBg}
                    borderRadius="lg"
                  />
                  <InputRightElement>
                    <IconButton
                      aria-label={showApiKey ? "API 키 숨기기" : "API 키 보기"}
                      icon={showApiKey ? <ViewOffIcon /> : <ViewIcon />}
                      onClick={() => setShowApiKey(!showApiKey)}
                      variant="ghost"
                      size="sm"
                    />
                  </InputRightElement>
                </InputGroup>
                <FormHelperText>
                  선택한 API 제공업체의 인증 키를 입력하세요. 키는 안전하게 저장됩니다.
                </FormHelperText>
              </VStack>
              
              <VStack spacing={3} pt={8}>
                <Button
                  onClick={testApiConnection}
                  isDisabled={!config.apiKey || !config.apiProvider}
                  isLoading={apiConnectionStatus === 'testing'}
                  colorScheme={apiConnectionStatus === 'success' ? 'green' : 'blue'}
                  variant={apiConnectionStatus === 'success' ? 'solid' : 'outline'}
                  size="sm"
                  leftIcon={
                    apiConnectionStatus === 'testing' ? <Spinner size="sm" /> :
                    apiConnectionStatus === 'success' ? <CheckIcon /> :
                    apiConnectionStatus === 'error' ? <WarningIcon /> : undefined
                  }
                >
                  {apiConnectionStatus === 'testing' ? '확인 중' : '연결 테스트'}
                </Button>
                
                {apiConnectionStatus !== 'idle' && (
                  <Badge
                    colorScheme={
                      apiConnectionStatus === 'success' ? 'green' :
                      apiConnectionStatus === 'error' ? 'red' : 'blue'
                    }
                    variant="solid"
                    px={2}
                    py={1}
                    borderRadius="md"
                    textAlign="center"
                    fontSize="xs"
                  >
                    {apiConnectionMessage}
                  </Badge>
                )}
              </VStack>
            </HStack>
          </FormControl>
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 언어 설정 섹션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🌍 언어 설정
          </Text>
          
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            <FormControl>
              <FormLabel fontWeight="medium">원본 언어</FormLabel>
              <Select
                value={config.sourceLang}
                onChange={(e) => updateConfig({ sourceLang: e.target.value })}
                bg={inputBg}
                borderRadius="lg"
              >
                <option value="English">English</option>
                <option value="Korean">Korean</option>
                <option value="Simplified Chinese">Simplified Chinese</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Spanish">Spanish</option>
                <option value="Japanese">Japanese</option>
                <option value="Portuguese">Portuguese</option>
                <option value="Russian">Russian</option>
                <option value="Turkish">Turkish</option>
                <option value="Italian">Italian</option>
              </Select>
              <FormHelperText>MOD 파일의 원본 언어를 선택하세요</FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">번역 대상 언어</FormLabel>
              <Select
                value={config.targetLang}
                onChange={(e) => updateConfig({ targetLang: e.target.value })}
                bg={inputBg}
                borderRadius="lg"
              >
                <option value="Korean">Korean</option>
                <option value="English">English</option>
                <option value="Simplified Chinese">Simplified Chinese</option>
                <option value="French">French</option>
                <option value="German">German</option>
                <option value="Spanish">Spanish</option>
                <option value="Japanese">Japanese</option>
                <option value="Portuguese">Portuguese</option>
                <option value="Russian">Russian</option>
                <option value="Turkish">Turkish</option>
                <option value="Italian">Italian</option>
              </Select>
              <FormHelperText>번역할 언어를 선택하세요</FormHelperText>
            </FormControl>
          </SimpleGrid>
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 경로 설정 섹션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            📁 경로 설정
          </Text>
          
          <FormControl>
            <FormLabel fontWeight="medium">입력 폴더</FormLabel>
            <HStack>
              <Input
                value={config.inputFolder}
                onChange={(e) => updateConfig({ inputFolder: e.target.value })}
                placeholder="번역할 MOD 파일이 있는 폴더를 선택하세요"
                bg={inputBg}
                borderRadius="lg"
              />
              <Button
                leftIcon={<AddIcon />}
                onClick={() => handleFolderSelect('input')}
                colorScheme="brand"
                variant="outline"
                flexShrink={0}
              >
                선택
              </Button>
            </HStack>
            <FormHelperText>
              번역할 MOD의 localisation 폴더 또는 .yml/.txt 파일이 있는 폴더
            </FormHelperText>
          </FormControl>
          
          <FormControl>
            <FormLabel fontWeight="medium">출력 폴더</FormLabel>
            <HStack>
              <Input
                value={config.outputFolder}
                onChange={(e) => updateConfig({ outputFolder: e.target.value })}
                placeholder="번역된 파일을 저장할 폴더를 선택하세요"
                bg={inputBg}
                borderRadius="lg"
              />
              <Button
                leftIcon={<AddIcon />}
                onClick={() => handleFolderSelect('output')}
                colorScheme="brand"
                variant="outline"
                flexShrink={0}
              >
                선택
              </Button>
            </HStack>
            <FormHelperText>
              번역된 파일이 저장될 폴더 (비어있으면 입력 폴더와 동일)
            </FormHelperText>
          </FormControl>
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 기본 성능 설정 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            ⚡ 기본 성능 설정
          </Text>
          
          <SimpleGrid columns={{ base: 1, md: 2, lg: 2 }} spacing={6}>
            <FormControl>
              <FormLabel fontWeight="medium">배치 크기</FormLabel>
              <Input
                type="number"
                value={config.batchSize}
                onChange={(e) => updateConfig({ batchSize: parseInt(e.target.value) || 50 })}
                min={1}
                max={200}
                bg={inputBg}
                borderRadius="lg"
              />
              <FormHelperText>한 번에 처리할 번역 항목 수 (1-200)</FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">최대 작업자 수</FormLabel>
              <Input
                type="number"
                value={config.maxWorkers}
                onChange={(e) => updateConfig({ maxWorkers: parseInt(e.target.value) || 100 })}
                min={1}
                max={500}
                bg={inputBg}
                borderRadius="lg"
              />
              <FormHelperText>동시에 실행할 번역 작업 수 (1-500)</FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">배치 간 지연 시간 (초)</FormLabel>
              <Input
                type="number"
                step="0.1"
                value={config.delayBetweenBatches}
                onChange={(e) => updateConfig({ delayBetweenBatches: parseFloat(e.target.value) || 0.8 })}
                min={0}
                max={10}
                bg={inputBg}
                borderRadius="lg"
              />
              <FormHelperText>API 제한을 피하기 위한 지연 시간</FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">컨텍스트 윈도우 크기</FormLabel>
              <Input
                type="number"
                value={config.maxTokens}
                onChange={(e) => updateConfig({ maxTokens: parseInt(e.target.value) || 65536 })}
                min={1024}
                max={200000}
                step={1024}
                bg={inputBg}
                borderRadius="lg"
              />
              <FormHelperText>AI 모델이 한 번에 처리할 수 있는 최대 토큰 수</FormHelperText>
            </FormControl>
          </SimpleGrid>
        </VStack>
      </Box>
    </VStack>
  )
}