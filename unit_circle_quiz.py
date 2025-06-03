import streamlit as st
import random
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# ---------------- Google Sheets Setup ----------------
SHEET_NAME = 'Unit Circle Results'  # Make sure this matches your actual Google Sheet name

def connect_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet

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

# ---------------- Quiz Logic ----------------

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

def generate_question():
    angle = random.choice(angles)
    angle_rad = angle[1]
    q_type = random.choice(["sin", "cos", "coord"])
    if q_type == "sin":
        return f"What is sin({angle_rad})?", angle[3]
    elif q_type == "cos":
        return f"What is cos({angle_rad})?", angle[2]
    else:
        return f"What are the coordinates at {angle_rad}?", f"({angle[2]}, {angle[3]})"

def generate_choices(correct, q_type):
    choices = {correct}
    while len(choices) < 4:
        if q_type == "coord":
            fake = f"({random.choice(['1/2', '0', '√2/2', '√3/2', '-1/2'])}, {random.choice(['1/2', '0', '√2/2', '√3/2', '-1'])})"
        else:
            fake = random.choice(["1", "0", "-1", "1/2", "-1/2", "√2/2", "-√2/2", "√3/2", "-√3/2"])
        choices.add(fake)
    return random.sample(list(choices), 4)

# ---------------- Streamlit UI ----------------

st.set_page_config(page_title="Unit Circle Mad Minute", layout="centered")
st.title("⏱️ 1-Minute Unit Circle Challenge")

# Input student name
if "name" not in st.session_state:
    st.session_state.name = ""

if st.session_state.name == "":
    st.session_state.name = st.text_input("Enter your name to begin:")

# Start quiz logic
if st.session_state.name and "start_time" not in st.session_state:
    if st.button("Start Quiz"):
        st.session_state.start_time = time.time()
        st.session_state.score = 0
        st.session_state.index = 0
        st.session_state.attempted = 0
        st.session_state.questions = [generate_question() for _ in range(20)]

elif "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(60 - elapsed)

    if remaining <= 0:
        name = st.session_state.name
        score = st.session_state.score
        attempted = st.session_state.attempted
        accuracy = round(score / attempted * 100, 2) if attempted else 0

        sheet = connect_sheet()
        prev_accuracy = get_last_accuracy(sheet, name)

        improvement = round(((accuracy - prev_accuracy) / prev_accuracy) * 100, 2) if prev_accuracy else 0.0
        append_result(sheet, name, score, attempted, accuracy, improvement)

        st.success(f"⏰ Time's up! {name}, you scored {score}/{attempted} — Accuracy: {accuracy}%")
        st.info(f"Change from last attempt: {improvement}%")

        if st.button("Restart"):
            st.session_state.clear()

    else:
        st.markdown(f"### 🕒 Time left: {remaining} seconds")

        question, correct_answer = st.session_state.questions[st.session_state.index]
        q_type = "coord" if "coordinates" in question else "sin" if "sin" in question else "cos"
        choices = generate_choices(correct_answer, q_type)

        st.write(f"**Q{st.session_state.index + 1}:** {question}")
        selected = st.radio("Choose your answer:", choices, key=f"q{st.session_state.index}")

        if st.button("Submit Answer"):
            if selected == correct_answer:
                st.session_state.score += 1
            st.session_state.index += 1
            st.session_state.attempted += 1
            if st.session_state.index >= len(st.session_state.questions):
                st.session_state.questions += [generate_question() for _ in range(10)]

