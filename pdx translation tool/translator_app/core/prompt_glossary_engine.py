"""
Prompt and Glossary Management Engine
프롬프트 템플릿 관리, 용어집 처리, 게임별 특화 프롬프트 기능
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class PromptManager:
    """프롬프트 템플릿 관리자"""
    
    def __init__(self):
        self.default_prompt_template = """Please translate the following YML formatted text from '{source_lang_for_prompt}' to '{target_lang_for_prompt}'.
{glossary_section}
You MUST adhere to the following rules strictly:
1. Only translate the text enclosed in double quotes after a colon (:). (e.g., `key: "text to translate"`)
2. Do NOT translate code-like strings, variable names (e.g., `$variable$`, `[variable]`, `<variable>`), special tags (e.g., `§Y`, `£gold£`), file paths, or URLs.
3. **CRITICAL**: You MUST preserve all original newline characters (\\n) and leading whitespace (indentation) for each line. Do NOT change or remove them. Each translated line must retain its original line break.
4. Provide ONLY the translated text. Do NOT include any other explanations, headers, or footers.
5. Translate all personal names and proper nouns according to the context.
6. If the content within quotes is a number, consists only of special characters, or is a simple path string, do NOT translate it.
7. Do NOT translate YML comments (lines starting with '#'). Keep them as they are.
8. For each input line, you MUST output exactly one translated line.
9. **ABSOLUTE REQUIREMENT**: When translating from {source_lang_for_prompt} to {target_lang_for_prompt}, you MUST completely translate ALL {source_lang_for_prompt} words and phrases. Do NOT leave any {source_lang_for_prompt} text untranslated. Every single {source_lang_for_prompt} word must be converted to {target_lang_for_prompt}.
10. **STRICT VALIDATION**: If any {source_lang_for_prompt} words remain in your translation, it is considered a FAILED translation. Retry until ALL {source_lang_for_prompt} is properly translated to {target_lang_for_prompt}.

