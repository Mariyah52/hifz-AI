interface ProgressRingProps {
  /** 0-100 */
  value: number;
  size?: number;
  label?: string;
  sublabel?: string;
  tone?: 'teal' | 'gold';
}

/**
 * Signature element: an illuminated rosette — the 8-point star roundel
 * classical mushafs use to mark every 5th/10th ayah — redrawn here as a
 * progress medallion. Used for Sabaq completion, juz progress, and streaks
 * wherever a plain progress bar would flatten the app's identity.
 */
export function ProgressRing({
  value,
  size = 96,
  label,
  sublabel,
  tone = 'teal',
}: ProgressRingProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const stroke = size * 0.07;
  const radius = size / 2 - stroke * 1.6;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const ringColor = tone === 'teal' ? 'var(--color-teal)' : 'var(--color-gold)';
  const center = size / 2;

  // 8-point star rosette, drawn as two overlapping squares rotated 45deg
  const starRadius = size / 2 - stroke * 0.4;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0">
        <g opacity={0.16} stroke={ringColor} strokeWidth={1}>
          <rect
            x={center - starRadius * 0.72}
            y={center - starRadius * 0.72}
            width={starRadius * 1.44}
            height={starRadius * 1.44}
            fill="none"
            transform={`rotate(0 ${center} ${center})`}
          />
          <rect
            x={center - starRadius * 0.72}
            y={center - starRadius * 0.72}
            width={starRadius * 1.44}
            height={starRadius * 1.44}
            fill="none"
            transform={`rotate(45 ${center} ${center})`}
          />
        </g>
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-sage)"
          strokeWidth={stroke}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${center} ${center})`}
          style={{
            transition: 'stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        />
      </svg>
      <div className="flex flex-col items-center justify-center text-center">
        {label && <span className="font-mono text-lg font-semibold text-ink leading-none">{label}</span>}
        {sublabel && <span className="text-[10px] text-ink-soft mt-1 leading-none">{sublabel}</span>}
      </div>
    </div>
  );
}
