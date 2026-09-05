"""
Random Joke Generator using External API
Generador de chistes aleatorios usando API externa
"""

import requests
import json
from typing import Optional, Dict, Any

class JokeGenerator:
    """
    A simple joke generator that fetches random jokes from an external API.
    Generador simple de chistes que obtiene bromas aleatorias de una API externa.
    """
    
    BASE_URL = "https://v2.jokeapi.dev/joke/"
    
    def __init__(self):
        """Initialize the joke generator."""
        self.session = requests.Session()
    
    def get_random_joke(self, 
                       joke_type: str = "Any",
                       contains_profanity: bool = False) -> Optional[Dict[str, Any]]:
        """
        Fetch a random joke from the API.
        
        Args:
            joke_type: Type of joke - "Any", "General", "Programming", "Knock-Knock"
            contains_profanity: Whether to allow jokes with profanity
        
        Returns:
            Dictionary with joke data or None if request fails
        """
        try:
            # Build query parameters
            params = {
                "format": "json",
                "safe-mode": "off" if contains_profanity else "on"
            }
            
            url = f"{self.BASE_URL}{joke_type}"
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            joke_data = response.json()
            
            if joke_data.get("error"):
                print(f"API Error: {joke_data.get('message')}")
                return None
            
            return joke_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching joke: {e}")
            return None
    
    def format_joke(self, joke_data: Dict[str, Any]) -> str:
        """
        Format the joke data into a readable string.
        
        Args:
            joke_data: Dictionary containing joke information
        
        Returns:
            Formatted joke string
        """
        if not joke_data:
            return "Could not fetch a joke. Please try again."
        
        joke_type = joke_data.get("type", "unknown")
        
        if joke_type == "single":
            return joke_data.get("joke", "No joke available")
        
        elif joke_type == "twopart":
            setup = joke_data.get("setup", "")
            delivery = joke_data.get("delivery", "")
            return f"{setup}\n\n{delivery}"
        
        else:
            return json.dumps(joke_data, indent=2)
    
    def get_programming_joke(self) -> str:
        """
        Get a programming-specific joke.
        
        Returns:
            Formatted programming joke
        """
        joke_data = self.get_random_joke(joke_type="Programming")
        return self.format_joke(joke_data)
    
    def get_general_joke(self) -> str:
        """
        Get a general joke.
        
        Returns:
            Formatted general joke
        """
        joke_data = self.get_random_joke(joke_type="General")
        return self.format_joke(joke_data)
    
    def get_knock_knock_joke(self) -> str:
        """
        Get a knock-knock joke.
        
        Returns:
            Formatted knock-knock joke
        """
        joke_data = self.get_random_joke(joke_type="Knock-Knock")
        return self.format_joke(joke_data)


# Example usage
if __name__ == "__main__":
    generator = JokeGenerator()
    
    print("=" * 60)
    print("RANDOM JOKE GENERATOR / GENERADOR DE CHISTES ALEATORIOS")
    print("=" * 60)
    
    print("\n--- Programming Joke ---")
    print(generator.get_programming_joke())
    
    print("\n--- General Joke ---")
    print(generator.get_general_joke())
    
    print("\n--- Knock-Knock Joke ---")
    print(generator.get_knock_knock_joke())
    
    print("\n--- Any Type Joke ---")
    print(generator.get_random_joke())
