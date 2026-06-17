import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class ConfigError(ValueError):
    """Exception raised for missing or invalid configuration settings."""
    pass

class Config:
    """Configuration class containing all environment variables and constant settings."""
    
    # Required Google OAuth configuration
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    GOOGLE_OAUTH_REFRESH_TOKEN: str = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "")
    
    # Required Groq configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Required Google Drive folder ID for knowledge base files
    KNOWLEDGE_DRIVE_FOLDER_ID: str = os.getenv("KNOWLEDGE_DRIVE_FOLDER_ID", "")
    
    # Recipient email for the daily digest
    DIGEST_RECIPIENT_EMAIL: str = os.getenv("DIGEST_RECIPIENT_EMAIL", "")
    
    # Configurable labels (with defaults)
    LABEL_PROCESSED: str = os.getenv("AGENT_PROCESSED_LABEL", "Agent-Processed")
    LABEL_NEEDS_HUMAN: str = os.getenv("NEEDS_HUMAN_LABEL", "Needs-Human")
    
    # Configurable Groq LLM models (with defaults)
    # Triage model: cheap, fast, smaller context requirement
    MODEL_TRIAGE: str = os.getenv("GROQ_TRIAGE_MODEL", "llama3-8b-8192")
    # Drafting model: stronger reasoning, larger capacity
    MODEL_DRAFT: str = os.getenv("GROQ_DRAFT_MODEL", "llama-3.3-70b-specdec")
    
    @classmethod
    def validate(cls) -> None:
        """Validates that all required configuration settings are present.
        
        Raises:
            ConfigError: If any required setting is missing.
        """
        missing_fields = []
        
        if not cls.GOOGLE_OAUTH_CLIENT_ID:
            missing_fields.append("GOOGLE_OAUTH_CLIENT_ID")
        if not cls.GOOGLE_OAUTH_CLIENT_SECRET:
            missing_fields.append("GOOGLE_OAUTH_CLIENT_SECRET")
        if not cls.GOOGLE_OAUTH_REFRESH_TOKEN:
            missing_fields.append("GOOGLE_OAUTH_REFRESH_TOKEN")
        if not cls.GROQ_API_KEY:
            missing_fields.append("GROQ_API_KEY")
        if not cls.KNOWLEDGE_DRIVE_FOLDER_ID:
            missing_fields.append("KNOWLEDGE_DRIVE_FOLDER_ID")
            
        if missing_fields:
            raise ConfigError(
                f"Missing required configuration environment variables: {', '.join(missing_fields)}. "
                "Please configure them in your environment or in a .env file."
            )
