# # """
# # DATABASE SEED SCRIPT
# # ====================
# # Creates a complete, realistic dataset so the application can be
# # run and demonstrated immediately after setup.

# # Usage:
# #     python scripts/seed.py          # creates fresh seed data
# #     python scripts/seed.py --reset  # drops and recreates everything

# # What gets created:
# #     Departments    : 3  (CSE-UG, MBA-PG, ECE-both)
# #     Principal      : 1
# #     HODs           : 3  (one per department)
# #     Teachers       : 6  (2 per department)
# #     Students       : 20 (spread across semesters and programs)
# #     Subjects       : 12 (4 per department)
# #     Attendance     : ~300 records (30 days history)
# #     Notifications  : various welcome + low-attendance alerts

# # Login credentials (all passwords: College@123):
# #     principal@college.edu  → Principal
# #     hod.cse@college.edu    → HOD (CSE)
# #     hod.mba@college.edu    → HOD (MBA)
# #     hod.ece@college.edu    → HOD (ECE)
# #     teacher1.cse@college.edu / teacher2.cse@college.edu → Teachers
# #     student001@college.edu → Student (CSE UG Sem 3, attendance ~80%)
# #     student002@college.edu → Student (CSE UG Sem 3, attendance ~60% LOW)
# #     ... (see full list printed after seed)
# # """

# # import sys
# # import os
# # import random
# # from datetime import date, timedelta

# # # Make sure we can import from the project root
# # sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # from app import create_app, db
# # from app.models.user         import User, Role
# # from app.models.department   import Department
# # from app.models.teacher      import Teacher
# # from app.models.student      import Student
# # from app.models.subject      import Subject
# # from app.models.attendance   import Attendance
# # from app.models.notification import Notification

# # DEFAULT_PASSWORD = 'College@123'
# # RESET = '--reset' in sys.argv


# # def make_user(email, first, last, role, password=DEFAULT_PASSWORD):
# #     u = User(email=email, first_name=first, last_name=last, role=role)
# #     u.set_password(password)
# #     db.session.add(u)
# #     db.session.flush()
# #     return u


# # def seed():
# #     app = create_app('development')
# #     with app.app_context():

# #         if RESET:
# #             print('⚠️  Dropping all tables...')
# #             db.drop_all()

# #         db.create_all()

# #         # Guard: don't re-seed if data already exists
# #         if not RESET and User.query.first():
# #             print('Database already has data. Use --reset to reseed.')
# #             return

# #         print('🌱 Seeding database...')
# #         random.seed(42)  # reproducible randomness

# #         # ══════════════════════════════════════════════════════════
# #         #  PRINCIPAL
# #         # ══════════════════════════════════════════════════════════
# #         principal = make_user('principal@spcollege.edu',
# #                                'Dr. Haris Izhar', 'Tantray', Role.PRINCIPAL)
# #         print(f'  ✅ Principal:   {principal.email}')

# #         # ══════════════════════════════════════════════════════════
# #         #  DEPARTMENTS
# #         # ══════════════════════════════════════════════════════════
# #         dept_IT = Department(name='Department of Information Technology',
# #                               code='IT', program_type='both')
# #         dept_Zoology = Department(name='Department of Zoology',
# #                               code='ZoG', program_type='both')
# #         dept_Physics = Department(name='Department of Physics',
# #                               code='Py', program_type='both')
# #         db.session.add_all([dept_IT, dept_Zoology, dept_Physics])
# #         db.session.flush()
# #         print(f'  ✅ Departments: IT (Both), Zoology (Both), Py (both)')

# #         # ══════════════════════════════════════════════════════════
# #         #  HODs
# #         # ══════════════════════════════════════════════════════════
# #         hod_IT_u = make_user('hod.IT@spcollege.edu',
# #                                'Dr. Waseem', 'Akram', Role.HOD)
# #         hod_Zoology_u = make_user('hod.Zoology@spcollege.edu',
# #                                'Prof. Showkat', 'Malik', Role.HOD)
# #         hod_Py_u = make_user('hod.Py@spcollege.edu',
# #                                'Dr. Showkat', 'Rasool', Role.HOD)

# #         hod_IT = Teacher(user_id=hod_IT_u.id, department_id=dept_IT.id,
# #                           employee_id='EMP001', is_hod=True)
# #         hod_Zoology = Teacher(user_id=hod_Zoology_u.id, department_id=dept_Zoology.id,
# #                           employee_id='EMP002', is_hod=True)
# #         hod_Py = Teacher(user_id=hod_Py_u.id, department_id=dept_Physics.id,
# #                           employee_id='EMP003', is_hod=True)
# #         db.session.add_all([hod_IT, hod_Zoology, hod_Py])
# #         db.session.flush()
# #         print(f'  ✅ HODs:        hod.IT / hod.Zoology / hod.Py @spcollege.edu')

# #         # ══════════════════════════════════════════════════════════
# #         #  TEACHERS  (2 per dept)
# #         # ══════════════════════════════════════════════════════════
# #         teacher_data = [
# #             ('uzmahamid.IT@spcollege.edu','Uzma','Hamid',  dept_IT,'EMP011'),
# #             ('kursheed.IT@spcollege.edu','Prof. Kursheed','Ahmad', dept_IT,'EMP012'),
# #             ('feroz.zg@spcollege.edu','Prof. Feroz Ahmad', 'Dar',  dept_Zoology,'EMP021'),
# #             ('anis.zg@spcollege.edu','Prof. Mohd. Anis','Ganie',   dept_Zoology,'EMP022'),
# #             ('muzamil.py@spcollege.edu','Prof. Muzamil','Bhat',   dept_Physics,'EMP031'),
# #             ('riyaz.py@college.edu','Prof. Riyaz','Ahmed Bhat', dept_Physics,'EMP032'),
# #         ]
# #         teachers = {}
# #         for email, fn, ln, dept, emp_id in teacher_data:
# #             u = make_user(email, fn, ln, Role.TEACHER)
# #             t = Teacher(user_id=u.id, department_id=dept.id,
# #                         employee_id=emp_id, is_hod=False)
# #             db.session.add(t)
# #             teachers[email] = (u, t)
# #         db.session.flush()
# #         print(f'  ✅ Teachers:    6 created (2 per department)')

# #         # ══════════════════════════════════════════════════════════
# #         #  SUBJECTS
# #         # ══════════════════════════════════════════════════════════
# #         subject_data = [
# #             # IT subjects
# #             ('Data Structures & Algorithms', 'DSA301', dept_IT, 3, 'UG', 45),
# #             ('Operating Systems',            'OS302',  dept_IT, 3, 'UG', 40),
# #             ('Database Management Systems',  'DBMS501',dept_IT, 5, 'UG', 40),
# #             ('Machine Learning',             'ML502',  dept_IT, 2, 'PG', 35),
# #             # Zoology subjects
# #             ('Non-Chordates and Chordates',  'Nc&C101',  dept_Zoology, 2, 'UG', 30),
# #             ('Principles of Ecology',        'PECG102',  dept_Zoology, 2, 'UG', 30),
# #             ('Mendelian Genetics',           'MG301',    dept_Zoology, 2, 'PG', 25),
# #             ('Comparative Physicology',      'COM302',    dept_Zoology, 2, 'PG', 30),
# #             # Physics subjects (both UG and PG)
# #             ('Digital Electronics',          'DE201',  dept_Physics, 2, 'UG', 40),
# #             ('Signal Processing',            'SP202',  dept_Physics, 2, 'UG', 35),
# #             ('VLSI Design',                  'VL101',  dept_Physics, 1, 'PG', 30),
# #             ('Embedded Systems',             'ES102',  dept_Physics, 1, 'PG', 30),
# #         ]
# #         subjects = {}
# #         for name, code, dept, sem, pt, tc in subject_data:
# #             s = Subject(department_id=dept.id, name=name, code=code,
# #                         semester=sem, program_type=pt, total_classes=tc)
# #             db.session.add(s)
# #             subjects[code] = s
# #         db.session.flush()

