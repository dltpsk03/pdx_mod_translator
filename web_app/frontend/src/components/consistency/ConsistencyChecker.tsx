import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Textarea,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Progress,
  useToast,
  Card,
  CardBody,
  CardHeader,
  Heading,
  useColorModeValue,
  FormControl,
  FormLabel,
  FormHelperText,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  SimpleGrid,
  Icon,
  Flex,
  Spacer,
  Select,
  Divider,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem
} from '@chakra-ui/react'
import { SearchIcon, CheckIcon, WarningIcon, InfoIcon } from '@chakra-ui/icons'
import { FiFileText, FiTarget, FiAlertTriangle, FiCheck } from 'react-icons/fi'
import axios from 'axios'

interface InconsistentTerm {
  term: string
  translations: string[]
  files: string[]
  suggestions: string[]
  severity: 'high' | 'medium' | 'low'
}

interface ConsistencyResult {
  total_files_checked: number
  total_terms_found: number
  inconsistent_terms: InconsistentTerm[]
  suggestions: string[]
}

interface ConsistencyCheckerProps {
  inputFolder?: string
}

export const ConsistencyChecker: React.FC<ConsistencyCheckerProps> = ({
  inputFolder = ''
}) => {
  const [isChecking, setIsChecking] = useState(false)
  const [results, setResults] = useState<ConsistencyResult | null>(null)
  const [selectedFolder, setSelectedFolder] = useState(inputFolder)
  const [customTerms, setCustomTerms] = useState<string[]>([])
  const [newTerm, setNewTerm] = useState('')
  const [filters, setFilters] = useState({
    severity: 'all',
    minOccurrences: 2
  })
  
  const toast = useToast()
  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const statBg = useColorModeValue('gray.50', 'gray.700')

  useEffect(() => {
    if (inputFolder) {
      setSelectedFolder(inputFolder)
    }
  }, [inputFolder])

  const addCustomTerm = () => {
    if (newTerm.trim() && !customTerms.includes(newTerm.trim())) {
      setCustomTerms([...customTerms, newTerm.trim()])
      setNewTerm('')
    }
  }

  const removeCustomTerm = (term: string) => {
    setCustomTerms(customTerms.filter(t => t !== term))
  }

  const selectFolder = async () => {
    try {
      const response = await axios.post('/api/folder/select')
      if (response.data.success && response.data.path) {
        setSelectedFolder(response.data.path)
      }
    } catch (error) {
      toast({
        title: '폴더 선택 실패',
        description: '폴더 선택 중 오류가 발생했습니다.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  const checkConsistency = async () => {
    if (!selectedFolder.trim()) {
      toast({
        title: '폴더를 선택해주세요',
        description: '일관성을 검사할 폴더를 선택해주세요.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    setIsChecking(true)
    try {
      const response = await axios.post('/api/consistency/check', {
        input_folder: selectedFolder,
        glossary_terms: customTerms,
        filters
      })

      if (response.data.status === 'success') {
        setResults(response.data.results)
        toast({
          title: '일관성 검사 완료',
          description: `${response.data.results.total_files_checked}개 파일을 검사했습니다.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
      }
    } catch (error) {
      toast({
        title: '검사 실패',
        description: '일관성 검사 중 오류가 발생했습니다.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsChecking(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'red'
      case 'medium': return 'orange'
      case 'low': return 'yellow'
      default: return 'gray'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return WarningIcon
      case 'medium': return InfoIcon
      case 'low': return CheckIcon
      default: return InfoIcon
    }
  }

  const filteredTerms = results?.inconsistent_terms.filter(term => {
    if (filters.severity !== 'all' && term.severity !== filters.severity) {
      return false
    }
    if (term.files.length < filters.minOccurrences) {
      return false
    }
    return true
  }) || []

  const getStats = () => {
    if (!results) {
      return {
        totalFiles: 0,
        totalTerms: 0,
        inconsistentTerms: 0,
        highSeverity: 0,
        mediumSeverity: 0,
        lowSeverity: 0
      }
    }

    return {
      totalFiles: results.total_files_checked,
      totalTerms: results.total_terms_found,
      inconsistentTerms: results.inconsistent_terms.length,
      highSeverity: results.inconsistent_terms.filter(t => t.severity === 'high').length,
      mediumSeverity: results.inconsistent_terms.filter(t => t.severity === 'medium').length,
      lowSeverity: results.inconsistent_terms.filter(t => t.severity === 'low').length
    }
  }

  const stats = getStats()

  return (
    <Box p={6} w="100%">
      <VStack spacing={6} align="stretch">
        {/* 헤더 */}
        <Flex justify="space-between" align="center">
          <Heading size="lg" color="brand.500">
            🔍 번역 일관성 검사
          </Heading>
        </Flex>

        {/* 설정 패널 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">검사 설정</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {/* 폴더 선택 */}
              <FormControl>
                <FormLabel>검사할 폴더</FormLabel>
                <HStack>
                  <Input
                    value={selectedFolder}
                    onChange={(e) => setSelectedFolder(e.target.value)}
                    placeholder="검사할 폴더 경로를 입력하거나 선택해주세요"
                  />
                  <Button onClick={selectFolder} minW="100px">
                    폴더 선택
                  </Button>
                </HStack>
                <FormHelperText>
                  번역된 YAML 파일들이 있는 폴더를 선택해주세요.
                </FormHelperText>
              </FormControl>

              {/* 커스텀 용어 추가 */}
              <FormControl>
                <FormLabel>추가 검사 용어</FormLabel>
                <HStack>
                  <Input
                    value={newTerm}
                    onChange={(e) => setNewTerm(e.target.value)}
                    placeholder="검사할 용어를 입력하세요"
                    onKeyPress={(e) => e.key === 'Enter' && addCustomTerm()}
                  />
                  <Button onClick={addCustomTerm} minW="80px">
                    추가
                  </Button>
                </HStack>
                {customTerms.length > 0 && (
                  <Box mt={2}>
                    <Wrap>
                      {customTerms.map((term, index) => (
                        <WrapItem key={index}>
                          <Tag size="md" colorScheme="blue" borderRadius="full">
                            <TagLabel>{term}</TagLabel>
                            <TagCloseButton onClick={() => removeCustomTerm(term)} />
                          </Tag>
                        </WrapItem>
                      ))}
                    </Wrap>
                  </Box>
                )}
                <FormHelperText>
                  특별히 검사하고 싶은 용어를 추가할 수 있습니다.
                </FormHelperText>
              </FormControl>

              {/* 필터 설정 */}
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                <FormControl>
                  <FormLabel>심각도 필터</FormLabel>
                  <Select
                    value={filters.severity}
                    onChange={(e) => setFilters({...filters, severity: e.target.value})}
                  >
                    <option value="all">모든 심각도</option>
                    <option value="high">높음</option>
                    <option value="medium">보통</option>
                    <option value="low">낮음</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>최소 출현 횟수</FormLabel>
                  <Select
                    value={filters.minOccurrences}
                    onChange={(e) => setFilters({...filters, minOccurrences: parseInt(e.target.value)})}
                  >
                    <option value="1">1회 이상</option>
                    <option value="2">2회 이상</option>
                    <option value="3">3회 이상</option>
                    <option value="5">5회 이상</option>
                  </Select>
                </FormControl>
              </SimpleGrid>

              {/* 검사 시작 버튼 */}
              <Button
                leftIcon={<SearchIcon />}
                onClick={checkConsistency}
                isLoading={isChecking}
                loadingText="검사 중..."
                colorScheme="brand"
                size="lg"
                isDisabled={!selectedFolder.trim()}
              >
                일관성 검사 시작
              </Button>
            </VStack>
          </CardBody>
        </Card>

        {/* 검사 결과 통계 */}
        {results && (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
            <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.500" fontWeight="medium">
                      검사한 파일
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                      {stats.totalFiles}
                    </Text>
                  </VStack>
                  <Icon as={FiFileText} w={8} h={8} color="blue.400" />
                </HStack>
              </CardBody>
            </Card>

            <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.500" fontWeight="medium">
                      발견한 용어
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold" color="green.500">
                      {stats.totalTerms}
                    </Text>
                  </VStack>
                  <Icon as={FiTarget} w={8} h={8} color="green.400" />
                </HStack>
              </CardBody>
            </Card>

            <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.500" fontWeight="medium">
                      불일치 용어
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold" color="red.500">
                      {stats.inconsistentTerms}
                    </Text>
                  </VStack>
                  <Icon as={FiAlertTriangle} w={8} h={8} color="red.400" />
                </HStack>
              </CardBody>
            </Card>

            <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <Text fontSize="sm" color="gray.500" fontWeight="medium">
                      일관성 점수
                    </Text>
                    <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                      {stats.totalTerms > 0 
                        ? ((stats.totalTerms - stats.inconsistentTerms) / stats.totalTerms * 100).toFixed(1)
                        : '100.0'
                      }%
                    </Text>
                  </VStack>
                  <Icon as={FiCheck} w={8} h={8} color="purple.400" />
                </HStack>
              </CardBody>
            </Card>
          </SimpleGrid>
        )}

        {/* 검사 결과 */}
        {isChecking && (
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <VStack py={8} spacing={4}>
                <Spinner size="xl" />
                <Text fontSize="lg">일관성을 검사하는 중...</Text>
                <Text fontSize="sm" color="gray.500">
                  파일을 분석하고 용어의 일관성을 확인하고 있습니다.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        )}

        {results && !isChecking && (
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <Heading size="md">불일치 용어 목록</Heading>
                <Badge colorScheme="red" fontSize="sm" px={2} py={1}>
                  {filteredTerms.length}개 발견
                </Badge>
              </HStack>
            </CardHeader>
            <CardBody>
              {filteredTerms.length === 0 ? (
                <Alert status="success" borderRadius="lg">
                  <AlertIcon />
                  <AlertDescription>
                    🎉 모든 용어가 일관되게 번역되었습니다!
                  </AlertDescription>
                </Alert>
              ) : (
                <VStack spacing={4} align="stretch">
                  {/* 심각도별 요약 */}
                  <HStack spacing={4}>
                    <Badge colorScheme="red" size="lg">
                      높음: {stats.highSeverity}개
                    </Badge>
                    <Badge colorScheme="orange" size="lg">
                      보통: {stats.mediumSeverity}개  
                    </Badge>
                    <Badge colorScheme="yellow" size="lg">
                      낮음: {stats.lowSeverity}개
                    </Badge>
                  </HStack>

                  <Divider />

                  {/* 불일치 용어 상세 목록 */}
                  <VStack spacing={3} align="stretch">
                    {filteredTerms.map((term, index) => (
                      <Card key={index} border="1px" borderColor={borderColor}>
                        <CardBody>
                          <VStack align="stretch" spacing={3}>
                            <HStack justify="space-between">
                              <HStack>
                                <Icon 
                                  as={getSeverityIcon(term.severity)}
                                  color={`${getSeverityColor(term.severity)}.500`}
                                />
                                <Text fontWeight="bold" fontSize="lg">
                                  {term.term}
                                </Text>
                              </HStack>
                              <Badge colorScheme={getSeverityColor(term.severity)}>
                                {term.severity}
                              </Badge>
                            </HStack>

                            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                              <Box>
                                <Text fontSize="sm" fontWeight="medium" color="gray.600" mb={2}>
                                  발견된 번역들:
                                </Text>
                                <Wrap>
                                  {term.translations.map((translation, i) => (
                                    <WrapItem key={i}>
                                      <Tag colorScheme="blue">
                                        <TagLabel>{translation}</TagLabel>
                                      </Tag>
                                    </WrapItem>
                                  ))}
                                </Wrap>
                              </Box>

                              <Box>
                                <Text fontSize="sm" fontWeight="medium" color="gray.600" mb={2}>
                                  출현 파일:
                                </Text>
                                <VStack align="start" spacing={1} maxH="100px" overflowY="auto">
                                  {term.files.map((file, i) => (
                                    <Text key={i} fontSize="xs" color="gray.500">
                                      {file}
                                    </Text>
                                  ))}
                                </VStack>
                              </Box>
                            </SimpleGrid>

                            {term.suggestions.length > 0 && (
                              <Box>
                                <Text fontSize="sm" fontWeight="medium" color="green.600" mb={2}>
                                  권장 번역:
                                </Text>
                                <Wrap>
                                  {term.suggestions.map((suggestion, i) => (
                                    <WrapItem key={i}>
                                      <Tag colorScheme="green">
                                        <TagLabel>{suggestion}</TagLabel>
                                      </Tag>
                                    </WrapItem>
                                  ))}
                                </Wrap>
                              </Box>
                            )}
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                </VStack>
              )}
            </CardBody>
          </Card>
        )}

        {/* 도움말 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack align="start" spacing={3}>
              <HStack>
                <Icon as={InfoIcon} color="blue.500" />
                <Heading size="sm" color="blue.500">일관성 검사 가이드</Heading>
              </HStack>
              <VStack align="start" spacing={2} pl={6}>
                <Text fontSize="sm" color="gray.600">
                  • <strong>높음</strong>: 같은 용어가 완전히 다르게 번역된 경우
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • <strong>보통</strong>: 비슷하지만 약간의 차이가 있는 번역
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • <strong>낮음</strong>: 문맥에 따라 다를 수 있는 번역
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 권장 번역을 참고하여 용어집을 업데이트하세요.
                </Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>
    </Box>
  )
}

export default ConsistencyChecker