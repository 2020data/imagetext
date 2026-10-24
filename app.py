import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

st.set_page_config(page_title="照片加註解產生器", layout="centered")

st.title("📸 照片加註解產生器")
st.markdown("上傳照片後，可在下方自動生成類似拍立得黑底白字的說明列。")

# 預設文字
default_text = "20261023 台中頂粵吉品餐廳午宴 (左起)\n李榮渵師母，莊樹汾，東海大學農學院退休施宗雄院長，許傳偉，陳榮泰、劉淑女伉儷。"

# --- 強化版：字體讀取邏輯 ---
# 取得目前 app.py 所在的絕對路徑，避免 Streamlit Cloud 路徑迷航
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 自動搜尋整個專案目錄下所有的字體檔 (不論放在根目錄、fonts 資料夾或子資料夾，且不限大小寫)
font_dict = {}
for root, dirs, files in os.walk(BASE_DIR):
    # 略過隱藏資料夾 (例如 .git)
    if '.git' in root:
        continue
    for file in files:
        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
            full_path = os.path.join(root, file)
            font_dict[file] = full_path

# --- 側邊欄：參數設定 ---
st.sidebar.header("排版與字體設定")

font_source = None

if font_dict:
    # 排序字體名稱，讓選單更整齊
    font_names = sorted(list(font_dict.keys()))
    selected_font_name = st.sidebar.selectbox("選擇字體 (自動掃描專案)", font_names)
    selected_font_path = font_dict[selected_font_name]
    
    # 檢查檔案大小，防範 GitHub LFS 指標檔或損毀檔 (小於 10KB 通常不是正常中文字體)
    file_size_kb = os.path.getsize(selected_font_path) / 1024
    if file_size_kb < 10:
        st.sidebar.error(f"⚠️ `{selected_font_name}` 檔案大小僅 {file_size_kb:.1f} KB，檔案可能未完整上傳至 GitHub (或變成了 Git LFS 捷徑)。")
    else:
        st.sidebar.caption(f"📄 字體大小: {file_size_kb / 1024:.2f} MB")
    
    font_source = selected_font_path
else:
    st.sidebar.warning("⚠️ 在 GitHub 專案中找不到任何字體檔 (.ttf/.ttc/.otf)。")

# 備用救援方案：允許直接從網頁上傳字體檔測試
uploaded_font = st.sidebar.file_uploader(
    "或者：手動從電腦上傳字體檔 (.ttf/.otf)", 
    type=['ttf', 'ttc', 'otf'],
    help="若 GitHub 字體讀取失敗，可直接從這裡上傳電腦裡的字體檔應急使用"
)
if uploaded_font is not None:
    font_source = uploaded_font
    st.sidebar.success(f"已載入手動上傳字體：{uploaded_font.name}")

font_size = st.sidebar.slider("文字大小", min_value=15, max_value=100, value=40)
chars_per_line = st.sidebar.slider("每行字數 (控制自動換行)", min_value=10, max_value=60, value=28)
line_spacing = st.sidebar.slider("行距", min_value=0, max_value=30, value=15)
padding = st.sidebar.slider("文字框上下留白", min_value=10, max_value=100, value=30)

# --- 主畫面：上傳與文字輸入 ---
uploaded_file = st.file_uploader("1. 請上傳照片", type=['jpg', 'jpeg', 'png'])
text = st.text_area("2. 輸入要壓在底部的文字", default_text, height=100)

if uploaded_file is not None:
    # 轉為 RGB 避免 PNG 透明背景貼上時報錯
    image = Image.open(uploaded_file).convert('RGB')
    st.image(image, caption="原始照片", use_container_width=True)
    
    if st.button("✨ 生成照片", type="primary"):
        try:
            # 1. 載入字體
            font = None
            if font_source is not None:
                try:
                    if isinstance(font_source, str):
                        # 從 GitHub 檔案路徑載入
                        font = ImageFont.truetype(font_source, font_size)
                    else:
                        # 從網頁手動上傳的記憶體載入
                        font_bytes = io.BytesIO(font_source.getvalue())
                        font = ImageFont.truetype(font_bytes, font_size)
                except Exception as font_err:
                    st.error(f"❌ 載入字體失敗，詳細錯誤原因：`{font_err}`")
                    st.info("💡 解決方法：請確認 GitHub 上的字體檔案大小是否正常（中文字體通常為 5MB~20MB），或先使用左側邊欄的「手動從電腦上傳字體檔」功能。")
                    st.stop()
            else:
                st.error("❌ 尚未選擇任何字體！請確認 GitHub 中有字體檔，或從左側邊欄手動上傳 `.ttf` 字體檔。")
                st.stop()

            # 2. 處理文字換行
            lines = []
            for paragraph in text.split('\n'):
                if paragraph.strip() == "":
                    lines.append("")
                else:
                    lines.extend(textwrap.wrap(paragraph, width=chars_per_line))
            wrapped_text = '\n'.join(lines)

            # 3. 計算文字所佔用的高度
            dummy_img = Image.new('RGB', (1, 1))
            draw_dummy = ImageDraw.Draw(dummy_img)
            bbox = draw_dummy.multiline_textbbox((0, 0), wrapped_text, font=font, spacing=line_spacing)
            text_height = bbox[3] - bbox[1]

            img_width, img_height = image.size
            caption_height = int(text_height + (padding * 2))

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
