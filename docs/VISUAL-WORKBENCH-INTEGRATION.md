# Visual Workbench Integration

Project Evidence Graph can be projected into Visual Workbench after assurance semantics have already been established by the owning repositories.

The reference path is now executable across five repositories:

```text
Mapping as Code
  -> Reconciliation as Code
  -> Cutover Graph
  -> Project Evidence Graph
  -> Visual Workbench
```

This is intentionally not a shared runtime platform. Each product keeps one bounded responsibility.

## Ownership

| Repository | Owns |
|---|---|
| Mapping as Code | mapping intent and transformation contract |
| Reconciliation as Code | deterministic comparison and reconciliation evidence |
| Cutover Graph | cutover checkpoint/gate semantics and external evidence verification |
| Project Evidence Graph | project traceability and assurance relationships |
| Visual Workbench | deterministic business-readable visual projection |

Visual Workbench never becomes the source of assurance truth. It consumes the Project Evidence Graph artifact read-only.

## Evidence-preserving projection

Project Evidence Graph separates local graph relationships from cross-repository references in `external_bridges`. The Visual Workbench adapter preserves both:

```json
{
  "from": "eac://dkharlanau/cutover-graph/checkpoint/reconcile-customers",
  "to": "eac://dkharlanau/reconciliation-as-code/reconciliation/customer-country-post-load/run/example",
  "type": "substantiated_by"
}
```

The external target becomes a neutral reference node in the visual, not a newly verified evidence object. Visual Workbench does not dereference the URI, execute upstream code, or upgrade trust state.

This matters because the same picture must distinguish:

- a registry-verified Cutover checkpoint that is positive Project Evidence;
- an unverified external checkpoint that remains a Project Evidence defect;
- the exact external reconciliation reference supporting the checkpoint.

## Derived views

The reference workflow renders two deliberately different outputs from the same upstream semantics:

- `verified-assurance.svg` / `verified-assurance.html` — assurance-oriented view of the verified path;
- `unverified-exceptions.svg` — exception-oriented view proving that fail-closed state remains visible.

The workflow also writes `visual-assurance-summary.json` and asserts that:

1. the exact RAC logical reference survived into the visual projection;
2. `substantiated_by` survived as a control/evidence relationship;
3. the unverified checkpoint remains a danger/risk state;
4. the assurance view still contains the external evidence reference;
5. the exception view still contains the failed checkpoint.

These assertions protect semantics, not screenshot appearance.

## Moving-main assurance

`.github/workflows/portfolio-assurance-contract.yml` checks out current `main` for the four upstream product repositories while the workflow itself runs from Project Evidence Graph. It then:

1. builds a RAC contract from current Mapping as Code;
2. produces current RAC evidence;
3. binds that evidence to a current Cutover checkpoint;
4. generates verified and deliberately unverified Cutover artifacts;
5. imports both into Project Evidence Graph;
6. renders both through current Visual Workbench;
7. retains the exact repository SHAs and generated artifacts in one receipt bundle.

The resulting receipt proves interoperability for those exact checked-out commits. It does not prove external adoption, production suitability, or compatibility with every future release.

## Why this integration stays small

The portfolio should not copy domain models merely to make diagrams easier. Visual Workbench therefore adapts only the public Project Evidence artifact surface and preserves original IDs/provenance.

New visualization requirements should first ask whether they are presentation concerns. If they require new business, reconciliation, cutover, or assurance truth, that truth belongs in the owning upstream repository and should only then be projected visually.
