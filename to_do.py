import streamlit as st
import pandas as pd
from datetime import date
import calendar
from pathlib import Path

st.set_page_config(page_title="To Do", layout="wide")

#####################################

## File Setup
DATA_FOLDER = Path("user_tasks")
DATA_FOLDER.mkdir(exist_ok=True)

## Helper functions 
def load_tasks(data_file):
    if data_file.exists():
        return pd.read_csv(data_file)
    return pd.DataFrame(columns=["Task", "Category", "Due Date", "Priority", "Completed"])

def save_tasks(df, data_file):
    df.to_csv(data_file, index=False)

## Colors for Task Time 
priority_colors = {
    "> 45 Minutes": "#832120",
    "15-45 Minutes": "#CE713B",
    "< 15 Minutes": "#FABC75"
}

## Login Page 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "secret_key" not in st.session_state:
    st.session_state.secret_key = ""

if not st.session_state.authenticated:
    st.markdown(f"<h1>Much To Do About Nothing!</h1>", unsafe_allow_html=True)
    st.markdown("Welcome! Please log in to access your to-do list.")

    with st.form("login_form"):
        user_name = st.text_input("Username")
        secret_key = st.text_input("Password:", type="password")
        submitted = st.form_submit_button("Log In")

        if submitted:
            if user_name and secret_key:
                st.session_state.user_name = user_name
                st.session_state.secret_key = secret_key
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.warning("Please enter both a name and secret key to continue.")
    st.stop()

## After login 
user_name = st.session_state.user_name
secret_key = st.session_state.secret_key
user_id = f"{user_name.lower().replace(' ', '_')}_{secret_key}"
DATA_FILE = DATA_FOLDER / f"tasks_{user_id}.csv"

## Load tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks(DATA_FILE)

tasks = st.session_state.tasks.copy()

#####################################

## Title 
st.markdown(f"<h1>Much To Do About Nothing!</h1>", unsafe_allow_html=True)

## Sidebar: Add task 
with st.sidebar:
    st.header("+ Add Task")
    with st.form("new_task_form", clear_on_submit=True):
        task = st.text_input("Task name")
        category = st.text_input("Category")
        due_date = st.date_input("Due date", value=date.today())
        priority = st.selectbox("Time", ["> 45 Minutes", "15-45 Minutes", "< 15 Minutes"])
        description = st.text_area("Description (optional)")   
        submitted = st.form_submit_button("Add task")

        if submitted and task:
            due_date_str = due_date.strftime("%m-%d-%Y")
            new_task = {
                "Task": task,
                "Category": category,
                "Due Date": due_date_str,
                "Priority": priority,
                "Completed": False,
                "Description": description  
            }
            st.session_state.tasks = pd.concat(
                [st.session_state.tasks, pd.DataFrame([new_task])],
                ignore_index=True
            )
            save_tasks(st.session_state.tasks, DATA_FILE)
            st.success(f"Added: {task}")


## Sidebar: Category overview 
st.sidebar.header("Category Overview")

if not tasks.empty:
    categories = sorted(tasks["Category"].dropna().unique().tolist())
    active_categories = []
    inactive_categories = []

    for cat in categories:
        cat_tasks = tasks[tasks["Category"] == cat]
        if not cat_tasks.empty:
            if cat_tasks["Completed"].all():
                inactive_categories.append(cat)
            else:
                active_categories.append(cat)

    st.sidebar.subheader("Active")
    if active_categories:
        for cat in active_categories:
            # Category name now appears as the label of the expander
            with st.sidebar.expander(f"### {cat}", expanded=False):
                cat_tasks = tasks[tasks["Category"] == cat]
                for i, row in cat_tasks.iterrows():
                    st.markdown(f"- {row['Task']}")
    else:
        st.sidebar.info("No active tasks!")

    st.sidebar.subheader("Inactive")
    if inactive_categories:
        for cat in inactive_categories:
            with st.sidebar.expander(f"### {cat}", expanded=False):
                cat_tasks = tasks[tasks["Category"] == cat]
                for i, row in cat_tasks.iterrows():
                    st.markdown(f"- {row['Task']}")
    else:
        st.sidebar.info("No inactive categories.")
else:
    st.sidebar.info("No tasks added yet.")

## Calendar view 
calendar_tasks = st.session_state.tasks.copy()
calendar_tasks["Due Date"] = pd.to_datetime(calendar_tasks["Due Date"], errors='coerce')

today = date.today()

## Initialize session state for month/year 
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year

col1, col2, col3 = st.columns([1, 2, 1])

prev_clicked = col1.button("←")
next_clicked = col3.button("→")

if prev_clicked:
    if st.session_state.cal_month == 1:
        st.session_state.cal_month = 12
        st.session_state.cal_year -= 1
    else:
        st.session_state.cal_month -= 1

if next_clicked:
    if st.session_state.cal_month == 12:
        st.session_state.cal_month = 1
        st.session_state.cal_year += 1
    else:
        st.session_state.cal_month += 1

with col2:
    st.markdown(
        f"### {calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}",
        unsafe_allow_html=True
    )


month_num = st.session_state.cal_month
year = st.session_state.cal_year

cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdatescalendar(year, month_num)

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
                    tasks_text += f"<div style='background-color:{color}; color:white; margin:2px; padding:2px; border-radius:4px; word-break: break-word;'>{row['Task']}</div>"
            html_calendar += f"<td style='vertical-align: top; padding:2px;'><strong>{day.day}</strong><br>{tasks_text}</td>"
        else:
            html_calendar += f"<td style='vertical-align: top; padding:2px;'>{day.day}</td>"
    html_calendar += "</tr>"
html_calendar += "</table>"

st.markdown(html_calendar, unsafe_allow_html=True)

## Interactive day selection (replace dropdown with mini calendar) 
selected_day = st.date_input(
    "Select a day",
    value=date.today(),
    min_value=date(today.year, 1, 1),
    max_value=date(today.year + 5, 12, 31)
)

## Filter tasks for the selected day
day_tasks = calendar_tasks[calendar_tasks["Due Date"].dt.date == selected_day]

if not day_tasks.empty:
    for i, row in day_tasks.iterrows():
        col1, col2, col3 = st.columns([0.1, 0.75, 0.15])

        with col1:  
            completed = st.checkbox(
                "",
                value=row["Completed"],
                key=f"main_completed_{i}"
            )
            if completed != row["Completed"]:
                st.session_state.tasks.at[i, "Completed"] = completed
                save_tasks(st.session_state.tasks, DATA_FILE)

        with col2:  
            task_text = f"{row['Task']}"
            if "Description" in row and pd.notna(row["Description"]) and row["Description"] != "":
                task_text += f": {row['Description']}"
            st.markdown(task_text)

        with col3:  
            delete = st.button("X", key=f"main_delete_{i}")
            if delete:
                st.session_state.tasks = st.session_state.tasks.drop(i).reset_index(drop=True)
                save_tasks(st.session_state.tasks, DATA_FILE)
                st.rerun()
else:
    st.info("Nothing to do!")

#####################################

## HTML Styling 
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


