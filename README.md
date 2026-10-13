# Winona Daily News 2026 election-results relay

This repository is a no-cost relay between the Minnesota Secretary of State election-results files and the Winona Daily News BLOX HTML results asset.

## What it does

1. GitHub Actions runs server-side on a schedule.
2. `scripts/fetch_results.py` downloads the 15 approved Minnesota SOS result files.
3. It writes them into one `docs/results.json` bundle.
4. GitHub Pages serves that JSON publicly with browser-readable CORS behavior.
5. The BLOX HTML asset makes one request to the GitHub Pages JSON instead of trying to fetch Minnesota directly.

The relay preserves the last known good copy of a feed if Minnesota temporarily fails. The JSON marks that feed `stale: true` and records the fetch error.

## Setup — GitHub web interface

### 1. Create the repository

Create a **public** GitHub repository named:

`winona-election-results`

A public repository is intentional: it contains only public election data and code, and public repositories can use standard GitHub-hosted Actions runners without billable minutes.

### 2. Upload these files

Upload the entire package while preserving the directories:

- `.github/workflows/update-results.yml`
- `scripts/fetch_results.py`
- `docs/index.html`
- `docs/results.json`
- `.nojekyll`
- `.gitignore`
- `README.md`

If the GitHub web uploader does not make it convenient to upload hidden `.github` directories, create `.github/workflows/update-results.yml` with **Add file → Create new file** and type the full path into the filename field.

### 3. Enable GitHub Pages

Go to:

**Settings → Pages**

Under **Build and deployment**:

- Source: **GitHub Actions**

The scheduled workflow both creates the JSON bundle and deploys the `docs/` directory to Pages in the same run.

Your relay URL should become:

`https://YOUR-GITHUB-USERNAME.github.io/winona-election-results/results.json`

Pages deployment can take a short time after a commit.

### 4. Allow the workflow to write results

Go to:

**Settings → Actions → General → Workflow permissions**

Select:

**Read and write permissions**

Save the setting.

The workflow also declares `contents: write`, but repository policy must permit that write.

### 5. Run the first test manually

Go to:

**Actions → Update Minnesota election results → Run workflow**

Run it from `main`.

The workflow should:

- fetch the state test files;
- update `docs/results.json`;
- commit the updated file for last-known-good fallback;
- deploy the `docs/` directory directly to GitHub Pages in the same workflow run.

Open the repository's GitHub Pages home page. It should report the number of fresh feeds and provide a link to `results.json`.

### 6. Configure the BLOX asset

Open `blox/winona-election-results-blox-github-v1.html` and replace:

`YOUR-GITHUB-USERNAME`

with your GitHub username in `window.WDE_GITHUB_RESULTS_URL`.

Then paste that HTML into the BLOX HTML asset.

## Schedule

The workflow is configured for:

- one daily run at 10:17 a.m. Central during testing;
- every five minutes from 5 a.m. through 11:59 p.m. Central on Nov. 3;
- every five minutes from midnight through 2:59 a.m. Central on Nov. 4;
- manual runs at any time through **Actions → Run workflow**.

GitHub schedules can start later than the exact cron time under load. The Minnesota source itself updates periodically, so the relay is designed for near-live rather than second-by-second reporting.

## Important GitHub behavior

Scheduled workflows only run from the default branch. GitHub may automatically disable scheduled workflows in a public repository after 60 days with no repository activity. This repository will be active within 60 days of Nov. 3, 2026, but verify that the workflow is enabled before Election Day.

## Election-night checks

Before relying on the module publicly:

1. Confirm the workflow has a recent successful run.
2. Open the GitHub Pages status page and confirm most/all 15 feeds are fresh.
3. Open `results.json` and confirm `meta.generatedAt` is recent.
4. Confirm the BLOX results asset reports that the GitHub relay loaded.
5. Spot-check at least one federal, legislative, county, city and school race against the Minnesota SOS site.

## Files fetched from Minnesota SOS

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

The relay is deliberately restricted to those files; it is not an open proxy.
