# scraper/ocr/pdf_extractor.py
"""
保单 PDF 精算数据提取器
支持：
  1. pdfplumber — 文字层 PDF（计划书大多数）
  2. PaddleOCR  — 扫描版 PDF（图片型）
  3. 正则模式匹配关键精算指标
"""
import re
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ActuarialData:
    """从 PDF 中提取的精算核心指标"""
    product_name:     Optional[str]  = None
    insurer:          Optional[str]  = None
    currency:         Optional[str]  = None
    premium_years:    Optional[int]  = None
    irr_5y:           Optional[float] = None
    irr_10y:          Optional[float] = None
    irr_20y:          Optional[float] = None
    irr_30y:          Optional[float] = None
    breakeven_year:   Optional[int]  = None
    loan_ltv:         Optional[float] = None
    dividend_fulfillment: Optional[float] = None
    max_early_exit_loss_pct: Optional[float] = None
    # 时间轴锚点（年份 → GCV倍数）
    timeline_anchors: Optional[dict] = None
    source_pdf:       Optional[str]  = None
    extraction_method: str = "unknown"
    confidence:       float = 0.0


class PDFExtractor:
    """PDF 数据提取主类"""

    # ── IRR 正则模式 ──
    IRR_PATTERNS = [
        r"(?:IRR|内部回报率|内部收益率)[^\d]*(\d+\.?\d*)\s*%",
        r"(\d+\.?\d*)\s*%\s*(?:IRR|内部回报率)",
        r"年化回报率[^\d]*(\d+\.?\d*)\s*%",
        r"Annuali[sz]ed Return[^\d]*(\d+\.?\d*)\s*%",
    ]

    BREAKEVEN_PATTERNS = [
        r"(?:回本期|保证回本|Breakeven)[^\d]*第?\s*(\d+)\s*(?:年|Year)",
        r"第\s*(\d+)\s*保单年度.*?回本",
        r"Policy Year\s*(\d+).*?Breakeven",
    ]

    PREMIUM_YRS_PATTERNS = [
        r"(?:缴费期|供款年期|Premium Payment)[^\d]*(\d+)\s*(?:年|Year|Yr)",
        r"(\d+)[-\s]?年?供款",
        r"(\d+)[-\s]?Year Premium",
    ]

    CURRENCY_PATTERNS = {
        "USD": r"US\s*Dollar|美元|USD",
        "HKD": r"港元|港幣|HKD|HK Dollar",
        "CNY": r"人民币|CNY|RMB",
    }

    DIVIDEND_PATTERNS = [
        r"(?:红利实现率|分红实现率|Dividend Fulfillment)[^\d]*(\d+\.?\d*)\s*%",
        r"Fulfillment Ratio[^\d]*(\d+\.?\d*)\s*%",
        r"历史实现率[^\d]*(\d+\.?\d*)\s*%",
    ]

    # ── 年期 → IRR 映射关键词 ──
    YEAR_IRR_MAP = {
        5:  [r"5\s*年.*?(\d+\.?\d*)\s*%", r"Year\s*5.*?(\d+\.?\d*)\s*%"],
        10: [r"10\s*年.*?(\d+\.?\d*)\s*%", r"Year\s*10.*?(\d+\.?\d*)\s*%"],
        20: [r"20\s*年.*?(\d+\.?\d*)\s*%", r"Year\s*20.*?(\d+\.?\d*)\s*%"],
        30: [r"30\s*年.*?(\d+\.?\d*)\s*%", r"Year\s*30.*?(\d+\.?\d*)\s*%"],
    }

    def extract(self, pdf_path: str) -> ActuarialData:
        """主入口：自动选择最优提取方式"""
        path = Path(pdf_path)
        if not path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return ActuarialData(source_pdf=pdf_path)

        # 尝试 pdfplumber（文字层）
        data = self._try_pdfplumber(pdf_path)
        if data.confidence >= 0.5:
            return data

        # 降级到 PaddleOCR（扫描版）
        logger.info(f"Low confidence with pdfplumber ({data.confidence:.2f}), trying OCR: {path.name}")
        data_ocr = self._try_paddleocr(pdf_path)
        return data_ocr if data_ocr.confidence > data.confidence else data

    def _try_pdfplumber(self, pdf_path: str) -> ActuarialData:
        """用 pdfplumber 提取文字层 PDF"""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed: pip install pdfplumber")
            return ActuarialData(source_pdf=pdf_path)

        data = ActuarialData(source_pdf=pdf_path, extraction_method="pdfplumber")
        full_text = ""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:20]:  # 最多前20页
                    text = page.extract_text() or ""
                    full_text += text + "\n"

                    # 尝试提取表格数据（IRR 表通常在表格里）
                    for table in page.extract_tables():
                        full_text += self._table_to_text(table) + "\n"

            self._parse_text(full_text, data)

        except Exception as e:
            logger.error(f"pdfplumber error: {e}")

        return data

    def _try_paddleocr(self, pdf_path: str) -> ActuarialData:
        """用 PaddleOCR 识别扫描版 PDF（图片型）"""
        data = ActuarialData(source_pdf=pdf_path, extraction_method="paddleocr")

        try:
            import fitz  # PyMuPDF
            from paddleocr import PaddleOCR
        except ImportError:
            logger.warning("PyMuPDF or PaddleOCR not installed")
            return data

        try:
            ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            doc = fitz.open(pdf_path)
            full_text = ""

            # OCR 前5页（计划书核心数据通常在前几页）
            for page_num in range(min(5, len(doc))):
                page = doc[page_num]
                # 转为高分辨率图片
                mat = fitz.Matrix(2.0, 2.0)  # 2x 放大，提高 OCR 精度
                pix = page.get_pixmap(matrix=mat)
                img_path = f"/tmp/himiao_ocr_p{page_num}.png"
                pix.save(img_path)

                result = ocr.ocr(img_path, cls=True)
                if result and result[0]:
                    page_text = "\n".join([line[1][0] for line in result[0]])
                    full_text += page_text + "\n"

            doc.close()
            self._parse_text(full_text, data)

        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")

        return data

    def _parse_text(self, text: str, data: ActuarialData):
        """从文本中正则提取精算指标"""
        hits = 0
        total = 8  # 总指标数

        # 货币
        for currency, pattern in self.CURRENCY_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                data.currency = currency
                hits += 1
                break

        # 缴费年期
        for pattern in self.PREMIUM_YRS_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 30:
                    data.premium_years = val
                    hits += 1
                    break

        # 分年度 IRR
        for year, patterns in self.YEAR_IRR_MAP.items():
            for pattern in patterns:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if 0 < val < 20:  # 合理范围
                        setattr(data, f"irr_{year}y", val)
                        if year == 20:
                            hits += 1
                        break

        # 通用 IRR（兜底）
        if not data.irr_20y:
            for pattern in self.IRR_PATTERNS:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    val = float(m.group(1))
                    if 0 < val < 20:
                        data.irr_20y = val
                        hits += 1
                        break

        # 回本年
        for pattern in self.BREAKEVEN_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 30:
                    data.breakeven_year = val
                    hits += 1
                    break

        # 分红实现率
        for pattern in self.DIVIDEND_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                if 0 < val <= 200:
                    data.dividend_fulfillment = val
                    hits += 1
                    break

        # 贷款成数
        m = re.search(r"(?:贷款|Loan).*?(\d+)\s*%", text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            if 30 <= val <= 100:
                data.loan_ltv = val
                hits += 1

        # 置信度
        data.confidence = hits / total

        logger.info(
            f"Extracted {hits}/{total} fields, confidence={data.confidence:.2f} "
            f"| IRR20y={data.irr_20y}, Breakeven={data.breakeven_year}, "
            f"Currency={data.currency}"
        )

    def _table_to_text(self, table) -> str:
        """将 pdfplumber 表格转为文本"""
        lines = []
        for row in (table or []):
            row_text = " | ".join(str(cell or "").strip() for cell in row)
            lines.append(row_text)
        return "\n".join(lines)

    def to_dict(self, data: ActuarialData) -> dict:
        return asdict(data)

    def to_json(self, data: ActuarialData) -> str:
        return json.dumps(asdict(data), ensure_ascii=False, indent=2)


# ── CLI 快速测试 ──
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        sys.exit(1)

    extractor = PDFExtractor()
    result = extractor.extract(sys.argv[1])
    print(extractor.to_json(result))
