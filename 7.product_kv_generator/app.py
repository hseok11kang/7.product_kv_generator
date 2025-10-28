# app.py — 📸Key Visual Editor (PDP → 3 KV → Pick → Prompt → Edit(Result))
# -----------------------------------------------------------------------------
# 설치:
#   pip install -U streamlit pillow
# 실행:
#   streamlit run app.py
# 조건:
#   C:\gemini-test\image 폴더에 KV1 / KV2 / KV3 (선택적으로 KV4/KV5/KV6) 이미지 파일 존재
#   확장자: png / jpg / jpeg / webp
# -----------------------------------------------------------------------------

import os, time
import streamlit as st
from PIL import Image
from pathlib import Path

# ========================== 기본 설정 ==========================
st.set_page_config(page_title="📸 Key Visual Editor", layout="centered")


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "image"   # app.py 옆의 image 폴더를 자동으로 찾음


ALLOWED_EXT = [".png", ".jpg", ".jpeg", ".webp"]
DISPLAY_BOX = (640, 640)         # 그리드 썸네일(통일 사이즈)
TALL_NAMES = {"KV5", "KV6"}      # 세로형: “표시 크기만” 줄이기(이미지 자체는 원본 유지)

# 제품 요약(3줄)
PRODUCT_SUMMARY_LINES = [
    "48형 4K OLED, α8 AI 프로세서 & webOS 24로 화질/사운드 자동 최적화",
    "4개의 HDMI 2.1, 120Hz, Dolby Vision & Atmos, G-SYNC/VRR 등 게이밍 지원",
    "초슬림 베젤 디자인과 LG ThinQ AI로 편리한 스마트 기능"
]

# ========================== 유틸 함수 ==========================
def try_open(path, max_px=2400):
    try:
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        if max(w, h) > max_px:
            scale = max_px / max(w, h)
            im = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
        return im
    except Exception:
        return None

def find_first_existing(basename, base_dir=IMAGE_DIR):
    """
    KV1 → KV1.png/jpg/jpeg/webp 중 '대소문자 무시'하고 존재하는 첫 파일 경로 반환
    - 확장자: .jpg/.JPG 모두 허용
    - 파일명: KV1/kv1/kv1 등 모두 허용
    """
    # 소문자 허용 확장자 + 대문자 확장자까지 모두 시도
    exts = ALLOWED_EXT + [e.upper() for e in ALLOWED_EXT]

    # 우선순위: 원래 표기(basename) → 소문자 → 대문자
    basenames = [basename, basename.lower(), basename.upper()]

    for bn in basenames:
        for ext in exts:
            p = os.path.join(base_dir, bn + ext)
            if os.path.isfile(p):
                return p
    return None

def load_kv123():
    items = []
    for name in ["KV1", "KV2", "KV3"]:
        p = find_first_existing(name)
        if p:
            im = try_open(p)
            if im:
                items.append((name, p, im))
    return items

def fit_to_box(im: Image.Image, box=(640,640), bg=(245,245,245,255)) -> Image.Image:
    """그리드 썸네일용(원본과 별개). 썸네일은 리샘플 허용."""
    W, H = box
    canvas = Image.new("RGBA", (W, H), bg)
    w, h = im.size
    scale = min(W / w, H / h)
    nw, nh = int(w * scale), int(h * scale)
    im2 = im.resize((nw, nh), Image.LANCZOS)
    x = (W - nw) // 2
    y = (H - nh) // 2
    canvas.alpha_composite(im2, dest=(x, y))
    return canvas

# ========================== 상태 ==========================
if "top3" not in st.session_state:
    st.session_state.top3 = []            # [(name, path, PIL.Image), ...]
if "picked" not in st.session_state:
    st.session_state.picked = None        # {"name": str, "path": str, "im": PIL.Image}
if "result" not in st.session_state:
    st.session_state.result = None        # {"name": str, "im": PIL.Image}
if "zoom_img" not in st.session_state:
    st.session_state.zoom_img = None      # {"name": str, "im": PIL.Image}

# ========================== UI ==========================
st.title("📸 Key Visual Editor")

