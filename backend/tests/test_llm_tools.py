import pytest

from app.llm.tools import format_tool_result, parse_tool_arguments


def test_parse_tool_arguments_returns_dict() -> None:
    assert parse_tool_arguments('{"sku": "MON-0001"}') == {"sku": "MON-0001"}


def test_parse_tool_arguments_rejects_non_object() -> None:
    with pytest.raises(ValueError):
        parse_tool_arguments('["MON-0001"]')


def test_format_tool_result_prefers_text_content() -> None:
    result = {
        "content": [
            {"type": "text", "text": "Product: Meridian 27 inch Monitor"},
        ],
        "structuredContent": {"result": "ignored"},
    }

    assert format_tool_result(result) == "Product: Meridian 27 inch Monitor"


def test_format_tool_result_falls_back_to_result_field() -> None:
    assert format_tool_result({"result": "Found 5 orders"}) == "Found 5 orders"

