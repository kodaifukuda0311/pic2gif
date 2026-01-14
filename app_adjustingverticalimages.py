import io
import math
import streamlit as st
from PIL import Image

# ===== アプリ情報 =====
APP_NAME = "JPG/PNG → アニメGIF変換器"

st.set_page_config(page_title=APP_NAME, page_icon="🖼️")
st.title(f"🖼️ {APP_NAME}")
st.write("1枚の画像から、ほぼ静止画に見えるアニメGIFを作ります。縦長の画像は左右に余白を加えます。")

uploaded_file = st.file_uploader(
    "JPG または PNG をアップロード",
    type=["jpg", "jpeg", "png"]
)

# ===== 固定パラメータ（静止寄り） =====
FRAMES_COUNT = 15
DURATION_MS = 250
ZOOM_STRENGTH_PCT = 0.18

# ===== 目標アスペクト比（22:23）=====
TARGET_RATIO = 22 / 23  # width / height

def ease_in_out_sine(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)

def pad_to_target_ratio_if_portrait(img: Image.Image) -> Image.Image:
    """
    縦長（w/h < 22/23）の場合のみ左右に余白を追加。
    横長はそのまま返す。
    """
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    if w / h >= TARGET_RATIO:
        return img  # 横長はそのまま

    new_w = math.ceil(h * TARGET_RATIO)
    pad_left = (new_w - w) // 2
    pad_right = new_w - w - pad_left

    # 背景：透過あり → 透明 / なし → 白
    has_alpha = "A" in img.getbands()
    bg = (0, 0, 0, 0) if has_alpha else (255, 255, 255, 255)

    canvas = Image.new("RGBA", (new_w, h), bg)
    canvas.paste(img.convert("RGBA"), (pad_left, 0))
    return canvas

def make_almost_still_frames(img: Image.Image):
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    frames = []

    for i in range(FRAMES_COUNT):
        x = i / (FRAMES_COUNT - 1)
        tri = 1.0 - abs(2.0 * x - 1.0)   # 0→1→0
        eased = ease_in_out_sine(tri)
        zoom = 1.0 + (ZOOM_STRENGTH_PCT / 100.0) * eased

        nw, nh = int(w * zoom), int(h * zoom)
        frame = img.resize((nw, nh), Image.LANCZOS)

        # 中央クロップ
        left = (nw - w) // 2
        top = (nh - h) // 2
        frame = frame.crop((left, top, left + w, top + h))
        frames.append(frame)

    return frames

if uploaded_file:
    try:
        img = Image.open(uploaded_file)
        img.load()

        # 縦長のみ余白調整
        adjusted = pad_to_target_ratio_if_portrait(img)

        # ほぼ静止のアニメGIF生成
        frames = make_almost_still_frames(adjusted)

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

