# Property scraper

En liten lokal scraper for bostadsannonser. Den hamtar publik HTML, plockar ut
brodtext och bild-URL:er, och sparar resultatet som Markdown och JSON.

## Grafiskt lage

Dubbelklicka pa:

```text
tools/start_property_scraper.cmd
```

Dar far du en textruta for annonslankar, en Scrape-knapp, Clear och en knapp
som oppnar output-mappen. Som standard sparas resultatet i `scrapes/`.

GUI:t laddar ned bilder och skapar en zip-fil automatiskt for varje annons, sa
du kan ladda upp hela zippen direkt i ChatGPT.

Du kan ocksa starta direkt med:

```powershell
python .\tools\property_scraper_gui.py
```

Tray-lage aktiveras automatiskt om `pystray` finns installerat:

```powershell
python -m pip install pystray
```

Utan `pystray` fungerar appen anda, men "Dolj" minimerar bara fonstret.

## Korning

```powershell
python .\tools\property_scraper.py "https://exempel.se/annons"
```

Resultatet hamnar i `scrapes/<annonsnamn>/`:

- `listing.md` - enklast att ladda upp i ChatGPT
- `listing.json` - strukturerad version

Vill du aven ladda ned bilder lokalt:

```powershell
python .\tools\property_scraper.py "https://exempel.se/annons" --download-images
```

Flera URL:er samtidigt:

```powershell
python .\tools\property_scraper.py `
  "https://exempel.se/annons-1" `
  "https://exempel.se/annons-2" `
  --download-images
```

## Viktigt

- Anvand bara publika sidor du far besoka.
- Verktyget kontrollerar `robots.txt` och avbryter om sidan inte tillater
  hamtning for den User-Agent som anvands.
- Forsok inte kringga inloggning, captcha, robots.txt eller betalvaggar.
- Kor lugnt och sporadiskt. Verktyget ar gjort for enstaka annonser, inte
  mass-skrapning.
- Vissa sidor renderar text/bilder med JavaScript efter sidladdning. Da kan den
  har enkla scrapern fa mindre innehall an du ser i webblasaren.
