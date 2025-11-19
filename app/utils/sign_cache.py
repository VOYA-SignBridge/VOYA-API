# app/utils/sign_cache.py
from sqlalchemy.orm import Session
from app.models.sign_alias import SignAlias

class SignCache:
    def __init__(self):
        # "binh minh" -> { sign_id, key, public_id, phrase_raw }
        self.phrase_to_sign: dict[str, dict] = {}

    def reload(self, db: Session):
        print("🔄 Reloading sign cache...")
        self.phrase_to_sign.clear()
        aliases = db.query(SignAlias).all()
        for al in aliases:
            print("alias in DB:", al.phrase_normalized, "->", al.sign.public_id)  # <--- thêm dòng này
            self.phrase_to_sign[al.phrase_normalized] = {
                "sign_id": al.sign.id,
                "key": al.sign.key,
                "public_id": al.sign.public_id,
                "phrase_raw": al.phrase_raw,
            }
        print("✅ Sign cache entries:", self.phrase_to_sign.keys())


    def match_tokens(self, tokens: list[str]):
        result = []
        i = 0
        while i < len(tokens):
            # thử cụm 2 từ
            if i + 1 < len(tokens):
                two = f"{tokens[i]} {tokens[i+1]}"
                if two in self.phrase_to_sign:
                    result.append(self.phrase_to_sign[two])
                    i += 2
                    continue
            # thử 1 từ
            one = tokens[i]
            if one in self.phrase_to_sign:
                result.append(self.phrase_to_sign[one])
            i += 1
        return result

sign_cache = SignCache()
