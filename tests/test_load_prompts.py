from src.helpers import load_prompts


def test_load_prompts() -> None:
    d = load_prompts("../data/prompts.json")
    assert isinstance(d, dict)
