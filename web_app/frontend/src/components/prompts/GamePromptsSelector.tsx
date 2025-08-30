import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormHelperText,
  Select,
  Textarea,
  Text,
  Button,
  Alert,
  AlertIcon,
  AlertDescription,
  Badge,
  Divider,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  useColorModeValue,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Tooltip,
  IconButton,
  useToast
} from '@chakra-ui/react'
import { InfoIcon, CopyIcon, EditIcon, CheckIcon } from '@chakra-ui/icons'
import { useAppStore } from '../../stores/appStore'

// 게임별 전용 프롬프트 템플릿
const GAME_PROMPTS = {
  "None": {
    name: "일반 (게임 선택 안함)",
    description: "범용적인 번역 프롬프트입니다.",
    prompt: `다음 YML 형식의 텍스트를 '{source_lang_for_prompt}'에서 '{target_lang_for_prompt}'로 번역하세요.

{glossary_section}
반드시 다음 규칙을 엄격히 준수하세요:
1. 콜론(:) 뒤의 큰따옴표 안의 텍스트만 번역하세요. (예: key: "번역할 텍스트")
2. 키(key) 이름은 절대 변경하지 마세요.
3. YML 형식과 구조는 그대로 유지하세요.
4. 특수 문자나 변수는 그대로 보존하세요.`,
    features: ["기본적인 YML 구조 보존", "키 이름 보호", "특수 문자 보존"],
    complexity: "basic"
  },
  
  "Crusader Kings 3": {
    name: "Crusader Kings 3 (중세 대전략)",
    description: "중세 시대의 웅장하고 서사적인 톤을 사용하여 궁정 음모와 귀족 문화에 적합한 번역을 제공합니다.",
    prompt: `당신은 중세 대전략 게임 'Crusader Kings 3'의 텍스트를 번역하는 전문가입니다.
중세 귀족과 궁정 음모에 적합한 웅장하고 서사적인 톤을 사용하세요.

{glossary_section}

중요 규칙:
1. 대괄호 안의 게임 코드 [Concept|E], [Character.GetFirstName] 등은 절대 번역하거나 수정하지 마세요.
   예: "Your son, [Heir.GetFirstName], is a genius." -> "당신의 아들, [Heir.GetFirstName]은(는) 천재입니다."
2. 중세적 분위기를 유지하면서도 자연스러운 번역을 하세요.
3. 귀족 칭호와 궁정 용어는 한국 역사의 적절한 대응어를 사용하세요.
4. 종교적, 문화적 맥락을 고려하여 번역하세요.

다음 텍스트를 번역하세요:`,
    features: ["중세 궁정 톤", "게임 코드 보존", "역사적 맥락 고려", "귀족 칭호 적절한 번역"],
    complexity: "advanced"
  },
  
  "Hearts of Iron 4": {
    name: "Hearts of Iron 4 (2차대전 대전략)",
    description: "2차 대전 시기의 간결하고 전문적인 군사 보고서 스타일로 번역합니다.",
    prompt: `당신은 2차 대전 대전략 게임 'Hearts of Iron 4'의 텍스트를 번역하는 전문가입니다.
간결하고 전문적인 군사 보고서 스타일을 사용하세요.

{glossary_section}

중요 규칙:
1. £로 시작하는 아이콘 코드 (£GFX_army_experience, £pol_power 등)는 절대 번역하지 마세요.
   예: "You gained 50 £pol_power." -> "정치력 50 £pol_power을(를) 획득했습니다."
2. 군사 용어는 정확하고 공식적으로 번역하세요.
3. 국가명, 지명, 인명은 표준 한국어 표기를 따르세요.
4. 수치와 날짜는 정확히 보존하세요.
5. 간결하고 명확한 문체를 유지하세요.

다음 텍스트를 번역하세요:`,
    features: ["군사 보고서 스타일", "아이콘 코드 보존", "전문 군사 용어", "간결한 문체"],
    complexity: "advanced"
  },
  
  "Stellaris": {
    name: "Stellaris (SF 대전략)",
    description: "미래적이고 과학적인 용어를 사용하여 우주 탐험과 외교에 적합한 번역을 제공합니다.",
    prompt: `당신은 SF 대전략 게임 'Stellaris'의 텍스트를 번역하는 전문가입니다.
미래적이고 과학적인 용어와 우주 탐험 및 외교에 적합한 톤을 사용하세요.

{glossary_section}

중요 규칙:
1. 대괄호 코드 [species.GetName]과 변수 $PLANET_NAME$ 등을 정확히 보존하세요.
2. 과학기술 용어는 정확하고 미래적인 느낌을 유지하세요.
3. 외계 종족명과 행성명은 원음에 가깝게 표기하세요.
4. 정부 유형과 정책 용어는 일관성 있게 번역하세요.
5. SF적 상상력을 자극하는 문체를 사용하세요.

다음 텍스트를 번역하세요:`,
    features: ["미래적 과학 용어", "외계 문명 맥락", "변수 코드 보존", "SF적 상상력"],
    complexity: "advanced"
  },
  
  "Europa Universalis IV": {
    name: "Europa Universalis IV (근세 대전략)",
    description: "르네상스에서 계몽주의 시대에 적합한 정중한 외교적 언어를 사용합니다.",
    prompt: `당신은 근세 대전략 게임 'Europa Universalis IV' (1444-1821년)의 텍스트를 번역하는 전문가입니다.
르네상스에서 계몽주의 시대에 적합한 정중한 외교적 언어를 사용하세요.

{glossary_section}

중요 규칙:
1. 대괄호 [] 안의 게임 코드와 $ 기호 변수를 정확히 보존하세요.
2. 시대에 적절한 칭호와 계급, 정부 용어를 사용하세요.
3. 종교적 맥락과 문화적 차이를 고려하여 번역하세요.
4. 무역, 외교, 전쟁 관련 용어는 역사적 정확성을 유지하세요.
5. 격식있고 품위있는 문체를 사용하세요.

다음 텍스트를 번역하세요:`,
    features: ["근세 외교적 언어", "역사적 정확성", "종교적 맥락", "격식있는 문체"],
    complexity: "advanced"
  },
  
  "Victoria 3": {
    name: "Victoria 3 (산업혁명 대전략)",
    description: "19세기 산업혁명 시대의 정치 운동, 경제 시스템, 사회 개혁에 적합한 용어를 사용합니다.",
    prompt: `당신은 산업혁명 시대 대전략 게임 'Victoria 3' (19세기)의 텍스트를 번역하는 전문가입니다.
산업혁명 시대의 정치 운동, 경제 시스템, 사회 개혁에 적합한 용어를 사용하세요.

{glossary_section}

중요 규칙:
1. 대괄호 코드와 특수 기호를 변경하지 마세요.
2. 산업혁명 시대의 기술과 사회 개념을 적절히 번역하세요.
3. 정치 이데올로기와 경제 용어는 표준 번역을 따르세요.
4. 계급과 직업군은 19세기 맥락에 맞게 번역하세요.
5. 역사적 진정성과 명확성의 균형을 유지하세요.

다음 텍스트를 번역하세요:`,
    features: ["산업혁명 용어", "정치 이데올로기", "경제 시스템", "사회 개혁 맥락"],
    complexity: "advanced"
  },
  
  "Imperator: Rome": {
    name: "Imperator: Rome (고대 로마)",
    description: "고대 로마 공화정과 초기 제국 시대에 적합한 고전적이고 위엄있는 언어를 사용합니다.",
    prompt: `당신은 고대 대전략 게임 'Imperator: Rome'의 텍스트를 번역하는 전문가입니다.
로마 공화정과 초기 제국 시대에 적합한 고전적이고 위엄있는 언어를 사용하세요.

{glossary_section}

중요 규칙:
1. 대괄호 안의 게임 코드나 특수 마커를 번역하지 마세요.
2. 칭호와 개념에는 적절한 라틴어 유래 용어를 사용하세요.
3. 고대 정치 시스템과 군사 용어를 정확히 번역하세요.
4. 고전 고대의 문화적 맥락을 고려하세요.
5. 위엄있고 격조높은 문체를 유지하세요.

다음 텍스트를 번역하세요:`,
    features: ["고전적 위엄", "라틴어 유래 용어", "고대 정치 시스템", "문화적 맥락"],
    complexity: "advanced"
  }
}

