import io
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


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
    "%Y年%m月%d日",  # Chinese format
    "%Y.%m.%d",
    "%d-%b-%Y",
    "%d %b, %Y",
]

DATE_REGEXES = [
    r"\b(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})\b",  # 2025-01-15, 2025.01.15
    r"\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})\b",  # 15/01/2025, 15.01.2025
    r"\b(\d{4}年\d{1,2}月\d{1,2}日)\b",  # 2025年1月15日 (Chinese)
    r"\b([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})\b",  # January 15, 2025
    r"\b(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b",  # 15 January 2025
    r"\b(\d{1,2}[-/][A-Za-z]{3}[-/]\d{4})\b",  # 15-Jan-2025
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

def _preprocess_image(image):
    """
    Preprocess image for better OCR accuracy.

    Improvements:
    - Convert to grayscale
    - Increase contrast
    - Denoise
    - Binarization
    - Deskew
    """
    if not CV2_AVAILABLE:
        # Return original image if OpenCV not available
        return image

    try:
        # Convert PIL Image to numpy array
        if hasattr(image, 'mode'):
            img_array = np.array(image)
        else:
            img_array = image

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

        # Adaptive thresholding for binarization
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Deskew (correct rotation)
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            # Only apply rotation if angle is significant
            if abs(angle) > 0.5:
                (h, w) = binary.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                binary = cv2.warpAffine(
                    binary, M, (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )

        # Convert back to PIL Image
        from PIL import Image
        return Image.fromarray(binary)

    except Exception as e:
        # If preprocessing fails, return original image
        print(f"Image preprocessing warning: {e}")
        return image


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


def _clean_ocr_text(text: str) -> str:
    """Clean OCR text by fixing common recognition errors."""
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', text)

    # Fix common OCR mistakes
    replacements = {
        r'\b0(?=[A-Z])': 'O',  # 0 -> O when followed by uppercase
        r'\bl(?=[0-9])': '1',  # l -> 1 when followed by digit
        r'\bI(?=[0-9])': '1',  # I -> 1 when followed by digit
        r'(?<=[A-Z])0(?=[A-Z])': 'O',  # 0 -> O between uppercase letters
    }

    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned)

    return cleaned


def _extract_text(pdf_path: str) -> str:
    """Returns combined text from all pages in the PDF or image file with enhanced OCR."""
    text_segments = []

    # Enhanced Tesseract configuration
    # PSM 3: Fully automatic page segmentation (default)
    # PSM 1: Automatic page segmentation with OSD (Orientation and Script Detection)
    # OEM 3: Default (both Legacy and LSTM engines)
    tesseract_config = r'--oem 3 --psm 3 -c preserve_interword_spaces=1'

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

                        # Convert page to higher resolution image (400 DPI for better accuracy)
                        pix = page.get_pixmap(dpi=400)
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))

                        # Preprocess image for better OCR
                        processed_img = _preprocess_image(img)

                        # Perform OCR with Chinese and English support
                        # Try with multiple configurations for better results
                        ocr_text = None

                        # Try English + Chinese (Traditional and Simplified)
                        try:
                            ocr_text = pytesseract.image_to_string(
                                processed_img,
                                lang='eng+chi_tra+chi_sim',
                                config=tesseract_config
                            )
                        except Exception:
                            # Fallback to English only
                            try:
                                ocr_text = pytesseract.image_to_string(
                                    processed_img,
                                    lang='eng',
                                    config=tesseract_config
                                )
                            except Exception:
                                pass

                        # If preprocessed image didn't work well, try original
                        if not ocr_text or len(ocr_text.strip()) < 10:
                            try:
                                ocr_text = pytesseract.image_to_string(
                                    img,
                                    lang='eng+chi_tra+chi_sim',
                                    config=tesseract_config
                                )
                            except Exception:
                                try:
                                    ocr_text = pytesseract.image_to_string(
                                        img,
                                        lang='eng',
                                        config=tesseract_config
                                    )
                                except Exception:
                                    pass

                        if ocr_text and ocr_text.strip():
                            cleaned_text = _clean_ocr_text(ocr_text)
                            text_segments.append(cleaned_text)

                    except ImportError:
                        # pytesseract not available, skip OCR
                        pass
                    except Exception as e:
                        # OCR failed, skip this page
                        print(f"OCR warning for page: {e}")
                        pass

    except Exception as e:
        # If PyMuPDF fails, try with PIL + pytesseract directly for image files
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(pdf_path)

            # Preprocess image
            processed_img = _preprocess_image(img)

            # Try OCR with multiple configurations
            ocr_text = None
            try:
                ocr_text = pytesseract.image_to_string(
                    processed_img,
                    lang='eng+chi_tra+chi_sim',
                    config=tesseract_config
                )
            except Exception:
                try:
                    ocr_text = pytesseract.image_to_string(
                        processed_img,
                        lang='eng',
                        config=tesseract_config
                    )
                except Exception:
                    pass

            # Try original image if preprocessed didn't work
            if not ocr_text or len(ocr_text.strip()) < 10:
                try:
                    ocr_text = pytesseract.image_to_string(
                        img,
                        lang='eng+chi_tra+chi_sim',
                        config=tesseract_config
                    )
                except Exception:
                    try:
                        ocr_text = pytesseract.image_to_string(
                            img,
                            lang='eng',
                            config=tesseract_config
                        )
                    except Exception:
                        pass

            if ocr_text and ocr_text.strip():
                cleaned_text = _clean_ocr_text(ocr_text)
                text_segments.append(cleaned_text)

        except ImportError:
            raise ValueError("Cannot process image files: pytesseract library not installed. Please install it with: pip install pytesseract")
        except Exception as ex:
            raise ValueError(f"Failed to extract text from file: {str(ex)}")

    return "\n".join(text_segments)


