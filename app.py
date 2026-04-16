import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.parse
import streamlit.components.v1 as components

# --- 頁面設定 ---
st.set_page_config(page_title="老照片加字幕小工具 (Pro版)", page_icon="📸", layout="centered")

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

# --- 處理圖片的函式 (新版本) ---
def process_image(img, line1, line2, angle, font_size_mult):
    # 1. 旋轉原照片
    # expand=True 會使圖像擴大以適應旋轉後的內容，而不裁剪
    rotated_img = img.rotate(angle, expand=True)

    width, height = rotated_img.size
    
    # 動態計算底部黑框的高度 (照片高度的 15%，最小 100px)
    text_bar_height = max(int(height * 0.15), 100)
    new_height = height + text_bar_height
    
    # 建立一張包含黑底的新畫布
    new_img = Image.new('RGB', (width, new_height), 'black')
    
    # 貼上旋轉後的原圖 (居中貼上，因為 expand=True 可能會改變尺寸)
    paste_x = (new_img.width - rotated_img.width) // 2
    paste_y = 0
    new_img.paste(rotated_img, (paste_x, paste_y))
    
    # 準備畫筆與字體
    draw = ImageDraw.Draw(new_img)
    
    # 2. 計算基礎字體大小，並乘以倍率
    base_font_size = max(int(width * 0.035), 20)
    target_font_size = int(base_font_size * font_size_mult)
    font = get_chinese_font(target_font_size)
    
    # 計算文字 Y 軸位置 (在黑框內)
    text_bar_start_y = height
    text_y1 = text_bar_start_y + (text_bar_height * 0.35)
    text_y2 = text_bar_start_y + (text_bar_height * 0.7)
    
    # 寫上文字 (anchor="mm" 表示以文字正中心為對齊基準)
    if line1:
        draw.text((width / 2, text_y1), line1, font=font, fill="white", anchor="mm")
    if line2:
        draw.text((width / 2, text_y2), line2, font=font, fill="white", anchor="mm")
        
    return new_img

# --- UI 介面設計 ---
st.title("📸 照片加字幕小工具 (Pro版)")
st.write("上傳照片，自定義角度、文字大小，並生成帶有黑底白字說明的紀念照片！")

# 1. 上傳區域
uploaded_file = st.file_uploader("1. 上傳照片", type=["jpg", "jpeg", "png"])

# 2. 控件區域
st.subheader("2. 自定義設置")
col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    angle = st.slider("旋轉角度", min_value=-180, max_value=180, value=0, step=1, help="滑動以旋轉照片")
with col_ctrl2:
    font_size_mult = st.slider("文字放大縮小倍率", min_value=0.5, max_value=2.0, value=1.0, step=0.1, help="滑動以調整文字大小")

# 3. 文字輸入區域
st.subheader("3. 輸入文字")
col_text1, col_text2 = st.columns(2)
with col_text1:
    line1_text = st.text_input("第一行文字 (如時間地點)", "2026.4.13. 新新餐廳晚餐")
with col_text2:
    line2_text = st.text_input("第二行文字 (如人物介紹)", "左起：許家輔、徐令凱夫人、徐令凱。")

# 4. 處理與顯示區域
if uploaded_file is not None:
    # 讀取使用者上傳的圖片
    original_image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("預覽結果")
    
    # 產生合成圖片
    result_image = process_image(original_image, line1_text, line2_text, angle, font_size_mult)
    
    # 顯示圖片
    st.image(result_image, use_container_width=True)
    
    # 準備下載按鈕
    img_byte_arr = io.BytesIO()
    result_image.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr = img_byte_arr.getvalue()
    
    st.download_button(
        label="⬇️ 點此下載合成照片",
        data=img_byte_arr,
        file_name="我的紀念照片_custom.jpg",
        mime="image/jpeg",
        type="primary"
    )

    # 5. 分享區域
    st.markdown("---")
    st.subheader("4. 分享")
    st.write("目前 Web 應用程序無法直接分享圖片文件。您可以複製下方連結進行連結分享，或點擊社交分享按鈕。**要分享完整圖片，請先下載圖片，然後在 LINE、FB 等應用程序中附加發送。**")

    # 分享 URL 示例 (替換為你的網頁網址，如果是本地運行，這分享給其他人將無效)
    share_url = "https://your-app.streamlit.app" # 假設的託管網址
    # 用戶輸入的文字可以用作分享文本
    share_text = f"快來看看我的紀念照片！\n{line1_text}\n{line2_text}\n由「老照片加字幕小工具」製作。"
    
    # 對文字和 URL 進行 URL 編碼
    encoded_text = urllib.parse.quote(share_text)
    encoded_url = urllib.parse.quote(share_url)

    # 生成分享連結
    line_share_link = f"https://line.me/R/msg/text/?{encoded_text}%0A{encoded_url}"
    fb_share_link = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"

    # 嵌入 HTML 按鈕 (需要一些 CSS 樣式)
    html_string = f"""
    <style>
        .share-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        .share-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
            text-decoration: none;
            color: white;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .share-button:hover {{
            opacity: 0.8;
        }}
        .line {{
            background-color: #00B900;
        }}
        .facebook {{
            background-color: #1877F2;
        }}
    </style>
    
    <div class="share-buttons">
        <a href="{line_share_link}" target="_blank" class="share-button line">分享到 LINE (連結分享)</a>
        <a href="{fb_share_link}" target="_blank" class="share-button facebook">分享到 Facebook (連結分享)</a>
    </div>
    """
    
    # 顯示 HTML 分享按鈕
    components.html(html_string, height=60) # height 需要手動調整以避免滾動條