export const GamePromptsSelector: React.FC = () => {
  const { config, updateConfig } = useAppStore()
  const [selectedGame, setSelectedGame] = useState<string>("None")
  const [customPrompt, setCustomPrompt] = useState<string>("")
  const [isCustomMode, setIsCustomMode] = useState(false)
  const toast = useToast()
  
  // 색상 테마
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  
  // 게임 선택 핸들러
  const handleGameSelection = (gameKey: string) => {
    setSelectedGame(gameKey)
    if (gameKey !== "None") {
      const gamePrompt = GAME_PROMPTS[gameKey as keyof typeof GAME_PROMPTS]
      updateConfig({
        selectedGame: gameKey,
        promptTemplate: gamePrompt.prompt
      } as any)
    } else {
      updateConfig({
        selectedGame: "None",
        promptTemplate: GAME_PROMPTS["None"].prompt
      } as any)
    }
    
    toast({
      title: "게임 프롬프트 적용됨",
      description: `${GAME_PROMPTS[gameKey as keyof typeof GAME_PROMPTS].name} 프롬프트가 적용되었습니다.`,
      status: "success",
      duration: 3000,
      isClosable: true,
    })
  }
  
  // 사용자 정의 프롬프트 적용
  const applyCustomPrompt = () => {
    if (customPrompt.trim()) {
      updateConfig({
        selectedGame: "Custom",
        promptTemplate: customPrompt
      } as any)
      
      toast({
        title: "사용자 정의 프롬프트 적용됨",
        description: "사용자가 작성한 프롬프트가 적용되었습니다.",
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    }
  }
  
  // 프롬프트 복사
  const copyPrompt = (prompt: string) => {
    navigator.clipboard.writeText(prompt)
    toast({
      title: "복사 완료",
      description: "프롬프트가 클립보드에 복사되었습니다.",
      status: "info",
      duration: 2000,
      isClosable: true,
    })
  }
  
  // 복잡도에 따른 색상
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'basic': return 'green'
      case 'advanced': return 'blue'
      default: return 'gray'
    }
  }
  
  return (
    <VStack spacing={8} align="stretch">
      {/* 안내 메시지 */}
      <Alert status="info" borderRadius="lg">
        <AlertIcon />
        <AlertDescription>
          각 Paradox 게임에 특화된 프롬프트 템플릿을 선택하세요. 
          게임별 고유한 형식과 용어를 보존하면서 더 정확한 번역을 제공합니다.
        </AlertDescription>
      </Alert>
      
      {/* 게임 선택 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            🎮 게임 선택
          </Text>
          
          <FormControl>
            <FormLabel fontWeight="medium">번역할 게임</FormLabel>
            <Select
              value={selectedGame}
              onChange={(e) => handleGameSelection(e.target.value)}
              size="lg"
              borderRadius="lg"
            >
              {Object.entries(GAME_PROMPTS).map(([key, game]) => (
                <option key={key} value={key}>
                  {game.name}
                </option>
              ))}
            </Select>
            <FormHelperText>
              선택한 게임에 최적화된 번역 프롬프트가 자동으로 적용됩니다.
            </FormHelperText>
          </FormControl>
          
          {selectedGame !== "None" && (
            <Card bg={cardBg} border="1px" borderColor={borderColor}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="md" fontWeight="semibold">
                      선택된 게임: {GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].name}
                    </Text>
                    <Badge 
                      colorScheme={getComplexityColor(GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].complexity)}
                      px={3} 
                      py={1}
                    >
                      {GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].complexity === 'basic' ? '기본' : '고급'}
                    </Badge>
                  </HStack>
                  
                  <Text fontSize="sm" color="gray.600">
                    {GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].description}
                  </Text>
                  
                  <Text fontSize="sm" fontWeight="medium" color="brand.500">
                    주요 특징:
                  </Text>
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={2}>
                    {GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].features.map((feature, index) => (
                      <HStack key={index} spacing={2}>
                        <CheckIcon color="green.500" boxSize={3} />
                        <Text fontSize="sm">{feature}</Text>
                      </HStack>
                    ))}
                  </SimpleGrid>
                  
                  <HStack>
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<CopyIcon />}
                      onClick={() => copyPrompt(GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].prompt)}
                    >
                      프롬프트 복사
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<EditIcon />}
                      onClick={() => {
                        setCustomPrompt(GAME_PROMPTS[selectedGame as keyof typeof GAME_PROMPTS].prompt)
                        setIsCustomMode(true)
                      }}
                    >
                      편집하기
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          )}
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 사용자 정의 프롬프트 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="lg" fontWeight="semibold" color="brand.500">
              ✏️ 사용자 정의 프롬프트
            </Text>
            <Button
              size="sm"
              variant={isCustomMode ? "solid" : "outline"}
              colorScheme="brand"
              onClick={() => setIsCustomMode(!isCustomMode)}
            >
              {isCustomMode ? "기본 모드" : "편집 모드"}
            </Button>
          </HStack>
          
          {isCustomMode && (
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel fontWeight="medium">사용자 정의 프롬프트</FormLabel>
                <Textarea
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="게임에 특화된 프롬프트를 직접 작성하세요..."
                  rows={15}
                  fontFamily="mono"
                  fontSize="sm"
                />
                <FormHelperText>
                  {'{source_lang_for_prompt}'}와 {'{target_lang_for_prompt}'}, {'{glossary_section}'}는 
                  자동으로 실제 값으로 대체됩니다.
                </FormHelperText>
              </FormControl>
              
              <HStack>
                <Button
                  colorScheme="brand"
                  onClick={applyCustomPrompt}
                  isDisabled={!customPrompt.trim()}
                >
                  사용자 정의 프롬프트 적용
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setCustomPrompt("")
                    setIsCustomMode(false)
                  }}
                >
                  취소
                </Button>
              </HStack>
            </VStack>
          )}
        </VStack>
      </Box>
      
      {/* 게임별 프롬프트 미리보기 */}
      <Accordion allowToggle>
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">
                📚 모든 게임 프롬프트 미리보기
              </Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              {Object.entries(GAME_PROMPTS).filter(([key]) => key !== "None").map(([key, game]) => (
                <Card key={key} bg={cardBg} border="1px" borderColor={borderColor}>
                  <CardHeader pb={2}>
                    <HStack justify="space-between">
                      <Text fontSize="md" fontWeight="semibold">
                        {game.name}
                      </Text>
                      <HStack>
                        <Badge colorScheme={getComplexityColor(game.complexity)}>
                          {game.complexity === 'basic' ? '기본' : '고급'}
                        </Badge>
                        <Tooltip label="프롬프트 복사">
                          <IconButton
                            aria-label="복사"
                            icon={<CopyIcon />}
                            size="xs"
                            variant="ghost"
                            onClick={() => copyPrompt(game.prompt)}
                          />
                        </Tooltip>
                      </HStack>
                    </HStack>
                  </CardHeader>
                  <CardBody pt={0}>
                    <VStack spacing={3} align="stretch">
                      <Text fontSize="xs" color="gray.600" noOfLines={2}>
                        {game.description}
                      </Text>
                      
                      <Box>
                        <Text fontSize="xs" fontWeight="medium" mb={1}>
                          주요 특징:
                        </Text>
                        {game.features.slice(0, 2).map((feature, index) => (
                          <Text key={index} fontSize="xs" color="gray.500">
                            • {feature}
                          </Text>
                        ))}
                        {game.features.length > 2 && (
                          <Text fontSize="xs" color="gray.400">
                            +{game.features.length - 2}개 더
                          </Text>
                        )}
                      </Box>
                      
                      <Button
                        size="sm"
                        colorScheme="brand"
                        variant="outline"
                        onClick={() => handleGameSelection(key)}
                      >
                        이 게임 선택
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
    </VStack>
  )
}