# Nginx Production Deployment Checklist

Use this checklist to ensure your Nginx setup is production-ready.

## 📋 Pre-Deployment

- [ ] **Domain configured** - DNS A/AAAA records point to server
- [ ] **Server provisioned** - Ubuntu 20.04+ or similar
- [ ] **Firewall configured** - Ports 80, 443, 22 open
- [ ] **Docker installed** - If using containerized deployment
- [ ] **Backup strategy** - Regular backups configured

## 🔧 Nginx Installation

- [ ] **Nginx installed** - Latest stable version
- [ ] **Configuration files copied** - All files in `/etc/nginx/`
- [ ] **Directories created** - `/var/www/freelanceflow/`, `/var/cache/nginx/`
- [ ] **Permissions set** - `www-data:www-data` ownership
- [ ] **Test configuration** - `sudo nginx -t` passes

## 🔒 SSL/TLS Setup

- [ ] **SSL certificate obtained** - Let's Encrypt or commercial
- [ ] **Certificate installed** - Files in `/etc/letsencrypt/` or `/etc/nginx/ssl/`
- [ ] **DH parameters generated** - `/etc/nginx/ssl/dhparam.pem` exists
- [ ] **Auto-renewal configured** - Certbot cron job or systemd timer
- [ ] **SSL test passed** - A+ rating on SSL Labs

## 🛡️ Security Configuration

- [ ] **HSTS enabled** - `Strict-Transport-Security` header set
- [ ] **Security headers** - CSP, X-Frame-Options, etc.
- [ ] **Rate limiting** - Configured for API and auth endpoints
- [ ] **Connection limiting** - Per-IP limits set
- [ ] **Admin IP restriction** - (Optional) Admin panel restricted
- [ ] **Hidden files blocked** - `.git`, `.env`, etc. denied
- [ ] **Server tokens disabled** - Version info hidden

## ⚡ Performance Optimization

- [ ] **Gzip enabled** - Compression for text files
- [ ] **Brotli enabled** - (Optional) Better compression
- [ ] **Static file caching** - Long cache times set
- [ ] **Proxy caching** - Cache zone configured
- [ ] **HTTP/2 enabled** - Modern protocol support
- [ ] **Keep-alive configured** - Connection reuse
- [ ] **Worker processes** - Set to `auto` or CPU count

## 🔌 Backend Integration

- [ ] **Upstream servers** - Django/Gunicorn configured
- [ ] **WebSocket support** - Daphne/Channels working
- [ ] **Health checks** - `/health/` endpoint responding
- [ ] **Load balancing** - (If multiple servers) Configured
- [ ] **Timeouts set** - Appropriate for your app
- [ ] **Buffer sizes** - Optimized for traffic

## 📊 Monitoring & Logging

- [ ] **Access logs** - Enabled and rotating
- [ ] **Error logs** - Enabled with appropriate level
- [ ] **Log rotation** - Logrotate configured
- [ ] **Monitoring tool** - Prometheus, Datadog, etc.
- [ ] **Alerts configured** - For errors and downtime
- [ ] **Performance metrics** - Response times tracked

## 🧪 Testing

- [ ] **HTTP to HTTPS redirect** - Works correctly
- [ ] **WWW redirect** - (If applicable) Configured
- [ ] **API endpoints** - All responding correctly
- [ ] **WebSocket connection** - Real-time features work
- [ ] **Static files** - Served with correct headers
- [ ] **Media uploads** - Working and secure
- [ ] **Rate limiting** - Triggers as expected
- [ ] **Load testing** - Passed with expected traffic

## 🚀 Go-Live

- [ ] **DNS updated** - Points to production server
- [ ] **SSL verified** - HTTPS working on domain
- [ ] **Monitoring active** - Alerts configured
- [ ] **Backup verified** - Recent backup exists
- [ ] **Rollback plan** - Documented and tested
- [ ] **Team notified** - Everyone knows about deployment

## 📈 Post-Deployment

- [ ] **Monitor logs** - First 24 hours closely watched
- [ ] **Check metrics** - Response times, error rates
- [ ] **Test all features** - End-to-end testing
- [ ] **SSL renewal test** - `certbot renew --dry-run`
- [ ] **Performance baseline** - Metrics recorded
- [ ] **Documentation updated** - Any changes documented

## 🔍 Regular Maintenance

### Daily
- [ ] Check error logs for issues
- [ ] Monitor response times
- [ ] Verify SSL certificate validity

### Weekly
- [ ] Review access logs for anomalies
- [ ] Check disk space usage
- [ ] Test backup restoration

### Monthly
- [ ] Update Nginx to latest stable
- [ ] Review and optimize rate limits
- [ ] Audit security headers
- [ ] Performance optimization review

### Quarterly
- [ ] Full security audit
- [ ] Load testing
- [ ] Disaster recovery drill
- [ ] Documentation review

---

## 🆘 Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| DevOps Lead | | |
| Backend Lead | | |
| On-Call Engineer | | |
| Hosting Provider | | |

---

## 📞 Quick Commands

```bash
# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx

# View error logs
sudo tail -f /var/log/nginx/freelanceflow_error.log

# View access logs
sudo tail -f /var/log/nginx/freelanceflow_access.log

# Test SSL
openssl s_client -connect freelanceflow.com:443

# Renew SSL
sudo certbot renew

# Check SSL expiry
sudo certbot certificates
```

---

*Use this checklist for every deployment to ensure nothing is missed!*