# #         # Assign subjects to teachers
# #         t1_IT = teachers['uzmahamid.IT@spcollege.edu'][1]
# #         t2_IT = teachers['kursheed.IT@spcollege.edu'][1]
# #         t1_Zg = teachers['feroz.zg@spcollege.edu'][1]
# #         t2_Zg = teachers['anis.zg@spcollege.edu'][1]
# #         t1_Py = teachers['muzamil.py@spcollege.edu'][1]
# #         t2_Py = teachers['riyaz.py@college.edu'][1]

# #         t1_IT.subjects.append(subjects['DSA301'])
# #         t1_IT.subjects.append(subjects['OS302'])
# #         t2_IT.subjects.append(subjects['DBMS501'])
# #         t2_IT.subjects.append(subjects['ML502'])

# #         t1_Zg.subjects.append(subjects['Nc&C101'])
# #         t1_Zg.subjects.append(subjects['PECG102'])
# #         t2_Zg.subjects.append(subjects['MG301'])
# #         t2_Zg.subjects.append(subjects['COM302'])

# #         t1_Py.subjects.append(subjects['DE201'])
# #         t1_Py.subjects.append(subjects['SP202'])
# #         t2_Py.subjects.append(subjects['VL101'])
# #         t2_Py.subjects.append(subjects['ES102'])
# #         db.session.flush()
# #         print(f'  ✅ Subjects:    12 created and assigned to teachers')

# #         # ══════════════════════════════════════════════════════════
# #         #  STUDENTS
# #         # ══════════════════════════════════════════════════════════
# #         student_data = [
# #             # CSE UG Sem 3 (will have attendance marked for DSA & OS)
# #             ('student001@college.edu','Rahul',   'Sharma',  dept_IT, 'CSE2022001','2022-23','UG',3, 0.85),
# #             ('student002@college.edu','Priya',   'Patel',   dept_IT, 'CSE2022002','2022-23','UG',3, 0.58),  # LOW
# #             ('student003@college.edu','Vikram',  'Singh',   dept_IT, 'CSE2022003','2022-23','UG',3, 0.76),
# #             ('student004@college.edu','Ananya',  'Roy',     dept_IT, 'CSE2022004','2022-23','UG',3, 0.92),
# #             # CSE UG Sem 5
# #             ('student005@college.edu','Arjun',   'Menon',   dept_IT, 'CSE2020005','2020-21','UG',5, 0.80),
# #             ('student006@college.edu','Deepa',   'Nair',    dept_IT, 'CSE2020006','2020-21','UG',5, 0.65),
# #             # MBA PG Sem 1
# #             ('student007@college.edu','Rohit',   'Gupta',   dept_Zoology, 'MBA2023007','2023-24','PG',1, 0.88),
# #             ('student008@college.edu','Sneha',   'Verma',   dept_Zoology, 'MBA2023008','2023-24','PG',1, 0.72),
# #             ('student009@college.edu','Arun',    'Joshi',   dept_Zoology, 'MBA2023009','2023-24','PG',1, 0.55),  # LOW
# #             # MBA PG Sem 3
# #             ('student010@college.edu','Kavya',   'Iyer',    dept_Zoology, 'MBA2022010','2022-23','PG',3, 0.91),
# #             ('student011@college.edu','Sanjay',  'Kumar',   dept_Zoology, 'MBA2022011','2022-23','PG',3, 0.79),
# #             # ECE UG Sem 2
# #             ('student012@college.edu','Meena',   'Pillai',  dept_Physics, 'ECE2023012','2023-24','UG',2, 0.83),
# #             ('student013@college.edu','Suresh',  'Das',     dept_Physics, 'ECE2023013','2023-24','UG',2, 0.61),
# #             ('student014@college.edu','Lakshmi', 'Bhat',    dept_Physics, 'ECE2023014','2023-24','UG',2, 0.78),
# #             # ECE PG Sem 1
# #             ('student015@college.edu','Kiran',   'Rao',     dept_Physics, 'ECE2023015','2023-24','PG',1, 0.90),
# #             ('student016@college.edu','Pooja',   'Shah',    dept_Physics, 'ECE2023016','2023-24','PG',1, 0.68),
# #             # CSE UG Sem 6 (graduation eligible!)
# #             ('student017@college.edu','Amit',    'Mehta',   dept_IT, 'CSE2019017','2019-20','UG',6, 0.88),
# #             ('student018@college.edu','Ritu',    'Chopra',  dept_IT, 'CSE2019018','2019-20','UG',6, 0.82),
# #             # CSE — already graduated
# #             ('student019@college.edu','Prakash', 'Reddy',   dept_IT, 'CSE2018019','2018-19','UG',8, 0.79),
# #             ('student020@college.edu','Divya',   'Pillai',  dept_IT, 'CSE2018020','2018-19','UG',8, 0.84),
# #         ]

# #         student_objects = {}
# #         for (email, fn, ln, dept, roll, year, pt, sem, _att_pct) in student_data:
# #             u = make_user(email, fn, ln, Role.STUDENT)
# #             s = Student(user_id=u.id, department_id=dept.id,
# #                         roll_number=roll, admission_year=year,
# #                         program_type=pt, semester=sem)
# #             db.session.add(s)
# #             student_objects[roll] = (u, s)
# #         db.session.flush()

# #         # Graduate the last two
# #         for roll in ['CSE2018019', 'CSE2018020']:
# #             u, s = student_objects[roll]
# #             s.is_graduated        = True
# #             s.graduation_semester = 8
# #             s.graduation_year     = '2022'
# #             s.graduation_reason   = 'Completed full 8-semester B.Tech programme.'
# #             s.graduated_by_id     = hod_IT.id
# #             u.is_active           = False
# #         db.session.flush()
# #         print(f'  ✅ Students:    20 created (2 graduated, 2 eligible for graduation)')

# #         # ══════════════════════════════════════════════════════════
# #         #  ATTENDANCE (30 days of realistic data)
# #         # ══════════════════════════════════════════════════════════
# #         today       = date.today()
# #         att_records = 0

# #         # Subject → teacher map for marking
# #         subject_teacher_map = {
# #             'DSA301': t1_IT, 'OS302': t1_IT,
# #             'DBMS501': t2_IT, 'ML502': t2_IT,
# #             'FM101': t1_Zg, 'MM102': t1_Zg,
# #             'SM301': t2_Zg, 'BA302': t2_Zg,
# #             'DE201': t1_Py, 'SP202': t1_Py,
# #             'VL101': t2_Py, 'ES102': t2_Py,
# #         }

# #         att_data = [
# #             # (subject_code, [student rolls], target_pct)
# #             ('DSA301',
# #              [('CSE2022001',0.85),('CSE2022002',0.58),('CSE2022003',0.76),('CSE2022004',0.92)]),
# #             ('OS302',
# #              [('CSE2022001',0.88),('CSE2022002',0.62),('CSE2022003',0.74),('CSE2022004',0.90)]),
# #             ('DBMS501',
# #              [('CSE2020005',0.80),('CSE2020006',0.65)]),
# #             ('ML502',
# #              [('CSE2020005',0.78),('CSE2020006',0.70)]),
# #             ('FM101',
# #              [('MBA2023007',0.88),('MBA2023008',0.72),('MBA2023009',0.55)]),
# #             ('MM102',
# #              [('MBA2023007',0.90),('MBA2023008',0.75),('MBA2023009',0.58)]),
# #             ('DE201',
# #              [('ECE2023012',0.83),('ECE2023013',0.61),('ECE2023014',0.78)]),
# #             ('SP202',
# #              [('ECE2023012',0.80),('ECE2023013',0.65),('ECE2023014',0.82)]),
# #             ('VL101',
# #              [('ECE2023015',0.90),('ECE2023016',0.68)]),
# #             ('ES102',
# #              [('ECE2023015',0.88),('ECE2023016',0.70)]),
# #         ]

