import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client'

export const fetchHCPs = createAsyncThunk('hcps/fetch', async () => {
  const { data } = await api.get('/hcps')
  return data
})

const hcpsSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], status: 'idle' },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list = action.payload
      })
  },
})

export default hcpsSlice.reducer
