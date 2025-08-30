import React, { useEffect, useState } from 'react'
import {
  Box,
  Container,
  Flex,
  Heading,
  HStack,
  IconButton,
  Spacer,
  useColorMode,
  useColorModeValue,
  VStack,
  Text,
  Badge,
  Divider,
  useDisclosure
} from '@chakra-ui/react'
import { MoonIcon, SunIcon, SettingsIcon } from '@chakra-ui/icons'
import { MainTabs } from './components/MainTabs'
import { ControlPanel } from './components/ControlPanel'
import { LogPanel } from './components/LogPanel'
import { SettingsModal } from './components/SettingsModal'
import { useAppStore } from './stores/appStore'
import { useWebSocket } from './hooks/useWebSocket'
import { useTranslation } from './hooks/useTranslation'

const App: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode()
  const { isConnected, connectionStatus } = useAppStore()
  const { isOpen: isSettingsOpen, onOpen: onSettingsOpen, onClose: onSettingsClose } = useDisclosure()
  const { t } = useTranslation()
  
  // WebSocket 연결
  useWebSocket()
  
  // 배경 그라데이션
  const bgGradient = useColorModeValue(
    'linear(to-br, gray.50, blue.50)',
    'linear(to-br, gray.900, blue.900)'
  )
  
  // 헤더 배경
  const headerBg = useColorModeValue('white', 'gray.800')
  const headerShadow = useColorModeValue('sm', 'dark-lg')
  
  return (
    <Box minH="100vh" bgGradient={bgGradient}>
      {/* 헤더 */}
      <Box 
        bg={headerBg} 
        shadow={headerShadow} 
        borderBottom="1px"
        borderColor={useColorModeValue('gray.200', 'gray.700')}
        position="sticky"
        top={0}
        zIndex={100}
        backdropFilter="blur(10px)"
      >
        <Container maxW="container.xl" py={4}>
          <Flex align="center">
            {/* 로고 및 제목 */}
            <HStack spacing={3}>
              <Box fontSize="2xl">🚀</Box>
              <VStack align="start" spacing={0}>
                <Heading size="lg" color="brand.500">
                  {t('header.title')}
                </Heading>
                <Text fontSize="sm" color="gray.500" fontWeight="medium">
                  {t('header.subtitle')}
                </Text>
              </VStack>
            </HStack>
            
            <Spacer />
            
            {/* 상태 및 컨트롤 */}
            <HStack spacing={4}>
              {/* 연결 상태 */}
              <HStack spacing={2}>
                <Badge 
                  colorScheme={isConnected ? 'green' : 'red'} 
                  variant="solid"
                  borderRadius="full"
                  px={3}
                  py={1}
                >
                  {isConnected ? t('header.connected') : t('header.disconnected')}
                </Badge>
                <Text fontSize="sm" color="gray.500">
                  {connectionStatus}
                </Text>
              </HStack>
              
              <Divider orientation="vertical" h={6} />
              
              {/* 테마 토글 */}
              <IconButton
                aria-label="테마 변경"
                icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                onClick={toggleColorMode}
                variant="ghost"
                size="md"
                borderRadius="full"
              />
              
              {/* 설정 버튼 */}
              <IconButton
                aria-label="설정"
                icon={<SettingsIcon />}
                onClick={onSettingsOpen}
                variant="ghost"
                size="md"
                borderRadius="full"
              />
            </HStack>
          </Flex>
        </Container>
      </Box>
      
      {/* 메인 컨텐츠 */}
      <Container maxW="container.xl" py={6}>
        <VStack spacing={6} align="stretch">
          {/* 메인 탭 영역 */}
          <Box
            bg={useColorModeValue('white', 'gray.800')}
            borderRadius="2xl"
            shadow="lg"
            border="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
            overflow="hidden"
            className="fade-in"
          >
            <MainTabs />
          </Box>
          
          {/* 컨트롤 패널 */}
          <Box
            bg={useColorModeValue('white', 'gray.800')}
            borderRadius="xl"
            shadow="md"
            border="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
            overflow="hidden"
            className="fade-in"
            style={{ animationDelay: '0.1s' }}
          >
            <ControlPanel />
          </Box>
          
          {/* 로그 패널 */}
          <Box
            bg={useColorModeValue('white', 'gray.800')}
            borderRadius="xl"
            shadow="md"
            border="1px"
            borderColor={useColorModeValue('gray.200', 'gray.700')}
            overflow="hidden"
            className="fade-in"
            style={{ animationDelay: '0.2s' }}
            h="300px"
          >
            <LogPanel />
          </Box>
        </VStack>
      </Container>
      
      {/* 푸터 */}
      <Box
        as="footer"
        py={8}
        mt={12}
        borderTop="1px"
        borderColor={useColorModeValue('gray.200', 'gray.700')}
      >
        <Container maxW="container.xl">
          <Text 
            textAlign="center" 
            color="gray.500" 
            fontSize="sm"
          >
            © 2025 PDX Mod Translator Professional Edition. 
            Made with ❤️ for the Paradox Gaming Community.
          </Text>
        </Container>
      </Box>
      
      {/* 설정 모달 */}
      <SettingsModal isOpen={isSettingsOpen} onClose={onSettingsClose} />
    </Box>
  )
}

export default App