# #         # Generate 20 class days (weekdays only, going back from today)
# #         class_days = []
# #         d = today - timedelta(days=1)
# #         while len(class_days) < 20:
# #             if d.weekday() < 5:   # Mon–Fri only
# #                 class_days.append(d)
# #             d -= timedelta(days=1)
# #         class_days.reverse()

# #         for subj_code, student_rolls in att_data:
# #             subj    = subjects[subj_code]
# #             teacher = subject_teacher_map[subj_code]
# #             for class_date in class_days:
# #                 for roll, target_pct in student_rolls:
# #                     if roll not in student_objects:
# #                         continue
# #                     _, stu = student_objects[roll]
# #                     # Decide status based on target attendance %
# #                     rand = random.random()
# #                     if rand < target_pct:
# #                         status = 'present'
# #                     elif rand < target_pct + 0.08:
# #                         status = 'leave'    # ~8% chance of authorised leave
# #                     elif rand < target_pct + 0.12:
# #                         status = 'event'    # ~4% chance of event
# #                     else:
# #                         status = 'absent'

# #                     db.session.add(Attendance(
# #                         student_id   = stu.id,
# #                         subject_id   = subj.id,
# #                         marked_by_id = teacher.id,
# #                         date         = class_date,
# #                         status       = status,
# #                         semester     = stu.semester,
# #                     ))
# #                     att_records += 1

# #         db.session.flush()
# #         print(f'  ✅ Attendance:  {att_records} records across 20 class days')

# #         # ══════════════════════════════════════════════════════════
# #         #  NOTIFICATIONS
# #         # ══════════════════════════════════════════════════════════
# #         # Low-attendance alerts for students below 75%
# #         low_att_students = [
# #             ('CSE2022002', 'DSA301', 58.0),
# #             ('MBA2023009', 'FM101',  55.0),
# #             ('MBA2023009', 'MM102',  58.0),
# #         ]
# #         for roll, subj_code, pct in low_att_students:
# #             if roll not in student_objects:
# #                 continue
# #             stu_u, stu = student_objects[roll]
# #             subj = subjects[subj_code]
# #             db.session.add(Notification(
# #                 user_id = stu_u.id,
# #                 type    = 'danger',
# #                 title   = f'Low Attendance Alert — {subj_code}',
# #                 message = (
# #                     f'Your attendance in {subj.name} has dropped to {pct}%. '
# #                     f'Minimum required is 75%. Please attend classes regularly.'
# #                 ),
# #                 target_type = 'system',
# #             ))

# #         # Welcome notifications for HODs
# #         for hod_u_obj, dept_obj in [
# #             (hod_IT_u, dept_IT),
# #             (hod_Zoology_u, dept_Zoology),
# #             (hod_Py_u, dept_Physics),
# #         ]:
# #             db.session.add(Notification(
# #                 user_id     = hod_u_obj.id,
# #                 type        = 'success',
# #                 title       = 'Welcome as HOD',
# #                 message     = (
# #                     f'You have been appointed as HOD of {dept_obj.name}. '
# #                     f'You can manage teachers, students, subjects, and attendance.'
# #                 ),
# #                 target_type = 'system',
# #             ))

# #         # Graduation-eligible alert for HOD
# #         db.session.add(Notification(
# #             user_id     = hod_IT_u.id,
# #             type        = 'info',
# #             title       = '2 Students Ready to Graduate',
# #             message     = (
# #                 'Students Amit Mehta (CSE2019017) and Ritu Chopra (CSE2019018) '
# #                 'are at Semester 6 and eligible for graduation. '
# #                 'Visit Graduation Management to proceed.'
# #             ),
# #             target_type = 'system',
# #         ))

# #         db.session.commit()
# #         print(f'  ✅ Notifications: seeded for low-att alerts and HOD welcome')

# #         # ══════════════════════════════════════════════════════════
# #         #  PRINT SUMMARY
# #         # ══════════════════════════════════════════════════════════
# #         print()
# #         print('═' * 60)
# #         print('  SEED COMPLETE — Login Credentials (password: College@123)')
# #         print('═' * 60)
# #         print()
# #         accounts = [
# #             ('Principal', 'principal@college.edu',   '→ /principal/dashboard'),
# #             ('HOD (CSE)', 'hod.cse@college.edu',     '→ /hod/dashboard'),
# #             ('HOD (MBA)', 'hod.mba@college.edu',     '→ /hod/dashboard'),
# #             ('HOD (ECE)', 'hod.ece@college.edu',     '→ /hod/dashboard'),
# #             ('Teacher',   'teacher1.cse@college.edu','→ /teacher/dashboard'),
# #             ('Teacher',   'teacher2.cse@college.edu','→ /teacher/dashboard'),
# #             ('Student (good att)',  'student001@college.edu', '→ /student/dashboard'),
# #             ('Student (LOW att)',   'student002@college.edu', '→ /student/dashboard'),
# #             ('Student (graduated)', 'student019@college.edu', '→ cannot login'),
# #         ]
# #         for role, email, route in accounts:
# #             print(f'  {role:25s}  {email:35s}  {route}')
# #         print()
# #         print(f'  Run with:  python run.py')
# #         print(f'  Open:      http://localhost:5000')
# #         print('═' * 60)


# # if __name__ == '__main__':
# #     seed()


# """
# DATABASE SEED SCRIPT
# ====================
# Creates a complete, realistic dataset so the application can be
# run and demonstrated immediately after setup.

# Usage:
#     python scripts/seed.py         # creates fresh seed data
#     python scripts/seed.py --reset # drops and recreates everything

# What gets created:
#     Departments    : 3  (IT, Zoology, Physics)
#     Principal      : 1
#     HODs           : 3  (one per department)
#     Teachers       : 6  (2 per department)
#     Students       : 20 (spread across semesters and programs)
#     Subjects       : 12 (4 per department)
#     Attendance     : ~300 records (30 days history)
#     Notifications  : various welcome + low-attendance alerts

# Login credentials (all passwords: College@123):
#     principal@spcollege.edu    → Principal
#     hod.IT@spcollege.edu       → HOD (IT)
#     hod.Zoology@spcollege.edu  → HOD (Zoology)
#     hod.Py@spcollege.edu       → HOD (Physics)
#     uzmahamid.IT@spcollege.edu → Teacher
#     student001@spcollege.edu   → Student (IT UG Sem 3, attendance ~85%)
#     student002@spcollege.edu   → Student (IT UG Sem 3, attendance ~58% LOW)
#     ... (see full list printed after seed)
# """

# import sys
# import os
# import random
# from datetime import date, timedelta

# # Make sure we can import from the project root
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app import create_app, db
# from app.models.user         import User, Role
# from app.models.department   import Department
# from app.models.teacher      import Teacher
# from app.models.student      import Student
# from app.models.subject      import Subject
# from app.models.attendance   import Attendance
# from app.models.notification import Notification

# DEFAULT_PASSWORD = 'College@123'
# RESET = '--reset' in sys.argv


