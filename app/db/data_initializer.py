from sqlalchemy.orm import Session
from app.models.sign import Sign
from app.models.sign_alias import SignAlias
from app.utils.normalize_text import normalize

DEFAULT_SIGNS = [
    # 1. CHÀO
    {
        "key": "CHAO",
        "public_id": "chao_y9ra17",
        "aliases": [
            "chào", "xin chào", "hello", "hi", "alo", "hê lô", "chao"
        ]
    },

    # 2. ÁO LEN
    {
        "key": "AO_LEN",
        "public_id": "ao_len_mcbyxr",
        "aliases": ["áo len", "ao len", "áo", "len"]
    },

    # 3. BẦU TRỜI
    {
        "key": "BAU_TROI",
        "public_id": "bau_troi_grr60x",
        "aliases": ["bầu trời", "bau troi", "bầu", "trời"]
    },

    # 4. BÌNH MINH
    {
        "key": "BINH_MINH",
        "public_id": "binh_minh_o5ue1e",
        "aliases": ["bình minh", "binh minh", "bình", "minh", "bình mình"]
    },

    # 5. KÍNH TRỌNG
    {
        "key": "KINH_TRONG",
        "public_id": "kinh_trong_onveij",
        "aliases": ["kính trọng", "kinh trong", "kính", "trọng"]
    },

    # 6. LỢI ÍCH
    {
        "key": "LOI_ICH",
        "public_id": "loi_ich_yftcak",
        "aliases": ["lợi ích", "loi ich", "có lợi"]
    },

    # 7. ĐỒ ĂN
    {
        "key": "DO_AN",
        "public_id": "do_an_eby5av",
        "aliases": ["đồ ăn", "do an", "thức ăn", "an uong", "ăn uống"]
    },

    # 8. NẰM NGOÀI
    {
        "key": "NAM_NGOAI",
        "public_id": "nam_ngoai_xmas26",
        "aliases": ["nằm ngoài", "nam ngoai", "ngoài trời", "ben ngoai"]
    },

    # 9. CHIA SẺ
    {
        "key": "CHIA_SE",
        "public_id": "chia_se_q54can",
        "aliases": ["chia sẻ", "chia se", "share", "tâm sự", "tam su"]
    },

    # 10. CÁ VOI
    {
        "key": "CA_VOI",
        "public_id": "ca_voi_tty6dc",
        "aliases": ["cá voi", "ca voi", "whale"]
    }
]


def init_seed_data(db: Session):
    print("⚙️ Initializing sign data...")

    for entry in DEFAULT_SIGNS:
        key = entry["key"]
        public_id = entry["public_id"]
        aliases = entry["aliases"]

        # 1) Insert Sign if missing
        sign = db.query(Sign).filter(Sign.key == key).first()
        if not sign:
            sign = Sign(
                key=key,
                language="vi",
                public_id=public_id
            )
            db.add(sign)
            db.commit()
            db.refresh(sign)
            print(f"➕ Added sign: {key}")

        # 2) Insert aliases
        for raw in aliases:
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
            print(f"   ➕ alias added: {raw} → {norm}")
        print("✅ Seed data completed")