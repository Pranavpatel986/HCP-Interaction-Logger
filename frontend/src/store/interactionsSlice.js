import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client'

export const fetchInteractions = createAsyncThunk('interactions/fetch', async (hcpId) => {
  const { data } = await api.get('/interactions', { params: hcpId ? { hcp_id: hcpId } : {} })
  return data
})

export const createInteraction = createAsyncThunk('interactions/create', async (payload) => {
  const { data } = await api.post('/interactions', payload)
  return data
})

export const updateInteraction = createAsyncThunk(
  'interactions/update',
  async ({ id, payload }) => {
    const { data } = await api.put(`/interactions/${id}`, payload)
    return data
  }
)

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: { list: [], status: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.list = action.payload
        state.status = 'succeeded'
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.list.unshift(action.payload)
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const idx = state.list.findIndex((i) => i.id === action.payload.id)
        if (idx !== -1) state.list[idx] = action.payload
      })
  },
})

export default interactionsSlice.reducer
