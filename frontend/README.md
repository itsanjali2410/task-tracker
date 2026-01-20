# TripStars Task Management System - Frontend

## Architecture

Production-ready React frontend with modular structure:

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Layout.js          # Main layout with sidebar
│   │   └── ui/                # Shadcn UI components
│   ├── contexts/
│   │   └── AuthContext.js     # Authentication state
│   ├── pages/
│   │   ├── Login.js           # Login page
│   │   ├── Dashboard.js       # Dashboard with stats
│   │   ├── UserManagement.js  # User management (Admin)
│   │   ├── TaskList.js        # All tasks (Manager/Admin)
│   │   ├── MyTasks.js         # Team member tasks
│   │   └── TaskDetail.js      # Task details with comments
│   ├── App.js                 # Main app component
│   ├── App.css                # Custom styles
│   └── index.css              # Global styles
├── package.json
├── tailwind.config.js
└── .env.example
```

## Features

### Phase 1
- ✅ User authentication (email + password)
- ✅ JWT token management
- ✅ Role-based UI (Admin, Manager, Team Member)
- ✅ Dashboard with task statistics
- ✅ User management (Admin only)
- ✅ Task creation and assignment (Manager/Admin)
- ✅ Task status updates (Team members)
- ✅ Protected routes

### Phase 2 (Comments)
- ✅ Task detail page
- ✅ Add comments to tasks
- ✅ View all task comments
- ✅ Real-time comment updates
- ✅ Comment timestamps

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
yarn install
# or
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
# For production:
# REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

### 3. Run Development Server

```bash
yarn start
# or
npm start
```

App will be available at http://localhost:3000

### 4. Build for Production

```bash
yarn build
# or
npm run build
```

Built files will be in the `build/` directory.

## Pages & Routes

### Public Routes
- `/login` - Login page

### Protected Routes
- `/dashboard` - Dashboard (All roles)
- `/users` - User Management (Admin only)
- `/tasks` - All Tasks (Manager/Admin)
- `/tasks/:taskId` - Task Details with Comments (All roles)
- `/my-tasks` - My Tasks (Team Member)

## Components

### Layout
Main layout with:
- Dark sidebar navigation
- User profile section
- Role-based menu items
- Logout functionality

### AuthContext
Manages:
- User authentication state
- JWT token storage
- Login/logout functions
- User profile data

### Protected Routes
Route guard that:
- Checks authentication
- Validates user roles
- Redirects unauthorized users

## Styling

### Design System
- **Primary Color**: #0F4C81 (Deep Ocean Blue)
- **Secondary Color**: #F5A623 (Sunset Orange)
- **Background**: #F8FAFC (Light Gray)
- **Fonts**: Manrope (headings), Inter (body)

### Tailwind CSS
Custom configuration in `tailwind.config.js` with:
- Custom color palette
- Typography settings
- Responsive breakpoints
- Custom utilities

## API Integration

All API calls use axios with:
- Base URL from environment variables
- JWT token in Authorization header
- Error handling with toast notifications

### Example API Call
```javascript
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// With authentication
const response = await axios.get(`${API}/tasks`);
// Token is automatically included via axios interceptor
```

## State Management

### Auth State
- Managed by `AuthContext`
- Stored in localStorage
- Auto-refresh on page reload

### Local Component State
- React hooks (useState, useEffect)
- Form data
- Loading states

## Deployment

### Vercel (Recommended)

1. Connect GitHub repository
2. Set environment variables:
   ```
   REACT_APP_BACKEND_URL=https://api.yourdomain.com
   ```
3. Deploy automatically on push

### Netlify

1. Connect repository
2. Build command: `yarn build`
3. Publish directory: `build`
4. Add environment variables

### AWS S3 + CloudFront

1. Build: `yarn build`
2. Upload `build/` to S3 bucket
3. Configure CloudFront distribution
4. Set environment variables during build

### Docker

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Testing

### Manual Testing
1. Login with seed users
2. Test role-based access
3. Create and assign tasks
4. Add comments
5. Update task status

### Seed Users
- Admin: admin@tripstars.com / Admin@123
- Manager: manager@tripstars.com / Manager@123
- Team Member: member@tripstars.com / Member@123

## Production Checklist

- [ ] Set correct `REACT_APP_BACKEND_URL`
- [ ] Enable HTTPS
- [ ] Configure CORS on backend
- [ ] Optimize images and assets
- [ ] Enable production build optimizations
- [ ] Setup error tracking (Sentry)
- [ ] Configure CDN for static assets
- [ ] Setup analytics (Google Analytics, etc.)
- [ ] Test on multiple browsers
- [ ] Mobile responsiveness check

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)
