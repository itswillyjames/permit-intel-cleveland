# Deployment Guide

This guide covers deploying the Permit Arbitrage Intelligence Hub to production on Render, Heroku, or AWS.

## Option 1: Deploy to Render (Recommended - Free Tier Available)

### 1. Prepare Repository
```bash
git add .
git commit -m "Deploy to Render"
git push
```

### 2. Create Render Account
- Go to https://render.com
- Sign up with GitHub
- Authorize access

### 3. Deploy via render.yaml
```bash
# Push to GitHub if not already pushed
git push

# Render will automatically detect render.yaml
# Check https://dashboard.render.com for deployment status
```

The `render.yaml` file includes:
- **Backend API** (uvicorn FastAPI)
- **Frontend** (React build)
- **Database** (PostgreSQL)
- **Cache/Queue** (Redis)
- **Background Worker** (Celery)

### 4. Set Environment Variables
In Render Dashboard:
1. Go to Backend service settings
2. Add environment variables:
   ```
   DATABASE_URL=postgresql://... (auto-set)
   REDIS_URL=redis://... (auto-set)
   ```

### 5. Monitor Deployment
```
https://dashboard.render.com → Services → permit-intel-api
```

---

## Option 2: Deploy to Heroku

### 1. Install Heroku CLI
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

### 2. Create App
```bash
heroku create permit-intel-hub
```

### 3. Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:premium-0
```

### 4. Set Environment Variables
```bash
heroku config:set DATABASE_URL=$(heroku config:get DATABASE_URL)
heroku config:set REDIS_URL=$(heroku config:get REDIS_URL)
```

### 5. Deploy
```bash
git push heroku main
```

### 6. Initialize Database
```bash
heroku run "cd backend && python -c 'from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)'"
```

### 7. Scale Dynos
```bash
# Web process
heroku ps:scale web=1

# Worker processes
heroku ps:scale worker=1
```

### 8. View Logs
```bash
heroku logs --tail
```

---

## Option 3: Deploy to AWS ECS + RDS

### 1. Create RDS PostgreSQL Database
```bash
aws rds create-db-instance \
  --db-instance-identifier permit-intel-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username permituser \
  --master-user-password <strong-password>
```

### 2. Create ElastiCache Redis Cluster
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id permit-intel-redis \
  --cache-node-type cache.t3.micro \
  --engine redis
```

### 3. Build and Push Docker Images
```bash
# Backend
aws ecr create-repository --repository-name permit-intel-backend
docker build -t permit-intel-backend backend/
docker tag permit-intel-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/permit-intel-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/permit-intel-backend:latest

# Frontend
aws ecr create-repository --repository-name permit-intel-frontend
docker build -t permit-intel-frontend frontend/
docker tag permit-intel-frontend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/permit-intel-frontend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/permit-intel-frontend:latest
```

### 4. Create ECS Cluster
```bash
aws ecs create-cluster --cluster-name permit-intel-cluster
```

### 5. Create Task Definitions & Services
(See AWS documentation for detailed ECS task definition setup)

### 6. Setup ALB (Application Load Balancer)
- Route `/api/*` → Backend service
- Route `/*` → Frontend service

---

## Post-Deployment Verification

### Health Checks
```bash
# Check API
curl https://your-domain.com/health
# Expected: {"status": "healthy", "service": "permit-intelligence-hub"}

# Check API Docs
https://your-domain.com/docs

# Check Frontend
https://your-domain.com
```

### Initialize Database
```bash
# Via deployment platform (e.g., Render shell)
python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### Fetch Live Data
```bash
# List available cities
curl https://your-domain.com/data/cities

# Fetch SF permits
curl -X POST https://your-domain.com/data/san-francisco/fetch?limit=100

# Result: 100+ permits ingested into live database!
```

---

## Configuration Checklist

### Environment Variables (All Platforms)
- [ ] `DATABASE_URL` – PostgreSQL connection string
- [ ] `REDIS_URL` – Redis connection string
- [ ] `PYTHONUNBUFFERED=1` – Python logging in real-time
- [ ] `NODE_ENV=production` – React optimization

### Database Setup
- [ ] Run migrations: `alembic upgrade head` (if using Alembic)
- [ ] Or: Run schema creation: `python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"`

