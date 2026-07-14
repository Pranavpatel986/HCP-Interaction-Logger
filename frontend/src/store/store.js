import { configureStore } from '@reduxjs/toolkit'
import interactionsReducer from './interactionsSlice'
import chatReducer from './chatSlice'
import hcpsReducer from './hcpsSlice'

export const store = configureStore({
  reducer: {
    interactions: interactionsReducer,
    chat: chatReducer,
    hcps: hcpsReducer,
  },
})
