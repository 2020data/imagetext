import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import platform

st.set_page_config(page_title="照片加註解產生器", layout="centered")

st.title("📸 照片加註解產生器")
st.markdown("上傳照片後，可在下方自動生成類似拍立得黑底白字的說明列。")

# 預設文字 (根據您的需求已經將「苗加三點水」更正為「渵」，並參考了圖2的文案)
default_text = "圖片文字自動換行測試。"

# 側邊欄：參數設定
st.sidebar.header("排版設定")
font_size = st.sidebar.slider("文字大小", min_value=15, max_value=100, value=40)
chars_per_line = st.sidebar.slider("每行字數 (控制自動換行)", min_value=10, max_value=60, value=28)
line_spacing = st.sidebar.slider("行距", min_value=0, max_value=30, value=15)
padding = st.sidebar.slider("文字框上下留白", min_value=10, max_value=100, value=30)

font_path_input = st.sidebar.text_input(
    "自訂字體檔案路徑 (留空則自動偵測系統字體)", 
    help="若中文顯示為方塊，請將中文字體 (如 font.ttf) 放在同資料夾並輸入檔名"
)

# 主畫面：上傳與文字輸入
uploaded_file = st.file_uploader("1. 請上傳照片", type=['jpg', 'jpeg', 'png'])
text = st.text_area("2. 輸入要壓在底部的文字", default_text, height=100)

if uploaded_file is not None:
    # 顯示原圖
    image = Image.open(uploaded_file)
    st.image(image, caption="原始照片", use_container_width=True)
    
    if st.button("✨ 生成照片", type="primary"):
        try:
            # 1. 決定字體
            font = None
            if font_path_input:
                try:
                    font = ImageFont.truetype(font_path_input, font_size)
                except IOError:
                    st.error("找不到您指定的字體檔，將嘗試使用系統預設。")
            
            if font is None:
                sys_plat = platform.system()
                try:
                    if sys_plat == "Windows":
                        font = ImageFont.truetype("msjh.ttc", font_size)  # 微軟正黑體
                    elif sys_plat == "Darwin":
                        font = ImageFont.truetype("PingFang.ttc", font_size)  # Mac 蘋方體
                    else:
                        # Linux 預設抓取
                        font = ImageFont.truetype("wqy-microhei.ttc", font_size) 
                except IOError:
                    st.error("無法載入系統中文字體！請手動下載 .ttf 中文字體檔，並在左側欄位輸入其檔名。")
                    st.stop()

            # 2. 處理文字換行
            lines = []
            for paragraph in text.split('\n'):
                # 使用 textwrap 自動把過長的句子截斷換行
                lines.extend(textwrap.wrap(paragraph, width=chars_per_line))
            wrapped_text = '\n'.join(lines)

            # 3. 計算文字所佔用的高度
            dummy_img = Image.new('RGB', (1, 1))
            draw_dummy = ImageDraw.Draw(dummy_img)
            bbox = draw_dummy.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
            text_height = bbox[3] - bbox[1]

            img_width, img_height = image.size
            caption_height = text_height + (padding * 2)

            # 4. 建立新圖片 (寬度不變，高度為：原圖高度 + 黑底文字區高度)
            new_img = Image.new('RGB', (img_width, img_height + caption_height), color='black')
            
            # 將原圖貼在上方 (0, 0)
            new_img.paste(image, (0, 0))

            # 5. 在黑色區域畫上白色文字
            draw = ImageDraw.Draw(new_img)
            draw.multiline_text(
                (img_width / 2, img_height + padding),  # 座標起點(水平置中，垂直為原圖底部往下加 padding)
                wrapped_text,
                fill="white",                           # 字體顏色
                font=font,
                anchor="ma",                            # 置中對齊基準點 (middle-ascender)
                align="center",                         # 多行文字置中
                spacing=line_spacing                    # 行距
            )

            # 6. 顯示結果並提供下載
            st.success("✅ 照片生成成功！")
            st.image(new_img, caption="生成的照片", use_container_width=True)

            # 將 PIL Image 轉換為 byte 以便下載
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
