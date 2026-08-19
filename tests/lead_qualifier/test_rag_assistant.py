from unittest.mock import Mock

from tools.lead_qualifier.rag_assistant import (
    GeminiGenerationClient,
    GroqGenerationClient,
    answer_from_results,
    direct_answer_for_common_question,
)
from tools.lead_qualifier.vector_store import VectorSearchResult


def _result(score: float = 0.8) -> VectorSearchResult:
    return VectorSearchResult(
        heading="Opening hours",
        content="Restaurant: daily, 09:00–23:00.",
        source_file="restaurant_info.md",
        metadata={"venue": "Family Secret"},
        score=score,
    )


def test_answer_uses_retrieved_context():
    client = Mock()
    client.generate.return_value = "Ресторан открыт ежедневно с 09:00 до 23:00."

    answer = answer_from_results("Когда вы открыты?", [_result()], client)

    assert answer.text == "Ресторан открыт ежедневно с 09:00 до 23:00."
    assert answer.sources == (_result(),)
    assert "Restaurant: daily, 09:00–23:00" in client.generate.call_args.args[1]


def test_weak_results_do_not_call_generation_model():
    client = Mock()

    answer = answer_from_results("Есть парковка?", [_result(score=0.2)], client)

    assert "нет надёжного ответа" in answer.text
    assert answer.sources == ()
    client.generate.assert_not_called()


def test_generation_client_extracts_text_from_response():
    response = Mock()
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "First "}, {"text": "answer"}]}}]
    }
    session = Mock()
    session.post.return_value = response
    client = GeminiGenerationClient("test-key", session=session)

    assert client.generate("Question", "Context") == "First answer"
    response.raise_for_status.assert_called_once()
    payload = session.post.call_args.kwargs["json"]
    assert payload["generationConfig"]["maxOutputTokens"] == 1024
    assert payload["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}


def test_common_hours_question_has_complete_direct_answer():
    answer = direct_answer_for_common_question("how you work")

    assert answer == (
        "We are open every day from 9:00 AM to 11:00 PM. "
        "We look forward to welcoming you to Family Secret!"
    )


def test_common_hours_question_answers_warmly_in_russian():
    answer = direct_answer_for_common_question("Как вы работаете?")

    assert answer == (
        "Мы открыты каждый день с 9 утра до 11 вечера. "
        "Будем рады видеть вас в Family Secret!"
    )


def test_common_menu_question_answers_in_russian():
    answer = direct_answer_for_common_question("У вас есть картофельное пюре?")

    assert answer == "Да, у нас есть картофельное пюре в качестве гарнира."


def test_groq_generation_client_extracts_fallback_answer():
    response = Mock()
    response.json.return_value = {
        "choices": [{"message": {"content": "Полный запасной ответ."}}]
    }
    session = Mock()
    session.post.return_value = response
    client = GroqGenerationClient("test-key", session=session)

    assert client.generate("Вопрос", "Факты") == "Полный запасной ответ."
    response.raise_for_status.assert_called_once()
    request = session.post.call_args.kwargs
    assert request["json"]["model"] == "openai/gpt-oss-20b"
    assert request["headers"]["Authorization"] == "Bearer test-key"
