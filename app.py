import json
import time
import streamlit as st
from google import genai

# === 1. การตั้งค่าหน้าเว็บและ CSS ธีม ดำ-ส้ม (Dark & Orange Premium) ===
st.set_page_config(page_title="Lenslineup AI Finder", page_icon="📸", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Prompt', sans-serif !important; }
    
    .stApp { background-color: #121212; color: #E0E0E0; }
    header, #MainMenu, footer { visibility: hidden !important; display: none !important; }
    
    /* Typography */
    h1, h2, h3 { color: #FF7A00 !important; font-weight: 700; text-align: center; }
    
    /* ปุ่ม CTA (Call to Action) หลัก */
    .stButton>button {
        background-color: #FF7A00 !important;
        color: #121212 !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 10px 24px !important;
        width: 100%;
        transition: 0.3s;
        box-shadow: 0 4px 15px rgba(255, 122, 0, 0.3);
    }
    .stButton>button:hover {
        background-color: #FF9933 !important;
        transform: translateY(-2px);
    }

    /* กล่องแชทและกรอบแสดงผล */
    div.stChatMessage[data-testid="stChatMessage-user"] {
        background-color: #1E1E1E; border-left: 4px solid #FF7A00; border-radius: 8px 15px 15px 8px; padding: 15px; margin-bottom: 15px;
    }
    div.stChatMessage[data-testid="stChatMessage-assistant"] {
        background-color: #161616; border: 1px solid #333; border-radius: 15px 8px 8px 15px; padding: 15px; margin-bottom: 15px;
    }
    
    /* แต่ง Input ให้เข้าธีม */
    .stChatInputContainer { border: 2px solid #FF7A00 !important; border-radius: 25px !important; background-color: #1E1E1E !important; }
    .stChatInputContainer textarea { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# === 2. โหลดข้อมูล API และ แคตตาล็อกกล้อง ===
api_key = st.secrets["GEMINI_API_KEY"]
try:
    with open("cameras.json", "r", encoding="utf-8") as f:
        camera_catalog = json.load(f)
except FileNotFoundError:
    st.error("ไม่พบไฟล์ 'cameras.json'")
    st.stop()

# === 3. ระบบจัดการหน้า (State Management) ===
if "step" not in st.session_state:
    st.session_state.step = "home"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = {}

# ฟังก์ชันเปลี่ยนหน้า
def go_to_quiz(): st.session_state.step = "quiz"
def go_to_result(): st.session_state.step = "result"
def reset_app(): 
    st.session_state.step = "home"
    st.session_state.messages = []

# ==========================================
# หน้าที่ 1: Homepage & Hero Section
# ==========================================
if st.session_state.step == "home":
    st.markdown("<h1 style='font-size: 2.8rem; margin-bottom: 0;'>📸 Lenslineup</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #FFFFFF !important; font-weight: 400; font-size: 1.2rem; margin-top: 5px;'>ไม่รู้จะเลือกกล้องตัวไหน? ให้ AI ช่วยคุณหาตัวที่ใช่ใน 1 นาที</h3>", unsafe_allow_html=True)
    st.write("")
    
    # Hero Visual เล็กๆ ดึงดูดสายตา
    st.markdown("""
        <div style='background-color: #1E1E1E; padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #333; margin-bottom: 20px;'>
            <h1 style='font-size: 4rem; margin: 0;'>✨🤖📷</h1>
            <p style='color: #AAA; font-size: 1rem; margin-top: 10px;'>วิเคราะห์จากสเปก, งบประมาณ และรูปแบบการใช้งานของคุณ</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.button("🚀 เริ่มค้นหากล้องด้วย AI", on_click=go_to_quiz)

# ==========================================
# หน้าที่ 2: Interactive Questionnaire (สเปกที่ต้องการ)
# ==========================================
elif st.session_state.step == "quiz":
    st.markdown("<h2>🎯 ค้นหากล้องที่ตรงใจคุณ</h2>", unsafe_allow_html=True)
    st.write("ตอบคำถามสั้นๆ 4 ข้อ เพื่อให้ AI ช่วยคัดกรองรุ่นที่ดีที่สุดให้ครับ")
    
    budget = st.select_slider("💰 1. งบประมาณค่าเช่าต่อวัน", options=["ไม่เกิน 500 บาท", "500 - 1,000 บาท", "1,000 - 2,000 บาท", "ไม่จำกัดงบ (เน้นคุณภาพ)"])
    use_case = st.radio("🎬 2. ประเภทการใช้งานหลัก", ["📸 ถ่ายภาพนิ่ง / ท่องเที่ยว / คาเฟ่", "🎥 ถ่ายวิดีโอ / VLOG / ทำ YouTube", "👤 ถ่ายพอร์ตเทรต / งานรับปริญญา", "🎤 ถ่ายคอนเสิร์ต / ศิลปิน (ซูมไกล)"])
    level = st.radio("⭐️ 3. ระดับความเชี่ยวชาญของคุณ", ["👶 มือใหม่ (เน้นออโต้ ใช้ง่าย จบหลังกล้อง)", "🧑‍🎓 มือสมัครเล่น (พอตั้งค่าเป็น อยากได้ฟีเจอร์เพิ่ม)", "😎 มืออาชีพ (เน้นไฟล์คุณภาพสูง รับงานได้)"])
    features = st.multiselect("✨ 4. ฟีเจอร์ที่มองหาเป็นพิเศษ (เลือกได้หลายข้อ)", ["เบา พกพาง่าย", "หน้าจอพับได้ (Selfie)", "กันสั่นดีเยี่ยม (IBIS)", "เปลี่ยนเลนส์ได้", "สไตล์วินเทจ/ฟิล์ม"])
    
    st.write("")
    if st.button("✨ ให้ AI ประมวลผลผลลัพธ์"):
        # เก็บข้อมูลแบบสอบถาม
        st.session_state.quiz_data = {"budget": budget, "use_case": use_case, "level": level, "features": features}
        
        # สร้าง Prompt ซ่อนส่งให้ AI
        feature_text = ", ".join(features) if features else "ทั่วไป"
        initial_prompt = f"ช่วยแนะนำกล้องให้หน่อยครับ มีสเปกดังนี้:\n- งบเช่า: {budget}\n- การใช้งาน: {use_case}\n- ประสบการณ์: {level}\n- ฟีเจอร์ที่อยากได้: {feature_text}"
        st.session_state.messages.append({"role": "user", "content": initial_prompt})
        go_to_result()
        st.rerun()

# ==========================================
# หน้าที่ 3: AI Recommendation Result & Chatbot
# ==========================================
elif st.session_state.step == "result":
    st.markdown("<h2>✨ ผลลัพธ์จาก AI & แชทสอบถามเพิ่มเติม</h2>", unsafe_allow_html=True)
    
    # ปุ่มกลับไปเริ่มใหม่
    if st.button("🔄 ค้นหาใหม่อีกครั้ง"):
        reset_app()
        st.rerun()
        
    st.divider()
    
    system_instruction = f"""
    คุณคือผู้เชี่ยวชาญของร้านเช่ากล้อง Lenslineup หน้าที่ของคุณคือแนะนำกล้องตามความต้องการของลูกค้า
    ให้วิเคราะห์จาก [งบประมาณ, การใช้งาน, ระดับความเชี่ยวชาญ, ฟีเจอร์] ที่ลูกค้าส่งมา
    
    กฎสำคัญ:
    1. แนะนำเฉพาะรุ่นที่มีอยู่ในฐานข้อมูลเท่านั้น
    2. จัดรูปแบบคำตอบให้น่าอ่าน แบ่งเป็น 2 ส่วนหลัก:
       🏆 **Top Match (แนะนำอันดับ 1): [ชื่อรุ่น]**
       ✨ **เหตุผลที่ AI เลือกให้:** [วิเคราะห์ว่าทำไมถึงตรงกับที่ลูกค้ากรอกมา]
       💰 **ราคาเช่า:** [ราคา] บาท/วัน
       👉 [คลิกดูรายละเอียด] (ใส่ URL)

       💡 **Alternative Options (ทางเลือกสำรอง):**
       - **[ชื่อรุ่นที่ประหยัดกว่า]**: [เหตุผลสั้นๆ] - [ราคา] บาท/วัน
       - **[ชื่อรุ่นที่สเปกสูงกว่า/สายโปร]**: [เหตุผลสั้นๆ] - [ราคา] บาท/วัน
       
    3. ลงท้ายด้วยการเปิดโอกาสให้ลูกค้าถามต่อ เช่น "สนใจตัวไหนเป็นพิเศษ หรืออยากให้เทียบสเปกให้ดูไหมครับ?"
    
    ข้อมูลกล้องทั้งหมด: {json.dumps(camera_catalog, ensure_ascii=False)}
    """

    # แสดงผลประวัติแชท
    for i, msg in enumerate(st.session_state.messages):
        # ปรับการแสดงผลข้อความแรก (ที่เป็น Prompt สเปก) ให้ออกมาเป็น UI สรุปสวยๆ แทนข้อความยาวๆ
        if i == 0 and msg["role"] == "user":
            st.markdown(f"""
            <div style='background-color: #242424; padding: 15px; border-radius: 10px; border-left: 4px solid #FF7A00; margin-bottom: 20px;'>
                <b>📌 สเปกที่คุณตั้งไว้:</b><br>
                💰 {st.session_state.quiz_data.get('budget')}<br>
                🎬 {st.session_state.quiz_data.get('use_case')}<br>
                ⭐️ {st.session_state.quiz_data.get('level')}
            </div>
            """, unsafe_allow_html=True)
        else:
            avatar = "🧑‍💻" if msg["role"] == "user" else "📸"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                
    # ถ้าเข้ามาหน้า result ครั้งแรกแล้ว AI ยังไม่ได้ตอบ ให้ AI เริ่มประมวลผล
    if len(st.session_state.messages) == 1:
        with st.chat_message("assistant", avatar="📸"):
            msg_ph = st.empty()
            success = False
            for attempt in range(3):
                try:
                    client = genai.Client(api_key=api_key)
                    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in st.session_state.messages]
                    response = client.models.generate_content(
                        model="gemini-3.6-flash", contents=contents, config={"system_instruction": system_instruction}
                    )
                    msg_ph.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    success = True
                    break
                except Exception as e:
                    if "429" in str(e) or "503" in str(e):
                        msg_ph.info("⏳ AI กำลังวิเคราะห์สเปกที่ใช่ที่สุดให้คุณ กรุณารอสักครู่...")
                        time.sleep(3)
                        continue
                    msg_ph.error(f"Error: {e}")
                    break

    # แชทบอทสอบถามเพิ่มเติมด้านล่าง (Value-Added Feature)
    if user_input := st.chat_input("💬 พิมพ์ถาม AI เพิ่มเติม (เช่น 'ตัวที่ 1 กับ 2 ต่างกันยังไง', 'มีเลนส์แนะนำไหม')"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)
            
        with st.chat_message("assistant", avatar="📸"):
            msg_ph = st.empty()
            for attempt in range(3):
                try:
                    client = genai.Client(api_key=api_key)
                    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in st.session_state.messages]
                    response = client.models.generate_content(
                        model="gemini-3.6-flash", contents=contents, config={"system_instruction": system_instruction}
                    )
                    msg_ph.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    break
                except Exception as e:
                    if "429" in str(e) or "503" in str(e):
                        msg_ph.info("⏳ กำลังประมวลผลคำตอบ...")
                        time.sleep(3)
                        continue
                    msg_ph.error(f"Error: {e}")
                    break
