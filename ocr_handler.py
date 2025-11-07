import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF


DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
]

DATE_REGEXES = [
    r"\b(\d{4}[-/]\d{2}[-/]\d{2})\b",
    r"\b(\d{2}[-/]\d{2}[-/]\d{4})\b",
    r"\b(\d{2}\.\d{2}\.\d{4})\b",
    r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b",
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b",
]

COMPANY_KEYWORDS = [
    "company name",
    "supplier",
    "vendor",
    "seller",
    "service provider",
    "issued by",
    "from",
    "invoice from",
    "provided by",
]

COMPANY_EXCLUDE_TERMS = [
    "bill to",
    "billed to",
    "invoice to",
    "sold to",
    "customer",
    "client",
    "ship to",
]

COMPANY_SUFFIXES = [
    "inc",
    "inc.",
    "co",
    "co.",
    "corp",
    "corp.",
    "ltd",
    "ltd.",
    "llc",
    "gmbh",
    "pte",
    "pte.",
    "company",
    "limited",
    "corporation",
    "plc",
    "sas",
    "sa",
    "kg",
    "ag",
    "bv",
    "srl",
    "oy",
]

ADDRESS_TERMS = [
    "street",
    "st.",
    "road",
    "rd.",
    "avenue",
    "ave",
    "suite",
    "unit",
    "floor",
    "fl",
    "building",
    "blvd",
    "boulevard",
    "drive",
    "dr",
    "lane",
    "ln",
    "highway",
    "hwy",
    "no.",
    "zip",
    "postal",
    "p.o.",
    "box",
]

CONTACT_TERMS = [
    "@",
    "www.",
    "http://",
    "https://",
    "support",
    "contact",
    "phone",
    "tel",
    "fax",
    "email",
]

def extract_invoice_data(pdf_path: str) -> Tuple[Dict[str, Optional[str]], List[str]]:
    """Extracts invoice information from a PDF or image file and returns the detected fields plus warnings."""
    text = _extract_text(pdf_path)
    if not text.strip():
        raise ValueError("No readable text detected in the file. Please fill the fields manually.")

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    invoice_number = _find_invoice_number(text)
    total_amount = _find_total_amount(text)
    invoice_date = _find_invoice_date(text, lines)
    company_name = _find_company_name(lines)

    if (
        invoice_number is None
        and invoice_date is None
        and company_name is None
        and total_amount is None
    ):
        raise ValueError("Could not detect invoice details automatically. Please fill them manually.")

    result: Dict[str, Optional[str]] = {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "company_name": company_name,
        "total_amount": f"{total_amount:.2f}" if total_amount is not None else None,
    }

    warnings: List[str] = []
    if not invoice_date:
        warnings.append("Invoice date was not detected; please enter it manually.")
    if not company_name:
        warnings.append("Company name was not detected; please enter it manually.")

    return result, warnings


def _extract_text(pdf_path: str) -> str:
    """Returns combined text from all pages in the PDF or image file."""
    text_segments = []

    try:
        # Try to open with PyMuPDF (supports PDF, images like JPEG, PNG, TIFF)
        with fitz.open(pdf_path) as doc:
            for page in doc:
                # First try to extract embedded text
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    text_segments.append(page_text)
                else:
                    # If no embedded text, try OCR with pytesseract
                    try:
                        import pytesseract
                        from PIL import Image

                        # Convert page to image
                        pix = page.get_pixmap(dpi=300)
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))

                        # Perform OCR
                        ocr_text = pytesseract.image_to_string(img, lang='eng')
                        if ocr_text and ocr_text.strip():
                            text_segments.append(ocr_text)
                    except ImportError:
                        # pytesseract not available, skip OCR
                        pass
                    except Exception:
                        # OCR failed, skip this page
                        pass
    except Exception as e:
        # If PyMuPDF fails, try with PIL + pytesseract directly for image files
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(pdf_path)
            ocr_text = pytesseract.image_to_string(img, lang='eng')
            if ocr_text and ocr_text.strip():
                text_segments.append(ocr_text)
        except ImportError:
            raise ValueError("Cannot process image files: pytesseract library not installed. Please install it with: pip install pytesseract")
        except Exception:
            raise ValueError(f"Failed to extract text from file: {str(e)}")

    return "\n".join(text_segments)


