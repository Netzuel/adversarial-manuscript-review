# Editor workflow

Complete this workflow automatically. The helper enforces structural gates; your review supplies scientific judgment. Use actual filesystem records as state. Read `records.md` and the helper help; do not invent JSON fields or mutate state.json manually.

## 1. Ingest and contract

Run `amr.py init SOURCE` with the requested controls, using an argv list or safely quoted literal path. Resolve skill scripts relative to the installed skill. Retain returned run path and session token. Without --resume make a new run. On resume validate persisted hashes, stage, consumed budgets and pending dispatches; inspect partial outputs before acting. Do not repeat a completed student edit or uncertain side effect. Stop on changed original or ambiguous run selection. For PDF, first look within the supplied project for clearly corresponding editable source and verify correspondence from content/rendering; a shared basename is insufficient. If correspondence is verified, initialize from that editable entry point. Direct PDF initialization records an input blocker; never clear it by editing state. Without verified matching editable source, finish available review with BLOCKED_INPUT; DOCX faithful revision is unsupported. Never produce fake editable/rendered placeholders.

Read the complete ingested manuscript/dependency closure and accessible supplied evidence. Record missing includes, ambiguous dynamic TeX paths, visual/extraction gaps and uninspected segments. Do not execute manuscript macros, build scripts or code while ingesting. Inspect before any safe bounded check. Use parsed text plus rendered pages where equations/figures/layout need it.

Write a contract JSON in a staging location outside protected run assets, then freeze through the helper. Include actual question, contributions, material claims, language, applicable discipline, assumptions, available inputs, required areas/claim IDs/artifact checks, out-of-scope work, limitations, allowable writes, resolved budgets and source-preservation policy. A hypothetical internal journal is the default. Check public requirements only if a real target is requested. No questionnaire is needed for obvious defaults. Missing science is a blocker. Don't silently weaken a contract or replace its central contribution.

Use reports in the current user language when evident, otherwise the manuscript language. Select applicable checks from [rubrics.md](rubrics.md); load only relevant installed scientific guidance.

Do not upload manuscripts or unpublished detailed claims to additional services, public repositories or cloud memory. Literature queries use public references and minimal generic technical terms, never unpublished text. Preserve existing memory policy without expanding collection. Reviewer requests for source access go through the editor, who records coordinator-retrieved evidence distinctly from independent checks.

Populate coverage and claims-evidence maps. Cover every section, equation, table, figure and reference, identifying exact locations and responsible reviewers. Snapshot through the helper; all review reports bind to that snapshot hash. Snapshots and admissible evidence are immutable.

## 2. Independent initial review

Enter INDEPENDENT_REVIEW. Reserve R1–R4 dispatches through the helper before native spawning. Use at most three active children (or the lower host limit). Each receives the same snapshot, frozen contract and admissible evidence, plus its role. Do not expose sibling reports. Reports return structured findings and precise coverage; save through completion commands after checking the guards. Persist the real native task ID and context provenance. If spawning fails, checkpoint the actual capability/permission failure and finish independent supported work; no simulated committee acceptance.

## 3. Triage and student revision

Enter EDITORIAL_TRIAGE. Record issues with stable IDs and all required fields. Preserve every report and duplicate/dissent link. Required criticisms need location, evidence, consequence and a concrete resolution condition. Optional stylistic demands must remain optional. Explain evidence-based rejections and valid rebuttals.

If review-only, do not dispatch a student or edit candidate content. Deliver review artifacts; unresolved issues imply REVISION_REQUIRED or the appropriate blocker.

Otherwise enter STUDENT_REVISION. Reserve the student dispatch before spawning. Give triaged issues, current candidate, frozen contract and permitted evidence-output paths. The student writes actual sources; the editor does not silently implement the scientific corrections. Author identities and affiliations must come from the supplied manuscript or explicit user instructions; missing metadata stays absent, never inferred from account names or paths. Permit supported narrow repairs even if an independent issue is blocked. Guard completion checks candidate/evidence allowlists and protected hashes. On unauthorized mutation invalidate the stage, preserve evidence and restore only the candidate stage from its checkpoint. Do not silently repair tampered reviewer evidence and call it valid.

Persist the student's plan/response and actual diff. A response alone cannot close an issue. If no edit is needed because all criticisms were rebutted or the manuscript is clean, record that reason; don't invent edits.

