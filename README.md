# ghas-mttr

GitHub Advanced Security Mean Time to Remediate (MTTR)

## Usage

**`.github/workflows/ghas-mttr.yml`**

```yaml
name: MTTR Report Action

on:
  schedule:
    # Weekly at 9:00am on Thursday
    - cron: '0 9 * * 4'
  # Manually run the action
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      # [optional]
      # This Action step with use a GitHub App versus a PAT Token (better for 
      # security and access control) - see the GitHub Actions documentation for
      # more details.
      - name: Get Token
        id: get_workflow_token
        uses: peter-murray/workflow-application-token-action@v1
        with:
          application_id: ${{ secrets.APPLICATION_ID }}
          application_private_key: ${{ secrets.APPLICATION_PRIVATE_KEY }}

      - uses: advanced-security/ghas-mttr@main
        with:
          exporter: 'issue_summary'
          token: ${{ steps.get_workflow_token.outputs.token }}
```
