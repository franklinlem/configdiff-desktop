"""Experimento descartável: política antes de construir a árvore canônica."""

import math
import re

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode
from yaml.tokens import AliasToken, AnchorToken, TagToken


class PolicyError(ValueError):
    def __init__(self) -> None:
        super().__init__("YAML rejeitado pela política do protótipo")


def parse(text: str) -> object:
    if len(text.encode("utf-8")) > 5 * 1024 * 1024:
        raise PolicyError()
    try:
        for index, token in enumerate(yaml.scan(text)):
            if index > 200_000 or isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise PolicyError()
        root = yaml.compose(text, Loader=yaml.BaseLoader)
        count = 0

        def convert(node, depth=0):
            nonlocal count
            count += 1
            if count > 50_000 or depth > 64:
                raise PolicyError()
            if isinstance(node, MappingNode):
                result = {}
                for key, value in node.value:
                    if not isinstance(key, ScalarNode) or key.value == "<<" or key.value in result:
                        raise PolicyError()
                    result[key.value] = convert(value, depth + 1)
                return result
            if isinstance(node, SequenceNode):
                return [convert(child, depth + 1) for child in node.value]
            if not isinstance(node, ScalarNode):
                raise PolicyError()
            value = node.value
            if node.style is not None:
                return value
            if value in ("null", "~", ""):
                return None
            if value in ("true", "false"):
                return value == "true"
            if re.fullmatch(r"-?(0|[1-9][0-9]*)", value):
                return int(value)
            if re.fullmatch(r"-?(0|[1-9][0-9]*)\.[0-9]+([eE][+-]?[0-9]+)?", value):
                number = float(value)
                if not math.isfinite(number):
                    raise PolicyError()
                return number
            if value.lower() in (".nan", ".inf", "+.inf", "-.inf"):
                raise PolicyError()
            return value

        return None if root is None else convert(root)
    except (yaml.YAMLError, RecursionError, ValueError):
        raise PolicyError() from None
