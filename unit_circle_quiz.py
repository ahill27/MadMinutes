import streamlit as st
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# --- Connect to Google Sheets ---
def connect_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Unit Circle Results").sheet1
        return sheet
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

def get_last_accuracy(sheet, name):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return None
    user_rows = df[df['Name'] == name]
    if user_rows.empty:
        return None
    return float(user_rows.iloc[-1]['Accuracy'])

def append_result(sheet, name, score, attempted, accuracy, improvement):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row = [name, score, attempted, accuracy, improvement, now]
    sheet.append_row(row)

# --- Angle bank ---
angles = [
    (0, "0", "1", "0"),
    (30, "π/6", "√3/2", "1/2"),
    (45, "π/4", "√2/2", "√2/2"),
    (60, "π/3", "1/2", "√3/2"),
    (90, "π/2", "0", "1"),
    (120, "2π/3", "-1/2", "√3/2"),
    (135, "3π/4", "-√2/2", "√2/2"),
    (150, "5π/6", "-√3/2", "1/2"),
    (180, "π", "-1", "0"),
    (210, "7π/6", "-√3/2", "-1/2"),
    (225, "5π/4", "-√2/2", "-√2/2"),
    (240, "4π/3", "-1/2", "-√3/2"),
    (270, "3π/2", "0", "-1"),
    (300, "5π/3", "1/2", "-√3/2"),
    (315, "7π/4", "√2/2", "-√2/2"),
    (330, "11π/6", "√3/2", "-1/2"),
    (360, "2π", "1", "0")
]

# --- Question Generator ---
def generate_question():
    angle = random.choice(angles)
    angle_deg, angle_rad, cos_val, sin_val = angle
    q_type = random.choice(["sin", "cos", "coord", "convert_deg", "convert_rad", "find_angle_sin", "find_angle_cos"])

    if q_type == "sin":
        return f"What is sin({angle_rad})?", sin_val, q_type
    elif q_type == "cos":
        return f"What is cos({angle_rad})?", cos_val, q_type
    elif q_type == "coord":
        return f"What are the coordinates at {angle_rad}?", f"({cos_val}, {sin_val})", q_type
    elif q_type == "convert_deg":
        return f"Convert {angle_deg}° to radians.", angle_rad, q_type
    elif q_type == "convert_rad":
        return f"Convert {angle_rad} to degrees.", str(angle_deg), q_type
    elif q_type == "find_angle_sin":
        return f"At which angle is sin(θ) = {sin_val}?", angle_rad, q_type
    elif q_type == "find_angle_cos":
        return f"At which angle is cos(θ) = {cos_val}?", angle_rad, q_type

# --- Generate multiple choices ---
def generate_choices(correct, q_type):
    choices = {correct}
    while len(choices) < 4:
        if q_type == "coord":
            fake = f"({random.choice(['1/2', '0', '√2/2', '√3/2', '-1/2'])}, {random.choice(['1/2', '0', '√2/2', '√3/2', '-1'])})"
        elif q_type == "convert_deg":
            fake = random.choice(["π/4", "π/2", "π", "3π/2", "2π", "7π/6", "5π/3"])
        elif q_type == "convert_rad":
            fake = str(random.choice([0, 30, 45, 60, 90, 120, 135, 150, 180, 270, 300, 360]))
        elif "find_angle" in q_type:
            fake = random.choice([a[1] for a in angles if a[1] != correct])
        else:
            fake = random.choice(["1", "0", "-1", "1/2", "-1/2", "√2/2", "-√2/2", "√3/2", "-√3/2"])
        choices.add(fake)
    return random.sample(list(choices), 4)



# --- Streamlit UI ---
if "just_reran" not in st.session_state:
    st.session_state.just_reran = False
st.set_page_config(page_title="Unit Circle Mad Minute", layout="centered")
st.title("⏱️ 1-Minute Unit Circle Challenge")

if "name" not in st.session_state:
    st.session_state.name = ""

if st.session_state.name == "":
    st.session_state.name = st.text_input("Enter your name to begin:")

if st.session_state.name and "start_time" not in st.session_state:
    if st.button("Start Quiz"):
        st.session_state.start_time = time.time()
        st.session_state.score = 0
        st.session_state.index = 0
        st.session_state.attempted = 0
        st.session_state.questions = [generate_question() for _ in range(30)]
        st.session_state.answered = -1

elif "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(60 - elapsed)

    if remaining <= 0:
        name = st.session_state.name
        score = st.session_state.score
        attempted = st.session_state.attempted
        accuracy = round(score / attempted * 100, 2) if attempted else 0

        sheet = connect_sheet()
        if sheet:
            try:
                prev_accuracy = get_last_accuracy(sheet, name)
            except Exception as e:
                st.warning(f"Couldn't fetch previous score: {e}")
                prev_accuracy = None

            improvement = round(((accuracy - prev_accuracy) / prev_accuracy) * 100, 2) if prev_accuracy else 0.0
            append_result(sheet, name, score, attempted, accuracy, improvement)

            st.success(f"⏰ Time's up! {name}, you scored {score}/{attempted} — Accuracy: {accuracy}%")
            st.info(f"Change from last attempt: {improvement}%")

        if st.button("Restart"):
            st.session_state.clear()

    else:
        st.markdown(f"<h2>🕒 Time left: {remaining} seconds</h2>", unsafe_allow_html=True)

        question_data = st.session_state.questions[st.session_state.index]
        st.session_state.just_reran = False
        st.session_state.current_question = question_data
        question, correct_answer, q_type = question_data
        choices = generate_choices(correct_answer, q_type)
        st.markdown(f"<h3>Q{st.session_state.index + 1}: {question}</h3>", unsafe_allow_html=True)

        selected = st.radio(
            "Choose your answer:",
            options=choices,
            index=None,
            key=f"q_{st.session_state.index}"
        )

        if selected is not None:
            st.session_state.attempted += 1
            if selected == correct_answer:
                st.session_state.score += 1
            st.session_state.index += 1
            st.experimental_rerun()




    
