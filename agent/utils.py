import re

def clean_json_string(text: str) -> str:
    """
    Cleans markdown code fences or extra characters from the LLM JSON response.
    """
    # Remove markdown code fences if present
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()
