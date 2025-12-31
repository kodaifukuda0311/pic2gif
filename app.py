import io
import streamlit as st
from PIL import Image

st.set_page_config(page_title="JPG/PNG → GIF (静止)", page_icon="🖼️")
st.title("🖼️JPG/PNG → GIF 変換")
st.write("1枚の JPG/PNG を静止GIFに変換してダウンロードできます。")

uploaded_file = st.file_uploader("JPG または PNG をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    try:
        img = Image.open(uploaded_file)
        img.load()

        st.subheader("プレビュー")
        st.image(img, caption=uploaded_file.name, use_container_width=True)

        # GIFへ変換
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA") if "A" in img.getbands() else img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="GIF")
        buf.seek(0)

        st.download_button(
            "GIF をダウンロード",
            data=buf,
            file_name="converted.gif",
            mime="image/gif",
        )
    except Exception as e:
        st.error(f"変換に失敗しました: {e}")
else:
    st.info("JPG/PNG を1枚アップロードしてください。")

