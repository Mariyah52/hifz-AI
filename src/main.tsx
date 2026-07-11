import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import '@/styles/globals.css';

// Phase 26: registered unconditionally so app-shell caching works for
// everyone, not just people who opt into push notifications (that's a
// separate, explicit subscribe step — see usePushNotifications.ts). This
// registration only makes the app cache-as-you-go for offline loading;
// it does not itself enable push.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Offline on first-ever load, or the browser blocked it — the app
      // still works online-only in that case, just without the offline
      // app-shell benefit until a registration attempt succeeds.
    });
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