def _find_invoice_number(text: str) -> Optional[str]:
    """Enhanced invoice number detection with more patterns."""
    patterns = [
        # Standard formats
        r"Invoice\s*(?:Number|No\.?|#|NUM)\s*[:#]?\s*([A-Za-z0-9\-\/\\_]+)",
        r"Invoice\s*ID\s*[:#]?\s*([A-Za-z0-9\-\/\\_]+)",
        r"Inv\.?\s*(?:No\.?|#|NUM)\s*[:#]?\s*([A-Za-z0-9\-\/\\_]+)",
        # Common variations
        r"(?:INV|INVOICE)[-\s]*([A-Z0-9]{3,}[\-\/]?[A-Z0-9]*)",
        r"Bill\s*(?:No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-\/\\_]+)",
        r"Receipt\s*(?:No\.?|#)\s*[:#]?\s*([A-Za-z0-9\-\/\\_]+)",
        # Chinese formats
        r"(?:发票号码|发票编号|票据号)[：:]\s*([A-Za-z0-9\-\/\\_]+)",
        r"(?:Invoice|发票)\s*(?:Number|号码|编号)[：:]\s*([A-Za-z0-9\-\/\\_]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Filter out invalid matches (too short or only special chars)
            if candidate and len(candidate) >= 3 and re.search(r'[A-Za-z0-9]', candidate):
                return candidate

    return None


def _find_total_amount(text: str) -> Optional[float]:
    """Enhanced total amount detection with more patterns and currency support."""
    patterns = [
        # English patterns
        r"(?:Total\s+(?:Amount|Due|Price)?|Amount\s+Due|Balance\s+Due|Grand\s+Total|Net\s+Total)\s*[:：]?\s*[$¥€£]?\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:Subtotal|Sub-total|Sub\s+Total)\s*[:：]?\s*[$¥€£]?\s*([\d,]+(?:\.\d{1,2})?)",
        r"(?:Total|Sum)[:：]\s*[$¥€£]?\s*([\d,]+(?:\.\d{1,2})?)",
        # Currency symbols followed by amount
        r"[$¥€£]\s*([\d,]+(?:\.\d{1,2})?)",
        # Chinese patterns
        r"(?:总[计金]额|合[计金]额|应付金额|总价)[：:]\s*[$¥€£]?\s*([\d,，]+(?:\.\d{1,2})?)",
        r"(?:Total|总额)\s*[$¥€£]?\s*([\d,，]+(?:\.\d{1,2})?)",
        # Invoice total patterns
        r"Invoice\s+Total\s*[:：]?\s*[$¥€£]?\s*([\d,]+(?:\.\d{1,2})?)",
    ]

    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            for value in matches:
                # Replace Chinese comma with standard comma
                value = value.replace('，', ',')
                number = _to_number(value)
                if number is not None and number > 0:
                    amounts.append(number)

    if amounts:
        # Return the maximum amount found (usually the total)
        return max(amounts)

    return None


def _find_invoice_date(text: str, lines: List[str]) -> Optional[str]:
    """Enhanced date detection with English and Chinese keyword support."""
    keyword_targets = [
        # English keywords
        "invoice date",
        "date of invoice",
        "issue date",
        "issued on",
        "date issued",
        "billing date",
        "bill date",
        # Chinese keywords
        "发票日期",
        "开票日期",
        "日期",
        "开具日期",
    ]

    # First, search lines with keywords
    for line in lines:
        lowered = line.lower()
        # Check English keywords
        if any(keyword in lowered for keyword in keyword_targets):
            match = _search_line_for_date(line)
            if match:
                normalized = _normalize_date(match)
                if normalized:
                    return normalized

        # Check Chinese keywords
        if any(keyword in line for keyword in ["发票日期", "开票日期", "开具日期"]):
            match = _search_line_for_date(line)
            if match:
                normalized = _normalize_date(match)
                if normalized:
                    return normalized

    # If not found in keyword lines, search entire text
    for pattern in DATE_REGEXES:
        matches = re.findall(pattern, text)
        for match in matches:
            normalized = _normalize_date(match)
            if normalized:
                # Validate year is reasonable (between 2000-2050)
                try:
                    year = int(normalized.split('-')[0])
                    if 2000 <= year <= 2050:
                        return normalized
                except:
                    pass

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
