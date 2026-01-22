import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LayoutDashboard, CheckSquare, Users, LogOut, Menu, X, TrendingUp, Shield } from 'lucide-react';
import { useState } from 'react';
import NotificationBell from './NotificationBell';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'manager', 'team_member'] },
    { path: '/tasks', icon: CheckSquare, label: 'All Tasks', roles: ['admin', 'manager'] },
    { path: '/my-tasks', icon: CheckSquare, label: 'My Tasks', roles: ['team_member'] },
    { path: '/users', icon: Users, label: 'User Management', roles: ['admin'] },
    { path: '/reports', icon: TrendingUp, label: 'Reports', roles: ['admin', 'manager'] },
  ];

  const filteredNavItems = navItems.filter(item => item.roles.includes(user?.role));

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-background-sidebar transform transition-transform duration-300 lg:translate-x-0 lg:static ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <span className="text-white font-heading font-bold text-xl">TripStars</span>
            </div>
            <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-white" data-testid="close-sidebar-btn">
              <X size={24} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-6 space-y-2">
            {filteredNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  isActive
                    ? 'flex items-center gap-3 px-4 py-3 text-white bg-primary rounded-md shadow-sm mx-2 font-medium'
                    : 'flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-white/5 rounded-md transition-colors mx-2'
                }
                data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <item.icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* User info & logout */}
          <div className="border-t border-slate-800 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">{user?.full_name?.charAt(0)}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{user?.full_name}</p>
                <p className="text-slate-400 text-xs truncate">{user?.role.replace('_', ' ')}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-2 text-slate-400 hover:text-white hover:bg-white/5 rounded-md transition-colors"
              data-testid="logout-btn"
            >
              <LogOut size={20} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)}></div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="flex items-center">
            <button onClick={() => setSidebarOpen(true)} className="lg:hidden mr-4" data-testid="open-sidebar-btn">
              <Menu size={24} className="text-text-primary" />
            </button>
            <h1 className="text-xl font-heading font-semibold text-text-primary">Task Management System</h1>
          </div>
          
          {/* Notification Bell */}
          <NotificationBell />
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
