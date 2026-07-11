import { Check, X } from 'lucide-react';

interface SelfMarkButtonsProps {
  onMark: (mark: 'correct' | 'missed') => void;
}

export function SelfMarkButtons({ onMark }: SelfMarkButtonsProps) {
  return (
    <div className="flex gap-3">
      <button
        onClick={() => onMark('missed')}
        className="flex-1 inline-flex items-center justify-center gap-2 rounded-full bg-maroon/10 text-maroon
          font-semibold text-sm py-3 hover:bg-maroon/20 transition-colors"
      >
        <X size={16} />
        I missed it
      </button>
      <button
        onClick={() => onMark('correct')}
        className="flex-1 inline-flex items-center justify-center gap-2 rounded-full bg-teal text-paper
          font-semibold text-sm py-3 hover:bg-teal-dark transition-colors"
      >
        <Check size={16} />
        Got it right
      </button>
    </div>
  );
}
