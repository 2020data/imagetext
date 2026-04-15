import streamlit as st
from streamlit_mic_recorder import mic_recorder
import whisper
import os
import io
import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# --- 1. 項目設置與環境配置 ---
# 請確保以下文件在項目根目錄：
FONT_PATH = "NotoSansCJKtc-Regular.ttf" 

# --- 2. 加載與緩存 Whisper 模型 ---
# 模型很大，應該緩存以避免每次呼叫都重新加載
@st.cache_resource
def load_whisper_model():
    # 根據您的系統性能，選擇模型大小: "base", "small", "medium", "large"
    # 對於 Streamlit，"small" 是一個不錯的平衡點。
    st.info("🔄 正在加載語音辨識模型，第一次可能需要一些時間...")
    model = whisper.load_model("small")
    st.success("✅ 語音辨識模型加載完成！")
    return model

model = load_whisper_model()

# --- 3. 核心功能函數 ---

def transcribe_audio_bytes(audio_bytes):
    """
    將音頻位元組轉換為文字。
    """
    if not audio_bytes:
        return ""

    # Whisper 需要一個文件路徑或 numpy 數組。
    # 為了簡便和可靠，我們將位元組寫入臨時文件。
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav.write(audio_bytes)
        temp_wav_path = temp_wav.name

    # 使用 Whisper 進行轉錄，設定語言為繁體中文 ("zh")
    st.info("🔄 正在進行語音轉文字辨識...")
    result = model.transcribe(temp_wav_path, language="zh")

    # 刪除臨時文件
    os.remove(temp_wav_path)

    return result["text"]

def combine_image_text(uploaded_image, text):
    """
    將上傳的圖片與文字合併成一張新的圖片（黑底白字在下方）。
    """
    # 打開原始圖片並轉換為 RGB (以防止 GIF 或灰度圖錯誤)
    img = Image.open(uploaded_image).convert("RGB")
    width, height = img.size

    # 文字設置
    font_size = 40 # 默認字體大小
    margin = 40 # 邊距
    line_spacing = 1.2 # 行間距

    # 載入字體 (如果找不到，請檢查 FONT_PATH)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        st.error(f"❌ 找不到字體文件 '{FONT_PATH}'。請確保它在項目目錄下，且文件名正確。將使用不支持中文的默認字體。")
        font = ImageFont.load_default()

    # 文字大小和換行計算
    max_text_width = width - 2 * margin
    lines = []
    current_line = []
    current_width = 0

    # 一個支持中文的簡單逐字符換行算法
    def get_text_size_char(char, font_obj):
        # 獲取單個字符的寬度。
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

    # 計算所需的黑條總高度
    # 獲取單行高度
    bbox = font.getbbox("測試文字") # 獲取“測試文字”的邊框，bbox[3]-bbox[1] 為高度
    single_line_height = bbox[3] - bbox[1]
    
    total_text_height = len(lines) * single_line_height * line_spacing
    text_area_height = total_text_height + 2 * margin # 加上上下邊距

    # 創建一個新的圖片，底部有黑條
    new_height = height + int(text_area_height)
    new_img = Image.new("RGB", (width, new_height), (0, 0, 0)) # 黑底
    new_img.paste(img, (0, 0)) # 貼上原始圖片

    new_draw = ImageDraw.Draw(new_img) # 在新圖片上繪製

    # 在黑條上繪製文字
    current_y = height + margin
    for line in lines:
        try:
             # new_draw.text((margin, current_y), line, font=font, fill=(255, 255, 255)) # 白字
             # 使用文本邊框在黑條上繪製文字
             new_draw.text((margin, current_y), line, font=font, fill=(255, 255, 255)) 
        except Exception as e:
             st.warning(f"⚠️ 繪製文字時發生錯誤：{e}")

        current_y += single_line_height * line_spacing

    return new_img

# --- 4. Streamlit 應用程序 UI ---

def main():
    st.set_page_config(page_title="圖文語音記錄器", page_icon="📸")

    st.title("📸 圖文語音記錄器")
    st.write("上傳照片、錄音（中文），自動轉文字並合成一張帶有說明的卡片。')

    # --- Step 1: 圖片上傳 ---
    uploaded_image = st.file_uploader("1. 上傳照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_image:
        # 顯示上傳的圖片
        st.image(uploaded_image, caption="您的照片", use_column_width=True)

        # --- Step 2: 語音輸入 ---
        st.write("---")
        st.write("2. 按下按鈕錄製中文語音（描述這張照片）")
        audio_data = mic_recorder(
            start_prompt="🔴 按下開始錄音",
            stop_prompt="⏹️ 按下停止錄音",
            key="mic",
            use_container_width=True
        )

        if audio_data:
            # 顯示錄音 (可選，供用戶試聽)
            # st.audio(audio_data['bytes'])

            # --- Step 3: 語音轉文字 ---
            try:
                text_result = transcribe_audio_bytes(audio_data['bytes'])
                
                # 自動添加一個時間前綴
                now = datetime.datetime.now()
                time_prefix = now.strftime("%Y%m%d ") # 用戶範例中的日期格式
                
                final_text = f"{time_prefix}{text_result}"
                
                st.session_state["transcribed_text"] = final_text
                st.success("✅ 語音辨識完成！")
            except Exception as e:
                st.error(f"❌ 語音轉文字發生錯誤: {e}")
                return

            # --- Step 4: 顯示與編輯文字 (重要！) ---
            # 因為 Whisper 對人名、地名可能不精確，必須讓用戶可以編輯。
            if "transcribed_text" in st.session_state:
                st.write("---")
                st.write("3. 辨識後的文字 (您可以修改如下)：")
                
                # 使用 text_area 讓用戶編輯
                edited_text = st.text_area("修改文字描述", value=st.session_state["transcribed_text"], height=150)
                
                # --- Step 5: 合成圖片 ---
                st.write("---")
                if st.button("4. 點選合成圖片"):
                    with st.spinner("正在合成圖片..."):
                        try:
                            combined_image = combine_image_text(uploaded_image, edited_text)
                            st.session_state["combined_image"] = combined_image
                            st.success("✅ 圖片合成完成！")
                        except Exception as e:
                            st.error(f"❌ 圖片合成發生錯誤: {e}")

                # --- Step 6: 顯示合成結果與下載 ---
                if "combined_image" in st.session_state:
                    st.write("---")
                    st.write("5. 合成結果與下載")
                    st.image(st.session_state["combined_image"], caption="合成後的圖文卡片", use_column_width=True)

                    # 準備下載 (將 Pillow Image 轉換為位元組)
                    buf = io.BytesIO()
                    st.session_state["combined_image"].save(buf, format="PNG")
                    byte_im = buf.getvalue()

                    # 創建文件名，包含時間戳
                    file_name = f"photo_diary_{now.strftime('%Y%m%d_%H%M%S')}.png"

                    st.download_button(
                        label="💾 點選下載合成後的圖片",
                        data=byte_im,
                        file_name=file_name,
                        mime="image/png"
                    )

if __name__ == "__main__":
    main()
