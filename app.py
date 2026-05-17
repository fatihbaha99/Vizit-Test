# MAIN FLASK APPLICATION

# This is the main server file that handles all web requests.
# It routes requests to appropriate functions and manages user sessions.

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_session import Session
import json, os

# Import configuration settings
from config import (
    CATEGORIES,
    DIFFICULTIES,
    QUESTION_TYPES,
    MAX_CASE_FOLLOWUPS,
    SECOND_CHANCE_ENABLED,
    APP_NAME,
    DIFFICULTY_DESCRIPTIONS,
    DIFFICULTY_DESCRIPTIONS_TR,
    CATEGORIES_TR,
    SUPPORTED_APIS
)

# Create Flask application
app = Flask(__name__)
app.secret_key = 'medicine-quiz-secret-key-2024'

# Use server-side sessions (filesystem) to avoid cookie size limits
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# Import AI generation functions
from generator import (
    generate_question,
    validate_case_answer,
    generate_followup
)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/config')
def config():
    lang = session.get('lang', 'en')
    return jsonify({
        'lang': lang,
        'categories': {c: CATEGORIES_TR.get(c, c) for c in CATEGORIES},
        'difficulties': DIFFICULTIES,
        'question_types': QUESTION_TYPES,
        'supported_apis': SUPPORTED_APIS,
        'app_name': APP_NAME,
        'difficulty_descriptions': DIFFICULTY_DESCRIPTIONS,
        'difficulty_descriptions_tr': DIFFICULTY_DESCRIPTIONS_TR
    })

@app.route('/set-lang', methods=['POST'])
def set_lang():
    data = request.get_json()
    lang = data.get('lang', 'en')
    if lang in ('en', 'tr'):
        session['lang'] = lang
    return jsonify({'success': True})



@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/.well-known/<path:path>')
def well_known(path):
    return '', 204

@app.after_request
def suppress_warnings(response):
    return response


# ============================================================================
# ROUTES
# ============================================================================
# Routes determine what happens when users visit different URLs

# ---------------------------------------------------------------------------
# GENERATE QUESTIONS - Create new questions based on user settings
# ---------------------------------------------------------------------------
@app.route('/generate', methods=['POST'])
def generate():
    """
    When user clicks "Generate Questions" button:
    
    1. Get settings from form (category, difficulty, count, topic)
    2. Call AI to generate questions
    3. Store questions in session (temporary server storage)
    4. Return questions to browser
    
    Request JSON format:
    {
        "category": "Pediatrics",
        "difficulty": "Intermediate",
        "count": 5,
        "topic": "malnutrition",  // optional
        "question_type": "Multiple Choice"  // or "Case Study"
    }
    """
    # Get data from POST request
    data = request.get_json()

    # Extract user settings
    api_type = data.get('api_type', 'OpenCode')
    category = data.get('category', 'Internal Medicine')
    difficulty = data.get('difficulty', 'Medium')
    count = min(int(data.get('count', 5)), 20)  # Max 20 questions
    topic = data.get('topic', '').strip()  # Optional specific topic
    question_type = data.get('question_type', 'Multiple Choice')
    lang = data.get('lang', session.get('lang', 'en'))

    # Handle Case Study differently
    if question_type == 'Case Study':
        result = generate_case_study_function(category, difficulty, topic, api_type, lang)
        # Auto-fallback: if Gemini fails, try MiniMax
        if "error" in result and api_type == "Gemini":
            print(f"[FALLBACK] Gemini failed, trying MiniMax: {result.get('error')}", flush=True)
            result = generate_case_study_function(category, difficulty, topic, "MiniMax", lang)
            api_type = "MiniMax"
    else:
        # Generate multiple choice questions
        result = generate_question(category, difficulty, count, topic, question_type, api_type, lang)

    # Check if AI returned an error
    if "error" in result:
        print(f"Error in generate: {result}")
        return jsonify(result), 500

    # Handle Case Study response
    if question_type == 'Case Study':
        stored_case = result.get('case', {})
        session['case'] = stored_case
        session['case_api_type'] = api_type
        session['current_question_index'] = 0
        session['followups'] = []
        session['case_score'] = 0
        session['case_questions_answered'] = []
        return jsonify({
            'success': True,
            'case': stored_case,
            'type': 'case_study'
        })

    # Handle Multiple Choice response
    else:
        # Add tracking fields to each question
        for q in result.get('questions', []):
            q['hints_used'] = 0
            q['second_chance_used'] = False

        # Store in session
        session['questions'] = result['questions']
        session['current_index'] = 0
        session['score'] = 0
        session['answers'] = []

        return jsonify({
            'success': True,
            'questions': result['questions'],
            'total': len(result['questions']),
            'type': 'multiple_choice'
        })