# def make_user(email, first, last, role, password=DEFAULT_PASSWORD):
#     u = User(email=email, first_name=first, last_name=last, role=role)
#     u.set_password(password)
#     db.session.add(u)
#     db.session.flush()
#     return u


# def seed():
#     app = create_app('development')
#     with app.app_context():

#         if RESET:
#             print('⚠️  Dropping all tables...')
#             db.drop_all()

#         db.create_all()

#         # Guard: don't re-seed if data already exists
#         if not RESET and User.query.first():
#             print('Database already has data. Use --reset to reseed.')
#             return

#         print('🌱 Seeding database...')
#         random.seed(42)  # reproducible randomness

#         # ══════════════════════════════════════════════════════════
#         #  PRINCIPAL
#         # ══════════════════════════════════════════════════════════
#         principal = make_user('principal@spcollege.edu',
#                                'Dr. Haris Izhar', 'Tantray', Role.PRINCIPAL)
#         print(f'  ✅ Principal:   {principal.email}')

#         # ══════════════════════════════════════════════════════════
#         #  DEPARTMENTS
#         # ══════════════════════════════════════════════════════════
#         dept_IT = Department(name='Department of Information Technology',
#                               code='IT', program_type='both')
#         dept_Zoology = Department(name='Department of Zoology',
#                               code='ZoG', program_type='both')
#         dept_Physics = Department(name='Department of Physics',
#                               code='Py', program_type='both')
#         db.session.add_all([dept_IT, dept_Zoology, dept_Physics])
#         db.session.flush()
#         print(f'  ✅ Departments: IT (Both), Zoology (Both), Py (both)')

#         # ══════════════════════════════════════════════════════════
#         #  HODs
#         # ══════════════════════════════════════════════════════════
#         hod_IT_u = make_user('hodIT@spcollege.edu',
#                                'Dr. Waseem', 'Akram', Role.HOD)
#         hod_Zoology_u = make_user('hodZoology@spcollege.edu',
#                                'Prof. Showkat', 'Malik', Role.HOD)
#         hod_Py_u = make_user('hodPy@spcollege.edu',
#                                'Dr. Showkat', 'Rasool', Role.HOD)

#         hod_IT = Teacher(user_id=hod_IT_u.id, department_id=dept_IT.id,
#                           employee_id='EMP001', is_hod=True)
#         hod_Zoology = Teacher(user_id=hod_Zoology_u.id, department_id=dept_Zoology.id,
#                           employee_id='EMP002', is_hod=True)
#         hod_Py = Teacher(user_id=hod_Py_u.id, department_id=dept_Physics.id,
#                           employee_id='EMP003', is_hod=True)
#         db.session.add_all([hod_IT, hod_Zoology, hod_Py])
#         db.session.flush()
#         print(f'  ✅ HODs:        hod.IT / hod.Zoology / hod.Py @spcollege.edu')

#         # ══════════════════════════════════════════════════════════
#         #  TEACHERS  (2 per dept)
#         # ══════════════════════════════════════════════════════════
#         teacher_data = [
#             ('uzmahamid@spcollege.edu','Uzma','Hamid',  dept_IT,'EMP011'),
#             ('kursheed@spcollege.edu','Prof. Kursheed','Ahmad', dept_IT,'EMP012'),
#             ('feroz@spcollege.edu','Prof. Feroz Ahmad', 'Dar',  dept_Zoology,'EMP021'),
#             ('anis@spcollege.edu','Prof. Mohd. Anis','Ganie',   dept_Zoology,'EMP022'),
#             ('muzamil@spcollege.edu','Prof. Muzamil','Bhat',    dept_Physics,'EMP031'),
#             ('riyaz@spcollege.edu','Prof. Riyaz','Ahmed Bhat', dept_Physics,'EMP032'),
#         ]
#         teachers = {}
#         for email, fn, ln, dept, emp_id in teacher_data:
#             u = make_user(email, fn, ln, Role.TEACHER)
#             t = Teacher(user_id=u.id, department_id=dept.id,
#                         employee_id=emp_id, is_hod=False)
#             db.session.add(t)
#             teachers[email] = (u, t)
#         db.session.flush()
#         print(f'  ✅ Teachers:    6 created (2 per department)')

#         # ══════════════════════════════════════════════════════════
#         #  SUBJECTS
#         # ══════════════════════════════════════════════════════════
#         subject_data = [
#             # IT subjects
#             ('Data Structures & Algorithms', 'DSA301', dept_IT, 3, 'UG', 45),
#             ('Operating Systems',            'OS302',  dept_IT, 3, 'UG', 40),
#             ('Database Management Systems',  'DBMS501',dept_IT, 5, 'UG', 40),
#             ('Machine Learning',             'ML502',  dept_IT, 2, 'PG', 35),
#             # Zoology subjects
#             ('Non-Chordates and Chordates',  'Nc&C101',  dept_Zoology, 2, 'UG', 30),
#             ('Principles of Ecology',        'PECG102',  dept_Zoology, 2, 'UG', 30),
#             ('Mendelian Genetics',           'MG301',    dept_Zoology, 2, 'PG', 25),
#             ('Comparative Physicology',      'COM302',    dept_Zoology, 2, 'PG', 30),
#             # Physics subjects (both UG and PG)
#             ('Digital Electronics',          'DE201',  dept_Physics, 2, 'UG', 40),
#             ('Signal Processing',            'SP202',  dept_Physics, 2, 'UG', 35),
#             ('VLSI Design',                  'VL101',  dept_Physics, 1, 'PG', 30),
#             ('Embedded Systems',             'ES102',  dept_Physics, 1, 'PG', 30),
#         ]
#         subjects = {}
#         for name, code, dept, sem, pt, tc in subject_data:
#             s = Subject(department_id=dept.id, name=name, code=code,
#                         semester=sem, program_type=pt, total_classes=tc)
#             db.session.add(s)
#             subjects[code] = s
#         db.session.flush()

#         # Assign subjects to teachers
#         t1_IT = teachers['uzmahamid@spcollege.edu'][1]
#         t2_IT = teachers['kursheed@spcollege.edu'][1]
#         t1_Zg = teachers['feroz@spcollege.edu'][1]
#         t2_Zg = teachers['anis@spcollege.edu'][1]
#         t1_Py = teachers['muzamil@spcollege.edu'][1]
#         t2_Py = teachers['riyaz@spcollege.edu'][1]

#         t1_IT.subjects.append(subjects['DSA301'])
#         t1_IT.subjects.append(subjects['OS302'])
#         t2_IT.subjects.append(subjects['DBMS501'])
#         t2_IT.subjects.append(subjects['ML502'])

#         t1_Zg.subjects.append(subjects['Nc&C101'])
#         t1_Zg.subjects.append(subjects['PECG102'])
#         t2_Zg.subjects.append(subjects['MG301'])
#         t2_Zg.subjects.append(subjects['COM302'])

#         t1_Py.subjects.append(subjects['DE201'])
#         t1_Py.subjects.append(subjects['SP202'])
#         t2_Py.subjects.append(subjects['VL101'])
#         t2_Py.subjects.append(subjects['ES102'])
#         db.session.flush()
#         print(f'  ✅ Subjects:    12 created and assigned to teachers')

