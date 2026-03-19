import io
import math
import streamlit as st
from PIL import Image

# ======================
# アプリ設定（固定）
# ======================
APP_NAME = "JPG/PNG → アニメGIF変換器（Ver.2）"
TARGET_RATIO = 22 / 22.5          # 幅/高さ
MAX_SIDE = 950                  # X・Postpone向けにサイズ抑制
GIF_COLORS = 256                # 256色
FRAMES_COUNT = 10               # フレーム数
DURATION_MS = 250               # フレーム間隔
ZOOM_STRENGTH_PCT = 0.18        # ほぼ静止に見える程度

OPTIMIZE_ALWAYS = False

st.set_page_config(page_title=APP_NAME, page_icon="🖼️")
st.title(f"🖼️{APP_NAME}")
st.write("1枚の画像から、ほぼ静止画に見えるアニメGIFを作ります（縦長画像は左右余白で22:23に）。")

uploaded_file = st.file_uploader("JPG または PNG をアップロード", type=["jpg", "jpeg", "png"])


def ease_in_out_sine(t: float) -> float:
    """0→1 を端でゆっくりにするイージング"""
    return 0.5 - 0.5 * math.cos(math.pi * t)


def resize_max_side(img: Image.Image, max_side: int) -> Image.Image:
    """最大辺を max_side に収める（縦横比は維持）"""
    w, h = img.size
    m = max(w, h)
    if m <= max_side:
        return img
    scale = max_side / m
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return img.resize(new_size, Image.LANCZOS)


def pad_to_target_ratio_if_portrait(img: Image.Image) -> Image.Image:
    """
    縦長（w/h < TARGET_RATIO）のときだけ左右に余白を足して22:23に寄せる。
    横長（w/h >= TARGET_RATIO）はそのまま返す。
    """
    # 余白を足すのでRGBAに寄せる
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    if w / h >= TARGET_RATIO:
        return img  # 横長はそのまま

    new_w = math.ceil(h * TARGET_RATIO)
    pad_left = (new_w - w) // 2

    # 白背景
    bg = (255, 255, 255)

    canvas = Image.new("RGB", (new_w, h), bg)
    canvas.paste(img, (pad_left, 0))
    return canvas


def make_almost_still_frames(img: Image.Image):
    """微ズームで「ほぼ静止に見える」フレーム列を作る"""
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    w, h = img.size
    frames = []
    n = FRAMES_COUNT

    for i in range(n):
        x = i / (n - 1) if n > 1 else 0.0
        tri = 1.0 - abs(2.0 * x - 1.0)   # 0→1→0
        eased = ease_in_out_sine(tri)
        zoom = 1.0 + (ZOOM_STRENGTH_PCT / 100.0) * eased

        nw, nh = int(w * zoom), int(h * zoom)
        frame = img.resize((nw, nh), Image.LANCZOS)

        # 中央クロップで元サイズに戻す
        left = (nw - w) // 2
        top = (nh - h) // 2
        frame = frame.crop((left, top, left + w, top + h))
        frames.append(frame)

    return frames


def quantize_to_256(frame: Image.Image) -> Image.Image:
    """
    GIF向けに256色パレットへ。
    透過PNGはSNS/変換経路で崩れやすいので、互換性と容量優先で白合成→256色化。
    """
    if frame.mode == "RGBA":
        bg = Image.new("RGB", frame.size, (255, 255, 255))
        bg.paste(frame, mask=frame.split()[-1])
        frame = bg
    elif frame.mode != "RGB":
        frame = frame.convert("RGB")

    return frame.quantize(colors=GIF_COLORS, method=Image.MEDIANCUT, dither=Image.NONE)


if uploaded_file:
    try:
        with st.spinner("GIFを生成中..."):
            img = Image.open(uploaded_file)
            img.load()

            # 1) 縮小
            img = resize_max_side(img, MAX_SIDE)

            # 2) 縦長のみ左右余白で22:23へ
            img = pad_to_target_ratio_if_portrait(img)

            # 3) 余白追加で横幅が増えるので、もう一度縮小
            img = resize_max_side(img, MAX_SIDE)

            # 4) フレーム生成
            frames = make_almost_still_frames(img)

            # 5) 256色化
            qframes = [quantize_to_256(f) for f in frames]

            # 6) 保存
            do_optimize = OPTIMIZE_ALWAYS

            buf = io.BytesIO()
            qframes[0].save(
                buf,
                format="GIF",
                save_all=True,
                append_images=qframes[1:],
                duration=DURATION_MS,
                loop=0,
                disposal=2,
                optimize=do_optimize,
            )
            gif_bytes = buf.getvalue()

        size_mb = len(gif_bytes) / (1024 * 1024)
        st.success(f"GIFを生成しました（{size_mb:.2f} MB）")

        # プレビュー
        st.image(gif_bytes)

        st.download_button(
            "GIFをダウンロード",
            data=gif_bytes,
            file_name="animated.gif",
            mime="image/gif",
        )

        # 目安表示
        if size_mb >= 12:
            st.warning("ファイルが大きめです（12MB以上）。Postpone→Xで失敗する場合は MAX_SIDE を 640 に下げると改善しやすいです。")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("画像を1枚アップロードしてください。")








