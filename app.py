import json
import time
import streamlit as st
from google import genai

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Lenslineup AI Guide", page_icon="📷", layout="centered")

# ตกแต่ง CSS ธีม ดำ-ส้ม แบบ Premium Tech
st.markdown("""
    <style>
    /* ธีมหลักพื้นหลังแอป */
    .stApp {
        background-color: #0e0e0e;
        color: #f3f4f6;
    }
    
    /* จัดแต่งหัวข้อหลัก */
    h1 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* ปรับแต่งกล่องข้อความแชทของผู้ใช้ (User) */
    div.stChatMessage[data-testid="stChatMessage-user"] {
        background-color: #1f1f1f;
        border: 1px solid #ff7a00;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(255, 122, 0, 0.1);
    }

    /* ปรับแต่งกล่องข้อความแชทของ AI (Assistant) */
    div.stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: #161616;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    /* ช่องพิมพ์ข้อความแชทด้านล่าง */
    .stChatInputContainer {
        border-radius: 12px;
        border: 1px solid #ff7a00 !important;
        background-color: #161616;
    }
    
    /* ปรับสีปุ่มกดต่างๆ ให้เป็นส้ม Accent */
    .stButton button {
        background-color: #ff7a00;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #e56d00;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📷 ผู้ช่วยแนะนำกล้องเช่า (Lenslineup)")
st.markdown("สวัสดีครับ! ยินดีต้อนรับสู่ผู้ช่วย AI จากร้าน Lenslineup อาคารเอเชีย (ติด BTS ราชเทวี) พิมพ์บอกงานหรือสเปกที่อยากได้เลยครับ!")

# === ดึง API Key จาก Streamlit Secrets ===
api_key = st.secrets["GEMINI_API_KEY"]

# โหลดแคตตาล็อกกล้อง
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json' กรุณาตรวจสอบว่ามีไฟล์นี้อยู่ในโฟลเดอร์เดียวกันกับ app.py")
    st.stop()

# คำสั่งควบคุมพฤติกรรมของ AI
system_instruction = f"""
คุณคือผู้เชี่ยวชาญด้านอุปกรณ์ของร้านเช่ากล้อง Lenslineup (ร้านอยู่ชั้น 12 อาคารเอเชีย ติด BTS ราชเทวี)
หน้าที่ของคุณคือ แนะนำกล้องหรือมือถือที่เหมาะสมที่สุดให้กับลูกค้าตามความต้องการ

กฎสำคัญในการจัดรูปแบบคำตอบ (บังคับใช้ทุกครั้งให้อ่านง่ายและสวยงาม):
1. แนะนำเฉพาะรุ่นที่มีอยู่ในฐานข้อมูลด้านล่างนี้เท่านั้น ห้ามมั่วชื่อรุ่นเด็ดขาด
2. ให้จัดรูปแบบคำตอบเป็นสัดส่วน ใช้ตัวหนา (Bold) และอิโมจิ (Emoji) เพื่อให้อ่านง่ายตามโครงสร้างนี้:

   (ทักทายและเกริ่นนำสั้นๆ)
   
   📷 **[ชื่อรุ่นกล้อง/มือถือที่แนะนำ]**
   ✨ **จุดเด่น:** [อธิบายสั้นๆ ตรงประเด็นว่าทำไมถึงตอบโจทย์ลูกค้า]
   💰 **ราคาเช่า:** [ราคา] บาท/วัน
   👉 **[คลิกดูรายละเอียดและจองอุปกรณ์นี้บน Lenslineup](ใส่ URL ของสินค้านั้น หากในระบบไม่มี URL ให้ใส่ https://www.lenslineup.com แทน)**

3. หากมีหลายตัวเลือกที่ตรงใจลูกค้า สามารถแนะนำ 2-3 รุ่นเรียงเป็นข้อๆ ได้
4. ปิดท้ายด้วยคำถามสั้นๆ 1 ประโยค เพื่อให้ลูกค้าพูดคุยต่อ (เช่น ถามเรื่องงบ, ถามวันที่จะใช้งาน)

รายการกล้องของร้านที่มีให้เช่า:
{json.dumps(camera_catalog, ensure_ascii=False, indent=2)}
"""

# จัดการ State ประวัติแชท
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงข้อความแชทเดิม
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# รอรับข้อความใหม่จากผู้ใช้
if user_input := st.chat_input("บอกงานที่ต้องการนำกล้องไปใช้ หรือสเปก/งบประมาณได้เลย..."):
    # บันทึกข้อความผู้ใช้
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # เรียกใช้งาน Gemini AI พร้อมระบบลองใหม่ (Retry) ป้องกันเซิร์ฟเวอร์หนาแน่น
    with st.chat_message("assistant"):
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
                        message_placeholder.info(f"⏳ เซิร์ฟเวอร์กำลังหนาแน่นหรือติดโควต้าชั่วคราว กำลังลองเชื่อมต่อใหม่อัตโนมัติ (ครั้งที่ {attempt + 1})...")
                        time.sleep(3)
                        continue
                response_text = f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI: {e}"
                break

        if success:
            message_placeholder.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            message_placeholder.error(response_text)
