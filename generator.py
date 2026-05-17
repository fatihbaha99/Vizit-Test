# ============================================================================
# AI QUESTION GENERATOR
# ============================================================================
# This module handles all AI-powered question generation.
# It communicates with OpenCode API to generate medical questions.

import json
import requests
import re
from config import (
    OPENCODE_API_KEY, OPENCODE_BASE_URL,
    MINIMAX_MODEL, DEEPSEEK_MODEL,
    GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL
)

def get_api_config(api_type):
    if api_type == "Gemini":
        return GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL
    elif api_type == "DeepSeek":
        return OPENCODE_API_KEY, OPENCODE_BASE_URL, DEEPSEEK_MODEL
    else:
        return OPENCODE_API_KEY, OPENCODE_BASE_URL, MINIMAX_MODEL


def call_api(system_prompt, user_prompt, api_type="OpenCode", temperature=0.3, max_tokens=16000, timeout=90):
    API_KEY, BASE_URL, MODEL = get_api_config(api_type)

    if api_type == "Gemini":
        headers = {
            "Content-Type": "application/json"
        }
        combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": combined}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
    else:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=timeout)

        if response.status_code != 200:
            return {"success": False, "error": f"API Error: {response.status_code}", "details": response.text[:500]}

        result = response.json()

        if api_type == "Gemini":
            if "candidates" not in result or not result["candidates"]:
                block_reason = result.get("promptFeedback", {}).get("blockReason", "unknown")
                return {"success": False, "error": f"Gemini blocked (reason: {block_reason})", "details": str(result)[:300]}
            candidate = result["candidates"][0]
            finish_reason = candidate.get("finishReason", "STOP")
            if finish_reason == "SAFETY":
                return {"success": False, "error": "Gemini blocked by safety filters", "details": str(candidate.get("safetyRatings", []))[:300]}
            content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
            if not content:
                return {"success": False, "error": f"Gemini empty response (finishReason: {finish_reason})", "details": str(candidate)[:300]}
        else:
            if "choices" not in result or not result["choices"]:
                return {"success": False, "error": "No choices in response", "details": str(result)[:200]}
            message = result["choices"][0]["message"]
            content = message.get("content", "") or message.get("reasoning_content", "") or message.get("reasoning", "")

            if content == "None" or content is None:
                content = message.get("reasoning", "") or message.get("reasoning_content", "") or ""
                if not content:
                    content = str(message.get("reasoning_details", ""))

            if not content and (message.get("reasoning") or message.get("reasoning_content")):
                content = message.get("reasoning") or message.get("reasoning_content") or ""

        if not content or content == "None":
            return {"success": False, "error": "Empty API response", "details": f"Status: {response.status_code}, Response body: '{response.text[:500] if response.text else 'empty'}'"}

        return {"success": True, "content": content}

    except json.JSONDecodeError as e:
        raw = response.text[:500] if 'response' in locals() else "No response"
        return {"success": False, "error": "JSON parse error", "details": str(e)[:200], "raw": raw}
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out", "details": "The AI took too long to respond"}
    except Exception as e:
        return {"success": False, "error": "Unknown error", "details": str(e)[:200]}


# ============================================================================
# MULTIPLE CHOICE QUESTION GENERATOR
# ============================================================================

