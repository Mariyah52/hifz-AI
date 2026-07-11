import type { HTMLAttributes } from 'react';

export function Card({ className = '', children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-card bg-paper border border-ink/[0.06] shadow-folio p-5 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
