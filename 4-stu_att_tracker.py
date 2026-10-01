import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import date, datetime
import math

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Student Attendance Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path("data")
STUDENTS_FILE = DATA_DIR / "students.json"
ATTENDANCE_FILE = DATA_DIR / "attendance.json"

LOW_ATTENDANCE_LIMIT = 75.0


# ============================================================
# FILE MANAGEMENT
# ============================================================

def initialize_files():
    """Create data directory and JSON files if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not STUDENTS_FILE.exists():
        STUDENTS_FILE.write_text("[]", encoding="utf-8")

    if not ATTENDANCE_FILE.exists():
        ATTENDANCE_FILE.write_text("[]", encoding="utf-8")


def load_json(file_path):
    """Safely load JSON data."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_json(file_path, data):
    """Save data to JSON."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_students():
    return load_json(STUDENTS_FILE)


def load_attendance():
    return load_json(ATTENDANCE_FILE)


# ============================================================
# SESSION STATE
# ============================================================

def initialize_session():
    if "students" not in st.session_state:
        st.session_state.students = load_students()

    if "attendance" not in st.session_state:
        st.session_state.attendance = load_attendance()

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"


initialize_files()
initialize_session()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def save_students():
    save_json(STUDENTS_FILE, st.session_state.students)


def save_attendance():
    save_json(ATTENDANCE_FILE, st.session_state.attendance)


def student_exists(student_id):
    return any(
        s["student_id"].lower() == student_id.lower()
        for s in st.session_state.students
    )


def get_student(student_id):
    for student in st.session_state.students:
        if student["student_id"] == student_id:
            return student

    return None


def get_student_name(student_id):
    student = get_student(student_id)

    if student:
        return student["name"]

    return "Unknown"


def get_student_stats(student_id, subject=None):
    """Calculate attendance statistics for a student."""

    total = 0
    present = 0

    for record in st.session_state.attendance:

        if subject and record.get("subject") != subject:
            continue

        attendance_data = record.get("attendance", {})

        if student_id in attendance_data:
            total += 1

            if attendance_data[student_id] == "Present":
                present += 1

    absent = total - present

    percentage = (present / total * 100) if total > 0 else 0

    return {
        "total": total,
        "present": present,
        "absent": absent,
        "percentage": percentage
    }


def get_all_subjects():
    subjects = set()

    for record in st.session_state.attendance:
        subject = record.get("subject")

        if subject:
            subjects.add(subject)

    return sorted(subjects)


def attendance_status(percentage):
    if percentage < 75:
        return "🔴 Low"
    elif percentage < 85:
        return "🟡 Average"
    else:
        return "🟢 Good"


def calculate_required_classes(present, total):
    """
    Calculate number of consecutive classes a student
    needs to attend to reach 75%.
    """

    if total == 0:
        return 0

    if (present / total) * 100 >= 75:
        return 0

    required = math.ceil((0.75 * total - present) / 0.25)

    return max(required, 0)


def attendance_dataframe():
    rows = []

    for student in st.session_state.students:

        stats = get_student_stats(student["student_id"])

        rows.append({
            "Student ID": student["student_id"],
            "Name": student["name"],
            "Department": student["department"],
            "Section": student["section"],
            "Year": student["year"],
            "Total Classes": stats["total"],
            "Present": stats["present"],
            "Absent": stats["absent"],
            "Attendance %": round(stats["percentage"], 2),
            "Status": attendance_status(stats["percentage"])
        })

    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🎓 Attendance Tracker")

    st.markdown("---")

    pages = {
        "📊 Dashboard": "Dashboard",
        "👨‍🎓 Students": "Students",
        "📝 Take Attendance": "Take Attendance",
        "📈 Reports": "Reports",
        "⚠️ Low Attendance": "Low Attendance",
        "⚙️ Settings": "Settings"
    }

    selected_page = st.radio(
        "Navigation",
        list(pages.keys()),
        label_visibility="collapsed"
    )

    st.session_state.page = pages[selected_page]

    st.markdown("---")

    st.caption("Local JSON Storage")
    st.caption("No database required")


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "Dashboard":

    st.title("📊 Attendance Dashboard")
    st.write("Monitor students and attendance from one place.")

    students = st.session_state.students
    attendance = st.session_state.attendance

    total_students = len(students)
    total_classes = len(attendance)

    if total_students > 0:

        percentages = []

        low_count = 0
        good_count = 0

        for student in students:

            stats = get_student_stats(student["student_id"])

            if stats["total"] > 0:

                percentages.append(stats["percentage"])

                if stats["percentage"] < LOW_ATTENDANCE_LIMIT:
                    low_count += 1
                else:
                    good_count += 1

        average_attendance = (
            sum(percentages) / len(percentages)
            if percentages
            else 0
        )

    else:
        average_attendance = 0
        low_count = 0
        good_count = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👨‍🎓 Students",
            total_students
        )

    with col2:
        st.metric(
            "📚 Classes",
            total_classes
        )

    with col3:
        st.metric(
            "📊 Average Attendance",
            f"{average_attendance:.1f}%"
        )

    with col4:
        st.metric(
            "⚠️ Below 75%",
            low_count
        )

    st.markdown("---")

    if low_count > 0:
        st.warning(
            f"⚠️ {low_count} student(s) currently have attendance below 75%."
        )
    else:
        st.success("🎉 No student is currently below 75% attendance.")

    if not students:

        st.info(
            "No students have been added yet. "
            "Go to **Students → Add Student**."
        )

    else:

        st.subheader("📋 Attendance Overview")

        df = attendance_dataframe()

        if not df.empty:

            display_df = df[
                [
                    "Student ID",
                    "Name",
                    "Department",
                    "Section",
                    "Total Classes",
                    "Present",
                    "Absent",
                    "Attendance %",
                    "Status"
                ]
            ]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )

            if "Attendance %" in df.columns:

                chart_df = df[
                    ["Name", "Attendance %"]
                ].set_index("Name")

                st.subheader("📈 Student Attendance")

                st.bar_chart(chart_df)


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

elif st.session_state.page == "Students":

    st.title("👨‍🎓 Student Management")

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Add Student",
            "📋 View Students",
            "✏️ Edit / Delete"
        ]
    )

    # --------------------------------------------------------
    # ADD STUDENT
    # --------------------------------------------------------

    with tab1:

        st.subheader("Add New Student")

        with st.form("add_student_form"):

            col1, col2 = st.columns(2)

            with col1:

                student_id = st.text_input(
                    "Student ID / Roll Number *",
                    placeholder="Example: CSE001"
                )

                name = st.text_input(
                    "Student Name *",
                    placeholder="Example: Rahul Kumar"
                )

                department = st.text_input(
                    "Department *",
                    placeholder="Example: CSE"
                )

            with col2:

                section = st.selectbox(
                    "Section",
                    ["A", "B", "C", "D", "E"]
                )

                year = st.selectbox(
                    "Year",
                    ["1", "2", "3", "4"]
                )

                email = st.text_input(
                    "Email",
                    placeholder="student@example.com"
                )

            submitted = st.form_submit_button(
                "➕ Add Student",
                use_container_width=True
            )

        if submitted:

            student_id = student_id.strip()
            name = name.strip()
            department = department.strip()
            email = email.strip()

            if not student_id or not name or not department:

                st.error(
                    "Please fill all required fields."
                )

            elif student_exists(student_id):

                st.error(
                    f"Student ID '{student_id}' already exists."
                )

            else:

                new_student = {
                    "student_id": student_id,
                    "name": name,
                    "department": department,
                    "section": section,
                    "year": year,
                    "email": email
                }

                st.session_state.students.append(new_student)

                save_students()

                st.success(
                    f"Student '{name}' added successfully."
                )

                st.rerun()

    # --------------------------------------------------------
    # VIEW STUDENTS
    # --------------------------------------------------------

    with tab2:

        st.subheader("Student List")

        if not st.session_state.students:

            st.info("No students available.")

        else:

            search = st.text_input(
                "🔎 Search students",
                placeholder="Search by ID or name"
            )

            filtered_students = st.session_state.students

            if search:

                search = search.lower()

                filtered_students = [
                    s
                    for s in filtered_students
                    if search in s["student_id"].lower()
                    or search in s["name"].lower()
                ]

            rows = []

            for student in filtered_students:

                stats = get_student_stats(
                    student["student_id"]
                )

                rows.append({
                    "Student ID": student["student_id"],
                    "Name": student["name"],
                    "Department": student["department"],
                    "Section": student["section"],
                    "Year": student["year"],
                    "Attendance": f"{stats['percentage']:.2f}%"
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # EDIT / DELETE
    # --------------------------------------------------------

    with tab3:

        if not st.session_state.students:

            st.info("No students available.")

        else:

            student_ids = [
                s["student_id"]
                for s in st.session_state.students
            ]

            selected_id = st.selectbox(
                "Select Student",
                student_ids
            )

            student = get_student(selected_id)

            if student:

                st.subheader(
                    f"Edit: {student['name']}"
                )

                with st.form("edit_student_form"):

                    new_name = st.text_input(
                        "Name",
                        value=student["name"]
                    )

                    new_department = st.text_input(
                        "Department",
                        value=student["department"]
                    )

                    new_section = st.selectbox(
                        "Section",
                        ["A", "B", "C", "D", "E"],
                        index=(
                            ["A", "B", "C", "D", "E"].index(
                                student["section"]
                            )
                            if student["section"]
                            in ["A", "B", "C", "D", "E"]
                            else 0
                        )
                    )

                    new_year = st.selectbox(
                        "Year",
                        ["1", "2", "3", "4"],
                        index=(
                            ["1", "2", "3", "4"].index(
                                student["year"]
                            )
                            if student["year"]
                            in ["1", "2", "3", "4"]
                            else 0
                        )
                    )

                    new_email = st.text_input(
                        "Email",
                        value=student.get("email", "")
                    )

                    update = st.form_submit_button(
                        "💾 Update Student",
                        use_container_width=True
                    )

                if update:

                    student["name"] = new_name.strip()
                    student["department"] = new_department.strip()
                    student["section"] = new_section
                    student["year"] = new_year
                    student["email"] = new_email.strip()

                    save_students()

                    st.success(
                        "Student updated successfully."
                    )

                    st.rerun()

                st.markdown("---")

                st.subheader("🗑️ Delete Student")

                confirm_delete = st.checkbox(
                    "I understand that deleting this student will also remove their attendance records."
                )

                if st.button(
                    "🗑️ Delete Student",
                    type="secondary",
                    disabled=not confirm_delete
                ):

                    st.session_state.students = [
                        s
                        for s in st.session_state.students
                        if s["student_id"] != selected_id
                    ]

                    new_attendance = []

                    for record in st.session_state.attendance:

                        if selected_id in record.get(
                            "attendance", {}
                        ):

                            del record["attendance"][selected_id]

                        if record.get("attendance"):

                            new_attendance.append(record)

                    st.session_state.attendance = new_attendance

                    save_students()
                    save_attendance()

                    st.success(
                        "Student deleted successfully."
                    )

                    st.rerun()


# ============================================================
# TAKE ATTENDANCE
# ============================================================

elif st.session_state.page == "Take Attendance":

    st.title("📝 Take Attendance")

    if not st.session_state.students:

        st.warning(
            "Add students before taking attendance."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            attendance_date = st.date_input(
                "📅 Attendance Date",
                value=date.today()
            )

        with col2:

            subject = st.text_input(
                "📚 Subject",
                placeholder="Example: Python"
            )

        subject = subject.strip()

        if subject:

            existing_record = None

            date_string = attendance_date.isoformat()

            for record in st.session_state.attendance:

                if (
                    record.get("date") == date_string
                    and record.get("subject", "").lower()
                    == subject.lower()
                ):

                    existing_record = record
                    break

            if existing_record:

                st.warning(
                    "⚠️ Attendance already exists for this date and subject. "
                    "Saving again will update the existing record."
                )

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:

                mark_all_present = st.button(
                    "✅ Mark All Present",
                    use_container_width=True
                )

            with col2:

                mark_all_absent = st.button(
                    "❌ Mark All Absent",
                    use_container_width=True
                )

            with col3:

                clear_attendance = st.button(
                    "🔄 Clear",
                    use_container_width=True
                )

            # Initialize temporary attendance state
            if (
                "temp_attendance" not in st.session_state
                or st.session_state.get(
                    "attendance_date"
                ) != date_string
                or st.session_state.get(
                    "attendance_subject"
                ) != subject
            ):

                st.session_state.temp_attendance = {}

                if existing_record:

                    st.session_state.temp_attendance = (
                        existing_record.get(
                            "attendance", {}
                        ).copy()
                    )

                else:

                    for student in st.session_state.students:

                        st.session_state.temp_attendance[
                            student["student_id"]
                        ] = "Present"

                st.session_state.attendance_date = date_string
                st.session_state.attendance_subject = subject

            if mark_all_present:

                for student in st.session_state.students:

                    st.session_state.temp_attendance[
                        student["student_id"]
                    ] = "Present"

                st.rerun()

            if mark_all_absent:

                for student in st.session_state.students:

                    st.session_state.temp_attendance[
                        student["student_id"]
                    ] = "Absent"

                st.rerun()

            if clear_attendance:

                for student in st.session_state.students:

                    st.session_state.temp_attendance[
                        student["student_id"]
                    ] = "Present"

                st.rerun()

            st.subheader("Mark Student Attendance")

            present_count = 0
            absent_count = 0

            for student in st.session_state.students:

                student_id = student["student_id"]

                current_status = (
                    st.session_state.temp_attendance.get(
                        student_id,
                        "Present"
                    )
                )

                col1, col2, col3 = st.columns(
                    [2, 3, 2]
                )

                with col1:

                    st.write(
                        f"**{student_id}**"
                    )

                with col2:

                    st.write(
                        student["name"]
                    )

                with col3:

                    status = st.selectbox(
                        "Status",
                        ["Present", "Absent"],
                        index=(
                            0
                            if current_status == "Present"
                            else 1
                        ),
                        key=f"attendance_{student_id}",
                        label_visibility="collapsed"
                    )

                    st.session_state.temp_attendance[
                        student_id
                    ] = status

                    if status == "Present":
                        present_count += 1
                    else:
                        absent_count += 1

            st.markdown("---")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "👨‍🎓 Total",
                len(st.session_state.students)
            )

            c2.metric(
                "✅ Present",
                present_count
            )

            c3.metric(
                "❌ Absent",
                absent_count
            )

            if st.button(
                "💾 Save Attendance",
                type="primary",
                use_container_width=True
            ):

                new_record = {
                    "date": date_string,
                    "subject": subject,
                    "created_at": datetime.now().isoformat(
                        timespec="seconds"
                    ),
                    "attendance":
                        st.session_state.temp_attendance.copy()
                }

                if existing_record:

                    index = st.session_state.attendance.index(
                        existing_record
                    )

                    st.session_state.attendance[index] = (
                        new_record
                    )

                else:

                    st.session_state.attendance.append(
                        new_record
                    )

                save_attendance()

                st.success(
                    f"Attendance saved for {subject} "
                    f"on {attendance_date.strftime('%d-%m-%Y')}."
                )

                st.rerun()

        else:

            st.info(
                "Enter a subject to start taking attendance."
            )


# ============================================================
# REPORTS
# ============================================================

elif st.session_state.page == "Reports":

    st.title("📈 Attendance Reports")

    if not st.session_state.students:

        st.info("No students available.")

    else:

        tab1, tab2 = st.tabs(
            [
                "👨‍🎓 Student Report",
                "📚 Subject Report"
            ]
        )

        # ----------------------------------------------------
        # STUDENT REPORT
        # ----------------------------------------------------

        with tab1:

            student_ids = [
                s["student_id"]
                for s in st.session_state.students
            ]

            selected_student_id = st.selectbox(
                "Select Student",
                student_ids
            )

            student = get_student(
                selected_student_id
            )

            stats = get_student_stats(
                selected_student_id
            )

            if student:

                st.subheader(
                    f"{student['name']} ({student['student_id']})"
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Total Classes",
                    stats["total"]
                )

                c2.metric(
                    "Present",
                    stats["present"]
                )

                c3.metric(
                    "Absent",
                    stats["absent"]
                )

                c4.metric(
                    "Attendance",
                    f"{stats['percentage']:.2f}%"
                )

                if stats["percentage"] < 75:

                    required = calculate_required_classes(
                        stats["present"],
                        stats["total"]
                    )

                    st.error(
                        f"⚠️ Attendance is below 75%. "
                        f"The student needs to attend approximately "
                        f"{required} consecutive future classes "
                        f"to reach 75%, assuming no further absences."
                    )

                else:

                    st.success(
                        "✅ Attendance is currently 75% or above."
                    )

                # Subject-wise data
                subject_rows = []

                for subject in get_all_subjects():

                    subject_stats = get_student_stats(
                        selected_student_id,
                        subject
                    )

                    if subject_stats["total"] > 0:

                        subject_rows.append({
                            "Subject": subject,
                            "Total Classes":
                                subject_stats["total"],
                            "Present":
                                subject_stats["present"],
                            "Absent":
                                subject_stats["absent"],
                            "Attendance %":
                                round(
                                    subject_stats["percentage"],
                                    2
                                )
                        })

                if subject_rows:

                    st.subheader(
                        "📚 Subject-wise Attendance"
                    )

                    st.dataframe(
                        pd.DataFrame(subject_rows),
                        use_container_width=True,
                        hide_index=True
                    )

        # ----------------------------------------------------
        # SUBJECT REPORT
        # ----------------------------------------------------

        with tab2:

            subjects = get_all_subjects()

            if not subjects:

                st.info(
                    "No attendance records available."
                )

            else:

                selected_subject = st.selectbox(
                    "Select Subject",
                    subjects
                )

                subject_rows = []

                for student in st.session_state.students:

                    stats = get_student_stats(
                        student["student_id"],
                        selected_subject
                    )

                    subject_rows.append({
                        "Student ID":
                            student["student_id"],
                        "Name":
                            student["name"],
                        "Total Classes":
                            stats["total"],
                        "Present":
                            stats["present"],
                        "Absent":
                            stats["absent"],
                        "Attendance %":
                            round(
                                stats["percentage"],
                                2
                            ),
                        "Status":
                            attendance_status(
                                stats["percentage"]
                            )
                    })

                df = pd.DataFrame(subject_rows)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                if not df.empty:

                    chart_data = df[
                        ["Name", "Attendance %"]
                    ].set_index("Name")

                    st.bar_chart(chart_data)


# ============================================================
# LOW ATTENDANCE
# ============================================================

elif st.session_state.page == "Low Attendance":

    st.title("⚠️ Low Attendance Alerts")

    st.write(
        "Students whose attendance is below 75% are shown here."
    )

    low_students = []

    for student in st.session_state.students:

        stats = get_student_stats(
            student["student_id"]
        )

        if (
            stats["total"] > 0
            and stats["percentage"] < LOW_ATTENDANCE_LIMIT
        ):

            required = calculate_required_classes(
                stats["present"],
                stats["total"]
            )

            low_students.append({
                "Student ID":
                    student["student_id"],
                "Name":
                    student["name"],
                "Department":
                    student["department"],
                "Section":
                    student["section"],
                "Total Classes":
                    stats["total"],
                "Present":
                    stats["present"],
                "Absent":
                    stats["absent"],
                "Attendance %":
                    round(
                        stats["percentage"],
                        2
                    ),
                "Classes Needed":
                    required
            })

    if low_students:

        st.error(
            f"⚠️ {len(low_students)} student(s) "
            f"have attendance below 75%."
        )

        df = pd.DataFrame(low_students)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🔔 Student Alerts")

        for student in low_students:

            st.warning(
                f"**{student['Name']} ({student['Student ID']})** "
                f"has {student['Attendance %']:.2f}% attendance. "
                f"They need approximately "
                f"**{student['Classes Needed']} consecutive classes** "
                f"with attendance to reach 75%."
            )

    else:

        st.success(
            "🎉 No students currently have attendance below 75%."
        )


# ============================================================
# SETTINGS
# ============================================================

elif st.session_state.page == "Settings":

    st.title("⚙️ Settings")

    st.subheader("📁 Storage Information")

    st.write(
        f"Students file: `{STUDENTS_FILE}`"
    )

    st.write(
        f"Attendance file: `{ATTENDANCE_FILE}`"
    )

    st.markdown("---")

    st.subheader("📊 Current Data")

    c1, c2 = st.columns(2)

    c1.metric(
        "Students",
        len(st.session_state.students)
    )

    c2.metric(
        "Attendance Records",
        len(st.session_state.attendance)
    )

    st.markdown("---")

    # --------------------------------------------------------
    # EXPORT STUDENTS
    # --------------------------------------------------------

    st.subheader("📥 Export Data")

    students_json = json.dumps(
        st.session_state.students,
        indent=4
    )

    attendance_json = json.dumps(
        st.session_state.attendance,
        indent=4
    )

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            "📥 Download Students JSON",
            data=students_json,
            file_name="students_backup.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:

        st.download_button(
            "📥 Download Attendance JSON",
            data=attendance_json,
            file_name="attendance_backup.json",
            mime="application/json",
            use_container_width=True
        )

    # --------------------------------------------------------
    # CSV EXPORT
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("📊 Export Attendance CSV")

    df = attendance_dataframe()

    if not df.empty:

        csv_data = df.to_csv(index=False)

        st.download_button(
            "📥 Download Attendance CSV",
            data=csv_data,
            file_name="attendance_report.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info(
            "No attendance data available for CSV export."
        )

    # --------------------------------------------------------
    # DANGER ZONE
    # --------------------------------------------------------

    st.markdown("---")

    st.subheader("🗑️ Data Management")

    confirm_reset = st.checkbox(
        "I understand that resetting data will permanently remove all students and attendance records."
    )

    if st.button(
        "🗑️ Reset All Data",
        disabled=not confirm_reset
    ):

        st.session_state.students = []
        st.session_state.attendance = []

        save_students()
        save_attendance()

        st.success(
            "All data has been reset."
        )

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🎓 Student Attendance Tracker • "
    "Built with Streamlit • Local JSON Storage"
)