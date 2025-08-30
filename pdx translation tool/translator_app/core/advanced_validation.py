"""
Advanced translation validation system for detecting and correcting specific translation errors
Focuses on language completion, YAML structure, and line preservation
"""

import re
import logging
import yaml
import os
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import unicodedata


class AdvancedTranslationValidator:
    """Advanced validator for specific translation error patterns"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Validation levels with different strictness
        self.validation_levels = {
            'off': {
                'enabled': False,
                'check_language_completion': False,
                'check_yaml_quotes': False,
                'check_line_count': False,
                'check_key_translation': False,
                'use_retry_logic': False
            },
            'basic': {
                'enabled': True,
                'check_language_completion': True,
                'check_yaml_quotes': True,
                'check_line_count': False,
                'check_key_translation': True,
                'use_retry_logic': False,
                'untranslated_ratio': 0.3,  # More lenient
                'yaml_error_ratio': 0.2
            },
            'standard': {
                'enabled': True,
                'check_language_completion': True,
                'check_yaml_quotes': True,
                'check_line_count': True,
                'check_key_translation': True,
                'use_retry_logic': True,
                'untranslated_ratio': 0.15,
                'yaml_error_ratio': 0.1,
                'line_count_tolerance': 0.05
            },
            'strict': {
                'enabled': True,
                'check_language_completion': True,
                'check_yaml_quotes': True,
                'check_line_count': True,
                'check_key_translation': True,
                'use_retry_logic': True,
                'untranslated_ratio': 0.05,
                'yaml_error_ratio': 0.05,
                'line_count_tolerance': 0.02
            }
        }
        
        # Current validation level
        self.current_level = self.config.get('validation_level', 'standard')
        self.level_config = self.validation_levels[self.current_level]
        
        # Error rate threshold for automatic activation
        self.auto_activation_threshold = self.config.get('auto_activation_threshold', 0.2)  # 20% 오류율
        self.current_session_errors = []
        
        # Language detection patterns
        self.language_patterns = {
            'korean': re.compile(r'[가-힣]'),
            'chinese': re.compile(r'[\u4e00-\u9fff]'),
            'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]'),
            'cyrillic': re.compile(r'[\u0400-\u04ff]'),
            'arabic': re.compile(r'[\u0600-\u06ff]'),
            'thai': re.compile(r'[\u0e00-\u0e7f]'),
        }
        
        # YAML patterns for Paradox games
        self.yaml_patterns = {
            'key_value_pair': re.compile(r'^(\s*)([a-zA-Z0-9_\.]+):(\d+)?\s*(.*)$'),
            'quoted_value': re.compile(r'^".*"$'),
            'needs_quotes': re.compile(r'[^\w\s\-\.]|^\s|\s$'),
            'paradox_variable': re.compile(r'\$[A-Z_][A-Z0-9_]*\$'),
            'paradox_color': re.compile(r'§[a-zA-Z!]'),
            'paradox_icon': re.compile(r'£[a-zA-Z0-9_]+'),
            'valid_key': re.compile(r'^[a-zA-Z][a-zA-Z0-9_\.]*$'),  # Valid key pattern
            'translated_key': re.compile(r'[가-힣\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]'),  # Non-ASCII in keys
        }
        
        # Dynamic thresholds based on current level
        self.thresholds = {
            'untranslated_ratio': self.level_config.get('untranslated_ratio', 0.15),
            'line_count_tolerance': self.level_config.get('line_count_tolerance', 0.05),
            'yaml_error_ratio': self.level_config.get('yaml_error_ratio', 0.1),
        }
    
    def set_validation_level(self, level: str):
        """Change validation level dynamically"""
        if level in self.validation_levels:
            self.current_level = level
            self.level_config = self.validation_levels[level]
            # Update thresholds
            self.thresholds = {
                'untranslated_ratio': self.level_config.get('untranslated_ratio', 0.15),
                'line_count_tolerance': self.level_config.get('line_count_tolerance', 0.05),
                'yaml_error_ratio': self.level_config.get('yaml_error_ratio', 0.1),
            }
            self.logger.info(f"Validation level changed to: {level}")
    
    def should_validate(self, check_type: str) -> bool:
        """Check if specific validation should be performed based on current level"""
        if not self.level_config.get('enabled', True):
            return False
        
        return self.level_config.get(f'check_{check_type}', True)
    
    def track_session_error(self, error_info: Dict):
        """Track errors for automatic activation threshold"""
        self.current_session_errors.append(error_info)
        
        # Keep only recent errors (last 100 translations)
        if len(self.current_session_errors) > 100:
            self.current_session_errors = self.current_session_errors[-100:]
    
    def get_current_error_rate(self) -> float:
        """Calculate current session error rate"""
        if not self.current_session_errors:
            return 0.0
        
        error_count = sum(1 for error in self.current_session_errors if not error.get('is_valid', True))
        return error_count / len(self.current_session_errors)
    
    def should_auto_activate_strict_mode(self) -> bool:
        """Check if strict mode should be automatically activated based on error rate"""
        if self.current_level == 'off':
            return False
        
        current_error_rate = self.get_current_error_rate()
        return current_error_rate > self.auto_activation_threshold
    
    def validate_key_translation(self, original_text: str, translated_text: str) -> Dict:
        """
        Validate that YAML keys are not translated (keys should remain in English)
        
        Args:
            original_text: Original YAML text
            translated_text: Translated YAML text
            
        Returns:
            Dict with validation results and corrected text
        """
        result = {
            'is_valid': True,
            'errors': [],
            'corrections_made': 0,
            'corrected_text': translated_text,
            'translated_keys': []
        }
        
        if not self.should_validate('key_translation'):
            return result
        
        corrected_lines = []
        original_lines = original_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        # Create a mapping of original keys
        original_keys = {}
        for i, line in enumerate(original_lines):
            match = self.yaml_patterns['key_value_pair'].match(line)
            if match:
                indent, key, number, value = match.groups()
                original_keys[i] = key
        
        for i, line in enumerate(translated_lines):
            corrected_line = line
            
            match = self.yaml_patterns['key_value_pair'].match(line)
            if match:
                indent, key, number, value = match.groups()
                
                # Check if key contains non-ASCII characters (likely translated)
                if self.yaml_patterns['translated_key'].search(key):
                    # Try to restore original key
                    if i in original_keys:
                        original_key = original_keys[i]
                        
                        # Reconstruct line with original key
                        if number:
                            corrected_line = f"{indent}{original_key}:{number} {value}"
                        else:
                            corrected_line = f"{indent}{original_key}: {value}"
                        
                        result['corrections_made'] += 1
                        result['translated_keys'].append({
                            'line_number': i + 1,
                            'original_key': original_key,
                            'translated_key': key,
                            'corrected_line': corrected_line
                        })
            
            corrected_lines.append(corrected_line)
        
        result['corrected_text'] = '\n'.join(corrected_lines)
        
        if result['corrections_made'] > 0:
            result['is_valid'] = False
            result['errors'].append({
                'type': 'key_translated',
                'severity': 'high',
                'message': f'{result["corrections_made"]} keys were incorrectly translated',
                'translated_keys': result['translated_keys'][:5]  # Show first 5 examples
            })
        
        return result
    
    def validate_language_completion(self, original_text: str, translated_text: str, 
                                   source_lang: str, target_lang: str) -> Dict:
        """
        Validate that translation is complete (no source language remains)
        
        Args:
            original_text: Original text
            translated_text: Translated text  
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'untranslated_ratio': 0.0,
            'untranslated_chars': 0,
            'total_chars': len(translated_text),
            'errors': [],
            'corrected_text': translated_text
        }
        
        # Skip if validation is disabled
        if not self.should_validate('language_completion'):
            return result
        
        # Skip validation if texts are empty
        if not original_text.strip() or not translated_text.strip():
            return result
        
        # Get language pattern for source language
        source_pattern = self._get_language_pattern(source_lang)
        if not source_pattern:
            # If we don't have a pattern for this language, skip validation
            return result
        
        # Count characters from source language in translated text
        source_chars = source_pattern.findall(translated_text)
        untranslated_count = len(source_chars)
        
        if untranslated_count > 0:
            total_meaningful_chars = len(re.sub(r'\s+', '', translated_text))
            if total_meaningful_chars > 0:
                untranslated_ratio = untranslated_count / total_meaningful_chars
                
                result['untranslated_ratio'] = untranslated_ratio
                result['untranslated_chars'] = untranslated_count
                
                if untranslated_ratio > self.thresholds['untranslated_ratio']:
                    result['is_valid'] = False
                    result['errors'].append({
                        'type': 'incomplete_translation',
                        'severity': 'high',
                        'message': f'{untranslated_ratio:.1%} of text remains in source language',
                        'untranslated_chars': untranslated_count,
                        'untranslated_samples': source_chars[:5]  # Show first 5 examples
                    })
        
        return result
    
    def validate_yaml_quotes(self, original_text: str, translated_text: str) -> Dict:
        """
        Validate YAML structure, especially proper quoting of values
        
        Args:
            original_text: Original YAML text
            translated_text: Translated YAML text
            
        Returns:
            Dict with validation results and corrected text
        """
        result = {
            'is_valid': True,
            'errors': [],
            'corrections_made': 0,
            'corrected_text': translated_text,
            'missing_quotes': []
        }
        
        # Skip if validation is disabled
        if not self.should_validate('yaml_quotes'):
            return result
        
        corrected_lines = []
        original_lines = original_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        for i, line in enumerate(translated_lines):
            corrected_line = line
            
            # Check if this is a key-value pair
            match = self.yaml_patterns['key_value_pair'].match(line)
            if match:
                indent, key, number, value = match.groups()
                
                # Clean up the value part
                value = value.strip()
                
                # Skip if value is empty or already quoted
                if not value or self.yaml_patterns['quoted_value'].match(value):
                    corrected_lines.append(corrected_line)
                    continue
                
                # Check if this value needs quotes
                needs_quotes = (
                    self.yaml_patterns['needs_quotes'].search(value) or  # Special chars/spaces
                    len(value.split()) > 1 or  # Multiple words
                    value.startswith('#') or  # Comments
                    value in ['true', 'false', 'null', 'yes', 'no'] or  # YAML keywords
                    self._is_numeric_string(value)  # Numbers that should be strings
                )
                
                if needs_quotes:
                    # Preserve Paradox game variables and tags
                    quoted_value = f'"{value}"'
                    
                    # Reconstruct the line
                    if number:
                        corrected_line = f"{indent}{key}:{number} {quoted_value}"
                    else:
                        corrected_line = f"{indent}{key}: {quoted_value}"
                    
                    result['corrections_made'] += 1
                    result['missing_quotes'].append({
                        'line_number': i + 1,
                        'original': line,
                        'corrected': corrected_line,
                        'value': value
                    })
            
            corrected_lines.append(corrected_line)
        
        # Update result
        result['corrected_text'] = '\n'.join(corrected_lines)
        
        if result['corrections_made'] > 0:
            result['errors'].append({
                'type': 'yaml_quote_missing',
                'severity': 'high',
                'message': f'{result["corrections_made"]} lines missing proper quotes',
                'corrections': result['missing_quotes'][:10]  # Show first 10 examples
            })
        
        return result
    
    def validate_line_count(self, original_text: str, translated_text: str) -> Dict:
        """
        Validate that line count is preserved between original and translated text
        
        Args:
            original_text: Original text
            translated_text: Translated text
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'errors': [],
            'original_line_count': 0,
            'translated_line_count': 0,
            'line_count_diff': 0,
            'missing_lines': [],
            'extra_lines': []
        }
        
        # Skip if validation is disabled
        if not self.should_validate('line_count'):
            return result
        
        original_lines = original_text.split('\n')
        translated_lines = translated_text.split('\n')
        
        # Filter out completely empty lines for counting
        original_meaningful = [line for line in original_lines if line.strip()]
        translated_meaningful = [line for line in translated_lines if line.strip()]
        
        result['original_line_count'] = len(original_meaningful)
        result['translated_line_count'] = len(translated_meaningful)
        result['line_count_diff'] = len(translated_meaningful) - len(original_meaningful)
        
        # Calculate tolerance
        tolerance = max(1, int(len(original_meaningful) * self.thresholds['line_count_tolerance']))
        
        if abs(result['line_count_diff']) > tolerance:
            result['is_valid'] = False
            
            severity = 'high' if abs(result['line_count_diff']) > len(original_meaningful) * 0.1 else 'medium'
            
            result['errors'].append({
                'type': 'line_count_mismatch',
                'severity': severity,
                'message': f'Line count changed by {result["line_count_diff"]} lines',
                'original_count': len(original_meaningful),
                'translated_count': len(translated_meaningful),
                'tolerance': tolerance
            })
            
            # Identify specific missing/extra lines if possible
            if len(translated_meaningful) < len(original_meaningful):
                # Lines are missing
                result['missing_lines'] = self._identify_missing_lines(original_lines, translated_lines)
            elif len(translated_meaningful) > len(original_meaningful):
                # Extra lines added
                result['extra_lines'] = self._identify_extra_lines(original_lines, translated_lines)
        
        return result
    
    def calculate_batch_quality_score(self, batch_results: List[Dict]) -> Dict:
        """
        Calculate overall quality score for a batch of translations
        
        Args:
            batch_results: List of validation results for each item in batch
            
        Returns:
            Dict with batch quality metrics
        """
        if not batch_results:
            return {'quality_score': 0.0, 'should_retry': True, 'error_summary': {}}
        
        total_items = len(batch_results)
        error_counts = Counter()
        severity_counts = Counter()
        
        valid_items = 0
        total_untranslated_ratio = 0.0
        total_corrections = 0
        
        for result in batch_results:
            if result.get('is_valid', False):
                valid_items += 1
            
            # Count untranslated ratio
            total_untranslated_ratio += result.get('untranslated_ratio', 0.0)
            
            # Count corrections made
            total_corrections += result.get('corrections_made', 0)
            
            # Count error types and severities
            for error in result.get('errors', []):
                error_counts[error.get('type', 'unknown')] += 1
                severity_counts[error.get('severity', 'medium')] += 1
        
        # Calculate quality score (0-100)
        quality_score = (valid_items / total_items) * 100
        avg_untranslated_ratio = total_untranslated_ratio / total_items
        
        # Adjust quality score based on untranslated ratio
        if avg_untranslated_ratio > 0:
            quality_score *= (1 - min(avg_untranslated_ratio * 2, 0.8))
        
        # Determine if batch should be retried
        should_retry = (
            quality_score < 70 or  # Less than 70% quality
            avg_untranslated_ratio > self.thresholds['untranslated_ratio'] or
            severity_counts['high'] > total_items * 0.2  # More than 20% high severity errors
        )
        
        return {
            'quality_score': round(quality_score, 1),
            'should_retry': should_retry,
            'valid_items': valid_items,
            'total_items': total_items,
            'avg_untranslated_ratio': round(avg_untranslated_ratio, 3),
            'total_corrections': total_corrections,
            'error_summary': dict(error_counts),
            'severity_summary': dict(severity_counts),
            'retry_reason': self._get_retry_reason(quality_score, avg_untranslated_ratio, severity_counts)
        }
    
    def validate_translation_comprehensive(self, original_text: str, translated_text: str,
                                         source_lang: str = "", target_lang: str = "") -> Dict:
        """
        Comprehensive validation combining all checks based on current level
        
        Args:
            original_text: Original text
            translated_text: Translated text
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dict with comprehensive validation results
        """
        comprehensive_result = {
            'is_valid': True,
            'total_errors': 0,
            'total_corrections': 0,
            'errors': [],
            'corrected_text': translated_text,
            'validation_level': self.current_level,
            'checks_performed': []
        }
        
        current_text = translated_text
        
        # 1. Key translation validation (highest priority)
        if self.should_validate('key_translation'):
            key_result = self.validate_key_translation(original_text, current_text)
            if not key_result['is_valid']:
                comprehensive_result['is_valid'] = False
                comprehensive_result['total_errors'] += len(key_result['errors'])
            comprehensive_result['total_corrections'] += key_result['corrections_made']
            comprehensive_result['errors'].extend(key_result['errors'])
            current_text = key_result['corrected_text']
            comprehensive_result['checks_performed'].append('key_translation')
        
        # 2. YAML quotes validation
        if self.should_validate('yaml_quotes'):
            yaml_result = self.validate_yaml_quotes(original_text, current_text)
            if not yaml_result['is_valid']:
                comprehensive_result['is_valid'] = False
                comprehensive_result['total_errors'] += len(yaml_result['errors'])
            comprehensive_result['total_corrections'] += yaml_result['corrections_made']
            comprehensive_result['errors'].extend(yaml_result['errors'])
            current_text = yaml_result['corrected_text']
            comprehensive_result['checks_performed'].append('yaml_quotes')
        
        # 3. Language completion validation
        if self.should_validate('language_completion') and source_lang and target_lang:
            lang_result = self.validate_language_completion(original_text, current_text, source_lang, target_lang)
            if not lang_result['is_valid']:
                comprehensive_result['is_valid'] = False
                comprehensive_result['total_errors'] += len(lang_result['errors'])
            comprehensive_result['errors'].extend(lang_result['errors'])
            comprehensive_result['checks_performed'].append('language_completion')
        
        # 4. Line count validation (least critical)
        if self.should_validate('line_count'):
            line_result = self.validate_line_count(original_text, current_text)
            if not line_result['is_valid']:
                # Line count errors are often warnings, don't always mark as invalid
                if any(error['severity'] == 'high' for error in line_result['errors']):
                    comprehensive_result['is_valid'] = False
                comprehensive_result['total_errors'] += len(line_result['errors'])
            comprehensive_result['errors'].extend(line_result['errors'])
            comprehensive_result['checks_performed'].append('line_count')
        
        comprehensive_result['corrected_text'] = current_text
        
        # Track this result for session statistics
        self.track_session_error({
            'is_valid': comprehensive_result['is_valid'],
            'error_count': comprehensive_result['total_errors'],
            'validation_level': self.current_level
        })
        
        return comprehensive_result
    
    def should_retry_batch(self, batch_results: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if a batch should be retried based on validation results
        
        Args:
            batch_results: List of validation results
            
        Returns:
            Tuple of (should_retry, reason)
        """
        # Don't retry if validation is off or retry logic is disabled
        if not self.level_config.get('use_retry_logic', True):
            return False, "Retry logic disabled for current validation level"
        
        quality_metrics = self.calculate_batch_quality_score(batch_results)
        return quality_metrics['should_retry'], quality_metrics['retry_reason']
    
    def _get_language_pattern(self, language_code: str) -> Optional[re.Pattern]:
        """Get regex pattern for detecting specific language characters"""
        language_map = {
            'ko': 'korean',
            'korean': 'korean',
            'zh': 'chinese', 
            'chinese': 'chinese',
            'ja': 'japanese',
            'japanese': 'japanese',
            'ru': 'cyrillic',
            'russian': 'cyrillic',
            'ar': 'arabic',
            'arabic': 'arabic',
            'th': 'thai',
            'thai': 'thai'
        }
        
        pattern_key = language_map.get(language_code.lower())
        return self.language_patterns.get(pattern_key) if pattern_key else None
    
    def _is_numeric_string(self, value: str) -> bool:
        """Check if string represents a number but should be treated as string"""
        try:
            # If it can be parsed as a number but contains leading zeros or decimal points
            # it should probably be quoted in YAML
            float(value)
            return value.startswith('0') and len(value) > 1 and value != '0'
        except ValueError:
            return False
    
    def _identify_missing_lines(self, original_lines: List[str], translated_lines: List[str]) -> List[Dict]:
        """Identify which lines might be missing from translation"""
        # Simple heuristic: find lines in original that don't have similar counterparts in translation
        missing = []
        
        # This is a simplified approach - could be enhanced with more sophisticated matching
        original_keys = set()
        translated_keys = set()
        
        for line in original_lines:
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match:
                original_keys.add(match.group(2))  # key part
        
        for line in translated_lines:
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match:
                translated_keys.add(match.group(2))  # key part
        
        missing_keys = original_keys - translated_keys
        for i, line in enumerate(original_lines):
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match and match.group(2) in missing_keys:
                missing.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'key': match.group(2)
                })
        
        return missing[:10]  # Return up to 10 examples
    
    def _identify_extra_lines(self, original_lines: List[str], translated_lines: List[str]) -> List[Dict]:
        """Identify which lines might be extra in translation"""
        # Similar approach to missing lines but in reverse
        extra = []
        
        original_keys = set()
        translated_keys = set()
        
        for line in original_lines:
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match:
                original_keys.add(match.group(2))
        
        for line in translated_lines:
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match:
                translated_keys.add(match.group(2))
        
        extra_keys = translated_keys - original_keys
        for i, line in enumerate(translated_lines):
            match = self.yaml_patterns['key_value_pair'].match(line.strip())
            if match and match.group(2) in extra_keys:
                extra.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'key': match.group(2)
                })
        
        return extra[:10]  # Return up to 10 examples
    
    def _get_retry_reason(self, quality_score: float, avg_untranslated_ratio: float, 
                         severity_counts: Dict) -> str:
        """Generate human-readable reason for retry recommendation"""
        reasons = []
        
        if quality_score < 70:
            reasons.append(f"Low quality score ({quality_score}%)")
        
        if avg_untranslated_ratio > self.thresholds['untranslated_ratio']:
            reasons.append(f"High untranslated content ({avg_untranslated_ratio:.1%})")
        
        if severity_counts.get('high', 0) > 0:
            reasons.append(f"{severity_counts['high']} high-severity errors")
        
        return "; ".join(reasons) if reasons else "Quality acceptable"


