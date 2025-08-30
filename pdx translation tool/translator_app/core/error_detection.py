"""
Error detection and correction system for translation quality assurance
Handles YAML syntax validation, duplicate detection, and Paradox game mod format validation
"""

import re
import yaml
import logging
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import difflib


class TranslationErrorDetector:
    """Comprehensive error detection for translations"""
    
    def __init__(self, enable_correction: bool = True):
        self.enable_correction = enable_correction
        self.logger = logging.getLogger(__name__)
        
        # Paradox game localization patterns
        self.paradox_patterns = {
            'variable': re.compile(r'\$[A-Z_][A-Z0-9_]*\$'),
            'color_tag': re.compile(r'§[a-zA-Z!]'),
            'icon_tag': re.compile(r'£[a-zA-Z0-9_]+'),
            'conditional': re.compile(r'\[([^\]]+)\]'),
            'localization_key': re.compile(r'^[a-z0-9_\.]+:'),
            'yaml_string': re.compile(r'^[a-z0-9_\.]+:\s*".*"$'),
            'formatting_tags': re.compile(r'<[^>]+>')
        }
        
        # Common translation issues patterns
        self.error_patterns = {
            'incomplete_translation': re.compile(r'\[번역\s*(실패|오류|불가)\]'),
            'mixed_languages': re.compile(r'[가-힣].*[a-zA-Z]|[a-zA-Z].*[가-힣]'),
            'untranslated_placeholder': re.compile(r'(TRANSLATE|TODO|FIXME|번역필요)'),
            'broken_yaml_syntax': re.compile(r'[^\s]:\s*[^"\']*[가-힣][^"\']*$'),
            'duplicate_keys': re.compile(r'^(\s*)([a-z0-9_\.]+):\s*(.*)$')
        }
    
    def detect_errors(self, original_text: str, translated_text: str, context: Dict = None) -> Dict:
        """
        Comprehensive error detection
        Returns: {
            'has_errors': bool,
            'error_types': List[str],
            'severity': str,  # 'critical', 'warning', 'minor'
            'suggestions': List[str],
            'corrected_text': str
        }
        """
        results = {
            'has_errors': False,
            'error_types': [],
            'severity': 'minor',
            'suggestions': [],
            'corrected_text': translated_text
        }
        
        # 1. YAML syntax validation
        yaml_errors = self._check_yaml_syntax(translated_text)
        if yaml_errors:
            results['has_errors'] = True
            results['error_types'].extend(yaml_errors)
            results['severity'] = 'critical'
        
        # 2. Paradox game format validation
        format_errors = self._check_paradox_format(original_text, translated_text)
        if format_errors:
            results['has_errors'] = True
            results['error_types'].extend(format_errors)
            if results['severity'] != 'critical':
                results['severity'] = 'warning'
        
        # 3. Translation quality checks
        quality_errors = self._check_translation_quality(original_text, translated_text)
        if quality_errors:
            results['has_errors'] = True
            results['error_types'].extend(quality_errors)
            if results['severity'] == 'minor':
                results['severity'] = 'warning'
        
        # 4. Apply corrections if enabled
        if self.enable_correction and results['has_errors']:
            corrected = self._apply_corrections(original_text, translated_text, results['error_types'])
            results['corrected_text'] = corrected
            results['suggestions'] = self._generate_suggestions(results['error_types'])
        
        return results
    
    def _check_yaml_syntax(self, text: str) -> List[str]:
        """Check for YAML syntax errors"""
        errors = []
        
        try:
            # Test if it's valid YAML
            yaml.safe_load(text)
        except yaml.YAMLError as e:
            errors.append(f"yaml_syntax_error")
            self.logger.warning(f"YAML syntax error: {e}")
        
        # Check for common YAML formatting issues
        lines = text.split('\n')
        for i, line in enumerate(lines, 1):
            # Check for unquoted strings with special characters
            if ':' in line and not line.strip().startswith('#'):
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    value = key_value[1].strip()
                    if value and not (value.startswith('"') or value.startswith("'") or value.isdigit()):
                        # Check if value contains problematic characters
                        if re.search(r'[{}[\]|>*&!%@`]', value):
                            errors.append(f"unquoted_special_chars_line_{i}")
        
        return errors
    
    def _check_paradox_format(self, original: str, translated: str) -> List[str]:
        """Check Paradox game specific formatting"""
        errors = []
        
        # Extract special elements from original
        original_variables = self.paradox_patterns['variable'].findall(original)
        original_colors = self.paradox_patterns['color_tag'].findall(original)
        original_icons = self.paradox_patterns['icon_tag'].findall(original)
        original_conditionals = self.paradox_patterns['conditional'].findall(original)
        
        # Extract from translated
        translated_variables = self.paradox_patterns['variable'].findall(translated)
        translated_colors = self.paradox_patterns['color_tag'].findall(translated)
        translated_icons = self.paradox_patterns['icon_tag'].findall(translated)
        translated_conditionals = self.paradox_patterns['conditional'].findall(translated)
        
        # Check if special elements are preserved
        if set(original_variables) != set(translated_variables):
            errors.append("missing_or_altered_variables")
        
        if set(original_colors) != set(translated_colors):
            errors.append("missing_or_altered_color_tags")
        
        if set(original_icons) != set(translated_icons):
            errors.append("missing_or_altered_icon_tags")
        
        if len(original_conditionals) != len(translated_conditionals):
            errors.append("missing_or_altered_conditionals")
        
        # Check localization key format
        if self.paradox_patterns['localization_key'].match(original):
            if not self.paradox_patterns['localization_key'].match(translated):
                errors.append("malformed_localization_key")
        
        return errors
    
    def _check_translation_quality(self, original: str, translated: str) -> List[str]:
        """Check translation quality issues"""
        errors = []
        
        # Check for incomplete translations
        if self.error_patterns['incomplete_translation'].search(translated):
            errors.append("incomplete_translation")
        
        # Check for untranslated placeholders
        if self.error_patterns['untranslated_placeholder'].search(translated):
            errors.append("untranslated_placeholder")
        
        # Check for mixed language content (Korean + English)
        if self.error_patterns['mixed_languages'].search(translated):
            errors.append("mixed_languages")
        
        # Check for empty or whitespace-only translations
        if not translated.strip():
            errors.append("empty_translation")
        
        # Check for suspicious character patterns
        if len(translated) < len(original) * 0.3:  # Too short
            errors.append("suspiciously_short_translation")
        
        if len(translated) > len(original) * 3:  # Too long
            errors.append("suspiciously_long_translation")
        
        return errors
    
    def _apply_corrections(self, original: str, translated: str, error_types: List[str]) -> str:
        """Apply automatic corrections where possible"""
        corrected = translated
        
        for error_type in error_types:
            if error_type == "missing_or_altered_variables":
                corrected = self._restore_variables(original, corrected)
            elif error_type == "missing_or_altered_color_tags":
                corrected = self._restore_color_tags(original, corrected)
            elif error_type == "missing_or_altered_icon_tags":
                corrected = self._restore_icon_tags(original, corrected)
            elif error_type == "unquoted_special_chars":
                corrected = self._fix_yaml_quoting(corrected)
            elif error_type == "incomplete_translation":
                corrected = self._fix_incomplete_translation(original, corrected)
            elif error_type == "empty_translation":
                corrected = original  # Fallback to original
        
        return corrected
    
    def _restore_variables(self, original: str, translated: str) -> str:
        """Restore missing variables from original"""
        original_vars = self.paradox_patterns['variable'].findall(original)
        translated_vars = self.paradox_patterns['variable'].findall(translated)
        
        missing_vars = set(original_vars) - set(translated_vars)
        
        # Simple heuristic: append missing variables at the end
        if missing_vars:
            for var in missing_vars:
                if var not in translated:
                    translated += f" {var}"
        
        return translated
    
    def _restore_color_tags(self, original: str, translated: str) -> str:
        """Restore missing color tags"""
        original_colors = self.paradox_patterns['color_tag'].findall(original)
        
        for color in original_colors:
            if color not in translated:
                # Try to place at the beginning of the text content
                if '"' in translated:
                    translated = translated.replace('"', f'"{color}', 1)
        
        return translated
    
    def _restore_icon_tags(self, original: str, translated: str) -> str:
        """Restore missing icon tags"""
        original_icons = self.paradox_patterns['icon_tag'].findall(original)
        
        for icon in original_icons:
            if icon not in translated:
                translated += f" {icon}"
        
        return translated
    
    def _fix_yaml_quoting(self, text: str) -> str:
        """Fix YAML quoting issues"""
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            if ':' in line and not line.strip().startswith('#'):
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    key = key_value[0]
                    value = key_value[1].strip()
                    
                    if value and not (value.startswith('"') or value.startswith("'") or value.isdigit()):
                        # Check if value needs quoting
                        if re.search(r'[{}[\]|>*&!%@`:]', value):
                            value = f'"{value}"'
                    
                    fixed_lines.append(f"{key}: {value}")
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_incomplete_translation(self, original: str, translated: str) -> str:
        """Fix incomplete translation markers"""
        # Remove incomplete translation markers and use original if needed
        cleaned = re.sub(self.error_patterns['incomplete_translation'], '', translated).strip()
        
        if not cleaned:
            return original
        
        return cleaned
    
    def _generate_suggestions(self, error_types: List[str]) -> List[str]:
        """Generate human-readable suggestions for fixing errors"""
        suggestions = []
        
        suggestion_map = {
            "yaml_syntax_error": "YAML 구문을 확인하고 올바른 형식으로 수정하세요.",
            "missing_or_altered_variables": "원본의 변수 ($VAR$)가 누락되거나 변경되었습니다.",
            "missing_or_altered_color_tags": "색상 태그 (§)가 누락되거나 변경되었습니다.",
            "missing_or_altered_icon_tags": "아이콘 태그 (£)가 누락되거나 변경되었습니다.",
            "incomplete_translation": "번역이 완료되지 않았습니다.",
            "mixed_languages": "번역문에 원본 언어가 섞여있습니다.",
            "untranslated_placeholder": "번역되지 않은 플레이스홀더가 있습니다.",
            "empty_translation": "번역문이 비어있습니다.",
            "suspiciously_short_translation": "번역문이 지나치게 짧습니다.",
            "suspiciously_long_translation": "번역문이 지나치게 깁니다."
        }
        
        for error_type in error_types:
            if error_type in suggestion_map:
                suggestions.append(suggestion_map[error_type])
            else:
                suggestions.append(f"알 수 없는 오류: {error_type}")
        
        return suggestions


