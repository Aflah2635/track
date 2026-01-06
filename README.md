# Expense Tracker with AI Assistant

A robust, production-ready web application for managing personal and shared finances. This system includes multi-account support, transaction tracking, budget management, PDF statement generation, and an embedded **AI Help Chatbot** powered by Google Gemini.

## 🚀 Features

### Core Functionality
- **Multi-Account Management**: Create and manage multiple accounts (Personal, Business, Shared).
- **Transactions**: Record Credits, Debits, Lending, and Borrowing.
- **Budget Tracking**: Set monthly budgets per category and get notified when you exceed them.
- **Account Sharing**: Share accounts with other users with granular permissions (Owner, Editor, Viewer).
- **Statements**: Generate and download PDF account statements with custom date ranges.
- **Notifications**: Real-time system alerts for budget limits and account activities.

### 🤖 AI Help Assistant
- **In-App Chatbot**: Integrated help assistant powered by Google Gemini.
- **Context-Aware**: Understands app features and workflows.
- **Safe & Secure**: Assistive only (read-only), with strict privacy guardrails.
- **Capabilities**: Explains features, guides users ("How do I..."), and clarifies terminology.

### 🛠 System & Admin
- **Role-Based Access Control (RBAC)**: Secure permission handling for resources.
- **Security**: Login activity tracking, forced logout, and session management.
- **Admin Controls**: Maintenance mode, Read-only mode, and User management.
- **Discord Integration**: Maintenance bot for remote system management.

## 💻 Tech Stack

- **Backend**: Django 5.0+, Python
- **Database**: SQLite (Dev) / PostgreSQL (Prod ready)
- **AI**: Google Gemini API
- **Frontend**: HTML5, CSS3 (Modern Fintech Design System), JavaScript
- **Utilities**: `xhtml2pdf` (PDFs), `discord.py` (Bot), `whitenoise` (Static files)

## 📦 Installation

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Steps

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd track
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `.env` file in the root directory:
    ```ini
    DEBUG=True
    SECRET_KEY=your-secret-key-here
    GEMINI_API_KEY=your-gemini-api-key
    DISCORD_BOT_TOKEN=optional-discord-token
    ```

5.  **Run Migrations**
    ```bash
    python manage.py migrate
    ```

6.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run Server**
    ```bash
    python manage.py runserver
    ```

    Access the app at `http://127.0.0.1:8000/`

## 🧪 Running Tests

Run the full test suite to ensure system integrity:

```bash
python manage.py test
```

## 📱 Mobile Responsiveness

The application features a fully responsive design:
- **Desktop**: Full data tables and expanded dashboards.
- **Mobile**: Simplified card-based views for transactions and stacked navigation.

## 📄 License

[MIT License](LICENSE)
