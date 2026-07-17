import { Megaphone, Store, Settings, ChevronRight } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { StatTile } from '@/components/progress/StatTile';
import { StudentCard } from '@/components/teacher/StudentCard';
import { TeacherCard } from '@/components/admin/TeacherCard';
import { ClassCard } from '@/components/admin/ClassCard';
import { OrganizationBanner } from '@/components/layout/OrganizationBanner';
import { postAdminAnnouncement } from '@/services/communicationService';
import { useAdminOverview } from '@/hooks/useAdminOverview';

export function AdminDashboardPage() {
  // `auditLog` is intentionally not read here — the "Security activity"
  // section was removed from this page, but the backend keeps logging
  // every login/logout/etc via log_audit_event() regardless (see
  // routers/auth.py), so nothing about the underlying data changed.
  const { teachers, classes, analytics, organization, isLoading } = useAdminOverview();
  const [annTitle, setAnnTitle] = useState('');
  const [annContent, setAnnContent] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  const [posted, setPosted] = useState(false);

  async function handlePostAnnouncement(e: FormEvent) {
    e.preventDefault();
    if (!annTitle.trim()) return;
    setIsPosting(true);
    try {
      await postAdminAnnouncement(annTitle.trim(), annContent.trim());
      setAnnTitle('');
      setAnnContent('');
      setPosted(true);
    } finally {
      setIsPosting(false);
    }
  }

  if (isLoading || !analytics) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading…</div>;
  }

  return (
    <>
      <OrganizationBanner roleLabel="Admin" />

      <main className="px-5 flex flex-col gap-5 mt-2 pb-4">
        {organization && (
          <Card>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-body font-semibold text-ink text-sm">Institution overview</p>
                <p className="font-mono text-xs text-ink-soft mt-0.5">
                  Code: {organization.slug} · {organization.plan} plan
                </p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div>
                <p className="font-mono text-xs text-ink-soft">Students</p>
                <p className="font-body text-sm font-semibold text-ink">
                  {organization.currentStudentCount} / {organization.maxStudents}
                </p>
              </div>
              <div>
                <p className="font-mono text-xs text-ink-soft">Teachers</p>
                <p className="font-body text-sm font-semibold text-ink">
                  {organization.currentTeacherCount} / {organization.maxTeachers}
                </p>
              </div>
            </div>
          </Card>
        )}

        <section>
          <h3 className="heading-subsection mb-3">Manage</h3>
          <div className="flex flex-col gap-2">
            <Link
              to="/admin/marketplace"
              className="flex items-center gap-3 rounded-card bg-paper border border-ink/[0.06] shadow-folio p-4 hover:bg-paper-dim transition-colors"
            >
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gold/15 text-[#8a6218]">
                <Store size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-body font-semibold text-ink text-sm">Marketplace</p>
                <p className="font-body text-xs text-ink-soft">Question banks, revision plans, reciters, themes, plugins</p>
              </div>
              <ChevronRight size={16} className="text-ink-soft shrink-0" />
            </Link>
            <Link
              to="/admin/settings"
              className="flex items-center gap-3 rounded-card bg-paper border border-ink/[0.06] shadow-folio p-4 hover:bg-paper-dim transition-colors"
            >
              <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-sage text-ink-soft">
                <Settings size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-body font-semibold text-ink text-sm">Branding &amp; settings</p>
                <p className="font-body text-xs text-ink-soft">Logo, colors, welcome message, principal's message</p>
              </div>
              <ChevronRight size={16} className="text-ink-soft shrink-0" />
            </Link>
          </div>
        </section>

        <div className="grid grid-cols-3 gap-3">
          <StatTile label="Students" value={String(analytics.totalStudents)} />
          <StatTile label="Teachers" value={String(analytics.totalTeachers)} />
          <StatTile label="Classes" value={String(analytics.totalClasses)} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <StatTile label="Sabaqs assigned" value={String(analytics.totalSabaqsAssigned)} />
          <StatTile label="Feedback given" value={String(analytics.totalFeedbackGiven)} />
          <StatTile
            label="Avg. test score"
            value={analytics.averageTestScore != null ? `${analytics.averageTestScore}%` : '—'}
          />
        </div>

        <section>
          <h3 className="heading-subsection mb-3">Classes</h3>
          <div className="flex flex-col gap-2">
            {classes.map((c) => (
              <ClassCard key={c.id} classSummary={c} />
            ))}
          </div>
        </section>

        <section>
          <h3 className="heading-subsection mb-3">Teachers</h3>
          <div className="flex flex-col gap-2">
            {teachers.map((t) => (
              <TeacherCard key={t.id} teacher={t} classCount={t.classIds.length} />
            ))}
          </div>
        </section>

        <section>
          <h3 className="heading-subsection mb-3">Needs attention</h3>
          {analytics.studentsNeedingAttention.length > 0 ? (
            <div className="flex flex-col gap-2">
              {analytics.studentsNeedingAttention.map((s) => (
                <StudentCard key={s.id} student={s} />
              ))}
            </div>
          ) : (
            <Card>
              <p className="font-body text-sm text-ink-soft">
                No students with a broken streak right now.
              </p>
            </Card>
          )}
        </section>

        <section>
          <h3 className="heading-subsection mb-3 flex items-center gap-1.5">
            <Megaphone size={16} />
            Institution-wide announcement
          </h3>
          <Card>
            {posted && <p className="font-body text-xs text-teal-dark mb-2">Posted.</p>}
            <form onSubmit={handlePostAnnouncement} className="flex flex-col gap-2">
              <input
                value={annTitle}
                onChange={(e) => {
                  setAnnTitle(e.target.value);
                  setPosted(false);
                }}
                placeholder="Title"
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
              <textarea
                value={annContent}
                onChange={(e) => setAnnContent(e.target.value)}
                placeholder="Message, visible to everyone in the organization"
                rows={2}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
              />
              <button
                type="submit"
                disabled={isPosting || !annTitle.trim()}
                className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
              >
                {isPosting ? 'Posting…' : 'Post'}
              </button>
            </form>
          </Card>
        </section>
      </main>
    </>
  );
}
