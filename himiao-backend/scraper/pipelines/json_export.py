# scraper/pipelines/json_export.py
"""
JSON 导出 Pipeline：
  1. 将爬取结果备份为 JSON 文件（/data/scraper_output/）
  2. 触发 PDF 下载 + OCR 提取流程
"""
import json
import logging
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from scraper.items import InsuranceProductItem, NewsArticleItem, PDFDocumentItem

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.getenv("SCRAPER_OUTPUT_DIR", "/data/scraper_output")
PDF_DIR    = os.getenv("SCRAPER_PDF_DIR",    "/data/scraper_pdfs")


class JsonExportPipeline:

    def open_spider(self, spider):
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(PDF_DIR).mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._products_file = open(f"{OUTPUT_DIR}/products_{ts}.jsonl", "w", encoding="utf-8")
        self._articles_file = open(f"{OUTPUT_DIR}/articles_{ts}.jsonl", "w", encoding="utf-8")
        self._pdf_queue = []

    def close_spider(self, spider):
        self._products_file.close()
        self._articles_file.close()
        # 处理 PDF 队列
        if self._pdf_queue:
            logger.info(f"Processing {len(self._pdf_queue)} PDFs...")
            self._process_pdf_queue()

    def process_item(self, item, spider):
        if isinstance(item, InsuranceProductItem):
            self._products_file.write(
                json.dumps(dict(item), ensure_ascii=False) + "\n"
            )
            self._products_file.flush()

            # 把 PDF 链接加入队列
            for pdf_url in (item.get("pdf_urls") or [])[:2]:
                self._pdf_queue.append({
                    "pdf_url":      pdf_url,
                    "insurer":      item.get("insurer"),
                    "product_name": item.get("product_name"),
                })

        elif isinstance(item, NewsArticleItem):
            self._articles_file.write(
                json.dumps(dict(item), ensure_ascii=False) + "\n"
            )
            self._articles_file.flush()

        elif isinstance(item, PDFDocumentItem):
            self._pdf_queue.append(dict(item))

        return item

    def _process_pdf_queue(self):
        """下载 PDF 并触发 OCR 提取"""
        from scraper.ocr.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()

        for task in self._pdf_queue:
            pdf_url  = task.get("pdf_url", "")
            insurer  = task.get("insurer", "unknown")
            name     = task.get("product_name", "unknown")

            if not pdf_url:
                continue

            # 安全文件名
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{insurer}_{name}")[:60]
            local_path = f"{PDF_DIR}/{safe_name}.pdf"

            try:
                # 下载 PDF
                logger.info(f"Downloading: {pdf_url}")
                resp = requests.get(pdf_url, timeout=30, headers={
                    "User-Agent": "Mozilla/5.0 HiMiao-Audit-Bot/1.0"
                })
                if resp.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"Downloaded: {local_path} ({len(resp.content)//1024}KB)")

                    # OCR 提取
                    result = extractor.extract(local_path)
                    result_path = local_path.replace(".pdf", "_ocr.json")
                    with open(result_path, "w", encoding="utf-8") as f:
                        f.write(extractor.to_json(result))
                    logger.info(
                        f"OCR done: confidence={result.confidence:.2f}, "
                        f"IRR20y={result.irr_20y}, breakeven={result.breakeven_year}"
                    )
                else:
                    logger.warning(f"PDF download failed {resp.status_code}: {pdf_url}")

            except Exception as e:
                logger.error(f"PDF processing error: {e} | {pdf_url}")
