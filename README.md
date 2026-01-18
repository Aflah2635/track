# Expense Tracker

A robust, production-ready web application for managing personal and shared finances. This system includes multi-account support, transaction tracking, budget management, and statement generation.

### ✨ Key Features

- **Smart Dashboard**: Real-time overview of balance, credit, debit, and debts.
- **Multi-Account Support**: Manage multiple bank accounts or wallets in one place.
- **Shared Accounts (RBAC)**: Share accounts with family or teams with granular permissions (Owner, Editor, Viewer).
- **Advanced Transactions**: Track Credit, Debit, Lend, and Borrow records with backdating support.
- **Statement Generation**: Download detailed PDF statements with date, category, and user filters.
- **Responsive Design**: Optimized for both desktop and mobile usage.

### 🛠 System & Admin

- **Role-Based Access Control (RBAC)**: Secure permission handling for resources.
- **Security**: Login activity tracking, forced logout, and session management.
- **Admin Controls**: Maintenance mode, Read-only mode, and User management.
- **Discord Integration**: Real-time audit logging to private channels and remote maintenance control via slash commands.

## 💻 Tech Stack

- **Backend**: Django 5.0+, Python
- **Database**: SQLite (Dev) / PostgreSQL (Prod ready)
- **Frontend**: HTML5, CSS3 (Modern Fintech Design System), JavaScript
- **Utilities**: `xhtml2pdf` (PDFs), `discord.py` (Bot), `whitenoise` (Static files)

## 📦 Installation

### Prerequisites

- Python 3.10+

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
    DISCORD_BOT_TOKEN=your-discord-bot-token
    DISCORD_GUILD_ID=your-server-id
    DISCORD_ADMIN_ROLE_ID=optional-admin-role-id
    ```

5.  **Discord Bot Setup (Optional)**
    To enable real-time system logging and remote maintenance control:
    - Create a Discord Application & Bot.
    - Enable "Message Content Intent" in the Discord Developer Portal.
    - Invite the bot to your server with `Administrator` or `Manage Channels` + `Send Messages` permissions.
    - Set the environment variables above.

    **Logging Channels**
    The bot automatically creates and routes logs to these private channels:
    - `#auth-logs`: Login, Logout, Failed attempts, Registration.
    - `#transaction-logs`: Transaction creation, updates, deletions, and statement downloads.
    - `#system-logs`: Maintenance mode toggles and system warnings.

    **Slash Commands**
    - `/maintenance on`: Enable maintenance mode.
    - `/maintenance off`: Disable maintenance mode.
    - `/maintenance status`: Check system status.

6.  **Run Migrations**

    ```bash
    python manage.py migrate
    ```

7.  **Create Superuser**

    ```bash
    python manage.py createsuperuser
    ```

8.  **Run Server**

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
