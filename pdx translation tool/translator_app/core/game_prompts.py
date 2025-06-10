# translator_project/translator_app/core/game_prompts.py

GAME_PROMPTS = {
    "Crusader Kings 3": """You are translating text from the medieval grand strategy game 'Crusader Kings 3'.
Use a majestic, epic tone appropriate for medieval nobility and court intrigue.
CRITICAL: Elements enclosed in square brackets like [Concept|E], [Character.GetFirstName] are game code - DO NOT translate or modify them.
Example: "Your son, [Heir.GetFirstName], is a genius." -> "당신의 아들, [Heir.GetFirstName]은(는) 천재입니다."
Maintain the medieval atmosphere while ensuring natural translation.""",
    
    "Hearts of Iron 4": """You are translating text from the WWII grand strategy game 'Hearts of Iron 4'.
Use a concise, military report style with professional terminology.
CRITICAL: Symbols starting with £ (like £GFX_army_experience, £pol_power) are icon codes - NEVER translate them.
Example: "You gained 50 £pol_power." -> "정치력 50 £pol_power 만큼 획득했습니다."
Keep military terms precise and formal.""",
    
    "Stellaris": """You are translating text from the sci-fi grand strategy game 'Stellaris'.
Use futuristic, scientific terminology and a tone suitable for space exploration and diplomacy.
CRITICAL: Preserve all bracketed codes like [species.GetName] and variables like $PLANET_NAME$ exactly as they appear.
Maintain consistency with established sci-fi terminology.""",
    
    "Europa Universalis IV": """You are translating text from the historical grand strategy game 'Europa Universalis IV' (1444-1821 period).
Use formal diplomatic language appropriate for Early Modern period (Renaissance to Enlightenment).
Employ period-appropriate titles, ranks, and governmental terms.
CRITICAL: Preserve all game codes in brackets [] and variables with $ symbols.""",
    
    "Victoria 3": """You are translating text from the industrial era grand strategy game 'Victoria 3' (19th century).
Use terminology appropriate for the Industrial Revolution era, including political movements, economic systems, and social reforms.
Maintain a balance between historical authenticity and clarity.
CRITICAL: Keep all bracketed codes and special symbols unchanged.""",
    
    "Imperator: Rome": """You are translating text from the ancient grand strategy game 'Imperator: Rome'.
Use classical, dignified language appropriate for the Roman Republic and early Empire period.
Employ Latin-derived terms where appropriate for titles and concepts.
CRITICAL: Do not translate any game codes within brackets or special markers."""
}

def get_enhanced_prompt(game_name, original_prompt):
    """게임별 컨텍스트를 원본 프롬프트에 추가"""
    if game_name in GAME_PROMPTS and game_name != "None":
        # 게임별 컨텍스트를 원본 프롬프트 앞에 추가
        game_context = f"""GAME CONTEXT:
{GAME_PROMPTS[game_name]}

REMEMBER: Always preserve game codes, variables, and special symbols exactly as they appear in the original text.

---ORIGINAL INSTRUCTIONS---
"""
        return game_context + original_prompt
    return original_prompt