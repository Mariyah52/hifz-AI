import { NavLink } from 'react-router-dom';
import { BookOpen, LayoutGrid, Mic, ListChecks, TrendingUp, Radio } from 'lucide-react';

const items = [
  { to: '/', label: 'Dashboard', icon: LayoutGrid, end: true },
  { to: '/learn', label: 'Learn', icon: BookOpen },
  { to: '/practice', label: 'Practice', icon: Mic },
  { to: '/live-coach', label: 'Live', icon: Radio },
  { to: '/test', label: 'Test', icon: ListChecks },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
];

export function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 inset-x-0 z-20 bg-paper/95 backdrop-blur border-t border-ink/[0.08]
        pb-[env(safe-area-inset-bottom)]"
      aria-label="Primary"
    >
      <ul className="grid grid-cols-6">
        {items.map(({ to, label, icon: Icon, end }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors ${
                  isActive ? 'text-teal' : 'text-ink-soft'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} strokeWidth={isActive ? 2.4 : 1.8} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
