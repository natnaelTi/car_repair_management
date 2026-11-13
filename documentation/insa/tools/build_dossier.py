"""Build an offline, source-traceable assessment dossier; never contacts a site."""
import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "documentation" / "insa"
BASELINE = "5974cf7addfef5d5cfc8fde325fc964343557a2f"
FILES = (
    "01-software-requirements-prd",
    "02-system-architecture-sdd",
    "03-technical-specifications-tdd",
    "04-user-guide",
    "05-security-documentation",
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8")


def source(path):
    return git("show", f"{BASELINE}:{path}")


def table_cell(value):
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", "<br>")


def table(headers, rows):
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(table_cell(v) for v in row) + " |" for row in rows),
    ])


def literal(node, fallback=None):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return fallback


def generate_inventory():
    paths = git("ls-tree", "-r", "--name-only", BASELINE).splitlines()
    inventory = {"baseline": BASELINE, "doctypes": [], "api_modules": [],
                 "setup_fields": [], "routes": [], "sources": {}}

    def read(path):
        content = source(path)
        inventory["sources"][path] = hashlib.sha256(content.encode()).hexdigest()
        return content

    for path in paths:
        if "/doctype/" not in path or not path.endswith(".json"):
            continue
        doc = json.loads(read(path))
        if doc.get("doctype") != "DocType":
            continue
        inventory["doctypes"].append({
            "name": doc["name"], "path": path, "child": bool(doc.get("istable")),
            "submittable": bool(doc.get("is_submittable")),
            "autoname": doc.get("autoname", ""), "permissions": doc.get("permissions", []),
            "fields": [{key: field.get(key) for key in
                        ("fieldname", "label", "fieldtype", "options", "reqd", "unique", "read_only")}
                       for field in doc.get("fields", [])
                       if field.get("fieldtype") not in
                       ("Section Break", "Column Break", "Tab Break", "HTML", "Button")],
        })

    controller = ("car_repair_management/car_repair_management/doctype/"
                  "repair_order/repair_order.py")
    for path in paths:
        if not ((path.startswith("car_repair_management/api/") or path == controller)
                and path.endswith(".py")):
            continue
        tree = ast.parse(read(path))
        methods = []
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = [item for item in node.decorator_list
                          if isinstance(item, ast.Call) and
                          isinstance(item.func, ast.Attribute) and item.func.attr == "whitelist"]
            if not decorators:
                continue
            options = {kw.arg: literal(kw.value, ast.unparse(kw.value))
                       for kw in decorators[0].keywords}
            methods.append({"name": node.name, "signature": ast.unparse(node.args),
                            "line": node.lineno, "whitelist": options})
        inventory["api_modules"].append({"path": path, "methods": methods})

    setup_paths = ["car_repair_management/install.py", "car_repair_management/api/setup.py",
                   "car_repair_management/api/setup_fuel_fields.py",
                   "car_repair_management/api/setup_issue_fields.py"]
    for path in setup_paths:
        fields = {}
        for node in ast.walk(ast.parse(read(path))):
            data = {}
            if isinstance(node, ast.Dict):
                data = {literal(k): literal(v) for k, v in zip(node.keys, node.values) if k}
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
                data = {kw.arg: literal(kw.value) for kw in node.keywords if kw.arg}
            if isinstance(data.get("fieldname"), str) and isinstance(data.get("fieldtype"), str):
                key = (data["fieldname"], data["fieldtype"], str(data.get("options") or ""))
                fields[key] = {k: data.get(k) for k in
                               ("fieldname", "fieldtype", "options", "reqd", "unique", "read_only")}
        inventory["setup_fields"].append({"path": path, "fields": sorted(fields.values(), key=lambda f: f["fieldname"])})

    router = read("frontend/src/router.ts")
    inventory["routes"] = re.findall(r"\bpath:\s*'([^']+)'", router)
    for path in ("car_repair_management/hooks.py", "car_repair_management/polling.py",
                 "car_repair_management/tasks.py", "car_repair_management/overrides/vehicle.py",
                 "car_repair_management/www/workshop.py", "frontend/src/api/client.ts",
                 "frontend/package.json", "pyproject.toml", "docker/Dockerfile",
                 "docker/compose.car-repair-management.yaml", "docker/README.md"):
        read(path)
    (DOCS / "source-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")

    parts = ["### 9.1 Inventory Summary", table(
        ["Item", "Count / baseline"], [
            ["Source revision", BASELINE],
            ["Shipped DocTypes (including child tables)", len(inventory["doctypes"])],
            ["Declared whitelisted functions in API modules and RO controller",
             sum(len(m["methods"]) for m in inventory["api_modules"])],
            ["Frontend route path declarations", len(inventory["routes"])],
        ]),
        "Source SHA-256 values and machine-readable definitions are in `source-inventory.json`. "
        "Runtime telemetry DocTypes are created by install.py, separately from shipped JSON. "
        "Inherited Frappe/ERPNext APIs and permissions are outside this application-only inventory.",
        "### 9.2 Shipped DocType Data Dictionary"]
    for doc in sorted(inventory["doctypes"], key=lambda d: d["name"]):
        parts.extend([f"#### {doc['name']}",
                      f"Source: `{doc['path']}`. Child: {doc['child']}. "
                      f"Submittable: {doc['submittable']}. Naming: `{doc['autoname'] or 'framework default'}`."])
        permissions = []
        for row in doc["permissions"]:
            actions = [k for k in ("read", "write", "create", "delete", "submit", "cancel",
                                   "amend", "report", "export", "print", "email", "share") if row.get(k)]
            permissions.append(f"{row.get('role')}: {', '.join(actions)} (level {row.get('permlevel', 0)})")
        parts.append("Declared permissions: " + ("; ".join(permissions) or "None on this JSON; child access inherits parent context.") + ".")
        parts.append(table(["Field", "Type / target or choices", "Flags"], [
            [f["fieldname"], f["fieldtype"] + (": " + str(f["options"]) if f.get("options") else ""),
             ", ".join(k for k in ("reqd", "unique", "read_only") if f.get(k)) or "-"]
            for f in doc["fields"]]))
    parts.append("### 9.3 Declared Application API Functions")
    parts.append("Paths below are Python source modules; remove `.py` and replace `/` with `.` "
                 "to form the module prefix. Append the function name after `/api/method/`. "
                 "`framework default` means no explicit methods restriction is declared, not that GET mutations are recommended. "
                 "This inventory includes only direct module-level whitelist decorators.")
    for module in inventory["api_modules"]:
        if not module["methods"]:
            continue
        parts.extend([f"#### {module['path']}", table(["Function and arguments", "Declared transport"], [
            [f"{m['name']}({m['signature']})", json.dumps(m["whitelist"]) if m["whitelist"] else "framework default"]
            for m in module["methods"]])])
    parts.append("### 9.4 Setup Field Declarations")
    parts.append("Unique static declarations grouped by setup source, including base telemetry fields. "
                 "A name can occur on more than one target DocType. Conditional/dynamically assembled values "
                 "may require code inspection; target placement is not inferred from these flattened rows.")
    for setup in inventory["setup_fields"]:
        parts.extend([f"#### {setup['path']}", table(["Field", "Type / target", "Flags"], [
            [f["fieldname"], f["fieldtype"] + (": " + str(f["options"]) if f.get("options") else ""),
             ", ".join(k for k in ("reqd", "unique", "read_only") if f.get(k)) or "-"]
            for f in setup["fields"]])])
    parts.extend(["### 9.5 Frontend Route Inventory",
                  "All paths are relative to `/workshop`. Dynamic parameters identify records. "
                  "Route declaration is not a role gate; backend authorization remains necessary.",
                  "\n".join(f"- `{route}`" for route in inventory["routes"])])
    path = DOCS / "03-technical-specifications-tdd.md"
    content = path.read_text()
    start, end = "<!-- BEGIN GENERATED INVENTORY -->", "<!-- END GENERATED INVENTORY -->"
    before, rest = content.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + start + "\n\n" + "\n\n".join(parts) + "\n\n" + end + after)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    from pypdf import PdfReader
    manifest = json.loads((DOCS / "build-manifest.json").read_text())
    if manifest["source_baseline"] != BASELINE:
        raise ValueError("Manifest baseline does not match the builder")
    for relative, expected in manifest["sha256"].items():
        path = DOCS / relative
        if digest(path) != expected:
            raise ValueError(f"Artifact hash mismatch: {relative}")
    for stem in FILES:
        reader = PdfReader(DOCS / "pdf" / f"{stem}.pdf")
        if not reader.pages or any(not page.extract_text().strip() for page in reader.pages):
            raise ValueError(f"Empty/unreadable PDF page: {stem}")
        combined = "\n".join(page.extract_text() for page in reader.pages)
        if "Addis Ababa Police Commission" not in combined:
            raise ValueError(f"Missing customer identity: {stem}")
        print(f"OK {stem}: {len(reader.pages)} readable pages")
    for md in DOCS.glob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", md.read_text()):
            if "://" not in target and not target.startswith("#"):
                if not (md.parent / target.split("#", 1)[0]).exists():
                    raise ValueError(f"Broken local link in {md.name}: {target}")


