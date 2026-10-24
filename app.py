import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os
import glob
import platform

st.set_page_config(page_title="照片加註解產生器", layout="centered")

st.title("📸 照片加註解產生器")
st.markdown("上傳照片後，可在下方自動生成類似拍立得黑底白字的說明列。")

# 預設文字
default_text = "20261023 台中頂粵吉品餐廳午宴 (左起)\n李榮渵師母，莊樹汾，東海大學農學院退休施宗雄院長，許傳偉，陳榮泰、劉淑女伉儷。"

# --- 字體讀取邏輯 ---
font_dir = "fonts"
# 確保資料夾存在，若無則自動建立
if not os.path.exists(font_dir):
    os.makedirs(font_dir)

# 抓取資料夾內所有的 ttf 與 ttc 檔案
font_files = glob.glob(os.path.join(font_dir, "*.ttf")) + glob.glob(os.path.join(font_dir, "*.ttc"))
font_options = [os.path.basename(f) for f in font_files]

# --- 側邊欄：參數設定 ---
st.sidebar.header("排版與字體設定")

# 字體選擇下拉選單
if font_options:
    selected_font = st.sidebar.selectbox("選擇字體 (讀取自 fonts 資料夾)", font_options)
    font_path = os.path.join(font_dir, selected_font)
else:
    st.sidebar.warning(f"在 `{font_dir}` 資料夾中找不到字體檔 (.ttf 或 .ttc)。將嘗試使用系統預設字體。")
    font_path = None

font_size = st.sidebar.slider("文字大小", min_value=15, max_value=100, value=40)
chars_per_line = st.sidebar.slider("每行字數 (控制自動換行)", min_value=10, max_value=60, value=28)
line_spacing = st.sidebar.slider("行距", min_value=0, max_value=30, value=15)
padding = st.sidebar.slider("文字框上下留白", min_value=10, max_value=100, value=30)

# --- 主畫面：上傳與文字輸入 ---
uploaded_file = st.file_uploader("1. 請上傳照片", type=['jpg', 'jpeg', 'png'])
text = st.text_area("2. 輸入要壓在底部的文字", default_text, height=100)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_container_width=True)
    
    if st.button("✨ 生成照片", type="primary"):
        try:
            # 1. 決定字體
            font = None
            if font_path:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except IOError:
                    st.error("無法載入選擇的字體，請確認檔案是否損毀。")
            
            # 備用：系統預設字體
            if font is None:
                sys_plat = platform.system()
                try:
                    if sys_plat == "Windows":
                        font = ImageFont.truetype("msjh.ttc", font_size)
                    elif sys_plat == "Darwin":
                        font = ImageFont.truetype("PingFang.ttc", font_size)
                    else:
                        font = ImageFont.truetype("wqy-microhei.ttc", font_size) 
                except IOError:
                    st.error("無法載入系統字體！請將字體檔案上傳至 GitHub 的 `fonts` 資料夾中。")
                    st.stop()

            # 2. 處理文字換行
            lines = []
            for paragraph in text.split('\n'):
                lines.extend(textwrap.wrap(paragraph, width=chars_per_line))
            wrapped_text = '\n'.join(lines)

            # 3. 計算文字所佔用的高度
            dummy_img = Image.new('RGB', (1, 1))
            draw_dummy = ImageDraw.Draw(dummy_img)
            bbox = draw_dummy.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
            text_height = bbox[3] - bbox[1]

            img_width, img_height = image.size
            caption_height = text_height + (padding * 2)

            # 4. 建立新圖片
            new_img = Image.new('RGB', (img_width, img_height + caption_height), color='black')
            new_img.paste(image, (0, 0))

            # 5. 畫上文字
            draw = ImageDraw.Draw(new_img)
            draw.multiline_text(
                (img_width / 2, img_height + padding), 
                wrapped_text,
                fill="white",
                font=font,
                anchor="ma",
                align="center",
                spacing=line_spacing
            )

            # 6. 顯示結果並提供下載
            st.success("✅ 照片生成成功！")
            st.image(new_img, caption="生成的照片", use_container_width=True)

            buf = io.BytesIO()
            new_img.save(buf, format="JPEG", quality=95)
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 下載生成的照片",
                data=byte_im,
                file_name="event_photo_with_caption.jpg",
                mime="image/jpeg"
            )

        except Exception as e:
            st.error(f"發生錯誤: {e}")
