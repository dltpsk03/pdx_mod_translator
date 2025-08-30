import React, { useEffect, useRef, useState } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  IconButton,
  Button,
  Input,
  Select,
  Tooltip,
  useColorModeValue,
  Flex,
  Spacer,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
  InputGroup,
  InputLeftElement
} from '@chakra-ui/react'
import {
  DeleteIcon,
  DownloadIcon,
  SearchIcon,
  SettingsIcon,
  ChevronDownIcon,
  TimeIcon
} from '@chakra-ui/icons'
import { useAppStore } from '../stores/appStore'
import type { LogMessage } from '../stores/appStore'

export const LogPanel: React.FC = () => {
  const { logs, clearLogs } = useAppStore()
  const [filter, setFilter] = useState<'all' | 'info' | 'warning' | 'error' | 'success'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [autoScroll, setAutoScroll] = useState(true)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const { isOpen: isMenuOpen, onOpen: onMenuOpen, onClose: onMenuClose } = useDisclosure()
  
  // 스타일 설정
  const panelBg = useColorModeValue('white', 'gray.800')
  const logBg = useColorModeValue('gray.50', 'gray.700')
  const headerBg = useColorModeValue('gray.100', 'gray.600')
  
  // 자동 스크롤
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [logs, autoScroll])
  
  // 로그 필터링
  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.level === filter
    const matchesSearch = searchTerm === '' || 
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.details && log.details.toLowerCase().includes(searchTerm.toLowerCase()))
    
    return matchesFilter && matchesSearch
  })
  
  // 로그 레벨별 색상
  const getLogColor = (level: string) => {
    switch (level) {
      case 'error': return 'red'
      case 'warning': return 'yellow'
      case 'success': return 'green'
      case 'info':
      default: return 'blue'
    }
  }
  
  // 로그 레벨별 아이콘
  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error': return '❌'
      case 'warning': return '⚠️'
      case 'success': return '✅'
      case 'info':
      default: return 'ℹ️'
    }
  }
  
  // 시간 포맷팅
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }
  
  // 로그 내보내기
  const handleExportLogs = () => {
    const logText = filteredLogs
      .map(log => `[${formatTime(log.timestamp)}] ${log.level.toUpperCase()}: ${log.message}${log.details ? `\n  ${log.details}` : ''}`)
      .join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pdx_translator_logs_${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  // 로그 통계
  const getLogStats = () => {
    const stats = {
      total: logs.length,
      info: logs.filter(log => log.level === 'info').length,
      warning: logs.filter(log => log.level === 'warning').length,
      error: logs.filter(log => log.level === 'error').length,
      success: logs.filter(log => log.level === 'success').length,
    }
    return stats
  }
  
  const stats = getLogStats()
  
  return (
    <Box h="full" bg={panelBg} borderRadius="xl" overflow="hidden">
      {/* 헤더 */}
      <Box bg={headerBg} px={4} py={3} borderBottom="1px" borderColor="gray.200">
        <Flex align="center">
          <HStack spacing={3}>
            <Text fontSize="lg" fontWeight="bold" color="brand.500">
              📋 실행 로그
            </Text>
            <Badge variant="outline" colorScheme="gray">
              {filteredLogs.length} / {logs.length}
            </Badge>
          </HStack>
          
          <Spacer />
          
          <HStack spacing={2}>
            {/* 필터 */}
            <Select
              size="sm"
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              w="120px"
            >
              <option value="all">전체</option>
              <option value="info">정보</option>
              <option value="success">성공</option>
              <option value="warning">경고</option>
              <option value="error">오류</option>
            </Select>
            
            {/* 검색 */}
            <InputGroup w="150px">
              <InputLeftElement h="32px">
                <SearchIcon color="gray.400" />
              </InputLeftElement>
              <Input
                size="sm"
                placeholder="로그 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            
            {/* 옵션 메뉴 */}
            <Menu isOpen={isMenuOpen} onOpen={onMenuOpen} onClose={onMenuClose}>
              <MenuButton
                as={IconButton}
                icon={<SettingsIcon />}
                size="sm"
                variant="ghost"
              />
              <MenuList>
                <MenuItem
                  icon={<TimeIcon />}
                  onClick={() => setAutoScroll(!autoScroll)}
                >
                  자동 스크롤 {autoScroll ? '끄기' : '켜기'}
                </MenuItem>
                <MenuItem
                  icon={<DownloadIcon />}
                  onClick={handleExportLogs}
                >
                  로그 내보내기
                </MenuItem>
                <MenuItem
                  icon={<DeleteIcon />}
                  onClick={clearLogs}
                  color="red.500"
                >
                  로그 지우기
                </MenuItem>
              </MenuList>
            </Menu>
          </HStack>
        </Flex>
        
        {/* 통계 */}
        <HStack spacing={4} mt={3}>
          <HStack spacing={2}>
            <Badge colorScheme="blue" variant="subtle" fontSize="xs">
              정보: {stats.info}
            </Badge>
            <Badge colorScheme="green" variant="subtle" fontSize="xs">
              성공: {stats.success}
            </Badge>
            <Badge colorScheme="yellow" variant="subtle" fontSize="xs">
              경고: {stats.warning}
            </Badge>
            <Badge colorScheme="red" variant="subtle" fontSize="xs">
              오류: {stats.error}
            </Badge>
          </HStack>
          
          <Spacer />
          
          {logs.length > 0 && (
            <Text fontSize="xs" color="gray.500">
              최근 업데이트: {formatTime(logs[0].timestamp)}
            </Text>
          )}
        </HStack>
      </Box>
      
      {/* 로그 내용 */}
      <Box
        ref={logContainerRef}
        flex={1}
        overflowY="auto"
        bg={logBg}
        maxH="calc(100% - 120px)"
        css={{
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: useColorModeValue('#f1f1f1', '#2d2d2d'),
          },
          '&::-webkit-scrollbar-thumb': {
            background: useColorModeValue('#c1c1c1', '#6b6b6b'),
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: useColorModeValue('#a8a8a8', '#8b8b8b'),
          },
        }}
      >
        {filteredLogs.length === 0 ? (
          <Box p={8} textAlign="center">
            <Text color="gray.500" fontSize="lg">
              {searchTerm || filter !== 'all' ? '조건에 맞는 로그가 없습니다' : '로그가 없습니다'}
            </Text>
            <Text color="gray.400" fontSize="sm" mt={2}>
              {searchTerm || filter !== 'all' 
                ? '필터 또는 검색 조건을 변경해보세요' 
                : '번역을 시작하면 로그가 표시됩니다'
              }
            </Text>
          </Box>
        ) : (
          <VStack spacing={0} align="stretch" p={2}>
            {filteredLogs.map((log, index) => (
              <Box
                key={log.id}
                p={3}
                borderBottom="1px"
                borderColor="gray.200"
                _hover={{ bg: useColorModeValue('gray.100', 'gray.600') }}
                transition="background-color 0.2s"
              >
                <HStack align="start" spacing={3}>
                  <Text fontSize="lg">{getLogIcon(log.level)}</Text>
                  
                  <VStack align="start" spacing={1} flex={1}>
                    <HStack spacing={2} w="full">
                      <Badge
                        colorScheme={getLogColor(log.level)}
                        variant="subtle"
                        size="sm"
                      >
                        {log.level.toUpperCase()}
                      </Badge>
                      
                      <Text fontSize="xs" color="gray.500">
                        {formatTime(log.timestamp)}
                      </Text>
                      
                      <Spacer />
                      
                      <Text fontSize="xs" color="gray.400">
                        #{logs.length - index}
                      </Text>
                    </HStack>
                    
                    <Text fontSize="sm" fontWeight="medium" color="gray.800" _dark={{ color: 'gray.200' }}>
                      {log.message}
                    </Text>
                    
                    {log.details && (
                      <Text 
                        fontSize="xs" 
                        color="gray.600" 
                        _dark={{ color: 'gray.400' }}
                        fontFamily="mono"
                        bg={useColorModeValue('gray.100', 'gray.700')}
                        p={2}
                        borderRadius="md"
                        w="full"
                      >
                        {log.details}
                      </Text>
                    )}
                  </VStack>
                </HStack>
              </Box>
            ))}
          </VStack>
        )}
      </Box>
      
      {/* 하단 정보 바 */}
      <Box 
        px={4} 
        py={2} 
        borderTop="1px" 
        borderColor="gray.200" 
        bg={headerBg}
      >
        <HStack justify="space-between" fontSize="xs" color="gray.500">
          <Text>
            {filteredLogs.length > 0 && `${filteredLogs.length}개 항목 표시`}
          </Text>
          <HStack spacing={4}>
            <Text>자동 스크롤: {autoScroll ? '켜짐' : '꺼짐'}</Text>
            {searchTerm && <Text>검색: "{searchTerm}"</Text>}
            {filter !== 'all' && <Text>필터: {filter}</Text>}
          </HStack>
        </HStack>
      </Box>
    </Box>
  )
}