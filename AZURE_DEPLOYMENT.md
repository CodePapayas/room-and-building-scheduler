# Azure App Service Deployment Guide

This guide covers deploying the Building Reservation System to Azure App Service using Python runtime and GitHub Actions for CI/CD.

## Prerequisites

- Azure subscription
- GitHub repository for the project
- Azure CLI installed (for local management)
- Git installed

## Quick Start

### 1. Create Azure App Service

**Via Azure Portal:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → **Web App**
3. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new or use existing
   - **Name**: `building-rez-app` (must be globally unique)
   - **Publish**: **Code**
   - **Runtime stack**: **Python 3.12**
   - **Operating System**: **Linux**
   - **Region**: Choose closest to your users
   - **App Service Plan**: Create new or select existing
     - Recommended: **Basic B1** or higher for production
4. Click **Review + Create** → **Create**

**Via Azure CLI:**

```bash
# Login to Azure
az login

# Create resource group
az group create --name building-rez-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name building-rez-plan \
  --resource-group building-rez-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --plan building-rez-plan \
  --runtime "PYTHON:3.12"
```

### 2. Configure App Settings (Environment Variables)

**Via Azure Portal:**

1. Go to your Web App → **Configuration** → **Application settings**
2. Click **+ New application setting** and add:

| Name | Value | Description |
|------|-------|-------------|
| `SECRET_KEY` | `[generate-random-key]` | Flask session secret (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Enable build during deployment |

3. Click **Save**

**Via Azure CLI:**

```bash
# Generate SECRET_KEY
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Configure app settings
az webapp config appsettings set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --settings \
    SECRET_KEY="$SECRET_KEY" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

### 3. Configure Startup Command

**Via Azure Portal:**

1. Go to your Web App → **Configuration** → **General settings**
2. **Startup Command**: `gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app`
3. Click **Save**

**Via Azure CLI:**

```bash
az webapp config set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --startup-file "gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app"
```

**Startup Command Explanation:**
- `-w 2`: 2 worker processes (optimal for Basic B1 tier)
- `-t 120`: 120-second timeout for requests
- `-b 0.0.0.0:8000`: Bind to port 8000 (Azure App Service standard port)
- `app:app`: Flask application module and instance

### 4. Set Up GitHub Actions Deployment

#### Step 1: Get Publish Profile

**Via Azure Portal:**

1. Go to your Web App → **Overview**
2. Click **Get publish profile** (downloads XML file)
3. Open the file and copy its contents

**Via Azure CLI:**

```bash
az webapp deployment list-publishing-profiles \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --xml
```

#### Step 2: Add Secret to GitHub Repository

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Value: Paste the publish profile XML
6. Click **Add secret**

#### Step 3: Update Workflow File

Edit `.github/workflows/azure-deploy.yml` and update:

```yaml
env:
  AZURE_WEBAPP_NAME: building-rez-app    # Change to your app name
  PYTHON_VERSION: '3.12'
```

#### Step 4: Deploy

```bash
# Commit and push to trigger deployment
git add .
git commit -m "Configure Azure deployment"
git push origin main
```

GitHub Actions will automatically:
1. Build the application
2. Install dependencies
3. Deploy to Azure App Service
4. Database will be initialized on first deployment

### 5. Verify Deployment

1. Go to your Web App → **Overview**
2. Click the **URL** (e.g., `https://building-rez-app.azurewebsites.net`)
3. You should see the application running
4. Access admin panel: `https://building-rez-app.azurewebsites.net/admin/login`
   - Username: `admin`
   - Password: `admin123` (⚠️ CHANGE IMMEDIATELY!)

## Database Persistence

Azure App Service persists the `/home` directory across deployments. The database is stored at `/home/building_rez.db` and will be retained even after redeployments.

### Backup Database

**Via Azure Portal:**

1. Go to your Web App → **SSH** (under Development Tools)
2. Run:
   ```bash
   cp /home/building_rez.db /home/backup_$(date +%Y%m%d).db
   ```

**Download backup locally:**

```bash
# Using Azure CLI
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Inside SSH session
cp /home/building_rez.db /home/site/wwwroot/backup.db
exit

# Download via FTP or use Azure Storage Explorer
```

### Restore Database

```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Restore backup
cp /home/backup_YYYYMMDD.db /home/building_rez.db

# Restart app
exit
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

## Post-Deployment Configuration

### 1. Enable App Service Authentication (Perimeter)

1. Go to your Web App → **Authentication**
2. Click **Add identity provider**
3. Choose **Microsoft Entra ID** (create a new app registration or use existing)
4. Set **Action to take when request is not authenticated** to **Log in with Microsoft**
5. Save changes
6. Keep the built-in admin login active as a secondary authorization layer

### 2. Change Default Admin Password

```bash
# SSH into your app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Generate new password hash
cd /home/site/wwwroot
python3 generate_admin_hash.py

# Update database
sqlite3 /home/building_rez.db
UPDATE Admins SET password_hash = 'NEW_HASH_HERE' WHERE username = 'admin';
.quit

exit
```

### 3. Configure Custom Domain (Optional)

**Via Azure Portal:**

1. Go to your Web App → **Custom domains**
2. Click **Add custom domain**
3. Follow the wizard to verify and add your domain
4. Configure SSL certificate (free via App Service Managed Certificate)

**Via Azure CLI:**

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name building-rez-app \
  --resource-group building-rez-rg \
  --hostname yourdomain.com

# Enable HTTPS
az webapp update \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --https-only true
```

### 4. Enable Application Insights (Monitoring)

**Via Azure Portal:**

1. Go to your Web App → **Application Insights**
2. Click **Turn on Application Insights**
3. Create new or select existing Application Insights resource
4. Click **Apply**

**Via Azure CLI:**

```bash
# Create Application Insights
az monitor app-insights component create \
  --app building-rez-insights \
  --location eastus \
  --resource-group building-rez-rg

# Link to Web App
az webapp config appsettings set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="[your-key]"
```

## Scaling

### Vertical Scaling (More Power)

**Via Azure Portal:**

1. Go to your Web App → **Scale up (App Service plan)**
2. Select a higher tier (e.g., S1, P1V2)
3. Click **Apply**
4. **Note**: Adjust worker count in startup command if needed (e.g., `-w 4` for larger tiers)

**Via Azure CLI:**

```bash
az appservice plan update \
  --name building-rez-plan \
  --resource-group building-rez-rg \
  --sku S1

# Update startup command for more workers
az webapp config set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --startup-file "gunicorn -w 4 -t 120 -b 0.0.0.0:8000 app:app"
```

### Horizontal Scaling (More Instances)

**Via Azure Portal:**

1. Go to your Web App → **Scale out (App Service plan)**
2. Configure auto-scale rules or manual scale
3. Set instance count (2-10 recommended for production)

**Via Azure CLI:**

```bash
az appservice plan update \
  --name building-rez-plan \
  --resource-group building-rez-rg \
  --number-of-workers 2
```

## Monitoring and Logs

### View Logs

**Via Azure Portal:**

1. Go to your Web App → **Log stream**
2. View real-time application logs

**Via Azure CLI:**

```bash
# Stream logs
az webapp log tail \
  --name building-rez-app \
  --resource-group building-rez-rg

# Download logs
az webapp log download \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --log-file logs.zip
```

### Enable Diagnostic Logging

**Via Azure Portal:**

1. Go to your Web App → **App Service logs**
2. Enable:
   - Application Logging (File System): **Error**
   - Web server logging: **File System**
   - Detailed error messages: **On**
3. Click **Save**

## Troubleshooting

### Application Won't Start

```bash
# Check logs
az webapp log tail --name building-rez-app --resource-group building-rez-rg

# Check startup command
az webapp config show --name building-rez-app --resource-group building-rez-rg

# Restart app
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

### Database Issues

```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Check if database exists
ls -la /home/building_rez.db

# Check database integrity
sqlite3 /home/building_rez.db "PRAGMA integrity_check;"

# Reinitialize database (WARNING: data loss)
rm /home/building_rez.db
cd /home/site/wwwroot
python3 -c "from app import init_db; init_db()"
exit
```

### Performance Issues

1. Check Application Insights for slow requests
2. Scale up or scale out
3. Enable caching
4. Optimize database queries

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/azure-deploy.yml`) automatically:

