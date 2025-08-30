import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Progress,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useColorModeValue,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Flex,
  Spacer,
  IconButton,
  Tooltip,
  Switch,
  FormControl,
  FormLabel,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Alert,
  AlertIcon,
  AlertDescription,
  Divider,
  Code,
  useToast
} from '@chakra-ui/react'
import { RepeatIcon, ViewIcon, DownloadIcon } from '@chakra-ui/icons'
import { FiActivity, FiClock, FiFileText, FiCheck } from 'react-icons/fi'
import axios from 'axios'

interface PreviewData {
  current_file: string
  source_lines: string[]
  translated_lines: string[]
  progress: number
  is_translating: boolean
  total_lines?: number
  completed_lines?: number
  estimated_time_remaining?: number
  translation_speed?: number
}

interface LivePreviewProps {
  inputFolder?: string
}

export const LivePreviewPanel: React.FC<LivePreviewProps> = ({
  inputFolder = ''
}) => {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [isAutoRefresh, setIsAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(2000)
  const [isLoading, setIsLoading] = useState(false)
  const intervalRef = useRef<number | null>(null)
  
  const toast = useToast()
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const statBg = useColorModeValue('gray.50', 'gray.700')
  const sourceBg = useColorModeValue('blue.50', 'blue.900')
  const translatedBg = useColorModeValue('green.50', 'green.900')

  useEffect(() => {
    fetchPreview()
    
    if (isAutoRefresh) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
    
    return () => stopAutoRefresh()
  }, [isAutoRefresh, refreshInterval])

  const fetchPreview = async () => {
    if (isLoading) return
    
    setIsLoading(true)
    try {
      const response = await axios.get('/api/preview/current')
      if (response.data.status === 'success') {
        setPreviewData(response.data.preview)
      }
    } catch (error) {
      // 조용히 실패 처리 (번역이 진행중이 아닐 수 있음)
    } finally {
      setIsLoading(false)
    }
  }

  const startAutoRefresh = () => {
    stopAutoRefresh()
    intervalRef.current = setInterval(fetchPreview, refreshInterval)
  }

  const stopAutoRefresh = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const toggleAutoRefresh = () => {
    setIsAutoRefresh(!isAutoRefresh)
  }

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(0)}초`
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}분`
    return `${(seconds / 3600).toFixed(1)}시간`
  }

  const getPreviewStats = () => {
    if (!previewData) {
      return {
        progress: 0,
        totalLines: 0,
        completedLines: 0,
        remainingTime: 0,
        speed: 0
      }
    }

    return {
      progress: previewData.progress || 0,
      totalLines: previewData.total_lines || 0,
      completedLines: previewData.completed_lines || 0,
      remainingTime: previewData.estimated_time_remaining || 0,
      speed: previewData.translation_speed || 0
    }
  }

  const stats = getPreviewStats()

  return (
    <Box p={6} w="100%">
      <VStack spacing={6} align="stretch">
        {/* 헤더 */}
        <Flex justify="space-between" align="center">
          <Heading size="lg" color="brand.500">
            👁️ 실시간 번역 미리보기
          </Heading>
          <HStack spacing={2}>
            <FormControl display="flex" alignItems="center">
              <FormLabel htmlFor="auto-refresh" mb={0} fontSize="sm">
                자동 새로고침
              </FormLabel>
              <Switch
                id="auto-refresh"
                isChecked={isAutoRefresh}
                onChange={toggleAutoRefresh}
                colorScheme="brand"
              />
            </FormControl>
            <Divider orientation="vertical" h={6} />
            <Tooltip label="수동 새로고침">
              <IconButton
                aria-label="새로고침"
                icon={<RepeatIcon />}
                onClick={fetchPreview}
                isLoading={isLoading}
                size="sm"
                variant="outline"
              />
            </Tooltip>
          </HStack>
        </Flex>

        {/* 번역 상태 알림 */}
        {!previewData?.is_translating ? (
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            <AlertDescription>
              현재 번역이 진행되지 않고 있습니다. 번역을 시작하면 여기에서 실시간으로 확인할 수 있습니다.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert status="success" borderRadius="lg">
            <AlertIcon />
            <AlertDescription>
              번역이 진행 중입니다. 실시간으로 번역 상황을 확인하세요.
            </AlertDescription>
          </Alert>
        )}

        {/* 번역 통계 카드 */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    전체 진행률
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                    {stats.progress.toFixed(1)}%
                  </Text>
                </VStack>
                <FiActivity size={32} color="#3182CE" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    처리된 라인
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.completedLines.toLocaleString()}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    / {stats.totalLines.toLocaleString()}
                  </Text>
                </VStack>
                <FiCheck size={32} color="#38A169" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    남은 시간
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                    {stats.remainingTime > 0 ? formatTime(stats.remainingTime) : '--'}
                  </Text>
                </VStack>
                <FiClock size={32} color="#805AD5" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    번역 속도
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                    {stats.speed.toFixed(1)}
                  </Text>
                  <Text fontSize="xs" color="gray.500">라인/분</Text>
                </VStack>
                <FiFileText size={32} color="#DD6B20" />
              </HStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* 현재 파일 정보 */}
        {previewData?.current_file && (
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">📄 현재 번역 중인 파일</Heading>
                <Badge colorScheme="blue" fontSize="sm" px={3} py={1}>
                  진행 중
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <HStack>
                  <Text fontSize="sm" color="gray.500" minW="80px">파일명:</Text>
                  <Code fontSize="sm" px={2} py={1} borderRadius="md">
                    {previewData.current_file}
                  </Code>
                </HStack>
                
                <Box>
                  <HStack justify="space-between" mb={2}>
                    <Text fontSize="sm" fontWeight="medium">파일 진행률</Text>
                    <Text fontSize="sm" color="gray.500">
                      {stats.completedLines} / {stats.totalLines} 라인
                    </Text>
                  </HStack>
                  <Progress
                    value={stats.progress}
                    size="lg"
                    colorScheme="brand"
                    borderRadius="full"
                    hasStripe
                    isAnimated={previewData.is_translating}
                  />
                </Box>
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* 번역 미리보기 */}
        {previewData?.source_lines && previewData.source_lines.length > 0 && (
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">🔄 최근 번역 내용</Heading>
                <Badge colorScheme="green" fontSize="sm" px={3} py={1}>
                  실시간
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Text fontSize="sm" color="gray.600" mb={2}>
                  최근 번역된 {Math.min(previewData.source_lines.length, 10)}줄을 보여줍니다.
                </Text>
                
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th width="50%" bg={sourceBg}>원문</Th>
                      <Th width="50%" bg={translatedBg}>번역</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {previewData.source_lines.slice(-10).map((sourceLine, index) => {
                      const translatedLine = previewData.translated_lines[
                        previewData.translated_lines.length - 10 + index
                      ] || '번역 중...'
                      
                      return (
                        <Tr key={index}>
                          <Td 
                            bg={sourceBg} 
                            verticalAlign="top"
                            maxW="0" 
                            overflow="hidden" 
                            textOverflow="ellipsis"
                            whiteSpace="nowrap"
                          >
                            <Tooltip label={sourceLine}>
                              <Text fontSize="sm">{sourceLine}</Text>
                            </Tooltip>
                          </Td>
                          <Td 
                            bg={translatedBg} 
                            verticalAlign="top"
                            maxW="0" 
                            overflow="hidden" 
                            textOverflow="ellipsis"
                            whiteSpace="nowrap"
                          >
                            <Tooltip label={translatedLine}>
                              <Text fontSize="sm">{translatedLine}</Text>
                            </Tooltip>
                          </Td>
                        </Tr>
                      )
                    })}
                  </Tbody>
                </Table>
                
                {previewData.source_lines.length > 10 && (
                  <Text fontSize="xs" color="gray.500" textAlign="center">
                    총 {previewData.source_lines.length}줄 중 최근 10줄만 표시됩니다.
                  </Text>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* 미리보기 설정 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">⚙️ 미리보기 설정</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
              <FormControl>
                <FormLabel fontSize="sm" fontWeight="medium">새로고침 간격</FormLabel>
                <HStack>
                  <Button
                    size="sm"
                    variant={refreshInterval === 1000 ? 'solid' : 'outline'}
                    onClick={() => setRefreshInterval(1000)}
                    colorScheme="brand"
                  >
                    1초
                  </Button>
                  <Button
                    size="sm"
                    variant={refreshInterval === 2000 ? 'solid' : 'outline'}
                    onClick={() => setRefreshInterval(2000)}
                    colorScheme="brand"
                  >
                    2초
                  </Button>
                  <Button
                    size="sm"
                    variant={refreshInterval === 5000 ? 'solid' : 'outline'}
                    onClick={() => setRefreshInterval(5000)}
                    colorScheme="brand"
                  >
                    5초
                  </Button>
                  <Button
                    size="sm"
                    variant={refreshInterval === 10000 ? 'solid' : 'outline'}
                    onClick={() => setRefreshInterval(10000)}
                    colorScheme="brand"
                  >
                    10초
                  </Button>
                </HStack>
              </FormControl>
              
              <VStack align="start" spacing={2}>
                <Text fontSize="sm" fontWeight="medium" color="gray.600">
                  상태 정보
                </Text>
                <HStack>
                  <Badge colorScheme={isAutoRefresh ? 'green' : 'gray'}>
                    {isAutoRefresh ? '자동 새로고침 활성' : '수동 모드'}
                  </Badge>
                  {previewData?.is_translating && (
                    <Badge colorScheme="blue" variant="outline">
                      번역 진행 중
                    </Badge>
                  )}
                </HStack>
                <Text fontSize="xs" color="gray.500">
                  마지막 업데이트: {new Date().toLocaleTimeString('ko-KR')}
                </Text>
              </VStack>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* 도움말 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack align="start" spacing={3}>
              <HStack>
                <ViewIcon color="blue.500" />
                <Heading size="sm" color="blue.500">라이브 미리보기 가이드</Heading>
              </HStack>
              <VStack align="start" spacing={2} pl={6}>
                <Text fontSize="sm" color="gray.600">
                  • 번역이 진행되는 동안 실시간으로 상태를 확인할 수 있습니다.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 자동 새로고침을 활성화하면 지정된 간격으로 자동 업데이트됩니다.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 최근 번역된 내용을 실시간으로 확인하여 번역 품질을 모니터링하세요.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 번역 속도와 남은 시간을 참고하여 작업을 계획하세요.
                </Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  )
}

export default LivePreviewPanel