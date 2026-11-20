"""Final archive links and an in-app quiz based on past exam topics."""

import json
from pathlib import Path

import streamlit as st


ATTEMPT_KEY = "final_quiz_attempt"
LETTERS = "ABCDE"


@st.cache_data(show_spinner=False)
def load_final_archive():
    path = Path(__file__).with_name("final_archive.json")
    return json.loads(path.read_text(encoding="utf-8"))


def show_final_quiz(app):
    st.subheader("Geçmiş Final Soruları")
    attempt = st.session_state.get(ATTEMPT_KEY)
    if attempt is None:
        show_final_setup(app)
        return

    questions = attempt["questions"]
    responses = attempt["responses"]
    st.caption(f'{attempt["course"]} · {attempt["period"]} · Uyarlanmış sorular')
    if attempt["finished"]:
        review = [
            {
                **question,
                "explanation": (
                    f'{question["explanation"]}\n\n'
                    f'[Kaynak · {question["year"]} finali]({question["source"]})'
                ),
            }
            for question in questions
        ]
        score = app["score_attempt"](questions, responses)
        app["show_review"](review, responses, score, header="Final testi sonucu")
        st.button(
            "Yeni final testi seç", type="primary", use_container_width=True,
            on_click=st.session_state.pop, args=(ATTEMPT_KEY, None),
        )
        return

    position = attempt["position"]
    question = questions[position]
    question_id = question["id"]
    choice_key = f"_final_choice_{question_id}"
    previous = responses.get(question_id)
    st.caption(f"Soru {position + 1} / {len(questions)} · {len(responses)} cevap işaretlendi")
    st.progress(len(responses) / len(questions))
    with st.container(border=True):
        st.markdown(f'**{question["question"]}**')
        st.radio(
            "Yanıtını seç", list(LETTERS),
            index=LETTERS.index(previous) if previous is not None else None,
            format_func=lambda letter: f'{letter}) {question["options"][letter]}',
            key=choice_key, on_change=save_final_answer, args=(question_id, choice_key),
        )
    previous_button, next_button = st.columns(2)
    previous_button.button(
        "← Önceki", disabled=position == 0, use_container_width=True,
        on_click=move_final_question, args=(-1,),
    )
    next_button.button(
        "Sonraki →", disabled=position == len(questions) - 1, use_container_width=True,
        on_click=move_final_question, args=(1,),
    )
    st.button(
        "Testi bitir ve cevapları gör", type="primary", use_container_width=True,
        on_click=finish_final_quiz,
    )
    with st.expander("Testi iptal et"):
        st.button(
            "Final testini iptal et", use_container_width=True,
            on_click=st.session_state.pop, args=(ATTEMPT_KEY, None),
        )


def show_final_setup(app):
    archive = load_final_archive()
    courses = [course["id"] for course in app["COURSES"]]
    labels = {course["id"]: course["name"] for course in app["COURSES"]}
    active_course = st.session_state["course"]
    course = st.selectbox(
        "Ders", courses, index=courses.index(active_course), format_func=labels.get,
        key="final_course",
    )
    entry = archive[course]
    questions = entry["questions"]
    years = sorted((entry["sets"].keys() | entry["sources"].keys()) - {"Tarihsiz"}, reverse=True)
    if "Tarihsiz" in entry["sets"]:
        years.append("Tarihsiz")
    year = st.selectbox(
        "Sınav yılı", [None, *years], key=f"final_year_{course}",
        format_func=lambda value: value or "Tüm yıllar (karma)",
    )
    selected = [question for question in questions if year in (None, question["year"])]
    period = year or "Tüm yıllar"
    st.caption("Uygulama içi sorular geçmiş final örneklerinden uyarlanmıştır.")
    if selected:
        st.write(f"**{len(selected)} açıklamalı soru**")
        st.button(
            "Final testine başla", type="primary", use_container_width=True,
            on_click=start_final_quiz, args=(labels[course], period, selected),
        )
    else:
        st.info("Bu yıl için kaynak sayfasından çalışabilirsin.")

    with st.container(border=True):
        st.markdown("#### Geçmiş final kaynakları")
        visible_years = [year] if year else years
        count = sum(len(entry["sets"].get(value, [])) for value in visible_years)
        if count:
            st.caption(f"Ön lisans kataloğunda {count} final seti kaydı var.")
            with st.expander("Katalogdaki final setleri", expanded=year is not None):
                for value in visible_years:
                    for number, exam in enumerate(entry["sets"].get(value, []), 1):
                        st.markdown(f'- [{value} · Set {number} ({exam["questions"]} soru)]({exam["url"]})')
        st.link_button("Dersin final arşivini aç", entry["catalog"], use_container_width=True)
        sources = {}
        for value in visible_years:
            source = entry["sources"].get(value)
            if source:
                sources.setdefault(source, []).append(value)
        for source, values in sources.items():
            st.markdown(f'- [Ek final kaynağı · {", ".join(values)}]({source})')


def start_final_quiz(course, period, questions):
    st.session_state[ATTEMPT_KEY] = {
        "course": course, "period": period, "questions": questions,
        "position": 0, "responses": {}, "finished": False,
    }


def save_final_answer(question_id, choice_key):
    responses = st.session_state[ATTEMPT_KEY]["responses"]
    answer = st.session_state.get(choice_key)
    if answer is None:
        responses.pop(question_id, None)
    else:
        responses[question_id] = answer


def move_final_question(step):
    attempt = st.session_state[ATTEMPT_KEY]
    attempt["position"] = min(max(0, attempt["position"] + step), len(attempt["questions"]) - 1)


def finish_final_quiz():
    st.session_state[ATTEMPT_KEY]["finished"] = True
