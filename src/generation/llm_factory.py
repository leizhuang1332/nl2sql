from typing import Any, Literal
from langchain_openai import ChatOpenAI


def create_llm(
    provider: Literal["minimax", "openai", "anthropic", "ollama", "custom"],
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    temperature: float = 0,
    stream: bool = False,
    thinking: bool = False,
    thinking_budget: int = 4096,
    **kwargs: Any
) -> Any:
    if provider == "minimax":
        from langchain_anthropic import ChatAnthropic
        
        # 构建 kwargs，包含 thinking 配置
        llm_kwargs = {
            "model": model or "MiniMax-M2.5",
            "api_key": api_key,
            "base_url": base_url or "https://api.minimaxi.com/anthropic",
            "temperature": temperature if temperature > 0 else 1.0,
            "streaming": stream,
            **kwargs
        }
        
        # 如果启用 thinking，设置 thinking 参数
        if thinking:
            # 确保 max_tokens 大于 thinking_budget
            current_max_tokens = llm_kwargs.get("max_tokens", 8192)
            if current_max_tokens <= thinking_budget:
                llm_kwargs["max_tokens"] = thinking_budget + 4096
            llm_kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        
        return ChatAnthropic(**llm_kwargs)

    elif provider == "openai":
        return ChatOpenAI(
            model=model or "gpt-4",
            api_key=api_key,
            temperature=temperature,
            streaming=stream,
            **kwargs
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        # 构建 kwargs，包含 thinking 配置
        llm_kwargs = {
            "model": model or "claude-3-opus-20240229",
            "api_key": api_key,
            "temperature": temperature,
            "streaming": stream,
            **kwargs
        }
        
        # 如果启用 thinking，设置 thinking 参数
        if thinking:
            current_max_tokens = llm_kwargs.get("max_tokens", 8192)
            if current_max_tokens <= thinking_budget:
                llm_kwargs["max_tokens"] = thinking_budget + 4096
            llm_kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        
        return ChatAnthropic(**llm_kwargs)

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
            streaming=stream,
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
        stream: bool = False,
        thinking: bool = False,
        thinking_budget: int = 4096,
        **kwargs: Any
    ) -> Any:
        return create_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            stream=stream,
            thinking=thinking,
            thinking_budget=thinking_budget,
            **kwargs
        )
