import streamlit as st
import requests
import json
import matplotlib.pyplot as plt

# Streamlit app for AI Chatbot with Bubble Style UI
st.set_page_config(
    page_title="Dynamic Quiz Generator with AI",
    page_icon="🤖",
    layout="wide"
)

# CONFIG API
API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# SIDEBAR
st.sidebar.title("Pengaturan Chatbot")

AVAILABLE_MODELS = {
    "deepseek/deepseek-chat-v3-0324": "DeepSeek Chat v3",
    "openai/gpt-3.5-turbo": "GPT-3.5 Turbo",
    "openai/gpt-4": "GPT-4"
}
selected_model = st.sidebar.selectbox(
    "Pilih Model LLM",
    options=list(AVAILABLE_MODELS.keys()),
    format_func=lambda x: AVAILABLE_MODELS[x]
)

LANGUAGES = {
    "id": "Bahasa Indonesia",
    "en": "English"
}
selected_lang = st.sidebar.selectbox(
    "Pilih Bahasa Chatbot",
    options=list(LANGUAGES.keys()),
    format_func=lambda x: LANGUAGES[x]
)

MODEL = selected_model

def extract_json_from_text(text):
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return None
    return text[start:end+1]

def generate_quiz(topic: str, num_questions: int = 5):
    prompt = f"""
    Buat {num_questions} soal kuis pilihan ganda, berbahasa {selected_lang} tentang topik '{topic}'.
    Format JSON array dengan atribut:
    - question (string)
    - options (list of strings)
    - answer (string)
    - explanation (string, penjelasan mengapa jawabannya benar).
    Contoh:
    [
    {{
        "question": "Apa fungsi utama dari tulangan pada struktur beton bertulang?",
        "options": ["A. Meningkatkan ketahanan terhadap api", "B. Menahan gaya tarik yang tidak dapat ditahan oleh beton", "C. Mempercepat waktu pengeringan beton", "D. Mengurangi biaya konstruksi"],
        "answer": "B. Menahan gaya tarik yang tidak dapat ditahan oleh beton",
        "explanation": "Jawaban B benar karena..."
    }},
    ...
    ]
    """
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt.strip()}]
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=body, timeout=15)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        json_str = extract_json_from_text(content)
        if not json_str:
            st.error("Gagal menemukan JSON di dalam respon AI.")
            return None
        quiz = json.loads(json_str)
        return quiz
    except Exception as e:
        st.error(f"Gagal mengurai JSON dari respon AI: {e}")
        if 'content' in locals():
            st.write("Response content:", content)
        return None

def main():
    st.title("🧠Dynamic Quiz Generator with AI")
    st.caption("""Made by : Felix Kho & Rheza Firmansyah
                
        Github : felixkhoiscoding & rhezafz
        """)
    st.markdown(f"Powered by {MODEL} via OpenRouter 🤖")

    topic = st.text_input("Masukkan topik kuis", value="", placeholder="Contoh: Energi Terbarukan")
    num_questions = st.number_input("Jumlah soal", min_value=1, max_value=20, value=5, step=1)

    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'score' not in st.session_state:
        st.session_state.score = 0

    if st.button("Generate Quiz"):
        if topic.strip() == "":
            st.warning("Mohon isi topik kuis terlebih dahulu.")
        else:
            st.session_state.quiz_data = generate_quiz(topic, num_questions)
            st.session_state.answers = {}
            st.session_state.submitted = False
            st.session_state.score = 0

    quiz = st.session_state.quiz_data

    if quiz:
        with st.form("quiz_form"):
            for i, q in enumerate(quiz):
                st.write(f"**{i+1}. {q['question']}**")
                options = q['options']
                selected = st.radio(
                    label=f"Pilihan untuk soal {i+1}",
                    options=options,
                    key=f"q_{i}",
                )
                st.session_state.answers[f"q_{i}"] = selected

            submitted = st.form_submit_button("Submit Jawaban")
            if submitted:
                score = 0
                for i, q in enumerate(quiz):
                    user_answer = st.session_state.answers.get(f"q_{i}", "").strip().lower()
                    correct_answer = q["answer"].strip().lower()
                    if user_answer == correct_answer:
                        score += 1
                st.session_state.score = score
                st.session_state.submitted = True

        if st.session_state.submitted:
            st.markdown("---")
            for i, q in enumerate(quiz):
                user_ans = st.session_state.answers.get(f"q_{i}", "")
                correct = q["answer"]
                explanation = q.get("explanation", "")

                if user_ans.strip().lower() == correct.strip().lower():
                    st.success(f"Soal {i+1}: ✅ Jawaban kamu benar!")
                else:
                    st.error(f"Soal {i+1}: ❌ Jawaban kamu salah. Jawaban benar: **{correct}**")

                st.info(f"📘 Penjelasan: {explanation}")

            total = len(quiz)
            st.success(f"Skor kamu: {st.session_state.score} / {total}")

            # Pie chart
            fig, ax = plt.subplots()
            labels = ['Jawaban Benar', 'Jawaban Salah']
            sizes = [st.session_state.score, total - st.session_state.score]
            colors = ['#4CAF50', '#F44336']
            _, _, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', colors=colors,
                startangle=90, textprops={'fontsize': 14, 'color': 'white'}
            )
            ax.set_title('Persentase Jawaban Benar dan Salah', fontsize=16)
            ax.axis('equal')
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            st.pyplot(fig)

            # Tombol Reset di tengah
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            if st.button("🔄 Reset Ulang", key="reset_button"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
