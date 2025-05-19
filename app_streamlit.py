import streamlit as st
from utils import get_chain, save_to_mongo, save_to_github, get_all_course_titles
import time

# --- CONFIG ---
st.set_page_config(page_title="🎓 Pedagogical Assistant Moodle", layout="wide", page_icon="image/startupgatex.png")

# --- LANGUES ---
LANGUAGES = {"en": "🇺🇸 English", "ar": "🇸🇦 العربية"}

# --- MESSAGES ---
WELCOME_MSG = {
    "en": "👋 Hello! I am your pedagogical assistant. Ready to generate a course scenario?",
    "ar": "👋 مرحبًا! أنا مساعدك التربوي. هل أنت جاهز لإنشاء سيناريو دورة؟"
}

QUESTIONS = {
    "en": [
        ("titre", "📝 What is the course title?"),
        ("niveau", "📈 What is the course level? (Beginner, Intermediate, Advanced)"),
        ("public", "👥 Who is the target audience? (e.g., students, employees, high schoolers)"),
        ("duree", "⏳ What is the duration of the course? (weeks, days, etc.)"),
        ("langue", "🌍 What is the course language? (English, Arabic)"),
        ("description", "🖊️ Provide a brief description of the course content.")
    ],
    "ar": [
        ("titre", "📝 ما هو عنوان الدورة؟"),
        ("niveau", "📈 ما هو مستوى الدورة؟ (مبتدئ، متوسط، متقدم)"),
        ("public", "👥 من هو الجمهور المستهدف؟ (مثل: طلاب، موظفين، تلاميذ)"),
        ("duree", "⏳ ما مدة الدورة؟ (أسابيع، أيام، إلخ)"),
        ("langue", "🌍 ما هي لغة الدورة؟ (إنجليزي، عربي)"),
        ("description", "🖊️ قدم وصفًا موجزًا لمحتوى الدورة.")
    ]
}

# --- SIDEBAR ---
with st.sidebar:
    st.image("image/startupgatex.png", width=180)
    st.markdown("## 🌐 " + ("Language / اللغة" if st.session_state.get("lang", "en") == "en" else "اللغة"))
    lang_choice = st.radio("", options=list(LANGUAGES.keys()), format_func=lambda x: LANGUAGES[x], index=0)
    st.session_state.lang = lang_choice

    st.markdown("---")
    st.markdown("## 📚 " + ("Course History" if lang_choice == "en" else "تاريخ الدورات"))
    try:
        course_titles = get_all_course_titles()
        if course_titles:
            selected_course = st.selectbox(
                "Select a course:" if lang_choice == "en" else "اختر دورة:",
                course_titles
            )
            if selected_course:
                st.success(f"{'Selected course:' if lang_choice == 'en' else 'تم اختيار الدورة:'} **{selected_course}**")
        else:
            st.info("No saved courses yet." if lang_choice == "en" else "لا توجد دورات محفوظة حتى الآن.")
    except Exception as e:
        st.error("MongoDB Error" if lang_choice == "en" else "خطأ في MongoDB")
        st.caption(str(e))

# --- INITIALIZE SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 0
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "lang" not in st.session_state:
    st.session_state.lang = "en"

lang = st.session_state.lang
questions = QUESTIONS[lang]

# --- DISPLAY CHAT HISTORY ---
for role, msg in st.session_state.chat_history:
    avatar = "image/startupgatex.png" if role == "assistant" else None
    st.chat_message(role, avatar=avatar).markdown(msg)

# --- START CONVERSATION ---
if st.session_state.step == 0:
    welcome = WELCOME_MSG[lang]
    st.session_state.chat_history.append(("assistant", welcome))
    st.chat_message("assistant", avatar="image/startupgatex.png").markdown(welcome)
    st.session_state.step = 1

# --- USER INPUT ---
prompt = st.chat_input(placeholder="Type your message here..." if lang == "en" else "اكتب رسالتك هنا...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.chat_history.append(("user", prompt))

    if st.session_state.step == 1:
        # Check confirmation to start questionnaire
        if prompt.strip().lower() in ["yes", "ok", "sure", "yep", "نعم", "حسنًا", "تمام", "ابدأ", "go"]:
            first_question = questions[0][1]
            st.session_state.chat_history.append(("assistant", first_question))
            st.chat_message("assistant", avatar="image/startupgatex.png").markdown(first_question)
            st.session_state.step = 2
        else:
            remind = "Please type 'yes' to start." if lang == "en" else "يرجى كتابة 'نعم' للبدء."
            st.session_state.chat_history.append(("assistant", remind))
            st.chat_message("assistant", avatar="image/startupgatex.png").markdown(remind)

    elif st.session_state.step >= 2:
        current_step = st.session_state.step - 2
        if current_step < len(questions):
            key, _ = questions[current_step]
            st.session_state.inputs[key] = prompt
            st.session_state.step += 1

            # Next question or generate scenario
            if current_step + 1 < len(questions):
                next_question = questions[current_step + 1][1]
                st.session_state.chat_history.append(("assistant", next_question))
                st.chat_message("assistant", avatar="image/startupgatex.png").markdown(next_question)
            else:
                # Generate scenario
                loading_msg = "⏳ Generating scenario, please wait..." if lang == "en" else "⏳ جاري إنشاء السيناريو، يرجى الانتظار..."
                st.session_state.chat_history.append(("assistant", loading_msg))
                st.chat_message("assistant", avatar="image/startupgatex.png").markdown(loading_msg)

                with st.spinner("Loading..." if lang == "en" else "جارٍ التحميل..."):
                    try:
                        start_time = time.time()
                        chain = get_chain(lang)  # ta fonction réelle ici
                        response = chain.run(st.session_state.inputs)

                        st.session_state.chat_history.append(("assistant", response))
                        st.chat_message("assistant", avatar="image/startupgatex.png").markdown(response)

                        # Save data
                        save_to_mongo(
                            st.session_state.inputs["titre"],
                            response,
                            st.session_state.inputs.get("niveau", "")
                        )
                        save_to_github(
                            st.session_state.inputs["titre"],
                            response
                        )

                        elapsed = time.time() - start_time
                        success_msg = f"✅ Generated in {elapsed:.1f}s 🚀" if lang == "en" else f"✅ تم الإنشاء خلال {elapsed:.1f} ثانية 🚀"
                        st.success(success_msg)

                    except Exception as e:
                        st.error("An error occurred:" if lang == "en" else "حدث خطأ:")
                        st.error(str(e))

                # Reset for next scenario
                st.session_state.step = 0
                st.session_state.inputs = {}
                final_msg = "Would you like to generate another scenario?" if lang == "en" else "هل ترغب في إنشاء سيناريو آخر؟"
                st.session_state.chat_history.append(("assistant", final_msg))
                st.chat_message("assistant", avatar="image/startupgatex.png").markdown(final_msg)