def build():
    import markdown
    from weasyprint import CSS, HTML

    def no_remote_resources(url):
        raise ValueError(f"External resources are disabled for dossier rendering: {url}")

    output = DOCS / "pdf"
    output.mkdir(exist_ok=True)
    hashes = {}
    for stem in FILES:
        md = DOCS / f"{stem}.md"
        renderer = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                                     extension_configs={"toc": {"toc_depth": "2-2"}})
        body = renderer.convert(md.read_text())
        title = md.read_text().splitlines()[0].lstrip("# ")
        markup = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
                  f"<title>{html.escape(title)}</title>"
                  "<meta name='author' content='Selfmade Cloud Solutions'>"
                  "</head><body>" + body.split("<h2", 1)[0] +
                  "<section class='toc'><h2>Contents</h2>" + renderer.toc + "</section>"
                  "<main class='document-body'><h2" + body.split("<h2", 1)[1] + "</main></body></html>")
        target = output / f"{stem}.pdf"
        HTML(string=markup, url_fetcher=no_remote_resources).write_pdf(
            target, stylesheets=[CSS(filename=DOCS / "tools" / "print.css")])
        hashes[md.name] = digest(md)
        hashes[f"pdf/{target.name}"] = digest(target)
        print(f"Built {target.name}")
    for relative in ("source-inventory.json", "verification.md", "README.md",
                     "tools/build_dossier.py", "tools/print.css", "tools/requirements.txt"):
        hashes[relative] = digest(DOCS / relative)
    manifest = {"document_version": "1.0", "issue_date": "2026-11-13",
                "product": "AAP Fleet Management System", "source_baseline": BASELINE,
                "renderer": {name: version(name) for name in ("Markdown", "weasyprint", "pypdf")},
                "sha256": hashes}
    (DOCS / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    check()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-inventory", action="store_true")
    parser.add_argument("--check", action="store_true", help="Verify existing artifacts without rewriting")
    args = parser.parse_args()
    if args.check:
        check()
        return
    if args.refresh_inventory:
        generate_inventory()
    build()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Dossier build failed: {exc}", file=sys.stderr)
        sys.exit(1)
