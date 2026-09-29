import json
import time
import streamlit as st
from google import genai

# === 1. การตั้งค่าหน้าเว็บและ CSS ===
st.set_page_config(page_title="Lenslineup AI Guide", page_icon="📸", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    
    /* แก้ปัญหาฟอนต์ไอคอนซ้อน */
    *:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]):not(i) {
        font-family: 'Prompt', sans-serif !important;
    }
    
    /* ซ่อนเฉพาะเมนูจุด 3 จุด (MainMenu) */
    #MainMenu, .viewerBadge_container__1QSob { visibility: hidden !important; display: none !important; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 800px;
    }

    h1, h2, h3 { color: #FFB800 !important; font-weight: 700; }
    
    /* ตกแต่งปุ่มกดทั่วไป */
    .stButton>button {
        background-color: #FFB800 !important;
        color: #121212 !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 10px 15px !important;
        width: 100%;
        transition: 0.3s;
        box-shadow: 0 4px 10px rgba(255, 184, 0, 0.2);
    }
    .stButton>button:hover { background-color: #FF9933 !important; transform: translateY(-2px); }

    /* ปรับแต่งปุ่มใน Sidebar */
    [data-testid="stSidebar"] .stButton>button {
        background-color: transparent !important;
        color: inherit !important;
        border: 1px solid #FFB800 !important;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #FFB800 !important;
        color: #121212 !important;
    }

    /* กล่องข้อความแชท */
    div.stChatMessage[data-testid="stChatMessage-user"] {
        border-left: 4px solid #FFB800; 
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 15px;
    }
    div.stChatMessage[data-testid="stChatMessage-assistant"] {
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 15px;
        line-height: 1.6;
    }

    .stChatInputContainer {
        border: 2px solid #FFB800 !important; 
        border-radius: 16px !important; 
        padding: 4px 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    /* สไตล์สำหรับกล่องประวัติแชทให้เหมือน Gemini */
    .history-item {
        padding: 10px;
        border-radius: 8px;
        background-color: rgba(255, 184, 0, 0.1);
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: inherit;
        border-left: 3px solid #FFB800;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: 0.2s;
    }
    .history-item:hover {
        background-color: rgba(255, 184, 0, 0.3);
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# === 2. โหลดข้อมูล ===
api_key = st.secrets["GEMINI_API_KEY"]
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json'")
    st.stop()

# === 3. ระบบจัดการหน้าและสถานะ ===
if "step" not in st.session_state:
    st.session_state.step = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []

def go_to_chat(): st.session_state.step = "chat"

# ==========================================
# แถบเมนูด้านข้าง (Sidebar)
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>📸</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; font-size: 1.3rem; margin-top: -10px;'>Lenslineup Menu</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>ผู้ช่วย AI ค้นหากล้องที่ตรงใจคุณ</p>", unsafe_allow_html=True)
    
    st.divider()
    
    # เปลี่ยนชื่อปุ่มให้เหมือนแอป AI ของจริง
    if st.button("➕ แชทใหม่ (New Chat)"):
        st.session_state.messages = []
        st.rerun()
        
    # --- ส่วนแสดงประวัติแชท (Chat History) ---
    st.markdown("<h3 style='font-size: 1.1rem; margin-top: 15px;'>🕒 ประวัติแชทล่าสุด</h3>", unsafe_allow_html=True)
    
    # ดึงเฉพาะข้อความที่ลูกค้าพิมพ์มาแสดง
    user_history = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    
    if not user_history:
        st.markdown("<p style='color: gray; font-size: 0.85rem; text-align: center; margin-top: 10px;'>ยังไม่มีประวัติการสนทนา</p>", unsafe_allow_html=True)
    else:
        # แสดงย้อนหลังเอาแค่ 6 ข้อความล่าสุด จะได้ไม่ล้นหน้าจอ
        for msg in reversed(user_history[-6:]):
            st.markdown(f"<div class='history-item'>💬 {msg}</div>", unsafe_allow_html=True)
            
    st.divider()
    with st.expander("📍 ข้อมูลร้าน Lenslineup"):
        st.markdown("**ที่ตั้ง:**\nชั้น 12 อาคารเอเชีย (ติด BTS ราชเทวี)\n\n**เปิดบริการ:**\nทุกวัน 10:00 - 20:00 น.")

# ==========================================
# หน้าที่ 1: หน้าแรก (Home)
# ==========================================
if st.session_state.step == "home":
    st.markdown("<h1 style='font-size: clamp(2.2rem, 6vw, 3rem); margin-bottom: 0; text-align: center;'>📸 Lenslineup AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-weight: 400; font-size: 1.1rem; text-align: center; margin-top: 5px;'>ผู้ช่วยอัจฉริยะค้นหากล้องที่ใช่สำหรับคุณ</h3>", unsafe_allow_html=True)
    st.write("")
    
    st.markdown("""
        <div style='padding: 30px; border-radius: 15px; text-align: center; border: 1px solid rgba(128,128,128,0.3); margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);'>
            <h1 style='font-size: 4.5rem; margin: 0;'>✨🤖📷</h1>
            <p style='font-size: 1rem; margin-top: 15px; line-height: 1.6;'>
                แค่บอกว่าคุณอยากนำกล้องไปทำอะไร<br>ไปเที่ยว, คอนเสิร์ต, VLOG หรือถ่ายงานจริงจัง<br>AI ของเราจะคัดเลือกรุ่นที่ใช่ที่สุดให้คุณทันที!
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.button("💬 เริ่มคุยกับ AI เลย", on_click=go_to_chat, use_container_width=True)

# ==========================================
# หน้าที่ 2: หน้าแชท AI (Chat)
# ==========================================
elif st.session_state.step == "chat":
    st.markdown("""
        <div style="text-align: center; margin-bottom: 10px;">
            <h2 style='color: #FFB800; margin-bottom: 5px; font-size: 1.8rem;'>✨ Lenslineup AI</h2>
            <p style='font-size: 0.95rem; margin: 0;'>บอกที่ที่ไป หรืองบที่มี เดี๋ยว AI จัดกล้องที่ตรงใจให้เลย!</p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    
    system_instruction = f"""
    คุณคือผู้เชี่ยวชาญด้านอุปกรณ์ของร้านเช่ากล้อง Lenslineup (ร้านอยู่ชั้น 12 อาคารเอเชีย ติด BTS ราชเทวี)
    หน้าที่ของคุณคือ แนะนำกล้องหรือมือถือที่เหมาะสมที่สุดให้กับลูกค้าตามความต้องการ

    กฎสำคัญในการจัดรูปแบบคำตอบ:
    1. แนะนำเฉพาะรุ่นที่มีอยู่ในฐานข้อมูลด้านล่างนี้เท่านั้น ห้ามมั่วชื่อรุ่นเด็ดขาด
    2. บังคับให้จัดรูปแบบคำตอบโดย ต้องขึ้นบรรทัดใหม่และใช้ Bullet Point (-) ในแต่ละหัวข้อย่อย:

       (ทักทายและเกริ่นนำสั้นๆ อย่างเป็นกันเอง)
       
       📸 **[ชื่อรุ่นกล้อง/มือถือที่แนะนำ]**
       - ✨ **จุดเด่น:** [อธิบายสั้นๆ ตรงประเด็นว่าทำไมถึงตอบโจทย์ลูกค้า]
       - 💰 **ราคาเช่า:** [ราคา] บาท/วัน
       - 👉 **[คลิกเพื่อดูรายละเอียดและจองคิว](ใส่ URL หากไม่มีใส่ https://www.lenslineup.com)**

    3. เว้นบรรทัดว่าง 1 บรรทัดระหว่างรุ่น
    4. ปิดท้ายด้วยคำถามสั้นๆ 1 ประโยค เพื่อให้ลูกค้าพูดคุยต่อ

    รายการกล้องของร้านที่มีให้เช่า:
    {json.dumps(camera_catalog, ensure_ascii=False, indent=2)}
    """

    # ทักทายเริ่มต้น
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="📸"):
            st.markdown("สวัสดีครับ! เอากล้องไปถ่ายแนวไหน เที่ยวที่ไหน หรือมีงบในใจเท่าไหร่ พิมพ์บอกมาได้เลยครับเดี๋ยวผมช่วยเลือกให้! 👇")

    # แสดงประวัติการสนทนาในช่องแชทหลัก
    for msg in st.session_state.messages:
        avatar = "🧑‍💻" if msg["role"] == "user" else "📸"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # รับค่าจากช่องพิมพ์
    if user_input := st.chat_input("พิมพ์บอกงานที่ต้องการนำกล้องไปใช้ หรือสเปก/งบประมาณ..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="📸"):
            message_placeholder = st.empty()
            success = False
            
            with st.spinner("⏳ AI กำลังค้นหากล้องที่ตรงใจคุณที่สุด..."):
                for attempt in range(3):
                    try:
                        client = genai.Client(api_key=api_key)
                        contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in st.session_state.messages]
                        response = client.models.generate_content(
                            model="gemini-3.6-flash", contents=contents, config={"system_instruction": system_instruction}
                        )
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
            
            if success:
                message_placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # รีรันหน้าเว็บเพื่อให้ข้อความไปอัปเดตบนแถบเมนูด้านข้าง (ประวัติแชท) ด้วย
                st.rerun()