class BatchRetryManager:
    """Manages batch-level retry logic with progressive prompt enhancement"""
    
    def __init__(self, validator: AdvancedTranslationValidator, max_retries: int = 3, 
                 enable_fast_mode: bool = False):
        self.validator = validator
        self.max_retries = max_retries
        self.enable_fast_mode = enable_fast_mode  # Skip expensive validations in fast mode
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.batch_stats = {
            'total_batches': 0,
            'retried_batches': 0,
            'successful_retries': 0,
            'avg_retry_attempts': 0.0
        }
    
    def process_batch_with_retry(self, api_provider, texts: List[str], base_prompt: str,
                               glossary: str = "", source_lang: str = "", target_lang: str = "",
                               progress_callback=None) -> Dict:
        """
        Process a batch with automatic retry on quality issues
        
        Args:
            api_provider: API provider instance
            texts: List of texts to translate
            base_prompt: Base prompt template
            glossary: Glossary text
            source_lang: Source language code
            target_lang: Target language code
            progress_callback: Optional progress callback
            
        Returns:
            Dict with final results and retry statistics
        """
        retry_stats = {
            'attempts': 0,
            'final_quality_score': 0.0,
            'total_corrections': 0,
            'retry_reasons': [],
            'success': False
        }
        
        current_prompt = base_prompt
        final_translations = []
        
        for attempt in range(self.max_retries + 1):
            retry_stats['attempts'] = attempt + 1
            
            try:
                # Get translations from API
                if hasattr(api_provider, 'translate_batch'):
                    translations = api_provider.translate_batch(texts, current_prompt, glossary)
                else:
                    # Fallback for async providers
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    translations = loop.run_until_complete(
                        api_provider.translate_batch(texts, current_prompt, glossary)
                    )
                    loop.close()
                
                # Validate each translation using comprehensive validation
                batch_results = []
                corrected_translations = []
                
                self.batch_stats['total_batches'] += 1
                
                for i, (original, translated) in enumerate(zip(texts, translations)):
                    # Use comprehensive validation
                    if self.enable_fast_mode and self.validator.current_level == 'basic':
                        # Fast mode: minimal validation
                        result = {
                            'is_valid': True,
                            'total_errors': 0,
                            'total_corrections': 0,
                            'errors': [],
                            'corrected_text': translated,
                            'validation_level': self.validator.current_level
                        }
                        
                        # Only do critical checks in fast mode
                        if self.validator.should_validate('key_translation'):
                            key_result = self.validator.validate_key_translation(original, translated)
                            result['corrected_text'] = key_result['corrected_text']
                            result['total_corrections'] = key_result['corrections_made']
                            if not key_result['is_valid']:
                                result['is_valid'] = False
                                result['errors'] = key_result['errors']
                                result['total_errors'] = len(key_result['errors'])
                    else:
                        # Full comprehensive validation
                        result = self.validator.validate_translation_comprehensive(
                            original, translated, source_lang, target_lang
                        )
                    
                    batch_results.append(result)
                    corrected_translations.append(result['corrected_text'])
                    retry_stats['total_corrections'] += result['total_corrections']
                
                # Calculate batch quality
                quality_metrics = self.validator.calculate_batch_quality_score(batch_results)
                retry_stats['final_quality_score'] = quality_metrics['quality_score']
                
                # Check if retry is needed
                should_retry, retry_reason = self.validator.should_retry_batch(batch_results)
                
                if not should_retry or attempt >= self.max_retries:
                    # Accept results
                    final_translations = corrected_translations
                    retry_stats['success'] = not should_retry
                    if should_retry:
                        retry_stats['retry_reasons'].append(f"Final attempt: {retry_reason}")
                    break
                else:
                    # Prepare for retry
                    retry_stats['retry_reasons'].append(f"Attempt {attempt + 1}: {retry_reason}")
                    current_prompt = self.enhance_prompt_for_retry(
                        base_prompt, quality_metrics['error_summary'], attempt + 1
                    )
                    
                    self.logger.info(f"Batch retry {attempt + 1}/{self.max_retries}: {retry_reason}")
                    
                    if progress_callback:
                        progress_callback(
                            -1, f"Retrying batch (attempt {attempt + 2}/{self.max_retries + 1}): {retry_reason}"
                        )
            
            except Exception as e:
                self.logger.error(f"Batch processing error on attempt {attempt + 1}: {e}")
                if attempt >= self.max_retries:
                    # Return error placeholders
                    final_translations = [f"[Translation Error: {str(e)[:50]}]"] * len(texts)
                    retry_stats['retry_reasons'].append(f"Final error: {str(e)}")
                    break
        
        return {
            'translations': final_translations,
            'retry_stats': retry_stats,
            'quality_metrics': quality_metrics if 'quality_metrics' in locals() else None
        }
    
    def enhance_prompt_for_retry(self, base_prompt: str, error_summary: Dict, attempt: int) -> str:
        """
        Enhance prompt based on previous errors and attempt number
        
        Args:
            base_prompt: Original prompt
            error_summary: Dictionary of error types and counts
            attempt: Current attempt number (1-based)
            
        Returns:
            Enhanced prompt string
        """
        enhancements = []
        
        # Add specific instructions based on error types
        if error_summary.get('incomplete_translation', 0) > 0:
            enhancements.append(
                "CRITICAL: You MUST translate ALL text completely. "
                "Do NOT leave any words in the original language. "
                "If you see Korean/Chinese/Japanese characters in your output, it's WRONG."
            )
        
        if error_summary.get('yaml_quote_missing', 0) > 0:
            enhancements.append(
                "YAML FORMAT REQUIREMENT: All text values MUST be enclosed in double quotes. "
                'Example: key:0 "translated text" NOT key:0 translated text'
            )
        
        if error_summary.get('line_count_mismatch', 0) > 0:
            enhancements.append(
                "LINE PRESERVATION: You MUST maintain the exact same number of lines as the input. "
                "Do not merge lines or split lines. Each input line = one output line."
            )
        
        # Add attempt-specific enhancements
        if attempt == 2:
            enhancements.append(
                "This is a RETRY attempt. Please be extra careful and double-check your output."
            )
        elif attempt >= 3:
            enhancements.append(
                "FINAL ATTEMPT: This is your last chance. Please follow ALL instructions precisely."
            )
            # Add example for final attempt
            enhancements.append(
                "\nEXAMPLE of correct output:\n"
                'original_key:0 "Source text"\n'
                'translated_key:0 "Translated text"\n'
            )
        
        # Combine enhancements with base prompt
        if enhancements:
            enhanced_prompt = base_prompt + "\n\nIMPORTANT ADDITIONAL INSTRUCTIONS:\n" + "\n\n".join(enhancements)
            return enhanced_prompt
        
        return base_prompt


