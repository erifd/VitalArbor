import requests
import base64
import API_Key_storage
from typing import Optional

def get_plant_diagnosis_groq(image_path: str) -> str:
    """
    Analyzes a tree image for diseases and structural problems using GroqCloud API.
    Get free API key at: https://console.groq.com/
    
    Args:
        image_path: Path to the tree image file
        
    Returns:
        Diagnosis summary as a string
    """
    
    API_KEY = API_Key_storage.give_groq_key()
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading image file: {str(e)}")
    
    mime_type = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'
    
    # Improved prompt with clearer instructions
    prompt = """You are a tree health diagnostic system. Analyze this tree image and provide a concise diagnosis.

Focus on identifying:
- Visible diseases (fungal infections, bacterial spots, cankers)
- Structural damage (cracks, splits, dead branches)
- Signs of decay or rot
- Pest damage or infestations
- Any conditions that could cause the tree to become unstable or die

Provide your assessment in exactly 3-4 complete sentences written as a single paragraph. Be factual and specific about what you observe. Note: This tree has been processed through image segmentation, which may affect its appearance.
Your assessment should be personalized to this specific tree, based on the image provided. You may not make generalized statements.

Do not include recommendations, predictions beyond immediate observations, or speculative statements."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }],
                "temperature": 0.5,  # Lower temperature for more consistent, factual responses
                "max_tokens": 1024
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status {response.status_code}: {response.text}")
        
        return response.json()['choices'][0]['message']['content']
    
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out after 60 seconds")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error occurred: {str(e)}")


def get_plant_fixes_groq(diagnosis: str, image_path: str) -> str:
    """
    Provides treatment recommendations based on the diagnosis.
    
    Args:
        diagnosis: The diagnosis string from get_plant_diagnosis_groq
        image_path: Path to the tree image file
        
    Returns:
        Treatment recommendations as a string
    """
    
    API_KEY = API_Key_storage.give_groq_key()
    
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading image file: {str(e)}")
    
    mime_type = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'
    
    # Improved prompt with better structure
    prompt = f"""You are providing treatment recommendations for a tree based on this diagnosis:

"{diagnosis}"

Provide actionable recommendations organized as follows:

1. IMMEDIATE SAFETY CONCERNS: If any exist, state them clearly and recommend consulting a certified arborist immediately.

2. HOMEOWNER-SAFE ACTIONS: List practical steps that a homeowner can safely perform without specialized equipment or climbing:
   - Basic care (watering, mulching)
   - Simple pruning of small dead branches (ground level only)
   - Monitoring instructions
   
3. PROFESSIONAL CONSULTATION: Clearly state when professional help is needed for:
   - Large branch removal
   - Tree climbing work
   - Pesticide/fungicide application
   - Structural assessment

Keep recommendations specific, safety-focused, and practical. Do not suggest any actions that could put a homeowner at risk of injury.
Your recommendations should be personalized to this specific tree, based on the diagnosis and image provided. You may not make generalized statements."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }],
                "temperature": 0.6,
                "max_tokens": 1024
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status {response.status_code}: {response.text}")
        
        return response.json()['choices'][0]['message']['content']
    
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out after 60 seconds")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error occurred: {str(e)}")


if __name__ == "__main__":
    # Example usage - returns just the diagnosis
    image_path = "C:\\Users\\family_2\\Documents\\GitHub\\VitalArbor\\Segmented photos\\Cherry Tree_crop_out.png"
    
    try:
        diagnosis = get_plant_diagnosis_groq(image_path)
        print(diagnosis)
        fixes = get_plant_fixes_groq(diagnosis, image_path)
        print(fixes)
    except Exception as e:
        print(f"Error: {str(e)}")