import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- 頁面設定 ---
st.set_page_config(page_title="老照片加字幕小工具", page_icon="📸", layout="centered")

# --- 輔助函式：尋找中文字體 ---
def get_chinese_font(size):
    """
    嘗試尋找系統中可用的中文字體。
    如果都找不到，請將字體檔（如 msjh.ttc 或 NotoSansTC.ttf）放在與 app.py 同一個資料夾，
    並將檔名加到下方清單中。
    """
    font_paths = [
        "msjh.ttc",        # Windows 微軟正黑體
        "simhei.ttf",      # Windows 黑體
        "PingFang.ttc",    # Mac 蘋方體
        "STHeiti Light.ttc", # Mac 黑體
        "NotoSansTC-Regular.otf", # 常見下載字體
        "NotoSansTC-Regular.ttf"
    ]
    
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            continue
            
    # 如果真的找不到，回傳預設（注意：預設字體無法顯示中文，會變成方塊）
    st.warning("⚠️ 系統找不到內建的中文字體，如果文字變成方塊，請將字體檔(如 msjh.ttc) 放到同一資料夾。")
    return ImageFont.load_default()

# --- 處理圖片的函式 ---
def process_image(img, line1, line2):
    width, height = img.size
    
    # 動態計算底部黑框的高度 (照片高度的 15%，最小 100px)
    text_bar_height = max(int(height * 0.15), 100)
    new_height = height + text_bar_height
    
    # 建立一張包含黑底的新畫布
    new_img = Image.new('RGB', (width, new_height), 'black')
    
    # 貼上原圖
    new_img.paste(img, (0, 0))
    
    # 準備畫筆與字體
    draw = ImageDraw.Draw(new_img)
    font_size = max(int(width * 0.035), 20)
    font = get_chinese_font(font_size)
    
    # 計算文字 Y 軸位置 (在黑框內)
    text_y1 = height + (text_bar_height * 0.35)
    text_y2 = height + (text_bar_height * 0.7)
    
    # 寫上文字 (anchor="mm" 表示以文字正中心為對齊基準)
    # 第一行
    if line1:
        draw.text((width / 2, text_y1), line1, font=font, fill="white", anchor="mm")
    # 第二行
    if line2:
        draw.text((width / 2, text_y2), line2, font=font, fill="white", anchor="mm")
        
    return new_img

# --- UI 介面設計 ---
st.title("📸 照片加字幕小工具")
st.write("上傳照片並輸入資訊，一鍵產生帶有經典黑底白字說明的紀念照片！")

# 1. 上傳區域
uploaded_file = st.file_uploader("1. 上傳照片", type=["jpg", "jpeg", "png"])

# 2. 文字輸入區域
col1, col2 = st.columns(2)
with col1:
    line1_text = st.text_input("第一行文字 (如時間地點)", "2026.4.13. 新新餐廳晚餐")
with col2:
    line2_text = st.text_input("第二行文字 (如人物介紹)", "左起：許家輔、徐令凱夫人、徐令凱。")

# 3. 處理與顯示區域
if uploaded_file is not None:
    # 讀取使用者上傳的圖片
    original_image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("預覽結果")
    
    # 產生合成圖片
    result_image = process_image(original_image, line1_text, line2_text)
    
    # 顯示圖片
    st.image(result_image, use_container_width=True)
    
    # 準備下載按鈕
    # 將 PIL Image 轉換為可下載的位元組流 (BytesIO)
    img_byte_arr = io.BytesIO()
    result_image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr = img_byte_arr.getvalue()
    
    st.download_button(
        label="⬇️ 點此下載合成照片",
        data=img_byte_arr,
        file_name="我的紀念照片.jpg",
        mime="image/jpeg",
        type="primary"
    )
