import streamlit as st
import random
import time
import csv
import pandas as pd
from datetime import datetime
import os

# --- Question bank ---
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

# --- App UI ---
st.set_page_config(page_title="Unit Circle Mad Minute", layout="centered")
st.title("⏱️ 1-Minute Unit Circle Challenge")

# Name input
if "name" not in st.session_state:
    st.session_state.name = ""

if st.session_state.name == "":
    st.session_state.name = st.text_input("Enter your name to begin:")

# Quiz logic
if st.session_state.name and "start_time" not in st.session_state:
    if st.button("Start Quiz"):
        st.session_state.start_time = time.time()
        st.session_state.score = 0
        st.session_state.index = 0
        st.session_state.questions = [generate_question() for _ in range(20)]
        st.session_state.attempted = 0

elif "start_time" in st.session_state:
    elapsed = time.time() - st.session_state.start_time
    remaining = int(60 - elapsed)
    
    if remaining <= 0:
        name = st.session_state.name
        score = st.session_state.score
        attempted = st.session_state.attempted
        accuracy = round(score / attempted * 100, 2) if attempted else 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Load previous results if they exist
        prev_accuracy = None
        if os.path.exists("results.csv"):
            df = pd.read_csv("results.csv")
            prev_rows = df[df['Name'] == name]
            if not prev_rows.empty:
                prev_accuracy = prev_rows.iloc[-1]['Accuracy']

        # Calculate improvement
        if prev_accuracy is not None and prev_accuracy != 0:
            improvement = round(((accuracy - prev_accuracy) / prev_accuracy) * 100, 2)
        else:
            improvement = 0.0

        # Save result
        with open("results.csv", "a", newline="") as f:
            writer = csv.writer(f)
            if os.stat("results.csv").st_size == 0:
                writer.writerow(["Name", "Score", "Attempted", "Accuracy", "Improvement %", "Timestamp"])
            writer.writerow([name, score, attempted, accuracy, improvement, now])

        st.success(f"⏰ Time's up! {name}, you scored {score} out of {attempted} — Accuracy: {accuracy}%")
        st.info(f"Change from last attempt: {improvement}%")

        if st.button("Restart"):
            st.session_state.clear()

    else:
        st.markdown(f"### 🕒 Time left: {remaining} seconds")
        q, a = st.session_state.questions[st.session_state.index]
        st.write(f"**Q{st.session_state.index + 1}:** {q}")
        user_answer = st.text_input("Your answer:", key=f"q{st.session_state.index}")

        if st.button("Submit Answer"):
            if user_answer.strip() == a:
                st.session_state.score += 1
            st.session_state.index += 1
            st.session_state.attempted += 1
            if st.session_state.index >= len(st.session_state.questions):
                st.session_state.questions += [generate_question() for _ in range(10)]
