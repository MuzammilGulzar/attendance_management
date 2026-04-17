# 📚 Attendance Management System

A web-based **Attendance Management System** built using **Python (Flask)** and **HTML/CSS**, designed to streamline attendance tracking and academic management in colleges.

---

## 🚀 Features

- 🔐 Role-based authentication system  
- 🏫 Department and semester management  
- 👨‍🏫 Teacher and subject allocation  
- 📊 Automatic attendance tracking & percentage calculation  
- 👨‍🎓 Student dashboard for attendance viewing  
- ✅ Structured and secure workflow  

---

## 🧑‍💼 User Roles & Functionalities

### 👑 Principal (Super Admin)
- Creates and manages **Departments**
- Appoints **HODs (Heads of Departments)**
- Full system control

---

### 🧑‍💻 HOD (Head of Department)
- Creates and manages **Teachers**
- Assigns **Subjects** to teachers
- Enrolls **Students**
- Assigns students to **Semesters**
- Allocates students to teachers

---

### 👨‍🏫 Teacher
- Views assigned subjects and students
- Marks attendance
- Updates attendance records

---

### 👨‍🎓 Student
- Views attendance records
- Tracks attendance percentage
- No permission to modify data

---

## 🔄 System Workflow
Principal

Creates Departments & HODs
↓
HOD
↓
Creates Teachers → Assigns Subjects
↓
Enrolls Students → Assigns Semester & Teacher
↓
Teacher
↓
Marks Attendance
↓
Student
↓
Views Attendance & Percentage