def generate_case_study_function(category, difficulty, topic="", api_type="OpenCode", lang="en"):
    """Helper function to call case study generator"""
    from generator import generate_case_study as gen_case
    return gen_case(category, difficulty, topic, api_type, lang)


# ---------------------------------------------------------------------------
# GET QUESTION - Get a specific question by index
# ---------------------------------------------------------------------------
@app.route('/question/<int:index>')
def get_question(index):
    """
    Get question details for a specific index.
    Used for navigation between questions.
    
    URL: /question/0  (gets first question)
    Returns: Question data as JSON
    """
    questions = session.get('questions', [])
    if index >= len(questions):
        return jsonify({'error': 'No more questions'}), 404

    return jsonify({
        'question': questions[index],
        'current': index + 1,
        'total': len(questions)
    })


# ---------------------------------------------------------------------------
# SUBMIT ANSWER - Check user's answer
# ---------------------------------------------------------------------------
@app.route('/answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    question_index = data.get('question_index', 0)
    selected_answer = data.get('answer', '').upper()
    is_second_chance = data.get('second_chance', False)

    questions = session.get('questions', [])
    if question_index >= len(questions):
        return jsonify({'error': 'Invalid question index'}), 404

    question = questions[question_index]
    correct = question.get('correct_answer', '').upper()
    hint_raw = question.get('hint', '')
    if isinstance(hint_raw, list) and len(hint_raw) > 0:
        hint = hint_raw[0] if hint_raw[0].strip() else 'Review the relevant clinical concepts.'
    elif hint_raw and isinstance(hint_raw, str) and hint_raw.strip():
        hint = hint_raw
    else:
        hint = 'Review the relevant clinical concepts.'
    explanation = question.get('explanation', 'No explanation available.')

    if question.get('answered'):
        return jsonify({
            'is_correct': question.get('is_correct'),
            'correct_answer': correct,
            'explanation': explanation,
            'score': session.get('score', 0),
            'total_answered': len(session.get('answers', [])),
            'already_answered': True,
            'user_answer': question.get('user_answer')
        })

    is_correct = selected_answer == correct

    if is_correct:
        question['user_answer'] = selected_answer
        question['is_correct'] = True
        question['answered'] = True
        question['explanation'] = explanation
        session['score'] = session.get('score', 0) + 1

        answer_record = {
            'question_index': question_index,
            'selected': selected_answer,
            'correct': correct,
            'is_correct': True,
            'question': question.get('question', ''),
            'explanation': explanation,
            'second_chance_used': False
        }
        session['answers'] = session.get('answers', []) + [answer_record]

        return jsonify({
            'is_correct': True,
            'correct_answer': correct,
            'explanation': explanation,
            'score': session.get('score', 0),
            'total_answered': len(session.get('answers', []))
        })

    if not is_second_chance:
        question['user_answer'] = selected_answer
        question['is_correct'] = False

        answer_record = {
            'question_index': question_index,
            'selected': selected_answer,
            'correct': correct,
            'is_correct': False,
            'question': question.get('question', ''),
            'explanation': explanation,
            'second_chance_used': True
        }
        session['answers'] = session.get('answers', []) + [answer_record]

        return jsonify({
            'is_correct': False,
            'correct_answer': correct,
            'hint': hint,
            'explanation': explanation,
            'score': session.get('score', 0),
            'total_answered': len(session.get('answers', [])),
            'second_chance_available': True
        })

    question['answered'] = True
    question['explanation'] = explanation

    return jsonify({
        'is_correct': False,
        'correct_answer': correct,
        'explanation': explanation,
        'score': session.get('score', 0),
        'total_answered': len(session.get('answers', [])),
        'second_chance_available': False
    })


# ============================================================================
# CASE STUDY ROUTES
# ============================================================================

@app.route('/case/chat', methods=['POST'])
def case_chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    lang = data.get('lang', session.get('lang', 'en'))
    case = session.get('case', {})
    if not case:
        return jsonify({'error': 'No case loaded'}), 404

    difficulty = case.get('difficulty', 'Intermediate')
    from generator import call_api
    chat_api_type = session.get('case_api_type', 'OpenCode')

    case_context = json.dumps(case, indent=2)
    lang_instruction = "TÜRKÇE konuş. Tüm yanıtların ve soruların Türkçe olmalıdır.\n\n" if lang == 'tr' else ""
    system_prompt = f"""{lang_instruction}You are a medical educator having a natural conversation with a student about this case. Talk like a friendly tutor — warm, encouraging, and adaptive.

=== FULL CASE DATA (reference only, do NOT repeat) ===
{case_context}

=== STUDENT KNOWLEDGE LEVEL: {difficulty} ===
- Intermediate: Student knows basics. Ask clear, fundamental questions.
- Difficult: Student handles complex cases. Ask nuanced clinical reasoning questions.
- Expert: Student mastered textbooks. Ask about rare conditions, subtle clues.
- Grand Master: Student knows latest guidelines. Ask about controversial topics and advanced reasoning.

=== CONVERSATION GUIDELINES ===
- Have a natural back-and-forth dialogue, NOT a rigid test
- Ask ONE question at a time
- Adapt follow-up questions based on what the student says — do NOT repeat similar questions
- If the student is partially correct, acknowledge and help them refine
- If wrong, guide gently with hints rather than just saying incorrect
- Keep responses warm and conversational (2-4 sentences)
- Do NOT repeat case data that's already shown above"""

    result = call_api(system_prompt, message, chat_api_type, 0.4, 2000, 180)

    if not result["success"]:
        return jsonify({'error': result["error"]}), 500

    return jsonify({'response': result["content"]})

@app.route('/case/question/<int:index>')
def get_case_question(index):
    """Get a specific question from the case study"""
    case = session.get('case', {})
    questions = case.get('questions', [])

    if index >= len(questions):
        return jsonify({'error': 'No more questions', 'no_more': True}), 404

    return jsonify({
        'question': questions[index],
        'current': index + 1,
        'total': len(questions),
        'followup_count': len(session.get('followups', [])),
        'max_followups': MAX_CASE_FOLLOWUPS
    })


@app.route('/case/validate', methods=['POST'])
def validate_case_answer_route():
    """
    Validate user's written answer for case study questions.
    Uses AI to compare user's answer with model answer and provide feedback.
    """
    data = request.get_json()
    question_index = data.get('question_index', 0)
    user_answer = data.get('answer', '').strip()

    case = session.get('case', {})
    if not case:
        return jsonify({'error': 'No case loaded'}), 404

    api_type = session.get('case_api_type', 'MiniMax')

    # Call AI to validate answer
    result = validate_case_answer(case, question_index, user_answer, api_type)

    if "error" in result:
        return jsonify(result), 500

    # Track answered questions
    session['case_questions_answered'] = session.get('case_questions_answered', []) + [{
        'question_index': question_index,
        'question': case.get('questions', [])[question_index].get('question', ''),
        'student_answer': user_answer,
        'score': result.get('score', 0)
    }]

    session['case_score'] = session.get('case_score', 0) + result.get('score', 0)

    return jsonify(result)


@app.route('/case/followup', methods=['POST'])
def submit_followup():
    """
    Generate a follow-up question based on user's answer.
    Allows up to MAX_CASE_FOLLOWUPS (5) follow-ups per question.
    """
    data = request.get_json()
    question_index = data.get('question_index', 0)
    user_answer = data.get('answer', '').strip()

    case = session.get('case', {})
    followups = session.get('followups', [])
    api_type = session.get('case_api_type', 'MiniMax')

    if len(followups) >= MAX_CASE_FOLLOWUPS:
        return jsonify({'error': 'Maximum follow-up questions reached', 'max_reached': True}), 400

    # Generate follow-up using AI
    result = generate_followup(case, question_index, user_answer, followups, api_type)

    if "error" in result:
        return jsonify(result), 500

    # Store follow-up in session
    followups.append({
        'question': result.get('followup_question', ''),
        'expected': result.get('expected_answer', ''),
        'user_answer': user_answer,
        'concept': result.get('clinical_concept', '')
    })
    session['followups'] = followups

    return jsonify({
        'followup': result,
        'followup_number': len(followups),
        'max_followups': MAX_CASE_FOLLOWUPS,
        'can_continue': len(followups) < MAX_CASE_FOLLOWUPS
    })


@app.route('/case/validate-followup', methods=['POST'])
def validate_followup():
    """Validate user's answer to a follow-up question"""
    data = request.get_json()
    followup_index = data.get('followup_index', 0)
    user_answer = data.get('answer', '').strip()

    followups = session.get('followups', [])
    if followup_index >= len(followups):
        return jsonify({'error': 'Invalid follow-up index'}), 404

    followup = followups[followup_index]
    expected = followup.get('expected', '')

    # Simple comparison - could be enhanced with AI validation
    prompt = f"""Compare these answers and score 0-100:
Expected: {expected}
Student: {user_answer}

Output JSON: {{"score": number, "feedback": "..."}}"""

    result = validate_followup_ai(prompt)

    if "error" not in result:
        session['case_score'] = session.get('case_score', 0) + result.get('score', 0)

    return jsonify(result)


def validate_followup_ai(prompt):
    """Helper to validate follow-up answers using AI"""
    import requests
    from config import OPENCODE_API_KEY, OPENCODE_BASE_URL, OPENCODE_MODEL

    headers = {
        "Authorization": f"Bearer {OPENCODE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENCODE_MODEL,
        "messages": [
            {"role": "system", "content": "You are a medical educator. Evaluate student answers briefly."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }

    try:
        response = requests.post(OPENCODE_BASE_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "") or result.get("choices", [{}])[0].get("message", {}).get("reasoning", "")

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content)
    except Exception as e:
        return {"score": 50, "feedback": "Could not evaluate answer. Please review the concept."}


# ============================================================================
# RESULTS ROUTES
# ============================================================================

@app.route('/results')
def results():
    """
    Get quiz results after completing all questions.
    Returns score, all questions, and user's answers.
    """
    questions = session.get('questions', [])
    answers = session.get('answers', [])
    score = session.get('score', 0)

    return jsonify({
        'score': score,
        'total': len(questions),
        'answers': answers,
        'questions': questions
    })


@app.route('/case/results')
def case_results():
    """Get case study results"""
    case = session.get('case', {})
    questions_answered = session.get('case_questions_answered', [])
    followups = session.get('followups', [])
    score = session.get('case_score', 0)

    total_possible = len(questions_answered) * 100
    if total_possible > 0:
        percentage = (score / total_possible) * 100
    else:
        percentage = 0

    return jsonify({
        'score': score,
        'total_possible': total_possible,
        'percentage': round(percentage, 1),
        'case': case,
        'questions_answered': questions_answered,
        'followups': followups
    })


@app.route('/reset', methods=['POST'])
def reset():
    """Clear all session data - start fresh"""
    session.clear()
    return jsonify({'success': True})


# ============================================================================
# START SERVER
# ============================================================================
if __name__ == '__main__':
    import logging
    # Enable standard Flask/Werkzeug request logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)