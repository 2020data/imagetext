import streamlit as st
from PIL import Image
import whisper
import tempfile
import os

# 設定頁面標題
st.set_page_config(page_title="照片語音標註工具", layout="centered")

## --- 1. 側邊欄設定 (控制項) ---
st.sidebar.header("樣式設定")
font_size = st.sidebar.slider("文字大小 (px)", 14, 60, 24)
font_style = st.sidebar.selectbox("字體粗細", ["Normal", "Bold"])
text_color = st.sidebar.color_picker("文字顏色", "#333333")

## --- 2. 上傳照片區 ---
st.title("📸 照片語音標註 App")
uploaded_image = st.file_uploader("請上傳一張照片", type=["jpg", "png", "jpeg"])

if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, use_container_width=True)

    ## --- 3. 語音輸入區 ---
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
            result = model.transcribe(tmp_path)
            recognized_text = result["text"]
            
            # 刪除暫存檔
            os.remove(tmp_path)
        
        st.success("辨識完成！")

    ## --- 4. 文字編輯與顯示 ---
    st.markdown("### 📝 標註文字內容")
    # 允許使用者手動修正辨識後的文字
    final_text = st.text_area("編輯文字", value=recognized_text, height=100)

    if final_text:
        # 根據側邊欄設定動態生成 CSS
        weight = "bold" if font_style == "Bold" else "normal"
        
        # 使用 HTML/CSS 在照片下方渲染文字
        st.markdown(
            f"""
            <div style="
                background-color: #f9f9f9; 
                padding: 20px; 
                border-radius: 5px; 
                margin-top: 10px;
                border-left: 5px solid #ccc;">
                <p style="
                    font-size: {font_size}px; 
                    font-weight: {weight}; 
                    color: {text_color}; 
                    line-height: 1.5;
                    white-space: pre-wrap;">
                    {final_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.info("請先上傳照片以開始使用。")
