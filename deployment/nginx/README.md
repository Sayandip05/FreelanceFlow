# Nginx Configuration for FreelanceFlow

Production-ready Nginx config for the FreelanceFlow platform.
Handles SSL termination, WebSocket routing, static files, and rate limiting.

## 📁 Files

| File | Purpose |
|------|---------|
| `freelanceflow.conf` | Production config — SSL, rate limiting, WebSocket, SPA routing |
| `local.conf` | Local development config (no SSL) |
| `nginx.conf` | Global Nginx settings |

---

## 🚀 Quick Start

### Local Development

```bash
docker-compose up -d
```

### Production Deployment

```bash
# 1. Copy config
sudo cp deployment/nginx/freelanceflow.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/freelanceflow.conf /etc/nginx/sites-enabled/

# 2. Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 SSL Setup (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d freelanceflow.com -d www.freelanceflow.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## ⚙️ What the Config Does

### Routing

| Path | Goes to | Notes |
|------|---------|-------|
| `http://` | `https://` redirect | Let's Encrypt ACME challenge allowed |
| `/api/` | Gunicorn (`web:8000`) | Rate limited: 100 req/min |
| `/api/users/login\|register\|password-reset/` | Gunicorn | Strict limit: 5 req/min |
| `/ws/` | Daphne (`daphne:8001`) | WebSocket, 7-day timeout |
| `/static/` | Local staticfiles dir | 1-year cache |
| `/media/` | Local media dir | 30-day cache, scripts blocked |
| `/admin/` | Gunicorn | No special rate limit |
| `/health/` | Gunicorn | No rate limit, no logging |
| `/` | React SPA (`index.html`) | 1-hour cache |

### Security Headers

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |

### Rate Limiting

| Zone | Rate | Burst | Applies to |
|------|------|-------|------------|
| `api_limit` | 100/min | 20 | `/api/` |
| `auth_limit` | 5/min | 3 | login, register, password-reset |

---

## 🔧 Customization

### Change domain

```bash
sed -i 's/freelanceflow.com/yourdomain.com/g' deployment/nginx/freelanceflow.conf
```

### Restrict admin to your IP

Uncomment in `freelanceflow.conf`:

```nginx
location /admin/ {
    allow 203.0.113.0/24;  # Your office IP
    deny all;
    proxy_pass http://django_backend;
    ...
}
```

### Add a second backend server

```nginx
upstream django_backend {
    server web1:8000;
    server web2:8000;
    keepalive 32;
}
```

---

## 📈 Monitoring

```bash
# Test config
sudo nginx -t

# View error log
sudo tail -f /var/log/nginx/freelanceflow_error.log

# View access log
sudo tail -f /var/log/nginx/freelanceflow_access.log

# Check SSL
sudo certbot certificates

# Renew SSL
sudo certbot renew
```

---

## 🐛 Troubleshooting

### 502 Bad Gateway
```bash
docker ps | grep web                          # Is Gunicorn running?
docker logs freelanceflow_web_1               # Check backend logs
sudo tail -f /var/log/nginx/freelanceflow_error.log
```

### WebSocket Not Connecting
```bash
docker ps | grep daphne                       # Is Daphne running?
sudo nginx -T | grep -A 10 "location /ws/"   # Check WS config
wscat -c wss://freelanceflow.com/ws/test/     # Test connection
```

### SSL Issues
```bash
sudo certbot certificates   # Check expiry
sudo certbot renew          # Renew
sudo nginx -t               # Validate config
```

### Rate Limit Too Strict
```bash
sudo grep "limiting requests" /var/log/nginx/freelanceflow_error.log
# Increase rate in freelanceflow.conf:
# limit_req_zone ... rate=200r/m;
```

---

## 🔐 Security Checklist

- [ ] SSL certificate installed and valid
- [ ] HSTS header enabled
- [ ] Rate limiting active on auth endpoints
- [ ] Hidden files (`/.env`, `/.git`) blocked
- [ ] Executable files in `/media/` blocked
- [ ] Admin access verified
- [ ] WebSocket connections tested

---

*Last Updated: July 2026 | Status: Production Ready*
