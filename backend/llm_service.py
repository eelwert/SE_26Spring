"""Backend-side LLM service — parses user NL commands into function plans.

Uses DeepSeek API (OpenAI-compatible) when available, falls back to keyword
parsing. The function registry is synced with the Blender plugin.
"""

import json
import os
import re

# For LLM API call
import urllib.request
import urllib.error
import ssl

DEFAULT_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

# Zhipu GLM-4V multimodal visual model
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_VISION_MODEL = "glm-4v-flash"

FUNCTION_LIST = [
    {"name": "apply_template_linkage", "params": {"template_id": "int 0-9", "tree_density": "int", "road_width": "int"}},
    {"name": "set_weather_lighting", "params": {"weather": "string", "time_of_day": "string HH:MM"}},
    {"name": "set_street_width", "params": {"width": "number 米"}},
    {"name": "set_lane_amount", "params": {"lanes": "int"}},
    {"name": "set_tree_density", "params": {"density": "number 0-1"}},
    {"name": "set_street_lights", "params": {"enable": "bool"}},
    {"name": "set_corner_radius", "params": {"radius": "number 米"}},
    {"name": "set_parking_probability", "params": {"probability": "number 0-1"}},
    {"name": "set_traffic_lights", "params": {"probability": "number 0-1"}},
    {"name": "set_building_height", "params": {"height": "int 米"}},
    {"name": "set_seed", "params": {"seed": "number"}},
    {"name": "set_sidewalk_scale", "params": {"scale": "number"}},
    {"name": "toggle_traffic", "params": {"enable": "bool"}},
    {"name": "toggle_buildings", "params": {"enable": "bool"}},
    {"name": "run_traffic_simulation", "params": {"rules_version": "string", "seed": "int"}},
    {"name": "run_crowd_simulation", "params": {"rules_version": "string", "seed": "int", "agent_count": "int"}},
    {"name": "solve_point_layout", "params": {"point_set": "array"}},
    {"name": "extract_sketch_topology", "params": {"attachment_ref": "string", "scale": "string"}},
]

SYSTEM_PROMPT = f"""你是智能城市生成系统的 AI 助手。将用户的自然语言指令转换为函数调用 JSON。

可用函数：
{json.dumps(FUNCTION_LIST, ensure_ascii=False, indent=2)}

输出纯 JSON（不含 markdown 标记）：
{{
  "plan": [
    {{"id": "node-1", "funcName": "set_street_width", "title": "调整道路宽度", "params": {{"width": 10}}}}
  ],
  "explanation": "中文说明",
  "intentTag": "scene_edit",
  "confidence": 0.9,
  "slots": {{}},
  "needsClarification": false
}}

天气映射：晴天→晴, 阴天→阴, 下雨→小雨, 暴雨→大雨, 晚上→20:00, 傍晚→18:00
模板映射：滨水/河岸→1, 商业街→2, 校园→4, 住宅→8
只输出 JSON，不要额外文字。"""


def parse_command(text: str, modalities: list[str], attachment_names: list[str], image_base64: str | None = None) -> dict:
    """Parse user instruction into a function plan.

    - 'screenshot' modality → GLM-4V-Flash analyses the image
    - 'text' modality → DeepSeek API or local parser
    Returns dict with keys: plan, explanation, intentTag, confidence, slots, needsClarification.
    """
    # Screenshot modality: send image to GLM-4V-Flash
    if "screenshot" in modalities and image_base64:
        zhipu_key = os.environ.get("ZHIPU_API_KEY", "")
        if zhipu_key:
            result = _analyze_screenshot(image_base64, text, zhipu_key)
            if result:
                return result

    # Text modality: DeepSeek API or fallback
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if api_key:
        result = _call_llm(text, api_key)
        if result:
            return result

    return _parse_local(text, modalities, attachment_names)


def _analyze_screenshot(image_base64: str, user_text: str, api_key: str) -> dict | None:
    """Send screenshot to GLM-4V-Flash for visual analysis."""
    payload = json.dumps({
        "model": ZHIPU_VISION_MODEL,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    {"type": "text", "text": user_text or "请分析这张城市场景截图，描述你看到的道路、建筑、环境等要素，并生成对应的优化建议。"},
                ],
            },
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode("utf-8")

    req = urllib.request.Request(
        ZHIPU_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception as e:
        print(f"[vision] GLM-4V call failed: {e}")
        return None


VISION_SYSTEM_PROMPT = f"""你是智能城市生成系统的 AI 助手。分析用户上传的城市场景截图，根据图像内容生成函数调用 JSON。

可用函数：
{json.dumps(FUNCTION_LIST, ensure_ascii=False, indent=2)}

输出纯 JSON（不要 markdown）：
{{
  "plan": [
    {{"id": "node-1", "funcName": "set_street_width", "title": "调整道路宽度", "params": {{"width": 8}}}}
  ],
  "explanation": "从截图中观察到了...",
  "intentTag": "screenshot_analysis",
  "confidence": 0.8,
  "slots": {{}},
  "needsClarification": false
}}

观察要点：道路宽度、车道数、建筑高度、树木密度、天气时间、路灯状态。只输出 JSON。"""


def _call_llm(text: str, api_key: str) -> dict | None:
    """Try calling DeepSeek API."""
    payload = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        DEFAULT_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "SmartCityBackend/1.0",
        },
        method="POST",
    )

    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return _extract_json(content)
    except Exception:
        # Try curl as fallback
        return _call_via_curl(text, api_key)


