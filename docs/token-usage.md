# Token usage study

**One completed synthetic revision used 4,555,808 reported tokens across 87 model
responses. The main agent, acting as editor, accounted for 75.8%. Cache reads
accounted for 93.4% of input tokens.** This is a measured calibration case, not an
estimate of the average research paper or a billing statement.

The repository has six child roles: four specialists, a student, and a fresh final
auditor. The main agent also acts as editor; there is no extra editor agent.
Repeated dispatches and model responses matter more than the number of role names.
This run used ten child sessions: four initial reviewers, one student, four
verification reviewers, and one auditor, plus the main session.

## Evidence and scope

The study reads saved native Codex usage records from a completed run on
2026-09-21. No new review runs were launched. All sessions report Codex 0.155.1
and model `gpt-6-astra`. The manuscript is byte-identical to the shipped
[Markdown fixture](../fixtures/manuscript.md): 92 whitespace-delimited words,
with deliberately planted errors. The saved run reports `PASS_INTERNAL`, two
rounds, ten dispatches, and one audit. That outcome concerns a synthetic identity
check, not scientific peer-review quality.

The repository's fixture checker was rerun for this study: all twelve recorded
artifact gates passed. Its [result](data/token-usage/fixture-check.json) and
[provenance](data/token-usage/provenance.json) retain the scope and limitations.

Selection starts from the fixture's main session and includes all ten directly
linked native child sessions. The helper's completed-task count and dispatch
budget counter both equal ten. All child spawns requested `fork_turns="none"`.
One unsuccessful spawn attempt did not produce an additional child session; any
main-session work surrounding that attempt remains counted. Setup/discovery
sessions, unrelated local work, and the cost of producing this study are excluded.
External tool-service charges and inference not recorded in these logs are outside
the measurement.

This is a convenience sample of **one short, successful Markdown run on one
host/model configuration**. It has no repeats, full-length papers, matched
single-agent control, Claude measurements, or randomized intervention. It cannot
support a population mean, confidence interval, quality-per-token comparison, or
causal claim that a particular tool or instruction caused the observed usage.
The measured configuration also includes local instructions and tool definitions;
it does not isolate the bare AMR skill overhead.

## Accounting method

The [exporter](../scripts/token_usage.py) reads an explicit private manifest of
session files. It uses the per-response `token_usage_record.payload.usage` fields,
deduplicates by response ID within a session, and requires their sum to equal the
last cumulative `token_count` record for **every** session. All eleven sessions
reconcile. Parent linkage and native child roles are checked. Cumulative counters
are a cross-check, never another term added to the total. Missing response data,
conflicting duplicates, malformed records, or mismatched totals cause failure.
Older logs without per-response records are unsupported by this exporter.

Each response belongs to its recorded thread. The editor's per-response sum
matches its own cumulative counter independently of the children's counters, so
adding the eleven distinct session totals does not count the child totals twice.
The manifest must cover the complete run and use dedicated run sessions: the
exporter cannot discover omitted children or separate unrelated tasks inside a
shared editor session. Inspect dispatch records before treating an export as a
complete run. Phase labels come from that inspection; the main session spans all
phases and is not assigned artificially to individual rounds.

`total_tokens = input_tokens + output_tokens`. Cache-read and cache-write tokens
are subsets of input. Reasoning tokens are a subset of output, not a third amount
to add. OpenAI documents the cache and reasoning distinction in its
[prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching)
and [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).
The study preserves the recorded fields; it does not reconstruct tokens from
visible prose or infer missing usage from word counts.

Only an allowlist is exported: role/phase labels, relative completion times,
model/client version, numeric usage, and SHA-256 hashes of source logs. Native IDs,
paths, manuscript text, prompts, responses, account limits, and credentials remain
private. The [sanitized per-response data](data/token-usage/observed.json) permit
independent recomputation of every total and plot. Source hashes permit a local
custodian to check identity, but do not make the private transcripts publicly
verifiable. This is an observational report, not independently audited billing.

## Measured results

| Role | Sessions | Responses | Input | Cache-read input | Output | Total |
|---|---:|---:|---:|---:|---:|---:|
| Main/editor | 1 | 48 | 3,437,896 | 3,339,008 | 16,686 | 3,454,582 |
| Mathematics | 2 | 10 | 280,674 | 239,616 | 2,771 | 283,445 |
| Methods | 2 | 9 | 232,024 | 212,096 | 2,545 | 234,569 |
| Evidence | 2 | 8 | 219,723 | 175,744 | 2,797 | 222,520 |
| Communication | 2 | 4 | 103,199 | 49,408 | 2,034 | 105,233 |
| Student | 1 | 6 | 200,886 | 174,208 | 1,499 | 202,385 |
| Fresh auditor | 1 | 2 | 52,001 | 36,992 | 1,073 | 53,074 |
| **All** | **11** | **87** | **4,526,403** | **4,227,072** | **29,405** | **4,555,808** |

