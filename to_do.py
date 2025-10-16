import streamlit as st
import pandas as pd
from datetime import date
import calendar

st.set_page_config(page_title="To Do", layout="wide")

# Sample priority colors
priority_colors = {"High": "#FF6B6B", "Medium": "#FFA500", "Low": "#90EE90"}

# Title
st.markdown("<h1>To DO!</h1>", unsafe_allow_html=True)

# --- Initialize tasks ---
if "tasks" not in st.session_state:
    st.session_state.tasks = pd.DataFrame(columns=["Task", "Category", "Due Date", "Priority"])

# --- Sidebar: Add task ---
with st.sidebar:
    st.header("➕ Add a new task")
    with st.form("new_task_form", clear_on_submit=True):
        task = st.text_input("Task name")
        category = st.text_input("Category")
        due_date = st.date_input("Due date", value=date.today())
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Add task")
        
        if submitted and task:
            # Convert date to MM-DD-YYYY string
            due_date_str = due_date.strftime("%m-%d-%Y")  # 10-09-2025
            new_task = {
                "Task": task,
                "Category": category,
                "Due Date": due_date_str,
                "Priority": priority
            }
            st.session_state.tasks = pd.concat(
                [st.session_state.tasks, pd.DataFrame([new_task])],
                ignore_index=True
            )
            st.success(f"Added: {task}")

# --- Sidebar: Category overview ---
st.sidebar.header("Category")

tasks = st.session_state.tasks.copy()

if not tasks.empty:
    categories = sorted(tasks["Category"].dropna().unique().tolist())
    for cat in categories:
        with st.sidebar.expander(cat, expanded=False):
            cat_tasks = tasks[tasks["Category"] == cat]
            for _, row in cat_tasks.iterrows():
                color = priority_colors.get(row["Priority"], "#ffffff")
                st.markdown(
                    f"- {row['Task']} | Due: {row['Due Date'].strftime('%Y-%m-%d')} "
                    f"| <span style='color:{color}; font-weight:bold'>{row['Priority']}</span>",
                    unsafe_allow_html=True
                )
else:
    st.sidebar.info("No tasks added yet.")
    
# --- Calendar view ---
calendar_tasks = st.session_state.tasks.copy()
calendar_tasks["Due Date"] = pd.to_datetime(calendar_tasks["Due Date"])

today = date.today()

col1, col2 = st.columns(2)

with col1:
    month = st.selectbox("Month", list(calendar.month_name)[1:], index=today.month - 1, key="month_select")

with col2:
    year = st.selectbox("Year", range(1900, 2101), index=today.year - 1900, key="year_select")

month_num = list(calendar.month_name).index(month)
cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdatescalendar(year, month_num)

priority_colors = {"High": "#FF6B6B", "Medium": "#FFA500", "Low": "#90EE90"}

# Build HTML calendar
html_calendar = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: center;'>"
html_calendar += "<tr>" + "".join(f"<th>{day}</th>" for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]) + "</tr>"

# Collect all dates in the month for day selection
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
                tasks_text += f"<div style='background-color:{color}; margin:2px; padding:2px; border-radius:4px;'>{row['Task']}</div>"
            html_calendar += f"<td><strong>{day.day}</strong><br>{tasks_text}</td>"
        else:
            html_calendar += f"<td>{day.day}</td>"
    html_calendar += "</tr>"
html_calendar += "</table>"

st.markdown(html_calendar, unsafe_allow_html=True)

# --- Interactive day selection ---
date_options = [d for d in all_dates if d.month == month_num]
selected_day = st.selectbox("Select a day", date_options, format_func=lambda d: d.strftime("%Y-%m-%d"))

day_tasks = calendar_tasks[calendar_tasks["Due Date"].dt.date == selected_day]
if not day_tasks.empty:
    st.table(day_tasks[["Task", "Category", "Priority"]])
else:
    st.info("No tasks for this day.")



##### Styling #####
st.markdown("""
<style>

        /* App background & font defaults */
    .stApp { background-color: #e2ebf3; }
    html, body, [class*="css"] { font-family: 'Helvetica', sans-serif; color: #556277; }
    .stMarkdown, .stMarkdown p, .stMarkdown li { font-family: 'Helvetica', sans-serif; color: #556277; }

    /* Headings */
    .stMarkdown h1 { color: #556277; }
    .stMarkdown h2, .stMarkdown h3 { color: #B15E6C; }
    
   

    /* Target markdown headings */
    .stMarkdown h1 { color: #556277; }  /* Main title color */
    .stMarkdown h2,
    h2 {
        color: #B15E6C !important;
        font-family: 'Helvetica', sans-serif !important;
    }
    .stMarkdown h3,
    h3 {
        color: #B15E6C !important;
        font-family: 'Helvetica', sans-serif !important;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] { 
        background-color: #E2EBF3; 
    }

    /* Button styling */
    button { 
        background-color: #b15e6c !important; 
        color: white !important; 
        border-radius: 8px !important; 
    }

    /* Sidebar body text */
    section[data-testid="stSidebar"] {
        color: #556277;        /* Default text color in sidebar */
        font-family: 'Helvetica', sans-serif;
}

    /* Sidebar headers (e.g., "Add New Recipe", "Recycling Bin") */
    section[data-testid="stSidebar"] h2 {
        color: #556277;        /* Match body text color */
        font-family: 'Helvetica', sans-serif;
}

    /* Buttons inside the sidebar */
    section[data-testid="stSidebar"] button {
        color: white !important;             /* Button text color */
        background-color: #b15e6c !important;  /* Button background */
        border-radius: 8px !important;
        font-family: 'Helvetica', sans-serif;
}

    /* Sidebar input boxes and textareas */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select {
        background-color: white !important;  /* Force white background */
        color: #556277 !important;           /* Match body text color */
        font-family: 'Helvetica', sans-serif;
}

    /* Force sidebar selectboxes to have white background and dark text */
    section[data-testid="stSidebar"] div[role="combobox"] > div,
    section[data-testid="stSidebar"] div[role="combobox"] input {
        background-color: white !important;
        color: #556277 !important;
        font-family: 'Helvetica', sans-serif !important;
}
      
</style>
  
""", unsafe_allow_html=True)