class YAMLFileValidator:
    """Validator for YAML files before translation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_file_size_mb = 100  # Maximum file size in MB
        self.max_lines = 50000  # Maximum number of lines
        
    def validate_file_before_processing(self, file_path: str) -> Tuple[bool, str, Dict]:
        """
        Validate YAML file before translation processing
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (is_valid, error_message, file_info)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"파일을 찾을 수 없습니다: {file_path}", {}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size_mb > self.max_file_size_mb:
                return False, f"파일이 너무 큽니다 ({file_size_mb:.1f}MB). 최대 {self.max_file_size_mb}MB까지 지원합니다.", {}
            
            # Check if file is readable
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    # Count lines and check basic structure
                    lines = []
                    line_count = 0
                    yaml_entries = 0
                    problematic_lines = []
                    
                    for line_num, line in enumerate(f, 1):
                        line_count += 1
                        if line_count > self.max_lines:
                            return False, f"파일 라인 수가 너무 많습니다 ({line_count}). 최대 {self.max_lines}라인까지 지원합니다.", {}
                        
                        lines.append(line.strip())
                        
                        # Check for YAML key-value pairs
                        if ':' in line and not line.strip().startswith('#'):
                            yaml_entries += 1
                            
                            # Check for common problems
                            stripped = line.strip()
                            if not stripped:
                                continue
                                
                            # Check for unquoted strings that might cause YAML parsing issues
                            if ':' in stripped and not stripped.startswith('#'):
                                parts = stripped.split(':', 1)
                                if len(parts) == 2:
                                    value_part = parts[1].strip()
                                    # Check for potentially problematic values
                                    if value_part and not value_part.startswith('"') and not value_part.startswith("'"):
                                        # Values with special characters should be quoted
                                        if any(char in value_part for char in ['#', '[', ']', '{', '}', '|', '>', '@', '`']):
                                            problematic_lines.append({
                                                'line': line_num,
                                                'content': stripped,
                                                'issue': '특수 문자가 포함된 값이 따옴표로 감싸지지 않았습니다'
                                            })
                        
                        # Early exit if too many lines
                        if line_count > 1000:  # For initial validation, only check first 1000 lines
                            break
                    
            except UnicodeDecodeError:
                return False, "파일 인코딩을 읽을 수 없습니다. UTF-8 인코딩을 사용해주세요.", {}
            except Exception as e:
                return False, f"파일 읽기 중 오류 발생: {str(e)}", {}
            
            # Try to parse as YAML (just a small sample for validation)
            yaml_validation_result = self._validate_yaml_structure(file_path)
            
            file_info = {
                'file_size_mb': file_size_mb,
                'line_count': line_count,
                'yaml_entries': yaml_entries,
                'problematic_lines': problematic_lines[:10],  # Only show first 10 problems
                'yaml_structure_valid': yaml_validation_result[0],
                'yaml_error': yaml_validation_result[1] if not yaml_validation_result[0] else None
            }
            
            # Determine if file is valid
            is_valid = True
            error_messages = []
            
            if yaml_entries == 0:
                is_valid = False
                error_messages.append("YAML 키-값 쌍이 발견되지 않았습니다")
            
            if not yaml_validation_result[0]:
                is_valid = False
                error_messages.append(f"YAML 구조 오류: {yaml_validation_result[1]}")
            
            if len(problematic_lines) > line_count * 0.5:  # More than 50% problematic lines
                is_valid = False
                error_messages.append("문제가 있는 라인이 너무 많습니다")
            
            final_message = "; ".join(error_messages) if error_messages else "파일이 유효합니다"
            
            return is_valid, final_message, file_info
            
        except Exception as e:
            self.logger.error(f"File validation error for {file_path}: {e}")
            return False, f"파일 검증 중 오류 발생: {str(e)}", {}
    
    def _validate_yaml_structure(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate YAML structure by attempting to parse a sample
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Read first 100 lines for structure validation
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = []
                for i, line in enumerate(f):
                    lines.append(line)
                    if i >= 100:  # Only validate first 100 lines for performance
                        break
                
                sample_content = ''.join(lines)
                
                # Try to parse as YAML
                yaml.safe_load(sample_content)
                return True, None
                
        except yaml.YAMLError as e:
            error_msg = str(e)
            # Make error message more user-friendly
            if "could not find expected" in error_msg.lower():
                return False, "YAML 구조에 문제가 있습니다. 따옴표나 들여쓰기를 확인해주세요."
            elif "found character" in error_msg.lower():
                return False, "특수 문자로 인한 YAML 파싱 오류입니다. 값을 따옴표로 감싸주세요."
            else:
                return False, f"YAML 구조 오류: {error_msg[:100]}..."
                
        except Exception as e:
            return False, f"파일 구조 검증 중 오류: {str(e)}"
    
    def get_file_processing_recommendations(self, file_info: Dict) -> List[str]:
        """
        Get recommendations for processing the file based on validation results
        
        Args:
            file_info: File information from validation
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if file_info.get('file_size_mb', 0) > 50:
            recommendations.append("큰 파일입니다. 번역에 시간이 오래 걸릴 수 있습니다.")
        
        if file_info.get('line_count', 0) > 10000:
            recommendations.append("라인 수가 많습니다. 파일 분할을 권장합니다.")
        
        if file_info.get('problematic_lines'):
            recommendations.append(f"{len(file_info['problematic_lines'])}개의 잠재적 문제 라인이 발견되었습니다.")
            recommendations.append("번역 전에 YAML 구조를 확인해보세요.")
        
        if not file_info.get('yaml_structure_valid', True):
            recommendations.append("YAML 구조에 문제가 있습니다. 번역 전에 수정을 권장합니다.")
        
        if file_info.get('yaml_entries', 0) < 10:
            recommendations.append("번역할 내용이 적은 것 같습니다. 파일 내용을 확인해보세요.")
        
        return recommendations