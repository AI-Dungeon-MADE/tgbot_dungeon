from dataclasses import dataclass
from typing import Dict

import yaml
from marshmallow_dataclass import class_schema


@dataclass
class RestGenerators:
    generators: Dict[str, str]


def read_rest_generators_config(path: str) -> RestGenerators:
    config_schema = class_schema(RestGenerators)
    with open(path, "r") as input_stream:
        schema = config_schema()
        return schema.load(yaml.safe_load(input_stream))
