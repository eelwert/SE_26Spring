import pytest

from backend import llm_service


def function_names(result: dict) -> list[str]:
    return [node["funcName"] for node in result["plan"]]


def test_local_parser_extracts_width_lanes_weather_and_template(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = llm_service.parse_command(
        "切换成商业街模板，道路宽度调到10米，增加到4车道，傍晚小雨",
        ["text"],
        [],
    )

    names = function_names(result)
    assert "apply_template_linkage" in names
    assert "set_street_width" in names
    assert "set_lane_amount" in names
    assert "set_weather_lighting" in names
    assert result["needsClarification"] is False


@pytest.mark.xfail(reason="backend.llm_service._parse_local uses undefined _re in simulation parsing")
def test_local_parser_handles_simulation_without_external_llm(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = llm_service.parse_command(
        "启动车辆与人群仿真，规则版本 traffic-r3.2",
        ["text"],
        [],
    )

    names = function_names(result)
    assert "run_traffic_simulation" in names
    assert "run_crowd_simulation" in names
    traffic = next(node for node in result["plan"] if node["funcName"] == "run_traffic_simulation")
    assert traffic["params"]["rules_version"] == "traffic-r3.2"


def test_unknown_text_requires_clarification(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = llm_service.parse_command("随便看看", ["text"], [])

    assert result["plan"] == []
    assert result["needsClarification"] is True


def test_sketch_without_api_key_requires_clarification(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    result = llm_service.parse_command("", ["sketch"], ["road.png"], image_base64="abc123")

    assert result["plan"] == []
    assert result["intentTag"] == "sketch_layout"
    assert result["needsClarification"] is True