## 4. Validate and re-review

Enter VALIDATION and freeze the revised candidate through the helper. Run inspected cheap checks within 60 seconds each and 300 seconds per round, recording argv, code/input hashes, environment, output, exit status and elapsed time. Use safe compilation without shell escape or auto-downloads. Build/render copies in disposable scratch, not immutable snapshots. Inspect affected page images when possible and record who inspected which pages; compilation alone is not visual QA. Required unavailable rendering/checks block acceptance; a genuinely irrelevant check can be excluded with a reason in the contract before review.

Write check reasons as neutral scientific purposes and inspection details, without reviewer names, verdicts or negotiation summaries. Check records may later be supplied to a fresh auditor. Preserve existing records exactly; do not redact a record retrospectively to conceal known exposure. If existing evidence exposes negotiation history, report that limitation and use a new neutral check only if justified within the remaining budget.

Enter RE_REVIEW. Dispatch relevant reviewers with current snapshot, issue IDs, actual diff and admissible check records. Bind every required area to the current snapshot: obtain all four current verdicts, or record explicit unchanged dependency/hash reuse that the helper supports. Do not transfer stale approvals implicitly. A new substantive regression creates/reopens an issue with a reason. Reviewer/editor closures require inspected evidence and resolution/rebuttal rationale. Maintain coverage and claims maps, with material missing support still visible.

Persist each returned task through `complete` before acting on its requested follow-up checks. Do not run checks or add evidence while any child reservation remains active: those writes would change the evidence frozen for that task and invalidate its guard. A returned native task is still active in the helper until its completion is recorded. Finish the current wave, then run new checks and dispatch any needed follow-up review.

If substantive work remains and budget permits, advance one round, triage, revise and verify. Record material progress as changes to substantive issue/coverage outcomes, not wording or file count. After two rounds without such progress stop STOPPED_NO_PROGRESS. Missing indispensable evidence leads BLOCKED_EVIDENCE; unsupported correction scope leads REVISION_REQUIRED. No full training, sweeps, GPU/hardware jobs or external publishing.

## 5. Fresh audit and final delivery

When specialist criteria are met, enter FRESH_AUDIT. Reserve a NEW audit task. Provide only current snapshot, contract, admissible evidence and the audit role/schema. Do not send prior verdicts, responses or negotiation history. Record the real context mechanism, exposure check and tools. Only after the independent result is saved compare it with history. New blocking findings consume the existing round/audit budget; do not reset it.

Include the current snapshot manifest and each executed check's code/input hashes in the auditor's allowed evidence paths. The auditor must be able to compare source hashes with the reviewed snapshot without reading the mutable candidate or negotiation records. A snapshot label alone is not that comparison. If the frozen contract cites baseline line numbers, identify them as baseline locations and supply a neutral current location index without verdicts or issue-closure history; do not rewrite the contract.

Finalize through the helper. PASS_INTERNAL requires current full coverage, no unresolved major/critical issue, inspected closure evidence, valid specialist verdicts, verified separate fresh audit without known history exposure, passed required artifact checks, matching delivered hashes and existing files. Structural validation is not a scientific theorem prover.

If a guard invalidates a stage, preserve the ERROR status and evidence. Confirm native tasks have ended, then use the proof-required `abandon` procedure in records.md for each remaining reservation and finalize ERROR. Do not bypass the gate by manually presenting another terminal status or delete evidence to make completion succeed. Ordinary safe interruption/resume is separate from terminal abandonment.

Deliver actual revised editable files plus REVIEW_RESULT.md, RESPONSE_TO_REVIEWERS.md, CHANGES.md, UNRESOLVED.md and REPRODUCIBILITY.md. Report the exact editable entry point, original preservation, terminal status, scope/limitations, unresolved issues, evidence and budget usage. PASS_INTERNAL means only that configured internal criteria were met for supplied material/scope, never journal acceptance or universal correctness. Blocked/budget/interrupted results still deliver useful candidate progress labelled accordingly.

With explicit --in-place, promote only PASS_INTERNAL after original hash/conflict checks and backups. No other invocation authorizes replacing originals. Release the run lease on orderly completion/interruption. On host exit work does not continue; a later --resume continues from the durable checkpoint.
