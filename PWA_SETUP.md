# PWA Setup — TransPyC

This document outlines the Progressive Web App (PWA) implementation for TransPyC.

## What is a PWA?

A Progressive Web App (PWA) is a web application that uses modern web capabilities to deliver an app-like experience to users. Key features:

- **Installable** — Add to home screen on mobile and desktop
- **Offline-capable** — Works offline or with poor connectivity via service workers
- **Fast** — Smart caching strategies for instant loads
- **App-like UI** — Fullscreen, no address bar, native feel
- **Secure** — Served over HTTPS

## PWA Files & Components

### 1. **manifest.json**
Location: `frontend/manifest.json` → deployed to `/manifest.json`

Metadata file defining:
- App name, short name, description
- Display mode (standalone = fullscreen, no browser UI)
- Theme colors (header) and background colors
- App icons (192x192, 512x512, maskable variants)
- Shortcuts (quick actions like "New Conversion", "View Problems")
- Share target (future: accept shares from other apps)

**Key settings:**
```json
{
  "display": "standalone",        // App-like experience
  "scope": "/",                   // All routes under root
  "start_url": "/",               // Launch to home
  "background_color": "#0d1117",  // During load
  "theme_color": "#2f81f7",       // Header & status bar
  "icons": [...]                  // App icons for stores & install
}
```

### 2. **service-worker.js**
Location: `frontend/service-worker.js` → deployed to `/service-worker.js`

JavaScript file running in the background that intercepts network requests and implements caching:

**Strategies:**
- **Cache-first (Static Assets):** Serve from cache, update in background. Fast, works offline.
  - HTML, CSS, JS files
  - Fonts from Google Fonts
  
- **Network-first (API calls):** Try network, fallback to cache if offline. Always fresh, graceful degradation.
  - `/api/convert` requests
  - Returns cached conversions if network fails
  - Shows offline notification if no cache available

**Lifecycle:**
- **Install:** Cache all static assets + fonts on first visit
- **Activate:** Clean up old cache versions
- **Fetch:** Intercept requests and apply cache strategy
- **Message:** Handle postMessage from app (e.g., `CLEAR_CACHE`, `SKIP_WAITING`)

**Cache Versioning:**
```javascript
const CACHE_VERSION = 'v1';
const STATIC_CACHE = `transpyc-static-${CACHE_VERSION}`;
const API_CACHE = `transpyc-api-${CACHE_VERSION}`;
const FONT_CACHE = `transpyc-fonts-${CACHE_VERSION}`;
```

To invalidate caches on new deployment, increment `v1` → `v2`.

### 3. **App Icons**
Location: `public/icon-*.png`

Generated PNG icons at 4 variants:
- `icon-192x192.png` — Standard app icon
- `icon-192x192-maskable.png` — Adaptive icon for Android (with safe zone)
- `icon-512x512.png` — Splash screen & stores
- `icon-512x512-maskable.png` — Adaptive variant

**Generation:**
```bash
python generate_icons.py
```

Generated using Pillow with TransPyC branding (lightning bolt + blue accent).

### 4. **index.html Updates**
Meta tags added for PWA detection:

```html
<!-- Theme & app detection -->
<meta name="theme-color" content="#2f81f7">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="TransPyC">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

<!-- Manifest & icons -->
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon-192x192.png">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192x192.png">
```

**Service Worker Registration:**
```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js')
    .then(reg => {
      // Check for updates every 60 seconds
      setInterval(() => reg.update(), 60000);
      // Notify user when new version available
      reg.addEventListener('updatefound', () => showUpdateNotification());
    });
}
```

### 5. **vercel.json Configuration**
Special routing for PWA files:

```json
{
  "src": "/service-worker.js",
  "headers": {
    "Cache-Control": "public, max-age=0, must-revalidate",  // Always fresh
    "Content-Type": "application/javascript"
  }
},
{
  "src": "/manifest.json",
  "headers": {
    "Cache-Control": "public, max-age=3600",  // Cache 1 hour
    "Content-Type": "application/json"
  }
}
```

## Usage & Testing

### Installation on Desktop/Mobile

1. **Chrome/Edge Desktop:**
   - Open the app
   - Click "Install" button in address bar (or menu → "Install app")
   - Opens in a standalone window

2. **Chrome/Firefox Android:**
   - Open the app
   - Tap menu → "Add to Home screen"
   - Opens fullscreen on home screen

3. **Safari iOS (iOS 15+):**
   - Open Safari
   - Share → "Add to Home Screen"
   - Uses apple-mobile-web-app-* meta tags

### Testing PWA Features

**Lighthouse Audit:**
1. Open DevTools (F12)
2. Go to "Lighthouse" tab
3. Run "PWA" audit
4. Check for:
   - ✅ Installable
   - ✅ Works offline
   - ✅ HTTPS
   - ✅ Manifest valid
   - ✅ Service worker registered

**Service Worker Inspector:**
1. DevTools → "Application" → "Service Workers"
2. See registered workers, cache storage
3. Manually "Unregister" or "Update"

**Offline Testing:**
1. DevTools → "Network" tab
2. Check "Offline" checkbox
3. Try converting code
4. Should show offline message or cached results

**Cache Inspection:**
1. DevTools → "Application" → "Cache Storage"
2. View cached files by cache name:
   - `transpyc-static-v1` — HTML, CSS, JS
   - `transpyc-fonts-v1` — Fonts
   - `transpyc-api-v1` — API responses

