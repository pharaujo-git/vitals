import { useState, type FormEvent } from 'react'
import { roleLabels } from '../../shared/api/types'
import { Badge } from '../../shared/ui/Badge'
import { Button } from '../../shared/ui/Button'
import { Input, Select } from '../../shared/ui/Field'
import { Card, ErrorNote, Spinner } from '../../shared/ui/Page'
import { useConsentQuery, useUpdateConsentMutation } from './api'

/** Admin-only: consent rules governing who may open a restricted record. */
export function ConsentCard({ patientId }: { patientId: string }) {
  const { data, isLoading } = useConsentQuery(patientId)
  const [update, { isLoading: saving, error }] = useUpdateConsentMutation()
  const [granteeType, setGranteeType] = useState<'role' | 'user'>('role')
  const [grantee, setGrantee] = useState('clinician')

  if (isLoading || !data) {
    return (
      <Card title="Consent & access rules">
        <Spinner />
      </Card>
    )
  }

  async function toggleRestricted() {
    if (!data) return
    await update({
      id: patientId,
      restricted: !data.restricted,
      grants: data.grants.map((g) => ({
        granteeType: g.granteeType,
        grantee: g.granteeType === 'user' ? g.display : g.grantee,
      })),
    })
  }

  async function addGrant(e: FormEvent) {
    e.preventDefault()
    if (!data || !grantee.trim()) return
    const result = await update({
      id: patientId,
      restricted: data.restricted,
      grants: [
        ...data.grants.map((g) => ({
          granteeType: g.granteeType,
          grantee: g.granteeType === 'user' ? g.display : g.grantee,
        })),
        { granteeType, grantee: grantee.trim() },
      ],
    })
    if (!('error' in result)) setGrantee(granteeType === 'role' ? 'clinician' : '')
  }

  async function removeGrant(index: number) {
    if (!data) return
    await update({
      id: patientId,
      restricted: data.restricted,
      grants: data.grants
        .filter((_, i) => i !== index)
        .map((g) => ({
          granteeType: g.granteeType,
          grantee: g.granteeType === 'user' ? g.display : g.grantee,
        })),
    })
  }

  return (
    <Card
      title="Consent & access rules"
      actions={
        <button
          onClick={toggleRestricted}
          disabled={saving}
          className={`relative h-5.5 w-10 cursor-pointer rounded-full transition-colors ${
            data.restricted ? 'bg-accent-red' : 'bg-ink-faint/40'
          }`}
          role="switch"
          aria-checked={data.restricted}
          aria-label="Restrict record"
        >
          <span
            className={`absolute top-0.5 size-4.5 rounded-full bg-white shadow transition-[left] ${
              data.restricted ? 'left-5' : 'left-0.5'
            }`}
          />
        </button>
      }
    >
      <div className="space-y-3">
        <p className="text-ink-muted text-xs">
          {data.restricted ? (
            <>
              <span className="text-accent-red font-semibold">Restricted.</span> Only administrators
              and the grantees below can open this record; denied attempts are written to the audit
              log.
            </>
          ) : (
            'Open access: any staff role with patient permissions can view this record. Toggle to restrict.'
          )}
        </p>

        {data.restricted && (
          <>
            <div className="flex flex-wrap gap-1.5">
              {data.grants.length === 0 && (
                <p className="text-ink-faint text-xs">No grants yet — only administrators have access.</p>
              )}
              {data.grants.map((grant, i) => (
                <span key={`${grant.granteeType}-${grant.grantee}`} className="inline-flex items-center gap-1">
                  <Badge tone={grant.granteeType === 'role' ? 'blue' : 'violet'}>
                    <i
                      className={`iconify ${grant.granteeType === 'role' ? 'tabler--users' : 'tabler--user'} size-3`}
                      aria-hidden
                    />
                    {grant.granteeType === 'role'
                      ? (roleLabels[grant.display as keyof typeof roleLabels] ?? grant.display)
                      : grant.display}
                    <button
                      onClick={() => removeGrant(i)}
                      disabled={saving}
                      className="hover:text-accent-red ml-0.5 cursor-pointer"
                      aria-label="Remove grant"
                    >
                      <i className="iconify tabler--x size-3" aria-hidden />
                    </button>
                  </Badge>
                </span>
              ))}
            </div>

            <form onSubmit={addGrant} className="flex items-end gap-2">
              <div className="w-32">
                <Select
                  label="Grant to"
                  value={granteeType}
                  onChange={(e) => {
                    const type = e.target.value as 'role' | 'user'
                    setGranteeType(type)
                    setGrantee(type === 'role' ? 'clinician' : '')
                  }}
                >
                  <option value="role">Role</option>
                  <option value="user">User</option>
                </Select>
              </div>
              <div className="flex-1">
                {granteeType === 'role' ? (
                  <Select value={grantee} onChange={(e) => setGrantee(e.target.value)}>
                    <option value="clinician">Clinician</option>
                    <option value="front_desk">Front desk</option>
                    <option value="manager">Manager</option>
                  </Select>
                ) : (
                  <Input
                    placeholder="user@clinic.org"
                    type="email"
                    value={grantee}
                    onChange={(e) => setGrantee(e.target.value)}
                  />
                )}
              </div>
              <Button type="submit" size="sm" className="h-9" disabled={saving || !grantee.trim()}>
                Add
              </Button>
            </form>
          </>
        )}
        {error !== undefined && <ErrorNote error={error} />}
      </div>
    </Card>
  )
}
