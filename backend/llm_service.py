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

# Zhipu GLM-4V multimodal visual model (for screenshot analysis)
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_VISION_MODEL = "glm-4v"  # higher quality than glm-4v-flash

# Qwen (DashScope) multimodal model — best for road topology extraction
QWEN_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
QWEN_VISION_MODEL = "qwen3.6-flash"

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
    # Member A
    {"name": "apply_scene_template", "params": {"template_id": "int 0-2"}},
    {"name": "apply_road_texture", "params": {"texture_id": "int"}},
    {"name": "apply_pavement_texture", "params": {"texture_id": "int"}},
    {"name": "delete_furniture", "params": {"asset_id": "string"}},
    {"name": "place_furniture", "params": {"asset_id": "string", "min_count": "int", "max_count": "int", "spacing": "number", "scale": "number", "randomize": "bool", "placement_offset": "number", "clear_previous": "bool"}},
    {"name": "apply_layout_template", "params": {"layout_id": "int", "rows": "int", "columns": "int"}},
    # Member C
    {"name": "generate_terrain", "params": {"hill_height": "number", "noise_scale": "number"}},
    {"name": "generate_lake", "params": {"lake_size": "number", "ripple_strength": "number"}},
    {"name": "generate_river", "params": {"river_width": "number", "seed": "int"}},
    {"name": "add_boat", "params": {"boat_scale": "number", "flow_speed": "number"}},
    # Member D
    {"name": "start_simulation", "params": {"car_density": "number", "pedestrian_density": "number"}},
    {"name": "stop_simulation", "params": {}},
    {"name": "apply_layout", "params": {"points": "array"}},
    {"name": "sketch_layout", "params": {"image_path": "string", "threshold": "int"}},
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

    - sketch → analyze road sketch → return apply_layout params
    - screenshot → analyze city scene → return function calls
    - text → LLM/keyword parse → return function calls
    """
    has_sketch = "sketch" in modalities and image_base64
    has_screenshot = "screenshot" in modalities and image_base64
    has_text = text.strip() and len(text.strip()) >= 2

    # ── Sketch: analyze road topology → apply_layout ──
    if has_sketch:
        sketch_result = analyze_sketch(image_base64)
        pts = sketch_result.get("points_text", "")
        conns = sketch_result.get("connections_text", "")
        faces = sketch_result.get("faces_text", "")
        if pts:
            return {
                "plan": [{
                    "id": "node-1",
                    "funcName": "apply_layout",
                    "title": "应用草图道路布局",
                    "params": {
                        "points": pts,
                        "connections": conns,
                        "faces": faces,
                    },
                    "dependsOn": [],
                    "status": "approved",
                }],
                "explanation": f"草图识别完成: {sketch_result.get('message', '')}",
                "intentTag": "sketch_layout",
                "confidence": 0.85,
                "slots": {"points_count": pts.count(";") + 1},
                "needsClarification": False,
            }
        return {
            "plan": [],
            "explanation": sketch_result.get("message", "草图识别失败"),
            "intentTag": "sketch_layout",
            "confidence": 0,
            "slots": {},
            "needsClarification": True,
        }

    # ── Screenshot / Text paths ──
    text_result = None
    screenshot_result = None

    if has_screenshot:
        zhipu_key = os.environ.get("ZHIPU_API_KEY", "")
        if zhipu_key:
            instruction = text if not has_text else "请独立分析这张城市场景截图。你的任务是让Blender城市贴近截图：截图里有什么就设置什么，截图里没有的不要额外添加。观察道路宽度、车道数、建筑高度、树木密度、天气时间、路灯、3D家具（野餐椅/小消防罐/小黄鸭）、地形湖泊河流、车辆行人，估算参数值并生成函数调用。"
            screenshot_result = _analyze_screenshot(image_base64, instruction, zhipu_key)

    if has_text:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if api_key:
            text_result = _call_llm(text, api_key)
        if not text_result:
            text_result = _parse_local(text, modalities, attachment_names)

    if text_result and screenshot_result:
        return _merge_plans(text_result, screenshot_result)
    elif screenshot_result:
        return screenshot_result
    elif text_result:
        return text_result

    return _parse_local(text, modalities, attachment_names) if has_text else {
        "plan": [],
        "explanation": "未能分析指令，请提供文本或截图。",
        "intentTag": "unknown",
        "confidence": 0,
        "slots": {},
        "needsClarification": True,
    }


def _merge_plans(text_plan: dict, screenshot_plan: dict) -> dict:
    """Merge two plans: text takes priority on conflict, screenshot adds new.
    Re-numbers node IDs to avoid React duplicate-key warnings."""
    text_nodes = {n.get("funcName"): n for n in text_plan.get("plan", [])}
    screenshot_nodes = {n.get("funcName"): n for n in screenshot_plan.get("plan", [])}

    # Start with screenshot nodes, then override/add with text
    merged = dict(screenshot_nodes)
    merged.update(text_nodes)  # text wins on conflict

    # Re-number IDs to avoid duplicates
    plan = []
    for i, node in enumerate(merged.values(), 1):
        plan.append({**node, "id": f"node-{i}"})

    return {
        "plan": plan,
        "explanation": f"[文本] {text_plan.get('explanation', '')}\n[截图] {screenshot_plan.get('explanation', '')}",
        "intentTag": text_plan.get("intentTag", screenshot_plan.get("intentTag", "merged")),
        "confidence": max(text_plan.get("confidence", 0), screenshot_plan.get("confidence", 0)),
        "slots": {**screenshot_plan.get("slots", {}), **text_plan.get("slots", {})},
        "needsClarification": False,
    }


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


VISION_SYSTEM_PROMPT = f"""你是智能城市生成系统的 AI 助手。用户的截图展示了一个期望的城市场景。你的任务是分析截图中的要素，生成函数调用让 Blender 中的城市尽量贴近截图。

