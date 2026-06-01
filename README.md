# 🚀 SaaS Support Ticket Management System

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-black.svg?logo=flask)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red.svg)
![Pytest](https://img.shields.io/badge/Pytest-Passing-brightgreen.svg)

SaaS Support Ticket Management System is a modern, responsive, and highly interactive IT Support System. It reimagines the traditional enterprise support desk into a visually stunning, Glassmorphism-powered web application backed by a robust, production-ready Python architecture.

## ✨ Features

### 🎨 Elite UI/UX & Gamification
* **Deep Space Glassmorphism**: A stunning, hardware-accelerated animated gradient background overlaid with translucent glass cards.
* **Bento Grid Layouts**: Modern, responsive, asymmetrical dashboard layouts.
* **Web Audio API Haptics**: Every interaction (creating tickets, resolving them, or popping bubbles) is backed by custom software synthesizer sound effects (triangle-wave whooshes, C-Major polyphonic chimes).
* **Interactive Physics Canvas**: A background canvas filled with floating pastel bubbles that dynamically react to mouse velocity and bounding-box physics.

### 🧠 Advanced Backend Logic
* **Smart Auto-Triage NLP Engine**: An algorithmic interceptor that automatically analyzes user descriptions for critical keywords ("crash", "database", "down") and dynamically elevates the ticket's severity to `High`.
* **State Machine & Assignment**: A multi-step state machine (`Open` -> `In Progress` -> `Resolved`) that allows Admins to securely claim and work on tickets.
* **Event-Driven Audit Logging**: A relational `TicketHistory` tracking system that logs every action (who did what, when) and displays it chronologically on the ticket detail page.
* **Role-Based Access Control (RBAC)**: Secure separation between standard users (who can only see their own tickets) and Admins (who possess global visibility and modification rights).

### 🛡️ Production-Ready Security
* **Automated Pytest Suite**: 100% test passing rate covering NLP logic, authentication, and database integrity.
* **Strict CSRF Protection**: All state-modifying actions are protected behind strict `POST` form submissions.
* **Graceful Exception Handling**: All database transactions are wrapped in safe rollback protocols with custom, gamified 404 and 500 HTTP error pages.

## 🏗️ Architecture

The system utilizes a modular **Application Factory** pattern, ensuring scalability and clean separation of concerns.

* **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), and Vanilla JavaScript (Canvas Physics, Web Audio API).
* **Backend Framework**: Flask (Python) with Jinja2 Templating and reusable macros.
* **Database & ORM**: SQLite managed by Flask-SQLAlchemy for strict, object-oriented database schema definition.
* **Authentication**: Flask-Login and Werkzeug securely managing user sessions and salted password hashes.

## 📂 Folder Structure

```text
project1_ticket_system/
│
├── app/                        # Main Application Package
│   ├── __init__.py             # Application Factory & Error Handlers
│   ├── models.py               # SQLAlchemy Database Schemas
│   ├── utils.py                # NLP Auto-Triage Engine & Helpers
│   ├── routes/                 # Blueprint Controllers
│   │   ├── auth.py             # Login & Registration
│   │   ├── main.py             # Dashboard & Ticket Creation
│   │   └── tickets.py          # CRUD, Claiming, Resolving, History
│   ├── static/                 # Assets
│   │   ├── style.css           # Glassmorphism & Animations
│   │   └── script.js           # Physics Canvas & Audio Synths
│   └── templates/              # Jinja2 Views
│       ├── _macros.html        # Reusable UI Components
│       ├── base.html           # Main Layout Wrapper
│       ├── dashboard.html      # Bento Grid Ticket View
│       ├── ticket_detail.html  # Audit Log & Admin Controls
│       └── errors/             # Custom 404 & 500 Pages
│
├── tests/                      # Pytest Automated Test Suite
│   ├── conftest.py             # Fixtures & In-Memory DB Setup
│   ├── test_auth.py            # Security & Login Tests
│   ├── test_tickets.py         # CSRF & Permission Tests
│   └── test_utils.py           # Auto-Triage Algorithm Tests
│
├── instance/                   # Local Database Storage
│   └── tickets.db
│
├── run.py                      # Application Entry Point
└── requirements.txt            # Python Dependencies
```

## 🚀 Installation Guide

### Prerequisites
* Python 3.10+
* Git

### Local Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ticketSystem.git
   cd ticketSystem
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```
   *Note: The database (`tickets.db`) will automatically generate via SQLAlchemy upon initial boot.*

5. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 🕹️ Usage Guide
1. **First User = Admin**: The very first user account registered on the platform is automatically granted `Admin` privileges. All subsequent registrations are standard users.
2. **Create a Ticket**: Log in and create a ticket. Try typing *"the database crashed"* to see the Auto-Triage engine instantly elevate the ticket to `High` severity.
3. **Pop the Bubbles**: Move your mouse rapidly around the screen to watch the pastel bubbles react. Click them to trigger the bouncy audio synthesizer!
4. **Claim & Resolve**: Log in as the Admin to view the global dashboard. Click into a ticket, claim it (which assigns it to you and moves it to `In Progress`), and eventually resolve it. Watch the Audit Log populate chronologically!

## 🔮 Future Enhancements
* **WebSockets for Real-Time Updates**: Implementing Socket.IO so Admins can see new tickets appear on the dashboard in real-time without refreshing.
* **Email / Slack Integration**: Dispatching notifications to the support team when a `High` severity incident is auto-triaged by the NLP engine.
* **Ticket Attachments**: Allowing users to upload screenshots of their bugs/errors to an S3 bucket or local storage.
* **Advanced Analytics View**: Creating a dedicated `Chart.js` dashboard for Admins to visualize ticket resolution times and peak incident hours.
