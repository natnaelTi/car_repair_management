# Verification and Evidence Record

Version 1.0 | 13 November 2026 | AAP Fleet Management System

## Source and Scope

- Reviewed application source: `5974cf7addfef5d5cfc8fde325fc964343557a2f`.
- Public remote checked: `https://github.com/natnaelTi/car_repair_management`, fetched `master` at `36e822205eb0f6df6cf4548e35af3d34ae128e1a` during preparation.
- The local Dockerfile and Compose override are unchanged from that remote master. They specify base `frappe/erpnext:v15.79.0` and application image `car-repair-management:v15.79.0` respectively.
- The evaluated hardware/polling application revision is not implied to be on remote master or in a built production image. Documentation publication and application release are distinct operations.
- Customer, product, planned on-premise hosting, more-than-700 vehicles/more-than-500 users and technical contact were provided by the project representative.
- No live site configuration, real provider credential or operational fleet dataset is included in the generated source inventory.

## Checks Executed for This Dossier

| Check | Method | Result |
| --- | --- | --- |
| Source grounding | Inspected hooks, setup, APIs, controllers, polling, routes, client and Docker files | Requirements/design tied to evaluated source; limitations recorded |
| Focused integration unit tests | Command below | 26 tests passed; mocked/unit coverage, not production end-to-end assurance |
| Source inventory | Python AST for declared APIs/setup fields, JSON DocType parser, literal route declaration extraction, Git-source SHA-256 | Generated into TDD and source-inventory.json; counts recorded there |
| PDF generation | Local Markdown + WeasyPrint; remote resource fetch disabled | Five PDFs generated with contents, page numbers and readable text |
| Artifact consistency | `build_dossier.py --check` and pypdf | Every manifest hash and all PDF pages checked |
| PDF layout | Temporary PDFium rasterization and text bounds inspection | 20 sampled pages visually reviewed; no out-of-page character boxes across all 73 pages |

```bash
# From application repository, using the existing bench interpreter
../../env/bin/python -m unittest \
  car_repair_management.tests.test_polling \
  car_repair_management.tests.test_hardware \
  car_repair_management.tests.test_integration_settings
../../env/bin/python documentation/insa/tools/build_dossier.py --refresh-inventory
../../env/bin/python documentation/insa/tools/build_dossier.py --check
```

## Not Established by These Checks

- Production Docker build/install/upgrade: Docker CLI/runtime is not available in this preparation environment. No image digest or final Compose stack was supplied.
- Final production infrastructure, TLS, account policy, secrets, private network boundaries and dependency patch status were not audited.
- No broad security scan, penetration test, full Frappe suite, role-negative matrix, concurrency test, 700+-vehicle/500+-user load test, retention exercise or witnessed restore was performed here.
- Earlier hardware integration testing reported successful provider requests, GPS/fuel workflows, browser behavior and background polling, but is not a new witnessed test on the Commission's final production Docker release. Historical results are not silently promoted into a production acceptance certificate.
- Existing frontend typecheck/dependency issues reported during integration work must be assessed in release QA; a previously successful production asset build is not proof of a clean whole-project typecheck.
- No official INSA template/checklist was supplied; the dossier is not represented as meeting an unverified authority-specific format.

## Evidence to Attach Before Submission

Record the final source and immutable image digest; complete Commission approval fields; attach clean Docker installation/upgrade, all-site audit, workflow/UAT, authorization-negative, security scan/assessment, capacity, retention and restore reports. Resolve/disposition the Security document's register through the authorized process. Keep sensitive evidence in controlled storage rather than this public repository.
