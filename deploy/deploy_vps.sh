#!/usr/bin/env bash
# ==============================================================================
# CodeCrew Automated VPS Production Deployment Script
# Target: AWS EC2 Ubuntu VPS | Domain: codecrew.abhishekpathak.site
# Internal Container: 127.0.0.1:5003 -> Host Nginx Reverse Proxy
# ==============================================================================

set -euo pipefail

DOMAIN="codecrew.abhishekpathak.site"
APP_DIR="/home/ubuntu/codecrew"
NGINX_AVAILABLE="/etc/nginx/sites-available/codecrew.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/codecrew.conf"

echo "=========================================================="
echo "🚀 Deploying CodeCrew Production to $DOMAIN"
echo "=========================================================="

# 1. Clone or pull repository
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Cloning repository to $APP_DIR..."
    git clone https://github.com/24f2001885/codecrew.git "$APP_DIR"
fi

cd "$APP_DIR"
echo "Fetching latest changes..."
git fetch origin MAIN || git fetch origin
git checkout -f MAIN || git checkout -f main
git reset --hard origin/MAIN || git reset --hard origin/main

# 2. Configure Production .env
if [ ! -f .env ]; then
    echo "Configuring production .env file..."
    if [ -f .env.production ]; then
        cp .env.production .env
    else
        cp .env.prod.example .env
        RAND_SECRET=$(openssl rand -hex 32)
        RAND_CSRF=$(openssl rand -hex 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=${RAND_SECRET}/" .env
        sed -i "s/WTF_CSRF_SECRET_KEY=.*/WTF_CSRF_SECRET_KEY=${RAND_CSRF}/" .env
    fi
fi

# Ensure production environment flags
sed -i "s/FLASK_ENV=.*/FLASK_ENV=production/" .env
sed -i "s/SESSION_COOKIE_SECURE=.*/SESSION_COOKIE_SECURE=True/" .env

# 3. Setup Nginx Virtual Host
echo "Configuring Nginx Reverse Proxy..."
sudo cp deploy/codecrew_production.conf "$NGINX_AVAILABLE"
sudo ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"

# Ensure Certbot webroot exists
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot

# 4. SSL Certificate Setup via Certbot (if not already issued)
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Attempting to issue Let's Encrypt SSL certificate for $DOMAIN..."
    # Temporarily ensure HTTP Nginx reload for ACME challenge
    sudo nginx -t && sudo systemctl reload nginx || true
    sudo certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" --non-interactive --agree-tos -m abhishekpathak4312@gmail.com || echo "Note: Run certbot manually once DNS propagates."
fi

# 5. Build and Restart Docker Stack (Port 5003)
echo "Starting Docker Compose production stack..."
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --build

echo "Awaiting application container readiness..."
sleep 8

# 6. Database Initialization & Seeding
echo "Running database schema initialization and initial seeding..."
docker compose -f docker-compose.prod.yml exec -T web python seed.py --sample --coder || true

# 7. Reload Nginx
echo "Validating and reloading Host Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# 8. Health Check
echo "Testing local HTTP response on port 5003..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5003/ || echo "000")
if [ "$HEALTH_STATUS" -eq 200 ] || [ "$HEALTH_STATUS" -eq 302 ]; then
    echo "✅ CodeCrew container is HEALTHY (HTTP $HEALTH_STATUS)!"
else
    echo "⚠️ Warning: Container returned HTTP $HEALTH_STATUS. Checking docker logs:"
    docker compose -f docker-compose.prod.yml logs --tail=30 web
fi

echo "=========================================================="
echo "🎉 CodeCrew Deployment Complete! Live at https://$DOMAIN"
echo "=========================================================="
