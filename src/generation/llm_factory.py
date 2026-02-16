from typing import Any, Literal
from langchain_openai import ChatOpenAI


def create_llm(
    provider: Literal["minimax", "openai", "anthropic", "ollama", "custom"],
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    temperature: float = 0,
    **kwargs: Any
) -> Any:
    if provider == "minimax":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "MiniMax-M2.5",
            api_key=api_key,
            base_url=base_url or "https://api.minimaxi.com/anthropic",
            temperature=temperature if temperature > 0 else 1.0,
            **kwargs
        )

    elif provider == "openai":
        return ChatOpenAI(
            model=model or "gpt-4",
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or "claude-3-opus-20240229",
            api_key=api_key,
            temperature=temperature,
            **kwargs
        )

    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model or "llama2",
            temperature=temperature,
            **kwargs
        )

    elif provider == "custom":
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )

    else:
        raise ValueError(f"不支持的 LLM 提供商: {provider}")


class LLMFactory:
    PROVIDERS = Literal["minimax", "openai", "anthropic", "ollama", "custom"]

    @staticmethod
    def create(
        provider: PROVIDERS,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        temperature: float = 0,
        **kwargs: Any
    ) -> Any:
        return create_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )
