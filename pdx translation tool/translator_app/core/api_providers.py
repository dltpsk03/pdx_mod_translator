"""
API providers abstraction layer for multi-API support
Supports Gemini, Claude (Anthropic), and OpenAI APIs
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    from google import genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class APIProvider(ABC):
    """Abstract base class for API providers"""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 1.0)
        
        # 생성 매개변수들
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 0.9)
        self.top_k = kwargs.get('top_k', 40)
        self.max_tokens = kwargs.get('max_tokens', 4096)
        
    @abstractmethod
    async def translate_batch(self, texts: List[str], prompt: str, glossary: str = "") -> List[str]:
        """Translate a batch of texts"""
        pass
    
    @abstractmethod
    def get_max_batch_size(self) -> int:
        """Get maximum recommended batch size for this provider"""
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> float:
        """Get recommended delay between requests in seconds"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate API connection and credentials"""
        pass
    
    @abstractmethod
    def get_supported_parameters(self) -> Dict[str, bool]:
        """Get which generation parameters are supported by this provider/model"""
        pass
    
    def get_generation_config(self) -> Dict[str, Any]:
        """Get generation configuration based on supported parameters"""
        supported = self.get_supported_parameters()
        config = {}
        
        if supported.get('temperature', False):
            config['temperature'] = self.temperature
        if supported.get('top_p', False):
            config['top_p'] = self.top_p  
        if supported.get('top_k', False):
            config['top_k'] = self.top_k
        if supported.get('max_tokens', False):
            config['max_tokens'] = self.max_tokens
            
        return config


