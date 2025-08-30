CONFIG_FILE = "translation_gui_config.json"

# Default API providers and models
DEFAULT_API_PROVIDERS = {
    "gemini": {
        "display_name": "Google Gemini",
        "models": [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-2.0-flash-exp",
            "gemini-exp-1206"
        ],
        "default_model": "gemini-1.5-flash"
    },
    "claude": {
        "display_name": "Anthropic Claude",
        "models": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ],
        "default_model": "claude-3-5-sonnet-20241022"
    },
    "openai": {
        "display_name": "OpenAI GPT",
        "models": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ],
        "default_model": "gpt-4o-mini"
    }
}

# Default error correction settings
DEFAULT_ERROR_CORRECTION = {
    "enabled": True,
    "strictness": "normal",
    "auto_fix": {
        "yaml_syntax": True,
        "preserve_format": True,
        "remove_duplicates": True,
        "fix_incomplete": False
    },
    "duplicate_strategy": "keep_first",
    "quality_thresholds": {
        "min_length_ratio": 0.3,
        "max_length_ratio": 3.0
    }
}

# Default performance settings
DEFAULT_PERFORMANCE = {
    "enable_caching": True,
    "cache_cleanup_days": 30,
    "max_concurrent_requests": 5,
    "adaptive_batching": True,
    "async_processing": True
}