from unittest.mock import Mock

from tools.lead_qualifier.rag_assistant import GeminiGenerationClient, answer_from_results
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

