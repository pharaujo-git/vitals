import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { AuthResponse, User } from '../../shared/api/types'

/** The refresh token lives in an httpOnly cookie; only the short-lived
 *  access token and the user profile touch JS-accessible storage. */
interface AuthState {
  user: User | null
  accessToken: string | null
}

const STORAGE_KEY = 'vitals-auth'

function loadInitialState(): AuthState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as AuthState
      return { user: parsed.user ?? null, accessToken: parsed.accessToken ?? null }
    }
  } catch {
    // fall through to a clean state
  }
  return { user: null, accessToken: null }
}

const authSlice = createSlice({
  name: 'auth',
  initialState: loadInitialState,
  reducers: {
    setCredentials(state, action: PayloadAction<AuthResponse>) {
      state.user = action.payload.user
      state.accessToken = action.payload.accessToken
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    },
    updateUser(state, action: PayloadAction<User>) {
      state.user = action.payload
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    },
    clearCredentials(state) {
      state.user = null
      state.accessToken = null
      localStorage.removeItem(STORAGE_KEY)
    },
  },
})

export const { setCredentials, updateUser, clearCredentials } = authSlice.actions
export default authSlice.reducer