## 核心原则：复制截图中有的，不额外添加截图中没有的

## 可用函数（共 28 个，必须从中选择）

{json.dumps(FUNCTION_LIST, ensure_ascii=False, indent=2)}

## 分析步骤

1. **先观察截图中有哪些要素**，再决定调用哪些函数
2. **只调用截图中有对应依据的函数**——截图里没有湖泊就不要生成湖泊，没有山丘就不要生成山丘
3. 参数值应该根据截图中的视觉特征估算，尽量贴近截图

## 对照表

| 截图特征 | 调用的函数 | 参数估算 |
|---------|-----------|---------|
| 道路看起来宽/窄 | set_street_width | 宽≈15m, 中≈10m, 窄≈6m |
| 可见车道线数量 | set_lane_amount | 数车道线 |
| 路边有停车 | set_parking_probability | 0.6-1.0 |
| 路口圆角大/小 | set_corner_radius | 大≈5m, 小≈1m |
| 建筑高/矮 | set_building_height | 高≈30m, 矮≈5m |
| 树木密集/稀疏 | set_tree_density | 密≈0.9, 疏≈0.2 |
| 晴天/阴天/雨天/傍晚 | set_weather_lighting | 直接映射 |
| 路灯亮/灭 | set_street_lights | 亮=true, 灭=false |
| 有车辆行人 | start_simulation | car_density根据车流量 |
| 有垃圾桶 | place_furniture(asset_id="wooden_picnic_table") | count≈5-15 |
| 有长椅/桌子 | place_furniture(asset_id="wooden_picnic_table") | count≈5-10 |
| 有小黄鸭玩具 | place_furniture(asset_id="rubber_duck_toy") | count≈3-8 |
| 有燃气罐 | place_furniture(asset_id="small_lpg_tank") | count≈3-8 |
| 有山丘地形 | generate_terrain | hill_height根据起伏 |
| 有湖泊 | generate_lake | lake_size根据大小 |
| 有河流 | generate_river | river_width根据宽度 |
| 有船只 | add_boat | — |
| 滨水风格 | apply_scene_template(template_id=0) | — |
| 商业街风格 | apply_scene_template(template_id=1) | — |
| 交通枢纽风格 | apply_scene_template(template_id=2) | — |

## 输出格式

