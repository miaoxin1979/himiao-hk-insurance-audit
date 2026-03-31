# scraper/pipelines/translation.py
import os
import requests
import logging
import re

logger = logging.getLogger(__name__)

class TranslationPipeline:
    def __init__(self):
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434/v1")
        self.model_name = os.environ.get("OLLAMA_MODEL_NAME", "deepseek-r1:32b")
        if self.ollama_host.endswith("/v1"):
            self.api_url = f"{self.ollama_host}/chat/completions"
        else:
            self.api_url = f"{self.ollama_host}/api/chat"
            
    def process_item(self, item, spider):
        from scraper.items import NewsArticleItem
        if isinstance(item, NewsArticleItem):
            title = item.get("title_zh") or item.get("title_zh")
            content = item.get("content_zh") or item.get("content_zh")
            
            # 翻译标题
            if title and not item.get("title_en"):
                item["title_en"] = self.translate(title, "English")
                logger.info("Translated title to English")
            if title and not item.get("title_tw"):
                item["title_tw"] = self.translate(title, "Traditional Chinese (zh-TW)")
                logger.info("Translated title to Traditional Chinese")
                
            # 翻译内容
            if content and not item.get("content_en"):
                item["content_en"] = self.translate(content, "English")
                logger.info("Translated content to English")
            if content and not item.get("content_tw"):
                item["content_tw"] = self.translate(content, "Traditional Chinese (zh-TW)")
                logger.info("Translated content to Traditional Chinese")
            
            # 标准化中文字段，以兼容旧结构
            item["title_zh"] = title
            item["content_zh"] = content
        
        return item
        
    def translate(self, text, target_lang):
        prompt = f"Please translate the following text into {target_lang}. Reply ONLY with the translated text without any explanation, markdown formatting, or <think> tags. Just the raw translation.\n\nText:\n{text}"
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        try:
            res = requests.post(self.api_url, json=payload, timeout=60)
            res.raise_for_status()
            data = res.json()
            if "choices" in data:
                reply = data["choices"][0]["message"]["content"]
            else:
                reply = data.get("message", {}).get("content", "")
            
            # 过滤 DeepSeek 可能产生的 <think>...</think>
            reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
            return reply
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