1. **On push to main branch:**
   - Checks out code
   - Sets up Python 3.12
   - Installs dependencies
   - Uploads build artifact

2. **Deployment:**
   - Downloads artifact
   - Deploys to Azure App Service
   - Runs post-build commands (database init)

### Manual Deployment

If you need to deploy manually:

```bash
# Using Azure CLI
cd /path/to/building-rez
az webapp up \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --runtime "PYTHON:3.12"
```

## Security Best Practices

### Application Settings

- [ ] Set strong `SECRET_KEY` (64+ characters)
- [ ] Change default admin password
- [ ] Enable HTTPS only
- [ ] Restrict CORS if needed

### Networking

- [ ] Consider Azure Private Link for database
- [ ] Use Azure Front Door for DDoS protection
- [ ] Configure IP restrictions if needed

### Authentication

- [ ] Enable Azure AD authentication (optional)
- [ ] Implement rate limiting
- [ ] Set up audit logging

## Cost Optimization

- Use **Basic B1** tier for small workloads (~$13/month)
- Use **Standard S1** for production (~$70/month)
- Enable auto-scaling to scale down during off-hours
- Monitor usage with Azure Cost Management

## Maintenance

### Regular Tasks

**Daily:**
- Monitor application logs
- Check Application Insights dashboard

**Weekly:**
- Backup database
- Review security alerts
- Check resource usage

**Monthly:**
- Update dependencies
- Review and optimize costs
- Security audit

### Backup Strategy

Set up Azure Automation runbook for automated backups:

```bash
# Create backup script in Azure Automation
# Schedule to run daily at 2 AM
# Copy /home/building_rez.db to Azure Blob Storage
```

## Support

- **Azure Status**: https://status.azure.com
- **Azure Support**: Create ticket in Azure Portal
- **Application Logs**: Web App → Log stream
- **GitHub Actions**: Repository → Actions tab

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Python on App Service](https://docs.microsoft.com/azure/app-service/quickstart-python)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [App Service Diagnostics](https://docs.microsoft.com/azure/app-service/overview-diagnostics)

---

**Deployment Method**: Azure App Service + GitHub Actions  
**Runtime**: Python 3.12 on Linux  
**Database**: SQLite on persistent /home storage  
**CI/CD**: Automated via GitHub Actions
