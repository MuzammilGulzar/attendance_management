"""
DATABASE SEED SCRIPT
====================
Creates a complete, realistic dataset so the application can be
run and demonstrated immediately after setup.

Usage:
    python scripts/seed.py          # creates fresh seed data
    python scripts/seed.py --reset  # drops and recreates everything

What gets created:
    Departments    : 3  (CSE-UG, MBA-PG, ECE-both)
    Principal      : 1
    HODs           : 3  (one per department)
    Teachers       : 6  (2 per department)
    Students       : 20 (spread across semesters and programs)
    Subjects       : 12 (4 per department)
    Attendance     : ~300 records (30 days history)
    Notifications  : various welcome + low-attendance alerts

Login credentials (all passwords: College@123):
    principal@college.edu  → Principal
    hod.cse@college.edu    → HOD (CSE)
    hod.mba@college.edu    → HOD (MBA)
    hod.ece@college.edu    → HOD (ECE)
    teacher1.cse@college.edu / teacher2.cse@college.edu → Teachers
    student001@college.edu → Student (CSE UG Sem 3, attendance ~80%)
    student002@college.edu → Student (CSE UG Sem 3, attendance ~60% LOW)
    ... (see full list printed after seed)
"""

import sys
import os
import random
from datetime import date, timedelta

