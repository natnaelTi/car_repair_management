# Repair Order Status Change Design

## Status Flow

```
Draft → Scheduled → In Progress → Awaiting Parts/Ready for Handover → Delivered → Closed
              ↓            ↓               ↓
           On Hold    On Hold         On Hold
              ↓            ↓               ↓
          Cancelled  Cancelled       Cancelled
```

## Status Definitions

- **Draft**: Initial state before submission
- **Scheduled**: RO submitted, project/tasks created, work scheduled
- **In Progress**: Work has started (tasks are being worked on)
- **Awaiting Parts**: Blocked waiting for parts/materials
- **Ready for Handover**: All work complete, QC passed, ready for customer
- **Delivered**: Vehicle handed over to customer
- **Closed**: Payment received, job complete
- **On Hold**: Temporarily paused
- **Cancelled**: Job cancelled

## Current Design (Manual Status Changes)

**The RO status is currently MANUAL** - it does NOT automatically change based on task status. This is by design because:

1. Workshop managers need control over the workflow
2. Multiple tasks may be in different states
3. Status reflects overall job state, not individual task state

## How to Use

1. **After Submission**: Status is "Draft" - manually change to "Scheduled"
2. **When Work Starts**: Change to "In Progress"
3. **If Blocked**: Change to "Awaiting Parts" 
4. **After QC**: Change to "Ready for Handover"
5. **After Handover**: Change to "Delivered"
6. **After Payment**: Change to "Closed"

## Automated Validations

The system DOES enforce these rules:

- Cannot set to "Ready for Handover" unless all QC tasks are Closed
- Cannot set to "Closed" unless linked Sales Invoice is Paid

## Recommendation: Add Auto-Status Updates

Would you like me to add automatic status updates based on:
- Task progress (e.g., auto-set to "In Progress" when first task starts)?
- Material availability (auto-set to "Awaiting Parts")?
- Task completion (auto-set to "Ready for Handover" when all done)?
