# Perimeter SaaS Platform

Web-based SaaS platform for Perimeter AI Security Gateway management.

## Features

- 🔐 User authentication (OAuth + Email)
- 📊 Usage dashboard with real-time metrics
- 🔑 API key management
- 💳 Stripe billing integration
- 👥 Team management
- 📈 Analytics and reporting
- ⚙️ Settings and configuration

## Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - Component library
- **Recharts** - Data visualization
- **React Query** - Data fetching and caching

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM for database
- **Clerk** - Authentication provider
- **Stripe** - Payment processing
- **PostgreSQL** - Primary database
- **Redis** - Session and cache storage

## Quick Start

### Development Setup

```bash
# Install dependencies
cd saas/frontend && npm install
cd ../backend && pip install -r requirements.txt

# Start services
docker-compose -f saas/docker-compose.yml up -d

# Start frontend
cd saas/frontend && npm run dev

# Start backend
cd saas/backend && uvicorn main:app --reload
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Directory Structure

```
saas/
├── frontend/              # Next.js application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   ├── lib/             # Utilities and configs
│   └── styles/          # Global styles
├── backend/             # FastAPI application
│   ├── routes/          # API endpoints
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   └── main.py         # Application entry
└── database/           # Database migrations
```
