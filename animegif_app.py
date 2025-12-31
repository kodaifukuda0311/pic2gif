import io
import streamlit as st
from PIL import Image

# ===== アプリ設定 =====
st.set_page_config(page_title="Pic2GIF", page_icon="🖼️")
st.title("🖼️JPG/PGN → アニメGIF変換")
st.write("1枚の画像から、ほぼ静止に見えるアニメGIFを作ります。")

uploaded_file = st.file_uploader(
    "JPG または PNG をアップロード",
    type=["jpg", "jpeg", "png"]
)

# ===== 設定UI =====
st.subheader("アニメーション設定")

frames_count = st.slider("フレーム数", 3, 15, 7)
duration = st.slider("スピード（ms）", 50, 500, 150)
zoom_strength = st.slider("動きの強さ（%）", 0.5, 3.0, 1.5)

# ===== 処理 =====
def make_subtle_zoom_gif(img: Image.Image):
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    frames = []

    # 拡大率（行って戻る）
    half = frames_count // 2
    zooms = (
        [1 + (zoom_strength / 100) * (i / half) for i in range(half)]
        + [1 + (zoom_strength / 100) * (i / half) for i in reversed(range(half + 1))]
    )

    for z in zooms:
        nw, nh = int(w * z), int(h * z)
        frame = img.resize((nw, nh), Image.LANCZOS)

        # 中央クロップして元サイズに戻す
        left = (nw - w) // 2
        top = (nh - h) // 2
        frame = frame.crop((left, top, left + w, top + h))

        frames.append(frame)

    return frames

# ===== 実行 =====
if uploaded_file:
    try:
        img = Image.open(uploaded_file)
        img.load()

        st.subheader("元画像")
        st.image(img, use_container_width=True)

        frames = make_subtle_zoom_gif(img)

        buf = io.BytesIO()
        frames[0].save(
            buf,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            disposal=2,
            optimize=True,
        )
        buf.seek(0)

        st.success("アニメGIFを生成しました！")
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
