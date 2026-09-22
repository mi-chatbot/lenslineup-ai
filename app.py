import json
import streamlit as st
from google import genai

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Lenslineup AI Guide", page_icon="📷", layout="centered")
st.title("📷 ผู้ช่วยแนะนำกล้องเช่า (Lenslineup)")
st.markdown("สวัสดีครับ! ยินดีต้อนรับสู่ผู้ช่วย AI จากร้าน Lenslineup อาคารเอเชีย (ติด BTS ราชเทวี) พิมพ์บอกงานหรือสเปกที่อยากได้เลยครับ!")

# === ใส่ API Key ตรงนี้ (ใส่แค่ครั้งเดียวแล้วใช้ได้ตลอด) ===
api_key = st.secrets["GEMINI_API_KEY"

# โหลดแคตตาล็อกกล้อง
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json' กรุณาตรวจสอบว่ามีไฟล์นี้อยู่ในโฟลเดอร์เดียวกันกับ app.py")
    st.stop()

# คำสั่งควบคุมพฤติกรรมของ AI (อัปเดตใหม่ให้จัดหน้าสวยงาม)
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

    # เรียกใช้งาน Gemini AI
    try:
        client = genai.Client(api_key=api_key)
        
        # จัดรูปแบบประวัติแชทเพื่อส่งให้ AI
        contents = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
            for m in st.session_state.messages
        ]

        # ประมวลผลและแสดงคำตอบ
        with st.chat_message("assistant"):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={"system_instruction": system_instruction}
            )
            st.markdown(response.text)
            # บันทึกคำตอบ AI
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI: {e}")
