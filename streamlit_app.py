import streamlit as st
import requests
import uuid
from datetime import datetime
import os

# ============= КОНФИГУРАЦИЯ - БЕКЕНД НА SELECTEL =============
# ⚠️ ВАЖНО! Укажите реальный IP вашего сервера Selectel!
SELECTEL_IP = os.getenv("SELECTEL_IP", "95.163.255.123")  # ВСТАВЬТЕ ВАШ IP!
API_URL = f"http://{SELECTEL_IP}:8001"
API_ASK = f"{API_URL}/ask"
API_HEALTH = f"{API_URL}/health"

# ============= НАСТРОЙКИ СТРАНИЦЫ =============
st.set_page_config(
    page_title="Газпром RAG - Ассистент",
    page_icon="🏭",
    layout="wide"
)

# ============= ИНИЦИАЛИЗАЦИЯ СЕССИИ =============
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ============= ПРОВЕРКА API =============
@st.cache_data(ttl=30)
def check_api():
    try:
        response = requests.get(API_HEALTH, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"❌ Ошибка подключения к Selectel: {e}")
    return None

# ============= ОТПРАВКА ВОПРОСА =============
def send_question(question):
    payload = {
        "question": question,
        "session_id": st.session_state.session_id
    }
    
    try:
        with st.spinner(f"🔍 Отправка запроса на Selectel ({SELECTEL_IP})..."):
            response = requests.post(
                API_ASK,
                json=payload,
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Ошибка API: {response.status_code}"}
    except Exception as e:
        return {"error": f"Не удалось подключиться к Selectel: {e}"}

# ============= ОТОБРАЖЕНИЕ ОТВЕТА =============
def display_answer(answer_data):
    if 'error' in answer_data:
        st.error(f"❌ {answer_data['error']}")
        return
    
    if 'answer' in answer_data:
        ans = answer_data['answer']
        
        # Краткий ответ
        st.markdown("### 📌 Ответ")
        st.success(ans.get('summary', 'Нет ответа'))
        
        # Детали
        if ans.get('details'):
            st.markdown("### 📋 Ключевые факты")
            for detail in ans['details']:
                st.markdown(detail)
        
        # Стандарты
        if ans.get('standards'):
            st.markdown("### 📚 Нормативные документы")
            cols = st.columns(min(len(ans['standards']), 3))
            for i, std in enumerate(ans['standards'][:3]):
                with cols[i]:
                    with st.container():
                        st.markdown(f"**{std.get('name', 'СТО Газпром')}**")
                        st.markdown(f"📌 *Пункт {std.get('section', '')}*")
                        st.caption(std.get('title', '')[:100])
        
        # Примечание
        if ans.get('note'):
            if "✓" in ans['note']:
                st.success(ans['note'])
            else:
                st.warning(ans['note'])

# ============= ИНТЕРФЕЙС =============
st.title("🏭 Газпром RAG - Технический ассистент")
st.caption(f"🟢 Бекенд: Selectel ({SELECTEL_IP}) | 🌐 Фронтенд: Streamlit Cloud")

# Проверка API
api_status = check_api()
if not api_status:
    st.error(f"❌ Сервер Selectel ({SELECTEL_IP}) не отвечает!")
    
    with st.expander("🔧 Информация для администратора"):
        st.markdown(f"""
        **Проверьте на сервере Selectel:**
        - Сервер: `{SELECTEL_IP}`
        - Порт: 8001
        - Команда: `curl http://localhost:8001/health`
        - CORS: Разрешить Streamlit Cloud
        """)
    st.stop()
else:
    st.success(f"✅ Подключено к Selectel. Документов: {api_status.get('documents', 0)}")

# Боковая панель
with st.sidebar:
    st.header("⚙️ Управление")
    
    if st.button("🔄 Новая сессия", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.subheader("📊 Информация")
    st.info(f"**Бекенд:** `{SELECTEL_IP}:8001`")
    st.info(f"**Сессия:** `{st.session_state.session_id[:8]}...`")
    
    st.divider()
    
    st.subheader("📖 О системе")
    st.markdown("""
    - **Бекенд:** Selectel (RAG API)
    - **Фронтенд:** Streamlit Cloud
    - **Документов:** 1 696
    - **Модель:** Llama 3.3 70B
    - **Векторная БД:** Qdrant
    """)

# История чата
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Поле ввода
if prompt := st.chat_input("Введите вопрос по документации Газпрома..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    result = send_question(prompt)
    
    with st.chat_message("assistant"):
        if 'error' not in result:
            display_answer(result)
            answer_text = result.get('answer', {}).get('summary', 'Ответ получен')
            st.session_state.messages.append({"role": "assistant", "content": answer_text})
        else:
            st.error(result['error'])
            st.session_state.messages.append({"role": "assistant", "content": f"❌ {result['error']}"})

# Footer
st.divider()
st.caption(f"🏭 Бекенд: Selectel | 🌐 Фронтенд: Streamlit Cloud | RAG: LangChain + Groq")