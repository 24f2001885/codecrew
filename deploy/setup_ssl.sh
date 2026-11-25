#!/usr/bin/env bash
# ==============================================================================
# One-Step Let's Encrypt SSL Setup for codecrew.abhishekpathak.site
# Run on AWS EC2 VPS: bash deploy/setup_ssl.sh
# ==============================================================================

set -euo pipefail

DOMAIN="codecrew.abhishekpathak.site"
EMAIL="abhishekpathak4312@gmail.com"
WEBROOT="/var/www/certbot"
CONF_SRC="deploy/codecrew_production.conf"
CONF_DEST="/etc/nginx/sites-available/codecrew.conf"
CONF_LINK="/etc/nginx/sites-enabled/codecrew.conf"

echo "=========================================================="
echo "🔒 Setting up Let's Encrypt SSL for https://$DOMAIN"
echo "=========================================================="

# 1. Ensure certbot webroot exists
echo "1. Ensuring Certbot challenge directory exists..."
sudo mkdir -p "$WEBROOT"
sudo chown -R www-data:www-data "$WEBROOT"
sudo chmod -R 755 "$WEBROOT"

# 2. Install Certbot if missing
if ! command -v certbot >/dev/null 2>&1; then
    echo "Installing certbot and python3-certbot-nginx..."
    sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx
fi

# 3. Handle certificate issuance
if [ -d "/etc/letsencrypt/live/$DOMAIN" ] && [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "✅ SSL Certificate for $DOMAIN already exists in /etc/letsencrypt/live/$DOMAIN/"
else
    echo "2. Requesting Let's Encrypt certificate..."
    
    # Create temporary HTTP-only configuration to avoid chicken-and-egg SSL error
    sudo bash -c "cat > /etc/nginx/sites-available/codecrew_temp.conf << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name codecrew.abhishekpathak.site;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }
    location / {
        return 200 'CodeCrew SSL Verification in Progress...';
        add_header Content-Type text/plain;
    }
}
EOF"
    sudo ln -sf /etc/nginx/sites-available/codecrew_temp.conf "$CONF_LINK"
    sudo nginx -t && sudo systemctl reload nginx

    # Issue certificate
    sudo certbot certonly --webroot -w "$WEBROOT" -d "$DOMAIN" \
        --non-interactive --agree-tos -m "$EMAIL"

    # Remove temporary config
    sudo rm -f /etc/nginx/sites-available/codecrew_temp.conf
fi

# 4. Link full production HTTPS virtual host configuration
echo "3. Linking production Nginx virtual host with SSL & Reverse Proxy..."
if [ -f "$CONF_SRC" ]; then
    sudo cp "$CONF_SRC" "$CONF_DEST"
elif [ -f "/home/ubuntu/codecrew/$CONF_SRC" ]; then
    sudo cp "/home/ubuntu/codecrew/$CONF_SRC" "$CONF_DEST"
fi

sudo ln -sf "$CONF_DEST" "$CONF_LINK"

# 5. Test and reload Nginx
echo "4. Validating and reloading Host Nginx..."
sudo nginx -t
sudo systemctl reload nginx

# 6. Test HTTPS connectivity
echo "5. Verifying live HTTPS endpoint..."
HTTP_STATUS=$(curl -k -s -o /dev/null -w "%{http_code}" "https://$DOMAIN" || echo "000")
echo "HTTP Response Status: $HTTP_STATUS"

echo "=========================================================="
echo "🎉 SSL Successfully Active! Site live at: https://$DOMAIN"
echo "=========================================================="