### Monitoring & Logging
- [ ] Enable platform logging (Render/Heroku/AWS CloudWatch)
- [ ] Set up error alerts
- [ ] Monitor database performance

### Security
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS (all platforms provide free HTTPS)
- [ ] Restrict database access to app only
- [ ] Use environment variables for all secrets (no hardcoding)

---

## Troubleshooting

### Database Connection Failed
```
Error: could not connect to server
```
- Verify DATABASE_URL is correct
- Check database is running
- Verify network/firewall rules

### Port Already in Use
```
Error: Address already in use
```
- Use platform's port assignment ($PORT on Render/Heroku)
- Or kill existing process: `lsof -i :8000`

### Module Not Found
```
ModuleNotFoundError: No module named 'app'
```
- Ensure working directory is correct
- Verify requirements.txt was installed
- Check PYTHONPATH includes the app directory

### Redis Connection Failed
```
Error: Cannot connect to Redis
```
- Verify REDIS_URL is correct
- Check Redis is running
- For background tasks, ensure Redis is accessible from worker process

---

## Performance Tuning

### PostgreSQL
- Enable connection pooling (e.g., PgBouncer)
- Add indexes on frequently queried columns
- Monitor slow queries

### Redis
- Monitor memory usage
- Use appropriate eviction policy
- Consider cluster mode for high concurrency

### API (FastAPI)
- Enable gzip compression
- Use async functions for I/O-bound operations
- Monitor worker processes

### Frontend (React)
- Enable CDN caching
- Minimize bundle size
- Use code splitting

---

## Scaling Strategy

### Stage 1: MVP (Current)
- Single backend dyno / EC2 instance
- Single database instance
- Single Redis instance
- Single frontend instance

### Stage 2: Growth (10k permits/day)
- Backend: 2-3 dynos / instances
- Database: Read replicas + connection pooling
- Redis: Cluster mode
- Frontend: CDN distribution

### Stage 3: Scale (100k+ permits/day)
- Backend: Auto-scaling group
- Database: Multi-region replication
- Redis: Distributed cache
- Frontend: Global CDN
- Elasticsearch for search (optional)

---

## Cost Estimate (Monthly)

### Render (Free Tier)
- Backend API: Free (limited)
- Frontend: Free (limited)
- Database: Free (limited)
- Redis: Free (limited)
- **Total**: $0–$50/month for free tier

### Render (Production)
- Backend API: ~$7/month (0.5 CPU)
- Frontend: ~$7/month
- Database: ~$15/month (1GB storage)
- Redis: ~$7/month
- **Total**: ~$36/month

### Heroku
- Web dyno: $7/month (eco)
- Worker dyno: $7/month
- PostgreSQL: $9/month (mini)
- Redis: $15/month (standard)
- **Total**: ~$38/month

### AWS (EC2 + RDS + ElastiCache)
- EC2 t3.micro: ~$8/month
- RDS db.t3.micro: ~$15/month
- ElastiCache cache.t3.micro: ~$15/month
- Data transfer: ~$5/month
- **Total**: ~$43/month

---

## CI/CD Setup (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: cd backend && pytest
      - name: Deploy to Render
        run: |
          curl -X POST https://api.render.com/deploy/srv-${{ secrets.RENDER_SERVICE_ID }}?key=${{ secrets.RENDER_API_KEY }}
```

---

## Next Steps

1. **Choose platform** (Render, Heroku, or AWS)
2. **Push code** to GitHub
3. **Deploy** using platform tools
4. **Initialize database** via shell
5. **Fetch live data** using `/data/{city}/fetch` endpoint
6. **Test full pipeline** with real permits
7. **Monitor performance** and logs
8. **Scale as needed**

---

**Ready to go live?** Choose your platform and push to production! 🚀
