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

Do not include recommendations, predictions beyond immediate observations, or speculative statements.
Your statements should be extremely specific, highlighting key issues in the tree, and other and any problems that are visible, bein extremely specific in all the details."""

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

2. HOMEOWNER-SAFE ACTIONS: List steps to take care of the specific tree issues that a honemeowner can safely perform. Be specific about treatments, and tell them what problems are arising that they need to care for themselves. NO GENERALIZATIONS.
   Elaborate on how to implement these actions, why they are necessary, point to specific parts on the tree, and list multiple actions.
3. PROFESSIONAL CONSULTATION: Clearly state when professional help is needed for something, and recommend what the homeowner should tell the arborist to help them with, and solve any problems that could lead to tree failure.

Do not suggest any actions that could put a homeowner at risk of injury.
Your recommendations should be personalized to this specific tree, based on the diagnosis and image provided. You may not make generalized statements.
Be specific in what you are talking about, and for the actions that the owner can take"""

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
    

def get_calendar_schedule_groq(diagnosis: str, fixes: str, image_path: str) -> str:
    """
    Provides a calendar schedule for treating the tree based on the diagnosis.
    
    Args:
        diagnosis: The diagnosis string from get_plant_diagnosis_groq
        fixes: The treatment recommendations string from get_plant_fixes_groq
        image_path: Path to the tree image file
        
    Returns:
        Calendar schedule in structured format parseable by Java server.
        Format: <TAG: description, days_between, number_of_times>
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
    
    # Enhanced prompt with strict formatting requirements
    prompt = f"""You are creating a structured calendar schedule for tree treatment based on this diagnosis and treatment plan:

DIAGNOSIS:
{diagnosis}

TREATMENT RECOMMENDATIONS:
{fixes}

Create a treatment calendar with EXACTLY 4 sections. Each section must follow this EXACT format with NO deviations:
<SECTION_NAME: description text, number, number>

CRITICAL FORMATTING RULES:
- Use angle brackets < > around each entire entry
- Section name must be in ALL CAPS followed by a colon
- After the colon: description, then comma-space, then days (number only), then comma-space, then times (number only)
- NO words like "days" or "times" - ONLY numbers
- Each entry on its own line
- NO extra punctuation or formatting

SECTION 1 - NUTRIENT_MANAGEMENT:
- If tree needs nutrients or watering: Provide specific fertilizer type, watering schedule, and application method
- If no nutrient issues: Write "No nutrient deficiencies detected, maintain regular watering"
- Format: <NUTRIENT_MANAGEMENT: [1 sentence description], [days between applications], [total number of applications]>
- Example: <NUTRIENT_MANAGEMENT: Apply balanced 10-10-10 fertilizer and water deeply twice weekly, 7, 12>

SECTION 2 - STRUCTURE_MANAGEMENT:
- If tree has structural issues, lean, or damaged branches: Provide staking/support plan and pruning schedule
- Specify which branches to prune (dead, crossing, diseased only - NOT aesthetic)
- If no structural issues: Write "No structural issues detected, no intervention needed"
- Format: <STRUCTURE_MANAGEMENT: [1-2 sentence description], [days between actions], [times to repeat OR 0 for one-time tasks]>
- Example: <STRUCTURE_MANAGEMENT: Stake tree with two support posts and prune three dead lower branches within first week, 0, 1>

SECTION 3 - DISEASE_MANAGEMENT:
- If disease, pests, or fungi present: Specify treatment type, application method, and monitoring signs
- Include preventive treatments if tree shows early warning signs
- If no disease: Write "No disease detected, monitor for signs of stress or pest activity"
- Format: <DISEASE_MANAGEMENT: [1-2 sentence description], [days between treatments], [number of treatment cycles]>
- Example: <DISEASE_MANAGEMENT: Apply copper fungicide spray to affected leaves and monitor for spreading spots, 14, 3>

SECTION 4 - RE_DIAGNOSING:
- Specify when to check tree progress using the app
- Include signs that require immediate re-diagnosis
- Note if professional arborist consultation is recommended
- Format: <RE_DIAGNOSING: [1-2 sentence description], [days between check-ins], [number of scheduled check-ins]>
- Example: <RE_DIAGNOSING: Re-photograph tree to track recovery progress and consult arborist if condition worsens, 30, 4>

YOUR COMPLETE RESPONSE MUST BE EXACTLY 4 LINES IN THIS FORMAT:
<NUTRIENT_MANAGEMENT: description here, number, number>
<STRUCTURE_MANAGEMENT: description here, number, number>
<DISEASE_MANAGEMENT: description here, number, number>
<RE_DIAGNOSING: description here, number, number>

Remember: 
- NO extra text outside the 4 formatted lines
- Numbers ONLY (no "days", "times", "applications" words)
- Keep descriptions concise but actionable"""

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
                "temperature": 0.1,  # Lower temperature for more consistent formatting
                "max_tokens": 1024
            },
            timeout=90
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"API request failed with status {response.status_code}: {response.text}")
        
        schedule_text = response.json()['choices'][0]['message']['content'].strip()
        
        # Validate format before returning
        lines = [line.strip() for line in schedule_text.split('\n') if line.strip()]
        expected_tags = ['NUTRIENT_MANAGEMENT', 'STRUCTURE_MANAGEMENT', 'DISEASE_MANAGEMENT', 'RE_DIAGNOSING']
        
        if len(lines) != 4:
            raise RuntimeError(f"Invalid response format: Expected 4 lines, got {len(lines)}")
        
        for i, line in enumerate(lines):
            if not line.startswith('<') or not line.endswith('>'):
                raise RuntimeError(f"Invalid format on line {i+1}: Missing angle brackets")
            if expected_tags[i] not in line:
                raise RuntimeError(f"Invalid format on line {i+1}: Missing {expected_tags[i]} tag")
        
        return schedule_text
    
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out after 90 seconds")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error occurred: {str(e)}")