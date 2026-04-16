import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.parse
import streamlit.components.v1 as components

# --- 頁面設定 ---
st.set_page_config(page_title="老照片加字幕小工具 (Pro版)", page_icon="📸", layout="centered")

# --- 狀態管理：初始化旋轉角度 ---
if 'angle' not in st.session_state:
    st.session_state.angle = 0

def rotate_ccw():
    """逆時針旋轉 90 度"""
    val = st.session_state.angle + 90
    st.session_state.angle = val if val <= 180 else val - 360

def rotate_cw():
    """順時針旋轉 90 度"""
    val = st.session_state.angle - 90
    st.session_state.angle = val if val >= -180 else val + 360

# --- 輔助函式：尋找中文字體 ---
def get_chinese_font(size):
    font_paths = [
        "msjh.ttc",        # Windows 微軟正黑體
        "simhei.ttf",      # Windows 黑體
        "PingFang.ttc",    # Mac 蘋方體
        "STHeiti Light.ttc", # Mac 黑體
        "NotoSansTC-Regular.otf", 
        "NotoSansTC-Regular.ttf"
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            continue
    st.warning("⚠️ 系統找不到內建的中文字體，如果文字變成方塊，請將字體檔放到同一資料夾。")
    return ImageFont.load_default()

# --- 處理圖片的函式 ---
def process_image(img, line1, line2, angle, font_size_mult):
    # 1. 旋轉原照片 (expand=True 確保旋轉後照片不被裁切)
    rotated_img = img.rotate(angle, expand=True)
    width, height = rotated_img.size
    
    # 動態計算底部黑框的高度
    text_bar_height = max(int(height * 0.15), 100)
    new_height = height + text_bar_height
    
    # 建立一張包含黑底的新畫布
    new_img = Image.new('RGB', (width, new_height), 'black')
    
    # 居中貼上旋轉後的原圖
    paste_x = (new_img.width - rotated_img.width) // 2
    paste_y = 0
    new_img.paste(rotated_img, (paste_x, paste_y))
    
    # 準備畫筆與字體
    draw = ImageDraw.Draw(new_img)
    base_font_size = max(int(width * 0.035), 20)
    target_font_size = int(base_font_size * font_size_mult)
    font = get_chinese_font(target_font_size)
    
    # 計算文字位置
    text_bar_start_y = height
    text_y1 = text_bar_start_y + (text_bar_height * 0.35)
    text_y2 = text_bar_start_y + (text_bar_height * 0.7)
    
    # 寫上文字
    if line1:
        draw.text((width / 2, text_y1), line1, font=font, fill="white", anchor="mm")
    if line2:
        draw.text((width / 2, text_y2), line2, font=font, fill="white", anchor="mm")
        
    return new_img

# --- UI 介面設計 ---
st.title("📸 照片加字幕小工具 (Pro版)")
st.write("上傳照片，自定義角度與文字大小，並生成帶有黑底白字說明的紀念照片！")

# 1. 上傳區域
uploaded_file = st.file_uploader("1. 上傳照片", type=["jpg", "jpeg", "png"])

# 2. 控件區域
st.subheader("2. 自定義設置")

# 使用欄位排版：左邊放兩個旋轉按鈕，右邊放文字放大滑桿
col_btn1, col_btn2, col_font = st.columns([1, 1, 2])
with col_btn1:
    st.button("↺ 左轉 90度", on_click=rotate_ccw, use_container_width=True)
with col_btn2:
    st.button("↻ 右轉 90度", on_click=rotate_cw, use_container_width=True)
with col_font:
    font_size_mult = st.slider("文字放大縮小倍率", min_value=0.5, max_value=2.0, value=1.0, step=0.1)

# 加入綁定 session_state 的細調滑桿
# key="angle" 會自動讀取/寫入 st.session_state.angle，與上面的按鈕完美連動
angle = st.slider("細調旋轉角度", min_value=-180, max_value=180, key="angle", step=1)

# 3. 文字輸入區域
st.subheader("3. 輸入文字")
col_text1, col_text2 = st.columns(2)
with col_text1:
    line1_text = st.text_input("第一行文字 (如時間地點)", "2026.4.16. 地點")
with col_text2:
    line2_text = st.text_input("第二行文字 (如人物介紹)", "左起：A、B、C。")

# 4. 處理與顯示區域
if uploaded_file is not None:
    original_image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("預覽結果")
    
    # 產生合成圖片
    result_image = process_image(original_image, line1_text, line2_text, angle, font_size_mult)
    st.image(result_image, use_container_width=True)
    
    # 準備下載按鈕
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

    # 5. 分享區域
    st.markdown("---")
    st.subheader("4. 分享小工具")
    st.write("如果覺得好用，可以把這個小工具分享給親朋好友！")
    st.write("*(提醒：要分享剛製作好的照片，請先點擊上方按鈕下載圖片，再到 LINE 或 Facebook 傳送圖片喔)*")

    # 更新為你指定的網址
    share_url = "https://imagetxt.streamlit.io"
    share_text = "我發現一個超好用的「照片加字幕小工具」，可以輕鬆製作像老照片一樣的黑底白字紀念照，快來試試看！"
    
    # 對文字和 URL 進行 URL 編碼
    encoded_text = urllib.parse.quote(share_text)
    encoded_url = urllib.parse.quote(share_url)

    # 生成分享連結
    line_share_link = f"https://line.me/R/msg/text/?{encoded_text}%0A{encoded_url}"
    fb_share_link = f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"

    # 嵌入 HTML 按鈕
    html_string = f"""
    <style>
        .share-buttons {{ display: flex; gap: 10px; margin-top: 10px; }}
        .share-button {{
            display: inline-flex; align-items: center; justify-content: center;
            padding: 8px 16px; border-radius: 5px; font-size: 14px;
            font-weight: bold; text-decoration: none; color: white;
            cursor: pointer; transition: opacity 0.2s; font-family: sans-serif;
        }}
        .share-button:hover {{ opacity: 0.8; }}
        .line {{ background-color: #00B900; }}
        .facebook {{ background-color: #1877F2; }}
    </style>
    <div class="share-buttons">
        <a href="{line_share_link}" target="_blank" class="share-button line">分享網址到 LINE</a>
        <a href="{fb_share_link}" target="_blank" class="share-button facebook">分享網址到 Facebook</a>
    </div>
    """
    components.html(html_string, height=60)
