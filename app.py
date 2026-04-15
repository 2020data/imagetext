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

def combine_image_text(uploaded_image, text):
    """將上傳的圖片與文字合併，並套用黃金比例排版"""
    img = Image.open(uploaded_image).convert("RGB")
    width, height = img.size

    # --- ✨ 黃金比例 (Golden Ratio) 設計 ✨ ---
    # 1. 字體大小根據圖片寬度動態調整 (設定最小為 24)
    font_size = max(int(width * 0.035), 24) 
    
    # 2. 邊距與行距採用黃金比例 1.618
    golden_ratio = 1.618
    margin = int(font_size * golden_ratio) # 上下左右邊距
    line_spacing = golden_ratio            # 行間距

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        st.error(f"❌ 找不到字體文件 '{FONT_PATH}'，將使用預設字體。")
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
    
    # 總文字高度 = (行數 * 單行高度) + (行數-1 * 行高 * 0.618的額外間距)
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
        except Exception as e:
             pass
        current_y += single_line_height * line_spacing

    return new_img

# --- 4. Streamlit 應用程序 UI ---

def main():
    st.set_page_config(page_title="圖文語音記錄器", page_icon="📸")
    st.title("📸 圖文語音記錄器")
    st.write("上傳照片、錄音（中文），自動轉文字並合成擁有黃金比例排版的卡片。")

    # --- Step 1: 圖片上傳 ---
    uploaded_image = st.file_uploader("1. 上傳照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_image:
        st.image(uploaded_image, caption="原始照片", use_column_width=True)
        st.write("---")
        st.write("2. 按下按鈕錄製中文語音（描述這張照片）")
        
        # --- Step 2: 語音輸入 ---
        audio_data = mic_recorder(
            start_prompt="🔴 按住開始錄音",
            stop_prompt="⏹️ 停止錄音",
            key="mic",
            use_container_width=True
        )

        # 當有新錄音時，進行辨識並存入 session_state
        if audio_data and "last_audio" not in st.session_state or (audio_data and st.session_state.get("last_audio") != audio_data):
            st.session_state["last_audio"] = audio_data
            try:
                text_result = transcribe_audio_bytes(audio_data['bytes'])
                now = datetime.datetime.now()
                time_prefix = now.strftime("%Y%m%d ") 
                st.session_state["transcribed_text"] = f"{time_prefix}{text_result}"
                st.success("✅ 語音辨識完成！")
            except Exception as e:
                st.error(f"❌ 語音轉文字發生錯誤: {e}")

        # --- Step 3 & 4: 編輯文字與合成 ---
        if "transcribed_text" in st.session_state:
            st.write("---")
            st.write("3. 辨識後的文字 (可手動修改)：")
            
            # 文字編輯框
            edited_text = st.text_area("修改文字描述", value=st.session_state["transcribed_text"], height=100)
            st.session_state["transcribed_text"] = edited_text # 確保更新
            
            # --- Step 5: 合成圖片 ---
            if st.button("✨ 產生拍立得圖文卡", use_container_width=True):
                with st.spinner("正在套用黃金比例合成圖片..."):
                    try:
                        combined_image = combine_image_text(uploaded_image, edited_text)
                        st.session_state["combined_image"] = combined_image
                    except Exception as e:
                        st.error(f"❌ 圖片合成發生錯誤: {e}")

            # --- Step 6: 顯示合成結果與一鍵下載 ---
            if "combined_image" in st.session_state:
                st.write("---")
                st.write("🎉 **合成結果**")
                
                # 顯示圖片
                st.image(st.session_state["combined_image"], use_column_width=True)

                # 準備下載檔案
                buf = io.BytesIO()
                st.session_state["combined_image"].save(buf, format="PNG")
                byte_im = buf.getvalue()
                now = datetime.datetime.now()
                file_name = f"photo_diary_{now.strftime('%Y%m%d_%H%M%S')}.png"

                # 直接提供下載按鈕
                st.download_button(
                    label="💾 點擊下載完整圖片",
                    data=byte_im,
                    file_name=file_name,
                    mime="image/png",
                    use_container_width=True,
                    type="primary" # 將按鈕設為主要視覺焦點
                )

if __name__ == "__main__":
    main()
