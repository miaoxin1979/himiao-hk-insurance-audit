#!/usr/bin/env python3
"""
translate_content.py — 精算辣评三语补齐（Mac 本地跑）

从 DB 读出 content_zh 不为空、但 content_tw 或 content_en 为空的产品，
用 Ollama（deepseek-r1:32b）翻译后写回。
为安全：先写 /tmp/himiao_work.db，成功后再 cp 回原路径。

用法:
  python scripts/translate_content.py --db /Volumes/docker/himiao-data/db/himiao.db
  python scripts/translate_content.py --db /path/to/himiao.db --dry-run   # 只打日志不写回

依赖: pip install httpx
"""
from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("请先安装: pip install httpx")
    sys.exit(1)

OLLAMA_DEFAULT = "http://YOUR_MAC_IP:11434"
MODEL_DEFAULT = "deepseek-r1:32b"
TIMEOUT = 180
WORK_DB = "/tmp/himiao_work.db"


def call_ollama(url: str, model: str, prompt: str) -> str | None:
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(
                f"{url.rstrip('/')}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
            r.raise_for_status()
            raw = r.json().get("response", "")
            cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.DOTALL).strip()
            return cleaned.strip() or None
    except Exception as e:
        print(f"  [Ollama 调用失败] {e}")
        return None


def translate_to_tw(zh: str, url: str, model: str) -> str | None:
    prompt = f"""将以下简体中文精算/保险文案翻译成繁体中文（香港用语）。保持数字、百分比、年份不变，专业术语准确。只输出译文，不要解释。

原文：
{zh}"""
    return call_ollama(url, model, prompt)


def translate_to_en(zh: str, url: str, model: str) -> str | None:
    prompt = f"""Translate the following Chinese actuarial/insurance text into English. Keep a professional financial tone. Preserve numbers, percentages, and years. Output only the translation, no explanation.

Original:
{zh}"""
    return call_ollama(url, model, prompt)


def main() -> None:
    p = argparse.ArgumentParser(description="精算辣评 content_zh → content_tw / content_en 补齐")
    p.add_argument("--db", default="/Volumes/docker/himiao-data/db/himiao.db", help="SQLite 库路径")
    p.add_argument("--ollama", default=OLLAMA_DEFAULT, help=f"Ollama 地址，默认 {OLLAMA_DEFAULT}")
    p.add_argument("--model", default=MODEL_DEFAULT, help=f"模型名，默认 {MODEL_DEFAULT}")
    p.add_argument("--dry-run", action="store_true", help="只翻译并打日志，不写回 DB")
    args = p.parse_args()

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"错误: 数据库不存在 {db_path}")
        sys.exit(1)

    print(f"复制 DB → {WORK_DB}")
    shutil.copy2(db_path, WORK_DB)

    conn = sqlite3.connect(WORK_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, slug, content_zh, content_tw, content_en
        FROM products
        WHERE content_zh IS NOT NULL AND trim(content_zh) != ''
          AND (content_tw IS NULL OR trim(content_tw) = '' OR content_en IS NULL OR trim(content_en) = '')
        ORDER BY id
    """)
    rows = cur.fetchall()
    total = len(rows)
    if total == 0:
        print("没有需要补齐的产品，退出。")
        conn.close()
        return

    print(f"共 {total} 个产品待翻译（Ollama {args.ollama} / {args.model}）\n")

    for i, row in enumerate(rows, 1):
        pid = row["id"]
        slug = row["slug"] or f"id={pid}"
        zh = (row["content_zh"] or "").strip()
        tw = (row["content_tw"] or "").strip()
        en = (row["content_en"] or "").strip()

        need_tw = not tw
        need_en = not en
        new_tw = tw
        new_en = en

        if need_tw:
            new_tw = translate_to_tw(zh, args.ollama, args.model)
            if new_tw is None:
                new_tw = tw  # 保留原值
        if need_en:
            new_en = translate_to_en(zh, args.ollama, args.model)
            if new_en is None:
                new_en = en

        status = []
        if need_tw: status.append("tw=ok" if new_tw else "tw=fail")
        if need_en: status.append("en=ok" if new_en else "en=fail")
        print(f"[{i}/{total}] {slug} {' '.join(status)}")

        if not args.dry_run and (new_tw != tw or new_en != en):
            cur.execute(
                "UPDATE products SET content_tw = ?, content_en = ?, updated_at = current_timestamp WHERE id = ?",
                (new_tw or tw, new_en or en, pid),
            )

    if not args.dry_run and total > 0:
        conn.commit()
        print(f"\n写回原库: cp {WORK_DB} {db_path}")
        shutil.copy2(WORK_DB, db_path)
        print("完成。若 API 使用同一 DB 卷，无需重启容器；否则请重启 himiao-api。")
    else:
        print("\n[dry-run] 未写回 DB。去掉 --dry-run 执行正式写入。")

    conn.close()


if __name__ == "__main__":
    main()
