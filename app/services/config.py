"""
Configuration file for the new dashboard creation pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env.local")

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model Configuration
MODELS = {
    "analyzer": "meta-llama/llama-4-scout-17b-16e-instruct",
    "designer": "deepseek-r1-distill-llama-70b", 
    "coder": "openai/gpt-oss-20b"
}

# Vector Database Configuration
VECTOR_DB_CONFIG = {
    "persist_directory": "./chroma_db",
    "collection_name": "viz_examples",
    "embedding_space": "cosine"
}

# Pipeline Configuration
PIPELINE_CONFIG = {
    "max_examples_retrieved": 3,
    "analysis_sample_size": 5,
    "design_temperature": 0.3,
    "code_temperature": 0.1,
    "optimization_temperature": 0.1
}

# Output Configuration
OUTPUT_CONFIG = {
    "output_directory": "./generated_dashboards",
    "filename_prefix": "generated_dashboard",
    "timestamp_format": "%Y%m%d_%H%M%S"
}

# Visualization Templates
TEMPLATES_FILE = "/Users/suhaaniagarwal/viz.ai/backend/app/services/rag1_example_viz.json"

# Default User Prompts
DEFAULT_PROMPTS = {
    "sales": "Create a beautiful animated dashboard showing sales trends by product and region with profit analysis, including interactive filters and time-based animations",
    "financial": "Create a professional financial dashboard with animated charts, correlation analysis, and interactive asset selection",
    "healthcare": "Create a medical performance dashboard with patient outcomes, resource utilization, and professional medical aesthetics",
    "environmental": "Create a climate monitoring dashboard with animated maps, trend analysis, and environmental insights",
    "general": "Create the best animated interactive dashboard that represents the entire dataset beautifully with linked plots"
}

# Validation
def validate_config():
    """Validate the configuration"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    if not os.path.exists(TEMPLATES_FILE):
        raise ValueError(f"Templates file not found: {TEMPLATES_FILE}")
    
    return True

# Get configuration
def get_config():
    """Get the complete configuration"""
    return {
        "groq_api_key": GROQ_API_KEY,
        "models": MODELS,
        "vector_db": VECTOR_DB_CONFIG,
        "pipeline": PIPELINE_CONFIG,
        "output": OUTPUT_CONFIG,
        "templates_file": TEMPLATES_FILE,
        "default_prompts": DEFAULT_PROMPTS
    }

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration is valid")
        config = get_config()
        print(f"🔧 Using models: {config['models']}")
        print(f"📁 Templates: {config['templates_file']}")
    except Exception as e:
        print(f"❌ Configuration error: {e}") 