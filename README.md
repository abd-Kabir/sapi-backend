# SAPI Backend

A robust Django/DRF backend API for the SAPI project - a content monetization and creator support platform.

## 🚀 Features

- **User Authentication & Authorization**: Complete user management system with JWT authentication
- **Content Management**: Post creation, management, and moderation
- **Chat System**: Real-time messaging with WebSocket support
- **File Management**: Secure file uploads and storage with MinIO
- **Payment Integration**: Multi-bank payment processing and donation system
- **Notification System**: Real-time notifications and distribution
- **Admin Panel**: Comprehensive admin interface for platform management

## 🛠 Tech Stack

- **Framework**: Django 5.2
- **API**: Django REST Framework (DRF) 3.16.0
- **Database**: PostgreSQL
- **File Storage**: MinIO
- **Authentication**: JWT
- **Real-time**: Django Channels (WebSocket)
- **Payment**: Multi-bank integration
- **Deployment**: Docker & Docker Compose

## 📋 Prerequisites

- Python 3.13
- PostgreSQL 15
- MinIO Server
- Docker & Docker Compose (for production)
- Ubuntu Server (for deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sapi-backend
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Run local development**
   ```bash
   python manage.py runserver
   ```

### Production Deployment

For production deployment on Ubuntu server:

```bash
# Restart the application
make restart
```

## 📁 Project Structure

```
sapi-backend/
├── apps/                    # Django applications
│   ├── authentication/      # User auth & management
│   ├── chat/               # Real-time chat system
│   ├── content/            # Content management
│   ├── files/              # File upload & storage
│   └── integrations/       # External service integrations
├── config/                 # Django settings & configuration
├── media/                  # User uploaded files
├── static/                 # Static files
├── startup/                # Startup configuration
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Docker image definition
├── Makefile               # Build & deployment commands
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=

# MinIO
MINIO_URL=http://minio:9000
MINIO_USERNAME=minio_username
MINIO_PASSWORD=minio_password
REDIS_URL=redis://redis:6379/0

# SMS Service
SMS_BASE_URL=https://notify.eskiz.uz
SMS_USERNAME=
SMS_PASSWORD=

# FireBase
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_PROJECT_BUCKET=
FIREBASE_SENDER_ID=
FIREBASE_APP_ID=
FIREBASE_MEASUREMENT_ID=

# Multi-bank Integration, your Multibank credentials
MULTIBANK_PROD_BASE_URL=
MULTIBANK_PROD_APPLICATION_ID=
MULTIBANK_PROD_MERCHANT_ID=
MULTIBANK_PROD_STORE_ID=
MULTIBANK_PROD_SECRET=

MULTIBANK_DEV_BASE_URL=
MULTIBANK_DEV_APPLICATION_ID=
MULTIBANK_DEV_MERCHANT_ID=
MULTIBANK_DEV_STORE_ID=
MULTIBANK_DEV_SECRET=

```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

[//]: # (## 📄 License)

[//]: # ()
[//]: # (This project is licensed under the MIT License - see the [LICENSE]&#40;LICENSE&#41; file for details.)

---

**Built with ❤️ SAPI Team**
