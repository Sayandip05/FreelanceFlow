# Nginx Production Deployment Checklist

Use this checklist before going live.

---

## 📋 Pre-Deployment

- [ ] DNS A record points to your server IP
- [ ] Ports 80 and 443 open in firewall
- [ ] Docker installed and `docker-compose up` works locally

---

## 🔧 Nginx Setup

- [ ] Config copied: `sudo cp deployment/nginx/freelanceflow.conf /etc/nginx/sites-available/`
- [ ] Symlink created: `sudo ln -s /etc/nginx/sites-available/freelanceflow.conf /etc/nginx/sites-enabled/`
- [ ] Config test passes: `sudo nginx -t`

---

## 🔒 SSL

- [ ] Certbot installed: `sudo apt-get install certbot python3-certbot-nginx`
- [ ] Certificate obtained: `sudo certbot --nginx -d freelanceflow.com -d www.freelanceflow.com`
- [ ] Auto-renewal tested: `sudo certbot renew --dry-run`
- [ ] HTTPS works in browser

---

## 🛡️ Security

- [ ] HSTS header present: `curl -I https://freelanceflow.com | grep Strict`
- [ ] Hidden files blocked: `curl https://freelanceflow.com/.env` → 403
- [ ] Auth rate limit active (login, register, password-reset)
- [ ] Executable scripts in `/media/` blocked

---

## 🔌 Backend Integration

- [ ] `/health/` endpoint responds: `curl https://freelanceflow.com/health/`
- [ ] `/api/` proxies to Django: test any API endpoint
- [ ] `/ws/` WebSocket works: `wscat -c wss://freelanceflow.com/ws/test/`
- [ ] `/static/` and `/media/` files served correctly
- [ ] `/` loads React app (try a deep link like `/dashboard`)

---

## 📊 Logging

- [ ] Access log writing: `sudo tail -f /var/log/nginx/freelanceflow_access.log`
- [ ] Error log writing: `sudo tail -f /var/log/nginx/freelanceflow_error.log`

---

## 🚀 Go-Live

- [ ] `sudo nginx -t` passes
- [ ] `sudo systemctl reload nginx` done
- [ ] End-to-end smoke test completed
- [ ] SSL valid and HTTPS loads correctly

---

## 📞 Quick Commands

```bash
sudo nginx -t                                          # Test config
sudo systemctl reload nginx                            # Reload
sudo systemctl restart nginx                           # Full restart
sudo tail -f /var/log/nginx/freelanceflow_error.log    # Error log
sudo tail -f /var/log/nginx/freelanceflow_access.log   # Access log
sudo certbot certificates                              # Check SSL
sudo certbot renew                                     # Renew SSL
```

---

## 🔁 Maintenance

**Weekly**
- Check error logs for 502s or rate-limit hits
- Verify SSL cert expiry (`sudo certbot certificates`)

**Monthly**
- `sudo apt-get upgrade nginx` — keep Nginx updated
- Review rate limit zones if traffic grows

---

*Use this checklist for every deployment to ensure nothing is missed.*
