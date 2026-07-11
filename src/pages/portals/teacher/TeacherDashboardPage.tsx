import { LogOut, Radio, ChevronRight, MessageCircle, Megaphone } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { StudentCard } from '@/components/teacher/StudentCard';
import { NotificationBellButton } from '@/components/shared/NotificationBellButton';
import { useTeacherRoster } from '@/hooks/useTeacherRoster';
import { useAuth } from '@/hooks/useAuth';

export function TeacherDashboardPage() {
  const { roster, isLoading } = useTeacherRoster();
  const { logout } = useAuth();

  return (
    <>
      <header className="flex items-center justify-between gap-3 px-5 pt-6 pb-2">
        <div>
          <p className="text-sm text-ink-soft font-body">Teacher Portal</p>
          <h1 className="font-display text-xl font-semibold text-ink">
            {isLoading ? 'Loading…' : `${roster.length} students`}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <NotificationBellButton sizeClass="h-9 w-9" />
          <button
            aria-label="Log out"
            onClick={logout}
            className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4">
        <Link
          to="/teacher/live-session"
          className="flex items-center justify-between rounded-2xl bg-teal/10 px-4 py-3 mb-4 hover:bg-teal/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Radio size={18} className="text-teal-dark shrink-0" />
            <div>
              <p className="font-body font-semibold text-teal-dark text-sm">Start a live class</p>
              <p className="font-body text-xs text-ink-soft mt-0.5">Listen live, mark mistakes, automatic attendance</p>
            </div>
          </div>
          <ChevronRight size={16} className="text-teal-dark shrink-0" />
        </Link>

        <div className="grid grid-cols-2 gap-2 mb-4">
          <Link
            to="/messages"
            className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-paper-dim px-3 py-3 hover:bg-sage/60 transition-colors"
          >
            <MessageCircle size={18} className="text-ink-soft" />
            <p className="font-body font-semibold text-ink text-xs">Messages</p>
          </Link>
          <Link
            to="/teacher/class-updates"
            className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-paper-dim px-3 py-3 hover:bg-sage/60 transition-colors"
          >
            <Megaphone size={18} className="text-ink-soft" />
            <p className="font-body font-semibold text-ink text-xs">Class updates</p>
          </Link>
        </div>

        <div className="flex flex-col gap-2">
          {roster.map((student) => (
            <StudentCard key={student.id} student={student} />
          ))}
          {!isLoading && roster.length === 0 && (
            <Card>
              <p className="font-body text-sm text-ink-soft">
                No students are enrolled in a class you teach yet — an admin can assign one.
              </p>
            </Card>
          )}
        </div>
      </main>
    </>
  );
}
