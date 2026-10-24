import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import os

# 改為 wide 寬螢幕模式，方便左右並排對比
st.set_page_config(page_title="照片加註解產生器", layout="wide")

st.title("📸 照片加註解產生器 (即時預覽版)")
st.markdown("上傳照片後，調整左側設定或修改文字，右側將**即時顯示**修改成果與原圖對比。")

# 預設文字
default_text = "這是一個測試照片用，可以自動修改文字大小與選擇字體。"

# --- 強化版：字體讀取邏輯 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

font_dict = {}
for root, dirs, files in os.walk(BASE_DIR):
    if '.git' in root:
        continue
    for file in files:
        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
            full_path = os.path.join(root, file)
            font_dict[file] = full_path

# --- 側邊欄：即時排版與字體設定 ---
st.sidebar.header("🎨 即時排版設定")

font_source = None

if font_dict:
    font_names = sorted(list(font_dict.keys()))
    selected_font_name = st.sidebar.selectbox("選擇字體 (自動掃描專案)", font_names)
    selected_font_path = font_dict[selected_font_name]
    
    file_size_kb = os.path.getsize(selected_font_path) / 1024
    if file_size_kb < 10:
        st.sidebar.error(f"⚠️ `{selected_font_name}` 僅 {file_size_kb:.1f} KB，可能損毀或未完整上傳。")
    else:
        st.sidebar.caption(f"📄 字體大小: {file_size_kb / 1024:.2f} MB")
    
    font_source = selected_font_path
else:
    st.sidebar.warning("⚠️ 專案中找不到字體檔 (.ttf/.ttc/.otf)。")

uploaded_font = st.sidebar.file_uploader(
    "手動從電腦上傳字體檔 (.ttf/.otf)", 
    type=['ttf', 'ttc', 'otf'],
    help="若 GitHub 字體讀取失敗，可直接從這裡上傳電腦裡的字體檔"
)
if uploaded_font is not None:
    font_source = uploaded_font
    st.sidebar.success(f"已套用手動上傳字體：{uploaded_font.name}")

# 滑桿設定 (只要拉動滑桿，網頁就會自動重新運算並更新預覽圖)
font_size = st.sidebar.slider("文字大小", min_value=15, max_value=120, value=42)
chars_per_line = st.sidebar.slider("每行字數 (控制自動換行)", min_value=10, max_value=60, value=24)
line_spacing = st.sidebar.slider("行距", min_value=0, max_value=50, value=15)
padding = st.sidebar.slider("文字框上下留白", min_value=10, max_value=150, value=35)

# --- 主畫面：上傳與文字輸入 ---
col_input1, col_input2 = st.columns([1, 2])
with col_input1:
    uploaded_file = st.file_uploader("1. 請上傳照片", type=['jpg', 'jpeg', 'png'])
with col_input2:
    text = st.text_area("2. 輸入要壓在底部的文字 (修改後按 Ctrl+Enter 或點擊框外即可即時更新)", default_text, height=110)

# --- 即時生成與左右對比顯示 ---
if uploaded_file is not None:
    st.divider()
    image = Image.open(uploaded_file).convert('RGB')
    
    # 建立左右兩欄，用來放「原始照片」與「即時預覽結果」
    col_orig, col_preview = st.columns(2)
    
    with col_orig:
        st.subheader("🖼️ 原始照片")
        st.image(image, use_container_width=True)
        
    with col_preview:
        st.subheader("✨ 即時修改預覽")
        
        if font_source is None:
            st.error("❌ 尚未載入任何字體！請確認 GitHub 中有字體檔，或從左側邊欄手動上傳 `.ttf` 字體檔。")
        else:
            try:
                # 1. 載入字體
                if isinstance(font_source, str):
                    font = ImageFont.truetype(font_source, font_size)
                else:
                    font_bytes = io.BytesIO(font_source.getvalue())
                    font = ImageFont.truetype(font_bytes, font_size)

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

                # 4. 建立新圖片並貼上原圖
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

                # 6. 即時顯示結果與下載按鈕
                st.image(new_img, use_container_width=True)

                buf = io.BytesIO()
                new_img.save(buf, format="JPEG", quality=95)
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="📥 滿意嗎？點此下載生成照片",
                    data=byte_im,
                    file_name="event_photo_with_caption.jpg",
                    mime="image/jpeg",
                    type="primary",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ 生成預覽時發生錯誤：`{e}`")
