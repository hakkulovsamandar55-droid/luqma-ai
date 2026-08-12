import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { temaniKuzat, temaniQoll } from './lib/theme'
import './styles/global.css'

// Temani React ishga tushishidan OLDIN qo'llaymiz — aks holda ilova bir
// lahza noto'g'ri rangda ko'rinib, keyin sakraydi.
temaniQoll()
temaniKuzat()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