### Clearing Cache

**From Browser DevTools:**
- Application → Cache Storage → Right-click cache → Delete

**Programmatically (from console):**
```javascript
// Clear all PWA caches
window.clearPWACache();
```

**In Service Worker Message:**
```javascript
navigator.serviceWorker.controller.postMessage({ type: 'CLEAR_CACHE' });
```

## Offline Behavior

### Connected
- All requests go to network
- Responses are cached for offline use
- Fresh data shown to user

### Offline (No Internet)

**Static Assets (HTML, CSS, JS):**
- Served from cache instantly
- Full UI available

**API Calls (/api/convert):**
- If previous conversion cached → show cached result
- If no cache → show "offline" notification with error message

**Offline Error Response:**
```json
{
  "error": "offline",
  "message": "You are currently offline. Conversion requires an active internet connection.",
  "warnings": [{
    "type": "error",
    "message": "Network unavailable — please reconnect to convert code",
    "hint": "Check your internet connection and try again."
  }]
}
```

## Updates & Versioning

### Automatic Update Checks
Service worker checks for updates every 60 seconds. When new version detected:
1. Toast notification: "Update available! Reload to get latest features"
2. User can click "Reload" to restart with new version
3. Or dismiss to continue using current version

### Versioning Strategy
To deploy a new version:

1. **Update code** (e.g., fix bugs, add features)
2. **Increment CACHE_VERSION** in `service-worker.js`:
   ```javascript
   const CACHE_VERSION = 'v2';  // was v1
   ```
3. **Commit & push** to GitHub
4. **Deploy to Vercel** (automatic via GitHub integration)
5. Users will see update notification on next visit

### Zero-Downtime Deployment
- Old service worker keeps working until user reloads
- New service worker activates in background
- Users are notified, not forced to update
- Graceful transition, no crashes

## File Structure

```
py-c-whisper-main/
├── frontend/
│   ├── index.html                    (+ PWA meta tags & SW registration)
│   ├── app.js
│   ├── styles.css
│   ├── manifest.json                 (NEW: PWA manifest)
│   └── service-worker.js             (NEW: Cache & offline logic)
├── public/
│   ├── icon-192x192.png             (NEW: App icon)
│   ├── icon-192x192-maskable.png    (NEW: Adaptive icon)
│   ├── icon-512x512.png             (NEW: Splash screen)
│   ├── icon-512x512-maskable.png    (NEW: Adaptive variant)
│   ├── icon-192x192.svg             (NEW: SVG source)
│   ├── icon-512x512.svg             (NEW: SVG source)
│   └── ICON_GENERATION.js           (NEW: Icon generation guide)
├── generate_icons.py                 (NEW: Python icon generator)
├── vercel.json                       (UPDATED: PWA headers & routing)
├── manifest.json                     → deployed to /manifest.json
└── service-worker.js                 → deployed to /service-worker.js
```

## Browser Support

| Browser | Desktop | Mobile | Notes |
|---------|---------|--------|-------|
| Chrome | ✅ | ✅ | Full PWA support |
| Edge | ✅ | ✅ | Full PWA support |
| Firefox | ⚠️ | ⚠️ | Service worker only; no install UI |
| Safari | ✅ | ⚠️ | iOS 15+; limited install UI |

## Performance Impact

**First Load (New User):**
- Static assets cached → future visits instant
- Service worker registered in background
- No performance penalty

**Subsequent Loads:**
- HTML/CSS/JS served from cache (< 100ms)
- API calls network-first (fresh data when possible)
- Offline mode available with cached data

**Cache Storage Limits:**
- Chrome/Edge: ~50MB
- Firefox: ~50MB per site
- Safari: ~50MB
- Typically not a concern; mostly code (< 1MB)

## Security Considerations

1. **HTTPS Required** — Service workers only work over HTTPS (or localhost)
2. **Manifest Signed** — Not cryptographically signed; reliant on HTTPS for integrity
3. **Offline Cache** — Stores past conversion results locally; no sensitive data exposed
4. **API Offline Cache** — Cached API responses not encrypted locally; user is responsible for device security

## Future Enhancements

1. **Share Target API** — Accept code from other apps
2. **Periodic Background Sync** — Sync conversions in background
3. **Custom App Shortcuts** — Quick access to common tasks
4. **Splash Screen Animation** — Custom branded loading screen
5. **App Shortcuts Badges** — Show problem count, etc.
6. **File Handling** — Open .py files directly in the app

## Debugging PWA Issues

**Service Worker not registering:**
- Check DevTools → Application → Service Workers
- Ensure HTTPS or localhost
- Check browser console for errors

**Cache not updating:**
- Clear all caches via DevTools
- Increment `CACHE_VERSION` in service-worker.js
- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

**Offline conversion fails:**
- No cache available for that API response
- User must reconnect to convert new code
- Design choice: safety over offline conversion

**Icons not showing:**
- Verify PNG files exist in `public/`
- Check manifest.json `icons` array paths
- Regenerate via `python generate_icons.py`

## Resources

- [MDN: Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [MDN: Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [PWA Checklist](https://web.dev/pwa-checklist/)
- [Google Workbox](https://developers.google.com/web/tools/workbox) (for advanced caching)
- [Can I Use: PWA](https://caniuse.com/service-workers)

---

**Last Updated:** 26-03-2026  
**Status:** ✅ Complete  
**PWA Support:** Production-ready