纯 JSON（不要 markdown）：
{{
  "plan": [
    {{"id": "node-1", "funcName": "set_street_width", "title": "截图道路约6m", "params": {{"width": 6}}}},
    {{"id": "node-2", "funcName": "set_building_height", "title": "截图建筑约15m", "params": {{"height": 15}}}}
  ],
  "explanation": "截图中观察到：双向2车道约6m宽，建筑约5层15m高，树木稀疏...",
  "intentTag": "screenshot_analysis",
  "confidence": 0.8,
  "slots": {{}},
  "needsClarification": false
}}

只输出 JSON。"""


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


SKETCH_ANALYSIS_PROMPT = """分析手绘道路草图，输出分号分隔的文本参数。

## 输出格式（纯 JSON）
{"points":"x,y;x,y;...","connections":"i,j;i,j;...","faces":"a,b,c,d;a,b,c,d;..."}

## 图形识别

已闭合（原样提取）：
- 三角形 → 3点 1三角面。{"points":"100,160;0,0;200,0","connections":"0,1;1,2;2,0","faces":"0,1,2"}
- 日字形（2竖格）→ 6点 2面。{"points":"0,0;80,0;0,80;80,80;0,160;80,160","connections":"0,1;0,2;1,3;2,3;2,4;3,5;4,5","faces":"0,1,3,2;2,3,5,4"}
- 日字形（2横格）→ 6点 2面。{"points":"0,0;80,0;160,0;0,80;80,80;160,80","connections":"0,1;1,2;0,3;1,4;2,5;3,4;4,5","faces":"0,1,4,3;1,2,5,4"}
- 目字形（3竖格）→ 8点 3面。{"points":"0,0;80,0;0,50;80,50;0,100;80,100;0,150;80,150","connections":"0,1;0,2;1,3;2,3;2,4;3,5;4,5;4,6;5,7;6,7","faces":"0,1,3,2;2,3,5,4;4,5,7,6"}
- 田字形（4方格）→ 9点 4面。{"points":"0,0;80,0;160,0;0,80;80,80;160,80;0,160;80,160;160,160","connections":"0,1;1,2;0,3;1,4;2,5;3,4;4,5;3,6;4,7;5,8;6,7;7,8","faces":"0,1,4,3;1,2,5,4;3,4,7,6;4,5,8,7"}
- 一字型/单线 → 直接输出点集{"points":"0,0;80,0;160,0;0,80;80,80;160,80","connections":"0,1;1,2;0,3;1,4;2,5;3,4;4,5","faces":"0,1,4,3;1,2,5,4"}
- 十字/T形/L形 → 直接输出点集{"points":"0,0;80,0;160,0;0,80;80,80;160,80;0,160;80,160;160,160","connections":"0,1;1,2;0,3;1,4;2,5;3,4;4,5;3,6;4,7;5,8;6,7;7,8","faces":"0,1,4,3;1,2,5,4;3,4,7,6;4,5,8,7"}


"""





def analyze_sketch(image_base64: str, api_key: str | None = None) -> dict:
    """Analyze a hand-drawn road sketch via Qwen VL and return Points/Connections/Faces text.

    Returns:
        {"points_text": str, "connections_text": str, "faces_text": str, "message": str}
    """
    import os
    api_key = api_key or os.environ.get("QWEN_API_KEY", "")
    if not api_key:
        return {"points_text": "", "connections_text": "", "faces_text": "", "message": "未设置 QWEN_API_KEY"}

    payload = json.dumps({
        "model": QWEN_VISION_MODEL,
        "messages": [
            {"role": "system", "content": SKETCH_ANALYSIS_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    {"type": "text", "text": "请分析这张道路草图"},
                ],
            },
        ],
        "max_tokens": 4096,
    }).encode("utf-8")

    req = urllib.request.Request(
        QWEN_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        result = _extract_json(content)
        pts = result.get("points", "")
        conns = result.get("connections", "")
        faces = result.get("faces", "")
        if not pts:
            return {"points_text": "", "connections_text": "", "faces_text": "", "message": "模型未能识别出道路结构"}
        return {
            "points_text": pts,
            "connections_text": conns,
            "faces_text": faces,
            "message": "识别成功",
        }
    except Exception as e:
        return {"points_text": "", "connections_text": "", "faces_text": "", "message": f"草图分析失败: {str(e)}"}


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