#         # ══════════════════════════════════════════════════════════
#         #  STUDENTS
#         # ══════════════════════════════════════════════════════════
#         student_data = [
#             # IT UG Sem 3 (will have attendance marked for DSA & OS)
#             ('muzammil@spcollege.edu','Muzamil',   'Gulzar',  dept_IT, 'IT2022001','2022-23','UG',3, 0.85),
#             ('ajamul@spcollege.edu','Ajamul',   'Peer',   dept_IT, 'IT2022002','2022-23','UG',3, 0.58),  # LOW
#             ('baaqir@spcollege.edu','Baaqir',  'Mehmood',   dept_IT, 'IT2022003','2022-23','UG',3, 0.76),
#             ('sammy@spcollege.edu','Syed',  'Samiullah',     dept_IT, 'IT2022004','2022-23','UG',3, 0.92),
#             # IT UG Sem 5
#             ('umar@spcollege.edu','Umar',   'Rashid',   dept_IT, 'IT2020005','2020-21','UG',5, 0.80),
#             ('muied@spcollege.edu','Muied',   'Riyaz',    dept_IT, 'IT2020006','2020-21','UG',5, 0.65),
#             # Zoology PG Sem 1
#             ('mehran@spcollege.edu','Mehran',   'Hassan',   dept_Zoology, 'ZG2023007','2023-24','PG',1, 0.88),
#             ('amir@spcollege.edu','Syed',   'Aamir',   dept_Zoology, 'ZG2023008','2023-24','PG',1, 0.72),
#             ('Ifra@spcollege.edu','Ms',    'Ifra',   dept_Zoology, 'ZG2023009','2023-24','PG',1, 0.55),  # LOW
#             # Zoology PG Sem 3
#             ('kavya@spcollege.edu','Kavya',   'Iyer',    dept_Zoology, 'ZG2022010','2022-23','PG',3, 0.91),
#             ('tawseef@spcollege.edu','Tawseef',  'Kumar',   dept_Zoology, 'ZG2022011','2022-23','PG',3, 0.79),
#             # Physics UG Sem 2
#             ('mehnoor@spcollege.edu','Ms',   'Mehnoor',  dept_Physics, 'PY2023012','2023-24','UG',2, 0.83),
#             ('adil@spcollege.edu','Adil',  'Reshi',     dept_Physics, 'PY2023013','2023-24','UG',2, 0.61),
#             ('Altaf@spcollege.edu','Altaf', 'Bhat',    dept_Physics, 'PY2023014','2023-24','UG',2, 0.78),
#             # Physics PG Sem 1
#             ('showkat@spcollege.edu','Showkat',   'Lone',     dept_Physics, 'PY2023015','2023-24','PG',1, 0.90),
#             ('mehnaz@spcollege.edu','Mehnaz',   'Gul',    dept_Physics, 'PY2023016','2023-24','PG',1, 0.68),
#             # IT UG Sem 6 (graduation eligible!)
#             ('hashim@spcollege.edu','Hashim',    'Kakroo',   dept_IT, 'IT2019017','2019-20','UG',6, 0.88),
#             ('nasir@spcollege.edu','Nasir',    'Nazir',  dept_IT, 'IT2019018','2019-20','UG',6, 0.82),
#             # IT — already graduated
#             ('Asif@spcollege.edu','Asif', 'Mir',   dept_IT, 'IT2018019','2018-19','UG',8, 0.79),
#             ('Fasil@spcollege.edu','Fasil',   'Shabir',  dept_IT, 'IT2018020','2018-19','UG',8, 0.84),
#         ]

#         student_objects = {}
#         for (email, fn, ln, dept, roll, year, pt, sem, _att_pct) in student_data:
#             u = make_user(email, fn, ln, Role.STUDENT)
#             s = Student(user_id=u.id, department_id=dept.id,
#                         roll_number=roll, admission_year=year,
#                         program_type=pt, semester=sem)
#             db.session.add(s)
#             student_objects[roll] = (u, s)
#         db.session.flush()

#         # Graduate the last two
#         for roll in ['IT2018019', 'IT2018020']:
#             u, s = student_objects[roll]
#             s.is_graduated        = True
#             s.graduation_semester = 8
#             s.graduation_year     = '2022'
#             s.graduation_reason   = 'Completed full 8-semester 3+1 Year Bsc programme.'
#             s.graduated_by_id     = hod_IT.id
#             u.is_active           = False
#         db.session.flush()
#         print(f'  ✅ Students:    20 created (2 graduated, 2 eligible for graduation)')

#         # ══════════════════════════════════════════════════════════
#         #  ATTENDANCE (30 days of realistic data)
#         # ══════════════════════════════════════════════════════════
#         today       = date.today()
#         att_records = 0

#         # Subject → teacher map for marking
#         subject_teacher_map = {
#             'DSA301': t1_IT, 'OS302': t1_IT,
#             'DBMS501': t2_IT, 'ML502': t2_IT,
#             'Nc&C101': t1_Zg, 'PECG102': t1_Zg,
#             'MG301': t2_Zg, 'COM302': t2_Zg,
#             'DE201': t1_Py, 'SP202': t1_Py,
#             'VL101': t2_Py, 'ES102': t2_Py,
#         }

#         att_data = [
#             # (subject_code, [student rolls], target_pct)
#             ('DSA301',
#              [('IT2022001',0.85),('IT2022002',0.58),('IT2022003',0.76),('IT2022004',0.92)]),
#             ('OS302',
#              [('IT2022001',0.88),('IT2022002',0.62),('IT2022003',0.74),('IT2022004',0.90)]),
#             ('DBMS501',
#              [('IT2020005',0.80),('IT2020006',0.65)]),
#             ('ML502',
#              [('IT2020005',0.78),('IT2020006',0.70)]),
#             ('Nc&C101',
#              [('ZG2023007',0.88),('ZG2023008',0.72),('ZG2023009',0.55)]),
#             ('PECG102',
#              [('ZG2023007',0.90),('ZG2023008',0.75),('ZG2023009',0.58)]),
#             ('DE201',
#              [('PY2023012',0.83),('PY2023013',0.61),('PY2023014',0.78)]),
#             ('SP202',
#              [('PY2023012',0.80),('PY2023013',0.65),('PY2023014',0.82)]),
#             ('VL101',
#              [('PY2023015',0.90),('PY2023016',0.68)]),
#             ('ES102',
#              [('PY2023015',0.88),('PY2023016',0.70)]),
#         ]

#         # Generate 20 class days (weekdays only, going back from today)
#         class_days = []
#         d = today - timedelta(days=1)
#         while len(class_days) < 20:
#             if d.weekday() < 5:   # Mon–Fri only
#                 class_days.append(d)
#             d -= timedelta(days=1)
#         class_days.reverse()

#         for subj_code, student_rolls in att_data:
#             subj    = subjects[subj_code]
#             teacher = subject_teacher_map[subj_code]
#             for class_date in class_days:
#                 for roll, target_pct in student_rolls:
#                     if roll not in student_objects:
#                         continue
#                     _, stu = student_objects[roll]
#                     # Decide status based on target attendance %
#                     rand = random.random()
#                     if rand < target_pct:
#                         status = 'present'
#                     elif rand < target_pct + 0.08:
#                         status = 'leave'    # ~8% chance of authorised leave
#                     elif rand < target_pct + 0.12:
#                         status = 'event'    # ~4% chance of event
#                     else:
#                         status = 'absent'

#                     db.session.add(Attendance(
#                         student_id   = stu.id,
#                         subject_id   = subj.id,
#                         marked_by_id = teacher.id,
#                         date         = class_date,
#                         status       = status,
#                         semester     = stu.semester,
#                     ))
#                     att_records += 1

#         db.session.flush()
#         print(f'  ✅ Attendance:  {att_records} records across 20 class days')

