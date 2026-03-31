"""
app/services/translator.py
─────────────────────────
中文 → 英文 / 繁体的统一翻译服务

用途：
  - AI 解析时生成 content_zh、tags 后，同步生成 content_en、content_tw、tags_en、tags_tw
  - 历史数据迁移：批量翻译已有中文内容
  - 通过 Ollama 本地模型翻译，无外网依赖
"""
from __future__ import annotations

import os
import json
import re
import logging
import httpx
from typing import List, Optional

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("MAC_IP", "YOUR_MAC_IP")
OLLAMA_BASE = f"http://{OLLAMA_URL}:11434"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL_NAME", "deepseek-r1:32b")
TIMEOUT = 180  # 32B 模型推理较慢，精算辣评翻译适当放宽


def _call_ollama(prompt: str) -> Optional[str]:
    """调用 Ollama 生成，返回纯文本"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "")
            # 去掉 <think>...</think>
            cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.DOTALL).strip()
            return cleaned.strip()
    except Exception as e:
        logger.warning(f"翻译服务调用失败: {e}")
        return None


def translate_text(zh_text: str, target: str = "en") -> Optional[str]:
    """
    单条中文文本翻译
    target: "en" 英文 | "hk" 繁体中文
    """
    if not zh_text or not zh_text.strip():
        return None
    lang_name = "英文" if target == "en" else "繁体中文（香港）"
    prompt = f"""将以下中文翻译成{lang_name}。只输出译文，不要任何解释、引号或标记。

原文：{zh_text}"""
    result = _call_ollama(prompt)
    return result if result and len(result) < len(zh_text) * 3 else result


def translate_tags(zh_tags: List[str], target: str = "en") -> List[str]:
    """
    批量标签翻译。保持顺序，翻译失败则保留原文
    """
    if not zh_tags:
        return []
    if target == "cn" or target == "zh":
        return zh_tags
    out = []
    for t in zh_tags:
        if not t or not isinstance(t, str):
            continue
        # 纯英文/数字可跳过
        if not any("\u4e00" <= c <= "\u9fff" for c in t):
            out.append(t)
            continue
        tr = translate_text(t, target)
        out.append(tr if tr else t)
    return out


def tags_to_i18n(zh_tags: List[str]) -> List[dict]:
    """
    将纯中文标签数组转为多语言格式
    返回 [{"zh":"x","en":"y","hk":"z"}, ...]
    """
    if not zh_tags:
        return []
    en_tags = translate_tags(zh_tags, "en")
    hk_tags = translate_tags(zh_tags, "hk")
    return [
        {
            "zh": zh_tags[i] if i < len(zh_tags) else "",
            "en": en_tags[i] if i < len(en_tags) else zh_tags[i],
            "hk": hk_tags[i] if i < len(hk_tags) else zh_tags[i],
        }
        for i in range(len(zh_tags))
    ]
