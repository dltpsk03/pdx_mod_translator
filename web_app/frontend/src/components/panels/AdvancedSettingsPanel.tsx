import React from 'react'
import {
  Box,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Select,
  Switch,
  Text,
  Divider,
  SimpleGrid,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Alert,
  AlertIcon,
  AlertDescription,
  useColorModeValue
} from '@chakra-ui/react'
import { useAppStore } from '../../stores/appStore'

export const AdvancedSettingsPanel: React.FC = () => {
  const { config, updateConfig } = useAppStore()
  
  // 스타일 설정
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const inputBg = useColorModeValue('white', 'gray.600')
  
  // API Provider별 지원 매개변수 매핑
  const getParameterSupport = () => {
    const supportMap: Record<string, Record<string, boolean>> = {
      'gemini': {
        temperature: true,
        topP: true,
        topK: true,
        maxTokens: true
      },
      'claude': {
        temperature: true,
        topP: true,
        topK: false, // Claude doesn't support top_k
        maxTokens: true
      },
      'openai': {
        temperature: config.modelName?.includes('gpt-5') ? false : true, // GPT-5 계열은 지원 안함
        topP: config.modelName?.includes('gpt-5') ? false : true, // GPT-5 계열은 지원 안함  
        topK: false, // OpenAI는 top_k 지원 안함
        maxTokens: true
      }
    }
    
    return supportMap[config.apiProvider] || {
      temperature: false,
      topP: false, 
      topK: false,
      maxTokens: false
    }
  }
  
  return (
    <VStack spacing={8} align="stretch">
      {/* 경고 메시지 */}
      <Alert status="warning" borderRadius="lg">
        <AlertIcon />
        <AlertDescription>
          고급 설정은 번역 품질과 성능에 영향을 줄 수 있습니다. 
          변경하기 전에 각 옵션의 의미를 정확히 이해하고 사용하세요.
        </AlertDescription>
      </Alert>
      
      {/* 생성 매개변수 설정 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🎛️ AI 생성 매개변수
          </Text>
          
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
            <FormControl>
              <FormLabel fontWeight="medium">Temperature</FormLabel>
              <NumberInput
                value={config.temperature}
                onChange={(_, value) => updateConfig({ temperature: value || 0.7 })}
                min={0}
                max={2}
                step={0.1}
                precision={1}
                bg={inputBg}
                borderRadius="lg"
                isDisabled={getParameterSupport().temperature === false}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              <FormHelperText>
                {getParameterSupport().temperature ? 
                  "창의성 조절 (0.0: 일관성, 2.0: 창의성)" : 
                  `${config.apiProvider}는 temperature를 지원하지 않습니다`
                }
              </FormHelperText>
            </FormControl>

            <FormControl>
              <FormLabel fontWeight="medium">Top-P</FormLabel>
              <NumberInput
                value={config.topP}
                onChange={(_, value) => updateConfig({ topP: value || 0.9 })}
                min={0}
                max={1}
                step={0.05}
                precision={2}
                bg={inputBg}
                borderRadius="lg"
                isDisabled={getParameterSupport().topP === false}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              <FormHelperText>
                {getParameterSupport().topP ? 
                  "누적 확률 임계값 (0.1~1.0)" : 
                  `${config.apiProvider}는 top-p를 지원하지 않습니다`
                }
              </FormHelperText>
            </FormControl>

            <FormControl>
              <FormLabel fontWeight="medium">Top-K</FormLabel>
              <NumberInput
                value={config.topK}
                onChange={(_, value) => updateConfig({ topK: value || 40 })}
                min={1}
                max={100}
                step={1}
                bg={inputBg}
                borderRadius="lg"
                isDisabled={getParameterSupport().topK === false}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              <FormHelperText>
                {getParameterSupport().topK ? 
                  "고려할 상위 토큰 수 (1~100)" : 
                  `${config.apiProvider}는 top-k를 지원하지 않습니다`
                }
              </FormHelperText>
            </FormControl>
          </SimpleGrid>
        </VStack>
      </Box>

      {/* 성능 최적화 설정 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🚀 성능 최적화
          </Text>
          
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
            <FormControl>
              <FormLabel fontWeight="medium">분할 임계값</FormLabel>
              <NumberInput
                value={config.splitThreshold}
                onChange={(valueString) => updateConfig({ splitThreshold: parseInt(valueString) || 1000 })}
                min={100}
                max={5000}
              >
                <NumberInputField bg={inputBg} borderRadius="lg" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              <FormHelperText>
                이 길이를 초과하는 텍스트는 여러 부분으로 분할하여 처리합니다
              </FormHelperText>
            </FormControl>
            
            <FormControl>
              <FormLabel fontWeight="medium">최대 재시도 횟수</FormLabel>
              <NumberInput
                value={config.maxRetries}
                onChange={(valueString) => updateConfig({ maxRetries: parseInt(valueString) || 3 })}
                min={1}
                max={10}
              >
                <NumberInputField bg={inputBg} borderRadius="lg" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              <FormHelperText>
                번역 실패 시 최대 재시도 횟수
              </FormHelperText>
            </FormControl>
          </SimpleGrid>
          
          <FormControl>
            <FormLabel fontWeight="medium">검증 수준</FormLabel>
            <Select
              value={config.validationLevel}
              onChange={(e) => updateConfig({ validationLevel: e.target.value })}
              bg={inputBg}
              borderRadius="lg"
            >
              <option value="basic">기본 (Basic)</option>
              <option value="standard">표준 (Standard)</option>
              <option value="strict">엄격 (Strict)</option>
              <option value="custom">사용자 정의 (Custom)</option>
            </Select>
            <FormHelperText>
              번역 품질 검증 수준을 설정합니다. 높을수록 더 정확하지만 느려집니다.
            </FormHelperText>
          </FormControl>
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 번역 옵션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🔧 번역 옵션
          </Text>
          
          <VStack spacing={4} align="stretch">
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  언어 정의 파일 보존
                </FormLabel>
                <FormHelperText mt={1}>
                  _l_english.yml과 같은 언어 정의 파일을 변경하지 않고 유지합니다
                </FormHelperText>
              </Box>
              <Switch
                isChecked={config.keepLangDefUnchanged}
                onChange={(e) => updateConfig({ keepLangDefUnchanged: e.target.checked })}
                colorScheme="brand"
              />
            </FormControl>
            
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  내부 언어 코드 확인
                </FormLabel>
                <FormHelperText mt={1}>
                  파일 내부의 언어 코드를 확인하여 올바른 언어인지 검증합니다
                </FormHelperText>
              </Box>
              <Switch
                isChecked={config.checkInternalLang}
                onChange={(e) => updateConfig({ checkInternalLang: e.target.checked })}
                colorScheme="brand"
              />
            </FormControl>
            
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  이미 번역된 항목 건너뛰기
                </FormLabel>
                <FormHelperText mt={1}>
                  이미 번역된 것으로 확인되는 텍스트는 재번역하지 않습니다
                </FormHelperText>
              </Box>
              <Switch
                isChecked={config.skipAlreadyTranslated}
                onChange={(e) => updateConfig({ skipAlreadyTranslated: e.target.checked })}
                colorScheme="brand"
              />
            </FormControl>
            
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  자동 백업 생성
                </FormLabel>
                <FormHelperText mt={1}>
                  번역 시작 전에 원본 파일의 백업을 자동으로 생성합니다
                </FormHelperText>
              </Box>
              <Switch
                isChecked={config.enableBackup}
                onChange={(e) => updateConfig({ enableBackup: e.target.checked })}
                colorScheme="brand"
              />
            </FormControl>
          </VStack>
        </VStack>
      </Box>
      
      <Divider />
      
      
      {/* 디버깅 및 로깅 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🔍 디버깅 및 로깅
          </Text>
          
          <VStack spacing={4} align="stretch">
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  상세 로깅 활성화
                </FormLabel>
                <FormHelperText mt={1}>
                  더 자세한 번역 과정 로그를 출력합니다
                </FormHelperText>
              </Box>
              <Switch colorScheme="brand" />
            </FormControl>
            
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  API 요청/응답 로깅
                </FormLabel>
                <FormHelperText mt={1}>
                  API 호출 내용을 로그에 기록합니다 (디버깅용)
                </FormHelperText>
              </Box>
              <Switch colorScheme="brand" />
            </FormControl>
            
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <FormLabel mb={0} fontWeight="medium">
                  성능 메트릭 수집
                </FormLabel>
                <FormHelperText mt={1}>
                  번역 성능 통계를 수집하고 표시합니다
                </FormHelperText>
              </Box>
              <Switch colorScheme="brand" />
            </FormControl>
          </VStack>
          
          <FormControl>
            <FormLabel fontWeight="medium">로그 파일 경로</FormLabel>
            <Input
              placeholder="기본 경로 사용 (비워두면 자동 설정)"
              bg={inputBg}
              borderRadius="lg"
            />
            <FormHelperText>
              로그 파일을 저장할 경로 (비워두면 프로그램 폴더에 저장)
            </FormHelperText>
          </FormControl>
        </VStack>
      </Box>
    </VStack>
  )
}