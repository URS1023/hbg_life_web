"""Small provider boundary used by jobs.

The local demo stays deterministic when no provider is configured. If an
OpenAI-compatible chat endpoint is configured, planning uses it and validates
the returned JSON before it reaches the project record.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEMO_BRIEF = {
    "logline": "一个普通人进入人生副本，在关键选择中重新认识自己。",
    "chapters": ["进入副本", "第一次选择", "代价与转折", "新的答案"],
}


def _configured() -> bool:
    return bool(os.getenv("HBG_TEXT_API_BASE") and os.getenv("HBG_TEXT_API_KEY"))


def _request_json(prompt: str) -> dict:
    base = os.environ["HBG_TEXT_API_BASE"].rstrip("/")
    endpoint = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    body = {
        "model": os.getenv("HBG_TEXT_MODEL", "gpt-4.1-mini"),
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "你是中文短视频编剧。只返回 JSON，字段必须是 logline(string) 和 chapters(string 数组，4 项)。"},
            {"role": "user", "content": prompt},
        ],
    }
    request = Request(endpoint, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['HBG_TEXT_API_KEY']}"}, method="POST")
    try:
        with urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"文本模型请求失败：{exc.__class__.__name__}") from exc
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("文本模型返回的规划不是有效 JSON") from exc
    if not isinstance(result.get("logline"), str) or not isinstance(result.get("chapters"), list) or len(result["chapters"]) != 4 or not all(isinstance(item, str) and item.strip() for item in result["chapters"]):
        raise RuntimeError("文本模型规划不符合 HBG 结构")
    return {"logline": result["logline"].strip(), "chapters": [item.strip() for item in result["chapters"]]}


def generate_plan(source_text: str, input_mode: str) -> tuple[dict, str]:
    if not _configured():
        return DEMO_BRIEF.copy(), "local-demo"
    prompt = f"创作入口：{input_mode}\n用户输入：{source_text}\n请保留明确的用户剧情意图，并输出四个递进章节。"
    return _request_json(prompt), "configured-provider"