![Measured tokens by role](figures/token-usage/roles.svg)

The other input consists of 299,331 uncached tokens and zero reported cache-write
tokens. Output includes 1,079 reasoning tokens. Uncached input plus output is
328,736 tokens, but **that is not the billed total**: cache reads may also have a
charge. Nor is the 4.56 million total the size of a single context window or the
number of unique words processed.

The editor made 48 responses. Its first recorded input was 24,409 tokens and its
last was 95,899 tokens, despite the tiny manuscript. Every request can include
instructions, tool schemas, previous conversation, and tool results. Repeated
input dominates this run: output is only 0.65% of the token total. Cache reuse
reduces the cost of repeated input under applicable tariffs; it does not remove
those tokens from reported input volume.

![Cumulative tokens and per-response input](figures/token-usage/timeline.svg)

The horizontal axis uses response completion times relative to the first response.
It is not active compute time or per-call latency; concurrent children overlap.
The curve covers about 13.3 minutes after the first response. The per-response
plot makes the editor's expanding input visible without claiming which prompt
component caused it. The auditor consumed about 1.2% of total tokens in this run;
removing independent audit would sacrifice a core safeguard for a small observed
share. Review length or difficulty could change that share in another run.

## What might an ordinary paper cost?

**There is not enough evidence to give a measured typical-paper number.** A
full-length paper adds source, references, figures, evidence checks, and potentially
more revision rounds. Those variables can increase both the number of responses
and the input per response. A fixed “seven agents times paper length” calculation
misses repeated context, orchestration, and verification.

The [generated summary](data/token-usage/summary.json) includes a conditional
sensitivity calculation anchored to this fixture. It is a planning model, not a
forecast or an upper bound. Its assumptions are:

- Each round contains all four specialist reviews. Every round after the first
  contains one student dispatch. There is exactly one final audit. Thus rounds
  one through four use 5, 10, 15, and 20 child dispatches, respectively. A one-round
  scenario has no student revision and serves only as a reference case.
- Initial reviewers, each later reviewer wave, each student revision, and the
  auditor retain their respective measured token and response totals. Editor
  usage and response count scale linearly with rounds, anchored at two rounds.
- An additional 0, 4,000, 8,000, or 16,000 manuscript tokens appears in 25%, 50%, or
  100% of modeled requests. Each affected request adds that many input tokens.
  Output length and response count do not change because of added text.
- No retries, extra audits, context truncation, new tools, or new evidence work
  are added. Model/provider behavior and review difficulty remain fixed.

For reproduction, the modeled baseline is the initial-review total plus the audit
total, plus `(rounds - 1)` times the sum of student and verification totals, plus
`rounds / 2` times the editor total. Apply the same construction to response counts.
Then add `modeled responses × exposure fraction × added manuscript tokens`.
The two-round, zero-added-text case exactly recovers the measured total.

![Conditional round and source-length sensitivity](figures/token-usage/sensitivity.svg)

The figure shows 100% exposure; all three exposure assumptions are retained in
JSON. With two rounds, adding 8,000 tokens to every response adds 696,000 input
tokens, giving 5,251,808 total tokens. At 25% exposure it adds 174,000, giving
4,729,808. These are alternative assumptions, not error bars. Real long-paper
runs may require many more responses, and persistent editor history can make
round growth faster than this linear model. The default 32-dispatch and four-round
limits are not token caps: they do not bound the number or size of model responses
inside a dispatch. Concurrency limits primarily schedule work and do not directly
limit the sum of tokens.

## Cache and money sensitivity

For API-like accounting, multiply uncached input, cache-read input, cache-write
input, and output by their respective applicable rates, then sum them. If rates
are quoted per million tokens, divide each token count by one million. Use the
actual model, service tier, context-length tier, and date. Do not add reasoning
again. This report does not supply current dollar rates or infer a subscription
credit conversion from API prices.

![Conditional cache-cost sensitivity](figures/token-usage/cache.svg)

