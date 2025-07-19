# Healthcare Directory Frontend

A modern React TypeScript application with Ant Design for managing healthcare providers in Japan.

## Features

### 🏥 Provider Management
- **Comprehensive Provider List**: Paginated table with advanced filtering
- **Detailed Provider Profiles**: Edit all provider information including AI-generated content
- **Bulk Operations**: Approve, reject, or sync multiple providers at once
- **Real-time Status Updates**: Live updates of provider processing status

### 📊 Analytics Dashboard
- **System Overview**: Key metrics and performance indicators
- **Interactive Charts**: Provider distribution, proficiency scores, city breakdown
- **Content Generation Progress**: Track AI content completion rates
- **API Usage Monitoring**: Cost tracking and usage statistics

### 🤖 AI Content Generation
- **Batch Processing Control**: Start/stop AI content generation
- **Progress Monitoring**: Real-time tracking of content generation
- **Content Type Selection**: Generate specific types of content (descriptions, SEO, etc.)
- **Dry Run Mode**: Preview operations before execution

### 🔄 WordPress Sync
- **Sync Management**: Control synchronization with WordPress
- **Connection Testing**: Verify WordPress API connectivity
- **Operation History**: Track sync operations and errors
- **Batch Operations**: Sync multiple providers efficiently

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Backend API server running on port 5000

### Installation & Development
```bash
cd frontend
npm install
npm start
```
Open [http://localhost:3999](http://localhost:3999)

### Default Login
- Username: `admin`
- Password: Set via `ADMIN_PASSWORD` in backend configuration

### Production Build
```bash
npm run build
```

## Technology Stack

- **React 18** with TypeScript
- **Ant Design** for UI components
- **React Router** for navigation
- **Recharts** for data visualization
- **Axios** for API communication

## Configuration

Create `.env` file:
```bash
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
```

## Key Components

### Dashboard
Real-time system overview with provider statistics, content generation progress, and interactive charts.

### Provider List
Advanced DataTable with filtering, bulk operations, and detailed provider management.

### Content Generation
AI content processing control panel with batch operations and progress monitoring.

### WordPress Sync
WordPress synchronization management with connection testing and operation history.

## Available Scripts

### `npm start`
Runs the app in development mode at [http://localhost:3999](http://localhost:3999).

### `npm test`
Launches the test runner in interactive watch mode.

### `npm run build`
Builds the app for production to the `build` folder.

## Project Structure

```
src/
├── components/           # React components
│   ├── Dashboard/       # Analytics dashboard
│   ├── Providers/       # Provider management
│   ├── ContentGeneration/ # AI content controls
│   ├── Sync/           # WordPress sync
│   ├── Layout/         # App layout
│   └── Login.tsx       # Authentication
├── contexts/           # React contexts
├── config/            # Configuration
├── types/             # TypeScript types
├── utils/             # Utilities
└── App.tsx            # Main app component
```

## Development Guidelines

- Use TypeScript strict mode
- Follow Ant Design patterns
- Implement responsive design
- Add proper error handling
- Include loading states

## Browser Support
Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
