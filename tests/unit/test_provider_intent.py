"""Tests for explicit natural-language provider intent detection."""
from core.conversation_intelligence.provider_intent import parse_provider_intent


def test_single_provider_portuguese_command():
    result = parse_provider_intent("Pede ajuda ao ChatGPT: revê esta arquitetura.")
    assert result.requested is True
    assert result.providers == ("chatgpt",)
    assert result.question == "revê esta arquitetura."


def test_multiple_providers_portuguese_command():
    result = parse_provider_intent("Consulta o Grok e o Gemini: compara estas opções.")
    assert result.requested is True
    assert result.providers == ("grok", "gemini")
    assert result.question == "compara estas opções."


def test_all_supported_providers_are_recognized():
    result = parse_provider_intent(
        "Pede ajuda ao ChatGPT, Grok, Gemini, Claude, DeepSeek e Qwen: "
        "analisa o plano."
    )
    assert result.providers == ("chatgpt", "grok", "gemini", "claude", "deepseek", "qwen")
    assert result.question == "analisa o plano."


def test_english_command_is_supported():
    result = parse_provider_intent("Ask ChatGPT and Claude: review this design.")
    assert result.requested is True
    assert result.providers == ("chatgpt", "claude")
    assert result.question == "review this design."


def test_provider_mention_without_command_does_not_dispatch():
    result = parse_provider_intent("O ChatGPT e o Grok têm opiniões diferentes.")
    assert result.requested is False
    assert result.providers == ()


def test_command_without_provider_does_not_dispatch():
    result = parse_provider_intent("Pede ajuda a uma IA: revê esta arquitetura.")
    assert result.requested is False
    assert result.reason == "explicit_intent_without_supported_provider"


def test_empty_message_is_safe():
    assert parse_provider_intent("").requested is False
    assert parse_provider_intent(None).requested is False


def test_provider_mentioned_before_command_is_not_selected():
    result = parse_provider_intent(
        "O ChatGPT foi mencionado. Consulta o Gemini: analisa esta proposta."
    )
    assert result.requested is True
    assert result.providers == ("gemini",)
    assert result.question == "analisa esta proposta."


def test_provider_mentioned_after_question_boundary_is_not_selected():
    result = parse_provider_intent(
        "Consulta o Grok: analisa esta proposta. O ChatGPT também foi referido."
    )
    assert result.requested is True
    assert result.providers == ("grok",)
    assert result.question == "analisa esta proposta. O ChatGPT também foi referido."
