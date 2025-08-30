import React from 'react'
import {
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Box,
  useColorModeValue
} from '@chakra-ui/react'
import { useAppStore } from '../stores/appStore'
import { BasicSettingsPanel } from './panels/BasicSettingsPanel'
import { AdvancedSettingsPanel } from './panels/AdvancedSettingsPanel'
import { PromptGlossaryPanel } from './panels/PromptGlossaryPanel'
import { ErrorCorrectionPanel } from './panels/ErrorCorrectionPanel'
import { GamePromptsSelector } from './prompts/GamePromptsSelector'
import { PerformanceOptimizer } from './optimizer/PerformanceOptimizer'
import { TranslationDashboard } from './dashboard/TranslationDashboard'
import { ConsistencyChecker } from './consistency/ConsistencyChecker'
import { CheckpointManager } from './checkpoint/CheckpointManager'
import { LivePreviewPanel } from './preview/LivePreviewPanel'

export const MainTabs: React.FC = () => {
  const { activeTab, setActiveTab } = useAppStore()
  
  // 탭 인덱스와 문자열 변환
  const tabMap = {
    'basic': 0,
    'advanced': 1,
    'prompt': 2,
    'error': 3,
    'game': 4,
    'performance': 5,
    'dashboard': 6,
    'consistency': 7,
    'checkpoint': 8,
    'preview': 9
  }
  
  const reverseTabMap = ['basic', 'advanced', 'prompt', 'error', 'game', 'performance', 'dashboard', 'consistency', 'checkpoint', 'preview']
  
  const handleTabChange = (index: number) => {
    setActiveTab(reverseTabMap[index])
  }
  
  // 탭 스타일
  const tabBg = useColorModeValue('gray.50', 'gray.700')
  const selectedTabBg = useColorModeValue('white', 'gray.800')
  const selectedTabColor = useColorModeValue('brand.500', 'brand.300')
  
  return (
    <Box p={6}>
      <Tabs
        index={tabMap[activeTab as keyof typeof tabMap] || 0}
        onChange={handleTabChange}
        variant="soft-rounded"
        colorScheme="brand"
      >
        <TabList 
          bg={tabBg}
          p={2}
          borderRadius="xl"
          mb={8}
          justifyContent="space-around"
        >
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            ⚙️ 기본 설정
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            🔧 고급 설정
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            📝 프롬프트/용어집
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            🔍 오류 교정
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            🎮 게임 프롬프트
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            ⚡ 성능 최적화
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            📊 번역 대시보드
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            🔍 일관성 검사
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            📋 체크포인트
          </Tab>
          <Tab
            fontSize="md"
            fontWeight="semibold"
            px={6}
            py={3}
            borderRadius="lg"
            _selected={{
              bg: selectedTabBg,
              color: selectedTabColor,
              shadow: 'md',
              transform: 'translateY(-1px)'
            }}
            _hover={{
              bg: useColorModeValue('gray.100', 'gray.600')
            }}
            transition="all 0.2s"
          >
            👁️ 실시간 미리보기
          </Tab>
        </TabList>

        <TabPanels>
          <TabPanel p={0}>
            <BasicSettingsPanel />
          </TabPanel>
          <TabPanel p={0}>
            <AdvancedSettingsPanel />
          </TabPanel>
          <TabPanel p={0}>
            <PromptGlossaryPanel />
          </TabPanel>
          <TabPanel p={0}>
            <ErrorCorrectionPanel />
          </TabPanel>
          <TabPanel p={0}>
            <GamePromptsSelector />
          </TabPanel>
          <TabPanel p={0}>
            <PerformanceOptimizer />
          </TabPanel>
          <TabPanel p={0}>
            <TranslationDashboard />
          </TabPanel>
          <TabPanel p={0}>
            <ConsistencyChecker />
          </TabPanel>
          <TabPanel p={0}>
            <CheckpointManager />
          </TabPanel>
          <TabPanel p={0}>
            <LivePreviewPanel />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}