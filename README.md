# Digital-academic-monitoring-and-engagement-system

A full-stack application for managing and monitoring academic engagement, built with **FastAPI (backend)** and **Next.js (frontend)**, containerized using Docker.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Digital-academic-monitoring-and-engagement-system.git
cd Digital-academic-monitoring-and-engagement-system
```

---

## ⚙️ Prerequisites

Make sure you have the following installed:

* Docker
* Docker Compose

Check installation:

```bash
docker --version
docker compose version
```

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend/` directory:

```bash
touch backend/.env
```

Add the following:

```env
# Database Configuration
POSTGRES_USER=your_username
POSTGRES_PASSWORD=Your_password
POSTGRES_DB=your_database_name
DATABASE_URL=postgresql+asyncpg://your_username:Your_password@localhost:5432/your_database_name
```

---

## 🐳 Running the Application with Docker

### 1. Build and Start Containers

From the root directory:

```bash
docker compose up --build
```

---

### 2. Access the Services

* Backend API: http://localhost:8000
* Frontend App: http://localhost:3030
* API Docs (Swagger): http://localhost:8000/docs

---
## 📁 Project Structure

```bash
.
├── backend/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── services/
│   ├── app.py
│   ├── database.py
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── public/
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## 🛑 Stopping the Application

```bash
docker compose down
```

---

## 🔧 Development Notes

* Backend uses **FastAPI** with async SQLAlchemy
* Frontend uses **Next.js**
* Database is **PostgreSQL**
* Containers are orchestrated using Docker Compose

---

## 🚀 Future Improvements

* Authentication (JWT / Keycloak)
* Role-based access control
* CI/CD pipeline
* Production deployment setup

---

## 👨‍💻 Author

Anele

---
