# Deployment Guide

This guide covers deploying Gopnik in various environments from development to production.

## 📖 Complete Deployment Documentation

For comprehensive deployment documentation, see:
- **[Docker Compose Development](../../docker-compose.yml)**: Development environment setup
- **[Docker Compose Production](../../docker-compose.prod.yml)**: Production container orchestration
- **[Deployment Scripts](../../scripts/deploy.sh)**: Automated deployment and management
- **[Configuration Files](../../config/)**: Environment-specific configurations
- **[Monitoring Setup](../../docker/prometheus/)**: Comprehensive monitoring and alerting

## 🚀 Quick Deployment Options

### Development Environment

```bash
# Clone repository
git clone https://github.com/happy2234/gopnik.git
cd gopnik

# Start development stack
docker-compose up -d

# Access services:
# - API: http://localhost:8000/docs
# - Web: http://localhost:8080
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

### Production Environment

```bash
# Deploy production stack
./scripts/deploy.sh

# Or manually with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### Single Container Deployments

```bash
# CLI container
docker run -v /path/to/docs:/home/gopnik/data gopnik/cli process document.pdf

# API server
docker run -p 8000:80 gopnik/api

# Web interface
docker run -p 8080:80 gopnik/web
```

## 🔧 Configuration Management

### Environment-Specific Configurations

- **[Development Config](../../config/development.yaml)**: Development environment settings
- **[Production Config](../../config/production.yaml)**: Production environment settings

### Environment Variables

Key environment variables for deployment:

```bash
# Deployment environment
DEPLOYMENT_ENV=production

# Services to deploy
SERVICES="gopnik-api gopnik-web nginx-lb redis postgres"

# Build configuration
BUILD_IMAGES=true
RUN_MIGRATIONS=true
BACKUP_BEFORE_DEPLOY=true

# Security
GOPNIK_SECRET_KEY=your-secret-key
POSTGRES_PASSWORD=your-db-password
GRAFANA_PASSWORD=your-grafana-password
```

## 📊 Monitoring and Alerting

### Prometheus Metrics

The deployment includes comprehensive monitoring:

- **Application Metrics**: Processing time, error rates, queue sizes
- **System Metrics**: CPU, memory, disk usage
- **Infrastructure Metrics**: Database, Redis, Nginx performance

### Grafana Dashboards

Pre-configured dashboards for:
- Application performance monitoring
- System resource utilization
- Error tracking and alerting
- User activity and usage patterns

### Alerting Rules

Automated alerts for:
- High error rates
- Memory/disk usage thresholds
- Service availability issues
- Processing queue backlogs

## 🔒 Security Considerations

### SSL/TLS Configuration

Production deployments include:
- Automatic SSL certificate generation
- HTTPS enforcement
- Secure headers configuration
- Rate limiting and DDoS protection

### Secrets Management

Secure handling of:
- API keys and tokens
- Database passwords
- SSL certificates
- Encryption keys

### Network Security

- Container network isolation
- Firewall configuration
- VPN integration support
- Access control lists

## 🔄 Backup and Recovery

### Automated Backups

The deployment script includes:
- Pre-deployment backups
- Audit log archival
- Configuration backups
- Database snapshots

### Disaster Recovery

- Rollback procedures
- Data restoration processes
- Service recovery workflows
- Monitoring and alerting for failures

## 📈 Scaling and Performance

### Horizontal Scaling

- Load balancer configuration
- Multi-instance deployments
- Database clustering
- Cache layer optimization

### Performance Tuning

- Resource allocation guidelines
- Memory optimization
- CPU utilization tuning
- I/O performance optimization

## 🛠️ Maintenance and Updates

### Update Procedures

```bash
# Update to latest version
./scripts/deploy.sh

# Update specific services
SERVICES="gopnik-api" ./scripts/deploy.sh

# Rollback if needed
./scripts/deploy.sh rollback
```

### Health Monitoring

```bash
# Check deployment status
./scripts/deploy.sh status

# Run health checks
./scripts/deploy.sh health

# View logs
docker-compose logs -f gopnik-api
```

### Cleanup and Optimization

```bash
# Clean up old images
./scripts/deploy.sh cleanup

# Create manual backup
./scripts/deploy.sh backup
```

## 🆘 Troubleshooting

### Common Issues

1. **Container startup failures**: Check logs and resource allocation
2. **Database connection issues**: Verify network connectivity and credentials
3. **SSL certificate problems**: Check certificate validity and paths
4. **Performance issues**: Monitor resource usage and scaling needs

### Diagnostic Commands

```bash
# Check container status
docker-compose ps

# View service logs
docker-compose logs service-name

# Check resource usage
docker stats

# Network connectivity
docker-compose exec service-name ping other-service
```

### Getting Help

- **[GitHub Issues](https://github.com/happy2234/gopnik/issues)**: Report deployment issues
- **[Discussions](https://github.com/happy2234/gopnik/discussions)**: Get community help
- **[Wiki](https://github.com/happy2234/gopnik/wiki)**: Community documentation

---

For detailed deployment procedures and advanced configurations, refer to the complete deployment documentation linked at the top of this page.