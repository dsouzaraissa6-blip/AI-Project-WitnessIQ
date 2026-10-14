// Navbar component
import { Link, useLocation } from 'react-router-dom';
import { Scale, LayoutDashboard, FolderOpen, Info } from 'lucide-react';

const navLinks = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/history', label: 'Case History', icon: FolderOpen },
  { to: '/about', label: 'Methodology', icon: Info },
];

export default function Navbar() {
  const location = useLocation();

  return (
    <nav style={{ backgroundColor: '#0f2044' }} className="text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 text-white no-underline">
            <Scale className="w-6 h-6 text-blue-300" />
            <span className="font-bold text-lg tracking-tight">WitnessIQ</span>
            <span className="text-xs text-blue-300 font-normal ml-1 hidden sm:block">
              Statement Analysis
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => {
              const active = location.pathname === to;
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors no-underline ${
                    active
                      ? 'bg-white/20 text-white'
                      : 'text-blue-200 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:block">{label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