class DuplicateDetector:
    """Detect and handle duplicate translations"""
    
    def __init__(self):
        self.translations_cache = {}
    
    def detect_duplicates(self, translations: List[Tuple[str, str]]) -> Dict:
        """
        Detect duplicate translations
        Args: List of (key, translation) tuples
        Returns: {'duplicates': {...}, 'stats': {...}}
        """
        key_counts = Counter(item[0] for item in translations)
        value_counts = Counter(item[1] for item in translations)
        
        duplicate_keys = {k: v for k, v in key_counts.items() if v > 1}
        duplicate_values = {k: v for k, v in value_counts.items() if v > 1}
        
        return {
            'duplicate_keys': duplicate_keys,
            'duplicate_values': duplicate_values,
            'total_duplicates': len(duplicate_keys) + len(duplicate_values),
            'stats': {
                'total_items': len(translations),
                'unique_keys': len(set(item[0] for item in translations)),
                'unique_values': len(set(item[1] for item in translations))
            }
        }
    
    def remove_duplicates(self, translations: List[Tuple[str, str]], 
                         strategy: str = 'keep_first') -> List[Tuple[str, str]]:
        """
        Remove duplicates using specified strategy
        Strategies: 'keep_first', 'keep_last', 'keep_longest', 'keep_shortest'
        """
        if strategy == 'keep_first':
            seen = set()
            result = []
            for key, value in translations:
                if key not in seen:
                    seen.add(key)
                    result.append((key, value))
            return result
        
        elif strategy == 'keep_last':
            seen = {}
            for key, value in translations:
                seen[key] = value
            return list(seen.items())
        
        elif strategy == 'keep_longest':
            seen = {}
            for key, value in translations:
                if key not in seen or len(value) > len(seen[key]):
                    seen[key] = value
            return list(seen.items())
        
        elif strategy == 'keep_shortest':
            seen = {}
            for key, value in translations:
                if key not in seen or len(value) < len(seen[key]):
                    seen[key] = value
            return list(seen.items())
        
        return translations