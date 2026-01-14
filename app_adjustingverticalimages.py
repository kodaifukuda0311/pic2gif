import io
import math
import streamlit as st
from PIL import Image

# ===== アプリ情報 =====
APP_NAME = "JPG/PNG → アニメGIF変換器"

st.set_page_config(page_title=APP_NAME, page_icon="🖼️")
st.title(f"🖼️{APP_NAME}")
st.write("1枚の画像から、ほぼ静止に見えるアニメGIFを作ります（縦長は左右に余白をつけて22:23程度に）。")

uploaded_file = st.file_uploader(
    "JPG または PNG をアップロード",
    type=["jpg", "jpeg", "png"]
)

# ===== 固定パラメータ（静止寄り） =====
FRAMES_COUNT = 15
DURATION_MS = 250
ZOOM_STRENGTH_PCT = 0.2

# ===== 目標アスペクト比 =====
TARGET_W = 22
TARGET_H = 23
TARGET_RATIO = TARGET_W / TARGET_H  # width / height

def ease_in_out_sine(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)

def pad_to_target_ratio_if_portrait(img: Image.Image) -> Image.Image:
    """
    縦長（w/h < TARGET_RATIO）の場合だけ左右に余白を足して、
    幅/高さ ≒ TARGET_RATIO になるようにする。
    横長（w/h >= TARGET_RATIO）はそのまま返す。
    """
    # 余白を足すため RGBA に寄せる（透過PNGは透過を維持しやすい）
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    current_ratio = w / h

    # 横長はそのまま
    if current_ratio >= TARGET_RATIO:
        return img

    # 縦長 → 高さは維持して、必要な幅まで左右に余白を足す
    new_w = math.ceil(h * TARGET_RATIO)
    pad_total = new_w - w
    pad_left = pad_total // 2
    pad_right = pad_total - pad_left

    # 背景：PNGなど透過がある場合は透明、JPGなどは白
    has_alpha = ("A" in img.getbands()) or (img.mode == "RGBA")
    bg = (0, 0, 0, 0) if has_alpha else (255, 255, 255, 255)

    canvas = Image.new("RGBA", (new_w, h), bg)
    canvas.paste(img.convert("RGBA"), (pad_left, 0))
    return canvas

def make_almost_still_gif_frames(img: Image.Image):
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    frames = []

    for i in range(FRAMES_COUNT):
        x = i / (FRAMES_COUNT - 1)
        tri = 1.0 - abs(2.0 * x - 1.0)  # 0→1→0
        eased = ease_in_out_sine(tri)
        zoom = 1.0 + (ZOOM_STRENGTH_PCT / 100.0) * eased

        nw, nh = int(w * zoom), int(h * zoom)
        frame = img.resize((nw, nh), Image.LANCZOS)

        # 中央クロップして元サイズへ
        left = (nw - w) // 2
        top = (nh - h) // 2
        frame = frame.crop((left, top, left + w, top + h))
        frames.append(frame)

    return frames

if uploaded_file:
    try:
        img = Image.open(uploaded_file)
        img.load()

        st.subheader("元画像")
        st.image(img, use_container_width=True)

        # 縦長だけ 22:23 に寄せる（左右余白）
        padded = pad_to_target_ratio_if_portrait(img)

        st.subheader("余白調整後（縦長のみ）")
        st.image(padded, use_container_width=True)

        frames = make_almost_still_gif_frames(padded)

        buf = io.BytesIO()
        frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=DURATION_MS,
            loop=0,
            disposal=2,
            optimize=True,
        )
        buf.seek(0)

        st.success("アニメGIFを生成しました")
        st.image(buf)
        st.download_button(
            "GIFをダウンロード",
            data=buf,
            file_name="animated.gif",
            mime="image/gif",
        )

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("画像を1枚アップロードしてください。")
