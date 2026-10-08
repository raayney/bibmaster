import json
import time
import streamlit as st

st.set_page_config(page_title="Bibmaster", layout="wide")

# Injection CSS pour Times New Roman et ajustement typographique
st.markdown(
    """
    <style>
    html, body, [class*="css"], [class*="st-"], .stMarkdown, button, input, textarea {
        font-family: 'Times New Roman', Times, serif !important;
    }
    /* Centrage de la carte d'accueil */
    .welcome-container {
        max-width: 550px;
        margin: 80px auto 0 auto;
        padding: 40px;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        text-align: center;
    }
    /* Titre discret pour l'exercice */
    .exercise-header {
        font-size: 1.05rem !important;
        font-weight: bold;
        color: #555555;
        margin-bottom: 0.4rem;
    }
    /* Grossissement du LaTeX et des questions */
    .stMarkdown p {
        font-size: 1.35rem !important;
        line-height: 1.6 !important;
    }
    .katex {
        font-size: 1.3em !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialisation de la Session State
if "page" not in st.session_state:
    st.session_state["page"] = "welcome"
if "exercises" not in st.session_state:
    st.session_state["exercises"] = []
if "tutorial_title" not in st.session_state:
    st.session_state["tutorial_title"] = ""
if "timers" not in st.session_state:
    st.session_state["timers"] = {}

# ==========================================
# PAGE 1 : ACCUEIL
# ==========================================
if st.session_state["page"] == "welcome":
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
        st.title("Bibmaster")
        st.write("")

        uploaded_file = st.file_uploader("Charger le fichier JSON de la fiche", type=["json"])

        with st.expander("i"):
            st.code(
                json.dumps(
                    {
                        "title": "Titre du Tutoriel",
                        "exercises": [
                            {
                                "title": "Exercice 1 : Calcul d'intégrale",
                                "question": "Calculer la valeur de $\\int_{0}^{1} x^2 dx$.",
                                "time_seconds": 360,
                                "hint": "Indice optionnel...",
                                "solution": "La solution détaillée..."
                            }
                        ]
                    },
                    indent=2,
                    ensure_ascii=False
                ),
                language="json"
            )

        if uploaded_file and not st.session_state["exercises"]:
            try:
                with st.spinner("Chargement de la fiche en cours..."):
                    time.sleep(0.8)
                    data = json.load(uploaded_file)
                    st.session_state["exercises"] = data.get("exercises", [])
                    st.session_state["tutorial_title"] = data.get("title", "Lancer le tutoriel")
                    st.session_state["timers"] = {
                        i: {
                            "status": "IDLE",
                            "start_time": 0.0,
                            "elapsed": 0.0,
                            "review_start_time": 0.0,
                            "review_elapsed": 0.0,
                        }
                        for i in range(len(st.session_state["exercises"]))
                    }
                st.success("Fichier chargé avec succès.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier JSON : {e}")

        if st.session_state["exercises"]:
            st.write("")
            if st.button(st.session_state["tutorial_title"], type="primary", use_container_width=True):
                st.session_state["page"] = "workspace"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGE 2 : ESPACE DE TRAVAIL / TUTORIEL
# ==========================================
elif st.session_state["page"] == "workspace":
    st.title(st.session_state["tutorial_title"])
    
    if st.button("Retour à l'accueil"):
        st.session_state["page"] = "welcome"
        st.session_state["exercises"] = []
        st.session_state["timers"] = {}
        st.rerun()

    has_running_timer = False

    for idx, ex in enumerate(st.session_state["exercises"]):
        st.divider()
        
        title_text = ex.get("title", f"Exercice {idx + 1}")
        st.markdown(f'<div class="exercise-header">{title_text}</div>', unsafe_allow_html=True)
        
        st.markdown(ex.get("question", ""))
        st.write("")

        timer_state = st.session_state["timers"].get(
            idx,
            {
                "status": "IDLE",
                "start_time": 0.0,
                "elapsed": 0.0,
                "review_start_time": 0.0,
                "review_elapsed": 0.0,
            },
        )
        status = timer_state["status"]
        allocated_secs = ex.get("time_seconds", 360)

        # 1. Calcul du temps d'exercice principal
        if status == "RUNNING":
            current_run = time.time() - timer_state["start_time"]
            total_elapsed = int(timer_state["elapsed"] + current_run)
        else:
            total_elapsed = int(timer_state["elapsed"])

        # 2. Calcul du temps de relecture / temps dépassé
        if status == "REVIEWING":
            current_review_run = time.time() - timer_state["review_start_time"]
            total_review_elapsed = int(timer_state["review_elapsed"] + current_review_run)
        else:
            total_review_elapsed = int(timer_state.get("review_elapsed", 0.0))

        rem = allocated_secs - total_elapsed

        col1, col2 = st.columns([1, 3])

        with col1:
            if status == "IDLE":
                if st.button(f"Démarrer #{idx + 1}", key=f"start_{idx}", type="primary"):
                    st.session_state["timers"][idx]["status"] = "RUNNING"
                    st.session_state["timers"][idx]["start_time"] = time.time()
                    st.rerun()

            elif status == "RUNNING":
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    # Premier clic "Terminé" : passe en mode correction/relecture
                    if st.button(f"Terminé #{idx + 1}", key=f"finish_{idx}", type="primary"):
                        st.session_state["timers"][idx]["elapsed"] = total_elapsed
                        st.session_state["timers"][idx]["status"] = "REVIEWING"
                        st.session_state["timers"][idx]["review_start_time"] = time.time()
                        st.rerun()
                with btn_col2:
                    if st.button(f"Pause #{idx + 1}", key=f"stop_{idx}", type="secondary"):
                        st.session_state["timers"][idx]["elapsed"] = total_elapsed
                        st.session_state["timers"][idx]["status"] = "STOPPED"
                        st.rerun()

            elif status == "STOPPED":
                if st.button(f"Reprendre #{idx + 1}", key=f"resume_{idx}"):
                    st.session_state["timers"][idx]["status"] = "RUNNING"
                    st.session_state["timers"][idx]["start_time"] = time.time()
                    st.rerun()

            elif status == "REVIEWING":
                # Deuxième clic "Terminé (Final)" : stoppe la horloge de relecture
                if st.button(f"Terminé (Final) #{idx + 1}", key=f"final_finish_{idx}", type="primary"):
                    st.session_state["timers"][idx]["review_elapsed"] = total_review_elapsed
                    st.session_state["timers"][idx]["status"] = "FINISHED"
                    st.rerun()

            elif status == "FINISHED":
                st.success("Exercice et correction terminés !")

        with col2:
            if status == "IDLE":
                target_mins = allocated_secs // 60
                target_secs = allocated_secs % 60
                st.write(f"Temps alloué : **{target_mins:02d}:{target_secs:02d}**")

            elif status == "RUNNING":
                has_running_timer = True
                rem_mins = abs(rem) // 60
                rem_secs = abs(rem) % 60

                if rem >= 0:
                    st.metric(label="Temps restant", value=f"{rem_mins:02d}:{rem_secs:02d}")
                else:
                    st.metric(label="Temps dépassé (en résolution)", value=f"+{rem_mins:02d}:{rem_secs:02d}")

            elif status == "REVIEWING":
                has_running_timer = True
                rev_mins = total_review_elapsed // 60
                rev_secs = total_review_elapsed % 60

                e_mins = total_elapsed // 60
                e_secs = total_elapsed % 60

                st.metric(
                    label="Temps de correction / relecture",
                    value=f"+{rev_mins:02d}:{rev_secs:02d}",
                    delta=f"Résolution effectuée en {e_mins:02d}:{e_secs:02d}",
                    delta_color="off"
                )

            elif status in ["STOPPED", "FINISHED"]:
                e_mins = total_elapsed // 60
                e_secs = total_elapsed % 60
                rev_mins = total_review_elapsed // 60
                rev_secs = total_review_elapsed % 60

                st.write(
                    f"Temps de recherche : **{e_mins:02d}:{e_secs:02d}** | "
                    f"Temps de correction : **{rev_mins:02d}:{rev_secs:02d}**"
                )

        if ex.get("hint"):
            with st.expander("Voir l'indice"):
                st.markdown(ex["hint"])

        # La correction s'ouvre automatiquement dès le passage en REVIEWING ou FINISHED, ou si le temps initial est écoulé
        should_expand_solution = (status in ["REVIEWING", "FINISHED", "STOPPED"]) or (status == "RUNNING" and rem <= 0)

        if ex.get("solution"):
            with st.expander("Voir la correction", expanded=should_expand_solution):
                st.markdown(ex["solution"])

    if has_running_timer:
        time.sleep(1)
        st.rerun()