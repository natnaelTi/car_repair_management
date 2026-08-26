# Vehicle Management

## Overview

The Vehicle module extends ERPNext's core Vehicle DocType with extensive custom fields for fleet management, driver assignments, fuel quota tracking, GPS telemetry, and asset integration.

## Vehicle Fields

### Core Information
- `license_plate` (Data) — Vehicle registration number (used as display name)
- `custom_status` (Select) — Active / In Maintenance / Undergoing Tests / Delivered to Customer / Scrapped
- `custom_vehicle_type` (Select) — Car / SUV / Truck / Van / Motorcycle / Bus / Other
- `custom_image` (Attach Image) — Vehicle photo
- `make`, `model`, `variant`, `year` — Vehicle identification
- `color`, `chassis_no`, `engine_number` — Additional identifiers

### Technical Specifications
- `engine_type`, `engine_capacity` (cc), `cylinders`, `drivetrain`
- `transmission` — Manual / Automatic / CVT
- `fuel_type` — Petrol / Diesel / Natural Gas / Electric
- `fuel_tank_capacity`, `battery_capacity`
- `seating_capacity`, `payload_capacity`, `towing_capacity`, `gross_vehicle_weight`
- `country_of_origin`

### Financial
- `acquisition_cost` (Currency) — Purchase price
- `acquisition_date` — Purchase date
- `vehicle_value` (Currency) — Current value
- `depreciation_method` — Straight Line / Double Declining Balance / Written Down Value
- `depreciation_months` — Useful life in months (default: 60)
- `erpnext_asset` (Link → Asset) — Auto-linked fixed asset

### Registration & Insurance
- `ownership_type`, `registration_authority`, `registration_expiry`
- `insurance_policy`, `insurance_company`, `insurance_expiry`
- `insured_value`, `insurance_start_date`, `comprehensive_insurance`

### Computed Fields (Read-Only)
- `odometer_at_last_service`, `last_service_date`, `next_service_due_date`
- `jobs_count` — Total repair orders
- `repair_cost_to_date` — Total repair expenses
- `revenue_billed_to_date` — Total billed revenue

### GPS Tracking
- `custom_telematics_imei` — Hardware tracker IMEI used by the central telemetry ingestion API to map incoming sensor data to this Vehicle
- `custom_last_known_latitude`, `custom_last_known_longitude`
- `custom_last_location_update`

### Fuel Quota
- `custom_fuel_capacity_liters` — Tank capacity
- `custom_km_per_liter` — Fuel efficiency
- `custom_monthly_fuel_quota` — Monthly quota override (if 0 or null, auto-calculated as capacity × 2)

## Driver & Custodian Management

### Custodian
The `custom_custodian` field (Link → Employee) designates the employee responsible for the vehicle. A custodian has approval authority over issues raised by drivers.

### Drivers
The `custom_drivers` child table (Table → Vehicle Driver) tracks the full driver assignment history:

| Field | Purpose |
|---|---|
| `employee` | The driver (Link → Employee) |
| `status` | Active / Removal Requested / Removed |
| `assigned_date` | When assigned |
| `assigned_by` | Who assigned |
| `ended_date` | When removed |
| `ended_by` | Who removed |
| `removal_reason` | Why removed |

**Validation**: Only one driver can have `status = "Active"` per vehicle (enforced in `overrides/vehicle.py` → `validate`).

### Employee Detail Integration
The Employee Detail page shows vehicle assignments from both sources:
- **Driver assignments**: Queried from `Vehicle Driver` child table by employee
- **Custodian assignments**: Queried from `Vehicle.custom_custodian` by employee
- Split into **current** (Active) and **past** (Removed) assignments with role badges (Driver/Custodian)

## Asset Integration

When a Vehicle is saved with acquisition data (`acquisition_date` + `acquisition_cost` > 0), the `on_update` hook automatically creates an ERPNext Asset:

1. Checks for existing linked asset (via `erpnext_asset` field or reverse lookup)
2. Creates Asset with:
   - Asset category: "Vehicles"
   - Item code: "VEHICLE-ASSET" (fixed asset item)
   - Gross purchase amount from `acquisition_cost`
   - Depreciation schedule from `depreciation_method` and `depreciation_months`
   - Valid depreciation start date (checks fiscal year availability)
3. Links the Asset back to the Vehicle via `erpnext_asset` field

### Insurance Sync
Insurance fields are synced from Vehicle to linked Asset on every save:
- `insurance_company` → Asset `insurer`
- `insurance_policy` → Asset `policy_number`
- `insured_value` → Asset `insured_value`
- `insurance_start_date` / `insurance_expiry` → Asset date fields
- `comprehensive_insurance` → Asset field

## Vehicle Dashboard (Frontend)

The Vehicle Detail page (`/workshop/vehicles/:id`) features 10 tabs:

| Tab | Content |
|---|---|
| **Specs** | Technical specifications, engine details, capacities |
| **Service History** | Past repair orders and services |
| **Work Orders** | Active and recent repair orders |
| **Inspection History** | All inspections for this vehicle |
| **Issues** | Open and resolved issues |
| **Financials** | Cost of ownership, insurance, depreciation, asset info |
| **Fuel Quota** | Monthly fuel quotas and refueling records |
| **Service Reminders** | Upcoming maintenance due dates |
| **Sensor Data** | GPS, fuel level, and sensor telemetry |
| **Attachments** | Documents and files |

The vehicle dashboard API (`get_vehicle_dashboard`) returns all this data in a single call.

## Fleet Analysis Pages

| Page | Route | Description |
|---|---|---|
| Assignments | `/vehicles/assignments` | Driver/custodian assignment overview |
| Meter History | `/vehicles/meter-history` | Fleet-wide odometer tracking |
| Expense History | `/vehicles/expense-history` | Fleet expense trends |
| Replacement Analysis | `/vehicles/replacement-analysis` | Vehicle replacement scoring |
| Aging Analysis | `/vehicles/aging-analysis` | Fleet age distribution |
