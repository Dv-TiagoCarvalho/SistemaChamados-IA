"""Configurações lidas de variáveis de ambiente (ou do arquivo .env).

Equivale ao application.properties do Spring: nada de segredo fixo no código.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracoes(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./chamados.db"

    provedor_ia: str = "simulado"  # "simulado" ou "anthropic"
    anthropic_api_key: str | None = None
    modelo_ia: str = "claude-haiku-4-5-20251001"

    itsm_base_url: str = "http://localhost:8001"
    itsm_segredo_webhook: str = "troque-este-segredo"
    itsm_timeout_segundos: float = 3.0

    origens_permitidas: list[str] = ["http://localhost:5173"]


@lru_cache
def obter_configuracoes() -> Configuracoes:
    """Lê as configurações uma única vez e reaproveita (cache)."""
    return Configuracoes()
