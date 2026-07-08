# Richart.app Auto-Twitter-Bot

Vollautomatischer X-Bot für [richart.app](https://richart.app): generiert täglich 10–12 englische Tweets über deine Bitcoin-Ordinals-Kollektionen und postet sie über die X-API — gesteuert durch GitHub Actions.

## Was der Bot macht

1. Wählt rotierend eine Kollektion aus `collections.yaml`
2. Generiert einen einzigartigen Tweet via OpenAI
3. Prüft auf Duplikate gegen `data/history.json`
4. Postet auf X (mit Link)
5. Speichert den Tweet in der History (Git commit via GitHub Actions)

## Kosten (realistisch)

| Posten | Kosten |
|---|---|
| X-API (~330 URL-Posts/Monat × $0,20) | **~$66/Monat** |
| OpenAI (gpt-4o-mini) | **~$1–3/Monat** |
| GitHub Actions (public Repo) | **$0** |
| **Gesamt** | **~$67–70/Monat** |

Quelle: [X API Pricing](https://docs.x.com/x-api/getting-started/pricing) — Posts mit URL kosten $0,20 pro Tweet.

Startguthaben-Empfehlung: **$20** in der X Developer Console (reicht für ~100 URL-Tweets).

## Voraussetzungen

- Python 3.12+
- [OpenAI API Key](https://platform.openai.com)
- [X Developer Account](https://developer.x.com) mit Credits
- GitHub-Account (public Repo für kostenlose Actions)

---

## 1. X-API einrichten

1. Gehe zu [developer.x.com](https://developer.x.com) und erstelle ein Projekt + App
2. Unter **User authentication settings**:
   - OAuth 1.0a aktivieren
   - **Read and write** Permissions
   - Callback URL: `https://localhost/`
3. Notiere diese vier Werte:
   - API Key (Consumer Key) → `X_API_KEY`
   - API Key Secret → `X_API_SECRET`
   - Access Token → `X_ACCESS_TOKEN`
   - Access Token Secret → `X_ACCESS_TOKEN_SECRET`
4. Kaufe Credits in der Developer Console (Pay-per-Use, kein Abo)

## 2. OpenAI API Key

1. [platform.openai.com](https://platform.openai.com) → API Keys
2. Key erstellen → `OPENAI_API_KEY`

## 3. Lokal testen

```powershell
cd c:\Users\thoma\Documents\twitter-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Trage deine Keys in `.env` ein, dann:

```powershell
# Tweet generieren, NICHT posten (braucht nur OPENAI_API_KEY)
python main.py --dry-run

# Einen echten Tweet posten (Test)
python main.py
```

## 4. GitHub Repository

1. Erstelle ein **public** Repo auf GitHub (z. B. `twitter-bot`)
2. Push dieses Projekt:

```powershell
git init
git add .
git commit -m "Initial richart.app twitter bot"
git remote add origin https://github.com/DEIN-USER/twitter-bot.git
git push -u origin main
```

3. Unter **Settings → Secrets and variables → Actions** diese Secrets anlegen:

| Secret | Wert |
|---|---|
| `OPENAI_API_KEY` | OpenAI API Key |
| `X_API_KEY` | X Consumer Key |
| `X_API_SECRET` | X Consumer Secret |
| `X_ACCESS_TOKEN` | X Access Token |
| `X_ACCESS_TOKEN_SECRET` | X Access Token Secret |
| `BOT_GITHUB_TOKEN` | GitHub PAT mit `contents: write` Scope |

**BOT_GITHUB_TOKEN erstellen:**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Fine-grained token: Repository access auf dein `twitter-bot` Repo
3. Permissions: **Contents: Read and write**

## 5. Zeitplan

Der Bot postet **5× täglich**, verteilt über den **US-Tag** (GitHub Actions nutzt UTC):

| UTC | US Eastern (EDT) | US Pacific (PDT) |
|---|---|---|
| 13:00 | 9:00 AM | 6:00 AM |
| 16:00 | 12:00 PM | 9:00 AM |
| 19:00 | 3:00 PM | 12:00 PM |
| 22:00 | 6:00 PM | 3:00 PM |
| 01:00 | 9:00 PM | 6:00 PM |

Zeiten anpassen: bearbeite `schedule_utc` in `config.yaml` **und** die `cron`-Einträge in `.github/workflows/tweet.yml`.

Manueller Test in GitHub: **Actions → Post Tweet → Run workflow**.

---

## Kollektionen (Priorität)

Der Bot rotiert durch diese 5 Kollektionen auf richart.app:

| Kollektion | URL |
|---|---|
| Primal Club | richart.app/primal-club |
| Bad Cats | richart.app/badcats |
| High Rollers | richart.app/high-rollers |
| Spikes | richart.app/spikes |
| Bitcoin Mixtape | richart.app/bitcoin-mixtape |

Inhalte und Stil basieren auf deinen bisherigen Posts als @richbi11. Anpassen in `collections.yaml` und `prompts/system.txt`.

### `prompts/system.txt`
Ton und Regeln für die KI (Englisch, kein Spam, Link-Pflicht).

---

## Projektstruktur

```
twitter-bot/
├── main.py
├── config.yaml
├── collections.yaml
├── prompts/system.txt
├── src/
│   ├── config_loader.py
│   ├── generate.py
│   ├── post.py
│   └── dedup.py
├── data/history.json
├── requirements.txt
└── .github/workflows/tweet.yml
```

---

## Compliance

- Der Bot postet **nur eigene Inhalte** über deinen Account
- Kein automatisches Lesen fremder Posts oder Auto-Replies (spart Kosten + ToS-Risiko)
- Automation muss der [X Developer Policy](https://developer.x.com/en/developer-terms/agreement-and-policy) entsprechen

---

## Fehlerbehebung

| Problem | Lösung |
|---|---|
| `Missing environment variable` | `.env` oder GitHub Secrets prüfen |
| `403 Forbidden` von X | App-Permissions auf Read+Write, Tokens neu generieren |
| `Insufficient credits` | Credits in X Developer Console aufladen |
| Workflow postet nicht | Repo muss public sein; Cron kann bis 15 Min verzögert starten |
| History commit schlägt fehl | `BOT_GITHUB_TOKEN` mit write-Permission prüfen |

---

## Spätere Erweiterungen

- Bilder mitposten
- Performance-Analyse (Achtung: Lesekosten!)
- Auto-Replies
- Mehrere Accounts
