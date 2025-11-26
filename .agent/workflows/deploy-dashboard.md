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

2.  **Sync Configuration (Manual Step)**:
    Since we modified `nginx/conf.d/fleetmanager.conf`, we need to ensure this file is updated on the server. The `deploy` job in GitHub Actions only runs `docker compose pull` and `up`. It assumes the repo is checked out or files are present.
    
    If the server has the repo checked out at `~/fleetmanager`, the `git pull` might be needed, or we can `scp` the config.
    
    **Recommended**: Update the `deploy` step in `.github/workflows/deploy-email-processor.yml` to `git pull` first, OR manually copy the file.
    
    Manual copy:
    ```bash
    scp -r nginx/conf.d/fleetmanager.conf root@<your-server-ip>:~/fleetmanager/nginx/conf.d/
    scp docker-compose.prod.yml root@<your-server-ip>:~/fleetmanager/
    ```

3.  **Verify Deployment**:
    - Check the actions tab in GitHub to see the build progress.
    - Once deployed, visit `https://dashboard.valdanktrading.org`.
    - Ensure DNS records for `dashboard.valdanktrading.org` point to your server IP.
