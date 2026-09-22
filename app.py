import json
import time
import streamlit as st
from google import genai

# === 1. การตั้งค่าหน้าเว็บ ===
st.set_page_config(page_title="Lenslineup AI Guide", page_icon="📸", layout="centered")

# === 2. ตกแต่ง CSS ธีมร้าน Lenslineup (Premium Dark & Orange/Yellow) ===
st.markdown("""
    <style>
    /* นำเข้าฟอนต์ Prompt จาก Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

    /* บังคับใช้ฟอนต์ Prompt ทั้งหน้าเว็บ */
    * {
        font-family: 'Prompt', sans-serif !important;
    }

    /* ธีมหลักพื้นหลังแอป */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* ซ่อนเมนูพื้นฐานของ Streamlit ให้ดูเป็นแอปจริงๆ */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ตกแต่งหัวข้อหลัก (Title) */
    h1 {
        color: #FFB800 !important;
        text-align: center;
        font-weight: 700;
        text-shadow: 0px 4px 15px rgba(255, 184, 0, 0.2);
        padding-bottom: 10px;
    }

    /* คำอธิบายใต้หัวข้อ */
    .stMarkdown p {
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* กล่องข้อความแชทของผู้ใช้ (User) */
    div.stChatMessage[data-testid="stChatMessage-user"] {
        background-color: #242424;
        border-left: 4px solid #FFB800;
        border-radius: 8px 15px 15px 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* กล่องข้อความแชทของ AI (Assistant) */
    div.stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: #1A1A1A;
        border: 1px solid #333333;
        border-radius: 15px 8px 8px 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    /* ช่องพิมพ์ข้อความแชทด้านล่าง */
    .stChatInputContainer {
        border: 2px solid #FFB800 !important;
        border-radius: 25px !important;
        background-color: #1E1E1E !important;
        padding: 2px 10px;
    }
    
    /* ปรับสีตัวอักษรในช่องแชท */
    .stChatInputContainer textarea {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# === 3. ส่วนหัวของเว็บแอป ===
st.title("📸 Lenslineup AI Assistant")
st.markdown("<p style='text-align: center; color: #AAAAAA;'>ยินดีต้อนรับสู่ผู้ช่วย AI จากร้าน Lenslineup อาคารเอเชีย (ติด BTS ราชเทวี)<br>พิมพ์บอกงาน สเปกที่อยากได้ หรือสไตล์การถ่ายรูปได้เลยครับ!</p>", unsafe_allow_html=True)
st.divider() # เส้นคั่นสวยๆ

# === 4. ดึง API Key ===
api_key = st.secrets["GEMINI_API_KEY"]

# === 5. โหลดแคตตาล็อกกล้อง ===
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json' กรุณาตรวจสอบว่ามีไฟล์นี้อยู่ในโฟลเดอร์เดียวกันกับ app.py")
    st.stop()

# === 6. คำสั่งควบคุมพฤติกรรมของ AI ===
system_instruction = f"""
คุณคือผู้เชี่ยวชาญด้านอุปกรณ์ของร้านเช่ากล้อง Lenslineup (ร้านอยู่ชั้น 12 อาคารเอเชีย ติด BTS ราชเทวี)
หน้าที่ของคุณคือ แนะนำกล้องหรือมือถือที่เหมาะสมที่สุดให้กับลูกค้าตามความต้องการ

กฎสำคัญในการจัดรูปแบบคำตอบ (บังคับใช้ทุกครั้งให้อ่านง่ายและสวยงาม):
1. แนะนำเฉพาะรุ่นที่มีอยู่ในฐานข้อมูลด้านล่างนี้เท่านั้น ห้ามมั่วชื่อรุ่นเด็ดขาด
2. ให้จัดรูปแบบคำตอบเป็นสัดส่วน ใช้ตัวหนา (Bold) และอิโมจิ (Emoji) เพื่อให้อ่านง่ายตามโครงสร้างนี้:

   (ทักทายและเกริ่นนำสั้นๆ อย่างเป็นกันเอง)
   
   📸 **[ชื่อรุ่นกล้อง/มือถือที่แนะนำ]**
   ✨ **จุดเด่น:** [อธิบายสั้นๆ ตรงประเด็นว่าทำไมถึงตอบโจทย์ลูกค้า]
   💰 **ราคาเช่า:** [ราคา] บาท/วัน
   👉 **[คลิกเพื่อดูรายละเอียดและจองคิว](ใส่ URL ของสินค้านั้น หากไม่มีให้ใส่ https://www.lenslineup.com)**

3. หากมีหลายตัวเลือกที่ตรงใจลูกค้า สามารถแนะนำ 2-3 รุ่นเรียงเป็นข้อๆ ได้
4. ปิดท้ายด้วยคำถามสั้นๆ 1 ประโยค เพื่อให้ลูกค้าพูดคุยต่อ (เช่น ถามเรื่องงบ, ถามวันที่จะใช้งาน, หรือมีเลนส์ในใจไหม)

รายการกล้องของร้านที่มีให้เช่า:
{json.dumps(camera_catalog, ensure_ascii=False, indent=2)}
"""

# === 7. จัดการ State ประวัติแชท ===
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงข้อความแชทเดิมพร้อม Avatar ประจำตัว
for msg in st.session_state.messages:
    avatar_icon = "🧑‍💻" if msg["role"] == "user" else "📸"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# === 8. รอรับข้อความใหม่จากผู้ใช้ ===
if user_input := st.chat_input("พิมพ์บอกงานที่ต้องการนำกล้องไปใช้ หรือสเปก/งบประมาณได้เลย..."):
    
    # บันทึกข้อความผู้ใช้
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # เรียกใช้งาน Gemini AI พร้อมระบบลองใหม่ (Retry)
    with st.chat_message("assistant", avatar="📸"):
        message_placeholder = st.empty()
        success = False
        response_text = ""
        
        for attempt in range(3):
            try:
                client = genai.Client(api_key=api_key)
                
                contents = [
                    {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                    for m in st.session_state.messages
                ]

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents,
                    config={"system_instruction": system_instruction}
                )
                response_text = response.text
                success = True
                break
            except Exception as e:
                error_str = str(e)
                if "503" in error_str or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < 2:
                        message_placeholder.info(f"⏳ เซิร์ฟเวอร์กำลังประมวลผล กรุณารอสักครู่ (กำลังลองใหม่ครั้งที่ {attempt + 1})...")
                        time.sleep(3)
                        continue
                response_text = f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}"
                break

        if success:
            message_placeholder.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            message_placeholder.error(response_text)
