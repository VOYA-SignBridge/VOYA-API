from sqlalchemy.orm import Session
from app.models.sign import Sign
from app.models.sign_alias import SignAlias

DEFAULT_SIGNS = [
    {
        "key": "CHAO",
        "public_id": "chao_y9ra17",
        "aliases": ["chào", "chao", "xin chào", "hello", "hi", "alo"]
    },
    {
        "key": "AO_LEN",
        "public_id": "ao_len_mcbyxr",
        "aliases": ["áo len", "ao len", "áo", "len"]
    },
    {
        "key": "BAU_TROI",
        "public_id": "bau_troi_grr6ox",
        "aliases": ["bầu trời", "bau troi", "bầu", "trời"]
    },
    {
        "key": "BINH_MINH",
        "public_id": "binh_minh_o5ue1e",
        "aliases": ["bình minh", "binh minh", "bình", "minh"]
    },
    {
        "key": "KINH_TRONG",
        "public_id": "kinh_trong_onveij",
        "aliases": ["kính trọng", "kinh trong", "kính", "trọng"]
    }
]

from app.utils.normalize_text import normalize


def init_seed_data(db: Session):
    print("⚙️ Initializing sign data...")

    for sign_def in DEFAULT_SIGNS:
        sign = db.query(Sign).filter(Sign.key == sign_def["key"]).first()

        if not sign:
            sign = Sign(
                key=sign_def["key"],
                public_id=sign_def["public_id"],
                language="vi"
            )
            db.add(sign)
            db.commit()
            db.refresh(sign)

        # alias
        for raw in sign_def["aliases"]:
            norm = normalize(raw)
            exists = db.query(SignAlias).filter(
                SignAlias.sign_id == sign.id,
                SignAlias.phrase_normalized == norm
            ).first()

            if not exists:
                db.add(SignAlias(
                    sign_id=sign.id,
                    phrase_raw=raw,
                    phrase_normalized=norm
                ))
                db.commit()

    print("✅ Seed data loaded")
