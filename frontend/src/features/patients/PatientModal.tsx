import { useState, type FormEvent } from 'react'
import { Button } from '../../shared/ui/Button'
import { Input, Select, Textarea } from '../../shared/ui/Field'
import { Modal } from '../../shared/ui/Modal'
import { ErrorNote } from '../../shared/ui/Page'
import { useCreatePatientMutation, useUpdatePatientMutation } from './api'
import type { Patient, Sex } from './types'

export function PatientModal({ patient, onClose }: { patient: Patient | null; onClose: () => void }) {
  const [firstName, setFirstName] = useState(patient?.firstName ?? '')
  const [lastName, setLastName] = useState(patient?.lastName ?? '')
  const [dob, setDob] = useState(patient?.dob ?? '')
  const [sex, setSex] = useState<Sex>(patient?.sex ?? 'unknown')
  const [phone, setPhone] = useState(patient?.phone ?? '')
  const [email, setEmail] = useState(patient?.email ?? '')
  const [address, setAddress] = useState(patient?.address ?? '')
  const [history, setHistory] = useState(patient?.history ?? '')

  const [create, { isLoading: creating, error: createError }] = useCreatePatientMutation()
  const [update, { isLoading: updating, error: updateError }] = useUpdatePatientMutation()
  const error = createError ?? updateError

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const input = {
      firstName,
      lastName,
      dob,
      sex,
      phone: phone.trim() || null,
      email: email.trim() || null,
      address: address.trim() || null,
      history: history.trim() || null,
    }
    const result = patient ? await update({ id: patient.id, ...input }) : await create(input)
    if (!('error' in result)) onClose()
  }

  return (
    <Modal title={patient ? 'Edit patient' : 'New patient'} open onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="First name"
            required
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
          <Input
            label="Last name"
            required
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Date of birth"
            type="date"
            required
            value={dob}
            onChange={(e) => setDob(e.target.value)}
          />
          <Select label="Sex" value={sex} onChange={(e) => setSex(e.target.value as Sex)}>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
            <option value="unknown">Unknown</option>
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <Input label="Address" value={address} onChange={(e) => setAddress(e.target.value)} />
        <Textarea
          label="Medical history"
          placeholder="Chronic conditions, allergies, prior procedures…"
          value={history}
          onChange={(e) => setHistory(e.target.value)}
        />
        {error !== undefined && <ErrorNote error={error} />}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={creating || updating}>
            {patient ? 'Save' : 'Create'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
