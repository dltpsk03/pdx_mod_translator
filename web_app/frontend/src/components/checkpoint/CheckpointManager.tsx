import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  useToast,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
  Progress,
  Tooltip,
  Card,
  CardBody,
  CardHeader,
  Heading,
  useColorModeValue,
  Flex,
  Spacer,
  Icon,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText
} from '@chakra-ui/react'
import { 
  DeleteIcon, 
  RepeatIcon, 
  DownloadIcon, 
  InfoIcon,
  TimeIcon,
  CheckCircleIcon
} from '@chakra-ui/icons'
import { 
  FiFileText,
  FiClock,
  FiDatabase,
  FiRefreshCw
} from 'react-icons/fi'
import axios from 'axios'

interface Checkpoint {
  filename: string
  file_path: string
  completed_lines: number
  total_lines: number
  progress: number
  timestamp: number
  api_provider: string
  schema_version: string
}

interface CheckpointManagerProps {
  onRestoreCheckpoint?: (config: any) => void
}

export const CheckpointManager: React.FC<CheckpointManagerProps> = ({
  onRestoreCheckpoint
}) => {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<Checkpoint | null>(null)
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure()
  const toast = useToast()
  const cancelRef = React.useRef<HTMLButtonElement>(null)

  const cardBg = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const statBg = useColorModeValue('gray.50', 'gray.700')

  useEffect(() => {
    fetchCheckpoints()
  }, [])

  const fetchCheckpoints = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/checkpoints')
      if (response.data.status === 'success') {
        setCheckpoints(response.data.checkpoints)
      }
    } catch (error) {
      toast({
        title: '체크포인트 로드 실패',
        description: '체크포인트 목록을 불러오는데 실패했습니다.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const deleteCheckpoint = async (filename: string) => {
    try {
      const response = await axios.delete(`/api/checkpoints/${filename}`)
      if (response.data.status === 'success') {
        toast({
          title: '체크포인트 삭제 완료',
          description: '체크포인트가 성공적으로 삭제되었습니다.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
        
        // 목록에서 제거
        setCheckpoints(prev => prev.filter(cp => cp.filename !== filename))
      }
    } catch (error) {
      toast({
        title: '삭제 실패',
        description: '체크포인트 삭제에 실패했습니다.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    } finally {
      onDeleteClose()
      setSelectedCheckpoint(null)
    }
  }

  const restoreFromCheckpoint = async (filename: string) => {
    try {
      const response = await axios.post(`/api/checkpoints/${filename}/restore`)
      if (response.data.status === 'success') {
        toast({
          title: '체크포인트 복원 완료',
          description: '체크포인트에서 설정을 복원했습니다.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
        
        // 부모 컴포넌트에 복원된 설정 전달
        if (onRestoreCheckpoint && response.data.config) {
          onRestoreCheckpoint(response.data.config)
        }
      }
    } catch (error) {
      toast({
        title: '복원 실패',
        description: '체크포인트 복원에 실패했습니다.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getProgressColor = (progress: number) => {
    if (progress >= 90) return 'green'
    if (progress >= 70) return 'yellow'
    if (progress >= 50) return 'orange'
    return 'red'
  }

  const getCheckpointStats = () => {
    if (checkpoints.length === 0) {
      return {
        totalCheckpoints: 0,
        avgProgress: 0,
        totalFiles: 0,
        recentCheckpoints: 0
      }
    }

    const totalCheckpoints = checkpoints.length
    const avgProgress = checkpoints.reduce((sum, cp) => sum + cp.progress, 0) / totalCheckpoints
    const totalFiles = checkpoints.length // 각 체크포인트는 하나의 파일
    const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000)
    const recentCheckpoints = checkpoints.filter(cp => (cp.timestamp * 1000) > oneWeekAgo).length

    return {
      totalCheckpoints,
      avgProgress,
      totalFiles,
      recentCheckpoints
    }
  }

  const stats = getCheckpointStats()

  return (
    <Box p={6} w="100%">
      <VStack spacing={6} align="stretch">
        {/* 헤더 */}
        <Flex justify="space-between" align="center">
          <Heading size="lg" color="brand.500">
            📋 체크포인트 관리
          </Heading>
          <HStack spacing={2}>
            <Button
              leftIcon={<RepeatIcon />}
              onClick={fetchCheckpoints}
              isLoading={loading}
              size="sm"
              variant="outline"
            >
              새로고침
            </Button>
          </HStack>
        </Flex>

        {/* 요약 통계 */}
        <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    총 체크포인트
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                    {stats.totalCheckpoints}
                  </Text>
                </VStack>
                <Icon as={FiDatabase} w={8} h={8} color="blue.400" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    평균 진행률
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="green.500">
                    {stats.avgProgress.toFixed(1)}%
                  </Text>
                </VStack>
                <Icon as={CheckCircleIcon} w={8} h={8} color="green.400" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    최근 일주일
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                    {stats.recentCheckpoints}
                  </Text>
                </VStack>
                <Icon as={FiClock} w={8} h={8} color="purple.400" />
              </HStack>
            </CardBody>
          </Card>

          <Card bg={statBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500" fontWeight="medium">
                    파일 수
                  </Text>
                  <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                    {stats.totalFiles}
                  </Text>
                </VStack>
                <Icon as={FiFileText} w={8} h={8} color="orange.400" />
              </HStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* 체크포인트 목록 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">체크포인트 목록</Heading>
          </CardHeader>
          <CardBody>
            {loading ? (
              <VStack py={8}>
                <Progress size="xs" isIndeterminate w="100%" />
                <Text color="gray.500">체크포인트를 불러오는 중...</Text>
              </VStack>
            ) : checkpoints.length === 0 ? (
              <VStack py={8}>
                <Icon as={FiDatabase} w={12} h={12} color="gray.400" />
                <Text color="gray.500" fontSize="lg">저장된 체크포인트가 없습니다</Text>
                <Text color="gray.400" fontSize="sm" textAlign="center">
                  번역 중에 자동으로 체크포인트가 생성됩니다.
                </Text>
              </VStack>
            ) : (
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>파일명</Th>
                    <Th>진행률</Th>
                    <Th>완료/총 라인</Th>
                    <Th>API</Th>
                    <Th>생성 시간</Th>
                    <Th>작업</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {checkpoints.map((checkpoint, index) => (
                    <Tr key={index}>
                      <Td>
                        <VStack align="start" spacing={1}>
                          <Text fontWeight="medium" noOfLines={1}>
                            {checkpoint.filename}
                          </Text>
                          <Text fontSize="xs" color="gray.500" noOfLines={1}>
                            {checkpoint.file_path}
                          </Text>
                        </VStack>
                      </Td>
                      <Td>
                        <VStack align="start" spacing={1}>
                          <Text fontSize="sm" fontWeight="bold">
                            {checkpoint.progress.toFixed(1)}%
                          </Text>
                          <Progress
                            value={checkpoint.progress}
                            size="sm"
                            colorScheme={getProgressColor(checkpoint.progress)}
                            w="100px"
                          />
                        </VStack>
                      </Td>
                      <Td>
                        <VStack align="start" spacing={0}>
                          <Text fontSize="sm" fontWeight="medium">
                            {checkpoint.completed_lines.toLocaleString()}
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            / {checkpoint.total_lines.toLocaleString()}
                          </Text>
                        </VStack>
                      </Td>
                      <Td>
                        <Badge colorScheme="blue" variant="outline">
                          {checkpoint.api_provider}
                        </Badge>
                      </Td>
                      <Td>
                        <Text fontSize="sm">
                          {formatTimestamp(checkpoint.timestamp)}
                        </Text>
                      </Td>
                      <Td>
                        <HStack spacing={1}>
                          <Tooltip label="체크포인트에서 복원">
                            <IconButton
                              aria-label="복원"
                              icon={<RepeatIcon />}
                              size="sm"
                              colorScheme="green"
                              variant="outline"
                              onClick={() => restoreFromCheckpoint(checkpoint.filename)}
                            />
                          </Tooltip>
                          <Tooltip label="체크포인트 삭제">
                            <IconButton
                              aria-label="삭제"
                              icon={<DeleteIcon />}
                              size="sm"
                              colorScheme="red"
                              variant="outline"
                              onClick={() => {
                                setSelectedCheckpoint(checkpoint)
                                onDeleteOpen()
                              }}
                            />
                          </Tooltip>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </CardBody>
        </Card>

        {/* 도움말 카드 */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack align="start" spacing={3}>
              <HStack>
                <Icon as={InfoIcon} color="blue.500" />
                <Heading size="sm" color="blue.500">체크포인트 관리 가이드</Heading>
              </HStack>
              <VStack align="start" spacing={2} pl={6}>
                <Text fontSize="sm" color="gray.600">
                  • 체크포인트는 번역 중에 자동으로 생성되어 진행 상황을 저장합니다.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 번역이 중단된 경우 체크포인트에서 복원하여 이어서 진행할 수 있습니다.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 불필요한 체크포인트는 삭제하여 저장공간을 절약할 수 있습니다.
                </Text>
                <Text fontSize="sm" color="gray.600">
                  • 체크포인트는 API 제공자, 모델, 번역 설정 등을 포함합니다.
                </Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </VStack>

      {/* 삭제 확인 다이얼로그 */}
      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              체크포인트 삭제
            </AlertDialogHeader>

            <AlertDialogBody>
              <VStack align="start" spacing={3}>
                <Text>
                  다음 체크포인트를 삭제하시겠습니까?
                </Text>
                {selectedCheckpoint && (
                  <Box p={3} bg={statBg} borderRadius="md" w="100%">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold">{selectedCheckpoint.filename}</Text>
                      <Text fontSize="sm" color="gray.600">
                        진행률: {selectedCheckpoint.progress.toFixed(1)}%
                      </Text>
                      <Text fontSize="sm" color="gray.600">
                        생성 시간: {formatTimestamp(selectedCheckpoint.timestamp)}
                      </Text>
                    </VStack>
                  </Box>
                )}
                <Text fontSize="sm" color="red.600">
                  ⚠️ 삭제된 체크포인트는 복구할 수 없습니다.
                </Text>
              </VStack>
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>
                취소
              </Button>
              <Button
                colorScheme="red"
                onClick={() => selectedCheckpoint && deleteCheckpoint(selectedCheckpoint.filename)}
                ml={3}
              >
                삭제
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  )
}

export default CheckpointManager