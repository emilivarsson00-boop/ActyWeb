const GA_MEASUREMENT_ID = "G-PC2BD74DD2";
const CONSENT_KEY = "actyweb-cookie-consent";

function loadGoogleAnalytics() {
  if (window.actywebAnalyticsLoaded) {
    return;
  }

  window.actywebAnalyticsLoaded = true;
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };

  window.gtag("js", new Date());
  window.gtag("config", GA_MEASUREMENT_ID, { anonymize_ip: true });

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);
}

function injectConsentStyles() {
  if (document.querySelector("#actyweb-consent-style")) {
    return;
  }

  const style = document.createElement("style");
  style.id = "actyweb-consent-style";
  style.textContent = `
    .actyweb-consent {
      position: fixed;
      right: 14px;
      bottom: 14px;
      left: 14px;
      z-index: 1000;
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 14px;
      align-items: center;
      width: min(960px, calc(100% - 28px));
      margin: 0 auto;
      padding: 14px;
      border: 1px solid #cbd6cf;
      border-radius: 8px;
      background: #f3f6f2;
      color: #18201d;
      box-shadow: 0 14px 28px rgba(24, 32, 29, 0.12);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    }

    .actyweb-consent p {
      margin: 0;
      color: color-mix(in srgb, #18201d 64%, #f3f6f2);
      font-size: 0.95rem;
      font-weight: 620;
      line-height: 1.45;
    }

    .actyweb-consent__actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }

    .actyweb-consent button {
      min-height: 40px;
      padding: 9px 13px;
      border: 1px solid #cbd6cf;
      border-radius: 7px;
      background: transparent;
      color: #18201d;
      font: inherit;
      font-weight: 850;
      cursor: pointer;
    }

    .actyweb-consent button[data-consent="accepted"] {
      border-color: #18201d;
      background: #18201d;
      color: #f3f6f2;
    }

    .actyweb-consent button:focus-visible {
      outline: 2px solid #6f7f67;
      outline-offset: 3px;
    }

    @media (max-width: 680px) {
      .actyweb-consent {
        grid-template-columns: 1fr;
      }

      .actyweb-consent__actions {
        justify-content: stretch;
      }

      .actyweb-consent button {
        flex: 1;
      }
    }
  `;
  document.head.appendChild(style);
}

function showConsentBanner() {
  injectConsentStyles();

  const banner = document.createElement("div");
  banner.className = "actyweb-consent";
  banner.setAttribute("role", "dialog");
  banner.setAttribute("aria-label", "Samtycke till analyscookies");
  banner.innerHTML = `
    <p>ActyWeb använder analysverktyg för att förstå hur hemsidan används och förbättra upplevelsen. Genom att fortsätta godkänner du användningen av analyscookies.</p>
    <div class="actyweb-consent__actions">
      <button type="button" data-consent="accepted">Godkänn</button>
      <button type="button" data-consent="declined">Avvisa</button>
    </div>
  `;

  banner.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-consent]");
    if (!button) {
      return;
    }

    const choice = button.dataset.consent;
    localStorage.setItem(CONSENT_KEY, choice);
    banner.remove();

    if (choice === "accepted") {
      loadGoogleAnalytics();
    }
  });

  document.body.appendChild(banner);
}

const consent = localStorage.getItem(CONSENT_KEY);

if (consent === "accepted") {
  loadGoogleAnalytics();
} else if (consent !== "declined") {
  showConsentBanner();
}
