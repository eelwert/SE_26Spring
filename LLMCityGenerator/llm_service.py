"""LLM service for natural language → Blender function calls.

Uses DeepSeek API (OpenAI-compatible) to convert user's natural language
instructions into structured function call JSON.
"""

import json
import re
import subprocess

from .function_registry import get_registry_for_prompt, FUNCTION_REGISTRY

DEFAULT_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

SYSTEM_PROMPT_TEMPLATE = """你是智能城市生成系统的AI助手。你的任务是将用户的自然语言指令转换为结构化的函数调用JSON。

## 可用函数

{function_list}

## 输出格式

你必须只返回一个JSON对象，格式如下：

```json
{{
  "functions": [
    {{"name": "函数名", "params": {{"参数名": 参数值}}}}
  ],
  "explanation": "用中文简要解释你做了什么配置"
}}
```

## 规则

1. 只使用上面列出的函数名
2. 参数名必须与函数定义完全一致
3. 必填参数（标记*）必须提供
4. 如果用户的指令可以映射到多个函数，返回多个函数调用
5. 如果用户指令无法映射到任何函数，返回空的functions数组并在explanation中说明
6. 天气相关的关键词映射：晴天→晴, 阴天→阴, 下雨/雨天→小雨, 暴雨→大雨, 下雪→雪
7. 时间相关：早上→08:00, 上午→10:00, 中午→12:00, 下午→14:00, 傍晚→18:00, 晚上→20:00, 深夜→23:00
8. 模板关键词映射：滨水/河岸→1, 商业街/步行街→2, 交通枢纽/换乘→3, 校园/学校→4, 公园/生态→5, 科技/园区→6, 历史/古城→7, 住宅/小区→8, 工业/物流→9

## 示例

用户: "把道路宽度调到12米，增加车道到6条"
输出:
```json
{{
  "functions": [
    {{"name": "set_street_width", "params": {{"width": 12}}}},
    {{"name": "set_lane_amount", "params": {{"lanes": 6}}}}
  ],
  "explanation": "已将道路宽度调整为12米，车道数量增加到6条"
}}
```

用户: "切换成滨水商业街区，树木多一些，傍晚小雨天气"
输出:
```json
{{
  "functions": [
    {{"name": "apply_template_linkage", "params": {{"template_id": 1, "tree_density": 80, "road_width": 8}}}},
    {{"name": "set_weather_lighting", "params": {{"weather": "小雨", "time_of_day": "18:00"}}}}
  ],
  "explanation": "已应用滨水活力街区模板，树木密度设为80%，天气切换为傍晚小雨"
}}
```"""


def _build_system_prompt():
    """Build the system prompt from the function registry."""
    func_list = get_registry_for_prompt()
    return SYSTEM_PROMPT_TEMPLATE.format(function_list=func_list)


def _extract_json(text):
    """Extract JSON from LLM response, handling markdown code blocks."""
    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
    if json_match:
        text = json_match.group(1)

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    text = text.strip()
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)

    return json.loads(text)


