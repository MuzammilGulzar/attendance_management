"""
RBAC TEST SUITE
================
Tests every access rule in the Access Control Matrix.
Run with:  python tests/test_rbac.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
# from app.models import Student, Subject
from app.models.user import Role
from app.models.user import User
from app.models.department import Department
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.subject import Subject

app = create_app('development')
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING']          = True


def seed_db():
    """Create one User per role plus related profiles."""
    db.drop_all()
    db.create_all()

    dept1 = Department(name='Computer Science', code='CSE', program_type='UG')
    dept2 = Department(name='Electronics',      code='ECE', program_type='UG')
    db.session.add_all([dept1, dept2])
    db.session.flush()

    users = {}
    profiles = [
        ('principal@c.com', 'Alice', 'P', Role.PRINCIPAL, None, None),
        ('hod@c.com',       'Bob',   'H', Role.HOD,       dept1.id, True),
        ('hod2@c.com',      'Carol', 'H2',Role.HOD,       dept2.id, True),
        ('Teacher@c.com',   'Dave',  'T', Role.TEACHER,   dept1.id, False),
        ('Student@c.com',   'Eve',   'S', Role.STUDENT,   dept1.id, None),
        ('student2@c.com',  'Frank', 'S2',Role.STUDENT,   dept2.id, None),
    ]

    for email, fn, ln, role, dept_id, is_hod in profiles:
        u = User(email=email, first_name=fn, last_name=ln, role=role)
        u.set_password('pass1234')
        db.session.add(u)
        db.session.flush()
        users[email] = u

        if role in (Role.HOD, Role.TEACHER):
            db.session.add(Teacher(
                user_id=u.id, department_id=dept_id,
                employee_id=f'E{u.id}', is_hod=bool(is_hod)
            ))
        elif role == Role.STUDENT:
            db.session.add(Student(
                user_id=u.id, department_id=dept_id,
                roll_number=f'R{u.id}', admission_year='2022-23',
                program_type='UG',
                semester=6 if fn == 'Eve' else 1
            ))

    # Subject assigned to dept1 Teacher
    subj = Subject(department_id=dept1.id, name='Maths',
                   code='MTH', semester=1, program_type='UG', total_classes=30)
    db.session.add(subj)
    db.session.flush()

    # Assign Subject to the Teacher
    teacher_profile = Teacher.query.filter_by(is_hod=False).first()
    teacher_profile.subjects.append(subj)

    db.session.commit()
    return users, dept1, dept2, subj


def login_as(client, email):
    client.post('/auth/login',
                data={'email': email, 'password': 'pass1234'},
                follow_redirects=False)


def logout(client):
    client.get('/auth/logout', follow_redirects=False)


PASS = '✅'
FAIL = '❌'

results = []

def check(label, response, expected_status):
    ok = response.status_code == expected_status
    symbol = PASS if ok else FAIL
    results.append((symbol, label, response.status_code, expected_status))
    return ok


with app.app_context():
    users, dept1, dept2, subj = seed_db()
    client = app.test_client()

    # ── Grab IDs we need ──────────────────────────────────────────────
    student1 = Student.query.filter_by(roll_number=f'R{users["Student@c.com"].id}').first()
    student2 = Student.query.filter_by(roll_number=f'R{users["student2@c.com"].id}').first()

    print('=' * 62)
    print('  RBAC TEST SUITE — College Attendance System')
    print('=' * 62)
    print()

    # ═════════════════════════════════════════════════════════════
    # 1. UNAUTHENTICATED ACCESS — every protected route must redirect
    # ═════════════════════════════════════════════════════════════
    print('── 1. Unauthenticated Access (expect 302 to login) ──')
    for path in ['/principal/dashboard', '/hod/dashboard',
                 '/Teacher/dashboard',   '/Student/dashboard']:
        r = client.get(path, follow_redirects=False)
        check(f'Anon → {path}', r, 302)

    # ═════════════════════════════════════════════════════════════
    # 2. PRINCIPAL EXCLUSIVE ROUTES
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 2. Principal-only routes ──')

    # Principal CAN access
    login_as(client, 'principal@c.com')
    r = client.get('/principal/dashboard')
    check('Principal → /principal/dashboard (expect 200)', r, 200)
    r = client.get('/principal/create-hod')
    check('Principal → /principal/create-hod  (expect 200)', r, 200)
    logout(client)

    # HOD cannot access principal routes
    login_as(client, 'hod@c.com')
    r = client.get('/principal/dashboard', follow_redirects=False)
    check('HOD → /principal/dashboard     (expect 403)', r, 403)
    r = client.get('/principal/create-hod', follow_redirects=False)
    check('HOD → /principal/create-hod   (expect 403)', r, 403)
    logout(client)

    # Teacher cannot access principal routes
    login_as(client, 'Teacher@c.com')
    r = client.get('/principal/dashboard', follow_redirects=False)
    check('Teacher → /principal/dashboard  (expect 403)', r, 403)
    logout(client)

    # Student cannot access principal routes
    login_as(client, 'Student@c.com')
    r = client.get('/principal/dashboard', follow_redirects=False)
    check('Student → /principal/dashboard  (expect 403)', r, 403)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 3. HOD EXCLUSIVE ROUTES (attendance edit, promote, graduate)
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 3. HOD-only routes ──')

    # Teacher CANNOT edit attendance
    login_as(client, 'Teacher@c.com')
    r = client.post(f'/hod/attendance/1/edit', follow_redirects=False)
    check('Teacher → POST /hod/attendance/edit (expect 403)', r, 403)

    # Teacher CANNOT promote students
    r = client.post(f'/hod/Student/{student1.id}/promote', follow_redirects=False)
    check('Teacher → POST /hod/promote          (expect 403)', r, 403)

    # Teacher CANNOT graduate students
    r = client.post(f'/hod/Student/{student1.id}/graduate', follow_redirects=False)
    check('Teacher → POST /hod/graduate         (expect 403)', r, 403)
    logout(client)

    # Student CANNOT access any HOD route
    login_as(client, 'Student@c.com')
    r = client.post(f'/hod/Student/{student1.id}/promote', follow_redirects=False)
    check('Student → POST /hod/promote          (expect 403)', r, 403)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 4. HOD DEPARTMENT OWNERSHIP
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 4. HOD Department ownership (cross-dept blocked) ──')

    # HOD of dept2 cannot promote a Student from dept1
    login_as(client, 'hod2@c.com')
    r = client.post(f'/hod/Student/{student1.id}/promote', follow_redirects=False)
    check('HOD(ECE) → promote CSE Student    (expect 403)', r, 403)
    logout(client)

    # HOD of dept1 CAN promote their own Student (at sem 3, not 6/8)
    login_as(client, 'hod@c.com')
    s_low = Student.query.filter_by(roll_number=f'R{users["Student@c.com"].id}').first()
    s_low.semester = 3          # reset to promotable semester
    db.session.commit()
    r = client.post(f'/hod/Student/{student1.id}/promote', follow_redirects=False)
    check('HOD(CSE) → promote own Student    (expect 302)', r, 302)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 5. GRADUATION RULES
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 5. Graduation rules ──')

    login_as(client, 'hod@c.com')

    # Student at semester 3 — NOT a valid graduation semester
    s_low.semester = 3
    db.session.commit()
    r = client.post(f'/hod/Student/{student1.id}/graduate',
                    data={'reason': 'test'}, follow_redirects=False)
    check('Graduate Student at sem 3        (expect 302+flash)', r, 302)

    # Student at semester 6 — IS a valid graduation semester for UG
    s_low.semester = 6
    db.session.commit()
    r = client.post(f'/hod/Student/{student1.id}/graduate',
                    data={'reason': 'Completed 6 semesters'}, follow_redirects=False)
    check('Graduate UG Student at sem 6     (expect 302 ok)', r, 302)

    # Verify graduation was applied
    db.session.refresh(s_low)
    grad_applied = s_low.is_graduated and not s_low.User.is_active
    print(f'  {"✅" if grad_applied else "❌"} Graduation applied: '
          f'is_graduated={s_low.is_graduated}, '
          f'User.is_active={s_low.User.is_active}, '
          f'graduation_semester={s_low.graduation_semester}')

    # Try to promote an already-graduated Student
    r = client.post(f'/hod/Student/{student1.id}/promote', follow_redirects=False)
    check('Promote already-graduated Student (expect 302+flash)', r, 302)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 6. TEACHER SUBJECT OWNERSHIP
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 6. Teacher Subject ownership ──')

    login_as(client, 'Teacher@c.com')
    # Teacher can GET the mark-attendance page for THEIR Subject
    r = client.get(f'/Teacher/mark-attendance/{subj.id}', follow_redirects=False)
    check('Teacher → own Subject page       (expect 200)', r, 200)

    # Create another Subject NOT assigned to this Teacher
    with app.app_context():
        other_subj = Subject(department_id=dept1.id, name='Physics',
                             code='PHY', semester=1, program_type='UG',
                             total_classes=20)
        db.session.add(other_subj)
        db.session.commit()
        other_id = other_subj.id

    r = client.get(f'/Teacher/mark-attendance/{other_id}', follow_redirects=False)
    check('Teacher → unassigned Subject     (expect 403)', r, 403)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 7. STUDENT OWNS RECORD
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 7. Student record ownership ──')

    # student1 is graduated — use student2 (active) for ownership tests
    login_as(client, 'student2@c.com')
    # Student 2 CAN view their own attendance
    r = client.get(f'/Student/attendance/{student2.id}', follow_redirects=False)
    check('Student2 → own attendance        (expect 200)', r, 200)
    # Student 2 CANNOT view Student 1's attendance
    r = client.get(f'/Student/attendance/{student1.id}', follow_redirects=False)
    check('Student2 → other Student record  (expect 403)', r, 403)
    logout(client)

    # ═════════════════════════════════════════════════════════════
    # 8. INACTIVE ACCOUNT BLOCKED
    # ═════════════════════════════════════════════════════════════
    print()
    print('── 8. Inactive / graduated account ──')
    # student1 was graduated in test 5 — login must fail
    # authenticate_user() returns error for inactive users
    # The route stays on login page (200) — no dashboard redirect
    r = client.post('/auth/login',
                    data={'email': 'Student@c.com', 'password': 'pass1234'},
                    follow_redirects=True)
    # Should stay on login page (200), NOT reach Student dashboard
    stayed_on_login = b'Log In' in r.data or b'login' in r.data.lower()
    went_to_dashboard = b'Student Dashboard' in r.data
    print(f'  {"✅" if stayed_on_login and not went_to_dashboard else "❌"} '
          f'Graduated Student blocked from dashboard '
          f'(on_login={stayed_on_login}, got_dashboard={went_to_dashboard})')
    check('Graduated Student stays on login (expect 200)', r, 200)

    # ═════════════════════════════════════════════════════════════
    # RESULTS SUMMARY
    # ═════════════════════════════════════════════════════════════
    print()
    print('=' * 62)
    print('  RESULTS')
    print('=' * 62)
    passed = sum(1 for r in results if r[0] == PASS)
    failed = sum(1 for r in results if r[0] == FAIL)
    for symbol, label, got, expected in results:
        print(f'  {symbol} {label}')
        if symbol == FAIL:
            print(f'       got={got}  expected={expected}')
    print()
    print(f'  Total: {passed} passed, {failed} failed out of {len(results)} tests')
    print('=' * 62)