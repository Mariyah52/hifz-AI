import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Sabaq } from '@/types/lesson';

interface ContinueCTAProps {
  sabaq: Sabaq;
}

export function ContinueCTA({ sabaq }: ContinueCTAProps) {
  return (
    <Link
      to="/learn"
      className="group relative block overflow-hidden rounded-card bg-teal text-paper p-5 shadow-folio
        animate-rise-in"
    >
      {/* bookmark ribbon */}
      <div className="absolute -right-3 top-0 h-full w-10 bg-gold/90 [clip-path:polygon(0_0,100%_0,100%_88%,50%_100%,0_88%)]" />
      <p className="text-xs uppercase tracking-widest text-paper/70 font-mono">Continue Sabaq</p>
      <h2 className="font-display text-xl font-semibold mt-1">
        {sabaq.surahName} <span className="font-mono text-paper/80 text-base">{sabaq.fromAyah}–{sabaq.toAyah}</span>
      </h2>
      <div className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold">
        Resume where you left off
        <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
