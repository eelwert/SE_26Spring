from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

from backend import llm_service


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def print_raw_ai_output_when_requested(monkeypatch, request):
    """Print raw model output from tests only; do not modify backend code."""
    if os.environ.get("AI_DEBUG_RAW") != "1":
        return

    original_extract_json = llm_service._extract_json

    def debug_extract_json(raw: str):
        print(f"\n[ai-debug:{request.node.name}] raw content start")
        print(raw)
        print(f"[ai-debug:{request.node.name}] raw content end\n")
        return original_extract_json(raw)

    monkeypatch.setattr(llm_service, "_extract_json", debug_extract_json)


def require_ai_integration(key_name: str) -> str:
    if os.environ.get("SKIP_AI_INTEGRATION") == "1":
        pytest.skip("SKIP_AI_INTEGRATION=1 is set.")
    key = os.environ.get(key_name, "")
    if not key:
        pytest.skip(f"Set {key_name} to run this AI integration test.")
    return key


@pytest.mark.ai_integration
def test_deepseek_text_parser_returns_function_plan():
    api_key = require_ai_integration("DEEPSEEK_API_KEY")

    result = llm_service._call_llm(
        "切换成商业街模板，道路宽度调到10米，增加到4车道，傍晚小雨",
        api_key,
    )

    assert result is not None
    assert isinstance(result.get("plan"), list)
    assert result["plan"]
    assert {"funcName", "params"} <= set(result["plan"][0])


@pytest.mark.ai_integration
def test_qwen_sketch_analyzer_returns_structured_result():
    api_key = require_ai_integration("QWEN_API_KEY")
    image_base64 = base64.b64encode((ROOT / "sketch_triangle.png").read_bytes()).decode("ascii")

    result = llm_service.analyze_sketch(image_base64, api_key=api_key)

    assert {"points_text", "connections_text", "faces_text", "message"} <= set(result)
    assert result["message"] != "未设置 QWEN_API_KEY"


@pytest.mark.ai_integration
def test_zhipu_screenshot_analyzer_returns_json_plan():
    api_key = require_ai_integration("ZHIPU_API_KEY")
    image_base64 = base64.b64encode((ROOT / "sketch_tian.png").read_bytes()).decode("ascii")

    result = llm_service._analyze_screenshot(
        image_base64,
        "请分析这张图，并尽量输出一个可执行的城市布局或场景调整函数计划。",
        api_key,
    )
    
    assert result is not None
    assert isinstance(result.get("plan"), list)
