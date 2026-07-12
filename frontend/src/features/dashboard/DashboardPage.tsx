import { Link } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { usePagination } from '../../shared/hooks/usePagination'
import { monthLabel } from '../../shared/lib/format'
import { Badge } from '../../shared/ui/Badge'
import { Card, EmptyState, PageBody, PageHeader, Spinner } from '../../shared/ui/Page'
import { Pagination } from '../../shared/ui/Pagination'
import { useDashboardQuery, useRiskFlagsQuery } from './api'
import type { LabeledCount } from './types'

// Categorical palette validated (light #fff / dark #1e2028) with the dataviz
// six-checks script; assigned in fixed order, never cycled.
const CHART_COLORS = ['#17a98c', '#2586c9', '#7a6ff0', '#c77b28']

const tooltipStyle = {
  backgroundColor: 'var(--color-surface)',
  border: '1px solid var(--color-line)',
  borderRadius: 8,
  fontSize: 12,
  color: 'var(--color-ink)',
}

function StatTile({ icon, label, value, tone }: { icon: string; label: string; value: number; tone: string }) {
  return (
    <Card>
      <div className="flex items-center gap-3.5">
        <span className={`flex size-11 shrink-0 items-center justify-center rounded-lg ${tone}`}>
          <i className={`iconify ${icon} size-5.5`} aria-hidden />
        </span>
        <div className="min-w-0">
          <p className="text-ink text-xl font-bold tabular-nums">{value.toLocaleString()}</p>
          <p className="text-ink-muted truncate text-xs font-semibold">{label}</p>
        </div>
      </div>
    </Card>
  )
}

function CategoryBars({ data, title }: { data: LabeledCount[]; title: string }) {
  return (
    <Card title={title}>
      {data.length === 0 ? (
        <EmptyState message="No data yet." />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ top: 18, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--color-line)" />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-ink-muted)', fontSize: 11 }}
            />
            <YAxis hide />
            <Tooltip cursor={{ fill: 'var(--color-well)' }} contentStyle={tooltipStyle} />
            <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={44}>
              <LabelList dataKey="count" position="top" fill="var(--color-ink)" fontSize={11.5} fontWeight={600} />
              {data.map((entry, index) => (
                <Cell key={entry.label} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  )
}

function TrendChart({ data, title }: { data: { year: number; month: number; count: number }[]; title: string }) {
  const points = data.map((d) => ({ ...d, label: monthLabel(d.year, d.month) }))
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={points} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#17a98c" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#17a98c" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-line)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-ink-muted)', fontSize: 11 }}
          />
          <YAxis
            allowDecimals={false}
            width={30}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--color-ink-muted)', fontSize: 11 }}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            type="monotone"
            dataKey="count"
            stroke="#17a98c"
            strokeWidth={2}
            fill="url(#trendFill)"
            activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}

function RiskFlagsCard() {
  const { limit, offset, setPage } = usePagination(10)
  const { data, isLoading } = useRiskFlagsQuery({ limit, offset })

  return (
    <Card title="Risk flags" flush>
      {isLoading && <Spinner />}
      {data && data.items.length === 0 && (
        <div className="p-5">
          <EmptyState icon="tabler--shield-check" message="No patients above the risk threshold." />
        </div>
      )}
      {data && data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-well text-ink-muted border-line border-b text-left text-[10.5px] font-bold tracking-[0.08em] uppercase">
                  <th className="px-5 py-2.5">Patient</th>
                  <th className="px-5 py-2.5">Age</th>
                  <th className="px-5 py-2.5">Risk</th>
                  <th className="px-5 py-2.5">Why flagged (each rule adds points)</th>
                </tr>
              </thead>
              <tbody className="divide-line divide-y">
                {data.items.map((flag) => (
                  <tr key={flag.patientId} className="hover:bg-well/60 align-top transition-colors">
                    <td className="px-5 py-3 whitespace-nowrap">
                      <Link to={`/patients/${flag.patientId}`} className="text-primary font-medium hover:underline">
                        {flag.patientName}
                      </Link>
                      <span className="text-ink-muted block font-mono text-xs">{flag.mrn}</span>
                    </td>
                    <td className="text-ink-muted px-5 py-3">{flag.age}</td>
                    <td className="px-5 py-3 whitespace-nowrap">
                      <Badge tone={flag.level === 'high' ? 'red' : 'amber'}>
                        <i className="iconify tabler--alert-triangle size-3" aria-hidden />
                        {flag.level} · {flag.score}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      <ul className="text-ink-muted space-y-0.5 text-xs">
                        {flag.reasons.map((reason) => (
                          <li key={reason}>• {reason}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination total={data.total} limit={limit} offset={offset} onPage={setPage} noun="flagged patient" />
        </>
      )}
    </Card>
  )
}

export function DashboardPage() {
  const { data, isLoading } = useDashboardQuery()

  return (
    <>
      <PageHeader title="Population dashboard" />
      <PageBody>
        {isLoading && <Spinner />}
        {data && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
              <StatTile icon="tabler--users" label="Patients" value={data.totals.patients} tone="bg-primary/15 text-primary" />
              <StatTile icon="tabler--stethoscope" label="Encounters" value={data.totals.encounters} tone="bg-accent-blue/15 text-accent-blue" />
              <StatTile icon="tabler--heart-rate-monitor" label="Observations" value={data.totals.observations} tone="bg-accent-violet/15 text-accent-violet" />
              <StatTile icon="tabler--calendar-time" label="Upcoming appointments" value={data.totals.upcomingAppointments} tone="bg-accent-amber/20 text-accent-amber" />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <TrendChart data={data.encounterTrend} title="Encounters per month" />
              <TrendChart data={data.observationTrend} title="Observations per month" />
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <CategoryBars data={data.ageBands} title="Age distribution" />
              <CategoryBars data={data.sexBreakdown} title="Sex" />
              <CategoryBars data={data.sourceBreakdown} title="Patients by source" />
            </div>

            <div className="text-ink-muted flex flex-wrap items-center gap-2 text-[13px]">
              <i className="iconify tabler--flag text-accent-red" aria-hidden />
              <span className="font-semibold">{data.riskSummary.flagged}</span> patient
              {data.riskSummary.flagged === 1 ? '' : 's'} flagged —{' '}
              <span className="text-accent-red font-semibold">{data.riskSummary.high} high</span> ·{' '}
              <span className="text-accent-amber font-semibold">{data.riskSummary.moderate} moderate</span>
              <span className="text-ink-faint">
                (rule-based score over each patient's latest observations; threshold ≥ 3)
              </span>
            </div>

            <RiskFlagsCard />
          </div>
        )}
      </PageBody>
    </>
  )
}
