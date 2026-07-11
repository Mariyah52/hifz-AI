import type { HTMLAttributes } from 'react';

type Tone = 'teal' | 'gold' | 'maroon' | 'neutral';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

const toneClasses: Record<Tone, string> = {
  teal: 'bg-teal/10 text-teal-dark',
  gold: 'bg-gold/15 text-[#8a6218]',
  maroon: 'bg-maroon/10 text-maroon',
  neutral: 'bg-sage text-ink-soft',
};

export function Badge({ tone = 'neutral', className = '', children, ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold
        font-mono tracking-tight ${toneClasses[tone]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
