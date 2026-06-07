# ActyWeb intern README

Denna README är för utvecklare och framtida underhåll. Den är inte skriven för kunder.

## Projektöversikt

- ActyWeb bygger enkla hemsidor åt lokala småföretag.
- Fokus är statiska hemsidor.
- Kunden ska alltid kunna få filerna.
- Sidorna ska vara enkla att hosta, flytta och underhålla.

## Grundprinciper

- Kunden äger hemsidan.
- Kunden ska inte låsas in.
- Kunden ska kunna flytta sidan till valfri leverantör.
- ActyWeb ska inte bli ett webbhotell.
- ActyWeb ska inte kräva konto, backend eller specialmiljö för enkla kundsidor.

## Hosting

Nuvarande arkitektur:

```text
Besökare
→ Cloudflare
→ GitHub Pages
→ Statiska filer
```

Detta projekt ska kunna fungera som statisk site utan backend. Håll rotprojektet kompatibelt med GitHub Pages.

## Säkerhet

Får inte ligga i repot:

- API-nycklar
- lösenord
- .env-filer
- databaskopplingar
- SMTP-uppgifter
- kunddata
- privata dokument

Lägg inte in personliga tokens, privata kundunderlag eller exportfiler från externa system. Om något sådant behövs i arbetet ska det hanteras utanför repot.

## Framtida backend

Om backend behövs, använd extern tjänst:

- Cloudflare Workers
- Supabase
- Formspree/Web3Forms
- Render/Railway

Ingen backend ska köras från utvecklarens egen dator.

Ingen port forwarding.

Undvik egen serverdrift om en statisk lösning eller enkel tredjepartstjänst räcker.

## Designfilosofi

Undvik:

- SaaS-känsla
- startup-design
- generiska kort
- överdriven whitespace
- AI-mallkänsla

Föredra:

- kundens identitet
- riktiga bilder
- tydliga telefonnummer
- praktisk information
- kort copy
- tydliga kontaktvägar

Målet är:

> Det här ser ut som vårt företag.

Inte:

> Det här ser ut som en AI-genererad mall.

## KILAB-lärdom

Försök inte göra industriföretag till startup-sidor.

Använd företagets befintliga identitet och tonalitet. Om företaget redan har färger, logotyp, bildspråk eller ett sätt att uttrycka sig ska sidan bygga på det i stället för att ersätta det med en generisk mall.

## Projektstruktur

```text
/
├── index.html
├── style.css
├── script.js
├── README.txt
├── assets/
│   └── images/
├── demos/
│   ├── blackrum/
│   ├── futura/
│   ├── hugos/
│   ├── kilab/
│   └── niffes/
```

### Rotfiler

- `index.html` är ActyWebs startsida.
- `style.css` innehåller layout, färger, typografi och responsiv design för startsidan.
- `script.js` innehåller enkel klientlogik, till exempel mobilmeny och årtal i footer.
- `README.txt` är denna interna README.

### assets/

Gemensamma assets för ActyWebs egen startsida.

- `assets/images/actyweb-wordmark-green-transparent.png` används som huvudlogga i navbaren.
- `assets/images/actyweb-logo-dark.png` används som favicon och liten footer-logga.
- `assets/images/actyweb-truck-badge.png` är arbetsmaterial. Den används inte på huvudsidan just nu.
- `assets/images/actyweb-truck-logo-dark-source.png` används som hero-badge ovanför erbjudanderutan.
- `assets/images/actyweb-truck-logo-badge-tight.png` är en tidigare crop och används inte just nu.
- Äldre truck- och mascot-assets finns kvar som arbetsmaterial, men används inte på huvudsidan just nu.
- `assets/images/actyweb-logo.png` och äldre logo-assets är arbetsmaterial. Undvik att upprepa full-loggan i innehållskort.

Lägg bara generella ActyWeb-assets här. Kundspecifika bilder ska ligga under respektive demo.

### demos/

Varje undermapp är en separat statisk demosida.

Exempel:

- `demos/kilab/`
- `demos/blackrum/`
- `demos/niffes/`
- `demos/hugos/`
- `demos/futura/`

Varje demo bör kunna fungera fristående med egna:

- `index.html`
- `style.css`
- `script.js`
- `assets/images/`
- eventuell demo-specifik `README.txt`

Demo-URL:er bör följa enkel struktur:

```text
/demos/foretagsnamn/
```

### screenshots/

Screenshots behövs normalt inte för ActyWebs huvudsida vid varje revision.

För kundsidor/demos kan screenshots sparas under respektive demo när sidan börjar bli färdig. Dessa är arbetsmaterial, inte kunddata.

Används för att snabbt kontrollera:

- desktop
- mobil
- hero
- exempel/demos
- kontakt

## Copyregler

- Skriv kort.
- Skriv konkret.
- Undvik webbyråfloskler.
- Förklara pris och ägande tydligt.
- Skriv hellre "HEMSIDAN GRATIS" eller "HEMSIDAN ÄR KOSTNADSFRI" än otydliga gratisformuleringar.
- Var tydlig med att 1499 kr är hjälp med uppsättning, inte priset på hemsidan.

## Teknisk riktning

Standard för ActyWeb-sidor:

- HTML
- CSS
- JavaScript
- statiska filer
- GitHub Pages-kompatibelt

Undvik om det inte finns ett tydligt behov:

- React
- Next.js
- backend
- databas
- byggsteg
- serverberoenden

Prioritet är att kunden ska kunna få en mapp med filer och använda sidan själv.
