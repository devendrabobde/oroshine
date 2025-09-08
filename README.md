# Oroshine

A Django web application with PostgreSQL database, email functionality, and Google Calendar integration through NoCode API.

## 🚀 Quick Start

Choose your preferred setup method:
- [Local Development](#local-development-setup) - For development and testing
- [Docker Deployment](#docker-deployment) - For simplified deployment

## 📋 Prerequisites

### For Local Development
- **Python 3.8+**
- **pip** (Python package installer)
- **PostgreSQL**
- **Git**

### For Docker Deployment
- **Docker & Docker Compose**
- **Git**

## 🛠️ Local Development Setup

### 1. Clone Repository
```bash
git clone git@github.com:devendrabobde/oroshine.git
cd oroshine
```

### 2. Create Virtual Environment

**Linux/macOS:**
```bash
python3 -m venv env
source env/bin/activate
```

**Windows:**
```cmd
python -m venv env
env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install django
pip install -r requirements.txt
pip install psycopg2-binary
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
PG_DB=oroshine
PG_USER=postgres
PG_PASSWORD=your_postgres_password
PG_HOST=localhost
PG_PORT=5432

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Calendar Integration
NOCODEAPI_CALENDAR_URL=https://v1.nocodeapi.com/your-username/calendar/your-api-key
```

### 5. Database Setup

**Linux/macOS:**
```bash
# Start PostgreSQL and create database
sudo -u postgres psql
```

**Windows:**
```cmd
# Open pgAdmin or use psql from PostgreSQL installation
psql -U postgres
```

**In PostgreSQL shell:**
```sql
CREATE DATABASE oroshine;
CREATE USER oroshine_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE oroshine TO oroshine_user;
\q
```

### 6. Django Setup
```bash
# Create Django app (if needed)
python manage.py startapp oroshine_webapp

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

🌐 **Access your application:**
- **Main App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

## 🐳 Docker Deployment

### 1. Environment Setup for Docker

Update your `.env` file for Docker (change database host):

```env
# Database Configuration (Docker)
PG_DB=oroshine
PG_USER=postgres
PG_PASSWORD=postgres
PG_HOST=db
PG_PORT=5432

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Calendar Integration
NOCODEAPI_CALENDAR_URL=https://v1.nocodeapi.com/your-username/calendar/your-api-key

#google Auth credential for socialauth-google  
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI= website-url/accounts/google/login/callback/ 
GOOGLE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GOOGLE_TOKEN_URI=https://oauth2.googleapis.com/token
GOOGLE_AUTH_PROVIDER_CERT_URL=your-google-auth-providerer-cert-url
GOOGLE_JAVASCRIPT_ORIGINS=your-website-url
```

### 2. Build and Run

**Linux/macOS:**
```bash
# Build and start services
sudo docker-compose up --build

# Run in background
sudo docker-compose up --build -d
```

**Windows:**
```cmd
# Build and start services
docker-compose up --build

# Run in background
docker-compose up --build -d
```

### 3. Docker Management

**Stop services:**
```bash
docker-compose down
```

**Complete cleanup:**
```bash
# Stop and remove everything
docker-compose down -v
docker system prune -af
```

**View logs:**
```bash
docker-compose logs web
docker-compose logs db
```

**Execute commands in container:**
```bash
docker-compose exec web python manage.py createsuperuser
```

## 📁 Project Structure

```
oroshine/
├── oroshine_app/          # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── oroshine_webapp/       # Django application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # App URLs
│   └── templates/        # HTML templates
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services
├── Dockerfile            # Docker image config
├── .env                  # Environment variables
└── README.md             # Documentation
```

## 🗓️ Google Calendar Integration Setup

### 1. Create NoCodeAPI Account
1. Visit [NoCodeAPI.com](https://nocodeapi.com)
2. Sign up or log in
3. Verify your email

### 2. Setup Google Calendar Integration
1. **Create API**: Dashboard → "Create New API" → "Google Calendar"
2. **Connect Google**: Sign in and grant calendar permissions
3. **Configure**: Set API name and permissions (Read/Write)
4. **Get Endpoint**: Copy your unique API URL

### 3. Update Environment
Add the API URL to your `.env` file:
```env
NOCODEAPI_CALENDAR_URL=https://v1.nocodeapi.com/your-username/calendar/your-api-key
```

### 4. Test Connection
```bash
curl -X GET "https://v1.nocodeapi.com/your-username/calendar/your-api-key/events"
```

## 📧 Email Configuration

### Gmail Setup
1. **Enable 2FA**: Go to Google Account → Security → 2-Step Verification
2. **Generate App Password**: Security → App passwords → Generate
3. **Update .env**: Use the generated app password (not your Gmail password)

## 🔧 Troubleshooting


# Google OAuth2 Configuration



### Database Issues
```bash
# Reset migrations
python manage.py migrate --fake-initial

# Check database connection
python manage.py dbshell
```

### Docker Issues
```bash
# Check running containers
docker ps

# Check logs for errors
docker-compose logs

# Restart services
docker-compose restart
```

### Common Solutions

| Issue | Solution |
|-------|----------|
| Port 8000 in use | Kill process: `lsof -ti:8000 \| xargs kill -9` (Linux/macOS) |
| Permission denied | Use `sudo` for Docker commands (Linux) |
| Database connection failed | Check PostgreSQL service status |
| Migration errors | Delete migration files and recreate |

## 🌟 Key Features

- **PostgreSQL Integration** - Robust database with Django ORM
- **Email System** - SMTP configuration for notifications
- **Calendar Sync** - Google Calendar integration via NoCode API
- **Admin Interface** - Django admin panel for management
- **Cross-Platform** - Works on Linux, macOS, and Windows
- **Docker Ready** - Containerized deployment option


## 📝 Development Notes

- Never commit `.env` files to version control
- Use strong secret keys in production
- Set `DEBUG=False` for production
- Regularly backup your database
- Monitor API usage limits for NoCode Calendar
