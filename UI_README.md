# Healthcare Directory v2 - UI Setup Guide

## Overview

The new Flask-based UI provides a comprehensive web interface for managing the healthcare directory system. It replaces the basic review app with a full-featured API and web application.

## Architecture

### Backend (Flask API)
- **Main App**: `app.py` - Core Flask application with API blueprints
- **API Blueprints**:
  - `/api/providers` - Provider CRUD operations, search, filtering
  - `/api/dashboard` - System metrics, statistics, health checks
  - `/api/content` - AI content generation control
  - `/api/sync` - WordPress synchronization management
  - `/api/auth` - Authentication endpoints

### Key Features
1. **Provider Management**
   - Search and filter providers by status, city, specialty, proficiency
   - View/edit provider details
   - Bulk operations (approve/reject)
   - Pagination support

2. **Dashboard & Analytics**
   - Real-time system metrics
   - API usage and cost tracking
   - Content generation progress
   - WordPress sync status

3. **Content Generation**
   - Trigger AI content generation
   - Monitor batch processing
   - Preview and regenerate content
   - Dry-run mode for testing

4. **WordPress Sync**
   - Sync providers to WordPress
   - Monitor sync operations
   - Force updates
   - Error tracking

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment setup**:
   Add to your `config/.env`:
   ```
   # Admin password for UI
   ADMIN_PASSWORD=your_secure_password
   
   # Secret key for sessions
   SECRET_KEY=your_secret_key_here
   ```

3. **Run the application**:
   ```bash
   # Development mode
   python app.py
   
   # Production mode
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/logout` - Logout current user
- `GET /api/auth/check` - Check authentication status

### Providers
- `GET /api/providers` - List providers (paginated)
- `GET /api/providers/<id>` - Get single provider
- `PUT /api/providers/<id>` - Update provider
- `POST /api/providers/bulk-update` - Bulk status update
- `GET /api/providers/stats` - Provider statistics

### Dashboard
- `GET /api/dashboard/overview` - System overview
- `GET /api/dashboard/metrics/timeline` - Metrics over time
- `GET /api/dashboard/metrics/costs` - API cost breakdown
- `GET /api/dashboard/system/health` - System health check

### Content Generation
- `POST /api/content/generate` - Start content generation
- `GET /api/content/status` - Generation statistics
- `GET /api/content/preview/<id>` - Preview provider content
- `POST /api/content/regenerate/<id>` - Regenerate content
- `GET /api/content/batch-status` - Batch processing status

### WordPress Sync
- `POST /api/sync/sync` - Start sync operation
- `GET /api/sync/status` - Sync statistics
- `GET /api/sync/check/<id>` - Check provider sync status
- `GET /api/sync/test-connection` - Test WordPress connection
- `POST /api/sync/force-update/<id>` - Force update provider

## Frontend Development

To build a modern frontend, you can use React or Vue.js:

### React Setup (Recommended)
```bash
# Create React app
npx create-react-app healthcare-directory-ui
cd healthcare-directory-ui

# Install UI libraries
npm install axios react-router-dom antd recharts

# Configure API base URL
# In src/config.js:
export const API_BASE_URL = 'http://localhost:5000/api';
```

### Key Frontend Components to Build
1. **Login Page** - Authentication form
2. **Dashboard** - Overview with charts using Recharts
3. **Provider List** - DataTable with filters
4. **Provider Detail** - Edit form with all fields
5. **Content Generation** - Control panel with progress
6. **Sync Manager** - WordPress sync interface

## Security Notes

1. **Authentication**: Basic auth is implemented. For production, consider:
   - JWT tokens instead of sessions
   - Role-based access control
   - API rate limiting

2. **CORS**: Currently allows all origins. Restrict in production:
   ```python
   CORS(app, origins=['https://your-frontend-domain.com'])
   ```

3. **Environment Variables**: Never commit `.env` files

## Next Steps

1. **Build Frontend**: Create React/Vue app with the components listed above
2. **Add WebSockets**: For real-time progress updates during batch operations
3. **Implement Celery**: For background task processing
4. **Add Tests**: Unit and integration tests for API endpoints
5. **Deploy**: Use Docker for containerization and nginx for reverse proxy

## Migration from Old System

The new API is compatible with all existing scripts. The old `review_app.py` is still functional but deprecated in favor of the new comprehensive API.