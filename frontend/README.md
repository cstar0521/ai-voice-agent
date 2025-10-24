# AI Voice Loan Agent - Frontend Dashboard

React-based dashboard for monitoring and managing the AI Voice Loan Agent system.

## Features

- **Authentication**: JWT-based login with protected routes
- **Call Monitoring**: Real-time call tracking with auto-refresh
- **Lead Management**: Comprehensive lead tracking with filters and detail views
- **Analytics Dashboard**: KPI metrics and visualizations
- **Configuration Management**: Voice prompt and conversation flow editor

## Tech Stack

- React 18 with TypeScript
- Material-UI (MUI) for UI components
- React Router for navigation
- Axios for API communication
- Recharts for data visualization
- date-fns for date formatting

## Setup

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
npm install
```

### Environment Variables

Create a `.env` file in the frontend directory:

```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

### Development

```bash
npm start
```

The app will run on http://localhost:3000

### Build

```bash
npm run build
```

### Testing

```bash
npm test
```

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Layout.tsx      # Main layout with navigation
│   └── ProtectedRoute.tsx  # Route protection wrapper
├── contexts/           # React contexts
│   └── AuthContext.tsx # Authentication context
├── pages/              # Page components
│   ├── Login.tsx       # Login page
│   ├── Dashboard.tsx   # Main dashboard
│   ├── CallMonitoring.tsx  # Call monitoring page
│   ├── LeadManagement.tsx  # Lead list page
│   ├── LeadDetail.tsx  # Lead detail page
│   ├── Analytics.tsx   # Analytics dashboard
│   └── Configuration.tsx   # Configuration management
├── services/           # API services
│   └── api.ts          # API client
├── types/              # TypeScript types
│   └── index.ts        # Type definitions
├── App.tsx             # Main app component
└── index.tsx           # Entry point
```

## API Integration

The frontend communicates with the backend API at `/api/v1`. All API calls are handled through the `apiClient` service which includes:

- Automatic JWT token injection
- Error handling and 401 redirect
- Request/response interceptors

## Authentication

The app uses JWT tokens stored in localStorage. Protected routes automatically redirect to login if no valid token is present.

Default credentials (configure in backend):
- Username: admin
- Password: (set in backend)

## Features by Page

### Dashboard
- Overview of key metrics
- Quick navigation to all sections

### Call Monitoring
- Real-time call list
- Call status indicators
- Auto-refresh every 5 seconds
- Hangup active calls

### Lead Management
- Searchable lead list
- Filter by status and category
- Lead detail view with full information
- Call history per lead
- Update lead status
- Trigger handoff

### Analytics
- KPI cards (total calls, completion rate, handoff rate)
- Call volume over time chart
- Sentiment distribution pie chart
- Language usage bar chart

### Configuration
- Voice prompt editor for all languages (Hinglish, English, Telugu)
- Conversation flow visualizer
- Prompt testing interface

## Testing

Component tests are located in `__tests__` directories alongside components. Tests cover:

- Authentication flow
- Dashboard rendering
- Lead management functionality
- Protected route behavior

Run tests with:
```bash
npm test
```

## Docker Support

The frontend can be containerized using the provided Dockerfile in the project root.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
