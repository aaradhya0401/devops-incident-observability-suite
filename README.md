# DevOps Incident Management & Observability Suite

An integrated DevOps project combining an Incident Management System with a complete observability stack for monitoring application metrics, collecting logs, and tracing application requests.

## Project Overview

This project demonstrates how a web application can be monitored using modern DevOps and observability tools.

It combines a Flask-based Incident Management application with Prometheus, Grafana, Loki, Promtail, Jaeger, and OpenTelemetry.

## Key Features

### Incident Management System
- User registration and login
- Incident creation and management
- Incident priority levels
- Incident dashboard
- Application logging
- Prometheus metrics endpoint

### Observability System
- **Prometheus:** Collects application metrics.
- **Grafana:** Visualizes metrics through dashboards.
- **Loki:** Stores and queries application logs.
- **Promtail:** Collects Docker container logs and forwards them to Loki.
- **Jaeger:** Displays distributed traces.
- **OpenTelemetry:** Instruments the Flask application and exports traces.

## Technology Stack

| Category | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite |
| Containerization | Docker |
| Container Orchestration | Docker Compose |
| Metrics | Prometheus |
| Visualization | Grafana |
| Log Management | Loki |
| Log Collection | Promtail |
| Distributed Tracing | Jaeger |
| Instrumentation | OpenTelemetry |

## Project Structure

```text
devops-incident-observability-suite/
│
├── incident-management/
│   ├── templates/
│   ├── static/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── observability/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   └── provisioning/
│   ├── loki/
│   │   └── loki-config.yml
│   └── promtail/
│       └── promtail-config.yml
│
└── docker-compose.yml
```

## Running the Project

### Prerequisites
- Docker Desktop
- Docker Compose
- Git

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd devops-incident-observability-suite
```

### Step 2: Start all services

```bash
docker compose up -d --build
```

### Step 3: Check running containers

```bash
docker compose ps
```

### Step 4: View application logs

```bash
docker compose logs incident-app
```

### Step 5: Stop all services

```bash
docker compose down
```

## Service URLs

| Service | URL |
|---|---|
| Incident Management | http://localhost:5000 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Loki | http://localhost:3100 |
| Jaeger | http://localhost:16686 |

## Testing and Verification

The following components were tested successfully:

- Incident Management application runs inside Docker.
- Prometheus successfully scrapes application metrics.
- Grafana connects to Prometheus and Loki.
- Promtail collects Docker container logs.
- Application logs are visible in Grafana Explore.
- Jaeger receives OpenTelemetry traces.
- Dashboard and incident creation requests are traced.

## Learning Outcomes

Through this project, I gained practical experience with:

- Docker containerization
- Docker Compose
- CI/CD and DevOps concepts
- Application monitoring
- Metrics collection and visualization
- Centralized log management
- Distributed tracing
- OpenTelemetry instrumentation
- Troubleshooting multi-container applications

## Author

Developed as part of a DevOps internship project.