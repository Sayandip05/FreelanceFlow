# Nginx Configuration for FreelanceFlow

This directory contains production-ready Nginx configurations for the FreelanceFlow platform.

## 📁 Files

| File | Purpose |
|------|---------|
| `freelanceflow.conf` | Main production configuration with SSL, rate limiting, caching |
| `local.conf` | Local development configuration (simplified) |
| `nginx.conf` | Main Nginx configuration file (global settings) |
| `ssl-params.conf` | SSL/TLS security parameters |

---

## 🚀 Quick Start

### Local Development

```bash
# Use local.conf for development
docker-compose up -d
```

### Production Deployment

```bash
# 1. Copy configuration to Nginx
sudo cp deployment/nginx/freelanceflow.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/freelanceflow.conf /etc/nginx/sites-enabled/

# 2. Copy main nginx.conf
sudo cp deployment/nginx/nginx.conf /etc/nginx/nginx.conf

# 3. Test configuration
sudo nginx -t

# 4. Reload Nginx
sudo systemctl reload nginx
```

---

## 🔒 SSL Setup

### Using Let's Encrypt (Certbot)

```bash
# 1. Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# 2. Obtain certificate
sudo certbot --nginx -d freelanceflow.com -d www.freelanceflow.com

# 3. Generate Diffie-Hellman parameters
sudo openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048

# 4. Test SSL configuration
sudo nginx -t

# 5. Reload Nginx
sudo systemctl reload nginx

# 6. Set up auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Certificate

```bash
# 1. Place your certificates
sudo mkdir -p /etc/nginx/ssl
sudo cp your-cert.crt /etc/nginx/ssl/
sudo cp your-key.key /etc/nginx/ssl/

# 2. Update paths in freelanceflow.conf
ssl_certificate /etc/nginx/ssl/your-cert.crt;
ssl_certificate_key /etc/nginx/ssl/your-key.key;

# 3. Generate DH parameters
sudo openssl dhparam -out /etc/nginx/ssl/dhparam.pem 2048
```

---

## ⚙️ Configuration Features

### Production (`freelanceflow.conf`)

✅ **Security**
- SSL/TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS with preload
- Security headers (CSP, X-Frame-Options, etc.)
- OCSP stapling

✅ **Performance**
- HTTP/2 support
- Gzip compression
- Static file caching (1 year)
- Proxy caching
- Connection keep-alive
- Load balancing ready

✅ **Rate Limiting**
- API endpoints: 100 req/min
- Auth endpoints: 5 req/min
- General: 200 req/min
- Connection limiting

✅ **WebSocket Support**
- Django Channels integration
- Long-lived connections
- Proper upgrade headers

✅ **Logging**
- Separate access and error logs
- Request ID tracking
- Performance metrics

### Local Development (`local.conf`)

✅ **Simplified Setup**
- No SSL required
- CORS enabled for localhost:3000
- Hot Module Replacement (HMR) support
- Debug logging
- Direct proxy to services

---

## 📊 Rate Limiting

| Zone | Rate | Burst | Use Case |
|------|------|-------|----------|
| `api_limit` | 100/min | 20 | General API calls |
| `auth_limit` | 5/min | 3 | Login, register, password reset |
| `general_limit` | 200/min | 10 | Admin, static pages |
| `conn_limit` | 10 connections | - | Per IP connection limit |

### Adjusting Rate Limits

Edit `freelanceflow.conf`:

```nginx
# Increase API rate limit
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=200r/m;

# Decrease auth rate limit (more strict)
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=3r/m;
```

---

## 🔧 Customization

### Change Domain

Replace `freelanceflow.com` with your domain:

```bash
sed -i 's/freelanceflow.com/yourdomain.com/g' deployment/nginx/freelanceflow.conf
```

### Enable IP Whitelisting for Admin

Uncomment in `freelanceflow.conf`:

```nginx
location /admin/ {
    allow 203.0.113.0/24;  # Your office IP
    deny all;
    # ... rest of config
}
```

### Add More Backend Servers

Edit upstream in `freelanceflow.conf`:

```nginx
upstream django_backend {
    least_conn;
    server web1:8000 max_fails=3 fail_timeout=30s;
    server web2:8000 max_fails=3 fail_timeout=30s;
    server web3:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

---

## 📈 Monitoring

### Check Nginx Status

```bash
# Test configuration
sudo nginx -t

# Check status
sudo systemctl status nginx

# View error logs
sudo tail -f /var/log/nginx/freelanceflow_error.log

# View access logs
sudo tail -f /var/log/nginx/freelanceflow_access.log

# Check cache status
curl -I https://freelanceflow.com/static/css/main.css | grep X-Cache-Status
```

### Performance Testing

```bash
# Test with Apache Bench
ab -n 1000 -c 10 https://freelanceflow.com/api/health/

# Test with wrk
wrk -t12 -c400 -d30s https://freelanceflow.com/

# Test SSL
openssl s_client -connect freelanceflow.com:443 -tls1_3
```

---

## 🐛 Troubleshooting

### 502 Bad Gateway

```bash
# Check if backend is running
docker ps | grep web

# Check backend logs
docker logs freelanceflow_web_1

# Check Nginx error log
sudo tail -f /var/log/nginx/freelanceflow_error.log
```

### WebSocket Connection Failed

```bash
# Check Daphne is running
docker ps | grep daphne

# Test WebSocket connection
wscat -c wss://freelanceflow.com/ws/chat/room1/

# Check Nginx WebSocket config
sudo nginx -T | grep -A 10 "location /ws/"
```

### SSL Certificate Issues

```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
sudo nginx -t
```

### Rate Limiting Too Strict

```bash
# Check rate limit logs
sudo grep "limiting requests" /var/log/nginx/freelanceflow_error.log

# Temporarily disable (for testing only)
# Comment out limit_req lines in freelanceflow.conf
```

---

## 🔐 Security Checklist

- [ ] SSL/TLS certificates installed and valid
- [ ] HSTS enabled with preload
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Admin panel IP-restricted (optional)
- [ ] File upload restrictions in place
- [ ] Hidden files (.git, .env) blocked
- [ ] Server tokens disabled
- [ ] Firewall configured (UFW/iptables)
- [ ] Regular security updates applied

---

## 📚 Additional Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
- [HTTP/2 with Nginx](https://www.nginx.com/blog/http2-module-nginx/)

---

## 🆘 Support

For issues or questions:
1. Check Nginx error logs: `/var/log/nginx/freelanceflow_error.log`
2. Test configuration: `sudo nginx -t`
3. Review this README
4. Check FreelanceFlow documentation

---

*Last Updated: April 14, 2026*  
*Version: 2.0*  
*Status: Production Ready*
