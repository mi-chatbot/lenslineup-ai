import json
import time
import streamlit as st
from google import genai

# === 1. การตั้งค่าหน้าเว็บและ CSS ธีม ดำ-ส้ม (Responsive) ===
st.set_page_config(page_title="Lenslineup AI Guide", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Prompt', sans-serif !important; }
    
    /* ธีมหลักพื้นหลังแอป */
    .stApp { background-color: #121212; color: #E0E0E0; }
    
    /* ซ่อนเมนูขยะของ Streamlit */
    header, #MainMenu, footer, .viewerBadge_container__1QSob { visibility: hidden !important; display: none !important; }
    
    /* ปรับระยะขอบหน้าจอสำหรับมือถือ */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 800px;
    }

    h1, h2 { color: #FFB800 !important; font-weight: 700; text-align: center; }
    
    /* ตกแต่งปุ่มกดใหญ่ (CTA) หน้าแรก */
    .stButton>button {
        background-color: #FFB800 !important;
        color: #121212 !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 12px 24px !important;
        width: 100%;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(255, 184, 0, 0.3);
    }
    .stButton>button:hover { background-color: #FF9933 !important; transform: translateY(-2px); }

    /* กล่องข้อความแชท */
    div.stChatMessage[data-testid="stChatMessage-user"] {
        background-color: #242424; border-left: 4px solid #FFB800; border-radius: 8px 15px 15px 8px; padding: 12px 15px; margin-bottom: 12px;
    }
    div.stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: #1A1A1A; border: 1px solid #333; border-radius: 15px 8px 8px 15px; padding: 12px 15px; margin-bottom: 12px;
    }

    /* ช่องพิมพ์แชท */
    .stChatInputContainer {
        border: 2px solid #FFB800 !important; border-radius: 25px !important; background-color: #1E1E1E !important; padding: 2px 10px;
    }
    .stChatInputContainer textarea { color: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# === 2. โหลดข้อมูล API และ แคตตาล็อก ===
api_key = st.secrets["GEMINI_API_KEY"]
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json'")
    st.stop()

# === 3. ระบบจัดการหน้า (Home -> Chat) ===
if "step" not in st.session_state:
    st.session_state.step = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []

def go_to_chat(): st.session_state.step = "chat"

# ==========================================
# หน้าที่ 1: หน้าแรก (Home)
# ==========================================
if st.session_state.step == "home":
    st.markdown("<h1 style='font-size: clamp(2.2rem, 6vw, 3rem); margin-bottom: 0;'>📸 Lenslineup AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #FFFFFF !important; font-weight: 400; font-size: 1.1rem; text-align: center; margin-top: 5px;'>ผู้ช่วยอัจฉริยะค้นหากล้องที่ใช่สำหรับคุณ</h3>", unsafe_allow_html=True)
    st.write("")
    
    # กรอบ Visual สวยๆ ดึงดูดสายตา
    st.markdown("""
        <div style='background-color: #1E1E1E; padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #333; margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.5);'>
            <h1 style='font-size: 4.5rem; margin: 0;'>✨🤖📷</h1>
            <p style='color: #AAA; font-size: 1rem; margin-top: 15px; line-height: 1.5;'>
                แค่บอกว่าคุณอยากนำกล้องไปทำอะไร<br>ไปเที่ยว, คอนเสิร์ต, VLOG หรือถ่ายงานจริงจัง<br>AI ของเราจะคัดเลือกรุ่นที่ใช่ที่สุดให้คุณทันที!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.button("💬 เริ่มคุยกับ AI เลย", on_click=go_to_chat)

# ==========================================
# หน้าที่ 2: หน้าแชท AI (Chat)
# ==========================================
elif st.session_state.step == "chat":
    # ส่วนหัว (เอาปุ่มออก และเพิ่มคำโปรยให้หน้าไม่โล่ง)
    st.markdown("""
        <div style="text-align: center; margin-bottom: 10px;">
            <h2 style='color: #FFB800; margin-bottom: 5px; font-size: 1.8rem;'>✨ Lenslineup AI</h2>
            <p style='color: #AAAAAA; font-size: 0.95rem; margin: 0;'>ตามหากล้องตัวไหนอยู่? ให้ AI ช่วยจับคู่กล้องที่ใช่สำหรับคุณ</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    # คำสั่ง AI
    system_instruction = f"""
    คุณคือผู้เชี่ยวชาญด้านอุปกรณ์ของร้านเช่ากล้อง Lenslineup (ร้านอยู่ชั้น 12 อาคารเอเชีย ติด BTS ราชเทวี)
    หน้าที่ของคุณคือ แนะนำกล้องหรือมือถือที่เหมาะสมที่สุดให้กับลูกค้าตามความต้องการ

    กฎสำคัญในการจัดรูปแบบคำตอบ (ต้องทำตามอย่างเคร่งครัดเพื่อให้หน้าเว็บอ่านง่าย):
    1. แนะนำเฉพาะรุ่นที่มีอยู่ในฐานข้อมูลด้านล่างนี้เท่านั้น ห้ามมั่วชื่อรุ่นเด็ดขาด
    2. บังคับให้จัดรูปแบบคำตอบโดย **ต้องขึ้นบรรทัดใหม่และใช้ Bullet Point (เครื่องหมาย -)** ในแต่ละหัวข้อย่อย เพื่อไม่ให้ข้อความติดกันเป็นบรรทัดเดียว ให้ใช้โครงสร้างเป๊ะๆ ตามนี้:

       (ทักทายและเกริ่นนำสั้นๆ อย่างเป็นกันเอง)
       
       📸 **[ชื่อรุ่นกล้อง/มือถือที่แนะนำ]**
       - ✨ **จุดเด่น:** [อธิบายสั้นๆ ตรงประเด็นว่าทำไมถึงตอบโจทย์ลูกค้า]
       - 💰 **ราคาเช่า:** [ราคา] บาท/วัน
       - 👉 **[คลิกเพื่อดูรายละเอียดและจองคิว](ใส่ URL ของสินค้านั้น หากไม่มีให้ใส่ https://www.lenslineup.com)**

    3. หากแนะนำหลายรุ่น ให้เว้นบรรทัดว่าง 1 บรรทัดระหว่างรุ่น เพื่อให้ดูสะอาดตา
    4. ปิดท้ายด้วยคำถามสั้นๆ 1 ประโยค เพื่อให้ลูกค้าพูดคุยต่อ (เช่น ถามเรื่องงบ, ถามวันที่จะใช้งาน)

    รายการกล้องของร้านที่มีให้เช่า:
    {json.dumps(camera_catalog, ensure_ascii=False, indent=2)}
    """

    # เปลี่ยนประโยคทักทายแรก
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="📸"):
            st.markdown("สวัสดีครับ! เอากล้องไปถ่ายแนวไหน เที่ยวที่ไหน หรือมีงบในใจเท่าไหร่ พิมพ์บอกมาได้เลยครับเดี๋ยวผมช่วยเลือกให้! 👇")

    for msg in st.session_state.messages:
        avatar = "🧑‍💻" if msg["role"] == "user" else "📸"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # รอรับข้อความผู้ใช้
    if user_input := st.chat_input("พิมพ์บอกงานที่ต้องการนำกล้องไปใช้ หรือสเปก/งบประมาณ..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        # เรียกใช้งาน Gemini
        with st.chat_message("assistant", avatar="📸"):
            message_placeholder = st.empty()
            success = False
            for attempt in range(3):
                try:
                    client = genai.Client(api_key=api_key)
                    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in st.session_state.messages]
                    response = client.models.generate_content(
                        model="gemini-3.6-flash", contents=contents, config={"system_instruction": system_instruction}
                    )
                    message_placeholder.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    success = True
                    break
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "503" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        if attempt < 2:
                            message_placeholder.info(f"⏳ ระบบกำลังประมวลผล กรุณารอสักครู่ (กำลังลองใหม่ครั้งที่ {attempt + 1})...")
                            time.sleep(3)
                            continue
                    message_placeholder.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
                    break