#         # ══════════════════════════════════════════════════════════
#         #  NOTIFICATIONS
#         # ══════════════════════════════════════════════════════════
#         # Low-attendance alerts for students below 75%
#         low_att_students = [
#             ('IT2022002', 'DSA301', 58.0),
#             ('ZG2023009', 'Nc&C101', 55.0),
#             ('ZG2023009', 'PECG102', 58.0),
#         ]
#         for roll, subj_code, pct in low_att_students:
#             if roll not in student_objects:
#                 continue
#             stu_u, stu = student_objects[roll]
#             subj = subjects[subj_code]
#             db.session.add(Notification(
#                 user_id = stu_u.id,
#                 type    = 'danger',
#                 title   = f'Low Attendance Alert — {subj_code}',
#                 message = (
#                     f'Your attendance in {subj.name} has dropped to {pct}%. '
#                     f'Minimum required is 75%. Please attend classes regularly.'
#                 ),
#                 target_type = 'system',
#             ))

#         # Welcome notifications for HODs
#         for hod_u_obj, dept_obj in [
#             (hod_IT_u, dept_IT),
#             (hod_Zoology_u, dept_Zoology),
#             (hod_Py_u, dept_Physics),
#         ]:
#             db.session.add(Notification(
#                 user_id     = hod_u_obj.id,
#                 type        = 'success',
#                 title       = 'Welcome as HOD',
#                 message     = (
#                     f'You have been appointed as HOD of {dept_obj.name}. '
#                     f'You can manage teachers, students, subjects, and attendance.'
#                 ),
#                 target_type = 'system',
#             ))

#         # Graduation-eligible alert for HOD
#         db.session.add(Notification(
#             user_id     = hod_IT_u.id,
#             type        = 'info',
#             title       = '2 Students Ready to Graduate',
#             message     = (
#                 'Students Hashim (IT2019017) and Nasir (IT2019018) '
#                 'are at Semester 6 and eligible for graduation. '
#                 'Visit Graduation Management to proceed.'
#             ),
#             target_type = 'system',
#         ))

#         db.session.commit()
#         print(f'  ✅ Notifications: seeded for low-att alerts and HOD welcome')

#         # ══════════════════════════════════════════════════════════
#         #  PRINT SUMMARY
#         # ══════════════════════════════════════════════════════════
#         print()
#         print('═' * 60)
#         print('  SEED COMPLETE — Login Credentials (password: College@123)')
#         print('═' * 60)
#         print()
#         accounts = [
#             ('Principal', 'principal@spcollege.edu',    '→ /principal/dashboard'),
#             ('HOD (IT)', 'hod.IT@spcollege.edu',        '→ /hod/dashboard'),
#             ('HOD (Zoology)', 'hod.Zoology@spcollege.edu', '→ /hod/dashboard'),
#             ('HOD (Physics)', 'hod.Py@spcollege.edu',   '→ /hod/dashboard'),
#             ('Teacher',   'uzmahamid.IT@spcollege.edu', '→ /teacher/dashboard'),
#             ('Teacher',   'riyaz.py@spcollege.edu',     '→ /teacher/dashboard'),
#             ('Student (good att)',  'student001@spcollege.edu', '→ /student/dashboard'),
#             ('Student (LOW att)',   'student002@spcollege.edu', '→ /student/dashboard'),
#             ('Student (graduated)', 'student019@spcollege.edu', '→ cannot login'),
#         ]
#         for role, email, route in accounts:
#             print(f'  {role:25s}  {email:35s}  {route}')
#         print()
#         print(f'  Run with:  python run.py')
#         print(f'  Open:      http://localhost:5000')
#         print('═' * 60)


# if __name__ == '__main__':
#     seed()




"""
DATABASE SEED SCRIPT
====================
Creates a complete, realistic dataset for SP College.

Usage:
    python scripts/seed.py          # creates fresh seed data
    python scripts/seed.py --reset  # drops and recreates everything

Login credentials (all passwords: College@123):
    principal@spcollege.edu       → Principal
    hod.IT@spcollege.edu          → HOD (IT)
    hod.Zoology@spcollege.edu     → HOD (Zoology)
    hod.Py@spcollege.edu          → HOD (Physics)
    uzmahamid.IT@spcollege.edu    → Teacher (IT)
    riyaz.py@spcollege.edu        → Teacher (Physics)
    muzamil@spcollege.edu         → Student (IT UG Sem 3, ~85%)
    ajamul@spcollege.edu          → Student (IT UG Sem 3, ~58% LOW)
    mehran@spcollege.edu          → Student (Zoology PG Sem 2, ~88%)
"""

import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user         import User, Role
from app.models.department   import Department
from app.models.teacher      import Teacher
from app.models.student      import Student
from app.models.subject      import Subject
from app.models.attendance   import Attendance
from app.models.notification import Notification

DEFAULT_PASSWORD = 'College@123'
RESET = '--reset' in sys.argv


