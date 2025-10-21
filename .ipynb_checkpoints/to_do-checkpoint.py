import streamlit as st
import pandas as pd
from datetime import date
import calendar
from pathlib import Path

st.set_page_config(page_title="To Do", layout="wide")

# ---------- File setup ----------
DATA_FILE = Path("tasks.csv")

def load_tasks():
    if DATA_FILE.exists():
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["Task", "Category", "Due Date", "Priority", "Completed"])

def save_tasks(df):
    df.to_csv(DATA_FILE, index=False)

# Sample priority colors
priority_colors = {"> 45 Minutes": "#832120", "15-45 Minutes": "#CE713B", "< 15 Minutes": "#FABC75"}

# Title
st.markdown("<h1>Much To Do About Nothing!</h1>", unsafe_allow_html=True)

# --- Initialize tasks ---
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# --- Sidebar: Add task ---
with st.sidebar:
    st.header("+ Add Task")
    with st.form("new_task_form", clear_on_submit=True):
        task = st.text_input("Task name")
        category = st.text_input("Category")
        due_date = st.date_input("Due date", value=date.today())
        priority = st.selectbox("Time", ["> 45 Minutes", "15-45 Minutes", "< 15 Minutes"])
        submitted = st.form_submit_button("Add task")

        if submitted and task:
            due_date_str = due_date.strftime("%m-%d-%Y")
            new_task = {
                "Task": task,
                "Category": category,
                "Due Date": due_date_str,
                "Priority": priority,
                "Completed": False
            }
            st.session_state.tasks = pd.concat(
                [st.session_state.tasks, pd.DataFrame([new_task])],
                ignore_index=True
            )
            save_tasks(st.session_state.tasks)
            st.success(f"Added: {task}")

# --- Sidebar: Category overview ---
st.sidebar.header("Category Overview")

tasks = st.session_state.tasks.copy()

if not tasks.empty:
    categories = sorted(tasks["Category"].dropna().unique().tolist())

    # Separate active vs inactive categories
    active_categories = []
    inactive_categories = []

    for cat in categories:
        cat_tasks = tasks[tasks["Category"] == cat]
        if not cat_tasks.empty:
            if cat_tasks["Completed"].all():
                inactive_categories.append(cat)
            else:
                active_categories.append(cat)

    # --- Active Categories ---
    st.sidebar.subheader("Active")
    if active_categories:
        for cat in active_categories:
            with st.sidebar.expander(cat, expanded=False):
                cat_tasks = tasks[tasks["Category"] == cat]
                for i, row in cat_tasks.iterrows():
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        completed = st.checkbox(
                            f"{row['Task']} | Due {row['Due Date']} | {row['Priority']}",
                            value=row["Completed"],
                            key=f"sidebar_{cat}_{i}"
                        )
                        if completed != row["Completed"]:
                            st.session_state.tasks.at[i, "Completed"] = completed
                            save_tasks(st.session_state.tasks)
                    with col2:
                        delete = st.button("🗑️", key=f"delete_{cat}_{i}")
                        if delete:
                            st.session_state.tasks = st.session_state.tasks.drop(i).reset_index(drop=True)
                            save_tasks(st.session_state.tasks)
                            st.rerun()
    else:
        st.sidebar.info("No active tasks!")

    # --- Inactive Categories ---
    st.sidebar.subheader("Inactive")
    if inactive_categories:
        for cat in inactive_categories:
            with st.sidebar.expander(cat, expanded=False):
                cat_tasks = tasks[tasks["Category"] == cat]
                for i, row in cat_tasks.iterrows():
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        completed = st.checkbox(
                            f"{row['Task']} | Due {row['Due Date']} | {row['Priority']}",
                            value=row["Completed"],
                            key=f"inactive_{cat}_{i}"
                        )
                        if completed != row["Completed"]:
                            st.session_state.tasks.at[i, "Completed"] = completed
                            save_tasks(st.session_state.tasks)
                    with col2:
                        delete = st.button("🗑️", key=f"delete_inactive_{cat}_{i}")
                        if delete:
                            st.session_state.tasks = st.session_state.tasks.drop(i).reset_index(drop=True)
                            save_tasks(st.session_state.tasks)
                            st.rerun()
    else:
        st.sidebar.info("No inactive categories.")