# 상단 액션
url_input = st.text_input("Product Detail Page URL", value="https://www.lge.co.kr/tvs/oled48b4nna-stand")
if st.button("PDP 분석 및 핵심 KV 추출", type="primary"):
    st.session_state.top3 = []
    st.session_state.picked = None
    st.session_state.result = None
    st.session_state.zoom_img = None

    # 7초 로딩 + 안내 문구
    with st.spinner("AI가 제품 PDP를 분석하고 있어요."):
        time.sleep(7)

    items = load_kv123()
    if len(items) < 3:
        st.error(
            f"이미지 3장을 찾지 못했습니다. 폴더를 확인하세요: {IMAGE_DIR}\n"
            f"필요 파일: KV1.*, KV2.*, KV3.* (확장자: {', '.join(ALLOWED_EXT)})"
        )
    else:
        st.session_state.top3 = items

# 제품 요약(3줄) + 3장 그리드(썸네일)
if st.session_state.top3:
    # ▼ 요청사항 반영: 워딩 변경 + 제품명 한 줄 추가
    st.markdown("### 제품 정보 및 Key Visual")
    st.write("LG 올레드 TV 스탠드형 (OLED48B4NNA)")
    for line in PRODUCT_SUMMARY_LINES:
        st.write(f"• {line}")

    cols = st.columns(3)
    for i, (name, path, im) in enumerate(st.session_state.top3):
        thumb = fit_to_box(im, DISPLAY_BOX)  # 썸네일(표시용)
        with cols[i]:
            st.image(thumb, caption=name, use_container_width=True)

            # 확대 보기(원본 사용, 표시 크기만 제어 — 해상도 유지)
            if st.button("이미지 크게 보기", key=f"zoom_{name}", use_container_width=True):
                st.session_state.zoom_img = {"name": name, "im": im}

            # 선택 버튼 + 선택 상태 표시
            if st.button("해당 이미지 선택", key=f"pick_{name}", use_container_width=True):
                st.session_state.picked = {"name": name, "path": path, "im": im}
                st.session_state.result = None

            if st.session_state.picked and st.session_state.picked["name"] == name:
                st.success("✅ 선택됨")

# 클릭 확대 섹션(원본 그대로, 표시 너비만 조절)
if st.session_state.zoom_img:
    zname = st.session_state.zoom_img['name']
    zim = st.session_state.zoom_img['im']
    st.markdown(f"### {zname} 크게 보기")
    if zname in TALL_NAMES:
        st.image(zim, width=520)  # 표시 크기만 줄임(해상도 원본 유지)
    else:
        st.image(zim, use_container_width=True)
    if st.button("닫기", key="close_zoom", use_container_width=True):
        st.session_state.zoom_img = None

# 선택 안내 배너
if st.session_state.picked:
    st.info(f"현재 선택된 이미지: {st.session_state.picked['name']}")

# 선택 후 편집 영역
if st.session_state.picked:
    st.markdown("### 선택한 KV 편집")
    prompt_val = st.text_area(
        "프롬프트 (예: 배경 톤을 약간 따뜻하게, 텍스트는 산세리프로, 제품 반사광 강조)",
        key="prompt_text",
        height=90
    )

    if st.button("편집하기", type="primary"):
        # 규칙: 프롬프트 특정 단어 → 해당 KV 반환
        target_name = None
        ptxt = (prompt_val or "")
        if "축구" in ptxt:
            target_name = "KV4"
        elif "인스타" in ptxt:
            target_name = "KV5"
        elif "LG" in ptxt or "lg" in ptxt:
            target_name = "KV6"

        with st.spinner("편집 중…"):
            time.sleep(7)

        show_name = st.session_state.picked["name"]
        show_im = st.session_state.picked["im"]
        if target_name:
            tpath = find_first_existing(target_name)
            if tpath:
                tim = try_open(tpath)
                if tim:
                    show_name, show_im = target_name, tim

        st.session_state.result = {"name": show_name, "im": show_im}

# 결과 표시(원본 그대로, 표시 너비만 조절 — 해상도 유지)
if st.session_state.result is not None:
    rname = st.session_state.result["name"]
    rim = st.session_state.result["im"]
    st.markdown("### 편집 결과")
    if rname in TALL_NAMES:
        st.image(rim, width=520)  # 해상도는 원본, 화면 표시만 작게
    else:
        st.image(rim, use_container_width=True)
