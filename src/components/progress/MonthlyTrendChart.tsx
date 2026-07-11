import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DailyActivity } from '@/types/progress';

interface MonthlyTrendChartProps {
  data: DailyActivity[];
}

function dayLabel(dateIso: string): string {
  return new Date(dateIso).toLocaleDateString(undefined, { day: 'numeric' });
}

export function MonthlyTrendChart({ data }: MonthlyTrendChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    label: dayLabel(d.date),
    total: d.practiceCount + d.testCount,
  }));

  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#16302b1a" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: '#4b5f59', fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={{ stroke: '#16302b1a' }}
            tickLine={false}
            interval={4}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 11, fill: '#4b5f59', fontFamily: 'IBM Plex Mono, monospace' }}
            axisLine={false}
            tickLine={false}
            width={20}
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
          <Line
            type="monotone"
            dataKey="total"
            name="Sessions"
            stroke="#0f5c4e"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
