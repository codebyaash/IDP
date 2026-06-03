# DeployForge Frontend Test Templates

Use these files to exercise the main frontend workflows.

## Recommended Walkthrough

1. Sign in with the demo account.

```text
demo@deployforge.local
deployforge123
```

2. Select the `dev` environment and upload `01-dev-baseline.yaml`.

Expected result: plan shows 5 creates, no policy findings, and a monthly cost around 61.

3. Click Deploy.

Expected result: pipeline/history update, cost dashboard populates, and the resource graph shows dependencies.

4. Upload `02-dev-drift-update.yaml` to the same `dev` environment.

Expected result: plan shows create, update, delete, and unchanged drift counts.

5. Deploy `02-dev-drift-update.yaml`.

Expected result: graph changes from storage/subnet focused state to VM/public IP focused state.

6. Open History and click Details on an older deployment.

Expected result: deployment detail page shows logs, plan changes, resource snapshot, drift, policy findings, and rollback.

7. Roll back to the first deployment.

Expected result: history updates and the resource graph returns to the previous resource snapshot.

8. Select `stage` and upload `03-stage-isolation.yaml`.

Expected result: stage has its own history/resources/cost, separate from dev.

9. Upload `04-policy-risk.yaml`.

Expected result: policy findings flag public and high-cost resources.

10. Upload files from `invalid/`.

Expected result: the frontend shows an upload error and the API returns `422`.

## File Map

```text
01-dev-baseline.yaml          Clean baseline with graph dependencies
02-dev-drift-update.yaml      Same environment, changed state for drift detection
03-stage-isolation.yaml       Separate environment demo
04-policy-risk.yaml           Policy finding demo
05-prod-json.json             JSON parser demo
06-basic-bicep.bicep          Basic Bicep parser demo
invalid/duplicate-names.yaml  Duplicate resource-name validation
invalid/bad-shape.yaml        Invalid resources shape validation
```
