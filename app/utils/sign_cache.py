# app/utils/sign_cache.py
from sqlalchemy.orm import Session
from app.models.sign_alias import SignAlias

class SignCache:
    def __init__(self):
        # map từ phrase chuẩn hoá -> { sign_id, key, public_id, phrase_raw }
        self.phrase_to_sign = {}
        # map từ key -> { sign_id, key, public_id, phrase_raw }
        self.key_to_sign = {}

    def reload(self, db: Session):
        print("🔄 Reloading sign cache...")

        self.phrase_to_sign.clear()
        self.key_to_sign.clear()

        aliases = db.query(SignAlias).all()

        for al in aliases:
            item = {
                "sign_id": al.sign.id,
                "key": al.sign.key,
                "public_id": al.sign.public_id,
                "phrase_raw": al.phrase_raw,
            }

            # phrase chuẩn hoá
            self.phrase_to_sign[al.phrase_normalized] = item

            # key -> sign
            self.key_to_sign[al.sign.key] = item

        print("✅ Loaded", len(self.phrase_to_sign), "phrases")

    def match_tokens(self, tokens):
        """
        tokens: ["xin", "chao"]
        ưu tiên match cụm 2 trước, sau đó 1 từ
        """
        result = []
        i = 0

        while i < len(tokens):
            # thử match 2 tokens
            if i + 1 < len(tokens):
                two = tokens[i] + " " + tokens[i + 1]
                if two in self.phrase_to_sign:
                    result.append(self.phrase_to_sign[two])
                    i += 2
                    continue

            # thử 1 token
            one = tokens[i]
            if one in self.phrase_to_sign:
                result.append(self.phrase_to_sign[one])

            i += 1

        return result

    def get_by_keys(self, keys):
        """Trả về danh sách sign tương ứng với list key"""
        return [self.key_to_sign[k] for k in keys if k in self.key_to_sign]


# global instance
sign_cache = SignCache()
