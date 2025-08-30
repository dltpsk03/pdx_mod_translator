import React, { useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormHelperText,
  Textarea,
  Text,
  Button,
  Divider,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  Badge,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertDescription,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Input,
  ModalFooter,
  useToast
} from '@chakra-ui/react'
import { 
  AddIcon, 
  DeleteIcon, 
  DownloadIcon, 
  EditIcon,
  AttachmentIcon
} from '@chakra-ui/icons'
import { useAppStore } from '../../stores/appStore'

export const PromptGlossaryPanel: React.FC = () => {
  const { config, updateConfig } = useAppStore()
  const { isOpen, onOpen, onClose } = useDisclosure()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const toast = useToast()
  
  // 스타일 설정
  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const inputBg = useColorModeValue('white', 'gray.600')
  const tableBg = useColorModeValue('white', 'gray.800')
  
  // 기본 프롬프트 템플릿
  const defaultPrompt = `당신은 Paradox Interactive의 전략 게임 (Europa Universalis, Hearts of Iron, Crusader Kings, Stellaris 등)의 MOD 번역 전문가입니다.

다음 지침을 따라 번역하세요:

1. **정확성**: 게임 용어와 역사적 맥락을 정확히 번역하세요
2. **일관성**: 동일한 용어는 항상 같은 방식으로 번역하세요  
3. **자연스러움**: 한국어 사용자에게 자연스럽게 읽히도록 번역하세요
4. **형식 보존**: YAML 형식과 특수 문자($, [], {} 등)는 그대로 유지하세요

원본 텍스트: {source_text}
번역 언어: {target_language}

번역:`

  const handlePromptReset = () => {
    updateConfig({ promptTemplate: defaultPrompt })
    toast({
      title: "프롬프트 초기화 완료",
      description: "기본 프롬프트 템플릿으로 복원되었습니다.",
      status: "success",
      duration: 3000,
      isClosable: true,
    })
  }
  
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      onOpen()
    }
  }
  
  const handleGlossaryAdd = () => {
    if (selectedFile) {
      const newFile = {
        path: selectedFile.name,
        name: selectedFile.name.replace(/\.[^/.]+$/, ""),
        size: selectedFile.size
      }
      
      updateConfig({ 
        glossaryFiles: [...config.glossaryFiles, newFile] 
      })
      
      toast({
        title: "용어집 추가 완료",
        description: `${selectedFile.name} 파일이 추가되었습니다.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      })
    }
    onClose()
    setSelectedFile(null)
  }
  
  const handleGlossaryRemove = (index: number) => {
    const newFiles = config.glossaryFiles.filter((_, i) => i !== index)
    updateConfig({ glossaryFiles: newFiles })
    
    toast({
      title: "용어집 제거 완료",
      description: "선택한 용어집 파일이 제거되었습니다.",
      status: "info",
      duration: 3000,
      isClosable: true,
    })
  }
  
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  return (
    <VStack spacing={8} align="stretch">
      {/* 프롬프트 템플릿 섹션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="lg" fontWeight="semibold" color="brand.500">
              📝 번역 프롬프트 템플릿
            </Text>
            <Button
              size="sm"
              variant="outline"
              colorScheme="brand"
              onClick={handlePromptReset}
            >
              기본값으로 초기화
            </Button>
          </HStack>
          
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            <AlertDescription>
              프롬프트 템플릿은 AI에게 번역 방식을 안내하는 지침입니다. 
              {'{source_text}'}와 {'{target_language}'}는 자동으로 실제 값으로 대체됩니다.
            </AlertDescription>
          </Alert>
          
          <FormControl>
            <FormLabel fontWeight="medium">프롬프트 템플릿</FormLabel>
            <Textarea
              value={config.promptTemplate}
              onChange={(e) => updateConfig({ promptTemplate: e.target.value })}
              placeholder="번역에 사용할 AI 프롬프트 템플릿을 작성하세요..."
              rows={12}
              bg={inputBg}
              borderRadius="lg"
              fontSize="sm"
              fontFamily="mono"
            />
            <FormHelperText>
              좋은 프롬프트는 번역 품질을 크게 향상시킵니다. 
              게임별 특성과 번역 스타일을 명확히 지정하세요.
            </FormHelperText>
          </FormControl>
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 용어집 관리 섹션 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={6} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="lg" fontWeight="semibold" color="brand.500">
              📚 용어집 관리
            </Text>
            <Button
              leftIcon={<AddIcon />}
              colorScheme="brand"
              size="sm"
              onClick={() => document.getElementById('glossary-upload')?.click()}
            >
              용어집 추가
            </Button>
            <input
              id="glossary-upload"
              type="file"
              accept=".txt,.csv,.json,.xlsx"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
          </HStack>
          
          <Alert status="info" borderRadius="lg">
            <AlertIcon />
            <AlertDescription>
              용어집 파일은 번역의 일관성을 보장합니다. 
              CSV, TXT, JSON, XLSX 형식을 지원하며, "원문,번역문" 형태로 작성하세요.
            </AlertDescription>
          </Alert>
          
          {config.glossaryFiles.length === 0 ? (
            <Box 
              p={8} 
              textAlign="center" 
              bg={tableBg} 
              borderRadius="lg" 
              border="2px dashed" 
              borderColor="gray.300"
            >
              <AttachmentIcon boxSize={8} color="gray.400" mb={4} />
              <Text color="gray.500" fontSize="lg">
                등록된 용어집이 없습니다
              </Text>
              <Text color="gray.400" fontSize="sm" mt={2}>
                용어집을 추가하여 번역 품질을 향상시키세요
              </Text>
            </Box>
          ) : (
            <Box bg={tableBg} borderRadius="lg" overflow="hidden">
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>파일명</Th>
                    <Th>크기</Th>
                    <Th>상태</Th>
                    <Th width="120px">작업</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {config.glossaryFiles.map((file, index) => (
                    <Tr key={index}>
                      <Td>
                        <Text fontWeight="medium">{file.name}</Text>
                        <Text fontSize="sm" color="gray.500">{file.path}</Text>
                      </Td>
                      <Td>{formatFileSize(file.size)}</Td>
                      <Td>
                        <Badge colorScheme="green" variant="subtle">
                          활성
                        </Badge>
                      </Td>
                      <Td>
                        <HStack spacing={2}>
                          <IconButton
                            aria-label="용어집 편집"
                            icon={<EditIcon />}
                            size="sm"
                            variant="ghost"
                            colorScheme="blue"
                          />
                          <IconButton
                            aria-label="용어집 다운로드"
                            icon={<DownloadIcon />}
                            size="sm"
                            variant="ghost"
                            colorScheme="green"
                          />
                          <IconButton
                            aria-label="용어집 삭제"
                            icon={<DeleteIcon />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleGlossaryRemove(index)}
                          />
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}
        </VStack>
      </Box>
      
      <Divider />
      
      {/* 번역 품질 향상 팁 */}
      <Box p={6} bg={sectionBg} borderRadius="xl">
        <VStack spacing={4} align="stretch">
          <Text fontSize="lg" fontWeight="semibold" color="brand.500">
            💡 번역 품질 향상 팁
          </Text>
          
          <VStack spacing={3} align="stretch">
            <Box p={4} bg={inputBg} borderRadius="lg">
              <Text fontWeight="medium" mb={2}>📋 효과적인 프롬프트 작성법</Text>
              <Text fontSize="sm" color="gray.600">
                • 게임의 특성과 맥락을 명확히 설명하세요<br/>
                • 번역 스타일 (격식체/반말, 직역/의역)을 지정하세요<br/>
                • 특수한 용어나 고유명사 처리 방법을 안내하세요<br/>
                • 예시 번역을 포함하면 더 좋은 결과를 얻을 수 있습니다
              </Text>
            </Box>
            
            <Box p={4} bg={inputBg} borderRadius="lg">
              <Text fontWeight="medium" mb={2}>📚 용어집 활용법</Text>
              <Text fontSize="sm" color="gray.600">
                • 게임별 전문 용어는 반드시 용어집에 포함하세요<br/>
                • 고유명사 (인명, 지명, 기관명)는 통일된 번역을 유지하세요<br/>
                • 자주 사용되는 UI 텍스트도 용어집에 추가하면 좋습니다<br/>
                • CSV 형식: "원문,번역문" 또는 "English,한국어" 형태로 작성
              </Text>
            </Box>
            
            <Box p={4} bg={inputBg} borderRadius="lg">
              <Text fontWeight="medium" mb={2}>🎯 번역 일관성 유지</Text>
              <Text fontSize="sm" color="gray.600">
                • 같은 MOD 내에서는 동일한 용어집과 프롬프트를 사용하세요<br/>
                • 시리즈물의 경우 이전 번역본과 용어를 통일하세요<br/>
                • 번역 완료 후 전체 검토를 통해 일관성을 확인하세요<br/>
                • 사용자 피드백을 용어집에 반영하여 지속적으로 개선하세요
              </Text>
            </Box>
          </VStack>
        </VStack>
      </Box>
      
      {/* 파일 추가 모달 */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>용어집 파일 추가</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              {selectedFile && (
                <Box p={4} bg="gray.50" borderRadius="lg">
                  <Text fontWeight="medium">선택된 파일:</Text>
                  <Text fontSize="sm">{selectedFile.name}</Text>
                  <Text fontSize="sm" color="gray.500">
                    크기: {formatFileSize(selectedFile.size)}
                  </Text>
                </Box>
              )}
              
              <FormControl>
                <FormLabel>용어집 이름</FormLabel>
                <Input 
                  placeholder="용어집 이름을 입력하세요"
                  defaultValue={selectedFile?.name.replace(/\.[^/.]+$/, "") || ''}
                />
              </FormControl>
              
              <Alert status="info" borderRadius="lg">
                <AlertIcon />
                <AlertDescription fontSize="sm">
                  용어집 파일은 "원문,번역문" 형식으로 작성해주세요. 
                  첫 번째 줄은 헤더로 처리됩니다.
                </AlertDescription>
              </Alert>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              취소
            </Button>
            <Button colorScheme="brand" onClick={handleGlossaryAdd}>
              추가
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  )
}