# Winona Daily News 2026 election-results relay

This repository provides the no-cost data relay used by the Winona Daily News 2026 general-election results module.

## Current production architecture

1. GitHub Actions runs server-side on a schedule.
2. `scripts/fetch_results.py` downloads 15 approved Minnesota Secretary of State result files.
3. The script consolidates those feeds into `docs/results.json`.
4. GitHub Pages publishes the JSON as a browser-readable public endpoint.
5. The Winona Daily News BLOX HTML asset makes one request to the GitHub Pages JSON rather than trying to fetch Minnesota directly.

This relay exists because the Minnesota result-file host does not allow the BLOX page to read the files directly through browser JavaScript because of cross-origin restrictions.

## Production URLs

Repository:

`https://github.com/toddc172/winona-election-results`

GitHub Pages status page:

`https://toddc172.github.io/winona-election-results/`

Results JSON consumed by BLOX:

`https://toddc172.github.io/winona-election-results/results.json`

## Current validation status

The BLOX results manifest contains 83 configured races/questions.

Latest completed mapping validation:

- 83 matched
- 0 unmatched
- 0 ambiguous
- 0 feed errors

The relay has also successfully loaded all 15 Minnesota result feeds with no stale or unavailable feeds during testing.

## Minnesota result files fetched

The relay is restricted to these 15 public Minnesota SOS files:

- `ussenate.txt`
- `ushouse.txt`
- `Governor.txt`
- `secofstate.txt`
- `auditor.txt`
- `attorneygen.txt`
- `stsenate.txt`
- `LegislativeByDistrict.txt`
- `cntyRaces.txt`
- `local.txt`
- `sdrace.txt`
- `judicial.txt`
- `judicialdst.txt`
- `ConstAmend.txt`
- `SDRaceQuestions.txt`

The relay is not an open proxy.

## Update schedule

All scheduled times use `America/Chicago`.

### Normal testing cadence

- Daily at **10:11 a.m. Central**.

### Election Day — Tuesday, Nov. 3, 2026

- **5 a.m.-6:59 p.m.:** every 15 minutes.
- **7 p.m.-11:59 p.m.:** every 5 minutes.

Minnesota polls close at 8 p.m. Central.

### Post-election — Wednesday, Nov. 4, 2026

- **Midnight-5:59 a.m.:** every 5 minutes.
- **6 a.m.-11:59 a.m.:** every 15 minutes.
- **12:02 p.m.:** one final scheduled check.

The workflow can also be run manually at any time through:

**Actions → Update Minnesota election results → Run workflow**

GitHub scheduled workflows can occasionally start later than their exact scheduled time under platform load.

## Last-known-good protection

If a Minnesota feed temporarily fails, `fetch_results.py` preserves the previous good copy of that feed rather than replacing it with empty or invalid data.

The JSON identifies feed health so the BLOX asset can distinguish:

- fresh feeds;
- cached/stale feeds;
- unavailable feeds.

The public BLOX status line uses one timestamp concept throughout:

- `Last updated: [time]` when all feeds are healthy;
- `Results may be delayed. Last updated: [time]` when a feed is stale;
- `Some results are temporarily unavailable. Last updated: [time]` when a feed is unavailable;
- `Live results are temporarily unavailable. Last updated: [last successful time]` if the relay cannot be reached after a prior successful load.

## BLOX results behavior

The production BLOX asset:

- displays all 83 configured races/questions;
- shows candidate names even before results are reported;
- shows party affiliation where applicable;
- marks incumbents with `(I)`;
- displays precincts reporting, total precincts and reporting percentage;
- displays candidate vote totals and percentages;
- displays total votes counted;
- displays write-in totals when returned by the SOS feed;
- shows full ballot-question text;
- automatically refreshes the GitHub JSON every 60 seconds while the page is open;
- supports manual winner calls before all precincts report;
- automatically determines winners when 100% of precincts report.

## Winner checkmarks

A green checkmark indicates a winner/called winner.

### Before 100% reporting

A newsroom editor can manually mark a called winner through `WDE_MANUAL_WINNERS` in the BLOX HTML asset.

The manual-reference block contains only contested candidate races and ballot questions to make election-night editing easier. Uncontested candidate races are omitted from the manual reference.

### At 100% reporting

Automatic SOS-based winner logic takes precedence over any lingering manual override.

- Single-seat races: highest vote total receives the checkmark.
- Multi-seat races: the top `electN` candidates receive checkmarks.
- A tie at the deciding position produces no automatic winner checkmark at that cutoff.
- Ballot questions use the reported YES/NO totals.

This means staff do not need to remove manual calls for the final automatic result to take control once all precincts have reported.

## Newsroom manual winner workflow

Inside the BLOX HTML asset, find:

`window.WDE_MANUAL_WINNERS`

The commented reference immediately above that block contains the exact current race IDs and candidate names for contested races.

For a single-winner race:

```js
window.WDE_MANUAL_WINNERS = {
  "race-id": "Candidate Name"
};
```

For a multi-seat race:

```js
window.WDE_MANUAL_WINNERS = {
  "race-id": ["Winner 1", "Winner 2"]
};
```

For ballot questions, use `"YES"` or `"NO"`.

Manual overrides are intended only for races called before 100% of precincts report.

## GitHub Pages configuration

Repository setting:

**Settings → Pages → Source: GitHub Actions**

The workflow both updates `docs/results.json` and deploys the `docs/` directory to GitHub Pages.

Required workflow permissions:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

The workflow uses a concurrency group with `cancel-in-progress: true` to prevent overlapping update/deployment runs.

## Key repository files

- `.github/workflows/update-results.yml` — polling and Pages deployment schedule.
- `scripts/fetch_results.py` — Minnesota SOS fetch/consolidation logic.
- `docs/results.json` — current consolidated relay output.
- `docs/index.html` — relay status page.
- `docs/.nojekyll` — disables Jekyll processing for the Pages artifact.
- `blox/` — reference copies of BLOX HTML assets.
- `newsroom-manual-winner-reference.txt` — newsroom reference material.

## Election-night verification checklist

Before polls close:

1. Confirm the most recent GitHub Actions run succeeded.
2. Open the GitHub Pages status page and confirm all 15 feeds are fresh.
3. Open `results.json` and confirm its generated timestamp is current.
4. Confirm the live BLOX asset shows a recent `Last updated` time.
5. Spot-check a federal, legislative, county, city, school and judicial race against the Minnesota SOS site.
6. Confirm the manual-winner reference is present in the BLOX production asset.
7. Confirm the GitHub scheduled workflow remains enabled.

When Minnesota switches from test results to unofficial/live results, the relay and BLOX asset should begin displaying those values automatically without a code change, provided the SOS file structure remains unchanged.

## Maintenance notes

- GitHub may disable scheduled workflows in a public repository after 60 days with no repository activity. Verify the workflow remains enabled before Election Day.
- Do not replace the GitHub Pages relay with a public third-party CORS proxy.
- Do not put credentials or private information in this public repository.
- If the Minnesota SOS changes its file names or schema before Election Day, update the fetch script and re-run the 83-race mapping validation before relying on the module publicly.
