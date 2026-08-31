# EVAL-SPLIT-001 — frozen split manifest

Split `gold150-v1`, frozen 2026-08-31T22:30:29Z.

| | |
| --- | --- |
| seed | `689336380` |
| algorithm | `eval-split-001/v1` |
| corpus snapshot | `snap_689e336380a054d8039dc35b2c09cd0a` |
| gold version | GOLD-001 (150 human_verified) |
| development | 20 cases, sha256 `e62670f38a0afaad…` |
| validation | 40 cases, sha256 `451963bdf379cef1…` |
| holdout | 90 cases, sha256 `756a3a9bc74ce3e2…` |
| contamination audit | `e3711444cec75a89…` |
| fact clusters | `57f01048478d5bf3…` |
| holdout frozen | **True** |

## Holdout lock

Holdout membership may not change because of system performance. A failure found during engineering goes to the challenge-candidate queue, never into or out of this set.

A holdout case later shown to be objectively invalid is recorded as a benchmark erratum and retained. It is never silently replaced.