Text to translate:
```yaml
{batch_text}
```"""
        
        # 게임별 특화 프롬프트
        self.game_prompts = {
            "Victoria 3": {
                "enhanced_rules": [
                    "11. **Victoria 3 Specific**: Preserve all variable references like `$COUNTRY$`, `[GetName]`, `[concept_pop]`, etc.",
                    "12. **Population & Economy**: Translate economic and population terms accurately (e.g., 'Pop' → '인구', 'GDP' → 'GDP')",
                    "13. **Political Terms**: Use consistent political terminology (e.g., 'Interest Group' → '이익집단', 'Law' → '법률')",
                    "14. **Technology**: Maintain technology names consistently (e.g., 'Steelworking' → '제강업')",
                    "15. **Diplomatic**: Use formal diplomatic language for international relations"
                ]
            },
            "Europa Universalis IV": {
                "enhanced_rules": [
                    "11. **EU4 Specific**: Preserve all event variables like `[Root.GetName]`, `[This.GetAdjective]`",
                    "12. **Historical Context**: Maintain historical accuracy in names and terms",
                    "13. **Religious Terms**: Use appropriate religious terminology for different faiths",
                    "14. **Trade & Economy**: Translate trade goods and economic terms consistently",
                    "15. **Military**: Use proper military ranks and unit names"
                ]
            },
            "Crusader Kings III": {
                "enhanced_rules": [
                    "11. **CK3 Specific**: Preserve character references like `[character.GetName]`, `[dynasty.GetName]`",
                    "12. **Medieval Context**: Use medieval/feudal terminology appropriately",
                    "13. **Religion & Culture**: Translate religious and cultural terms with historical context",
                    "14. **Titles**: Maintain consistency in noble titles and positions",
                    "15. **Dynasty Names**: Keep dynasty and character names culturally appropriate"
                ]
            },
            "Hearts of Iron IV": {
                "enhanced_rules": [
                    "11. **HOI4 Specific**: Preserve country tags like `[GER.GetName]`, `[SOV.GetAdjective]`",
                    "12. **Military Context**: Use appropriate WWII-era military terminology",
                    "13. **Political Ideologies**: Translate political terms with historical accuracy",
                    "14. **Equipment**: Maintain consistency in military equipment names",
                    "15. **Leaders**: Keep historical figure names accurate"
                ]
            },
            "Stellaris": {
                "enhanced_rules": [
                    "11. **Stellaris Specific**: Preserve empire variables like `[This.GetName]`, `[owner.GetSpeciesName]`",
                    "12. **Sci-Fi Terms**: Use consistent science fiction terminology",
                    "13. **Species & Empires**: Translate species names and empire types appropriately",
                    "14. **Technology**: Maintain sci-fi technology naming conventions",
                    "15. **Galactic Context**: Use appropriate space-age language"
                ]
            },
            "Imperator: Rome": {
                "enhanced_rules": [
                    "11. **Imperator Specific**: Preserve country variables like `[Root.GetName]`, `[This.GetAdjective]`",
                    "12. **Classical Context**: Use appropriate ancient world terminology",
                    "13. **Roman Terms**: Translate Roman political and military terms accurately",
                    "14. **Trade & Commerce**: Use classical economic terminology",
                    "15. **Religion & Culture**: Maintain historical accuracy in religious and cultural terms"
                ]
            }
        }
        
        # 사용자 정의 프롬프트 저장소
        self.custom_prompts = {}
        self.current_prompt = self.default_prompt_template
    
    def get_enhanced_prompt(self, game_name: str, base_prompt: Optional[str] = None) -> str:
        """게임별 강화 프롬프트 생성"""
        if not game_name or game_name not in self.game_prompts:
            return base_prompt or self.default_prompt_template
        
        prompt_to_enhance = base_prompt or self.default_prompt_template
        game_rules = self.game_prompts[game_name]["enhanced_rules"]
        
        # 기존 규칙 뒤에 게임별 규칙 추가
        enhanced_rules = "\n".join(game_rules)
        
        # 규칙 섹션 찾아서 추가
        if "Text to translate:" in prompt_to_enhance:
            parts = prompt_to_enhance.split("Text to translate:")
            enhanced_prompt = f"{parts[0]}{enhanced_rules}\n\nText to translate:{parts[1]}"
        else:
            # 기본 위치에 추가
            enhanced_prompt = f"{prompt_to_enhance}\n\n{enhanced_rules}"
        
        return enhanced_prompt
    
    def format_prompt(self, prompt_template: str, source_lang: str, target_lang: str, 
                     batch_text: str, glossary_section: str = "") -> str:
        """프롬프트 포맷팅"""
        formatted_prompt = prompt_template.format(
            source_lang_for_prompt=source_lang,
            target_lang_for_prompt=target_lang,
            batch_text=batch_text,
            glossary_section=glossary_section
        )
        return formatted_prompt
    
    def save_custom_prompt(self, name: str, prompt: str):
        """사용자 정의 프롬프트 저장"""
        self.custom_prompts[name] = prompt
    
    def load_custom_prompt(self, name: str) -> Optional[str]:
        """사용자 정의 프롬프트 로드"""
        return self.custom_prompts.get(name)
    
    def get_available_games(self) -> List[str]:
        """사용 가능한 게임 목록 반환"""
        return list(self.game_prompts.keys())


class GlossaryManager:
    """용어집 관리자"""
    
    def __init__(self, glossary_dir: str = "glossaries"):
        self.glossary_dir = Path(glossary_dir)
        self.glossary_dir.mkdir(exist_ok=True)
        
        # 메모리상 용어집
        self.glossaries = {}
        self.active_glossaries = []
        
        # 용어집 파일 로드
        self.load_all_glossaries()
    
    def load_all_glossaries(self):
        """모든 용어집 파일 로드"""
        if not self.glossary_dir.exists():
            return
        
        for file_path in self.glossary_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    glossary_data = json.load(f)
                    glossary_name = file_path.stem
                    self.glossaries[glossary_name] = glossary_data
            except Exception as e:
                print(f"Failed to load glossary {file_path}: {e}")
    
    def save_glossary(self, name: str, terms: Dict[str, str], description: str = ""):
        """용어집 저장"""
        glossary_data = {
            "name": name,
            "description": description,
            "terms": terms,
            "version": "1.0"
        }
        
        file_path = self.glossary_dir / f"{name}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(glossary_data, f, ensure_ascii=False, indent=2)
            
            self.glossaries[name] = glossary_data
            return True
        except Exception as e:
            print(f"Failed to save glossary {name}: {e}")
            return False
    
    def load_glossary(self, name: str) -> Optional[Dict[str, Any]]:
        """특정 용어집 로드"""
        return self.glossaries.get(name)
    
    def delete_glossary(self, name: str) -> bool:
        """용어집 삭제"""
        file_path = self.glossary_dir / f"{name}.json"
        try:
            if file_path.exists():
                file_path.unlink()
            if name in self.glossaries:
                del self.glossaries[name]
            if name in self.active_glossaries:
                self.active_glossaries.remove(name)
            return True
        except Exception as e:
            print(f"Failed to delete glossary {name}: {e}")
            return False
    
    def activate_glossary(self, name: str):
        """용어집 활성화"""
        if name in self.glossaries and name not in self.active_glossaries:
            self.active_glossaries.append(name)
    
    def deactivate_glossary(self, name: str):
        """용어집 비활성화"""
        if name in self.active_glossaries:
            self.active_glossaries.remove(name)
    
    def get_active_terms(self) -> Dict[str, str]:
        """활성화된 용어집의 모든 용어 반환"""
        all_terms = {}
        
        for glossary_name in self.active_glossaries:
            if glossary_name in self.glossaries:
                terms = self.glossaries[glossary_name].get("terms", {})
                all_terms.update(terms)
        
        return all_terms
    
    def format_glossary_section(self, source_lang: str, target_lang: str) -> str:
        """프롬프트용 용어집 섹션 포맷팅"""
        active_terms = self.get_active_terms()
        
        if not active_terms:
            return ""
        
        glossary_lines = [f"\n**Glossary ({source_lang} → {target_lang})**:"]
        for source_term, target_term in active_terms.items():
            glossary_lines.append(f"- {source_term} → {target_term}")
        
        glossary_lines.append("**Please use these exact translations for the above terms.**\n")
        
        return "\n".join(glossary_lines)
    
    def get_available_glossaries(self) -> List[str]:
        """사용 가능한 용어집 목록"""
        return list(self.glossaries.keys())
    
    def import_glossary_from_file(self, file_path: str, name: str) -> bool:
        """외부 파일에서 용어집 가져오기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    if 'terms' in data:
                        return self.save_glossary(name, data['terms'], data.get('description', ''))
                elif file_path.endswith('.txt') or file_path.endswith('.csv'):
                    # 텍스트 파일에서 용어 추출
                    terms = {}
                    for line in f:
                        line = line.strip()
                        if '→' in line or '->' in line or '=' in line:
                            # 다양한 구분자 지원
                            if '→' in line:
                                source, target = line.split('→', 1)
                            elif '->' in line:
                                source, target = line.split('->', 1)
                            else:
                                source, target = line.split('=', 1)
                            
                            terms[source.strip()] = target.strip()
                    
                    if terms:
                        return self.save_glossary(name, terms, f"Imported from {Path(file_path).name}")
            
            return False
        except Exception as e:
            print(f"Failed to import glossary from {file_path}: {e}")
            return False
    
    def export_glossary(self, name: str, file_path: str, format_type: str = 'json') -> bool:
        """용어집 내보내기"""
        if name not in self.glossaries:
            return False
        
        glossary = self.glossaries[name]
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type == 'json':
                    json.dump(glossary, f, ensure_ascii=False, indent=2)
                elif format_type == 'txt':
                    f.write(f"# {glossary.get('name', name)}\n")
                    f.write(f"# {glossary.get('description', '')}\n\n")
                    for source, target in glossary.get('terms', {}).items():
                        f.write(f"{source} → {target}\n")
                elif format_type == 'csv':
                    f.write("Source,Target\n")
                    for source, target in glossary.get('terms', {}).items():
                        f.write(f'"{source}","{target}"\n')
            
            return True
        except Exception as e:
            print(f"Failed to export glossary {name}: {e}")
            return False
    
    def merge_glossaries(self, name1: str, name2: str, new_name: str) -> bool:
        """두 용어집 병합"""
        if name1 not in self.glossaries or name2 not in self.glossaries:
            return False
        
        terms1 = self.glossaries[name1].get('terms', {})
        terms2 = self.glossaries[name2].get('terms', {})
        
        merged_terms = terms1.copy()
        merged_terms.update(terms2)
        
        description = f"Merged from {name1} and {name2}"
        
        return self.save_glossary(new_name, merged_terms, description)
    
    def search_terms(self, query: str) -> Dict[str, Dict[str, str]]:
        """용어 검색"""
        results = {}
        
        for glossary_name, glossary_data in self.glossaries.items():
            terms = glossary_data.get('terms', {})
            matching_terms = {}
            
            for source, target in terms.items():
                if (query.lower() in source.lower() or 
                    query.lower() in target.lower()):
                    matching_terms[source] = target
            
            if matching_terms:
                results[glossary_name] = matching_terms
        
        return results