def _find_invoice_number(text: str) -> Optional[str]:
    patterns = [
        r"Invoice\s*(?:Number|No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"Invoice\s*ID\s*[:#]?\s*([A-Za-z0-9\-\/]+)",
        r"Inv\.\s*#\s*([A-Za-z0-9\-\/]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate
    return None


def _find_total_amount(text: str) -> Optional[float]:
    patterns = [
        r"(?:Total\s+(?:Amount|Due)?|Amount\s+Due|Balance\s+Due)\s*[:$]?\s*([\d,]+(?:\.\d+)?)",
        r"\$\s*([\d,]+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            numbers = [_to_number(value) for value in matches]
            numbers = [number for number in numbers if number is not None]
            if numbers:
                return max(numbers)
    return None


def _find_invoice_date(text: str, lines: List[str]) -> Optional[str]:
    keyword_targets = [
        "invoice date",
        "date of invoice",
        "issue date",
        "issued on",
    ]
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in keyword_targets):
            match = _search_line_for_date(line)
            if match:
                normalized = _normalize_date(match)
                if normalized:
                    return normalized

    for pattern in DATE_REGEXES:
        matches = re.findall(pattern, text)
        for match in matches:
            normalized = _normalize_date(match)
            if normalized:
                return normalized
    return None


def _search_line_for_date(line: str) -> Optional[str]:
    for pattern in DATE_REGEXES:
        match = re.search(pattern, line)
        if match:
            return match.group(1)
    return None


def _find_company_name(lines: List[str]) -> Optional[str]:
    best_value: Optional[str] = None
    best_score: float = -float("inf")

    for index, raw_line in enumerate(lines[:20]):
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if _looks_like_contact(line):
            continue

        score = _base_company_score(line)

        if any(term in lower for term in COMPANY_EXCLUDE_TERMS):
            score -= 4
        if _looks_like_address(line):
            score -= 6

        # Company name is often directly above an address block.
        if index + 1 < len(lines) and _looks_like_address(lines[index + 1]):
            score += 7
        if index + 1 < len(lines) and _looks_like_contact(lines[index + 1].strip()):
            score += 2

        # If previous line is address, this line might be continuation -> penalise.
        if index > 0 and _looks_like_address(lines[index - 1]):
            score -= 2

        # Prioritise early lines.
        if index <= 2:
            score += 1

        # Encourage succinct names.
        if len(line.split()) > 4:
            score -= 1

        if score > best_score:
            best_score = score
            best_value = line

    if best_score < 0:
        return None
    return best_value


def _normalize_date(value: str) -> Optional[str]:
    candidate = value.strip()
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try normalizing textual dates without commas (e.g., "January 5 2023")
    candidate_without_comma = re.sub(r",", "", candidate)
    if candidate_without_comma != candidate:
        for fmt in ("%b %d %Y", "%B %d %Y"):
            try:
                parsed = datetime.strptime(candidate_without_comma, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _to_number(value: str) -> Optional[float]:
    cleaned = re.sub(r"[^\d\.\-]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_value_after_separator(line: str) -> Optional[str]:
    for separator in (":", "-", "–", "—"):
        if separator in line:
            _, _, remainder = line.partition(separator)
            value = remainder.strip()
            if value:
                return value
    return None


def _looks_like_company(value: str) -> bool:
    return _base_company_score(value) >= 0


def _base_company_score(value: str) -> int:
    text = value.strip()
    if not text:
        return -5

    lower = text.lower()
    words = re.split(r"[,\s]+", lower)

    score = 0

    if any(word in COMPANY_SUFFIXES for word in words):
        score += 4

    if text.isupper() and len(text) > 3:
        score += 3

    if any(term in lower for term in COMPANY_EXCLUDE_TERMS):
        score -= 4

    if any(term in lower for term in ADDRESS_TERMS):
        score -= 3

    digit_count = sum(ch.isdigit() for ch in text)
    if digit_count:
        digit_ratio = digit_count / max(len(text), 1)
        if digit_ratio > 0.3:
            score -= 2
        else:
            score -= 1

    if len(words) >= 2:
        score += 1

    if len(text) > 45:
        score -= 2

    if len(text) < 3:
        score -= 2

    return score


def _looks_like_address(line: str) -> bool:
    lowered = line.lower()
    if any(term in lowered for term in ADDRESS_TERMS):
        return True
    digit_count = sum(ch.isdigit() for ch in lowered)
    if digit_count >= 2 and any(char.isdigit() for char in lowered.split()[0]):
        return True
    return False


def _looks_like_contact(value: str) -> bool:
    lowered = value.lower()
    if any(term in lowered for term in CONTACT_TERMS):
        return True
    if "@" in value or lowered.endswith(".com") or lowered.endswith(".net") or lowered.endswith(".org"):
        return True
    return False
