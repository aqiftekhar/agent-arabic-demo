"""
Centralized configuration for the AI voice agent stack.
"""

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)


def _get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


logger = _get_logger("agent-config")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise ConfigError(f"Missing required environment variable: {name}")
    return val


def _optional(name: str, default: str) -> str:
    return os.getenv(name, default)


class Settings:
    def __init__(self):
        # --- LiveKit ---
        self.livekit_url: str = _require("LIVEKIT_URL")
        self.livekit_api_key: str = _require("LIVEKIT_API_KEY")
        self.livekit_api_secret: str = _require("LIVEKIT_API_SECRET")

        # --- STT / LLM providers ---
        self.deepgram_api_key: str = _require("DEEPGRAM_API_KEY")
        self.groq_api_key: str = _require("GROQ_API_KEY")
        self.llm_model: str = _optional("LLM_MODEL", "openai/gpt-oss-120b")
        self.llm_base_url: str = _optional("LLM_BASE_URL", "https://api.groq.com/openai/v1")
        self.stt_model: str = _optional("STT_MODEL", "nova-3")
        self.stt_language: str = _optional("STT_LANGUAGE", "ar")

        # --- TTS provider (Deepgram TTS has no Arabic support, hence ElevenLabs) ---
        self.elevenlabs_api_key: str = _require("ELEVENLABS_API_KEY")
        self.elevenlabs_voice_id: str = _require("ELEVENLABS_VOICE_ID")
        self.tts_model: str = _optional("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5")

        # --- FreePBX / SIP topology ---
        self.freepbx_host: str = _require("FREEPBX_HOST")
        self.sip_did_number: str = _require("SIP_DID_NUMBER")
        self.sip_transfer_extension: str = _optional("SIP_TRANSFER_EXTENSION", "80")

        # --- Agent identity ---
        self.agent_name: str = _optional("AGENT_NAME", "va-arabic")

        # --- Guardrails / limits ---
        self.max_call_duration_seconds: int = int(_optional("MAX_CALL_DURATION_SECONDS", "600"))
        self.max_llm_tokens: int = int(_optional("MAX_LLM_TOKENS", "120"))
        self.dtmf_debounce_seconds: float = float(_optional("DTMF_DEBOUNCE_SECONDS", "0.3"))
        self.menu_timeout_seconds: float = float(_optional("MENU_TIMEOUT_SECONDS", "9"))
        self.menu_max_reprompts: int = int(_optional("MENU_MAX_REPROMPTS", "2"))

        # --- VAD tuning ---
        self.vad_min_speech_duration: float = float(_optional("VAD_MIN_SPEECH_DURATION", "0.1"))
        self.vad_min_silence_duration: float = float(_optional("VAD_MIN_SILENCE_DURATION", "0.8"))
        self.vad_prefix_padding_duration: float = float(_optional("VAD_PREFIX_PADDING_DURATION", "0.5"))
        self.vad_activation_threshold: float = float(_optional("VAD_ACTIVATION_THRESHOLD", "0.6"))

        # --- Endpointing tuning ---
        self.min_endpointing_delay: float = float(_optional("MIN_ENDPOINTING_DELAY", "1.2"))
        self.max_endpointing_delay: float = float(_optional("MAX_ENDPOINTING_DELAY", "6.0"))

    @property
    def operator_sip_uri(self) -> str:
        return f"sip:{self.sip_transfer_extension}@{self.freepbx_host}"

    @classmethod
    def load(cls) -> "Settings":
        try:
            settings = cls()
        except ConfigError as e:
            logger.error(str(e))
            logger.error(
                "Check your .env file — see .env.example for the full list "
                "of required variables."
            )
            sys.exit(1)
        return settings


if __name__ == "__main__":
    s = Settings.load()
    logger.info("Configuration OK.")
    logger.info(f"LiveKit URL: {s.livekit_url}")
    logger.info(f"FreePBX host: {s.freepbx_host}")
    logger.info(f"DID number: {s.sip_did_number}")
    logger.info(f"Operator transfer URI: {s.operator_sip_uri}")
    logger.info(f"STT language: {s.stt_language}")
    logger.info(f"Endpointing delay: {s.min_endpointing_delay}-{s.max_endpointing_delay}s")