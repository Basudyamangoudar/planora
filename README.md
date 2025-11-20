# 🧠 Planora — Smart Study Planner

Planora is a smart and interactive study planning system that helps students organize their subjects, track progress, and plan their study sessions effectively. Built using **Django**, **Django REST Framework**, **MySQL**, and **React**, Planora makes study planning simple and productive.

---

## 📽️ Demo Video  
YouTube Link: *(Add your demo link here if available)*

---

## ✨ Features

### 📌 Study Planning  
- Create subjects and tasks  
- Update task status (Pending / In-progress / Completed)  
- Auto-generation of study plans (upcoming)

### 📈 Progress Tracking  
- Track daily & weekly progress  
- View completed tasks  
- Task history and analytics (future update)

### 🔐 User Module  
- User login and registration  
- Set personal study goals  

### 🧠 AI-based Features (Coming soon)  
- Smart daily study schedule  
- Intelligent task rescheduling  
- Personalized AI recommendations  

### 🔔 Notifications  
- Email reminders (future update)  
- Task deadline alerts  

---

## 🛠️ Tech Stack

### **Frontend**
- React  
- HTML, CSS, Bootstrap  
- Axios

### **Backend**
- Django  
- Django REST Framework  
- MySQL  
- Celery + Redis (planned)

### **Tools**
- VS Code  
- Git & GitHub  

---

## 📂 Project Structure

planora/
│── backend/
│ ├── manage.py
│ ├── planora_backend/
│ ├── apps/
│── frontend/
│ ├── src/
│ ├── public/
│── README.md


---

## ⚙️ How to Run Locally

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/Basudyamangoudar/planora.git
cd planora

cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

cd ../frontend
npm install
npm start




👨‍💻 Developer

Basavaraj Dyamangoudar
MCA Student | Full Stack Developer

GitHub: https://github.com/Basudyamangoudar

⭐ Support

If you like this project, please consider giving it a ⭐ Star on GitHub!

LinkedIn: (Add your LinkedIn link)
