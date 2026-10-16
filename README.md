# Winona Daily News 2026 election-results relay

This repository supports the Winona Daily News live 2026 general-election results module.

The system retrieves unofficial election-result files from the Minnesota Secretary of State, publishes browser-readable JSON through independent GitHub and Microsoft Azure paths, and feeds the BLOX HTML results asset used on winonadailynews.com.

## Current status

- Election: Minnesota State General Election
- Election date: Nov. 3, 2026
- Minnesota SOS election ID: `201`
- Configured races/questions: `83`
- Minnesota SOS feeds: `15`
- Last full mapping validation: `83 matched / 0 unmatched / 0 ambiguous`
- Current BLOX architecture: active-active GitHub + Azure
- Current BLOX code version: `v23`
- Stale-data threshold: `30 minutes`

Results remain unofficial until canvassed and certified.

---

# Architecture

The system has two independent server-side collection paths.

```text
                   Minnesota Secretary of State
                         /             \
                        /               \
               GitHub Actions       Azure Pipelines
                     |                    |
                GitHub Pages       Azure Static Web Apps
                       \              /
                        \            /
                     BLOX HTML asset
                 fetches both in parallel
                           |
                 compares meta.generatedAt
                           |
                  uses freshest valid bundle
                           |
                   raw GitHub fallback
                           |
                browser last-good snapshot
                           |
                    candidate roster
```

The GitHub and Azure collection paths independently retrieve Minnesota SOS data. Azure does not depend on GitHub for live election-result collection, and GitHub does not depend on Azure.

This provides protection against:

- delayed GitHub scheduled workflows;
- GitHub Pages serving/deployment failures;
- Azure pipeline or Static Web Apps failures;
- temporary Minnesota SOS feed failures;
- a stalled browser request;
- temporary browser inability to reach either primary relay;
- stale result bundles.

---

# Public result endpoints

## GitHub Pages

```text
https://toddc172.github.io/winona-election-results/results.json
```

## Azure Static Web Apps

```text
https://agreeable-ground-0f0ceab10.5.azurestaticapps.net/results.json
```

## Raw GitHub fallback

```text
https://raw.githubusercontent.com/toddc172/winona-election-results/main/docs/results.json
```

The BLOX asset requests GitHub Pages and Azure Static Web Apps in parallel and normally
