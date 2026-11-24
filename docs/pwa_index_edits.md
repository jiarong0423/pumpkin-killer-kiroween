# Main-line PWA edits for `index.html`

Add these lines in `<head>`, after the viewport meta:
```html
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#5a328c">
<link rel="apple-touch-icon" href="icons/icon-192.png">
```

Add this before `</body>`, after the page's existing script tags:
```html
<script>
  if ("serviceWorker" in navigator &&
      (location.protocol === "https:" || location.hostname === "localhost")) {
    navigator.serviceWorker.register("sw.js").catch((error) => {
      console.warn("Service worker registration failed:", error);
    });
  }
</script>
```

In `scripts/release/export_manifest.json`, insert these INCLUDE rules after the
existing `index.html` rule (the existing `scripts/` rule already includes the
new generator and test):
```json
{"match":"manifest.webmanifest","decision":"INCLUDE","reason":"PWA manifest"},
{"match":"sw.js","decision":"INCLUDE","reason":"PWA service worker"},
{"match":"icons/","decision":"INCLUDE","reason":"PWA icons"}
```

The service worker registers only over HTTPS or localhost, never `file://`.
Task 151's zip start scripts use localhost, so the installed app and offline
cache also work when the zip package is served locally.
