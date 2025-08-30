import React from 'react'
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
  Text,
  Divider,
  useColorModeValue,
  useColorMode,
  IconButton,
  Box
} from '@chakra-ui/react'
import { MoonIcon, SunIcon } from '@chakra-ui/icons'
import { useAppStore } from '../stores/appStore'
import { useTranslation } from '../hooks/useTranslation'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { config, updateConfig } = useAppStore()
  const { colorMode, setColorMode } = useColorMode()
  const { t } = useTranslation()
  
  const handleLanguageChange = (language: string) => {
    updateConfig({ uiLanguage: language })
  }
  
  const handleThemeChange = (theme: 'light' | 'dark' | 'system') => {
    updateConfig({ appearanceMode: theme })
    
    // 실제로 테마를 적용
    if (theme === 'system') {
      // 시스템 설정에 따라 자동 설정 (단순화를 위해 light로 설정)
      const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      setColorMode(systemPreference)
    } else {
      setColorMode(theme)
    }
  }

  const sectionBg = useColorModeValue('gray.50', 'gray.700')
  const buttonBg = useColorModeValue('white', 'gray.600')

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay backdropFilter="blur(4px)" />
      <ModalContent mx={4}>
        <ModalHeader>
          <HStack spacing={3}>
            <Text fontSize="xl">⚙️</Text>
            <Text>{t('settings.title')}</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* 언어 설정 */}
            <Box p={4} bg={sectionBg} borderRadius="lg">
              <VStack spacing={4} align="stretch">
                <HStack spacing={2}>
                  <Text fontSize="lg" fontWeight="semibold">🌍</Text>
                  <Text fontSize="lg" fontWeight="semibold">{t('settings.language.title').replace('🌍 ', '')}</Text>
                </HStack>
                
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="medium">{t('settings.language.interface')}</FormLabel>
                  <Select 
                    value={config.uiLanguage}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    bg={buttonBg}
                    size="sm"
                  >
                    <option value="ko">한국어 (Korean)</option>
                    <option value="en">English</option>
                  </Select>
                </FormControl>
              </VStack>
            </Box>
            
            <Divider />
            
            {/* 테마 설정 */}
            <Box p={4} bg={sectionBg} borderRadius="lg">
              <VStack spacing={4} align="stretch">
                <HStack spacing={2}>
                  <Text fontSize="lg" fontWeight="semibold">🎨</Text>
                  <Text fontSize="lg" fontWeight="semibold">{t('settings.theme.title').replace('🎨 ', '')}</Text>
                </HStack>
                
                <FormControl>
                  <FormLabel fontSize="sm" fontWeight="medium">{t('settings.theme.app')}</FormLabel>
                  <HStack spacing={2}>
                    <IconButton
                      aria-label={t('settings.theme.light')}
                      icon={<SunIcon />}
                      onClick={() => handleThemeChange('light')}
                      variant={colorMode === 'light' && config.appearanceMode !== 'system' ? 'solid' : 'outline'}
                      colorScheme="yellow"
                      size="sm"
                      flex={1}
                    />
                    <IconButton
                      aria-label={t('settings.theme.dark')}
                      icon={<MoonIcon />}
                      onClick={() => handleThemeChange('dark')}
                      variant={colorMode === 'dark' && config.appearanceMode !== 'system' ? 'solid' : 'outline'}
                      colorScheme="blue"
                      size="sm"
                      flex={1}
                    />
                    <Box
                      as="button"
                      onClick={() => handleThemeChange('system')}
                      px={3}
                      py={2}
                      borderRadius="md"
                      fontSize="sm"
                      fontWeight="medium"
                      bg={config.appearanceMode === 'system' ? 'brand.500' : buttonBg}
                      color={config.appearanceMode === 'system' ? 'white' : 'inherit'}
                      border="1px"
                      borderColor={config.appearanceMode === 'system' ? 'brand.500' : 'gray.300'}
                      _hover={{ bg: config.appearanceMode === 'system' ? 'brand.600' : 'gray.100' }}
                      flex={1}
                      textAlign="center"
                    >
                      {t('settings.theme.system')}
                    </Box>
                  </HStack>
                </FormControl>
                
                <Text fontSize="xs" color="gray.500">
                  {config.appearanceMode === 'system' && t('settings.theme.description.system')}
                  {config.appearanceMode === 'light' && t('settings.theme.description.light')}
                  {config.appearanceMode === 'dark' && t('settings.theme.description.dark')}
                </Text>
              </VStack>
            </Box>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  )
}