def generate_question(category, difficulty, question_count=1, topic="", question_type="Multiple Choice", api_type="OpenCode", language="en"):
    options_letters = ["A", "B", "C", "D", "E", "F", "G"]

    # If user wants Case Study, call different function
    if question_type == "Case Study":
        return generate_case_study(category, difficulty, topic, api_type, language)

    # Build topic part of prompt (optional)
    topic_part = f" about {topic}" if topic else ""
    
    # Build prompt with difficulty-specific quality instructions
    # Keep prompts simple to avoid model outputting reasoning instead of JSON
    
    diff_quality = ""
    if difficulty == "Grand Master":
        diff_quality = "Distractors must be high-level and clinically plausible. Only one is correct."
    elif difficulty == "Expert":
        diff_quality = "Options should be tricky with plausible distractors."
    elif difficulty == "Difficult":
        diff_quality = "Include tricky distractors testing common misconceptions."
    else:
        diff_quality = "Clear options with plausible distractors."

    lang_instruction = "\n\nTüm sorular ve cevaplar TÜRKÇE olmalıdır." if language == 'tr' else ""
    prompt = f"""Generate {question_count} MULTIPLE CHOICE QUESTIONS (MCQ){topic_part} in {category} at {difficulty} level. {diff_quality}

CRITICAL: Output MUST be a JSON ARRAY where each item represents ONE question with 7 options (A-G).

JSON structure for each question:
{{
  "question": "clinical scenario or question text",
  "options": {{"A": "choice1", "B": "choice2", "C": "choice3", "D": "choice4", "E": "choice5", "F": "choice6", "G": "choice7"}},
  "correct_answer": "X",
  "explanation": "2-3 sentences explaining why this answer is correct",
  "hint": "1 sentence hint specific to THIS question's clinical case (not generic)",
  "category": "{category}",
  "difficulty": "{difficulty}"
}}

Example: For a pneumonia question, hint: "Consider which findings differentiate typical vs atypical pathogens." NOT "Review respiratory system."
{lang_instruction}

Output ONLY the JSON array, no additional text."""

    sys_prompt = "You are a medical exam question writer. Generate multiple choice questions with exactly 7 options (A-G). Output ONLY valid JSON array."
    if language == 'tr':
        sys_prompt += " Yanıtların TÜRKÇE olmalıdır."
    result = call_api(sys_prompt, prompt, api_type, 0.3, 16000, 180)

    if not result["success"]:
        return {"error": result["error"], "details": result["details"]}

    content = result["content"].strip()

    # Extract JSON from code blocks anywhere in the content
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
    if code_block:
        content = code_block.group(1).strip()

    # Parse JSON - handle truncated/invalid responses
    questions = None
    
    # Try direct parse
    try:
        questions = json.loads(content)
    except:
        pass
    
    if questions is None:
        # Fix truncated JSON
        fixed = content
        if fixed.count('{') > fixed.count('}'):
            fixed += '}' * (fixed.count('{') - fixed.count('}'))
        if fixed.count('[') > fixed.count(']'):
            fixed += ']' * (fixed.count('[') - fixed.count(']'))
        
        try:
            questions = json.loads(fixed)
        except:
            pass
    
    if questions is None:
        # Try regex to find JSON array (greedy match)
        m = re.search(r'(\[[\s\S]*\])', content)
        if m:
            extracted = m.group()
            try:
                questions = json.loads(extracted)
            except:
                try:
                    fixed = extracted.replace("'", '"').replace(',}', '}').replace(',]', ']')
                    fixed = re.sub(r'(?<!")(\w+)(?!")\s*:', r'"\1":', fixed)
                    questions = json.loads(fixed)
                except:
                    pass
    
    if questions is None:
        # Try to find individual question objects
        objs = re.findall(r'\{[^{}]*"question"[^{}]*\}', content)
        if objs:
            questions = []
            for o in objs:
                try:
                    questions.append(json.loads(o))
                except:
                    try:
                        fixed = o.replace("'", '"').replace(',}', '}')
                        fixed = re.sub(r'(?<!")(\w+)(?!")\s*:', r'"\1":', fixed)
                        questions.append(json.loads(fixed))
                    except:
                        continue
            if not questions:
                questions = None
    
    if questions is None:
        return {"error": "Could not parse AI response", "details": f"Content[0:300]: {content[:300] if content else 'empty'}", "raw": content[:500] if content else "No content"}

    # Ensure we have a list (single question -> list)
    if not isinstance(questions, list):
        questions = [questions]

    # Normalize question format
    for q in questions:
        if not isinstance(q, dict):
            continue
            
        if "question" not in q:
            q["question"] = str(q)
        
        # Get explanation from various possible field names
        explanation = (
            q.get("explanation") or 
            q.get("explanationText") or 
            q.get("explanation_text") or 
            q.get("Explanation") or
            q.get("reasoning") or
            ""
        )
        if not explanation or explanation == "None":
            explanation = "This question tests your knowledge of the topic. Review the relevant clinical guidelines for more details."
        q["explanation"] = explanation
            
        if "correctAnswer" in q and "correct_answer" not in q:
            q["correct_answer"] = q.pop("correctAnswer")
        if "correct_answer" not in q:
            for key in ["answer", "correct", "Answer", "Correct"]:
                if key in q:
                    q["correct_answer"] = str(q.pop(key))
                    break
        
        # Convert options array to dictionary if needed
        if "options" in q and isinstance(q["options"], dict):
            pass  # Already correct format
        elif "options" in q and isinstance(q["options"], list):
            options_dict = {}
            for opt in q["options"]:
                if isinstance(opt, dict):
                    key = opt.get("key", "")
                    text = opt.get("text", "") or opt.get("value", "") or str(opt)
                    if key and text:
                        options_dict[key] = text
                elif isinstance(opt, str):
                    idx = len(options_dict)
                    if idx < len(options_letters):
                        options_dict[options_letters[idx]] = opt
                elif isinstance(opt, list) and len(opt) >= 2:
                    options_dict[opt[0]] = opt[1]
            q["options"] = options_dict

        # Ensure hints exist
        if "hint" not in q or not q["hint"]:
            q["hint"] = ["Review the relevant clinical guidelines for this condition."]
        elif isinstance(q["hint"], list) and len(q["hint"]) > 0:
            q["hint"] = [q["hint"][0] if q["hint"][0] else "Review the relevant clinical guidelines."]

    return {"questions": questions, "count": len(questions), "type": "multiple_choice"}