# Make sure we can import from the project root
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

        # Guard: don't re-seed if data already exists
        if not RESET and User.query.first():
            print('Database already has data. Use --reset to reseed.')
            return

        print('🌱 Seeding database...')
        random.seed(42)  # reproducible randomness

        # ══════════════════════════════════════════════════════════
        #  PRINCIPAL
        # ══════════════════════════════════════════════════════════
        principal = make_user('principal@college.edu',
                               'Dr. Rajiv', 'Mehta', Role.PRINCIPAL)
        print(f'  ✅ Principal:   {principal.email}')

        # ══════════════════════════════════════════════════════════
        #  DEPARTMENTS
        # ══════════════════════════════════════════════════════════
        dept_cse = Department(name='Computer Science & Engineering',
                              code='CSE', program_type='UG')
        dept_mba = Department(name='Master of Business Administration',
                              code='MBA', program_type='PG')
        dept_ece = Department(name='Electronics & Communication',
                              code='ECE', program_type='both')
        db.session.add_all([dept_cse, dept_mba, dept_ece])
        db.session.flush()
        print(f'  ✅ Departments: CSE (UG), MBA (PG), ECE (both)')

        # ══════════════════════════════════════════════════════════
        #  HODs
        # ══════════════════════════════════════════════════════════
        hod_cse_u = make_user('hod.cse@college.edu',
                               'Dr. Ayesha', 'Khan', Role.HOD)
        hod_mba_u = make_user('hod.mba@college.edu',
                               'Prof. Suresh', 'Rao', Role.HOD)
        hod_ece_u = make_user('hod.ece@college.edu',
                               'Dr. Priya', 'Nair', Role.HOD)

        hod_cse = Teacher(user_id=hod_cse_u.id, department_id=dept_cse.id,
                          employee_id='EMP001', is_hod=True)
        hod_mba = Teacher(user_id=hod_mba_u.id, department_id=dept_mba.id,
                          employee_id='EMP002', is_hod=True)
        hod_ece = Teacher(user_id=hod_ece_u.id, department_id=dept_ece.id,
                          employee_id='EMP003', is_hod=True)
        db.session.add_all([hod_cse, hod_mba, hod_ece])
        db.session.flush()
        print(f'  ✅ HODs:        hod.cse / hod.mba / hod.ece @college.edu')

        # ══════════════════════════════════════════════════════════
        #  TEACHERS  (2 per dept)
        # ══════════════════════════════════════════════════════════
        teacher_data = [
            ('teacher1.cse@college.edu','Prof. Arjun','Singh',  dept_cse,'EMP011'),
            ('teacher2.cse@college.edu','Prof. Meena','Pillai', dept_cse,'EMP012'),
            ('teacher1.mba@college.edu','Prof. Ravi', 'Kumar',  dept_mba,'EMP021'),
            ('teacher2.mba@college.edu','Prof. Sunita','Das',   dept_mba,'EMP022'),
            ('teacher1.ece@college.edu','Prof. Kiran','Bhat',   dept_ece,'EMP031'),
            ('teacher2.ece@college.edu','Prof. Lakshmi','Iyer', dept_ece,'EMP032'),
        ]
        teachers = {}
        for email, fn, ln, dept, emp_id in teacher_data:
            u = make_user(email, fn, ln, Role.TEACHER)
            t = Teacher(user_id=u.id, department_id=dept.id,
                        employee_id=emp_id, is_hod=False)
            db.session.add(t)
            teachers[email] = (u, t)
        db.session.flush()
        print(f'  ✅ Teachers:    6 created (2 per department)')

        # ══════════════════════════════════════════════════════════
        #  SUBJECTS
        # ══════════════════════════════════════════════════════════
        subject_data = [
            # CSE UG subjects
            ('Data Structures & Algorithms', 'DSA301', dept_cse, 3, 'UG', 45),
            ('Operating Systems',            'OS302',  dept_cse, 3, 'UG', 40),
            ('Database Management Systems',  'DBMS501',dept_cse, 5, 'UG', 40),
            ('Machine Learning',             'ML502',  dept_cse, 5, 'UG', 35),
            # MBA PG subjects
            ('Financial Management',         'FM101',  dept_mba, 1, 'PG', 30),
            ('Marketing Management',         'MM102',  dept_mba, 1, 'PG', 30),
            ('Strategic Management',         'SM301',  dept_mba, 3, 'PG', 25),
            ('Business Analytics',           'BA302',  dept_mba, 3, 'PG', 30),
            # ECE subjects (both UG and PG)
            ('Digital Electronics',          'DE201',  dept_ece, 2, 'UG', 40),
            ('Signal Processing',            'SP202',  dept_ece, 2, 'UG', 35),
            ('VLSI Design',                  'VL101',  dept_ece, 1, 'PG', 30),
            ('Embedded Systems',             'ES102',  dept_ece, 1, 'PG', 30),
        ]
        subjects = {}
        for name, code, dept, sem, pt, tc in subject_data:
            s = Subject(department_id=dept.id, name=name, code=code,
                        semester=sem, program_type=pt, total_classes=tc)
            db.session.add(s)
            subjects[code] = s
        db.session.flush()

        # Assign subjects to teachers
        t1_cse = teachers['teacher1.cse@college.edu'][1]
        t2_cse = teachers['teacher2.cse@college.edu'][1]
        t1_mba = teachers['teacher1.mba@college.edu'][1]
        t2_mba = teachers['teacher2.mba@college.edu'][1]
        t1_ece = teachers['teacher1.ece@college.edu'][1]
        t2_ece = teachers['teacher2.ece@college.edu'][1]

        t1_cse.subjects.append(subjects['DSA301'])
        t1_cse.subjects.append(subjects['OS302'])
        t2_cse.subjects.append(subjects['DBMS501'])
        t2_cse.subjects.append(subjects['ML502'])
        t1_mba.subjects.append(subjects['FM101'])
        t1_mba.subjects.append(subjects['MM102'])
        t2_mba.subjects.append(subjects['SM301'])
        t2_mba.subjects.append(subjects['BA302'])
        t1_ece.subjects.append(subjects['DE201'])
        t1_ece.subjects.append(subjects['SP202'])
        t2_ece.subjects.append(subjects['VL101'])
        t2_ece.subjects.append(subjects['ES102'])
        db.session.flush()
        print(f'  ✅ Subjects:    12 created and assigned to teachers')

        # ══════════════════════════════════════════════════════════
        #  STUDENTS
        # ══════════════════════════════════════════════════════════
        student_data = [
            # CSE UG Sem 3 (will have attendance marked for DSA & OS)
            ('student001@college.edu','Rahul',   'Sharma',  dept_cse, 'CSE2022001','2022-23','UG',3, 0.85),
            ('student002@college.edu','Priya',   'Patel',   dept_cse, 'CSE2022002','2022-23','UG',3, 0.58),  # LOW
            ('student003@college.edu','Vikram',  'Singh',   dept_cse, 'CSE2022003','2022-23','UG',3, 0.76),
            ('student004@college.edu','Ananya',  'Roy',     dept_cse, 'CSE2022004','2022-23','UG',3, 0.92),
            # CSE UG Sem 5
            ('student005@college.edu','Arjun',   'Menon',   dept_cse, 'CSE2020005','2020-21','UG',5, 0.80),
            ('student006@college.edu','Deepa',   'Nair',    dept_cse, 'CSE2020006','2020-21','UG',5, 0.65),
            # MBA PG Sem 1
            ('student007@college.edu','Rohit',   'Gupta',   dept_mba, 'MBA2023007','2023-24','PG',1, 0.88),
            ('student008@college.edu','Sneha',   'Verma',   dept_mba, 'MBA2023008','2023-24','PG',1, 0.72),
            ('student009@college.edu','Arun',    'Joshi',   dept_mba, 'MBA2023009','2023-24','PG',1, 0.55),  # LOW
            # MBA PG Sem 3
            ('student010@college.edu','Kavya',   'Iyer',    dept_mba, 'MBA2022010','2022-23','PG',3, 0.91),
            ('student011@college.edu','Sanjay',  'Kumar',   dept_mba, 'MBA2022011','2022-23','PG',3, 0.79),
            # ECE UG Sem 2
            ('student012@college.edu','Meena',   'Pillai',  dept_ece, 'ECE2023012','2023-24','UG',2, 0.83),
            ('student013@college.edu','Suresh',  'Das',     dept_ece, 'ECE2023013','2023-24','UG',2, 0.61),
            ('student014@college.edu','Lakshmi', 'Bhat',    dept_ece, 'ECE2023014','2023-24','UG',2, 0.78),
            # ECE PG Sem 1
            ('student015@college.edu','Kiran',   'Rao',     dept_ece, 'ECE2023015','2023-24','PG',1, 0.90),
            ('student016@college.edu','Pooja',   'Shah',    dept_ece, 'ECE2023016','2023-24','PG',1, 0.68),
            # CSE UG Sem 6 (graduation eligible!)
            ('student017@college.edu','Amit',    'Mehta',   dept_cse, 'CSE2019017','2019-20','UG',6, 0.88),
            ('student018@college.edu','Ritu',    'Chopra',  dept_cse, 'CSE2019018','2019-20','UG',6, 0.82),
            # CSE — already graduated
            ('student019@college.edu','Prakash', 'Reddy',   dept_cse, 'CSE2018019','2018-19','UG',8, 0.79),
            ('student020@college.edu','Divya',   'Pillai',  dept_cse, 'CSE2018020','2018-19','UG',8, 0.84),
        ]

        student_objects = {}
        for (email, fn, ln, dept, roll, year, pt, sem, _att_pct) in student_data:
            u = make_user(email, fn, ln, Role.STUDENT)
            s = Student(user_id=u.id, department_id=dept.id,
                        roll_number=roll, admission_year=year,
                        program_type=pt, semester=sem)
            db.session.add(s)
            student_objects[roll] = (u, s)
        db.session.flush()

        # Graduate the last two
        for roll in ['CSE2018019', 'CSE2018020']:
            u, s = student_objects[roll]
            s.is_graduated        = True
            s.graduation_semester = 8
            s.graduation_year     = '2022'
            s.graduation_reason   = 'Completed full 8-semester B.Tech programme.'
            s.graduated_by_id     = hod_cse.id
            u.is_active           = False
        db.session.flush()
        print(f'  ✅ Students:    20 created (2 graduated, 2 eligible for graduation)')

        # ══════════════════════════════════════════════════════════
        #  ATTENDANCE (30 days of realistic data)
        # ══════════════════════════════════════════════════════════
        today       = date.today()
        att_records = 0

        # Subject → teacher map for marking
        subject_teacher_map = {
            'DSA301': t1_cse, 'OS302': t1_cse,
            'DBMS501': t2_cse, 'ML502': t2_cse,
            'FM101': t1_mba, 'MM102': t1_mba,
            'SM301': t2_mba, 'BA302': t2_mba,
            'DE201': t1_ece, 'SP202': t1_ece,
            'VL101': t2_ece, 'ES102': t2_ece,
        }

        att_data = [
            # (subject_code, [student rolls], target_pct)
            ('DSA301',
             [('CSE2022001',0.85),('CSE2022002',0.58),('CSE2022003',0.76),('CSE2022004',0.92)]),
            ('OS302',
             [('CSE2022001',0.88),('CSE2022002',0.62),('CSE2022003',0.74),('CSE2022004',0.90)]),
            ('DBMS501',
             [('CSE2020005',0.80),('CSE2020006',0.65)]),
            ('ML502',
             [('CSE2020005',0.78),('CSE2020006',0.70)]),
            ('FM101',
             [('MBA2023007',0.88),('MBA2023008',0.72),('MBA2023009',0.55)]),
            ('MM102',
             [('MBA2023007',0.90),('MBA2023008',0.75),('MBA2023009',0.58)]),
            ('DE201',
             [('ECE2023012',0.83),('ECE2023013',0.61),('ECE2023014',0.78)]),
            ('SP202',
             [('ECE2023012',0.80),('ECE2023013',0.65),('ECE2023014',0.82)]),
            ('VL101',
             [('ECE2023015',0.90),('ECE2023016',0.68)]),
            ('ES102',
             [('ECE2023015',0.88),('ECE2023016',0.70)]),
        ]

        # Generate 20 class days (weekdays only, going back from today)
        class_days = []
        d = today - timedelta(days=1)
        while len(class_days) < 20:
            if d.weekday() < 5:   # Mon–Fri only
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
                    # Decide status based on target attendance %
                    rand = random.random()
                    if rand < target_pct:
                        status = 'present'
                    elif rand < target_pct + 0.08:
                        status = 'leave'    # ~8% chance of authorised leave
                    elif rand < target_pct + 0.12:
                        status = 'event'    # ~4% chance of event
                    else:
                        status = 'absent'

                    db.session.add(Attendance(
                        student_id   = stu.id,
                        subject_id   = subj.id,
                        marked_by_id = teacher.id,
                        date         = class_date,
                        status       = status,
                        semester     = stu.semester,
                    ))
                    att_records += 1

        db.session.flush()
        print(f'  ✅ Attendance:  {att_records} records across 20 class days')

        # ══════════════════════════════════════════════════════════
        #  NOTIFICATIONS
        # ══════════════════════════════════════════════════════════
        # Low-attendance alerts for students below 75%
        low_att_students = [
            ('CSE2022002', 'DSA301', 58.0),
            ('MBA2023009', 'FM101',  55.0),
            ('MBA2023009', 'MM102',  58.0),
        ]
        for roll, subj_code, pct in low_att_students:
            if roll not in student_objects:
                continue
            stu_u, stu = student_objects[roll]
            subj = subjects[subj_code]
            db.session.add(Notification(
                user_id = stu_u.id,
                type    = 'danger',
                title   = f'Low Attendance Alert — {subj_code}',
                message = (
                    f'Your attendance in {subj.name} has dropped to {pct}%. '
                    f'Minimum required is 75%. Please attend classes regularly.'
                ),
                target_type = 'system',
            ))

        # Welcome notifications for HODs
        for hod_u_obj, dept_obj in [
            (hod_cse_u, dept_cse),
            (hod_mba_u, dept_mba),
            (hod_ece_u, dept_ece),
        ]:
            db.session.add(Notification(
                user_id     = hod_u_obj.id,
                type        = 'success',
                title       = 'Welcome as HOD',
                message     = (
                    f'You have been appointed as HOD of {dept_obj.name}. '
                    f'You can manage teachers, students, subjects, and attendance.'
                ),
                target_type = 'system',
            ))

        # Graduation-eligible alert for HOD
        db.session.add(Notification(
            user_id     = hod_cse_u.id,
            type        = 'info',
            title       = '2 Students Ready to Graduate',
            message     = (
                'Students Amit Mehta (CSE2019017) and Ritu Chopra (CSE2019018) '
                'are at Semester 6 and eligible for graduation. '
                'Visit Graduation Management to proceed.'
            ),
            target_type = 'system',
        ))

        db.session.commit()
        print(f'  ✅ Notifications: seeded for low-att alerts and HOD welcome')

        # ══════════════════════════════════════════════════════════
        #  PRINT SUMMARY
        # ══════════════════════════════════════════════════════════
        print()
        print('═' * 60)
        print('  SEED COMPLETE — Login Credentials (password: College@123)')
        print('═' * 60)
        print()
        accounts = [
            ('Principal', 'principal@college.edu',   '→ /principal/dashboard'),
            ('HOD (CSE)', 'hod.cse@college.edu',     '→ /hod/dashboard'),
            ('HOD (MBA)', 'hod.mba@college.edu',     '→ /hod/dashboard'),
            ('HOD (ECE)', 'hod.ece@college.edu',     '→ /hod/dashboard'),
            ('Teacher',   'teacher1.cse@college.edu','→ /teacher/dashboard'),
            ('Teacher',   'teacher2.cse@college.edu','→ /teacher/dashboard'),
            ('Student (good att)',  'student001@college.edu', '→ /student/dashboard'),
            ('Student (LOW att)',   'student002@college.edu', '→ /student/dashboard'),
            ('Student (graduated)', 'student019@college.edu', '→ cannot login'),
        ]
        for role, email, route in accounts:
            print(f'  {role:25s}  {email:35s}  {route}')
        print()
        print(f'  Run with:  python run.py')
        print(f'  Open:      http://localhost:5000')
        print('═' * 60)


if __name__ == '__main__':
    seed()
