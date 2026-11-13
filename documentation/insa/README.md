# Production Assessment Documentation

AAP Fleet Management System | Addis Ababa Police Commission | Version 1.0 | 13 November 2026

## Purpose and Status

This package supports the Commission's application for software assessment by the Information Network Security Authority (INSA), Federal Democratic Republic of Ethiopia. It is an engineering dossier, not a certificate, an attestation of compliance, or a representation that INSA has approved the software. No official assessment template or additional authority-issued criteria were supplied for this preparation.

The documented product is **AAP Fleet Management System**, implemented by the `car_repair_management` Frappe/ERPNext application, Vue workshop interface, hardware integration, and Docker packaging. It is planned for on-premise hosting on the Addis Ababa Police Commission's server, serving more than 700 vehicles and more than 500 users. These are minimum planning figures, not a measured concurrent-load capacity. Unrelated apps installed on a development bench, including payment and ID-card applications, are outside this dossier unless explicitly added to the approved production bill of materials.

**Issue status: prepared for Commission technical review, not signed for submission.** Functionality is described from source; production deployment and security acceptance require the evidence and signatures below. Previously successful integration tests are not a production security certification.

## Documents

| ID | Document | Markdown | PDF |
| --- | --- | --- | --- |
| CRM-PRD-001 | Software Requirements / Product Requirements | [PRD](01-software-requirements-prd.md) | [PDF](pdf/01-software-requirements-prd.pdf) |
| CRM-SDD-001 | System Architecture and Design | [SDD](02-system-architecture-sdd.md) | [PDF](pdf/02-system-architecture-sdd.pdf) |
| CRM-TDD-001 | Technical Specifications / Low-Level Design | [TDD/LLD](03-technical-specifications-tdd.md) | [PDF](pdf/03-technical-specifications-tdd.pdf) |
| CRM-UG-001 | User Manual | [User Guide](04-user-guide.md) | [PDF](pdf/04-user-guide.pdf) |
| CRM-SEC-001 | Security Documentation (optional application item, included) | [Security](05-security-documentation.md) | [PDF](pdf/05-security-documentation.pdf) |

The TDD includes generated inventories of shipped DocTypes and fields, declared API functions, frontend routes, setup-field declarations, and source hashes. These are static inventories, not a runtime permission audit, dependency SBOM, or proof of coverage.

## Configuration Baseline

| Item | Recorded value |
| --- | --- |
| Application source revision reviewed | `5974cf7addfef5d5cfc8fde325fc964343557a2f` |
| Application package version | `0.0.1` (not a unique release identifier) |
| Upstream repository | `https://github.com/natnaelTi/car_repair_management` |
| Framework target | Frappe v15 and ERPNext v15 |
| Dockerfile default base tag | `frappe/erpnext:v15.79.0` |
| Compose override image | `car-repair-management:v15.79.0` |
| Deployment verification | Final Commission production stack/image not supplied or inspected |
| Evidence scope | Source inspection and focused local tests; see `verification.md` |

The source revision is the evaluated integration revision, **not** the final production image digest. Documentation may be published independently of that application revision. Release engineering must make the evaluated revision available in the controlled source repository, reconcile subsequent fixes, regenerate the inventory, and record the final image digest before submission. A documentation-only branch does not install or publish application code.

## Commission Review Record

Complete these in a controlled submission copy. `TO BE CONFIRMED` is a review field, not an approved operating value.

| Required confirmation | Owner | Value / approval |
| --- | --- | --- |
| Commission's full legal name and owning department | Commission sponsor | Addis Ababa Police Commission; owning department to be confirmed |
| Formal product/deployment name and assessment scope | Product owner | AAP Fleet Management System; scope as described in this package |
| Production release source SHA and image digest | Release manager | TO BE CONFIRMED |
| Hosting country, facility/operator and network boundary | Infrastructure owner | Planned on-premise on the Commission's server; facility/network details to be confirmed |
| Final Compose bundle, secrets mechanism and service versions | Infrastructure owner | TO BE CONFIRMED |
| Users, vehicles, peak concurrency and telemetry rate | Operations owner | More than 500 users and 700 vehicles; peak concurrency/rate to be confirmed |
| Availability target, RPO, RTO and support hours | Service owner | TO BE CONFIRMED |
| GPS/personnel/finance retention and permitted exports | Information owner | TO BE CONFIRMED |
| Hardware provider agreement, units and timestamp timezone | Integration owner | TO BE CONFIRMED |
| Security finding disposition and independent test report | Security assessor | TO BE CONFIRMED |
| Submission authority, signature and date | Commission authorized signatory | TO BE CONFIRMED |

No real API key, employee identity, license plate, device identifier, internal address, or operational GPS trace is needed in this public-repository dossier. Examples use fictional data. Keep penetration-test details, final network maps, credentials and signed deployment records in an access-controlled evidence store; reference their identifiers in the signed copy.

User-designated technical contact: **Natnael Tilaye**, **natnaeltilaye30@gmail.com**. This contact is included for the assessment submission at the request of the project representative.

## Rebuild and Verify

Run as a documentation maintainer from the application repository, not as a production administrator. The script reads Git objects and documentation files, renders the five PDFs, and hashes their Markdown/PDF pairs. It does not connect to any site, database, sensor or provider.

```bash
# Use an isolated environment if the dependencies are not already available.
python3 -m venv /tmp/crm-dossier-env
/tmp/crm-dossier-env/bin/pip install -r documentation/insa/tools/requirements.txt
/tmp/crm-dossier-env/bin/python documentation/insa/tools/build_dossier.py --refresh-inventory
/tmp/crm-dossier-env/bin/python documentation/insa/tools/build_dossier.py --check
```

For the existing bench environment, use `../../env/bin/python` instead of the temporary interpreter if the required packages are installed. WeasyPrint also requires its platform text/font libraries. The requirements file captures the versions used here, not approved application runtime dependencies. HTML and PDFs are generated locally; rendering blocks remote resources. `--refresh-inventory` requires the evaluated source commit to exist in the local Git object database. A documentation-only checkout can rebuild PDFs from the included Markdown/inventory by omitting that flag, or verify them using `--check`; release engineering must supply the controlled source revision before refreshing its inventory.

Review `build-manifest.json` for baseline SHA, document hashes and renderer versions. `--check` validates hashes and PDF readability without rewriting artifacts. PDF metadata and font rendering may differ between platforms; compare content and regenerate the manifest rather than expecting byte-identical output across platforms.

## Release Gates

1. Product owner validates PRD requirements and user workflows against the intended operating procedures.
2. Architect verifies the actual Compose topology, versions, storage and external dependencies against the SDD.
3. Engineers resolve or formally disposition the security register; disabling a button is not API authorization.
4. QA executes a clean Docker installation, upgrade, permission-negative tests, telemetry tests, load tests and backup restore.
5. Security assessor reviews the final build; archive dependency/image scans and penetration-test results.
6. Commission completes review fields, attaches controlled evidence, signs the document-control records and authorizes submission.

## Revision and Approval

| Version | Date | Change | Approval |
| --- | --- | --- | --- |
| 1.0 | 13 November 2026 | Initial source-grounded five-document dossier and reproducible PDFs | Pending Commission review |

Prepared by: Selfmade Cloud Solutions engineering documentation. Technical reviewer, security reviewer and Commission approver: **TO BE CONFIRMED**. Material application or infrastructure changes require impact review and a new document revision.