def call_llm(user_text, api_key, api_url=None, model=None):
    """Send user text to LLM via curl and get parsed function calls.
    Uses curl to bypass Blender's firewall-blocked Python network stack.
    """
    api_url = api_url or DEFAULT_API_URL
    model = model or DEFAULT_MODEL
    system_prompt = _build_system_prompt()

    payload_str = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"},
    })

    try:
        result = subprocess.run(
            ["curl", "-s", api_url,
             "-H", "Content-Type: application/json",
             "-H", f"Authorization: Bearer {api_key}",
             "-H", "User-Agent: LLMCityGenerator/1.0",
             "-d", payload_str,
             "--connect-timeout", "15", "--max-time", "45"],
            capture_output=True, text=True, timeout=50, shell=True,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return {
                "functions": [],
                "explanation": f"curl 请求失败 (code {result.returncode})",
                "raw_response": result.stderr[:200] if result.stderr else "",
                "success": False,
            }
        body = json.loads(result.stdout)
    except Exception as e:
        return {
            "functions": [],
            "explanation": f"网络错误: {str(e)}",
            "raw_response": "",
            "success": False,
        }

    content = body["choices"][0]["message"]["content"]

    try:
        parsed = _extract_json(content)
        functions = parsed.get("functions", [])
        explanation = parsed.get("explanation", "")

        valid_functions = []
        for func in functions:
            name = func.get("name", "")
            if name in FUNCTION_REGISTRY:
                valid_functions.append(func)
            else:
                valid_functions.append({
                    "name": name,
                    "params": func.get("params", {}),
                    "_skipped": True,
                    "_reason": f"函数 '{name}' 未在注册表中找到",
                })
        return {
            "functions": valid_functions,
            "explanation": explanation,
            "raw_response": content,
            "success": True,
        }
    except json.JSONDecodeError as e:
        return {
            "functions": [],
            "explanation": f"JSON 解析失败: {str(e)}",
            "raw_response": content,
            "success": False,
        }


def call_llm_with_retry(user_text, api_key, max_retries=2, api_url=None, model=None):
    """Call LLM with retry on failure."""
    result = call_llm(user_text, api_key, api_url, model)
    if result["success"] and result["functions"]:
        return result

    if not result["success"]:
        for i in range(max_retries):
            result = call_llm(user_text, api_key, api_url, model)
            if result["success"]:
                break

    return result


def parse_local(user_text):
    """Local keyword-based parser as fallback when LLM API is unavailable.

    Parses simple Chinese natural language commands into function calls.
    """
    functions = []
    text = user_text

    # --- Template matching ---
    template_map = {
        "滨水": 1, "河岸": 1, "水岸": 1,
        "商业街": 2, "步行街": 2, "商业": 2,
        "枢纽": 3, "换乘": 3, "交通": 3, "公交": 3,
        "校园": 4, "学校": 4, "大学": 4,
        "公园": 5, "生态": 5, "绿地": 5, "绿化": 5,
        "科技": 6, "园区": 6, "产业园": 6,
        "历史": 7, "古城": 7, "古街": 7,
        "住宅": 8, "小区": 8, "社区": 8, "居住": 8,
        "工业": 9, "物流": 9, "工厂": 9,
    }
    for keyword, tid in template_map.items():
        if keyword in text:
            functions.append({"name": "apply_template_linkage", "params": {"template_id": tid, "tree_density": 70, "road_width": 8}})
            break

    # --- Weather matching ---
    weather_map = {
        "晴天": "晴", "晴天": "晴",
        "阴天": "阴", "阴": "阴",
        "小雨": "小雨", "下雨": "小雨", "雨天": "小雨",
        "大雨": "大雨", "暴雨": "大雨",
        "下雪": "雪", "雪": "雪",
        "多云": "多云",
    }
    time_map = {
        "早上": "08:00", "早晨": "07:00",
        "上午": "10:00",
        "中午": "12:00", "正午": "12:00",
        "下午": "14:00",
        "傍晚": "18:00", "黄昏": "18:00",
        "晚上": "20:00", "夜晚": "20:00", "夜间": "20:00",
        "深夜": "23:00",
    }
    weather = ""
    time_str = ""
    for kw, w in weather_map.items():
        if kw in text:
            weather = w
            break
    for kw, t in time_map.items():
        if kw in text:
            time_str = t
            break
    if weather or time_str:
        if not weather:
            weather = "晴"
        if not time_str:
            time_str = "12:00"
        functions.append({"name": "set_weather_lighting", "params": {"weather": weather, "time_of_day": time_str}})

    # --- Road width ---
    import re as _re
    m = _re.search(r"道路宽度?.*?(\d+)\s*米", text)
    if not m:
        m = _re.search(r"路宽.*?(\d+)", text)
    if m:
        functions.append({"name": "set_street_width", "params": {"width": float(m.group(1))}})

    # --- Lane amount ---
    m = _re.search(r"车道.*?(\d+)", text)
    if m:
        functions.append({"name": "set_lane_amount", "params": {"lanes": int(m.group(1))}})

    # --- Tree density ---
    m = _re.search(r"树木?密度?.*?([\d.]+)", text)
    if not m:
        m = _re.search(r"树木?.*?密度.*?([\d.]+)", text)
    if not m:
        m = _re.search(r"密度.*?([\d.]+)", text)
    if m:
        val = float(m.group(1))
        if val > 1:
            val = val / 100.0
        functions.append({"name": "set_tree_density", "params": {"density": val}})

    # --- Corner radius ---
    m = _re.search(r"圆角.*?(\d+)", text)
    if not m:
        m = _re.search(r"路口.*?半径.*?(\d+)", text)
    if m:
        functions.append({"name": "set_corner_radius", "params": {"radius": float(m.group(1))}})

    # --- Parking probability ---
    if "停车" in text:
        m = _re.search(r"停车.*?([\d.]+)", text)
        prob = float(m.group(1)) if m else 0.5
        functions.append({"name": "set_parking_probability", "params": {"probability": prob}})

    # --- Street lights ---
    if "路灯" in text:
        enable = not ("关闭" in text or "关" in text)
        functions.append({"name": "set_street_lights", "params": {"enable": enable}})

    # --- Traffic lights ---
    if "交通灯" in text or "红绿灯" in text:
        m = _re.search(r"(?:交通灯|红绿灯).*?([\d.]+)", text)
        prob = float(m.group(1)) if m else 0.6
        functions.append({"name": "set_traffic_lights", "params": {"probability": prob}})

    # --- Building height ---
    m = _re.search(r"建筑.*?高.*?(\d+)", text)
    if not m:
        m = _re.search(r"楼.*?高.*?(\d+)", text)
    if m:
        functions.append({"name": "set_building_height", "params": {"height": int(m.group(1))}})
    elif "降低建筑" in text or "减少建筑" in text or "建筑降低" in text or "建筑减少" in text:
        functions.append({"name": "set_building_height", "params": {"height": 3}})
    elif "增加建筑" in text or "提高建筑" in text or "建筑增加" in text or "建筑提高" in text:
        functions.append({"name": "set_building_height", "params": {"height": 30}})

    # --- Toggle traffic ---
    if "关闭交通" in text or "禁用交通" in text or "没有交通" in text:
        functions.append({"name": "toggle_traffic", "params": {"enable": False}})
    elif "开启交通" in text or "启用交通" in text:
        functions.append({"name": "toggle_traffic", "params": {"enable": True}})

    # --- Toggle buildings ---
    if "关闭建筑" in text or "隐藏建筑" in text:
        functions.append({"name": "toggle_buildings", "params": {"enable": False}})
    elif "显示建筑" in text:
        functions.append({"name": "toggle_buildings", "params": {"enable": True}})

    # --- Seed ---
    m = _re.search(r"种子.*?(\d+)", text)
    if m:
        functions.append({"name": "set_seed", "params": {"seed": float(m.group(1))}})

    # --- Sidewalk scale ---
    m = _re.search(r"人行道.*?([\d.]+)", text)
    if m:
        functions.append({"name": "set_sidewalk_scale", "params": {"scale": float(m.group(1))}})

    explanation = f"本地解析完成，识别到 {len(functions)} 个操作"
    if not functions:
        explanation = "未能从指令中识别出可执行的操作，请尝试更明确的描述。\n支持的关键词：道路宽度、车道、树木密度、模板（滨水/商业/校园/住宅等）、天气、时间、路灯、建筑高度等"

    return {
        "functions": functions,
        "explanation": explanation,
        "raw_response": "[local]",
        "success": True,
    }
