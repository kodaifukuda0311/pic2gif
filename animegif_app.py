import io
import math
import streamlit as st
from PIL import Image

# ===== アプリ情報 =====
APP_NAME = "Pic2GIF"

st.set_page_config(page_title=APP_NAME, page_icon="🖼️")
st.title(f"🖼️ JPG/PGN → アニメGIF変換器")
st.write("1枚の画像から、ほぼ静止に見えるアニメGIFを作ります。")

uploaded_file = st.file_uploader(
    "JPG または PNG をアップロード",
    type=["jpg", "jpeg", "png"]
)

# ===== 固定パラメータ（静止寄り） =====
FRAMES_COUNT = 15        # フレーム数
DURATION_MS = 250        # フレーム間隔
ZOOM_STRENGTH_PCT = 0.25 # ズーム強度（%）

def ease_in_out_sine(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)

def make_almost_still_gif_frames(img: Image.Image):
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

        st.subheader("元画像")
        st.image(img, use_container_width=True)

        frames = make_almost_still_gif_frames(img)

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