def _call_via_curl(text: str, api_key: str) -> dict | None:
    """Use system curl as fallback for network issues."""
    import subprocess
    payload = json.dumps({
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
    })
    try:
        result = subprocess.run(
            ["curl", "-s", DEFAULT_API_URL,
             "-H", "Content-Type: application/json",
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "User-Agent: SmartCityBackend/1.0",
             "-d", payload, "--max-time", "30"],
            capture_output=True, text=True, timeout=35,
        )
        if result.returncode == 0 and result.stdout.strip():
            body = json.loads(result.stdout)
            content = body["choices"][0]["message"]["content"]
            return _extract_json(content)
    except Exception:
        pass
    return None


def _extract_json(raw: str) -> dict:
    """Extract JSON from LLM response."""
    m = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', raw)
    if m:
        raw = m.group(1)
    start, end = raw.find('{'), raw.rfind('}')
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return json.loads(raw)


def _parse_local(text: str, modalities: list[str], attachment_names: list[str]) -> dict:
    """Local keyword parser — same logic as the Blender plugin's parse_local()."""
    plan = []
    node_id = 0

    tm = {
        "滨水":1,"河岸":1,"商业街":2,"步行街":2,"枢纽":3,"换乘":3,
        "校园":4,"学校":4,"公园":5,"生态":5,"科技":6,"住宅":8,"小区":8,"工业":9,
    }
    for kw, tid in tm.items():
        if kw in text:
            node_id += 1
            plan.append({"id":f"node-{node_id}","funcName":"apply_template_linkage",
                         "title":f"应用模板{tid}","params":{"template_id":tid,"tree_density":70,"road_width":8},
                         "dependsOn":[],"status":"approved"})
            break

    weather = ""
    for kw, w in {"晴天":"晴","阴天":"阴","小雨":"小雨","下雨":"小雨","大雨":"大雨","雪":"雪"}.items():
        if kw in text:
            weather = w
            break
    time_str = ""
    for kw, t in {"早上":"08:00","上午":"10:00","中午":"12:00","下午":"14:00","傍晚":"18:00","晚上":"20:00"}.items():
        if kw in text:
            time_str = t
            break
    if weather or time_str:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_weather_lighting","title":"设置天气",
                     "params":{"weather":weather or "晴","time_of_day":time_str or "12:00"},
                     "dependsOn":[],"status":"approved"})

    m = re.search(r"道路宽度?.*?(\d+)", text)
    if m:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_street_width","title":"设置道路宽度",
                     "params":{"width":int(m.group(1))},"dependsOn":[],"status":"approved"})

    m = re.search(r"(\d+)\s*车道", text) or re.search(r"车道.*?(\d+)", text)
    if m:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_lane_amount","title":"设置车道",
                     "params":{"lanes":int(m.group(1))},"dependsOn":[],"status":"approved"})

    m = re.search(r"树木?密度?.*?([\d.]+)", text)
    if m:
        node_id += 1
        val = float(m.group(1))
        plan.append({"id":f"node-{node_id}","funcName":"set_tree_density","title":"设置树木密度",
                     "params":{"density":val/100 if val>1 else val},"dependsOn":[],"status":"approved"})

    if "路灯" in text:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_street_lights","title":"开关路灯",
                     "params":{"enable":not("关" in text)},"dependsOn":[],"status":"approved"})

    m = re.search(r"建筑.*?高.*?(\d+)", text)
    if m:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_building_height","title":"设置建筑高度",
                     "params":{"height":int(m.group(1))},"dependsOn":[],"status":"approved"})
    elif "降低建筑" in text or "减少建筑" in text:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_building_height","title":"降低建筑高度",
                     "params":{"height":3},"dependsOn":[],"status":"approved"})
    elif "增加建筑" in text or "提高建筑" in text:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"set_building_height","title":"增加建筑高度",
                     "params":{"height":30},"dependsOn":[],"status":"approved"})

    if "关闭交通" in text or "禁用交通" in text:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"toggle_traffic","title":"关闭交通",
                     "params":{"enable":False},"dependsOn":[],"status":"approved"})

    if "关闭建筑" in text:
        node_id += 1
        plan.append({"id":f"node-{node_id}","funcName":"toggle_buildings","title":"关闭建筑",
                     "params":{"enable":False},"dependsOn":[],"status":"approved"})

    if "仿真" in text or "模拟" in text:
        if "人群" in text or "行人" in text:
            node_id += 1
            plan.append({"id":f"node-{node_id}","funcName":"run_crowd_simulation","title":"人群仿真",
                         "params":{"rules_version":"crowd-r2.8","seed":20260506,"agent_count":200},
                         "dependsOn":[],"status":"approved"})
        if "车辆" in text or "交通" in text:
            node_id += 1
            ver = "traffic-r3.2"
            m = _re.search(r"traffic-r[\d.]+", text) or _re.search(r"rules.*?([\d.]+)", text)
            if m:
                ver = m.group(0)
            plan.append({"id":f"node-{node_id}","funcName":"run_traffic_simulation","title":"车辆仿真",
                         "params":{"rules_version":ver,"seed":20260506},"dependsOn":[],"status":"approved"})

    return {
        "plan": plan,
        "explanation": f"本地解析完成，生成 {len(plan)} 个操作" if plan else "未识别出操作",
        "intentTag": "scene_edit",
        "confidence": 0.7 if plan else 0.3,
        "slots": {},
        "needsClarification": len(plan) == 0,
    }
