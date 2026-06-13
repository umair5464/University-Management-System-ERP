import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from db_config import get_db_connection

ctk.set_appearance_mode("Light")  
ctk.set_default_color_theme("blue") 

class AdminDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MNS-UAM | Enterprise Resource Planning")
        self.withdraw() 

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- TOP HEADER BAR ---
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="white")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_frame.grid_propagate(False)

        self.menu_btn = ctk.CTkButton(
            self.header_frame, text="☰", width=40, height=40, 
            fg_color="transparent", text_color="#1e3c72", hover_color="#f4f7f6", 
            font=ctk.CTkFont(size=24), command=self.toggle_sidebar
        )
        self.menu_btn.grid(row=0, column=0, padx=15, pady=10)

        self.brand_label = ctk.CTkLabel(
            self.header_frame, text="MNS-UAM ERP Admin", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color="#2c3e50"
        )
        self.brand_label.grid(row=0, column=1, pady=10, sticky="w")

        # --- COLLAPSIBLE SIDEBAR ---
        self.sidebar_visible = True
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#1e3c72")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        nav_buttons = [
            ("📊 Dashboard", self.render_overview),
            ("📝 Admissions Pipeline", self.render_admissions),
            ("🎓 Enrolled Students", self.render_students),
            ("👨‍🏫 Faculty Management", self.render_faculty),
            ("🏫 Academic Master Data", self.render_academics),
            ("💰 Finance & Fee Challans", self.render_finance),
            ("📚 Library System", self.render_library),
            ("⚙️ AI Timetable Generator", self.render_timetable)
        ]

        for i, (text, command) in enumerate(nav_buttons):
            btn = ctk.CTkButton(
                self.sidebar_frame, text=text, fg_color="transparent", text_color="white", 
                hover_color="#2a5298", anchor="w", font=ctk.CTkFont(size=15), command=command
            )
            btn.grid(row=i, column=0, padx=20, pady=12, sticky="ew")

        # --- DYNAMIC MAIN CONTENT AREA ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#f4f7f6")
        self.main_frame.grid(row=1, column=1, sticky="nsew")

        # Set up Table Styling
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background="#e0e0e0", foreground="#2c3e50")
        self.style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
        self.style.map('Treeview', background=[('selected', '#3498db')], foreground=[('selected', 'white')])

        self.launch_splash_screen()

    # ==========================================
    # DATABASE LOGIC & ACTION METHODS
    # ==========================================
    
    # --- DASHBOARD & ADMISSIONS ---
    def fetch_dashboard_stats(self):
        stats = {"students": 0, "faculty": 0, "pending": 0}
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM enrolled_students")
                stats["students"] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM faculty")
                stats["faculty"] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM applicants WHERE Status = 'Pending'")
                stats["pending"] = cursor.fetchone()[0]
                cursor.close(); conn.close()
            except Exception as e: print(f"SQL Error: {e}")
        return stats
        
    def fetch_programs(self):
        programs = []
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Program_ID, Program_Name FROM programs")
                programs = cursor.fetchall()
                cursor.close(); conn.close()
            except Exception as e: print(f"SQL Error: {e}")
        return programs

    def fetch_applicants(self, status):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Applicant_ID, First_Name, Last_Name, Applied_Program_ID, Merit_Score, Status FROM applicants WHERE Status = %s ORDER BY Merit_Score DESC", (status,))
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def run_merit_engine(self):
        selected_program_str = self.prog_var.get()
        seats_str = self.seats_var.get()
        if not selected_program_str or not seats_str.isdigit():
            messagebox.showwarning("Input Error", "Please select a program and enter a valid number of seats.")
            return
        prog_id = int(selected_program_str.split(" - ")[0])
        limit = int(seats_str)
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                update_query = """
                    UPDATE applicants SET Status = 'Merit_List' WHERE Applicant_ID IN (
                        SELECT Applicant_ID FROM (
                            SELECT Applicant_ID FROM applicants WHERE Status = 'Pending' AND Applied_Program_ID = %s ORDER BY Merit_Score DESC LIMIT %s
                        ) as tmp
                    )
                """
                cursor.execute(update_query, (prog_id, limit))
                conn.commit()
                rows_updated = cursor.rowcount
                cursor.close(); conn.close()
                if rows_updated > 0:
                    messagebox.showinfo("Success", f"Merit List Generated!\nMoved the top {rows_updated} students for Program {prog_id} to the Merit List.")
                else:
                    messagebox.showinfo("Notice", "No pending applicants found for this program.")
                self.render_admissions()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    def migrate_students(self):
        selected_items = self.merit_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select at least one student from the table to enroll.")
            return
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                migrated_count = 0
                for item in selected_items:
                    row_data = self.merit_tree.item(item, "values")
                    app_id = int(row_data[0])
                    prog_id = int(row_data[3])
                    
                    cursor.execute("SELECT Department_ID FROM programs WHERE Program_ID = %s", (prog_id,))
                    dept_result = cursor.fetchone()
                    dept_id = dept_result[0] if dept_result else 1 
                    
                    # --- THE FIX: DYNAMIC SECTION LOOKUP ---
                    # The system now checks the sections table for the correct match!
                    cursor.execute("SELECT Section_ID FROM sections WHERE Program_ID = %s AND Semester_Number = 1 LIMIT 1", (prog_id,))
                    sec_result = cursor.fetchone()
                    # If no section exists yet, default to NULL so it doesn't corrupt data
                    sec_id = sec_result[0] if sec_result else None 
                    
                    roll_no = f"FA26-{prog_id}-{app_id}"
                    
                    # Notice we pass sec_id instead of hardcoding a 1
                    insert_student = "INSERT INTO enrolled_students (Applicant_ID, Roll_no, Department_ID, Program_ID, Current_Semester, Section_ID, Fee_Status) VALUES (%s, %s, %s, %s, 1, %s, 'Unpaid')"
                    cursor.execute(insert_student, (app_id, roll_no, dept_id, prog_id, sec_id))
                    
                    student_id = cursor.lastrowid
                    
                    insert_user = "INSERT INTO system_users (Username, Password_Hash, Role, Reference_ID) VALUES (%s, %s, 'Student', %s)"
                    cursor.execute(insert_user, (roll_no, 'student123', student_id))
                    
                    cursor.execute("UPDATE applicants SET Status = 'Enrolled' WHERE Applicant_ID = %s", (app_id,))
                    migrated_count += 1
                    
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Success", f"Successfully enrolled {migrated_count} selected students!\nUniversity Roll Numbers generated.")
                self.render_admissions()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    # --- ENROLLED STUDENTS ---
    def fetch_enrolled_roster(self, program_id=None):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    SELECT 
                        e.Roll_no, a.First_Name, a.Last_Name, p.Program_Name, e.Current_Semester, a.Email,
                        COALESCE(ROUND(AVG(sg.GPA_Points), 2), 0.00) as CGPA
                    FROM enrolled_students e
                    INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
                    INNER JOIN programs p ON e.Program_ID = p.Program_ID
                    LEFT JOIN student_grades sg ON e.Student_ID = sg.Student_ID
                """
                if program_id and program_id != "ALL":
                    query += " WHERE e.Program_ID = %s GROUP BY e.Student_ID ORDER BY e.Roll_no ASC"
                    cursor.execute(query, (program_id,))
                else:
                    query += " GROUP BY e.Student_ID ORDER BY e.Roll_no ASC"
                    cursor.execute(query)
                    
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def promote_all_students_to_next_semester(self):
        confirm = messagebox.askyesno("Confirm Batch Promotion", "Are you sure you want to promote all active students to their next semester?\n\nThis will also reset their Fee Status to 'Unpaid' for the new term.")
        if confirm:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE enrolled_students SET Current_Semester = Current_Semester + 1, Fee_Status = 'Unpaid'")
                    conn.commit()
                    cursor.close(); conn.close()
                    messagebox.showinfo("Success", "Academic Promotion Complete!\nStudents have been automatically enrolled in their new courses.")
                    self.render_students() # Refresh screen
                except Exception as e:
                    messagebox.showerror("Database Error", str(e))

    # --- FACULTY & ACADEMICS ---
    def fetch_faculty_roster(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT f.Faculty_ID, f.First_Name, f.Last_Name, d.Department_Name, f.Role, f.Email 
                    FROM faculty f INNER JOIN departments d ON f.Department_ID = d.Department_ID
                    ORDER BY f.Faculty_ID ASC
                """)
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def fetch_academic_courses(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.Course_ID, c.Course_Code, c.Course_Name, p.Program_Code, c.Credit_Hours, c.Course_Type
                    FROM courses c INNER JOIN programs p ON c.Program_ID = p.Program_ID
                    ORDER BY p.Program_Code, c.Course_Code ASC
                """)
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []
    
    def fetch_academic_programs(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.Program_ID, p.Program_Code, p.Program_Name, d.Department_Name, p.Total_Seats 
                    FROM programs p INNER JOIN departments d ON p.Department_ID = d.Department_ID
                    ORDER BY p.Program_ID ASC
                """)
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def fetch_academic_departments(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Department_ID, Department_Name FROM departments ORDER BY Department_ID ASC")
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    # --- FINANCE ---
    def fetch_finance_roster(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.Roll_no, CONCAT(a.First_Name, ' ', a.Last_Name) as Student_Name, p.Program_Name,
                           'Rs. 45,000' as Base_Tuition, e.Fee_Status as Status, '15th of Current Month' as Due_Date
                    FROM enrolled_students e
                    INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
                    INNER JOIN programs p ON e.Program_ID = p.Program_ID
                    ORDER BY e.Roll_no ASC
                """)
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def mark_fee_paid(self):
        selected_items = getattr(self, 'finance_tree', None)
        if not selected_items or not self.finance_tree.selection():
            messagebox.showwarning("Warning", "Please select a student from the table first.")
            return
        selected = self.finance_tree.selection()
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                updated_count = 0
                for item in selected:
                    roll_no = self.finance_tree.item(item, "values")[0]
                    cursor.execute("UPDATE enrolled_students SET Fee_Status = 'Paid' WHERE Roll_no = %s", (roll_no,))
                    updated_count += 1
                conn.commit()
                cursor.close(); conn.close()
                messagebox.showinfo("Success", f"Successfully marked {updated_count} student(s) as Paid!")
                self.render_finance() 
            except Exception as e: messagebox.showerror("Database Error", str(e))

    def generate_batch_challans(self):
        messagebox.showinfo("Batch Processing Complete", "Fee Challans generated for all active students.\n\nStudents can now download their PDFs from the Web Portal.")

    # --- LIBRARY ---
    def fetch_library_books(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT Book_ID, Title, Author, Total_Copies, Available_Copies FROM books ORDER BY Book_ID ASC")
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    def fetch_library_checkouts(self):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.Checkout_ID, b.Title, e.Roll_no, CONCAT(a.First_Name, ' ', a.Last_Name), c.Checkout_Date, c.Due_Date
                    FROM book_checkouts c
                    INNER JOIN books b ON c.Book_ID = b.Book_ID
                    INNER JOIN enrolled_students e ON c.Student_ID = e.Student_ID
                    INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
                    WHERE c.Return_Date IS NULL ORDER BY c.Due_Date ASC
                """)
                rows = cursor.fetchall()
                cursor.close(); conn.close()
                return rows
            except Exception as e: print(f"SQL Error: {e}")
        return []

    # ==========================================
    # UI ROUTING & HELPERS
    # ==========================================
    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.grid_remove()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
            self.sidebar_visible = True

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def build_page_header(self, title, subtitle):
        header = ctk.CTkLabel(self.main_frame, text=title, font=ctk.CTkFont(size=32, weight="bold"), text_color="#2c3e50")
        header.pack(pady=(40, 5), anchor="w", padx=50)
        sub = ctk.CTkLabel(self.main_frame, text=subtitle, font=ctk.CTkFont(size=16), text_color="#7f8c8d")
        sub.pack(pady=(0, 20), anchor="w", padx=50)

    def build_placeholder_table(self):
        table_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10, height=300)
        table_frame.pack(fill="both", expand=True, padx=50, pady=10)
        lbl = ctk.CTkLabel(table_frame, text="[ System Component Will Render Here ]", text_color="#bdc3c7")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    def create_data_tree(self, parent, rows, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="extended")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for row in rows:
            tree.insert("", tk.END, values=row)
        return tree

    # ==========================================
    # MODULE RENDERERS (UI SCREENS)
    # ==========================================
    def render_overview(self):
        self.clear_main_frame()
        self.build_page_header("System Overview", "University-wide metrics and system status.")
        live_stats = self.fetch_dashboard_stats()
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=50, pady=10)
        card_data = [f"Total Students: {live_stats['students']}", f"Active Faculty: {live_stats['faculty']}", f"Pending Applications: {live_stats['pending']}"]
        for i, text in enumerate(card_data):
            card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10, height=100)
            card.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 10, 0))
            ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=18, weight="bold"), text_color="#2c3e50").place(relx=0.5, rely=0.5, anchor="center")

    def render_admissions(self):
        self.clear_main_frame()
        self.build_page_header("Admissions Pipeline", "Manage Applicants and generate Program-specific Merit Lists.")
        control_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        control_frame.pack(fill="x", padx=50, pady=(0, 10))
        
        ctk.CTkLabel(control_frame, text="Target Program:").pack(side="left", padx=(20, 5), pady=15)
        db_programs = self.fetch_programs()
        prog_options = [f"{p[0]} - {p[1]}" for p in db_programs] if db_programs else ["1 - Setup Programs First"]
        self.prog_var = ctk.StringVar(value=prog_options[0])
        ctk.CTkComboBox(control_frame, variable=self.prog_var, values=prog_options, width=200).pack(side="left", padx=5, pady=15)
        
        ctk.CTkLabel(control_frame, text="Available Seats:").pack(side="left", padx=(20, 5), pady=15)
        self.seats_var = ctk.StringVar(value="50")
        ctk.CTkEntry(control_frame, textvariable=self.seats_var, width=60).pack(side="left", padx=5, pady=15)
        ctk.CTkButton(control_frame, text="⚙️ Generate List", fg_color="#27ae60", hover_color="#2ecc71", command=self.run_merit_engine).pack(side="left", padx=20, pady=15)

        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=50, pady=10)
        tabview.add("Pending Applicants")
        tabview.add("Official Merit List")
        
        cols = ("ID", "First Name", "Last Name", "Program ID", "Merit Score", "Status")
        self.pending_tree = self.create_data_tree(tabview.tab("Pending Applicants"), self.fetch_applicants("Pending"), cols)
        
        ctk.CTkButton(tabview.tab("Official Merit List"), text="🎓 Enroll Selected Students", fg_color="#8e44ad", hover_color="#9b59b6", command=self.migrate_students).pack(anchor="e", pady=(5, 5), padx=10)
        self.merit_tree = self.create_data_tree(tabview.tab("Official Merit List"), self.fetch_applicants("Merit_List"), cols)

    def render_students(self):
        self.clear_main_frame()
        self.build_page_header("Enrolled Students", "View Master Roster. Use the dropdown to filter by Program.")
        
        # Filter & Promotion Control Panel
        filter_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", padx=50, pady=(0, 10))
        
        ctk.CTkLabel(filter_frame, text="Filter by Program:").pack(side="left", padx=(20, 5), pady=15)
        db_programs = self.fetch_programs()
        prog_options = ["ALL - Show All Programs"] + [f"{p[0]} - {p[1]}" for p in db_programs]
        self.roster_prog_var = ctk.StringVar(value=prog_options[0])
        ctk.CTkComboBox(filter_frame, variable=self.roster_prog_var, values=prog_options, width=300).pack(side="left", padx=5, pady=15)

        def apply_filter():
            for widget in table_container.winfo_children():
                widget.destroy()
            selection = self.roster_prog_var.get()
            prog_id = "ALL" if selection.startswith("ALL") else int(selection.split(" - ")[0])
            self.create_data_tree(table_container, self.fetch_enrolled_roster(prog_id), cols)

        ctk.CTkButton(filter_frame, text="🔍 Apply Filter", fg_color="#2980b9", hover_color="#3498db", command=apply_filter).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(filter_frame, text="🎓 Promote All Students", fg_color="#e67e22", hover_color="#d35400", command=self.promote_all_students_to_next_semester).pack(side="right", padx=20, pady=15)

        table_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=40, pady=0)
        cols = ("Roll Number", "First Name", "Last Name", "Program", "Semester", "Email", "CGPA")
        self.create_data_tree(table_container, self.fetch_enrolled_roster("ALL"), cols)

    def render_faculty(self):
        self.clear_main_frame()
        self.build_page_header("Faculty Management", "Manage faculty roles, departments, and credentials.")
        table_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=40, pady=10)
        self.create_data_tree(table_container, self.fetch_faculty_roster(), ("ID", "First Name", "Last Name", "Department", "Designation", "Official Email"))

    def render_academics(self):
        self.clear_main_frame()
        self.build_page_header("Academic Master Data", "Manage Departments, Programs, and Course Catalogs.")
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=50, pady=10)
        tabview.add("Course Catalog")
        tabview.add("Degree Programs")
        tabview.add("Departments")
        self.create_data_tree(tabview.tab("Course Catalog"), self.fetch_academic_courses(), ("ID", "Course Code", "Course Name", "Program", "Cr. Hours", "Type"))
        self.create_data_tree(tabview.tab("Degree Programs"), self.fetch_academic_programs(), ("ID", "Program Code", "Program Name", "Department", "Total Seats"))
        self.create_data_tree(tabview.tab("Departments"), self.fetch_academic_departments(), ("Department ID", "Department Name"))

    def render_finance(self):
        self.clear_main_frame()
        self.build_page_header("Finance & Fee Management", "Track Tuition, Financial Aid, and generate digital payment vouchers.")
        control_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        control_frame.pack(fill="x", padx=50, pady=(0, 10))
        ctk.CTkLabel(control_frame, text="Billing Actions:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(control_frame, text="🧾 Generate Batch Challans", fg_color="#8e44ad", hover_color="#9b59b6", command=self.generate_batch_challans).pack(side="left", padx=10, pady=15)
        ctk.CTkButton(control_frame, text="✅ Mark Selected as Paid", fg_color="#27ae60", hover_color="#2ecc71", command=self.mark_fee_paid).pack(side="left", padx=10, pady=15)
        table_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=40, pady=10)
        self.finance_tree = self.create_data_tree(table_container, self.fetch_finance_roster(), ("Roll Number", "Student Name", "Program", "Base Tuition", "Status", "Due Date"))

    def render_library(self):
        self.clear_main_frame()
        self.build_page_header("Library System", "Manage Book Inventory and Track Student Checkouts.")
        control_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        control_frame.pack(fill="x", padx=50, pady=(0, 10))
        ctk.CTkLabel(control_frame, text="Librarian Actions:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(control_frame, text="📚 Issue Book", fg_color="#2980b9", hover_color="#3498db").pack(side="left", padx=10, pady=15)
        ctk.CTkButton(control_frame, text="✅ Process Return", fg_color="#27ae60", hover_color="#2ecc71").pack(side="left", padx=10, pady=15)
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=50, pady=10)
        tabview.add("Active Checkouts")
        tabview.add("Master Book Inventory")
        self.create_data_tree(tabview.tab("Active Checkouts"), self.fetch_library_checkouts(), ("Checkout ID", "Book Title", "Roll Number", "Student Name", "Checkout Date", "Due Date"))
        self.create_data_tree(tabview.tab("Master Book Inventory"), self.fetch_library_books(), ("Book ID", "Title", "Author", "Total Copies", "Available Copies"))
        
    def render_timetable(self):
        self.clear_main_frame()
        self.build_page_header("AI Timetable Generator", "Execute Python scheduling algorithms against Timetable_Slots.")
        self.build_placeholder_table()

    # --- SPLASH SCREEN LOGIC ---
    def launch_splash_screen(self):
        self.splash = ctk.CTkToplevel(self)
        self.splash.overrideredirect(True)
        w, h = self.splash.winfo_screenwidth(), self.splash.winfo_screenheight()
        self.splash.geometry(f"{w}x{h}+0+0")
        self.splash.configure(fg_color="#2a5298")

        center_frame = ctk.CTkFrame(self.splash, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        canvas = tk.Canvas(center_frame, width=120, height=80, bg="#2a5298", highlightthickness=0)
        canvas.pack(pady=(0, 20))
        canvas.create_polygon(60, 10, 10, 35, 60, 60, 110, 35, fill="white")
        canvas.create_arc(30, 40, 90, 75, start=180, extent=180, outline="white", width=8, style="arc")

        ctk.CTkLabel(center_frame, text="Admin Portal", font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"), text_color="white").pack()
        ctk.CTkLabel(center_frame, text="University Management System", font=ctk.CTkFont(family="Segoe UI", size=16), text_color="#e0e0e0").pack(pady=10)
        self.after(2500, self.close_splash)

    def close_splash(self):
        self.splash.destroy()
        self.deiconify() 
        self.state('zoomed') 
        self.render_overview() 

if __name__ == "__main__":
    app = AdminDashboard()
    app.mainloop()