class GamePromptManager:
    """게임별 특화 프롬프트 관리자"""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.glossary_manager = GlossaryManager()
    
    def get_game_specific_prompt(self, game_name: str, source_lang: str, 
                               target_lang: str, batch_text: str, 
                               custom_prompt: Optional[str] = None) -> str:
        """게임별 특화 프롬프트 생성"""
        
        # 베이스 프롬프트 선택
        base_prompt = custom_prompt or self.prompt_manager.default_prompt_template
        
        # 게임별 강화 프롬프트 적용
        enhanced_prompt = self.prompt_manager.get_enhanced_prompt(game_name, base_prompt)
        
        # 활성 용어집 섹션 생성
        glossary_section = self.glossary_manager.format_glossary_section(source_lang, target_lang)
        
        # 최종 프롬프트 포맷팅
        final_prompt = self.prompt_manager.format_prompt(
            enhanced_prompt, source_lang, target_lang, batch_text, glossary_section
        )
        
        return final_prompt
    
    def create_game_glossary(self, game_name: str) -> bool:
        """게임별 기본 용어집 생성"""
        game_terms = {
            "Victoria 3": {
                "Pop": "인구",
                "GDP": "GDP",
                "Interest Group": "이익집단",
                "Law": "법률",
                "Technology": "기술",
                "Trade Route": "무역로",
                "Diplomatic": "외교"
            },
            "Europa Universalis IV": {
                "Nation": "국가",
                "Province": "주",
                "Trade Node": "무역 노드",
                "Monarch": "군주",
                "Institution": "제도",
                "Casus Belli": "개전사유"
            },
            "Crusader Kings III": {
                "Dynasty": "왕조",
                "Realm": "영토",
                "Vassal": "봉신",
                "Court": "궁정",
                "Faith": "신앙",
                "Culture": "문화"
            }
        }
        
        if game_name in game_terms:
            return self.glossary_manager.save_glossary(
                f"{game_name}_default",
                game_terms[game_name],
                f"Default terms for {game_name}"
            )
        
        return False