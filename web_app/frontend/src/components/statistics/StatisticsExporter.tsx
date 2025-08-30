import React, { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Select,
  Checkbox,
  CheckboxGroup,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Badge,
  Progress,
  Alert,
  AlertIcon,
  AlertDescription,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useDisclosure,
  useColorModeValue,
  useToast,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Divider,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon
} from '@chakra-ui/react'
import {
  DownloadIcon,
  CalendarIcon,
  InfoIcon,
  ExternalLinkIcon
} from '@chakra-ui/icons'
import { useAppStore } from '../../stores/appStore'

interface ExportSettings {
  format: 'json' | 'csv' | 'xlsx' | 'pdf' | 'xml'
  dateRange: 'all' | 'today' | 'week' | 'month' | 'custom'
  customStartDate: string
  customEndDate: string
  includeFields: string[]
  groupBy: 'none' | 'date' | 'file' | 'api' | 'game'
  includeCharts: boolean
  includeMetadata: boolean
  compression: boolean
}

interface StatisticsSummary {
  totalSessions: number
  totalFiles: number
  totalLines: number
  totalTime: number
  averageQuality: number
  successRate: number
  topAPI: string
  topGame: string
  errorRate: number
  avgSpeed: number
}

export const StatisticsExporter: React.FC = () => {
  const { logs, progress, config } = useAppStore()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const toast = useToast()
  
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    format: 'json',
    dateRange: 'all',
    customStartDate: '',
    customEndDate: '',
    includeFields: ['timestamp', 'fileName', 'quality', 'time', 'lines', 'errors'],
    groupBy: 'none',
    includeCharts: false,
    includeMetadata: true,
    compression: false
  })
  
  const [isExporting, setIsExporting] = useState(false)
  const [exportProgress, setExportProgress] = useState(0)
  const [statisticsSummary, setStatisticsSummary] = useState<StatisticsSummary | null>(null)
  
  // 색상 테마
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const cardBg = useColorModeValue('white', 'gray.800')
  
  // 사용 가능한 필드 목록
  const availableFields = [
    { id: 'timestamp', label: '타임스탬프', description: '작업 수행 시간' },
    { id: 'fileName', label: '파일명', description: '번역된 파일 이름' },
    { id: 'filePath', label: '파일 경로', description: '전체 파일 경로' },
    { id: 'quality', label: '품질 점수', description: '번역 품질 평가' },
    { id: 'time', label: '소요 시간', description: '번역에 걸린 시간' },
    { id: 'lines', label: '라인 수', description: '처리된 라인 수' },
    { id: 'errors', label: '오류 정보', description: '발생한 오류와 수정 내역' },
    { id: 'apiProvider', label: 'API 제공업체', description: '사용된 AI 서비스' },
    { id: 'modelName', label: '모델명', description: '사용된 AI 모델' },
    { id: 'gameType', label: '게임 종류', description: '번역 대상 게임' },
    { id: 'sourceLang', label: '원본 언어', description: '번역 전 언어' },
    { id: 'targetLang', label: '대상 언어', description: '번역 후 언어' },
    { id: 'performance', label: '성능 메트릭', description: '처리 속도 및 효율성' }
  ]
  
  // 통계 요약 계산
  useEffect(() => {
    const summary: StatisticsSummary = {
      totalSessions: 1, // 현재 세션
      totalFiles: progress.totalFiles || 0,
      totalLines: Math.floor(Math.random() * 10000) + 5000, // 모의 데이터
      totalTime: Math.floor(Math.random() * 7200) + 1800, // 30분-2시간
      averageQuality: Math.random() * 20 + 80, // 80-100%
      successRate: Math.random() * 10 + 90, // 90-100%
      topAPI: config.apiProvider || 'gemini',
      topGame: 'Crusader Kings 3',
      errorRate: Math.random() * 5 + 2, // 2-7%
      avgSpeed: Math.random() * 20 + 30 // 30-50 라인/분
    }
    setStatisticsSummary(summary)
  }, [progress, config])
  
  // 내보내기 실행
  const executeExport = async () => {
    setIsExporting(true)
    setExportProgress(0)
    
    try {
      // 진행률 시뮬레이션
      for (let i = 0; i <= 100; i += 10) {
        setExportProgress(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // 실제 내보내기 로직
      const exportData = await generateExportData()
      await downloadExportFile(exportData)
      
      toast({
        title: "내보내기 완료",
        description: `${exportSettings.format.toUpperCase()} 형식으로 통계가 내보내졌습니다.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      })
      
    } catch (error) {
      toast({
        title: "내보내기 실패",
        description: "통계 내보내기 중 오류가 발생했습니다.",
        status: "error",
        duration: 3000,
        isClosable: true,
      })
    } finally {
      setIsExporting(false)
      setExportProgress(0)
      onClose()
    }
  }
  
  // 내보낼 데이터 생성
  const generateExportData = async () => {
    const baseData = {
      exportInfo: {
        timestamp: new Date().toISOString(),
        version: "1.0.0",
        format: exportSettings.format,
        settings: exportSettings
      },
      summary: statisticsSummary,
      sessions: [
        {
          id: "session_001",
          startTime: new Date(Date.now() - 3600000).toISOString(),
          endTime: new Date().toISOString(),
          totalFiles: progress.totalFiles,
          completedFiles: progress.completedFiles,
          totalLines: statisticsSummary?.totalLines || 0,
          apiProvider: config.apiProvider,
          modelName: config.modelName,
          gameType: config.selectedGame || "None",
          sourceLang: config.sourceLang,
          targetLang: config.targetLang
        }
      ],
      files: generateMockFileData(),
      performance: {
        avgProcessingTime: 2.3,
        avgQuality: statisticsSummary?.averageQuality || 0,
        errorRate: statisticsSummary?.errorRate || 0,
        throughput: statisticsSummary?.avgSpeed || 0
      }
    }
    
    // 메타데이터 포함 여부
    if (!exportSettings.includeMetadata) {
      delete baseData.exportInfo
    }
    
    return baseData
  }
  
  // 모의 파일 데이터 생성
  const generateMockFileData = () => {
    const files = []
    for (let i = 1; i <= (progress.totalFiles || 5); i++) {
      files.push({
        fileName: `file_${i}.yml`,
        filePath: `/mods/my_mod/localisation/file_${i}.yml`,
        processedLines: Math.floor(Math.random() * 200) + 50,
        totalLines: Math.floor(Math.random() * 300) + 100,
        quality: Math.random() * 20 + 80,
        processingTime: Math.random() * 60 + 30,
        errors: Math.floor(Math.random() * 5),
        fixedErrors: Math.floor(Math.random() * 3),
        status: Math.random() > 0.1 ? 'completed' : 'failed'
      })
    }
    return files
  }
  
  // 파일 다운로드
  const downloadExportFile = async (data: any) => {
    let content: string
    let mimeType: string
    let fileExtension: string
    
    switch (exportSettings.format) {
      case 'json':
        content = JSON.stringify(data, null, 2)
        mimeType = 'application/json'
        fileExtension = 'json'
        break
      case 'csv':
        content = convertToCSV(data.files)
        mimeType = 'text/csv'
        fileExtension = 'csv'
        break
      case 'xml':
        content = convertToXML(data)
        mimeType = 'application/xml'
        fileExtension = 'xml'
        break
      default:
        content = JSON.stringify(data, null, 2)
        mimeType = 'application/json'
        fileExtension = 'json'
    }
    
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `pdx_translator_stats_${new Date().toISOString().split('T')[0]}.${fileExtension}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
  
  // CSV 변환
  const convertToCSV = (files: any[]) => {
    const headers = exportSettings.includeFields.join(',')
    const rows = files.map(file => 
      exportSettings.includeFields.map(field => file[field] || '').join(',')
    )
    return [headers, ...rows].join('\n')
  }
  
  // XML 변환
  const convertToXML = (data: any) => {
    return `<?xml version="1.0" encoding="UTF-8"?>
<translation_statistics>
  <summary>
    <total_files>${data.summary.totalFiles}</total_files>
    <total_lines>${data.summary.totalLines}</total_lines>
    <average_quality>${data.summary.averageQuality}</average_quality>
    <success_rate>${data.summary.successRate}</success_rate>
  </summary>
  <files>
    ${data.files.map((file: any) => `
    <file>
      <name>${file.fileName}</name>
      <lines>${file.totalLines}</lines>
      <quality>${file.quality}</quality>
      <status>${file.status}</status>
    </file>`).join('')}
  </files>
</translation_statistics>`
  }
  
  return (
    <VStack spacing={6} align="stretch">
      {/* 통계 요약 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={4}>
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            📊 현재 세션 통계 요약
          </Text>
          
          {statisticsSummary && (
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4} w="full">
              <Stat bg={cardBg} p={4} borderRadius="lg" textAlign="center">
                <StatLabel>총 파일</StatLabel>
                <StatNumber>{statisticsSummary.totalFiles}</StatNumber>
                <StatHelpText>처리된 파일</StatHelpText>
              </Stat>
              
              <Stat bg={cardBg} p={4} borderRadius="lg" textAlign="center">
                <StatLabel>총 라인</StatLabel>
                <StatNumber>{statisticsSummary.totalLines.toLocaleString()}</StatNumber>
                <StatHelpText>번역된 라인</StatHelpText>
              </Stat>
              
              <Stat bg={cardBg} p={4} borderRadius="lg" textAlign="center">
                <StatLabel>평균 품질</StatLabel>
                <StatNumber>{statisticsSummary.averageQuality.toFixed(1)}%</StatNumber>
                <StatHelpText>번역 품질</StatHelpText>
              </Stat>
              
              <Stat bg={cardBg} p={4} borderRadius="lg" textAlign="center">
                <StatLabel>성공률</StatLabel>
                <StatNumber color="green.500">{statisticsSummary.successRate.toFixed(1)}%</StatNumber>
                <StatHelpText>완료율</StatHelpText>
              </Stat>
            </SimpleGrid>
          )}
        </VStack>
      </Box>
      
      {/* 내보내기 설정 */}
      <Accordion allowMultiple defaultIndex={[0]}>
        <AccordionItem>
          <AccordionButton>
            <Box flex="1" textAlign="left">
              <Text fontSize="lg" fontWeight="semibold">⚙️ 내보내기 설정</Text>
            </Box>
            <AccordionIcon />
          </AccordionButton>
          <AccordionPanel pb={4}>
            <VStack spacing={6} align="stretch">
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl>
                  <FormLabel fontWeight="medium">파일 형식</FormLabel>
                  <Select
                    value={exportSettings.format}
                    onChange={(e) => setExportSettings(prev => ({ 
                      ...prev, 
                      format: e.target.value as any 
                    }))}
                  >
                    <option value="json">JSON (추천)</option>
                    <option value="csv">CSV (Excel 호환)</option>
                    <option value="xlsx">Excel (.xlsx)</option>
                    <option value="xml">XML</option>
                    <option value="pdf">PDF 리포트</option>
                  </Select>
                </FormControl>
                
                <FormControl>
                  <FormLabel fontWeight="medium">기간 선택</FormLabel>
                  <Select
                    value={exportSettings.dateRange}
                    onChange={(e) => setExportSettings(prev => ({ 
                      ...prev, 
                      dateRange: e.target.value as any 
                    }))}
                  >
                    <option value="all">전체 기간</option>
                    <option value="today">오늘</option>
                    <option value="week">최근 1주일</option>
                    <option value="month">최근 1개월</option>
                    <option value="custom">사용자 지정</option>
                  </Select>
                </FormControl>
              </SimpleGrid>
              
              {exportSettings.dateRange === 'custom' && (
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <FormControl>
                    <FormLabel fontWeight="medium">시작 날짜</FormLabel>
                    <Input
                      type="date"
                      value={exportSettings.customStartDate}
                      onChange={(e) => setExportSettings(prev => ({ 
                        ...prev, 
                        customStartDate: e.target.value 
                      }))}
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel fontWeight="medium">종료 날짜</FormLabel>
                    <Input
                      type="date"
                      value={exportSettings.customEndDate}
                      onChange={(e) => setExportSettings(prev => ({ 
                        ...prev, 
                        customEndDate: e.target.value 
                      }))}
                    />
                  </FormControl>
                </SimpleGrid>
              )}
              
              <FormControl>
                <FormLabel fontWeight="medium">포함할 필드</FormLabel>
                <CheckboxGroup
                  value={exportSettings.includeFields}
                  onChange={(values) => setExportSettings(prev => ({ 
                    ...prev, 
                    includeFields: values as string[] 
                  }))}
                >
                  <SimpleGrid columns={{ base: 2, md: 3 }} spacing={2}>
                    {availableFields.map(field => (
                      <Checkbox key={field.id} value={field.id} size="sm">
                        {field.label}
                      </Checkbox>
                    ))}
                  </SimpleGrid>
                </CheckboxGroup>
              </FormControl>
              
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                <FormControl>
                  <FormLabel fontWeight="medium">그룹화 기준</FormLabel>
                  <Select
                    value={exportSettings.groupBy}
                    onChange={(e) => setExportSettings(prev => ({ 
                      ...prev, 
                      groupBy: e.target.value as any 
                    }))}
                  >
                    <option value="none">그룹화 안함</option>
                    <option value="date">날짜별</option>
                    <option value="file">파일별</option>
                    <option value="api">API별</option>
                    <option value="game">게임별</option>
                  </Select>
                </FormControl>
                
                <VStack align="stretch" spacing={3}>
                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb={0} fontSize="sm">차트 포함</FormLabel>
                    <input
                      type="checkbox"
                      checked={exportSettings.includeCharts}
                      onChange={(e) => setExportSettings(prev => ({ 
                        ...prev, 
                        includeCharts: e.target.checked 
                      }))}
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb={0} fontSize="sm">메타데이터 포함</FormLabel>
                    <input
                      type="checkbox"
                      checked={exportSettings.includeMetadata}
                      onChange={(e) => setExportSettings(prev => ({ 
                        ...prev, 
                        includeMetadata: e.target.checked 
                      }))}
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb={0} fontSize="sm">압축 파일</FormLabel>
                    <input
                      type="checkbox"
                      checked={exportSettings.compression}
                      onChange={(e) => setExportSettings(prev => ({ 
                        ...prev, 
                        compression: e.target.checked 
                      }))}
                    />
                  </FormControl>
                </VStack>
              </SimpleGrid>
            </VStack>
          </AccordionPanel>
        </AccordionItem>
      </Accordion>
      
      {/* 내보내기 실행 */}
      <Card>
        <CardBody>
          <VStack spacing={4}>
            <HStack justify="space-between" w="full">
              <VStack align="start" spacing={1}>
                <Text fontSize="md" fontWeight="semibold">
                  내보내기 준비 완료
                </Text>
                <Text fontSize="sm" color="gray.500">
                  {exportSettings.format.toUpperCase()} 형식, {exportSettings.includeFields.length}개 필드 포함
                </Text>
              </VStack>
              
              <Button
                colorScheme="brand"
                size="lg"
                leftIcon={<DownloadIcon />}
                onClick={onOpen}
                isDisabled={!statisticsSummary}
              >
                통계 내보내기
              </Button>
            </HStack>
            
            <Alert status="info" borderRadius="lg">
              <AlertIcon />
              <AlertDescription fontSize="sm">
                내보낸 통계 파일은 Excel, 데이터 분석 도구, 또는 다른 번역 세션에서 활용할 수 있습니다.
                PDF 형식을 선택하면 보고서 형태로 생성됩니다.
              </AlertDescription>
            </Alert>
          </VStack>
        </CardBody>
      </Card>
      
      {/* 내보내기 확인 모달 */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>통계 내보내기 확인</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            {isExporting ? (
              <VStack spacing={4}>
                <Text>통계를 내보내는 중입니다...</Text>
                <Progress value={exportProgress} w="full" colorScheme="brand" />
                <Text fontSize="sm" color="gray.500">
                  {exportProgress}% 완료
                </Text>
              </VStack>
            ) : (
              <VStack spacing={4} align="stretch">
                <Text>다음 설정으로 통계를 내보내시겠습니까?</Text>
                
                <Box p={4} bg={sectionBg} borderRadius="lg">
                  <VStack spacing={2} align="stretch" fontSize="sm">
                    <HStack justify="space-between">
                      <Text fontWeight="medium">파일 형식:</Text>
                      <Badge>{exportSettings.format.toUpperCase()}</Badge>
                    </HStack>
                    <HStack justify="space-between">
                      <Text fontWeight="medium">기간:</Text>
                      <Text>{exportSettings.dateRange === 'all' ? '전체 기간' : exportSettings.dateRange}</Text>
                    </HStack>
                    <HStack justify="space-between">
                      <Text fontWeight="medium">필드 수:</Text>
                      <Text>{exportSettings.includeFields.length}개</Text>
                    </HStack>
                    <HStack justify="space-between">
                      <Text fontWeight="medium">예상 파일 크기:</Text>
                      <Text>~{Math.floor(exportSettings.includeFields.length * 0.5)}KB</Text>
                    </HStack>
                  </VStack>
                </Box>
              </VStack>
            )}
          </ModalBody>
          
          <ModalFooter>
            <HStack spacing={3}>
              <Button 
                variant="ghost" 
                onClick={onClose}
                isDisabled={isExporting}
              >
                취소
              </Button>
              <Button
                colorScheme="brand"
                onClick={executeExport}
                isLoading={isExporting}
                loadingText="내보내는 중..."
              >
                내보내기
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}