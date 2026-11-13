# Car Repair Management — Documentation

## Overview

Car Repair Management is a comprehensive Frappe/ERPNext application for fleet management, vehicle repair workshops, and maintenance operations. It provides a modern Vue 3 Single Page Application (SPA) frontend served at `/workshop` alongside a full-featured Frappe backend with custom DocTypes, whitelisted APIs, and deep ERPNext integrations.

| Property | Value |
|---|---|
| **Publisher** | Selfmade Cloud Solutions |
| **License** | MIT |
| **Requires** | ERPNext v15+ |
| **Frontend** | Vue 3 + Vite + Tailwind CSS |
| **Backend** | Python (Frappe Framework) |
| **Languages** | English, Amharic, French, Arabic, Tigrinya, Oromo, Kinyarwanda |

## Table of Contents

### Production Assessment Dossier

[AAP Fleet Management System - INSA Documentation](insa/README.md): source-grounded PRD, system design, technical specifications, user guide and security documentation, each with a PDF edition, source inventory and verification record for Addis Ababa Police Commission.

### Developer Guides

1. [Architecture Overview](architecture.md) — System architecture, directory structure, integration points
2. [DocType Reference](doctypes.md) — All 28+ DocTypes with fields, naming, and relationships
3. [Backend API Reference](api-reference.md) — All whitelisted API methods organized by module
4. [Frontend Guide](frontend-guide.md) — Vue 3 SPA structure, components, routing, state management
5. [Repair Order Lifecycle](repair-order-lifecycle.md) — Full RO workflow from creation to close
6. [Vehicle Management](vehicle-management.md) — Vehicle CRUD, drivers, custodians, asset integration
7. [Fuel Quota System](fuel-quota-system.md) — Quota auto-creation, refueling, over-quota approval
8. [Inspection System](inspection-system.md) — Inspections, schedules, forms, failure tracking
9. [Issues, Faults & Recalls](issues-faults-recalls.md) — Issue workflow, fault codes, recalls
10. [Expenses & Invoicing](expenses-invoicing.md) — Expense tracking, sales/purchase invoices
11. [Reports & Analytics](reports-analytics.md) — 30+ standard reports, saved reports, scheduling

### Operations & Configuration

12. [Settings & Configuration](settings-configuration.md) — 14 settings categories
13. [Roles & Permissions](roles-permissions.md) — Role-based access control
14. [Deployment & Operations](deployment-operations.md) — Deployment, restart procedures, maintenance

### End User

15. [User Manual](user-manual.md) — Step-by-step guide for end users

---

## Quick Start

### Installation

```bash
# Get the app
bench get-app https://github.com/selfmadecs/car_repair_management.git

# Install on a site
bench --site your-site.com install-app car_repair_management
```

### What Happens on Install

The `after_install` hook (`install.py`) performs:

1. **Creates custom DocTypes**: Vehicle Location, Vehicle Fuel Level, Vehicle Sensor Data
2. **Creates custom fields** on 10+ standard DocTypes (Vehicle, Asset, Quotation, Sales Order, Sales Invoice, Project, Task, Timesheet, Stock Entry, Purchase Invoice, Repair Order)
3. **Creates master data**: Asset Category "Vehicles", Item "VEHICLE-ASSET" for fixed asset integration
4. **Sets up workspace**: Workshop workspace with KPI Number Cards, Dashboard Charts, Kanban Board, shortcuts
5. **Seeds demo data**: Sample vehicles, employees, repair orders, customers

### Accessing the Application

- **Frontend SPA**: `https://your-site.com/workshop`
- **Frappe Desk**: `https://your-site.com/app/repair-order` (standard desk views)
- **Workshop Workspace**: Available in Frappe Desk sidebar under "Workshop"

### Development

```bash
# Start backend
bench start

# Start frontend dev server (hot reload)
cd apps/car_repair_management/frontend && yarn dev

# Build frontend for production
cd apps/car_repair_management/frontend && yarn build
```
