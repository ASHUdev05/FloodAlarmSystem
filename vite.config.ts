import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // This line is the critical addition
  base: process.env.VITE_PUBLIC_BASE_PATH || '/',
})
