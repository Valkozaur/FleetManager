---
description: How to deploy the dashboard to Hetzner
---

# Deploy Dashboard to Hetzner

1.  **Commit and Push Changes**:
    The GitHub Actions workflow is configured to build and deploy automatically on push to `main`.
    ```bash
    git add .
    git commit -m "feat: add orders dashboard and deployment config"
    git push origin main
    ```

2.  **Verify Deployment**:
    - Check the actions tab in GitHub to see the build progress.
    - The workflow now automatically copies `docker-compose.prod.yml` and `nginx/conf.d/fleetmanager.conf` to the server.
    - Once deployed, visit `https://dashboard.valdanktrading.org`.
    - Ensure DNS records for `dashboard.valdanktrading.org` point to your server IP.
