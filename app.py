import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import whisper
import tempfile
import os
import io

# 設定頁面標題
st.set_page_config(page_title="照片語音標註工具", layout="centered")

## --- 1. 側邊欄設定 (控制項) ---
st.sidebar.header("樣式設定")
font_size = st.sidebar.slider("文字大小 (px)", 14, 60, 24)
font_style = st.sidebar.selectbox("字體粗細", ["Normal", "Bold"])
# 刪除顏色選擇器，因為範例是固定樣式（黑底白字）

## --- 2. 核心功能函數 ---

def get_font(size, is_bold):
    # 這是一個簡單的字體查找，可能需要根據系統進行調整
    # 這裡我們嘗試加載一些常見的系統中文字體
    font_paths = []
    if os.name == 'nt':  # Windows
        font_paths = [
            "C:\\Windows\\Fonts\\msyh.ttc",    # 微軟正黑體
            "C:\\Windows\\Fonts\\simsun.ttc",   # 宋體
        ]
    elif os.name == 'posix':  # macOS / Linux
        # 如果是 macOS Catalina 或更高版本，字體路徑可能不同
        possible_mac_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf", # 或者通用字體
        ]
        font_paths = possible_mac_paths + [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto Sans CJK
        ]
    
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                # Pillow 的 ImageFont 處理多字體文件 (.ttc) 時需要索引
                index = 0
                if "msyh" in path and is_bold: index = 1  # 嘗試 msyh-bold
                # 對於其他字體，粗體處理可能更複雜，這裡只做一個簡單的嘗試
                font = ImageFont.truetype(path, size, index=index)
                break
            except Exception as e:
                print(f"Error loading font {path}: {e}")
    
    if font is None:
        try:
            # 最後的嘗試，加載 PIL 默認字體，可能無法正確顯示中文
            font = ImageFont.load_default()
            st.warning("無法加載中文字體，某些字符可能無法正確顯示。")
        except Exception as e:
            st.error(f"無法加載任何字體：{e}")
    
    return font

def generate_final_image(orig_image, text, font_size_px, is_bold, padding=20):
    # 創建一個 ImageDraw 對象，用於測量
    draw = ImageDraw.Draw(orig_image)
    
    # 計算字體大小（px 轉為 pt，約為 1px = 0.75pt）
    font_size_pt = int(font_size_px * 0.75)
    font = get_font(font_size_pt, is_bold)
    
    if font is None:
        return None

    # 處理多行文字
    lines = text.split('\n')
    line_height = font.getbbox("Tg")[3] - font.getbbox("Tg")[1] # 獲取單行文字高度
    
    # 計算文字區域高度
    text_area_height = 0
    max_line_width = 0
    for line in lines:
        line_bbox = font.getbbox(line)
        line_width = line_bbox[2] - line_bbox[0]
        max_line_width = max(max_line_width, line_width)
        text_area_height += line_height + 5 # 加上一點行間距
        
    text_area_height += 2 * padding # 加上上下 padding
    
    # 創建一個新的畫布，寬度與原圖相同
    final_image_width = orig_image.width
    final_image_height = orig_image.height + text_area_height
    final_image = Image.new("RGB", (final_image_width, final_image_height), "black") # 範例背景是黑色的

    # 粘貼原圖
    final_image.paste(orig_image, (0, 0))
    
    # 準備繪製文字
    draw = ImageDraw.Draw(final_image)
    
    y_offset = orig_image.height + padding
    for line in lines:
        draw.text((padding, y_offset), line, font=font, fill="white") # 強制設為白色
        y_offset += line_height + 5
        
    return final_image

## --- 3. App 佈局 ---

st.title("📸 照片語音標註 App")
uploaded_image = st.file_uploader("請上傳一張照片", type=["jpg", "png", "jpeg"])

if uploaded_image:
    # 打開圖片並自動轉正
    image = Image.open(uploaded_image)
    image = ImageOps.exif_transpose(image) # 照片轉正
    st.image(image, use_container_width=True)

    ## --- 4. 語音輸入區 ---
    st.markdown("---")
    st.subheader("🎤 錄製或上傳語音說明")
    audio_file = st.file_uploader("上傳音檔 (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])

    # 初始化文字
    recognized_text = ""

    if audio_file:
        with st.spinner("語音辨識中，請稍候..."):
            # 將上傳的音檔寫入暫存檔以供 Whisper 讀取
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_path = tmp_file.name

            # 載入 Whisper 模型 (base 模型速度較快)
            model = whisper.load_model("base")
            # 確保使用繁體中文
            result = model.transcribe(tmp_path, language="zh", initial_prompt="繁體中文")
            recognized_text = result["text"]
            
            # 刪除暫存檔
            os.remove(tmp_path)
        
        st.success("辨識完成！")

    ## --- 5. 文字編輯與顯示 ---
    st.markdown("### 📝 標註文字內容")
    # 允許使用者手動修正辨識後的文字
    final_text = st.text_area("編輯文字", value=recognized_text, height=100)

    if final_text:
        # 根據側邊欄設定動態生成 CSS
        weight = "bold" if font_style == "Bold" else "normal"
        
        # 使用 HTML/CSS 在照片下方渲染實時文字框架
        # 為了貼近範例，將背景設為黑色，文字設為白色，並確保中文字體
        st.markdown(
            f"""
            <div style="
                background-color: black; 
                padding: 20px; 
                border-radius: 5px; 
                margin-top: 10px;
                border-left: 5px solid #ccc;
                font-family: 'Microsoft JhengHei', 'PingFang TC', sans-serif;">
                <p style="
                    font-size: {font_size}px; 
                    font-weight: {weight}; 
                    color: white; 
                    line-height: 1.5;
                    white-space: pre-wrap;">
                    {final_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        ## --- 6. 生成並下載合併圖片 ---
        st.markdown("---")
        st.subheader("⬇️ 生成最終圖片")
        
        # 處理樣式
        is_bold = True if font_style == "Bold" else False
        
        # 生成圖片
        with st.spinner("正在生成最終圖片..."):
            combined_image = generate_final_image(image, final_text, font_size, is_bold)
            
        if combined_image:
            # 將 Pillow 圖片轉為 bytes 供下載
            buf = io.BytesIO()
            # 提高 JPEG 質量以獲得更好的結果
            combined_image.save(buf, format="JPEG", quality=95)
            byte_im = buf.getvalue()
            
            # 顯示預覽
            st.image(combined_image, use_container_width=True)
            
            # 提供下載按鈕
            st.download_button(
                label="下載合併後的圖片",
                data=byte_im,
                file_name="combined_image.jpg",
                mime="image/jpeg",
            )
        else:
            st.error("圖片生成失敗。")

else:
    st.info("請先上傳照片以開始使用。")
