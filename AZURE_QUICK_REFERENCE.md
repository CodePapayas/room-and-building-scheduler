# Azure App Service - Quick Reference

## 🚀 Quick Deploy

### First Time Setup

1. **Create App Service** (Azure Portal or CLI)
   ```bash
   az webapp create --name building-rez-app \
     --resource-group building-rez-rg \
     --plan building-rez-plan \
     --runtime "PYTHON:3.12"
   ```

2. **Set SECRET_KEY** (Azure App Settings)
   ```bash
   az webapp config appsettings set \
     --name building-rez-app \
     --resource-group building-rez-rg \
     --settings \
       SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
       SCM_DO_BUILD_DURING_DEPLOYMENT="true"
   ```

3. **Set Startup Command**
   ```bash
   az webapp config set \
     --name building-rez-app \
     --resource-group building-rez-rg \
     --startup-file "gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app"
   ```

4. **Enable App Service Authentication (Entra ID)**
  - Azure Portal → App Service → Authentication
  - Add identity provider → Microsoft Entra ID
  - Action when unauthenticated: **Log in with Microsoft**
  - Keep built-in admin login as secondary check

5. **Add GitHub Secret**
   - Get publish profile: Azure Portal → App Service → Get publish profile
   - GitHub: Settings → Secrets → New secret
   - Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Value: Paste XML content

6. **Deploy**
   ```bash
   git push origin main  # Auto-deploys via GitHub Actions
   ```

## 📋 Common Commands

### Deployment
```bash
# Manual deployment (if not using GitHub Actions)
az webapp up --name building-rez-app --resource-group building-rez-rg --runtime "PYTHON:3.12"

# Trigger GitHub Actions manually
# Go to GitHub → Actions → Select workflow → Run workflow
```

### Monitoring
```bash
# Stream logs
az webapp log tail --name building-rez-app --resource-group building-rez-rg

# Download logs
az webapp log download --name building-rez-app --resource-group building-rez-rg

# Check status
az webapp show --name building-rez-app --resource-group building-rez-rg --query state
```

### Management
```bash
# Restart app
az webapp restart --name building-rez-app --resource-group building-rez-rg

# Stop app
az webapp stop --name building-rez-app --resource-group building-rez-rg

# Start app
az webapp start --name building-rez-app --resource-group building-rez-rg

# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg
```

### Configuration
```bash
# View all settings
az webapp config appsettings list \
  --name building-rez-app \
  --resource-group building-rez-rg

# Add/Update setting
az webapp config appsettings set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --settings KEY=VALUE

# Delete setting
az webapp config appsettings delete \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --setting-names KEY
```

## 💾 Database Management

### Backup
```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Inside SSH
cp /home/building_rez.db /home/backup_$(date +%Y%m%d).db
ls -lh /home/*.db
exit
```

### Restore
```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Inside SSH
cp /home/backup_YYYYMMDD.db /home/building_rez.db
exit

# Restart app
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

### Access Database
```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Inside SSH
sqlite3 /home/building_rez.db
.tables
SELECT * FROM Admins;
.quit
exit
```

## 🔐 Security

### Change Admin Password
```bash
# SSH into app
az webapp ssh --name building-rez-app --resource-group building-rez-rg

# Generate new hash
cd /home/site/wwwroot
python3 generate_admin_hash.py
# Enter new password when prompted

# Update database (use hash from above)
sqlite3 /home/building_rez.db
UPDATE Admins SET password_hash = 'NEW_HASH' WHERE username = 'admin';
.quit
exit
```

### Rotate SECRET_KEY
```bash
# Generate new key
NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Update Azure setting
az webapp config appsettings set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --settings SECRET_KEY="$NEW_KEY"

# Restart app
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

## 📊 Scaling

### Scale Up (More Power)
```bash
# Upgrade to Standard S1
az appservice plan update \
  --name building-rez-plan \
  --resource-group building-rez-rg \
  --sku S1
```

### Scale Out (More Instances)
```bash
# Add more instances
az appservice plan update \
  --name building-rez-plan \
  --resource-group building-rez-rg \
  --number-of-workers 3
```

### Enable Auto-Scale
```bash
# Via Azure Portal
# App Service Plan → Scale out → Configure auto-scale rules
```

## 🌐 Custom Domain

### Add Domain
```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name building-rez-app \
  --resource-group building-rez-rg \
  --hostname yourdomain.com

# Enable HTTPS only
az webapp update \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --https-only true
```

### Create SSL Binding
```bash
# Create free managed certificate
az webapp config ssl create \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --hostname yourdomain.com

# Bind certificate
az webapp config ssl bind \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --certificate-thumbprint [thumbprint] \
  --ssl-type SNI
```

## 📈 Application Insights

### Enable
```bash
# Create Application Insights
az monitor app-insights component create \
  --app building-rez-insights \
  --location eastus \
  --resource-group building-rez-rg

# Get instrumentation key
APPINSIGHTS_KEY=$(az monitor app-insights component show \
  --app building-rez-insights \
  --resource-group building-rez-rg \
  --query instrumentationKey -o tsv)

# Configure app
az webapp config appsettings set \
  --name building-rez-app \
  --resource-group building-rez-rg \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="$APPINSIGHTS_KEY"
```

## 🔧 Troubleshooting

### Check Deployment Status
```bash
# View deployment history
az webapp deployment list-publishing-profiles \
  --name building-rez-app \
  --resource-group building-rez-rg

# Check last deployment
az webapp deployment source show \
  --name building-rez-app \
  --resource-group building-rez-rg
```

### View Application Errors
```bash
# Stream logs
az webapp log tail --name building-rez-app --resource-group building-rez-rg

# Or via Azure Portal
# App Service → Log stream
```

### Restart App
```bash
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

### Reset to Clean State
```bash
# SSH and remove database
az webapp ssh --name building-rez-app --resource-group building-rez-rg
rm /home/building_rez.db
exit

# Restart (database will be recreated)
az webapp restart --name building-rez-app --resource-group building-rez-rg
```

## 🌍 URLs

- **Production**: `https://building-rez-app.azurewebsites.net`
- **Admin**: `https://building-rez-app.azurewebsites.net/admin/login`
- **Azure Portal**: `https://portal.azure.com`
- **GitHub Actions**: `https://github.com/[org]/building-rez/actions`

## 📝 Environment Variables (App Settings)

| Name | Required | Example | Description |
|------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | `abc123...` | Flask session secret (64 chars) |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | ✅ | `true` | Enable build on deploy |
| `WEBSITE_SITE_NAME` | Auto-set | `building-rez-app` | App name (Azure sets this) |

**Note**: Port is configured in the startup command (8000), not in environment variables.

**Startup Command**: `gunicorn -w 2 -t 120 -b 0.0.0.0:8000 app:app`

## 📖 Documentation

- **Full Guide**: [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)
- **Migration Summary**: [AZURE_MIGRATION_SUMMARY.md](AZURE_MIGRATION_SUMMARY.md)
- **README**: [README.md](README.md)

## ✅ Production Checklist

- [ ] Azure App Service created
- [ ] SECRET_KEY configured
- [ ] GitHub Actions secrets set
- [ ] Application deployed and running
- [ ] App Service Authentication enabled (Entra ID)
- [ ] Default admin password changed
- [ ] Custom domain configured (optional)
- [ ] SSL enabled
- [ ] Application Insights enabled
- [ ] Auto-scaling configured
- [ ] Backup strategy implemented

---

**Quick Start**: Just push to `main` branch and GitHub Actions deploys automatically! 🚀
