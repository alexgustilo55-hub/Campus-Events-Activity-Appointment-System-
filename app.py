from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql, os, calendar, datetime

app = Flask(__name__)
app.secret_key = "12345"
app.config['UPLOAD_FOLDER'] = "static/img_profile/"
app.config['EVENT_UPLOADS'] = "static/img_events/"


def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",       
        password="Flaskframework",       
        database="ecela",
        cursorclass=pymysql.cursors.DictCursor
    )
#------------------- Main Page ------------------#


@app.route('/')
def main():
    return render_template("login.html")

# --------------------------- User Register Process -----------------------#

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        gender = request.form.get('gender')
        fullname = request.form.get('fullname')
        phone = request.form.get('phone')
        birthday = request.form.get('birthday')
        email = request.form.get('email')
        address = request.form.get('address')
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_email = cursor.fetchone()

        cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
        existing_phone = cursor.fetchone()

        if existing_user:
            flash("Username already taken!", "danger")
        elif existing_email:
            flash("Email already registered!", "danger")
        elif existing_phone:
            flash("Phone number already registered!", "danger")
        else:
            cursor.execute("""
                INSERT INTO users 
                (email, username, password, phone, full_name, gender, role, address, birthday) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (email, username, password, phone, fullname, gender, role, address, birthday))
            
            conn.commit()
            flash("Registration successful!", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('login'))

        cursor.close()
        conn.close()
        return render_template("register.html")

    
    return render_template("register.html")


#------------------------------- User Login Process -------------------------------------#

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s", (username, password,role))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['role'] = user['role']
            session['username'] = user['username']
            flash("Login successful!", "success")

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('home'))
            elif user['role'] == 'faculty':
                return redirect(url_for('home'))
            elif user['role'] == 'organizer':
                if user['organizer_type'] == 'faculty':
                    return redirect(url_for('organizer_dashboard'))
            else:
                return redirect(url_for('login'))          
        else:
            flash("Invalid username or password", "error")
    return render_template("login.html")




#------------------------------------- Home About Us -----------------------------------#
@app.route('/about_us_notlogged')
def about_us_notlogged():
    return render_template("about_us_notlogged.html")

#------------------------------------- Admin Dashboard -----------------------------------#


@app.route('/admin_dashboard')
def admin_dashboard():
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # Get current admin/user details
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()

            # Get all events
            cursor.execute("SELECT * FROM events")
            events = cursor.fetchall()

            # Count total events
            cursor.execute("SELECT COUNT(*) AS total_events FROM events")
            total_events = cursor.fetchone()["total_events"]

            # Count total users who registered for events
            cursor.execute("SELECT COUNT(*) AS total_users FROM user_registers")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) AS pending_request FROM appointments Where status = 'Pending'")
            pending_request = cursor.fetchone()["pending_request"]

            # Get recent activities (latest events)
            cursor.execute("""
                SELECT event_name, event_type, event_date
                FROM events
                ORDER BY event_date DESC
                LIMIT 10
            """)
            recent_activities = cursor.fetchall()

        conn.close()

        # Render admin dashboard with all stats
        return render_template(
            "admin_dash.html",
            user=user,
            events=events,
            total_events=total_events,
            total_users=total_users,
            pending_request=pending_request,  
            recent_activities=recent_activities
        )
    else:
        return redirect(url_for("login"))


    
#------------------------------------- Admin Information -----------------------------------#

@app.route('/admin_info')
def admin_info():
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()
        conn.close()
        return render_template("admin_information.html", user=user)
    else:
        return redirect(url_for("login"))
    
#------------------------------------- Admin Update Profile-----------------------------------#
@app.route("/admin_profile_update", methods=["GET", "POST"])
def admin_profile_update():
    if "username" not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username = %s", (session["username"],))
    user = cursor.fetchone()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update":
            full_name = request.form.get("full_name")
            phone = request.form.get("phone")
            username = request.form.get("username")
            birthday = request.form.get("birthday")
            email = request.form.get("email")
            gender = request.form.get("gender")
            address = request.form.get("address")

            cursor.execute("""
                UPDATE users
                SET full_name = %s,
                    phone = %s,
                    email = %s,
                    username = %s,
                    birthday = %s,
                    gender = %s,
                    address = %s
                WHERE username = %s
            """, (full_name, phone, email, username, birthday, gender, address, session["username"]))
            conn.commit()

            if username != session["username"]:
                session["username"] = username

            flash("✅ Profile updated successfully!", "success")
            return redirect(url_for("admin_info"))

        conn.close()
        return redirect(url_for('admin_profile_update'))

    conn.close()

    if user:
        for field in ["full_name", "phone", "birthday", "gender", "address", "email"]:
            user[field] = user.get(field) or ""

    return render_template("admin_update_profile.html", user=user)

    
#-------------------------------------- Admin Update Password ------------------------------#

@app.route('/admin_update_password', methods=['GET', 'POST'])
def admin_update_password():
    if "username" not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if request.method == "POST":
        email = request.form.get("email")
        current_password = request.form.get("current_password") 
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        with conn.cursor() as cursor:
            
            cursor.execute("SELECT email, password FROM users WHERE username=%s", (session["username"],))
            result = cursor.fetchone()

            if result is None:
                flash("User not found.", "danger")
                conn.close()
                return redirect(url_for("admin_update_password"))

            db_email = result["email"]        
            db_password = result["password"]  

            if email != db_email:
                flash("Email does not match.", "danger")
                conn.close()
                return redirect(url_for("admin_update_password"))

            if current_password != db_password:
                flash("Incorrect current password.", "danger")
                conn.close()
                return redirect(url_for("admin_update_password"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                conn.close()
                return redirect(url_for("admin_update_password"))

            cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, session["username"]))
            conn.commit()

        conn.close()
        flash("Password updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
        user = cursor.fetchone()
    conn.close()
    return render_template("admin_changepass.html", user=user)



#-------------------------------------- Admin View Events ----------------------------------------#

@app.route('/manage_events')
def manage_events():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()
    print("DEBUG user:", user)   

    cursor.execute("""
    SELECT 
        event_id,
        event_name,
        event_type,
        description,
        location,
        event_date,
        DATE_FORMAT(start_time, '%h:%i %p') AS start_time,
        DATE_FORMAT(end_time, '%h:%i %p') AS end_time,
        event_image
    FROM events
    ORDER BY event_date ASC
""")

    events = cursor.fetchall()
    print("DEBUG events:", events)   

    conn.close()
    return render_template("admin_manage_event.html", user=user, events=events)


#-------------------------------------- Admin Delete Events ----------------------------------------#

@app.route('/delete_event/<int:event_id>', methods=['GET'])
def delete_event(event_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    conn.commit()

    conn.close()
    flash("Event deleted successfully!", "success")
    return redirect(url_for("manage_events"))


#-------------------------------------- Admin Update Events ----------------------------------------#


@app.route('/update_event/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
    event = cursor.fetchone()

    if not event:
        conn.close()
        flash("Event not found!", "danger")
        return redirect(url_for("manage_events"))

    if request.method == 'POST':
        
        name = request.form.get('event_name')
        event_type = request.form.get('event_type')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')

        event_image_filename = event['event_image']  
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename != '':
                filename = file.filename
                upload_path = os.path.join(app.config['EVENT_UPLOADS'], filename)
                file.save(upload_path)
                event_image_filename = filename  

        query = """
            UPDATE events
            SET event_name=%s, event_type=%s, description=%s, 
                event_date=%s, start_time=%s, end_time=%s, 
                location=%s, event_image=%s
            WHERE event_id=%s
        """
        cursor.execute(query, (name, event_type, description, event_date,
                               start_time, end_time, location, event_image_filename, event_id))
        conn.commit()
        conn.close()

        flash("Event updated successfully!", "success")
        return redirect(url_for("manage_events"))

    conn.close()
   
    return render_template("admin_update_event.html", user=user, event=event)



#----------------------------------------- Admin Manage Appointments -----------------------------------------#

@app.route('/admin_appointments')
def admin_appointments():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username = %s", (session["username"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM appointments ORDER BY created_at DESC")
    appointments = cursor.fetchall()
    conn.close()
    return render_template("admin_appointment.html", user=user,appointments=appointments)

#------- Admin approve Appointments -----#
@app.route('/approve_appointment/<int:id>', methods=['POST'])
def approve_appointment(id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    
    cursor.execute("UPDATE appointments SET status = 'Approved' WHERE appointment_id = %s", (id,))

    
    cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s", (id,))
    appointment = cursor.fetchone()

    
    if appointment:
        student_email = appointment.get("student_email")  
        message = f"Your appointment on {appointment['appointment_date']} has been approved!"

        cursor.execute("SELECT username FROM users WHERE email = %s", (student_email,))
        user = cursor.fetchone()

        if user:
            cursor.execute("""
                INSERT INTO notifications (username, message, created_at)
         
                                  VALUES (%s, %s, NOW())
            """, (user["username"], message))
        else:
            print(f"⚠️ No user found with email {student_email}")

    conn.commit()
    conn.close()

    flash("Appointment approved successfully!", "success")
    return redirect(url_for('admin_appointments'))




#------- Admin reject Appointments ---#
@app.route('/reject_appointment/<int:id>', methods=['POST'])
def reject_appointment(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE appointments SET status = 'Rejected' WHERE appointment_id = %s", (id,))
    conn.commit()
    conn.close()
    flash("Appointment rejected.", "error")
    return redirect(url_for('admin_appointments'))


#----------------------------------------- Admin Recent Appointments -----------------------------------------#
@app.route('/admin_recent_appointments')
def admin_recent_appointments():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username = %s", (session["username"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM appointments ORDER BY appointment_date DESC")
    recent_appointments = cursor.fetchall()
    conn.close()

    
    return render_template("admin_recent_app.html", recent_appointments = recent_appointments, user = user)

# ================== Delete Appointment ==================#

@app.route('/delete_appointment/<int:appointment_id>', methods=["POST"])
def delete_appointment(appointment_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))

    cursor.execute("DELETE FROM user_registers WHERE stud_id = %s", (appointment_id,))

    conn.commit()
    conn.close()

    flash("Appointment deleted successfully!", "success")
    return redirect(url_for("admin_recent_appointments"))



#------------------------------------------- Admin Calendar View -----------------------------------------#

@app.route("/admin_calendar")
def admin_calendar_view():
    
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    
    
    today = datetime.date.today()

    # Get query params for month/year
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    # Compute previous and next month/year
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    
    selected_date_str = request.args.get("selected_date")
    if selected_date_str:
        selected_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        selected_date = None

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Get user info
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    # ✅ Get all events for the month
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    cursor.execute("SELECT * FROM events WHERE event_date BETWEEN %s AND %s", (first_day, last_day))
    events = cursor.fetchall()

    # ✅ Get events on selected date
    selected_events = []
    if selected_date:
        cursor.execute("SELECT * FROM events WHERE event_date=%s", (selected_date,))
        selected_events = cursor.fetchall()

    conn.close()

    # ✅ Calendar setup
    current_month_name = calendar.month_name[month]
    first_weekday, num_days = calendar.monthrange(year, month)
    days = []

    for _ in range((first_weekday + 1) % 7):
        days.append(None)
    for d in range(1, num_days + 1):
        days.append(datetime.date(year, month, d))

    return render_template(
        "admin_calendar.html",
        user=user,
        today=today,
        selected_date=selected_date,
        selected_events=selected_events,
        current_year=year,
        current_month=month,
        current_month_name=current_month_name,
        days=days,
        events=events,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )
#-------------------------------------- Admin About Us ----------------------------------------#
@app.route("/admin_about_us")
def admin_about_us():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM notifications WHERE username = %s ORDER BY created_at DESC", (session["username"],))
    notifications = cursor.fetchall()
    unread_count = sum(1 for n in notifications if not n['is_read'])
    conn.close()
    return render_template("admin_about_us.html", user=user, unread_count=unread_count)


#-------------------------------------- Organizer Dashboard Page ----------------------------------------#

@app.route('/organizer_dashboard')
def organizer_dashboard():
   if "username" in session:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            # Get current admin/user details
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()

            # Get all events
            cursor.execute("SELECT * FROM events")
            events = cursor.fetchall()
            
            # Count total events
            cursor.execute("SELECT COUNT(*) AS total_events FROM events")
            total_events = cursor.fetchone()["total_events"]

            cursor.execute("SELECT COUNT(*) AS upcoming_events FROM events WHERE event_date >= CURDATE()")
            upcoming_events = cursor.fetchone()["upcoming_events"]

            cursor.execute("SELECT COUNT(*) AS total_users FROM user_registers")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) AS pending_request FROM appointments Where status = 'Pending'")
            pending_request = cursor.fetchone()["pending_request"]

            cursor.execute("""
                SELECT event_name, event_type, event_date
                FROM events
                ORDER BY event_date DESC
                LIMIT 10
            """)
            recent_activities = cursor.fetchall()

        conn.close()

        
        return render_template(
            "org_dash.html",
            user=user,
            events=events,
            total_events=total_events,
            upcoming_events=upcoming_events,
            total_users=total_users,
            pending_request=pending_request,  
            recent_activities=recent_activities
        )
   else:
        return redirect(url_for("login"))
            
    
#------------------------------------- Organizer Information -----------------------------------#

@app.route('/organizer_info')
def organizer_info():
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()
        conn.close()
        return render_template("org_information.html", user=user)
    else:
        return redirect(url_for("login"))
    

#-------------------------------------- Organizer Update Profile ------------------------------#

@app.route("/org_update_profile", methods =["GET", "POST"])
def org_update_profile():
    if "username" not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username = %s", (session["username"],))
    user = cursor.fetchone()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update":
            full_name = request.form.get("full_name")
            phone = request.form.get("phone")
            username = request.form.get("username")
            birthday = request.form.get("birthday")
            email = request.form.get("email")
            gender = request.form.get("gender")
            address = request.form.get("address")

            cursor.execute("""
                UPDATE users
                SET full_name = %s,
                    phone = %s,
                    email = %s,
                    username = %s,
                    birthday = %s,
                    gender = %s,
                    address = %s
                WHERE username = %s
            """, (full_name, phone, email, username, birthday, gender, address, session["username"]))
            conn.commit()

            if username != session["username"]:
                session["username"] = username
                
                flash("✅ Profile updated successfully!", "success")
            return redirect(url_for('organizer_info'))

        conn.close()
        return redirect(url_for("org_update_profile"))

    conn.close()

    if user:
        for field in ["full_name", "phone", "birthday", "gender", "address", "email"]:
            user[field] = user.get(field) or ""
        return render_template("org_profile_update.html", user=user)


#-------------------------------------- Organizer Update Password ------------------------------#

@app.route('/organizer_update_password', methods=['GET', 'POST'])
def organizer_update_password():
    if "username" not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if request.method == "POST":
        email = request.form.get("email")
        current_password = request.form.get("current_password") 
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        with conn.cursor() as cursor:
            
            cursor.execute("SELECT email, password FROM users WHERE username=%s", (session["username"],))
            result = cursor.fetchone()

            if result is None:
                flash("User not found.", "danger")
                conn.close()
                return redirect(url_for("organizer_update_password"))

            db_email = result["email"]        
            db_password = result["password"]  

            if email != db_email:
                flash("Email does not match.", "danger")
                conn.close()
                return redirect(url_for("organizer_update_password"))

            if current_password != db_password:
                flash("Incorrect current password.", "danger")
                conn.close()
                return redirect(url_for("organizer_update_password"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                conn.close()
                return redirect(url_for("organizer_update_password"))

            cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, session["username"]))
            conn.commit()

        conn.close()
        flash("Password updated successfully!", "success")
        return redirect(url_for("organizer_dashboard"))
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
        user = cursor.fetchone()
    conn.close()
    return render_template("org_changepass.html", user=user)

#-------------------------------------- Organizer Create Events -----------------------------------#

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
        user = cursor.fetchone()
    conn.close()

    if request.method == 'POST':
        name = request.form.get('event_name')
        event_type = request.form.get('event_type')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')

        
        event_image_filename = None
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename != '':
                filename = file.filename
                upload_path = os.path.join(app.config['EVENT_UPLOADS'], filename)
                file.save(upload_path)
                event_image_filename = filename  

        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO events (event_name, event_type, description, event_date, start_time, end_time, location, event_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, event_type, description, event_date, start_time, end_time, location, event_image_filename))
        conn.commit()
        conn.close()

        flash("Successfully created event!", "success")
        return redirect(url_for("organizer_dashboard"))

    return render_template("org_create_event.html", user=user)

#---- Organizer Manage Events ----#

@app.route('/org_manage_events')
def organizer_manage_events():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get organizer info
    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()

    
    cursor.execute("""
    SELECT 
        event_id,
        event_name,
        event_type,
        description,
        location,
        event_date,
        DATE_FORMAT(start_time, '%h:%i %p') AS start_time,
        DATE_FORMAT(end_time, '%h:%i %p') AS end_time,
        event_image
    FROM events
    ORDER BY event_date ASC
""")
    events = cursor.fetchall()

    conn.close()
    return render_template("org_manage_event.html", user=user, events=events)

#----- Organizer Delete Event ----#

@app.route('/org_delete_event/<int:event_id>', methods=['GET'])
def org_delete_event(event_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    conn.commit()
    conn.close()

    flash("Event deleted successfully!", "success")
    return redirect(url_for("organizer_manage_events"))


#-------------------------------------- Organizer Update Event ----------------------------------------#

@app.route('/org_update_event/<int:event_id>', methods=['GET', 'POST'])
def organizer_update_events(event_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    
    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
    event = cursor.fetchone()

    if not event:
        conn.close()
        flash("Event not found!", "danger")
        return redirect(url_for("organizer_manage_events"))

    if request.method == 'POST':
        name = request.form.get('event_name')
        event_type = request.form.get('event_type')
        description = request.form.get('description')
        event_date = request.form.get('event_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        location = request.form.get('location')

        event_image_filename = event['event_image']
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename != '':
                filename = file.filename
                upload_path = os.path.join(app.config['EVENT_UPLOADS'], filename)
                file.save(upload_path)
                event_image_filename = filename

        query = """
            UPDATE events
            SET event_name=%s, event_type=%s, description=%s,
                event_date=%s, start_time=%s, end_time=%s,
                location=%s, event_image=%s
            WHERE event_id=%s
        """
        cursor.execute(query, (name, event_type, description, event_date,
                               start_time, end_time, location, event_image_filename, event_id))
        conn.commit()
        conn.close()

        flash("Event updated successfully!", "success")
        return redirect(url_for("organizer_manage_events"))

    conn.close()
    return render_template("org_update_event.html", user = user, event = event)

#-------------------------------------- Organizer View all Register Students ----------------------------------------#

@app.route('/view_registered_students')
def view_registered_students():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()

    
    cursor.execute("SELECT * FROM user_registers ORDER BY stud_app_time DESC")
    students = cursor.fetchall()

    conn.close()

   
    return render_template("org_registered_stud.html", user=user, students=students)

#--------------------------------------- Organizer Calendar View --------------------------------------------#
@app.route("/org_calendar")
def org_calendar_view():
    
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    
    #  Get today
    today = datetime.date.today()

    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    
    selected_date_str = request.args.get("selected_date")
    if selected_date_str:
        selected_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        selected_date = None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    cursor.execute("SELECT * FROM events WHERE event_date BETWEEN %s AND %s", (first_day, last_day))
    events = cursor.fetchall()

    
    selected_events = []
    if selected_date:
        cursor.execute("SELECT * FROM events WHERE event_date=%s", (selected_date,))
        selected_events = cursor.fetchall()

    conn.close()

    current_month_name = calendar.month_name[month]
    first_weekday, num_days = calendar.monthrange(year, month)
    days = []

    for _ in range((first_weekday + 1) % 7):
        days.append(None)
    for d in range(1, num_days + 1):
        days.append(datetime.date(year, month, d))

    return render_template(
        "org_calendar.html",
        user=user,
        today=today,
        selected_date=selected_date,
        selected_events=selected_events,
        current_year=year,
        current_month=month,
        current_month_name=current_month_name,
        days=days,
        events=events,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )


#-------------------------------------- Organizer About Us--------------------------------------------#


@app.route("/org_about_us")
def org_about_us():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM notifications WHERE username = %s ORDER BY created_at DESC", (session["username"],))
    notifications = cursor.fetchall()
    unread_count = sum(1 for n in notifications if not n['is_read'])
    conn.close()
    return render_template("org_about_us.html", user=user, unread_count=unread_count)

#--------------------------------------- User Home Page --------------------------------------------#

@app.route('/home')
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()
    print("DEBUG user:", user)   

    cursor.execute("""
    SELECT 
        event_id,
        event_name,
        event_type,
        description,
        location,
        event_date,
        DATE_FORMAT(start_time, '%h:%i %p') AS start_time,
        DATE_FORMAT(end_time, '%h:%i %p') AS end_time,
        event_image
    FROM events
    ORDER BY event_date ASC
""")
    events = cursor.fetchall()
    print("DEBUG events:", events)

    cursor.execute("SELECT * FROM notifications WHERE username = %s ORDER BY created_at DESC", (session["username"],))
    notifications = cursor.fetchall()

    unread_count = sum(1 for n in notifications if not n['is_read'])   

    conn.close()
    return render_template("user_home.html", user=user, events=events, notifications = notifications, unread_count=unread_count)

#--------------------------------------- Notification Mark All Read ---------------------------------------------#

@app.route('/mark_all_read', methods=['POST'])
def mark_all_read():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE username = %s", (session["username"],))
    conn.commit()
    conn.close()
    
    flash("all notification marked as read", "success")
    return redirect(url_for("home"))

#------- Notification Mark All Read -------#

@app.route("/delete_all_notifications", methods=["POST"])
def delete_all_notifications():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notifications WHERE username = %s", (session["username"],))

    conn.commit()
    conn.close()

    flash("All notifications deleted successfully!", "success")
    return redirect(url_for("home"))

    
#--------------------------------------- User Event Page ---------------------------------------------#

@app.route('/u_event')
def u_event():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    
    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()
    print("DEBUG user:", user)   

    
    cursor.execute("""
    SELECT 
        event_id,
        event_name,
        event_type,
        description,
        location,
        event_date,
        DATE_FORMAT(start_time, '%h:%i %p') AS start_time,
        DATE_FORMAT(end_time, '%h:%i %p') AS end_time,
        event_image
    FROM events
    ORDER BY event_date ASC
""")
    events = cursor.fetchall()
    print("DEBUG events:", events)   

    cursor.execute("SELECT * FROM notifications WHERE username = %s ORDER BY created_at DESC", (session["username"],))
    notifications = cursor.fetchall()

    unread_count = sum(1 for n in notifications if not n['is_read'])

    conn.close()
    return render_template("user_event.html", user=user, events=events, unread_count=unread_count)


#--------------------------------------- User View Event Details ---------------------------------------------#

@app.route('/view_details/<int:event_id>')
def view_details(event_id):
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor() as cursor:
           
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()  

            
            cursor.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
            event = cursor.fetchone()
        conn.close()

        if event:
            return render_template("user_eventdetails.html", user=user, event=event)
        else:
            return "Event not found", 404
    else:
        return redirect(url_for("login"))
    
#----------------------------------------- User Register to events -----------------------------------------#

@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
    user = cursor.fetchone()

    if request.method == "POST":
        
        name = user['full_name']
        email = user['email']
        number = user.get('phone', '')  

        course = request.form['s_course']
        year = request.form['s_year']
        appointment_date = request.form['s_date']
        appointment_time = request.form['s_time']
        comments = request.form.get('comments', '')

        appointment_datetime = f"{appointment_date} {appointment_time}"

        cursor.execute("""
            INSERT INTO appointments 
            (student_name, student_number, student_email, student_course, student_year_level, appointment_date, comments, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, number, email, course, year, appointment_datetime, comments, 'Pending'))

        cursor.execute("""
            INSERT INTO user_registers
            (stud_name, stud_no, stud_email, stud_course, stud_year_level, stud_app_time, stud_comments)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, number, email, course, year, appointment_datetime, comments))

        conn.commit()
        flash("Appointment submitted successfully! Please wait for admin approval.", "success")

    conn.close()
    return render_template("user_registers.html", user=user)




#--------------------------------------- User Information --------------------------------------------#

@app.route('/user_info')
def user_info():
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()
        conn.close()
        return render_template("user_information.html", user=user)
    else:
        return redirect(url_for("login"))
    
    
#--------------------------------------- User update password --------------------------------------------#

@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if "username" not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if request.method == "POST":
        email = request.form.get("email")
        current_password = request.form.get("current_password") 
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        with conn.cursor() as cursor:
            
            cursor.execute("SELECT email, password FROM users WHERE username=%s", (session["username"],))
            result = cursor.fetchone()

            if result is None:
                flash("User not found.", "danger")
                conn.close()
                return redirect(url_for("update_password"))

            db_email = result["email"]        
            db_password = result["password"]  

            if email != db_email:
                flash("Email does not match.", "danger")
                conn.close()
                return redirect(url_for("update_password"))

            if current_password != db_password:
                flash("Incorrect current password.", "danger")
                conn.close()
                return redirect(url_for("update_password"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                conn.close()
                return redirect(url_for("update_password"))

            cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, session["username"]))
            conn.commit()

        conn.close()
        flash("Password updated successfully!", "success")
        return redirect(url_for("home"))
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
        user = cursor.fetchone()
    conn.close()
    return render_template("user_changepass.html", user=user)


#--------------------------------------- User Update Information--------------------------------------------#

@app.route("/update_users", methods=["GET", "POST"])
def update_users():
    if "username" not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE username = %s", (session["username"],))
    user = cursor.fetchone()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update":
            full_name = request.form.get("full_name")
            phone = request.form.get("phone")
            username = request.form.get("username")
            birthday = request.form.get("birthday")
            email = request.form.get("email")
            gender = request.form.get("gender")
            address = request.form.get("address")

            cursor.execute("""
                UPDATE users
                SET full_name = %s,
                    phone = %s,
                    email = %s,
                    username = %s,
                    birthday = %s,
                    gender = %s,
                    address = %s
                WHERE username = %s
            """, (full_name, phone, email, username, birthday, gender, address, session["username"]))
            conn.commit()

            if username != session["username"]:
                session["username"] = username

            flash("✅ Profile updated successfully!", "success")
            return redirect(url_for("user_info"))

        conn.close()
        return redirect(url_for("update_users"))

    conn.close()

    if user:
        for field in ["full_name", "phone", "birthday", "gender", "address", "email"]:
            user[field] = user.get(field) or ""

    return render_template("user_update.html", user=user)

#-------- User Acc Delete ---------#

@app.route('/account_delete', methods=['POST'])
def account_delete():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE username=%s", (session["username"],))
        conn.commit()

    conn.close()
    session.clear()
    flash("❌ Profile deleted successfully.", "success")
    return redirect(url_for("login"))



#--------------------------------------- Upload Profile Picture --------------------------------------------#


@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if "username" not in session:
        return redirect(url_for("login"))
    
    file = request.files.get('profile_pic')
    
    if file:
        filename = file.filename 
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET profile_pic=%s WHERE username=%s",
                (filename, session["username"])
            )
            conn.commit()
        conn.close()
        flash("Profile picture updated successfully!", "success")
    else:
        flash("No file selected.")

    return redirect(url_for("user_info"))






#--------------------------------------- User Calendar View --------------------------------------------#
@app.route("/calendar")
def calendar_view():
    
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]
    
    today = datetime.date.today()

    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    
    selected_date_str = request.args.get("selected_date")
    if selected_date_str:
        selected_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        selected_date = None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, calendar.monthrange(year, month)[1])
    cursor.execute("SELECT * FROM events WHERE event_date BETWEEN %s AND %s", (first_day, last_day))
    events = cursor.fetchall()

    selected_events = []
    if selected_date:
        cursor.execute("SELECT * FROM events WHERE event_date=%s", (selected_date,))
        selected_events = cursor.fetchall()

    conn.close()

    # ✅ Calendar setup
    current_month_name = calendar.month_name[month]
    first_weekday, num_days = calendar.monthrange(year, month)
    days = []

    for _ in range((first_weekday + 1) % 7):
        days.append(None)
    for d in range(1, num_days + 1):
        days.append(datetime.date(year, month, d))


    return render_template(
        "user_calendar.html",
        user=user,
        today=today,
        selected_date=selected_date,
        selected_events=selected_events,
        current_year=year,
        current_month=month,
        current_month_name=current_month_name,
        days=days,
        events=events,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )
#----------------------------------------- User About Us -----------------------------------------#
@app.route('/about_us')
def about_us():
    if "username" in session:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (session["username"],))
            user = cursor.fetchone()

            cursor.execute("SELECT * FROM notifications WHERE username = %s ORDER BY created_at DESC", (session["username"],))
            notifications = cursor.fetchall()

            unread_count = sum(1 for n in notifications if not n['is_read'])

        conn.close()

        return render_template("user_about_us.html", user=user, unread_count = unread_count)
    
#----------------------------------------- Logout -----------------------------------------#

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)

        