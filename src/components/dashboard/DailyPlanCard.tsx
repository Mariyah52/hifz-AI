import { Badge } from '@/components/ui/Badge';
import { getJuzForAyah } from '@/services/quranService';
import type { Sabaq, SabqiReview, ManzilReview } from '@/types/lesson';

interface DailyPlanCardProps {
  sabaq: Sabaq | null;
  sabqi: SabqiReview | null;
  manzil: ManzilReview | null;
}

const statusTone = {
  completed: 'teal',
  in_progress: 'gold',
  not_started: 'neutral',
} as const;

function PlanRow({
  label,
  sublabel,
  detail,
  status,
  score,
}: {
  label: string;
  sublabel: string;
  detail: string;
  status: Sabaq['status'];
  score?: number;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-ink/[0.06] last:border-b-0">
      <div>
        <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">{label}</p>
        <p className="font-body font-semibold text-ink text-sm mt-0.5">{sublabel}</p>
        <p className="font-mono text-xs text-ink-soft mt-0.5">{detail}</p>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {typeof score === 'number' && (
          <span className="font-mono text-sm font-semibold text-teal-dark">{score}%</span>
        )}
        <Badge tone={statusTone[status]}>{status.replace('_', ' ')}</Badge>
      </div>
    </div>
  );
}

export function DailyPlanCard({ sabaq, sabqi, manzil }: DailyPlanCardProps) {
  // Phase 13: Manzil is a real SM-2-scheduled due review now (Sabaq-shaped,
  // same as Sabqi) rather than a picked juz — the "Juz N" label is still
  // useful context, so it's derived client-side from the already-verified
  // juz-boundary lookup instead of the backend needing to know about juz.
  const manzilJuz = manzil ? getJuzForAyah(manzil.surahNumber, manzil.fromAyah) : null;

  if (!sabaq && !sabqi && !manzil) return null;

  return (
    <section className="rounded-card bg-paper border border-ink/[0.06] shadow-folio px-4">
      {sabaq && (
        <PlanRow
          label="Sabaq · new"
          sublabel={sabaq.surahName}
          detail={`Ayah ${sabaq.fromAyah}–${sabaq.toAyah}`}
          status={sabaq.status}
          score={sabaq.score}
        />
      )}
      {sabqi && (
        <PlanRow
          label="Sabqi · recent review"
          sublabel={sabqi.surahName}
          detail={`Ayah ${sabqi.fromAyah}–${sabqi.toAyah}`}
          status={sabqi.status}
          score={sabqi.score}
        />
      )}
      {manzil && (
        <PlanRow
          label={`Manzil · distant review${manzilJuz ? ` · Juz ${manzilJuz}` : ''}`}
          sublabel={manzil.surahName}
          detail={`Ayah ${manzil.fromAyah}–${manzil.toAyah}`}
          status={manzil.status}
          score={manzil.score}
        />
      )}
    </section>
  );
}