else:
    st.sidebar.info("No tasks added yet.")


# --- Calendar view ---
calendar_tasks = st.session_state.tasks.copy()
calendar_tasks["Due Date"] = pd.to_datetime(calendar_tasks["Due Date"], errors='coerce')

today = date.today()
col1, col2 = st.columns(2)

with col1:
    month = st.selectbox("Month", list(calendar.month_name)[1:], index=today.month - 1, key="month_select")
with col2:
    year = st.selectbox("Year", range(2025, 2101), index=today.year - 2025, key="year_select")

month_num = list(calendar.month_name).index(month)
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdatescalendar(year, month_num)

# Build HTML calendar
html_calendar = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: center; table-layout: fixed;'>"
html_calendar += "<tr>" + "".join(f"<th>{day}</th>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]) + "</tr>"

all_dates = []
for week in month_days:
    html_calendar += "<tr>"
    for day in week:
        all_dates.append(day)
        day_tasks = calendar_tasks[calendar_tasks["Due Date"].dt.date == day]
        if day.month != month_num:
            html_calendar += "<td style='background-color:#f0f0f0; color:#999;'> </td>"
        elif not day_tasks.empty:
            tasks_text = ""
            for _, row in day_tasks.iterrows():
                color = priority_colors.get(row["Priority"], "#ffffff")
                if row["Completed"]:
                    tasks_text += f"<div style='background-color:#d3d3d3; color:#888; margin:2px; padding:2px; border-radius:4px; text-decoration:line-through; word-break: break-word;'>{row['Task']}</div>"
                else:
                    tasks_text += f"<div style='background-color:{color}; margin:2px; padding:2px; border-radius:4px; word-break: break-word;'>{row['Task']}</div>"
            html_calendar += f"<td style='vertical-align: top; padding:2px;'><strong>{day.day}</strong><br>{tasks_text}</td>"
        else:
            html_calendar += f"<td style='vertical-align: top; padding:2px;'>{day.day}</td>"
    html_calendar += "</tr>"
html_calendar += "</table>"

st.markdown(html_calendar, unsafe_allow_html=True)

# --- Interactive day selection ---
date_options = [d for d in all_dates if d.month == month_num]
selected_day = st.selectbox("Select a day", date_options, format_func=lambda d: d.strftime("%Y-%m-%d"))

day_tasks = calendar_tasks[calendar_tasks["Due Date"].dt.date == selected_day]
if not day_tasks.empty:
    st.table(day_tasks[["Task", "Category", "Priority", "Completed"]])
else:
    st.info("Nothing to do!")

##### Styling #####
st.markdown("""
<style>
    .stApp { background-color: #e2ebf3; }
    html, body, [class*="css"] { font-family: 'Helvetica', sans-serif; color: #556277; }
    .stMarkdown, .stMarkdown p, .stMarkdown li { font-family: 'Helvetica', sans-serif; color: #556277; }
    .stMarkdown h1 { color: #556277; }
    .stMarkdown h2, .stMarkdown h3 { color: #B15E6C; }
    section[data-testid="stSidebar"] { background-color: #E2EBF3; }
    button { background-color: #b15e6c !important; color: white !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# Delete Button Styling
st.markdown("""
<style>
/* Target only buttons whose key starts with "delete_" */
div[data-testid^="stButton"][data-testid*="delete_"] button {
    background-color: #E2EBF3 !important;
    color: #556277 !important;
    border: 1px solid #E2EBF3 !important;
    border-radius: 6px !important;
    padding: 0.2rem 0.5rem !important;
}
div[data-testid^="stButton"][data-testid*="delete_"] button:hover {
    background-color: #E2EBF3 !important;
}
</style>
""", unsafe_allow_html=True)

# Make Sidebar Headers Match Main Header
st.markdown("""
<style>
/* Match sidebar headers to main page header style */
section[data-testid="stSidebar"] h2,  /* Sidebar headers */
section[data-testid="stSidebar"] h3   /* Sidebar subheaders */ {
    font-family: 'Helvetica', sans-serif;
    color: #556277;  /* Same as main page h1 */
}
</style>
""", unsafe_allow_html=True)

