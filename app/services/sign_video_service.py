# app/services/sign_video_service.py

from typing import List, Dict, Optional
import json
from fastapi import HTTPException
import numpy as np
# from app.ai.embedding_text import get_sign_vectors, embed_text
import logging

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    logging.warning("google.generativeai is not installed. Sign-video generation via Gemini is disabled.")
from cloudinary.utils import cloudinary_url

from app.core.config import settings
from app.utils.sign_cache import sign_cache
from app.utils.normalize_text import normalize
from app.schemas.sign_video_schema import SignVideo

# =========================
# 0. CẤU HÌNH GEMINI
# =========================

# Yêu cầu: pip install google-generativeai
# Trong settings của bạn nên có GEMINI_API_KEY
genai.configure(api_key=settings.gemini_api_key)


# =========================
# 1. HELPER: build list SignVideo từ cache item
# =========================

def _build_videos_from_sign_items(items: List[Dict]) -> List[SignVideo]:
    """
    Convert các dict trong cache -> list SignVideo có URL Cloudinary.
    items: [{ sign_id, key, public_id, phrase_raw }, ...]
    """
    videos: List[SignVideo] = []

    for item in items:
        mp4_url, _ = cloudinary_url(
            item["public_id"],
            resource_type="video",
            secure=True,
            format="mp4",
        )
        webm_url, _ = cloudinary_url(
            item["public_id"],
            resource_type="video",
            secure=True,
            format="webm",
        )
        videos.append(
            SignVideo(
                sign_id=item["sign_id"],
                key=item["key"],
                phrase=item["phrase_raw"],
                mp4_url=mp4_url,
                webm_url=webm_url,
            )
        )

    return videos


# =========================
# 2. LAYER 1 – DICTIONARY MATCH (sign_cache)
# =========================

def _match_by_dictionary(norm_text: str) -> List[Dict]:
    """
    Bước 1: Dùng từ điển sign_cache (đã normalize) để match.
    Trả list item: { sign_id, key, public_id, phrase_raw }.
    """
    if not norm_text:
        return []

    tokens = norm_text.split()
    matched = sign_cache.match_tokens(tokens)
    return matched


# =========================
# 3. LAYER 2 – GEMINI (LLM) HOOKS
# =========================

def _llm_rewrite_for_sign(text: str) -> Optional[str]:
    """
    Kiểu A – dùng Gemini để viết lại câu chat thành câu “sạch”,
    dễ map từ điển hơn (bỏ slang, tiếng Anh, rác…).
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
    Bạn là hệ thống tiền xử lý cho ứng dụng dịch chat sang ngôn ngữ ký hiệu.
    Hãy viết lại câu sau thành TIẾNG VIỆT đơn giản, lịch sự, ngắn gọn,
    chỉ giữ lại ý chính và loại bỏ từ lóng / rác / thừa.
    Không thêm ý mới.

    Câu gốc: "{text}"

    Chỉ trả về câu đã viết lại, không giải thích thêm.
    """

    try:
        resp = model.generate_content(prompt)
        cleaned = resp.text.strip()
        if cleaned:
            return cleaned
    except Exception as e:
        # TODO: log error nếu cần
        print("Gemini rewrite error:", e)

    return None


def _llm_extract_sign_keys(text: str) -> Optional[List[str]]:
    """
    Kiểu B – dùng Gemini để trả thẳng danh sách sign key,
    ví dụ: ["CHAO", "BAU_TROI"].

    YÊU CẦU: sign_cache có thuộc tính key_to_sign: key -> item
    (bạn chỉ cần thêm dict này trong SignCache.reload).
    """
    model = genai.GenerativeModel("gemini-2.5-flash")

    all_keys = list(sign_cache.key_to_sign.keys())  # ví dụ: ["CHAO","BAU_TROI",...]

    prompt = f"""
    You are a STRICT sign-language action selector.

    Your task:
    - Extract the core meaning of the user's message.
    - Select ONLY from the available sign keys below.
    - Choose the minimal set of sign keys that best convey the meaning.
    - Keep the order semantically correct.
    - If a word has no matching sign key, SKIP it (do NOT hallucinate).

    Available sign keys (exact matching only):
    {all_keys}

    User message: "{text}"

    Output format (MANDATORY):
    - Return ONLY a JSON array of sign keys.
    - No comments. No extra text.
    - If no keys match, return an empty array: []

    Example output:
    ["CHAO", "BAU_TROI"]
    """


    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip()

        # Phòng trường hợp Gemini trả thêm text -> cố parse JSON
        # Ví dụ: "Here is the result:\n```json\n[\"CHAO\"]\n```"
        # Ta strip mã markdown nếu có:
        raw = raw.replace("```json", "").replace("```", "").strip()

        keys = json.loads(raw)
        print("Extracted sign keys:", keys)
        if isinstance(keys, list):
            # Lọc những key hợp lệ
            filtered = [k for k in keys if k in sign_cache.key_to_sign]
            return filtered or None
        
    except Exception as e:
        print("Gemini extract keys error:", e)

    return None


