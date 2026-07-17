import { useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Megaphone, BookMarked } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { getMyClasses, type TeacherClass } from '@/services/liveSessionService';
import { postTeacherAnnouncement, postHomework, getAnnouncements, getHomework } from '@/services/communicationService';
import type { Announcement, Homework } from '@/types/communication';

export function TeacherClassUpdatesPage() {
  const [classes, setClasses] = useState<TeacherClass[]>([]);
  const [classId, setClassId] = useState('');
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [homework, setHomework] = useState<Homework[]>([]);

  const [annTitle, setAnnTitle] = useState('');
  const [annContent, setAnnContent] = useState('');
  const [hwTitle, setHwTitle] = useState('');
  const [hwDescription, setHwDescription] = useState('');
  const [hwDueDate, setHwDueDate] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  function refresh() {
    getAnnouncements().then(setAnnouncements);
    getHomework().then(setHomework);
  }

  useEffect(() => {
    getMyClasses().then((list) => {
      setClasses(list);
      if (list[0]) setClassId(list[0].id);
    });
    refresh();
  }, []);

  async function handlePostAnnouncement(e: FormEvent) {
    e.preventDefault();
    if (!classId || !annTitle.trim()) return;
    setIsSaving(true);
    try {
      await postTeacherAnnouncement(classId, annTitle.trim(), annContent.trim());
      setAnnTitle('');
      setAnnContent('');
      refresh();
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePostHomework(e: FormEvent) {
    e.preventDefault();
    if (!classId || !hwTitle.trim() || !hwDueDate) return;
    setIsSaving(true);
    try {
      await postHomework(classId, hwTitle.trim(), hwDescription.trim(), hwDueDate);
      setHwTitle('');
      setHwDescription('');
      setHwDueDate('');
      refresh();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/teacher"
          aria-label="Back to Teacher Portal"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Teacher Portal</p>
          <h1 className="heading-section">Class updates</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        {classes.length > 1 && (
          <select
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
            className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
          >
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}

        <section>
          <h3 className="heading-subsection mb-2 flex items-center gap-1.5">
            <Megaphone size={16} />
            Post an announcement
          </h3>
          <Card>
            <form onSubmit={handlePostAnnouncement} className="flex flex-col gap-2">
              <input
                value={annTitle}
                onChange={(e) => setAnnTitle(e.target.value)}
                placeholder="Title"
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
              <textarea
                value={annContent}
                onChange={(e) => setAnnContent(e.target.value)}
                placeholder="Message"
                rows={2}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
              />
              <button
                type="submit"
                disabled={isSaving || !annTitle.trim() || !classId}
                className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
              >
                Post
              </button>
            </form>
          </Card>
        </section>

        <section>
          <h3 className="heading-subsection mb-2 flex items-center gap-1.5">
            <BookMarked size={16} />
            Assign homework
          </h3>
          <Card>
            <form onSubmit={handlePostHomework} className="flex flex-col gap-2">
              <input
                value={hwTitle}
                onChange={(e) => setHwTitle(e.target.value)}
                placeholder="Title"
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
              <textarea
                value={hwDescription}
                onChange={(e) => setHwDescription(e.target.value)}
                placeholder="Description"
                rows={2}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
              />
              <input
                type="date"
                value={hwDueDate}
                onChange={(e) => setHwDueDate(e.target.value)}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
              <button
                type="submit"
                disabled={isSaving || !hwTitle.trim() || !hwDueDate || !classId}
                className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
              >
                Assign
              </button>
            </form>
          </Card>
        </section>

        <section>
          <h3 className="heading-subsection mb-2">Recently posted</h3>
          <div className="flex flex-col gap-2">
            {homework.map((h) => (
              <Card key={h.id}>
                <p className="font-body font-semibold text-ink text-sm">{h.title}</p>
                <p className="font-mono text-[10px] text-ink-soft mt-0.5">{h.className} · due {h.dueDate}</p>
              </Card>
            ))}
            {announcements.map((a) => (
              <Card key={a.id}>
                <p className="font-body font-semibold text-ink text-sm">{a.title}</p>
                <p className="font-mono text-[10px] text-ink-soft mt-0.5">{a.className}</p>
              </Card>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