def make_user(email, first, last, role, password=DEFAULT_PASSWORD):
    u = User(email=email, first_name=first, last_name=last, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.flush()
    return u


def seed():
    app = create_app('development')
    with app.app_context():

        if RESET:
            print('⚠️  Dropping all tables...')
            db.drop_all()

        db.create_all()

        if not RESET and User.query.first():
            print('Database already has data. Use --reset to reseed.')
            return

        print('🌱 Seeding database...')
        random.seed(42)

        # ── PRINCIPAL ──────────────────────────────────────────────
        principal = make_user('principal@spcollege.edu',
                               'Dr. Haris Izhar', 'Tantray', Role.PRINCIPAL)
        print(f'  ✅ Principal:   {principal.email}')

        # ── DEPARTMENTS ────────────────────────────────────────────
        dept_IT      = Department(name='Department of Information Technology',
                                   code='IT',  program_type='both')
        dept_Zoology = Department(name='Department of Zoology',
                                   code='ZoG', program_type='both')
        dept_Physics = Department(name='Department of Physics',
                                   code='Py',  program_type='both')
        db.session.add_all([dept_IT, dept_Zoology, dept_Physics])
        db.session.flush()
        print(f'  ✅ Departments: IT, Zoology, Physics')

        # ── HODs ───────────────────────────────────────────────────
        hod_IT_u      = make_user('hod.IT@spcollege.edu',      'Dr. Waseem',  'Akram',  Role.HOD)
        hod_Zoology_u = make_user('hod.Zoology@spcollege.edu', 'Prof. Showkat', 'Malik',  Role.HOD)
        hod_Py_u      = make_user('hod.Py@spcollege.edu',      'Dr. Showkat', 'Rasool', Role.HOD)

        hod_IT      = Teacher(user_id=hod_IT_u.id,      department_id=dept_IT.id,      employee_id='EMP001', is_hod=True)
        hod_Zoology = Teacher(user_id=hod_Zoology_u.id, department_id=dept_Zoology.id, employee_id='EMP002', is_hod=True)
        hod_Py      = Teacher(user_id=hod_Py_u.id,      department_id=dept_Physics.id, employee_id='EMP003', is_hod=True)
        db.session.add_all([hod_IT, hod_Zoology, hod_Py])
        db.session.flush()
        print(f'  ✅ HODs:        hod.IT / hod.Zoology / hod.Py @spcollege.edu')

        # ── TEACHERS ───────────────────────────────────────────────
        teacher_rows = [
            ('uzmahamid.IT@spcollege.edu',  'Uzma',              'Hamid',       dept_IT,      'EMP011'),
            ('kursheed.IT@spcollege.edu',   'Prof. Kursheed',    'Ahmad',       dept_IT,      'EMP012'),
            ('feroz.zg@spcollege.edu',      'Prof. Feroz Ahmad', 'Dar',         dept_Zoology, 'EMP021'),
            ('anis.zg@spcollege.edu',       'Prof. Mohd. Anis',  'Ganie',       dept_Zoology, 'EMP022'),
            ('muzamil.py@spcollege.edu',    'Prof. Muzamil',     'Bhat',        dept_Physics, 'EMP031'),
            ('riyaz.py@spcollege.edu',      'Prof. Riyaz',       'Ahmed Bhat',  dept_Physics, 'EMP032'),
        ]
        teachers = {}
        for email, fn, ln, dept, emp_id in teacher_rows:
            u  = make_user(email, fn, ln, Role.TEACHER)
            tp = Teacher(user_id=u.id, department_id=dept.id,
                         employee_id=emp_id, is_hod=False)
            db.session.add(tp)
            teachers[email] = (u, tp)
        db.session.flush()
        print(f'  ✅ Teachers:    6 created (2 per department)')

        # ── SUBJECTS ───────────────────────────────────────────────
        #
        # RULE: Subject.semester + program_type MUST match the students
        # who will be enrolled, otherwise the subject won't show up.
        #
        # IT:
        #   UG sem 3 students → DSA301, OS302
        #   UG sem 5 students → DBMS501
        #   PG sem 2 students → ML502   ← was sem 2 before, no PG students had sem 2
        #                                  FIXED: changed to PG sem 3 to match ZG students,
        #                                  or kept as IT PG — but no IT PG students exist.
        #                                  Decision: IT has no PG students in seed, so ML502
        #                                  is UG sem 5 alongside DBMS501.
        #
        # Zoology:
        #   PG sem 2 students → Nc&C, PECG, MG301, COM302
        #   (was sem 1 and 2 mismatch — FIXED: all Zoology PG students now sem 2)
        #
        # Physics:
        #   UG sem 2 students → DE201, SP202
        #   PG sem 1 students → VL101, ES102
        #
        subject_rows = [
            # name,                            code,      dept,         sem, pt,   tc
            ('Data Structures & Algorithms',   'DSA301',  dept_IT,      3,  'UG', 45),
            ('Operating Systems',              'OS302',   dept_IT,      3,  'UG', 40),
            ('Database Management Systems',    'DBMS501', dept_IT,      5,  'UG', 40),
            ('Machine Learning',               'ML502',   dept_IT,      5,  'UG', 35),  # ← UG sem 5, matches IT2020 students
            ('Non-Chordates and Chordates',    'NCC101',  dept_Zoology, 2,  'PG', 30),  # ← PG sem 2
            ('Principles of Ecology',          'PECG102', dept_Zoology, 2,  'PG', 30),  # ← PG sem 2
            ('Mendelian Genetics',             'MG301',   dept_Zoology, 2,  'PG', 25),  # ← PG sem 2
            ('Comparative Physiology',         'COM302',  dept_Zoology, 2,  'PG', 30),  # ← PG sem 2
            ('Digital Electronics',            'DE201',   dept_Physics, 2,  'UG', 40),
            ('Signal Processing',              'SP202',   dept_Physics, 2,  'UG', 35),
            ('VLSI Design',                    'VL101',   dept_Physics, 1,  'PG', 30),
            ('Embedded Systems',               'ES102',   dept_Physics, 1,  'PG', 30),
        ]
        subjects = {}
        for name, code, dept, sem, pt, tc in subject_rows:
            s = Subject(department_id=dept.id, name=name, code=code,
                        semester=sem, program_type=pt, total_classes=tc)
            db.session.add(s)
            subjects[code] = s
        db.session.flush()

        t1_IT = teachers['uzmahamid.IT@spcollege.edu'][1]
        t2_IT = teachers['kursheed.IT@spcollege.edu'][1]
        t1_Zg = teachers['feroz.zg@spcollege.edu'][1]
        t2_Zg = teachers['anis.zg@spcollege.edu'][1]
        t1_Py = teachers['muzamil.py@spcollege.edu'][1]
        t2_Py = teachers['riyaz.py@spcollege.edu'][1]

        t1_IT.subjects.append(subjects['DSA301'])
        t1_IT.subjects.append(subjects['OS302'])
        t2_IT.subjects.append(subjects['DBMS501'])
        t2_IT.subjects.append(subjects['ML502'])
        t1_Zg.subjects.append(subjects['NCC101'])
        t1_Zg.subjects.append(subjects['PECG102'])
        t2_Zg.subjects.append(subjects['MG301'])
        t2_Zg.subjects.append(subjects['COM302'])
        t1_Py.subjects.append(subjects['DE201'])
        t1_Py.subjects.append(subjects['SP202'])
        t2_Py.subjects.append(subjects['VL101'])
        t2_Py.subjects.append(subjects['ES102'])
        db.session.flush()
        print(f'  ✅ Subjects:    12 created and assigned to teachers')

        # ── STUDENTS ───────────────────────────────────────────────
        #
        # Every student's (department, semester, program_type) MUST
        # match at least one subject row above, or their dashboard
        # will show no subjects.
        #
        student_rows = [
            # email,                  first,      last,       dept,         roll,        year,      pt,   sem, att%
            # IT UG Sem 3 — matches DSA301, OS302
            ('muzamil@spcollege.edu',  'Muzamil',  'Gulzar',   dept_IT,  'IT2022001', '2022-23', 'UG', 3, 0.85),
            ('ajamul@spcollege.edu',   'Ajamul',   'Peer',     dept_IT,  'IT2022002', '2022-23', 'UG', 3, 0.58),
            ('baaqir@spcollege.edu',   'Baaqir',   'Mehmood',  dept_IT,  'IT2022003', '2022-23', 'UG', 3, 0.76),
            ('sammy@spcollege.edu',    'Syed',     'Samiullah',dept_IT,  'IT2022004', '2022-23', 'UG', 3, 0.92),
            # IT UG Sem 5 — matches DBMS501, ML502
            ('umar@spcollege.edu',     'Umar',     'Rashid',   dept_IT,  'IT2020005', '2020-21', 'UG', 5, 0.80),
            ('muied@spcollege.edu',    'Muied',    'Riyaz',    dept_IT,  'IT2020006', '2020-21', 'UG', 5, 0.65),
            # Zoology PG Sem 2 — matches NCC101, PECG102, MG301, COM302
            ('mehran@spcollege.edu',   'Mehran',   'Hassan',   dept_Zoology, 'ZG2023007', '2023-24', 'PG', 2, 0.88),
            ('amir@spcollege.edu',     'Syed',     'Aamir',    dept_Zoology, 'ZG2023008', '2023-24', 'PG', 2, 0.72),
            ('ifra@spcollege.edu',     'Ms',       'Ifra',     dept_Zoology, 'ZG2023009', '2023-24', 'PG', 2, 0.55),
            # Zoology PG Sem 4 (no subjects seeded for sem 4 — they are shown as no subjects)
            ('kavya@spcollege.edu',    'Kavya',    'Iyer',     dept_Zoology, 'ZG2022010', '2022-23', 'PG', 4, 0.91),
            ('tawseef@spcollege.edu',  'Tawseef',  'Kumar',    dept_Zoology, 'ZG2022011', '2022-23', 'PG', 4, 0.79),
            # Physics UG Sem 2 — matches DE201, SP202
            ('mehnoor@spcollege.edu',  'Ms',       'Mehnoor',  dept_Physics, 'PY2023012', '2023-24', 'UG', 2, 0.83),
            ('adil@spcollege.edu',     'Adil',     'Reshi',    dept_Physics, 'PY2023013', '2023-24', 'UG', 2, 0.61),
            ('altaf@spcollege.edu',    'Altaf',    'Bhat',     dept_Physics, 'PY2023014', '2023-24', 'UG', 2, 0.78),
            # Physics PG Sem 1 — matches VL101, ES102
            ('showkat@spcollege.edu',  'Showkat',  'Lone',     dept_Physics, 'PY2023015', '2023-24', 'PG', 1, 0.90),
            ('mehnaz@spcollege.edu',   'Mehnaz',   'Gul',      dept_Physics, 'PY2023016', '2023-24', 'PG', 1, 0.68),
            # IT UG Sem 6 — graduation eligible
            ('hashim@spcollege.edu',   'Hashim',   'Kakroo',   dept_IT,  'IT2019017', '2019-20', 'UG', 6, 0.88),
            ('nasir@spcollege.edu',    'Nasir',    'Nazir',    dept_IT,  'IT2019018', '2019-20', 'UG', 6, 0.82),
            # IT UG Sem 8 — already graduated
            ('asif@spcollege.edu',     'Asif',     'Mir',      dept_IT,  'IT2018019', '2018-19', 'UG', 8, 0.79),
            ('fasil@spcollege.edu',    'Fasil',    'Shabir',   dept_IT,  'IT2018020', '2018-19', 'UG', 8, 0.84),
        ]

        student_objects = {}
        for (email, fn, ln, dept, roll, year, pt, sem, _pct) in student_rows:
            u = make_user(email, fn, ln, Role.STUDENT)
            s = Student(user_id=u.id, department_id=dept.id,
                        roll_number=roll, admission_year=year,
                        program_type=pt, semester=sem)
            db.session.add(s)
            student_objects[roll] = (u, s)
        db.session.flush()

        for roll in ['IT2018019', 'IT2018020']:
            u, s = student_objects[roll]
            s.is_graduated        = True
            s.graduation_semester = 8
            s.graduation_year     = '2022'
            s.graduation_reason   = 'Completed full 8-semester BSc programme.'
            s.graduated_by_id     = hod_IT.id
            u.is_active           = False
        db.session.flush()
        print(f'  ✅ Students:    20 created (2 graduated, 2 eligible for graduation)')

        # ── ATTENDANCE ─────────────────────────────────────────────
        today = date.today()
        att_records = 0

        subject_teacher_map = {
            'DSA301': t1_IT,  'OS302':   t1_IT,
            'DBMS501': t2_IT, 'ML502':   t2_IT,
            'NCC101': t1_Zg,  'PECG102': t1_Zg,
            'MG301':  t2_Zg,  'COM302':  t2_Zg,
            'DE201':  t1_Py,  'SP202':   t1_Py,
            'VL101':  t2_Py,  'ES102':   t2_Py,
        }

        att_data = [
            ('DSA301',  [('IT2022001',0.85),('IT2022002',0.58),('IT2022003',0.76),('IT2022004',0.92)]),
            ('OS302',   [('IT2022001',0.88),('IT2022002',0.62),('IT2022003',0.74),('IT2022004',0.90)]),
            ('DBMS501', [('IT2020005',0.80),('IT2020006',0.65)]),
            ('ML502',   [('IT2020005',0.78),('IT2020006',0.70)]),
            ('NCC101',  [('ZG2023007',0.88),('ZG2023008',0.72),('ZG2023009',0.55)]),
            ('PECG102', [('ZG2023007',0.90),('ZG2023008',0.75),('ZG2023009',0.58)]),
            ('MG301',   [('ZG2023007',0.85),('ZG2023008',0.78),('ZG2023009',0.60)]),
            ('COM302',  [('ZG2023007',0.82),('ZG2023008',0.70),('ZG2023009',0.65)]),
            ('DE201',   [('PY2023012',0.83),('PY2023013',0.61),('PY2023014',0.78)]),
            ('SP202',   [('PY2023012',0.80),('PY2023013',0.65),('PY2023014',0.82)]),
            ('VL101',   [('PY2023015',0.90),('PY2023016',0.68)]),
            ('ES102',   [('PY2023015',0.88),('PY2023016',0.70)]),
        ]

        class_days = []
        d = today - timedelta(days=1)
        while len(class_days) < 20:
            if d.weekday() < 5:
                class_days.append(d)
            d -= timedelta(days=1)
        class_days.reverse()

        for subj_code, student_rolls in att_data:
            subj    = subjects[subj_code]
            teacher = subject_teacher_map[subj_code]
            for class_date in class_days:
                for roll, target_pct in student_rolls:
                    if roll not in student_objects:
                        continue
                    _, stu = student_objects[roll]
                    rand = random.random()
                    if rand < target_pct:
                        status = 'present'
                    elif rand < target_pct + 0.08:
                        status = 'leave'
                    elif rand < target_pct + 0.12:
                        status = 'event'
                    else:
                        status = 'absent'
                    db.session.add(Attendance(
                        student_id=stu.id, subject_id=subj.id,
                        marked_by_id=teacher.id, date=class_date,
                        status=status, semester=stu.semester,
                    ))
                    att_records += 1

        db.session.flush()
        print(f'  ✅ Attendance:  {att_records} records across 20 class days')

        # ── NOTIFICATIONS ──────────────────────────────────────────
        for roll, subj_code, pct in [
            ('IT2022002',  'DSA301',  58.0),
            ('ZG2023009',  'NCC101',  55.0),
            ('ZG2023009',  'PECG102', 58.0),
        ]:
            if roll not in student_objects:
                continue
            stu_u, stu = student_objects[roll]
            db.session.add(Notification(
                user_id=stu_u.id, type='danger',
                title=f'Low Attendance Alert — {subj_code}',
                message=(f'Your attendance in {subjects[subj_code].name} '
                         f'has dropped to {pct}%. Minimum required is 75%.'),
                target_type='system',
            ))

        for hod_u_obj, dept_obj in [
            (hod_IT_u, dept_IT), (hod_Zoology_u, dept_Zoology), (hod_Py_u, dept_Physics)
        ]:
            db.session.add(Notification(
                user_id=hod_u_obj.id, type='success',
                title='Welcome as HOD',
                message=(f'You have been appointed as HOD of {dept_obj.name}. '
                         f'You can manage teachers, students, subjects, and attendance.'),
                target_type='system',
            ))

        db.session.add(Notification(
            user_id=hod_IT_u.id, type='info',
            title='2 Students Ready to Graduate',
            message=('Students Hashim (IT2019017) and Nasir (IT2019018) '
                     'are at Semester 6 and eligible for graduation.'),
            target_type='system',
        ))

        db.session.commit()
        print(f'  ✅ Notifications: seeded')

        # ── PRINT SUMMARY ──────────────────────────────────────────
        print()
        print('═' * 62)
        print('  SEED COMPLETE — Login Credentials (password: College@123)')
        print('═' * 62)
        accounts = [
            ('Principal',           'principal@spcollege.edu',    '/principal/dashboard'),
            ('HOD (IT)',             'hod.IT@spcollege.edu',       '/hod/dashboard'),
            ('HOD (Zoology)',        'hod.Zoology@spcollege.edu',  '/hod/dashboard'),
            ('HOD (Physics)',        'hod.Py@spcollege.edu',       '/hod/dashboard'),
            ('Teacher (IT)',         'uzmahamid.IT@spcollege.edu', '/teacher/dashboard'),
            ('Teacher (Physics)',    'riyaz.py@spcollege.edu',     '/teacher/dashboard'),
            ('Student (good att)',   'muzamil@spcollege.edu',      '/student/dashboard'),
            ('Student (LOW att)',    'ajamul@spcollege.edu',       '/student/dashboard'),
            ('Student (graduated)',  'asif@spcollege.edu',         'cannot login'),
        ]
        print()
        for role, email, route in accounts:
            print(f'  {role:25s}  {email:35s}  → {route}')
        print()
        print('  Run with:  python run.py')
        print('  Open:      http://localhost:5000')
        print('═' * 62)


if __name__ == '__main__':
    seed()
