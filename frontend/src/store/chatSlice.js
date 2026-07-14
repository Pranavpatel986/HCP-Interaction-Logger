import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client'

export const sendChatMessage = createAsyncThunk('chat/send', async (message) => {
  const { data } = await api.post('/chat', { message })
  return { userMessage: message, ...data }
})

const chatSlice = createSlice({
  name: 'chat',
  initialState: { messages: [], status: 'idle' },
  reducers: {
    resetChat: (state) => {
      state.messages = []
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state, action) => {
        state.status = 'loading'
        state.messages.push({ role: 'user', text: action.meta.arg })
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.messages.push({
          role: 'agent',
          text: action.payload.reply,
          tool: action.payload.tool_used,
        })
      })
      .addCase(sendChatMessage.rejected, (state) => {
        state.status = 'failed'
        state.messages.push({ role: 'agent', text: 'Something went wrong. Please try again.' })
      })
  },
})

export const { resetChat } = chatSlice.actions
export default chatSlice.reducer
