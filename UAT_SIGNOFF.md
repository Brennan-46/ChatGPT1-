# UAT Sign-off Template

## Environment
- Release tag:
- Date:
- Staging URL:

## Real Credential Validation
- Google Calendar OAuth configured and validated: [ ]
- Slack bot token configured and validated: [ ]

## Tenant Matrix
- Tenants tested:
- Users tested:

## Required Passes
- Scripted UAT run (`./scripts/uat_go_live.sh`) passed: [ ]
- HITL lifecycle (run -> approve -> resume) per tenant passed: [ ]
- Audit retrieval by run_id passed: [ ]
- Alerts endpoint sanity check passed: [ ]

## Go-Live Decision
- Approved for production: [ ]
- Approver name:
- Timestamp:

## Rollback Readiness
- Backup validated: [ ]
- Restore dry run validated: [ ]
- Rollback plan reviewed: [ ]
