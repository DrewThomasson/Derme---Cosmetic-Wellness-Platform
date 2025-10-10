"""
Google Gemini API helper for allergen identification and ingredient analysis
"""
import google.generativeai as genai
from PIL import Image
import io
import json
import re
from typing import Dict, List, Optional, Tuple


class GeminiHelper:
    """Helper class for Google Gemini API interactions"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """Initialize Gemini helper with API key"""
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"Error initializing Gemini: {e}")
                self.model = None
    
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return self.model is not None
    
    def extract_ingredients_from_image(self, image: Image.Image) -> Tuple[str, List[str]]:
        """
        Extract ingredient list from product label image using Gemini Vision
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (raw_text, parsed_ingredients_list)
        """
        if not self.is_available():
            return "", []
        
        try:
            prompt = """
            Analyze this cosmetic product label image and extract ALL ingredients listed.
            
            Instructions:
            1. Look for ingredient lists (usually starts with "INGREDIENTS:" or similar)
            2. Extract every single ingredient name
            3. Return the raw text first, then a clean list
            4. Preserve original ingredient names as they appear
            5. Separate ingredients by commas
            
            Format your response as:
            RAW TEXT:
            [paste the full text you see]
            
            INGREDIENTS LIST:
            [ingredient 1], [ingredient 2], [ingredient 3], ...
            """
            
            response = self.model.generate_content([prompt, image])
            text = response.text
            
            # Parse the response
            raw_text = ""
            ingredients_list = []
            
            if "RAW TEXT:" in text and "INGREDIENTS LIST:" in text:
                parts = text.split("INGREDIENTS LIST:")
                raw_part = parts[0].replace("RAW TEXT:", "").strip()
                ingredients_part = parts[1].strip()
                
                raw_text = raw_part
                
                # Parse ingredients
                ingredients_list = [
                    ing.strip() 
                    for ing in re.split(r'[,\n]', ingredients_part) 
                    if ing.strip() and len(ing.strip()) > 2
                ]
            else:
                # Fallback parsing
                raw_text = text
                ingredients_list = [
                    ing.strip() 
                    for ing in re.split(r'[,\n]', text) 
                    if ing.strip() and len(ing.strip()) > 2
                ]
            
            return raw_text, ingredients_list
            
        except Exception as e:
            print(f"Error extracting ingredients with Gemini: {e}")
            return "", []
    
    def get_allergen_information(self, ingredient_name: str) -> Dict:
        """
        Get detailed information about an allergen/ingredient using Gemini
        
        Args:
            ingredient_name: Name of the ingredient
            
        Returns:
            Dictionary with allergen information
        """
        if not self.is_available():
            return {}
        
        try:
            prompt = f"""
            Provide detailed information about the cosmetic ingredient: {ingredient_name}
            
            Please include:
            1. Common alternative names and synonyms (list up to 10)
            2. Chemical category (e.g., preservative, fragrance, surfactant, etc.)
            3. Allergen potential (low/medium/high)
            4. Brief description of why it might cause allergic reactions
            5. Common products where it's found
            
            Format your response as JSON:
            {{
                "ingredient": "official name",
                "alternative_names": ["name1", "name2", ...],
                "category": "category",
                "allergen_potential": "low/medium/high",
                "description": "brief description",
                "common_in": ["product type 1", "product type 2", ...]
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                info = json.loads(json_match.group())
                return info
            else:
                # Return basic info if JSON parsing fails
                return {
                    "ingredient": ingredient_name,
                    "alternative_names": [],
                    "category": "unknown",
                    "allergen_potential": "unknown",
                    "description": text[:500],
                    "common_in": []
                }
                
        except Exception as e:
            print(f"Error getting allergen info with Gemini: {e}")
            return {}
    
    def analyze_ingredient_list(self, ingredients: List[str], known_allergens: List[str]) -> Dict:
        """
        Analyze a list of ingredients against known allergens using Gemini
        
        Args:
            ingredients: List of ingredient names
            known_allergens: List of user's known allergens
            
        Returns:
            Dictionary with analysis results
        """
        if not self.is_available():
            return {}
        
        try:
            ingredients_str = ", ".join(ingredients)
            allergens_str = ", ".join(known_allergens)
            
            prompt = f"""
            Analyze these cosmetic ingredients for potential allergens:
            
            INGREDIENTS: {ingredients_str}
            
            USER'S KNOWN ALLERGENS: {allergens_str}
            
            Please:
            1. Identify which ingredients match the user's allergens (including synonyms/alternative names)
            2. Flag common allergens even if not in user's list
            3. Highlight ingredients with high sensitization potential
            4. Provide brief explanation for each concern
            
            Format as JSON:
            {{
                "user_allergens_found": [
                    {{
                        "ingredient": "name as appears in list",
                        "matches_allergen": "user allergen it matches",
                        "confidence": "high/medium/low",
                        "explanation": "brief explanation"
                    }}
                ],
                "common_allergens": [
                    {{
                        "ingredient": "name",
                        "category": "type",
                        "risk": "high/medium/low",
                        "description": "why it's concerning"
                    }}
                ],
                "safe_ingredients": ["list of safe ingredients"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            else:
                return {
                    "user_allergens_found": [],
                    "common_allergens": [],
                    "safe_ingredients": ingredients
                }
                
        except Exception as e:
            print(f"Error analyzing ingredients with Gemini: {e}")
            return {}
    
    def find_ingredient_synonyms(self, ingredient_name: str) -> List[str]:
        """
        Find alternative names and synonyms for an ingredient
        
        Args:
            ingredient_name: Name of the ingredient
            
        Returns:
            List of synonym names
        """
        if not self.is_available():
            return [ingredient_name]
        
        try:
            prompt = f"""
            List ALL alternative names, synonyms, and chemical names for the cosmetic ingredient: {ingredient_name}
            
            Include:
            - Chemical names (INCI names)
            - Common names
            - Trade names
            - Abbreviated forms
            - Regional variations
            
            Return only the list of names, one per line, without explanations.
            """
            
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Parse the response
            synonyms = [ingredient_name]  # Always include original
            lines = text.strip().split('\n')
            
            for line in lines:
                # Clean up the line
                line = line.strip()
                # Remove bullet points, numbers, etc.
                line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)
                if line and len(line) > 2 and line not in synonyms:
                    synonyms.append(line)
            
            return synonyms[:10]  # Limit to 10 synonyms
            
        except Exception as e:
            print(f"Error finding synonyms with Gemini: {e}")
            return [ingredient_name]
