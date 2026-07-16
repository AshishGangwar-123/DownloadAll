# PWA (Progressive Web App) Setup Guide & Discussion Notes

A Progressive Web App (PWA) is a type of application software delivered through the web, built using common web technologies including HTML, CSS, and JavaScript. It is intended to work on any platform that uses a standards-compliant browser, including both desktop and mobile devices.

---

## 1. Web App Manifest (`manifest.json`)
The manifest file provides metadata about the web application, such as its name, icons, start URL, display style, and theme colors. This information is used by the browser to install the app on the device.

Create a file named `manifest.json` in the root of your application:
```json
{
  "short_name": "StreamGlide",
  "name": "StreamGlide Video Downloader",
  "description": "Download videos instantly from popular platforms.",
  "icons": [
    {
      "src": "icon-192.png",
      "type": "image/png",
      "sizes": "192x192"
    },
    {
      "src": "icon-512.png",
      "type": "image/png",
      "sizes": "512x512"
    }
  ],
  "start_url": "/index.html",
  "background_color": "#0b0f19",
  "theme_color": "#6366f1",
  "display": "standalone",
  "orientation": "portrait"
}
```

Include it in the HTML `<head>`:
```html
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#6366f1">
```

---

## 2. Service Worker (`sw.js`)
A service worker is a script that your browser runs in the background, separate from a web page. It is responsible for caching resources for offline access and is a mandatory requirement for installation.

Create a file named `sw.js` in the root:
```javascript
const CACHE_NAME = 'streamglide-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/manifest.json'
];

// Install Event: Cache app shell
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

// Activate Event: Cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// Fetch Event: Serve cached assets when offline
self.addEventListener('fetch', event => {
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        return cachedResponse || fetch(event.request);
      })
  );
});
```

---

## 3. Install Button Trigger Logic (JavaScript)
The browser triggers a `beforeinstallprompt` event when it determines the web app meets PWA installation criteria. We capture this event and link it to our custom UI installation banner.

Add this code in your main JavaScript file (`app.js`):
```javascript
let deferredPrompt;
const installBanner = document.getElementById('installBanner');
const installBtn = document.getElementById('installBtn');

// Listen for the browser's install prompt event
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the default browser mini-infobar
  e.preventDefault();
  // Store the event so it can be triggered later
  deferredPrompt = e;
  // Show our custom banner / install button
  if (installBanner) {
    installBanner.classList.remove('hidden');
  }
});

// Trigger installation when the user clicks our button
if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    
    // Show the browser install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User choice outcome: ${outcome}`);
    
    // We can only use the prompt once, clear it
    deferredPrompt = null;
    
    // Hide our install UI
    if (installBanner) {
      installBanner.classList.add('hidden');
    }
  });
}

// Track when installation finishes successfully
window.addEventListener('appinstalled', (evt) => {
  console.log('App was successfully installed on the user device!');
});
```

---

## 4. Requirement Criteria
For the browser to prompt the user to install your PWA:
1. **Served via HTTPS** (or `localhost` for local testing).
2. **Valid `manifest.json`** with name, icons (192px and 512px sizes), and `start_url`.
3. **Registered Service Worker** with a functional `fetch` event handler.

---

# Detailed Q&A & Discussion Notes (Hindi / Hinglish)

Hamare discussion ke dauran uthe questions aur unke details niche diye gaye hain:

### Q1. Kya ye app phone ke browser me open karne par UI par install/download ke liye dikhega?
**Ans:** Haan, bilkul dikhega! Lekin iske liye 2 baatein dhyaan rakhna zaroori hain:
* **HTTPS Context:** Mobile phone me testing ke liye ya to local IP setup standard secure rules se bypass ho ya fir site **HTTPS** par deploy ho (jaise Netlify, Vercel ya GitHub Pages par). Local host server machine ke bahar direct IP `http://192.168.x.x` par default chrome secure permissions allow nahi karta.
* **Android vs iOS Interface:**
  * **Android (Chrome, Edge):** Custom banner screen par automatically pop-up ho jayega kyuki isme `beforeinstallprompt` event support hota hai.
  * **iPhone (Safari):** Apple custom banners support nahi karta. Iske liye user ko Safari menu ke niche **Share button** click karke manual scroll karke **"Add to Home Screen"** karna hoga.

---

### Q2. Jo videos download hongi, vo phone me save hongi ya server me?
**Ans:** 
* **Pehle ka implementation:** Videos sirf server machine ke `./downloads` folder me store ho rahi thi. Client (Phone) par link to success display hota tha lekin file actually device tak nahi aati thi.
* **Naya (Current) implementation:** Humne backend me `FileResponse` integrate kiya hai. Backend file binary stream response me browser ko return karta hai aur Javascript use browser window target through automatically default phone ke **"Downloads"** folder me redirect karta hai.

---

### Q3. Agar browser ko file bhejte hain, tab bhi kya files server disk par save rahengi?
**Ans:** Haan! `yt-dlp` ko merge process (audio-video streams bundle) ke liye workspace space chahiye hota hai, to file local folder me temporary create hoti hai.
* **Auto-cleanup solution:** Humne FastAPI me **`BackgroundTasks`** add kiye hain. Jaise hi user ko download stream start/complete hoti hai, server background task trigger karke temporary file ko server local database disk se automatically delete (`os.remove`) kar deta hai. Isse aapka server space bilkul safe rehta hai aur client ko uski file mil jati hai.

---

### Q4. Icons settings me 192px aur 512px ki do alag-alag images kyun specify ki gayi hain?
**Ans:** Photo/Design bilkul ek hi (same design) hai, lekin use do alag dimensions (sizes) me generate kiya hai:
1. **`192x192` (Small icon size):** Launcher screens shortcut icons ke grid display me notification updates area ke liye.
2. **`512x512` (High-res large icon size):** Responsive splash screens (jaise loading loading dynamic screens launch page) ke resolution scale support ke liye.
3. **Browser rule:** Chrome/Edge specifications check complete tabhi pass karte hain jab dono standard options file system manifest list me declared aur paths correct hon.
