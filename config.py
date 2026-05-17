# CONFIGURATION FILE

# This file contains all configuration settings for the application.
# API keys, model settings, categories, and UI options are defined here.

# ---------------------------------------------------------------------------
# Environment Setup
# ---------------------------------------------------------------------------


# Try to load environment variables from .env file
# If dotenv fails, we fall back to default values
import os
import sys

try:
    from dotenv import load_dotenv
    # Build the absolute path to the .env file located in the same directory as this script
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Load environment variables from the specified path
    load_dotenv(env_path)
    
except Exception as e:
    # Catch the exception and print the error message to the console
    print("Critical Error: Failed to load environment variables from the .env file!")
    print(f"Error details: {e}")
    
    # Halt the system execution and exit with status code 1 (indicating an error)
    sys.exit(1)

# ---------------------------------------------------------------------------
# API Settings
# ---------------------------------------------------------------------------

# OpenCode API key - used for AI model calls
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "sk-your-key-here")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "sk-your-key-here")

# Base URL for OpenCode API
OPENCODE_BASE_URL = "https://opencode.ai/zen/v1/chat/completions"

# Base URL for Gemini API (you might need to update this based on actual endpoint)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

# Models to use for generating questions via OpenCode API
MINIMAX_MODEL = "minimax-m2.5-free"
DEEPSEEK_MODEL = "deepseek-v4-flash-free"

# Default model (backward compatibility)
OPENCODE_MODEL = MINIMAX_MODEL

# Gemini Model
GEMINI_MODEL = "gemini-2.5-flash"

# List of supported AI APIs
SUPPORTED_APIS = ["MiniMax", "DeepSeek", "Gemini"]

# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------

# The name shown in the browser tab and header
APP_NAME = "Vizit Medical Quiz Generator"

# Number of answer options for multiple choice questions (A-G = 7 options)
OPTIONS_COUNT = 7

# Maximum follow-up questions in case study mode (0-5 allowed)
MAX_CASE_FOLLOWUPS = 5

# Maximum hints available per question (default: 1)
MAX_HINTS = 1

# Enable/disable second chance feature (allows one retry after wrong answer)
SECOND_CHANCE_ENABLED = True

# ---------------------------------------------------------------------------
# Medical Categories
# ---------------------------------------------------------------------------
# List of medical specialties/topic areas for questions
CATEGORIES = [
    "Cardiology",        # Heart and cardiovascular system
    "Neurology",         # Brain and nervous system
    "Pediatrics",        # Children's medicine (DEFAULT)
    "Internal Medicine", # Adult internal diseases
    "Surgery",           # Surgical procedures
    "Pharmacology",      # Medications and drugs
    "Biochemistry",      # Chemical processes in living organisms
    "Anatomy",           # Body structure
    "Physiology"         # Body functions
]

CATEGORIES_TR = {
    "Cardiology": "Kardiyoloji",
    "Neurology": "Nöroloji",
    "Pediatrics": "Pediatri",
    "Internal Medicine": "Dahiliye",
    "Surgery": "Cerrahi",
    "Pharmacology": "Farmakoloji",
    "Biochemistry": "Biyokimya",
    "Anatomy": "Anatomi",
    "Physiology": "Fizyoloji"
}

# ---------------------------------------------------------------------------
# Difficulty Levels with Descriptions
# ---------------------------------------------------------------------------
# Each difficulty level has a description explaining what it tests
DIFFICULTIES = [
    "Intermediate",  # Basic level
    "Difficult",     # Medium level
    "Expert",         # Hard level
    "Grand Master"    # Very hard level
]

# Detailed descriptions for each difficulty level
# Shown to users when they select a difficulty
DIFFICULTY_DESCRIPTIONS = {
    # Intermediate: Tests fundamental skills with clear, straightforward options
    "Intermediate": "Tests fundamental skills and expects the examinee to have a solid grasp of basic definitions and concepts. Options are clear and straightforward.",
    
    # Difficult: Requires comprehensive knowledge with tricky distractors
    "Difficult": "Goes beyond the basic level; requires comprehensive knowledge of necessary clinical interventions. Includes tricky distractors.",
    
    # Expert: Tests mastery of core reference resources like textbooks
    "Expert": "Evaluates the mastery of core reference resources, such as Nelson Textbook of Pediatrics. Options include strong, high-level distractors.",
    
    # Grand Master: Focuses on cutting edge medicine from latest guidelines
    "Grand Master": "Focuses on the cutting edge of modern medicine; derived from the latest clinical guidelines and current literature. Options are highly deceptive and require advanced clinical reasoning."
}

DIFFICULTY_DESCRIPTIONS_TR = {
    "Intermediate": "Temel becerileri test eder ve adayın temel tanımlar ile kavramlara hakim olmasını bekler. Seçenekler net ve anlaşılırdır.",
    "Difficult": "Temel seviyenin ötesine geçer; gerekli klinik müdahaleler hakkında kapsamlı bilgi gerektirir. Yanıltıcı seçenekler içerir.",
    "Expert": "Nelson Pediatri gibi temel başvuru kaynaklarına hakimiyeti değerlendirir. Seçenekler güçlü ve üst düzey yanıltıcılardır.",
    "Grand Master": "Modern tıbbın en güncel noktasına odaklanır; en yeni klinik kılavuzlar ve güncel literatürden türetilmiştir. Seçenekler ileri düzey klinik akıl yürütme gerektirir."
}

# ---------------------------------------------------------------------------
# Question Types
# ---------------------------------------------------------------------------
# Types of questions the app can generate
QUESTION_TYPES = [
    "Multiple Choice",  # Standard MCQ with 7 options
    "Case Study"        # Clinical case with written answers
]