import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { AuthResponse, User } from '../../shared/api/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
}

const STORAGE_KEY = 'vitals-auth'

function loadInitialState(): AuthState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return JSON.parse(stored) as AuthState
  } catch {
    // fall through to a clean state
  }
  return { user: null, accessToken: null, refreshToken: null }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: loadInitialState,
  reducers: {
    setCredentials(state, action: PayloadAction<AuthResponse>) {
      state.user = action.payload.user
      state.accessToken = action.payload.accessToken
      state.refreshToken = action.payload.refreshToken
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    },
    clearCredentials(state) {
      state.user = null
      state.accessToken = null
      state.refreshToken = null
      localStorage.removeItem(STORAGE_KEY)
    },
  },
})

export const { setCredentials, clearCredentials } = authSlice.actions
export default authSlice.reducer