This what-if holds the measured input/output counts fixed. One unit is the charge
for one million uncached input tokens; output is assumed to cost six times as much
per token. The three cache-read rates are hypothetical ratios. Cache writes remain
zero, as reported in this run. At a cache-read ratio of 0.1 and the observed hit
fraction, relative cost is 0.898 units, compared with 4.703 at zero hits: 80.9% lower
under these assumptions. This is not an observed bill or a prediction that disabling
caching would leave the workload unchanged. Cache availability and write pricing
must be checked for the actual deployment.

## How to use fewer tokens without weakening the review

The measured editor share makes orchestration the first place to investigate.
These are testable hypotheses, not measured savings:

1. Read bounded, relevant file sections and return compact tool summaries. Keep
   full evidence in files with hashes and paths instead of repeatedly printing it.
2. Keep the editor's issue ledger concise and stable. Reference verified artifacts
   rather than copying whole reviewer reports into later messages.
3. Keep specialists independent and the auditor fresh. This run already used no
   history fork for all children; do not claim that switching to that policy would
   save the measured baseline again. Shared host/tool context can remain large.
4. Bundle independent read-only checks when useful. Do not omit verification or
   close findings merely to avoid a model response. Batch size is a tradeoff:
   large tool output can increase subsequent input even if calls decrease.
5. Measure after changing model, reasoning effort, instructions, or tool inventory.
   A cheaper model or shorter prompt is not a demonstrated quality-preserving
   improvement until the same acceptance and evidence gates still hold.

No agent definitions, prompts, acceptance gates, runtime logic, default limits, or
installation behavior were changed for this study. Plot dependencies are optional
analysis dependencies, not new runtime requirements.

## Reproduce and extend

The plots used Python 3.10.20 and Matplotlib 3.10.8 in the local analysis environment.
From the repository root, with Matplotlib and NumPy available (optional versions
are specified in `requirements-analysis.txt`, also included by the development
requirements):

```sh
python scripts/plot_token_usage.py
python -m pytest -q tests/test_token_usage.py
```

The script writes four figures in SVG, EPS, PNG, and PDF, plus `summary.json`.
The repository tracks SVG/EPS figures; PNG/PDF exports are generated locally and
ignored by Git to preserve the existing text-based publication checks.
No inference calls, private files, or network access are needed to regenerate them.
Export formats can differ in metadata across environments; compare numeric data
and figure content rather than expecting identical binary hashes.

For a new measured run, retain its main and child session logs privately. Make a
private JSON manifest with one record per session, for example:

```json
[
  {"path": "/path/to/editor.jsonl", "role": "editor", "phase": "all"},
  {"path": "/path/to/math.jsonl", "role": "math", "phase": "initial"}
]
```

This two-entry example is incomplete for a full AMR run. Add every child session,
including retries and repeated specialists. Allowed roles are `editor`, `math`,
`methods`, `evidence`, `communication`, `student`, and `auditor`; phases are `all`,
`initial`, `revision`, `verification`, and `audit`. Then run:

```sh
python scripts/token_usage.py /path/to/private-manifest.json /path/to/usage.json
```

Inspect the export before sharing. Record manuscript size, source type, host/model,
reasoning settings, tool setup, stage outcomes, rounds, audits, failures, and
whether all native sessions were retained. Use dedicated sessions or capture
explicit start/end boundaries if unrelated tasks share a session. The current
exporter supports whole dedicated sessions only and direct children, not nested
agent trees or alternate host schemas.

To establish ordinary-paper usage, collect multiple representative papers with
permission, repeat each configuration, and retain blocked runs as well as successes.
Compare total tokens, cache partitions, cost under actual rates, elapsed time, and
verified outcome quality. Match paper and review requirements across configurations.
Until those observations exist, use this fixture to understand the accounting and
possible bottlenecks, not to promise a typical token budget.

## Verification of this study

Local checks on 2026-09-23 used the `torch-mps` Python environment on macOS:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`: 130 tests passed,
  including six new accounting tests. The full suite took 272 seconds.
- `ruff check .` and `ruff format --check .`: passed.
- Project Pyright and explicit checks of the new scripts/tests: zero errors.
- A second export from all eleven private logs matched `observed.json` byte for
  byte. All native child paths matched the completed helper contexts.
- The fixture checker passed all twelve recorded artifact gates. All four figure
  previews were inspected; PDF renders were also checked during layout review.
- Staged content passed `scripts/check_public_content.py` and `git diff --check`.
  Raw transcripts and binary figure exports are not staged.

These checks do not establish Linux CI results, representative paper costs, or
scientific review quality.

[Project overview](../README.md)