# ============================================================================
# CASE STUDY GENERATOR
# ============================================================================

def _fallback_case(category, difficulty, language="en", raw=""):
    if language == 'tr':
        return {
            "case_title": "Tıbbi Vaka Çalışması",
            "category": category,
            "difficulty": difficulty,
            "patient": {"age": "Bilinmiyor", "gender": "Bilinmiyor", "occupation": "Bilinmiyor"},
            "chief_complaint": "Vaka verisi mevcut değil",
            "history": "Vaka verisi yüklenemedi",
            "physical_exam": "Yüklenemedi",
            "labs": {},
            "imaging": "",
            "working_diagnosis": "Bilinmiyor",
            "questions": [{"question": "Değerlendirmeniz nedir?", "answer": "Vaka verisi mevcut değil", "key_points": []}],
            "learning_points": ["Vaka çalışması yüklenemedi"]
        }
    return {
        "case_title": "Medical Case Study",
        "category": category,
        "difficulty": difficulty,
        "patient": {"age": "Unknown", "gender": "Unknown", "occupation": "Unknown"},
        "chief_complaint": "Case data unavailable",
        "history": f"RAW AI RESPONSE (debug):\n{raw[:500]}",
        "physical_exam": "Unable to load",
        "labs": {},
        "imaging": "",
        "working_diagnosis": "Unknown",
        "questions": [{"question": "What is your assessment?", "answer": "Case data unavailable", "key_points": []}],
        "learning_points": ["Unable to load case study"]
    }

