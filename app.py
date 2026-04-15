import streamlit as st
from streamlit_mic_recorder import mic_recorder
import whisper
import os
import io
import datetime
from PIL import Image, ImageDraw, ImageFont

# --- 1. 項目設置與環境配置 ---
# 請確保以下文件在項目根目錄：
FONT_PATH = "NotoSansCJKtc-Regular.ttf" 

# --- 2. 加載與緩存 Whisper 模型 ---
@st.cache_resource
def load_whisper_model():
    st.info("🔄 正在加載語音辨識模型，第一次可能需要一些時間...")
    model = whisper.load_model("small")
    st.success("✅ 語音辨識模型加載完成！")
    return model

model = load_whisper_model()

# --- 3. 核心功能函數 ---

def transcribe_audio_bytes(audio_bytes):
    """將音頻位元組轉換為文字"""
    if not audio_bytes:
        return ""

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav.write(audio_bytes)
        temp_wav_path = temp_wav.name

    st.info("🔄 正在進行語音轉文字辨識...")
    result = model.transcribe(temp_wav_path, language="zh")
    os.remove(temp_wav_path)

    return result["text"]

def combine_image_text(uploaded_image, text, font_scale=1.0):
    """
    將圖片與文字合併，支援動態字體比例 (font_scale) 調整
    """
    img = Image.open(uploaded_image).convert("RGB")
    width, height = img.size

    # --- ✨ 結合黃金比例與手動縮放 ✨ ---
    # 基礎字體大小為圖片寬度的 3.5%，乘上使用者手動拉動的 scale 比例
    base_font_size = width * 0.035
    font_size = max(int(base_font_size * font_scale), 16) # 確保字體不會小於 16
    
    # 邊距與行距維持黃金比例 1.618 帶來的美感
    golden_ratio = 1.618
    margin = int(font_size * golden_ratio) 
    line_spacing = golden_ratio            

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        # 為了避免找不到字體時報錯中斷，改用 st.warning 並使用預設字體
        font = ImageFont.load_default()

    # 文字換行計算
    max_text_width = width - 2 * margin
    lines = []
    current_line = []
    current_width = 0

    def get_text_size_char(char, font_obj):
        return font_obj.getlength(char)

    for char in text:
        char_width = get_text_size_char(char, font)
        if current_width + char_width <= max_text_width:
            current_line.append(char)
            current_width += char_width
        else:
            lines.append("".join(current_line))
            current_line = [char]
            current_width = char_width
    if current_line:
        lines.append("".join(current_line))

    # 計算排版高度
    bbox = font.getbbox("測試文字") 
    single_line_height = bbox[3] - bbox[1]
    
    if len(lines) == 0:
        text_area_height = margin * 2
    else:
        total_text_height = single_line_height + (len(lines) - 1) * single_line_height * line_spacing
        text_area_height = total_text_height + 2 * margin 

    # 創建新圖片 (加上下方黑條)
    new_height = height + int(text_area_height)
    new_img = Image.new("RGB", (width, new_height), (0, 0, 0))
    new_img.paste(img, (0, 0))

    new_draw = ImageDraw.Draw(new_img)

    # 繪製文字
    current_y = height + margin
    for line in lines:
        try:
             new_draw.text((margin, current_y), line, font=font, fill=(255, 255, 255)) 
        except Exception:
             pass
        current_y += single_line_height * line_spacing

    return new_img

# --- 4. Streamlit 應用程序 UI ---

def main():
    # 設定網頁版面為寬屏模式，讓左右對照更清楚
    st.set_page_config(page_title="圖文語音記錄器", page_icon="📸", layout="wide")
    st.title("📸 語音拍立得：圖文語音記錄器")
    st.write("上傳照片並錄音，即可在下方即時預覽並微調您的專屬圖文卡。")

    # --- Step 1: 圖片上傳 ---
    uploaded_image = st.file_uploader("1. 上傳照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_image:
        st.write("---")
        st.write("2. 點擊麥克風錄製中文語音（描述這張照片）")
        
        # --- Step 2: 語音輸入 ---
        audio_data = mic_recorder(
            start_prompt="🔴 按住開始錄音",
            stop_prompt="⏹️ 停止錄音",
            key="mic",
            use_container_width=False # 縮小按鈕寬度
        )

        # 當有新錄音時，進行辨識並存入 session_state
        if audio_data and ("last_audio" not in st.session_state or st.session_state["last_audio"] != audio_data):
            st.session_state["last_audio"] = audio_data
            try:
                text_result = transcribe_audio_bytes(audio_data['bytes'])
                now = datetime.datetime.now()
                time_prefix = now.strftime("%Y%m%d ") 
                # 儲存原始辨識結果
                st.session_state["transcribed_text"] = f"{time_prefix}{text_result}"
                st.success("✅ 語音辨識完成！開始微調排版：")
            except Exception as e:
                st.error(f"❌ 語音轉文字發生錯誤: {e}")

        # --- Step 3: 即時編輯面板與預覽 ---
        # 只要 session_state 裡面有文字，就顯示編輯與預覽區塊
        if "transcribed_text" in st.session_state:
            st.write("---")
            
            # 建立左右兩欄，左邊是控制項，右邊是即時預覽
            col1, col2 = st.columns([1, 1.2]) 

            with col1:
                st.subheader("⚙️ 調整與修改")
                
                # 1. 即時文字編輯框 (綁定 session_state 的預設值)
                edited_text = st.text_area(
                    "文字描述 (可直接修改)：", 
                    value=st.session_state["transcribed_text"], 
                    height=150
                )
                
                # 2. 字體比例滑桿 (預設 1.0 倍，可調整範圍 0.5 ~ 2.5)
                font_scale = st.slider(
                    "🔠 調整字體顯示比例：", 
                    min_value=0.5, 
                    max_value=2.5, 
                    value=1.0, 
                    step=0.1
                )
                
                st.caption("💡 提示：在上方修改文字或拖拉滑桿，右側的圖片會立刻更新！")

            with col2:
                st.subheader("👀 即時預覽與下載")
                
                # 每當左側的 edited_text 或 font_scale 改變，這段程式碼就會自動重新執行並產生新圖
                with st.spinner("渲染圖片中..."):
                    try:
                        preview_image = combine_image_text(uploaded_image, edited_text, font_scale)
                        
                        # 顯示即時預覽圖
                        st.image(preview_image, use_container_width=True)

                        # 準備下載檔案
                        buf = io.BytesIO()
                        preview_image.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        now = datetime.datetime.now()
                        file_name = f"VoiceCaption_{now.strftime('%Y%m%d_%H%M%S')}.png"

                        # 下載按鈕
                        st.download_button(
                            label="📥 確認無誤，點擊下載最終圖片",
                            data=byte_im,
                            file_name=file_name,
                            mime="image/png",
                            use_container_width=True,
                            type="primary"
                        )
                    except Exception as e:
                         st.error(f"❌ 產生預覽圖時發生錯誤: {e}")

if __name__ == "__main__":
    main()
