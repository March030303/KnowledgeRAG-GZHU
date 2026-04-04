from pathlib import Path

from dotenv import dotenv_values

from trace_logging import get_trace_id


def test_trace_id_is_available() -> None:
    trace_id = get_trace_id()
    assert isinstance(trace_id, str)
    assert len(trace_id) == 8


def test_env_example_contains_langsmith_settings() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env.example"
    values = dotenv_values(env_path)

    assert values.get("DB_HOST")
    assert "LANGSMITH_TRACING" in values
    assert "LANGSMITH_PROJECT" in values