def _match_by_llm(text: str) -> List[Dict]:
    """
    LAYER 2: thử dùng Gemini theo 2 cách:
      1) rewrite -> normalize -> match từ điển
      2) extract sign keys -> map key -> item
    """
    # 2.1. Rewrite thuần ngữ nghĩa, rồi dùng lại từ điển
    rewritten = _llm_rewrite_for_sign(text)
    if rewritten:
        norm = normalize(rewritten)
        items = _match_by_dictionary(norm)
        if items:
            return items

    # 2.2. Không được thì dùng dạng sign key luôn
    sign_keys = _llm_extract_sign_keys(text)
    if sign_keys:
        items = sign_cache.get_by_keys(sign_keys)  # cần hàm này trong sign_cache
        if items:
            return items

    return []


# =========================
# 4. LAYER 3 – VECTOR / EMBEDDING (stub)
# =========================

def _semantic_fallback(text: str) -> List[Dict]:
    # """
    # Bước 3: dùng embedding để tìm sign gần nhất với câu user.
    # Ở đây mình demo theo kiểu: chọn 1–2 sign có similarity cao nhất.
    # """

    # sign_vectors = get_sign_vectors()
    # if not sign_vectors:
    #     return []

    # # Embed câu user
    # user_vec = embed_text(text)

    # # Tính cosine similarity với từng sign
    # best_keys: List[str] = []
    # best_scores: List[float] = []

    # for key, vec in sign_vectors.items():
    #     # cosine similarity = (u·v) / (|u||v|)
    #     sim = float(np.dot(user_vec, vec) /
    #                 (np.linalg.norm(user_vec) * np.linalg.norm(vec) + 1e-8))

    #     # Threshold ví dụ: > 0.6 mới tính là “gần”
    #     if sim > 0.6:
    #         best_keys.append(key)
    #         best_scores.append(sim)

    # if not best_keys:
    #     return []

    # # Sắp xếp theo độ giống giảm dần
    # sorted_pairs = sorted(zip(best_keys, best_scores), key=lambda x: x[1], reverse=True)

    # # Ví dụ: chỉ lấy top 1–2 sign
    # top_keys = [k for k, _ in sorted_pairs[:2]]

    # # Map key -> item trong cache
    # items = sign_cache.get_by_keys(top_keys)
    # return items
    return []


# =========================
# 5. HÀM PUBLIC: text -> list[SignVideo]
# =========================

def text_to_sign_videos(
    text: str,
    use_llm: bool = False,
    use_semantic_fallback: bool = False,
) -> List[SignVideo]:
    """
    Pipeline:
      1) normalize + từ điển (sign_cache)
      2) (optional) LLM (Gemini) để rewrite / extract sign keys
      3) (optional) semantic fallback (vector / fuzzy)

    Trả về list SignVideo (backend trả cho React Native).
    """

    if genai is None:
        # Tạm thời cho backend sống, chỉ chặn endpoint này
        raise HTTPException(
            status_code=500,
            detail="Gemini is not available on this server (google.generativeai not installed)."
        )
    # Bước 0: normalize string thô
    norm = normalize(text)
    if not norm:
        return []

    # Bước 1: từ điển (cache)
    dict_items = _match_by_dictionary(norm)
    if dict_items:
        return _build_videos_from_sign_items(dict_items)

    # Bước 2: LLM nếu bật
    if use_llm:
        llm_items = _match_by_llm(text)
        if llm_items:
            return _build_videos_from_sign_items(llm_items)

    # Bước 3: semantic fallback (embedding)
    if use_semantic_fallback:
        sem_items = _semantic_fallback(text)
        if sem_items:
            return _build_videos_from_sign_items(sem_items)

    # Không tìm được sign nào
    return []


