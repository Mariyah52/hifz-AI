import { useState, type FormEvent } from 'react';
import { Award } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { issueCertificate } from '@/services/teacherService';

interface IssueCertificateFormProps {
  studentId: string;
  onIssued: () => void;
}

export function IssueCertificateForm({ studentId, onIssued }: IssueCertificateFormProps) {
  const [type, setType] = useState<'attendance' | 'competition'>('attendance');
  const [title, setTitle] = useState('');
  const [detail, setDetail] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setIsSaving(true);
    try {
      await issueCertificate(studentId, type, title.trim(), detail.trim() || title.trim());
      setTitle('');
      setDetail('');
      onIssued();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Card className="flex flex-col gap-2">
      <p className="font-body font-semibold text-ink text-sm flex items-center gap-1.5">
        <Award size={15} />
        Issue a certificate
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <select
          value={type}
          onChange={(e) => setType(e.target.value as 'attendance' | 'competition')}
          className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
        >
          <option value="attendance">Attendance</option>
          <option value="competition">Competition / achievement</option>
        </select>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title, e.g. 'Perfect Attendance — Ramadan'"
          className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
        />
        <input
          type="text"
          value={detail}
          onChange={(e) => setDetail(e.target.value)}
          placeholder="Detail line shown on the certificate (optional)"
          className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
        />
        <button
          type="submit"
          disabled={isSaving || !title.trim()}
          className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
        >
          {isSaving ? 'Issuing…' : 'Issue certificate'}
        </button>
      </form>
    </Card>
  );
}
