import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

// 컬러 모드 설정
const config: ThemeConfig = {
  initialColorMode: 'system',
  useSystemColorMode: true,
}

// 커스텀 색상 팔레트 (CustomTkinter 스타일과 유사하게)
const colors = {
  brand: {
    50: '#eff6ff',
    100: '#dbeafe', 
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',  // Primary blue
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0', 
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',  // Green
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',  // Red
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  }
}

// 컴포넌트 기본 스타일
const components = {
  Button: {
    defaultProps: {
      size: 'md',
      variant: 'solid',
    },
    variants: {
      gradient: {
        bg: 'linear-gradient(135deg, brand.500, purple.500)',
        color: 'white',
        _hover: {
          bg: 'linear-gradient(135deg, brand.600, purple.600)',
          transform: 'translateY(-1px)',
          boxShadow: 'lg',
        },
        _active: {
          transform: 'translateY(0)',
        },
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
      },
      glass: {
        backdropFilter: 'blur(10px)',
        bg: 'whiteAlpha.200',
        border: '1px solid',
        borderColor: 'whiteAlpha.300',
        color: 'white',
        _hover: {
          bg: 'whiteAlpha.300',
        },
        _dark: {
          bg: 'blackAlpha.200',
          borderColor: 'whiteAlpha.200',
        }
      }
    },
    sizes: {
      xl: {
        h: 14,
        minW: 14,
        fontSize: 'lg',
        px: 8,
        py: 4,
      },
    },
  },
  
  Card: {
    baseStyle: {
      container: {
        borderRadius: 'xl',
        overflow: 'hidden',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        _hover: {
          transform: 'translateY(-2px)',
          boxShadow: 'xl',
        }
      }
    },
    variants: {
      glass: {
        container: {
          backdropFilter: 'blur(10px)',
          bg: 'whiteAlpha.100',
          border: '1px solid',
          borderColor: 'whiteAlpha.200',
          _dark: {
            bg: 'blackAlpha.100',
            borderColor: 'whiteAlpha.100',
          }
        }
      }
    }
  },

  Tabs: {
    variants: {
      modern: {
        tab: {
          borderRadius: 'lg',
          fontWeight: 'medium',
          _selected: {
            bg: 'brand.500',
            color: 'white',
            boxShadow: 'md',
          },
          _hover: {
            bg: 'gray.100',
            _dark: {
              bg: 'gray.700',
            }
          },
          transition: 'all 0.2s',
        },
        tablist: {
          borderBottom: 'none',
          bg: 'gray.50',
          borderRadius: 'xl',
          p: 1,
          _dark: {
            bg: 'gray.800',
          }
        },
      }
    }
  },

  Progress: {
    baseStyle: {
      track: {
        borderRadius: 'full',
        bg: 'gray.200',
        _dark: {
          bg: 'gray.700'
        }
      },
      filledTrack: {
        borderRadius: 'full',
        bg: 'linear-gradient(90deg, success.400, success.600)',
        transition: 'all 0.3s ease',
      }
    },
    sizes: {
      xl: {
        track: {
          h: 6,
        }
      }
    }
  }
}

// 폰트 설정
const fonts = {
  heading: `'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif`,
  body: `'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif`,
}

// 그림자 설정
const shadows = {
  outline: '0 0 0 3px rgba(59, 130, 246, 0.5)',
  glass: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
}

export const theme = extendTheme({
  config,
  colors,
  components,
  fonts,
  shadows,
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
        color: props.colorMode === 'dark' ? 'whiteAlpha.900' : 'gray.800',
      },
    }),
  },
})