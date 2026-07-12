import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, EmptyState, Spinner } from '../../shared/ui/Page'
import { useObservationTrendsQuery, type TrendSeries } from './api'

const tooltipStyle = {
  backgroundColor: 'var(--color-surface)',
  border: '1px solid var(--color-line)',
  borderRadius: 8,
  fontSize: 12,
  color: 'var(--color-ink)',
}

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

/** One small chart per measure — small multiples, never a dual axis. */
function TrendChart({ series }: { series: TrendSeries }) {
  const points = series.points.map((p) => ({ ...p, label: shortDate(p.takenAt) }))
  const latest = series.points[series.points.length - 1]
  return (
    <div className="border-line rounded-md border p-3">
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <p className="text-ink-muted truncate text-xs font-semibold">{series.label}</p>
        <p className="text-ink text-[13px] font-bold whitespace-nowrap tabular-nums">
          {latest.value}
          {series.unit && <span className="text-ink-muted ml-0.5 text-[11px] font-normal">{series.unit}</span>}
        </p>
      </div>
      <ResponsiveContainer width="100%" height={110}>
        <LineChart data={points} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--color-line)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-ink-faint)', fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            width={34}
            domain={['auto', 'auto']}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-ink-faint)', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value) => [`${value}${series.unit ? ` ${series.unit}` : ''}`, series.label]}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#17a98c"
            strokeWidth={2}
            dot={{ r: 2.5, fill: '#17a98c', strokeWidth: 0 }}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function TrendsCard({ patientId }: { patientId: string }) {
  const { data, isLoading } = useObservationTrendsQuery(patientId)

  return (
    <Card title="Vitals trends">
      {isLoading && <Spinner />}
      {data && data.length === 0 && (
        <EmptyState
          icon="tabler--chart-line"
          message="Trends appear once a measure has at least two recorded values."
        />
      )}
      {data && data.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {data.map((series) => (
            <TrendChart key={series.code} series={series} />
          ))}
        </div>
      )}
    </Card>
  )
}
