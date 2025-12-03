# 🚚 Transport Company Database Application  
### 📘 Laboratory Work №10 — ORM + Tkinter GUI (SQLAlchemy)

This repository contains the completed Lab Work #10, which demonstrates:

✔ Object–Relational Mapping (ORM) using **SQLAlchemy**  
✔ A full **Tkinter GUI application** for managing transport company data  
✔ CRUD operations for all major entities  
✔ Clean project structure suitable for GitHub  

---

## 🎯 Purpose of the Project
The goal of the lab is to implement a database-driven application using:

- Python + SQLAlchemy ORM  
- SQLite database  
- Tkinter graphical user interface  
- Entities of a transport company (Client, Driver, Vehicle, Order, TripDetails, TripLog)

---

## 🏗 Project Structure

```
lab10/
│── gui.py             # Tkinter GUI (CRUD for all entities)
│── models.py          # SQLAlchemy ORM models + DB setup
│── transport.db       # SQLite database (auto-created)
└── README.md          # Documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Create a virtual environment  
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2️⃣ Install dependencies
```bash
pip install sqlalchemy
```

Tkinter is included with standard Python installations.

---

## ▶ Running the Application

Run the GUI:

```bash
python gui.py
```

A window appears with tabs for:

- **Clients**
- **Drivers**
- **Vehicles**
- **Orders**
- **Trips (TripDetails + TripLog)**

Each tab allows:

- Viewing records  
- Adding new entries  
- Editing entries  
- Deleting entries  

---

## 🧩 Database Schema (ORM Entities)

### Client
- id  
- client_type (company/person)  
- name  
- contacts  

### Driver
- id  
- full_name  
- license_number  
- phone  

### Vehicle
- id  
- reg_number  
- vehicle_type  
- capacity  
- description  

### Order
- client_id  
- route  
- departure_time  
- arrival_time  

### TripDetails
- order_id  
- driver_id  
- vehicle_id  
- status  
- cost  

### TripLog
- actual departure/arrival times  
- comment  

---

## 🖼 Screenshots (recommended for GitHub README)
📌 Add your own screenshots here after uploading them:

- Main application window  
- CRUD operations  
- Trips editing dialog  
- Database file generated  

---

## 🚀 Features

- Full CRUD support  
- ORM abstraction — no raw SQL  
- User-friendly GUI  
- Automatic database creation  
- Clean modular architecture  
- Easy to extend with new entities  

---

## 📄 License
You may distribute or modify this code freely for educational purposes.

---

## 🤝 Author
Laboratory work completed according to methodological instructions.  
Feel free to open issues or ask for improvements!