class GeminiProvider(APIProvider):
    """Google Gemini API provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(api_key, model, **kwargs)
        if not genai:
            raise ImportError("google-genai package not installed")
        
        self.client = genai.Client(api_key=api_key)
        
    async def translate_batch(self, texts: List[str], prompt: str, glossary: str = "") -> List[str]:
        """Translate using Gemini API"""
        try:
            full_prompt = self._build_prompt(prompt, glossary, texts)
            
            # 생성 설정 구성
            generation_config = self.get_generation_config()
            
            # Generate content using new API - simplified config
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
            )
            
            if response and response.text:
                return self._parse_response(response.text, len(texts))
            else:
                raise Exception("Empty response from Gemini API")
                
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            raise
    
    def get_max_batch_size(self) -> int:
        if "pro" in self.model.lower():
            return 20
        elif "flash" in self.model.lower():
            return 50
        return 30
    
    def get_rate_limit(self) -> float:
        if "pro" in self.model.lower():
            return 2.0
        return 1.0
    
    def validate_connection(self) -> bool:
        try:
            test_response = self.client.models.generate_content(
                model=self.model,
                contents="Test connection"
            )
            return bool(test_response and test_response.text)
        except:
            return False
    
    def get_supported_parameters(self) -> Dict[str, bool]:
        """Gemini supports temperature, top_p, top_k, max_tokens"""
        return {
            'temperature': True,
            'top_p': True, 
            'top_k': True,
            'max_tokens': True
        }
    
    def _build_prompt(self, base_prompt: str, glossary: str, texts: List[str]) -> str:
        """Build complete prompt for Gemini"""
        prompt_parts = [base_prompt]
        
        if glossary.strip():
            prompt_parts.append(f"\n용어집 (Glossary):\n{glossary}")
        
        prompt_parts.append("\n번역할 텍스트:")
        for i, text in enumerate(texts, 1):
            prompt_parts.append(f"{i}. {text}")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str, expected_count: int) -> List[str]:
        """Parse Gemini response into list of translations"""
        lines = response_text.strip().split('\n')
        translations = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('번역'):
                # Remove numbering if present
                if line.startswith(tuple(f"{i}." for i in range(1, 100))):
                    line = line.split('.', 1)[1].strip()
                translations.append(line)
        
        # Ensure we return the expected number of translations
        while len(translations) < expected_count:
            translations.append("[번역 실패]")
        
        return translations[:expected_count]


class ClaudeProvider(APIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, model, **kwargs)
        if not anthropic:
            raise ImportError("anthropic package not installed")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
    async def translate_batch(self, texts: List[str], prompt: str, glossary: str = "") -> List[str]:
        """Translate using Claude API"""
        try:
            full_prompt = self._build_prompt(prompt, glossary, texts)
            
            # 생성 설정 구성
            generation_config = self.get_generation_config()
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=generation_config.get('max_tokens', 4096),
                    temperature=generation_config.get('temperature', 0.7),
                    top_p=generation_config.get('top_p', 0.9),
                    messages=[{"role": "user", "content": full_prompt}]
                )
            )
            
            if response and response.content:
                return self._parse_response(response.content[0].text, len(texts))
            else:
                raise Exception("Empty response from Claude API")
                
        except Exception as e:
            logging.error(f"Claude API error: {e}")
            raise
    
    def get_max_batch_size(self) -> int:
        if "opus" in self.model.lower():
            return 15
        elif "sonnet" in self.model.lower():
            return 40
        return 25
    
    def get_rate_limit(self) -> float:
        if "opus" in self.model.lower():
            return 3.0
        return 1.5
    
    def validate_connection(self) -> bool:
        try:
            test_response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": "Test connection"}]
            )
            return bool(test_response and test_response.content)
        except:
            return False
    
    def get_supported_parameters(self) -> Dict[str, bool]:
        """Claude supports temperature, top_p, max_tokens (no top_k)"""
        return {
            'temperature': True,
            'top_p': True, 
            'top_k': False,  # Claude doesn't support top_k
            'max_tokens': True
        }
    
    def _build_prompt(self, base_prompt: str, glossary: str, texts: List[str]) -> str:
        """Build complete prompt for Claude"""
        prompt_parts = [base_prompt]
        
        if glossary.strip():
            prompt_parts.append(f"\n용어집 (Glossary):\n{glossary}")
        
        prompt_parts.append("\n번역할 텍스트 (각 줄을 개별적으로 번역해주세요):")
        for i, text in enumerate(texts, 1):
            prompt_parts.append(f"{i}. {text}")
        
        prompt_parts.append("\n번역된 결과만 순서대로 출력해주세요 (번호나 설명 없이):")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str, expected_count: int) -> List[str]:
        """Parse Claude response into list of translations"""
        lines = response_text.strip().split('\n')
        translations = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('번역'):
                # Remove numbering if present
                if line.startswith(tuple(f"{i}." for i in range(1, 100))):
                    line = line.split('.', 1)[1].strip()
                translations.append(line)
        
        # Ensure we return the expected number of translations
        while len(translations) < expected_count:
            translations.append("[번역 실패]")
        
        return translations[:expected_count]


class OpenAIProvider(APIProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        if not OpenAI:
            raise ImportError("openai package not installed")
        
        self.client = OpenAI(api_key=api_key)
        
    async def translate_batch(self, texts: List[str], prompt: str, glossary: str = "") -> List[str]:
        """Translate using OpenAI API"""
        try:
            full_prompt = self._build_prompt(prompt, glossary, texts)
            
            # 생성 설정 구성
            generation_config = self.get_generation_config()
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}],
                    **generation_config
                )
            )
            
            if response and response.choices:
                return self._parse_response(response.choices[0].message.content, len(texts))
            else:
                raise Exception("Empty response from OpenAI API")
                
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            raise
    
    def get_max_batch_size(self) -> int:
        if "gpt-4" in self.model.lower():
            if "turbo" in self.model.lower():
                return 35
            return 25
        elif "gpt-3.5" in self.model.lower():
            return 45
        return 30
    
    def get_rate_limit(self) -> float:
        if "gpt-4" in self.model.lower() and "turbo" not in self.model.lower():
            return 2.5
        return 1.2
    
    def validate_connection(self) -> bool:
        try:
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            return bool(test_response and test_response.choices)
        except:
            return False
    
    def get_supported_parameters(self) -> Dict[str, bool]:
        """OpenAI parameter support varies by model"""
        # GPT-5 계열 모델은 temperature, top_p 지원 안함
        is_gpt5_series = 'gpt-5' in self.model.lower()
        
        return {
            'temperature': not is_gpt5_series,  # GPT-5 계열은 지원 안함
            'top_p': not is_gpt5_series,        # GPT-5 계열은 지원 안함
            'top_k': False,                     # OpenAI는 모든 모델에서 top_k 지원 안함
            'max_tokens': True                  # 모든 모델에서 지원
        }
    
    def _build_prompt(self, base_prompt: str, glossary: str, texts: List[str]) -> str:
        """Build complete prompt for OpenAI"""
        prompt_parts = [base_prompt]
        
        if glossary.strip():
            prompt_parts.append(f"\n용어집 (Glossary):\n{glossary}")
        
        prompt_parts.append("\n번역할 텍스트:")
        for i, text in enumerate(texts, 1):
            prompt_parts.append(f"{i}. {text}")
        
        prompt_parts.append("\n각 번역을 새 줄에 순서대로 출력해주세요 (번호 없이).")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str, expected_count: int) -> List[str]:
        """Parse OpenAI response into list of translations"""
        lines = response_text.strip().split('\n')
        translations = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('번역'):
                # Remove numbering if present
                if line.startswith(tuple(f"{i}." for i in range(1, 100))):
                    line = line.split('.', 1)[1].strip()
                translations.append(line)
        
        # Ensure we return the expected number of translations
        while len(translations) < expected_count:
            translations.append("[번역 실패]")
        
        return translations[:expected_count]


class APIProviderFactory:
    """Factory class to create API providers"""
    
    PROVIDERS = {
        "gemini": GeminiProvider,
        "claude": ClaudeProvider, 
        "openai": OpenAIProvider
    }
    
    MODELS = {
        "gemini": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite"
        ],
        "claude": [
            "claude-opus-4-1-20250805",
            "claude-opus-4-20250514", 
            "claude-sonnet-4-20250514",
            "claude-3-7-sonnet-latest",
            "claude-3-5-haiku-latest"
        ],
        "openai": [
            "gpt-5-2025-08-07",
            "gpt-5-mini-2025-08-07", 
            "gpt-5-nano-2025-08-07",
            "gpt-4.1-2025-04-14",
            "o3-2025-04-16"
        ]
    }
    
    # Internal test models (hidden from UI)
    TEST_MODELS = {
        "gemini": "gemini-1.5-flash",
        "claude": "claude-3-5-haiku-20241022", 
        "openai": "gpt-4.1-nano-2025-04-14"
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, api_key: str, model: str, **kwargs) -> APIProvider:
        """Create an API provider instance"""
        if provider_type not in cls.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_type}")
        
        provider_class = cls.PROVIDERS[provider_type]
        return provider_class(api_key, model, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        available = []
        for provider_type, provider_class in cls.PROVIDERS.items():
            try:
                # Check if required package is available
                if provider_type == "gemini" and genai:
                    available.append(provider_type)
                elif provider_type == "claude" and anthropic:
                    available.append(provider_type)
                elif provider_type == "openai" and OpenAI:
                    available.append(provider_type)
            except ImportError:
                continue
        return available
    
    @classmethod
    def validate_provider_setup(cls, provider_type: str, api_key: str) -> Tuple[bool, str]:
        """Validate provider setup and return user-friendly status"""
        try:
            if not api_key or api_key.strip() == "":
                return False, "API 키를 입력해주세요."
            
            if provider_type == "gemini":
                if not genai:
                    return False, "Google Gemini 패키지가 설치되지 않았습니다. 'pip install google-genai'로 설치해주세요."
                # Test connection with cheapest model (2025-08-25)
                try:
                    # Create client and test with minimal request
                    client = genai.Client(api_key=api_key)
                    test_model = cls.TEST_MODELS.get("gemini", "gemini-1.5-flash")
                    response = client.models.generate_content(
                        model=test_model,
                        contents="test"
                    )
                    return True, "연결 성공"
                        
                except Exception as e:
                    error_str = str(e).lower()
                    if "api_key_invalid" in error_str or "invalid api key" in error_str or "authentication" in error_str or "401" in error_str:
                        return False, "잘못된 API 키입니다. API 키를 확인해주세요."
                    elif "quota" in error_str or "limit" in error_str or "429" in error_str:
                        return False, "API 사용 한도를 초과했습니다. 잠시 후 다시 시도하거나 결제 상태를 확인해주세요."
                    elif "permission" in error_str or "403" in error_str:
                        return False, "API 키에 해당 모델 사용 권한이 없습니다."
                    elif "network" in error_str or "connection" in error_str:
                        return False, "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인해주세요."
                    else:
                        return False, f"연결 실패: {str(e)[:100]}..."
                    
            elif provider_type == "claude":
                if not anthropic:
                    return False, "Anthropic Claude 패키지가 설치되지 않았습니다. 'pip install anthropic'로 설치해주세요."
                try:
                    # Just test client initialization - safest method
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Try a minimal API call to validate the key
                    try:
                        # Use test model for connection validation
                        test_model = cls.TEST_MODELS.get("claude", "claude-3-5-haiku-20241022")
                        response = client.messages.create(
                            model=test_model,
                            max_tokens=1,
                            messages=[{"role": "user", "content": "test"}]
                        )
                        return True, "연결 성공"
                    except Exception as api_error:
                        error_str = str(api_error).lower()
                        if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
                            return False, "잘못된 API 키입니다. API 키를 확인해주세요."
                        elif "quota" in error_str or "limit" in error_str or "429" in error_str:
                            return False, "API 사용 한도를 초과했습니다."
                        else:
                            return True, "연결 성공 (클라이언트 초기화 완료)"
                            
                except Exception as e:
                    error_str = str(e).lower()
                    if "authentication" in error_str or "unauthorized" in error_str:
                        return False, "잘못된 API 키입니다. API 키를 확인해주세요."
                    return False, f"연결 실패: {str(e)[:100]}..."
                    
            elif provider_type == "openai":
                if not OpenAI:
                    return False, "OpenAI 패키지가 설치되지 않았습니다. 'pip install openai'로 설치해주세요."
                try:
                    client = OpenAI(api_key=api_key)
                    
                    # Test with cheapest model (2025-08-25)
                    try:
                        test_model = cls.TEST_MODELS.get("openai", "gpt-4.1-nano-2025-04-14")
                        response = client.chat.completions.create(
                            model=test_model,
                            messages=[{"role": "user", "content": "test"}],
                            max_tokens=1
                        )
                        return True, "연결 성공"
                    except Exception as api_error:
                        error_str = str(api_error).lower()
                        if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str:
                            return False, "잘못된 API 키입니다. API 키를 확인해주세요."
                        elif "quota" in error_str or "limit" in error_str or "429" in error_str:
                            return False, "API 사용 한도를 초과했습니다."
                        else:
                            return True, "연결 성공 (클라이언트 초기화 완료)"
                            
                except Exception as e:
                    error_str = str(e).lower()
                    if "authentication" in error_str or "unauthorized" in error_str:
                        return False, "잘못된 API 키입니다. API 키를 확인해주세요."
                    return False, f"연결 실패: {str(e)[:100]}..."
            else:
                return False, f"지원되지 않는 API 제공자: {provider_type}"
                
        except Exception as e:
            return False, f"설정 확인 중 오류가 발생했습니다: {str(e)}"
    
    @classmethod
    def get_model_display_name(cls, model_key: str) -> str:
        """Get user-friendly display name for model"""
        display_names = {
            # OpenAI models
            "gpt-5-2025-08-07": "GPT-5",
            "gpt-5-mini-2025-08-07": "GPT-5 Mini",
            "gpt-5-nano-2025-08-07": "GPT-5 Nano",
            "gpt-4.1-2025-04-14": "GPT-4.1",
            "o3-2025-04-16": "O3",
            
            # Claude models
            "claude-opus-4-1-20250805": "Claude Opus 4.1 (2025-08-05)",
            "claude-opus-4-20250514": "Claude Opus 4 (2025-05-14)",
            "claude-sonnet-4-20250514": "Claude Sonnet 4 (2025-05-14)",
            "claude-3-7-sonnet-latest": "Claude 3.7 Sonnet (Latest)",
            "claude-3-5-haiku-latest": "Claude 3.5 Haiku (Latest)",
            
            # Gemini models
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "gemini-2.5-flash": "Gemini 2.5 Flash", 
            "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite",
            "gemini-2.0-flash": "Gemini 2.0 Flash",
            "gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite"
        }
        return display_names.get(model_key, model_key)
    
    @classmethod
    def get_models_for_provider(cls, provider_type: str) -> List[str]:
        """Get available models for a provider"""
        return cls.MODELS.get(provider_type, [])