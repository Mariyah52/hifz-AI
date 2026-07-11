import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DailyActivity } from '@/types/progress';

interface WeeklyActivityChartProps {
  data: DailyActivity[];
}

function shortLabel(dateIso: string): string {
  return new Date(dateIso).toLocaleDateString(undefined, { weekday: 'short' });
}

export function WeeklyActivityChart({ data }: WeeklyActivityChartProps) {
  const chartData = data.map((d) => ({ ...d, label: shortLabel(d.date) }));

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#16302b1a" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: '#4b5f59', fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={{ stroke: '#16302b1a' }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 11, fill: '#4b5f59', fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            width={24}
          />
          <Tooltip
            contentStyle={{
              background: '#faf3e4',
              border: '1px solid #16302b1a',
              borderRadius: 12,
              fontSize: 12,
              fontFamily: 'Inter, sans-serif',
            }}
          />
          <Bar dataKey="practiceCount" name="Practice" fill="#0f5c4e" radius={[4, 4, 0, 0]} maxBarSize={18} />
          <Bar dataKey="testCount" name="Test" fill="#c08a28" radius={[4, 4, 0, 0]} maxBarSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
