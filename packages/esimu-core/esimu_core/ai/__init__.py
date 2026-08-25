"""Optional AI integration for esimu simulator adapters.

The package is safe to import without the OpenAI SDK. Constructing
``OpenAICompatibleTransport`` requires the ``esimu-core[ai]`` extra.
"""

from esimu_core.ai.config import (
    AIModelConfig,
    generic_model_config_from_env,
    roleplay_model_config_from_env,
)
from esimu_core.ai.policy import ContentMode, ResolvedContent, resolve_content
from esimu_core.ai.service import AIContentService
from esimu_core.ai.transport import (
    ChatTransport,
    OpenAICompatibleTransport,
    OpenAITransportRegistry,
)

__all__ = [
    "AIContentService",
    "AIModelConfig",
    "ChatTransport",
    "ContentMode",
    "OpenAICompatibleTransport",
    "OpenAITransportRegistry",
    "ResolvedContent",
    "generic_model_config_from_env",
    "resolve_content",
    "roleplay_model_config_from_env",
]
