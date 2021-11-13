from src.entities import read_rest_generators_config, RestGenerators


def test_config() -> None:
    gen = read_rest_generators_config("config/rest_generator_config.yaml")
    assert isinstance(gen, RestGenerators)
