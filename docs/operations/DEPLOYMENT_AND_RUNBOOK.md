# Deployment Guide, Operational Runbook & SRE Resilience Specification

## 1. Production Architecture & Orchestration

RemediSync is packaged for zero-friction containerized deployment utilizing **Docker** and **Docker Compose**. The production deployment topology isolates private database services from public Internet traffic through an Nginx edge proxy.

```mermaid
graph TD
    Client["Client Web Browser / Tablet POS"] -->|"HTTPS (443)"| Nginx["Nginx Edge Proxy"]
    
    subgraph Docker_Bridge_Network ["remedisync-internal Network"]
        Nginx -->|"Proxy Pass / (Static)"| Frontend["React/Vite Frontend Container (Port 80)"]
        Nginx -->|"Proxy Pass /api/v1"| Backend["FastAPI Backend Container (Port 8000)"]
        Backend <-->|"PostgreSQL Connection Pool (Port 5432)"| PostgresDB[("PostgreSQL 16 Container")]
    end
```

---

## 2. Container Service Topology

```yaml
# docker-compose.prod.yml reference structure
services:
  postgres:
    image: postgres:16-alpine
    container_name: remedisync-db
    environment:
      POSTGRES_DB: remedisync_prod
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - remedisync-internal
    restart: always

  backend:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    container_name: remedisync-backend
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/remedisync_prod
      ENVIRONMENT: production
      LOG_LEVEL: INFO
    depends_on:
      - postgres
    networks:
      - remedisync-internal
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: remedisync-frontend
    networks:
      - remedisync-internal
    restart: always

  nginx:
    image: nginx:alpine
    container_name: remedisync-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
      - frontend
    networks:
      - remedisync-internal
    restart: always

networks:
  remedisync-internal:
    driver: bridge

volumes:
  pgdata:
    driver: local
```

---

## 3. Production Environment Configuration

Create a `.env.production` file on the deployment server:

```bash
# Environment Mode
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# PostgreSQL Configuration
POSTGRES_USER=remedisync_admin
POSTGRES_PASSWORD=SECURE_HEX_PASSWORD_GENERATED_AT_DEPLOYMENT
POSTGRES_DB=remedisync_prod
DATABASE_URL=postgresql+asyncpg://remedisync_admin:SECURE_HEX_PASSWORD_GENERATED_AT_DEPLOYMENT@postgres:5432/remedisync_prod

# Application & API Security
SECRET_KEY=SECURE_64_CHAR_HEX_KEY
ALLOWED_ORIGINS=https://app.remedisync.internal

# Data & Model File Paths
FEATURE_STORE_PATH=/app/data/processed/feature_matrix.parquet
MODEL_ARTIFACT_PATH=/app/models/forecaster_v1.joblib
```

---

## 4. Operational Runbook

### 4.1 Initial Service Startup
```bash
# 1. Clone repository on production node
git clone https://github.com/organization/RemediSync.git /opt/remedisync
cd /opt/remedisync

# 2. Populate environment secrets
cp .env.production.example .env.production
nano .env.production

# 3. Build containers and launch daemon
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify healthy status across all 4 services
docker compose -f docker-compose.prod.yml ps
```

### 4.2 Database Migrations & Seeding
```bash
# Execute schema migration script
docker compose -f docker-compose.prod.yml exec backend python -m src.database.migrate

# Seed master dimensions (medicines, branches, suppliers)
docker compose -f docker-compose.prod.yml exec backend python -m src.database.seed
```

### 4.3 Automated Nightly Model Retraining Runbook
The ML model inference runs daily at **04:00 AM IST** to prepare reorder feeds before store opening:
```bash
# Add cron job to production server crontab
0 4 * * * docker compose -f /opt/remedisync/docker-compose.prod.yml exec backend python -m src.models.run_daily_inference >> /var/log/remedisync/inference.log 2>&1
```

---

## 5. Backup, Disaster Recovery & High Availability

### 5.1 Automated PostgreSQL Backup
A daily automated database dump is executed at **02:00 AM IST** and shipped to an encrypted off-site cloud storage bucket:
```bash
#!/bin/bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/remedisync"
mkdir -p $BACKUP_DIR

# Dump database inside container
docker exec remedisync-db pg_dump -U remedisync_admin remedisync_prod | gzip > "$BACKUP_DIR/remedisync_$TIMESTAMP.sql.gz"

# Retain local backups for 14 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +14 -delete
```

### 5.2 Restoration Procedure
In the event of database volume corruption:
```bash
# 1. Stop backend services
docker compose -f docker-compose.prod.yml stop backend

# 2. Restore from target dump
gunzip < /var/backups/remedisync/remedisync_TARGET_TIMESTAMP.sql.gz | docker exec -i remedisync-db psql -U remedisync_admin remedisync_prod

# 3. Restart backend services
docker compose -f docker-compose.prod.yml start backend
```

---

## 6. Incident Response & Troubleshooting Playbook

| Symptom | Root Cause | Immediate Diagnostic & Remediation |
| :--- | :--- | :--- |
| **`GET /health` returns 503** | PostgreSQL connection pool exhausted | Check connection count: `docker exec remedisync-db psql -U remedisync_admin -c "SELECT count(*) FROM pg_stat_activity;"`. Restart backend container to recycle connections. |
| **Model Inference Error: Missing Parquet** | Feature store file deleted or corrupted | Re-run feature extraction pipeline: `docker exec remedisync-backend python -m src.features.run_pipeline`. |
| **Reorder Feeds Empty** | Master sales telemetry missing for date range | Verify `daily_sales` table: `SELECT max(date) FROM daily_sales;`. Ingest missing daily receipts. |
| **High Memory Usage on Backend** | Pandas loading full feature store in worker process | Verify that `read_parquet` filters by `columns` parameter and does not load unused raw columns. |
