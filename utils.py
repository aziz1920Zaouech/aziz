from datetime import datetime
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from config import courses_collection, github, GITHUB_REPO
import subprocess
import requests
import time
import re

OLLAMA_URL = "http://localhost:11434"

def is_ollama_running():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_ollama_server():
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)  # attendre que le serveur démarre

def ensure_model_loaded(model_name="qwen3:0.6b"):
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        models = [m["name"] for m in response.json().get("models", [])]
        if model_name not in models:
            subprocess.run(["ollama", "pull", model_name], check=True)
    except Exception as e:
        print(f"Erreur lors du chargement du modèle Ollama : {e}")
        raise

def load_model(model_name="qwen3:0.6b"):
    if not is_ollama_running():
        start_ollama_server()
        if not is_ollama_running():
            raise RuntimeError("❌ Impossible de démarrer le serveur Ollama.")
    ensure_model_loaded(model_name)

    return Ollama(
        model=model_name,
        temperature=0.7,
        top_k=40,
        top_p=0.9,
        timeout=60
    )

def get_prompt_template(lang="en"):
    if lang == "ar":
        template = """
        أنت خبير تربوي. ساعد المعلم في تصميم السيناريو التعليمي التالي بناءً على المعلومات التالية:

        ### عنوان الدورة : {titre}
        ### الجمهور المستهدف : {public}
        ### المدة : {duree}
        ### المستوى : {niveau}
        ### اللغة : {langue}
        ### الوصف : {description}

        اكتب رد كامل وواضح بالتنسيق التالي:

        ### 🌟 الأهداف التعليمية
        - ...

        ### 📝 أنشطة Moodle (المدة المقدرة)
        - ...

        ### 🏫 الطرق التعليمية
        - ...

        ### 📚 الموارد
        - ...

        ### 📊 التقييم
        - ...

        ### 🗓️ تنظيم الدورة (4 أسابيع)
        - الأسبوع 1 : ...
        - الأسبوع 2 : ...
        - الأسبوع 3 : ...
        - الأسبوع 4 : ...
        """
    else:
        template = """
        You are an educational expert. Help the teacher design the following pedagogical scenario based on the given info:

        ### Course Title : {titre}
        ### Target Audience : {public}
        ### Duration : {duree}
        ### Level : {niveau}
        ### Language : {langue}
        ### Description : {description}

        Provide a full, clear response formatted as:

        ### 🌟 Learning Objectives
        - ...

        ### 📝 Moodle Activities (estimated duration)
        - ...

        ### 🏫 Teaching Methods
        - ...

        ### 📚 Resources
        - ...

        ### 📊 Assessment
        - ...

        ### 🗓️ Course Organization (4 weeks)
        - Week 1 : ...
        - Week 2 : ...
        - Week 3 : ...
        - Week 4 : ...
        """
    return PromptTemplate.from_template(template)

def get_chain(lang="en"):
    llm = load_model()
    prompt = get_prompt_template(lang)
    return LLMChain(llm=llm, prompt=prompt)

def extract_weeks_from_duree(duree: str) -> int:
    match = re.search(r"(\d+)\s*semaines?", duree.lower())
    if match:
        return int(match.group(1))
    return 4  # valeur par défaut

def get_reflection_text(lang="en", titre="", niveau="", duree="4 semaines"):
    nb_semaines = extract_weeks_from_duree(duree)

    if lang == "ar":
        return f"""
<div dir="rtl" style="text-align: right;">
🤔 حسنًا، سأبدأ بتحليل طلب إعداد دورة بعنوان "{titre}" موجهة للمتعلمين في مستوى {niveau}. مدة الدورة هي {nb_semaines} أسبوع{'ًا' if nb_semaines == 1 else 'ًا'}.

سأحدد أهدافًا تعليمية واضحة لهذا الموضوع، مع أنشطة Moodle مناسبة موزعة على {nb_semaines} أسبوع{'ًا' if nb_semaines == 1 else 'ًا'}.

طرق التدريس ستشمل استراتيجيات تفاعلية مثل العمل الجماعي، استخدام الوسائط، والتقييم الذاتي.

سأقترح موارد رقمية وكتب وفيديوهات تدعم التعلم النشط.

التقييم سيكون متنوعًا بين اختبارات قصيرة ومشروع ختامي، يتماشى مع الأهداف.

سأنظم الأسابيع بشكل متسلسل منطقي، بدءًا من المفاهيم الأساسية وحتى التقييم الختامي. سأحرص على وضوح السيناريو وكتابته باللغة العربية دون علامات Markdown.
</div>
"""
    else:
        return f"""
🤔 Alright, let's begin by designing a course titled "{titre}" for {niveau} level learners. The course spans {nb_semaines} week{"s" if nb_semaines > 1 else ""}.

I’ll start by identifying clear learning objectives relevant to the topic.

Then, I’ll create engaging Moodle activities logically distributed across {nb_semaines} week{"s" if nb_semaines > 1 else ""}, ensuring progression from basics to advanced application.

The teaching methods will emphasize interactivity: collaborative tasks, multimedia, and critical thinking.

I'll propose digital resources, books, and videos that support learning.

Assessment will include short quizzes and a final project, aligned with the course goals.

The weekly structure will ensure gradual development, ending with a final review. I’ll keep the scenario clear, professional, and Markdown-free.
"""

def save_to_mongo(title, scenario, level):
    doc = {
        "title": title,
        "level": level,
        "scenario": scenario,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    return courses_collection.insert_one(doc).inserted_id

def get_all_course_titles():
    try:
        return [doc["title"] for doc in courses_collection.find({}, {"title": 1, "_id": 0})]
    except Exception as e:
        print(f"Erreur MongoDB : {e}")
        return []

def save_to_github(title, scenario):
    if not github:
        return None
    repo = github.get_repo(GITHUB_REPO)
    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)
    filename = f"scenarios/{safe_title}_{datetime.now().strftime('%Y%m%d')}.md"
    repo.create_file(
        path=filename,
        message=f"Ajout du scénario pour {title}",
        content=scenario,
        branch="main"
    )
    return filename