def generate_case_study(category, difficulty, topic="", api_type="OpenCode", language="en"):
    # Build topic part of prompt
    topic_part = f" about {topic}" if topic else f" in {category}"

    lang_instruction = "\n\nTüm vaka verileri, sorular ve cevaplar TÜRKÇE olmalıdır." if language == 'tr' else ""

    # Detailed prompt for case study
    prompt = f"""Generate ONE detailed medical CASE STUDY{topic_part} with difficulty {difficulty}.

CRITICAL: Output MUST be a SINGLE JSON OBJECT (not an array), representing one patient case.

JSON structure:
{{{{
  "case_title": "descriptive title",
  "category": "{category}",
  "difficulty": "{difficulty}",
  "patient": {{"age": "X years", "gender": "male/female", "occupation": "..."}},
  "chief_complaint": "what brings patient to clinic",
  "history": "detailed history of present illness",
  "physical_exam": "relevant physical findings",
  "labs": {{"Lab Test Name": "result", ...}},
  "imaging": "imaging findings or omit if not applicable",
  "working_diagnosis": "initial diagnosis",
  "questions": [
    {{"question": "clinical question about this case", "answer": "detailed model answer", "key_points": ["point1", "point2"]}}
  ],
  "learning_points": ["clinical pearl 1", "clinical pearl 2"]
}}}}

The case should be comprehensive - include patient story, findings, and thought-provoking questions for discussion.
{lang_instruction}

Output ONLY the JSON object, no additional text."""

    sys_prompt = "You are an experienced medical educator. Create detailed clinical case studies with patient info, labs, imaging, and discussion questions."
    if language == 'tr':
        sys_prompt += " Tüm çıktıların TÜRKÇE olmalıdır."
    result = call_api(sys_prompt, prompt, api_type, 0.4, 8000, 180)

    if not result["success"]:
        print(f"[DEBUG] generate_case_study API call failed: {result.get('error')}", flush=True)
        return {"error": result["error"], "details": result["details"]}

    content = result["content"].strip()

    # Extract JSON from code blocks anywhere in the content
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
    if code_block:
        content = code_block.group(1).strip()

    # Parse JSON with error handling
    try:
        case = json.loads(content)
    except json.JSONDecodeError:
        # Try to find complete JSON object
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            extracted = json_match.group()
            try:
                case = json.loads(extracted)
            except:
                try:
                    # Fix unquoted keys and single quotes
                    fixed = extracted.replace("'", '"')
                    fixed = re.sub(r'(?<!")(\w+)(?!")\s*:', r'"\1":', fixed)
                    fixed = fixed.replace(',}', '}')
                    case = json.loads(fixed)
                except:
                    case = _fallback_case(category, difficulty, language, content)
        else:
            case = _fallback_case(category, difficulty, language, content)

    # Ensure questions exist
    if "questions" not in case or not isinstance(case["questions"], list):
        if language == 'tr':
            case["questions"] = [
                {"question": "İlk değerlendirmeniz nedir?", "answer": "Vaka sunumuna dayanarak...", "key_points": ["Klinik bulgular", "Ayırıcı tanı"]}
            ]
        else:
            case["questions"] = [
                {"question": "What is your initial assessment?", "answer": "Based on the case presentation...", "key_points": ["Clinical findings", "Differential diagnosis"]}
            ]

    # Add tracking fields
    case["current_question_index"] = 0
    case["followup_count"] = 0

    return {"case": case, "type": "case_study"}


# ============================================================================
# ANSWER VALIDATION
# ============================================================================

def validate_case_answer(case, question_index, user_answer, api_type="OpenCode"):
    # ... (rest of function)
    result = call_api("You are a medical educator. Provide constructive, detailed feedback on student answers.", prompt, api_type, 0.3, 1000, 180)

    if not result["success"]:
        return {"error": result["error"], "details": result["details"]}

    content = result["content"].strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        evaluation = json.loads(content)
        evaluation["student_answer"] = user_answer
        evaluation["model_answer"] = model_answer
        return evaluation
    except Exception as e:
        return {"error": "Failed to evaluate answer", "details": str(e)[:200]}


# ============================================================================
# FOLLOW-UP QUESTION GENERATOR
# ============================================================================

def generate_followup(case, question_index, user_answer, previous_followups, api_type="OpenCode"):
    # ... (rest of function)
    result = call_api("You are an experienced medical professor. Create probing questions that test deep understanding.", prompt, api_type, 0.4, 800, 180)

    if not result["success"]:
        return {"error": result["error"], "details": result["details"]}

    content = result["content"].strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        followup = json.loads(content)
        return followup
    except Exception as e:
        return {"error": "Failed to generate follow-up", "details": str(e)[:200]}