
# Cloud Task - Deployment Architecture 🚀

FastAPI application demonstrating **multiple cloud deployment strategies** — from fully managed PaaS to manual production-grade IaaS setup.

Goal: Understand the differences in abstraction levels, operational responsibility, security considerations, and scaling approaches between PaaS and IaaS.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Process Manager**: Gunicorn (production)
- **Reverse Proxy**: Nginx (production)
- **Containerization**: Docker
- **PaaS Provider**: Render
- **IaaS Provider**: AWS EC2
- **OS (IaaS)**: Ubuntu Linux

## 🏗️ Deployment Strategies Covered

| # | Tier          | Provider   | Method                  | Automation | Container | Key Learnings                              |
|---|---------------|------------|-------------------------|------------|-----------|--------------------------------------------|
| 1 | PaaS          | Render     | Native Python           | Full CI/CD | No        | Zero server management, git push → deploy  |
| 2 | PaaS          | Render     | Docker                  | Full CI/CD | Yes       | Consistent environments across platforms   |
| 3 | IaaS Dev      | AWS EC2    | Manual SSH + venv       | None       | No        | Basic Linux admin, security groups, SSH    |
| 4 | IaaS Prod     | AWS EC2    | Gunicorn + systemd + Nginx | Manual   | No        | Hardening, reverse proxy, service daemon   |

### 1. Render – Native Python Deployment (PaaS)

- Auto-detected Python environment
- Uses `render.yaml` for configuration
- Zero-downtime deploys on every push

### 2. Render – Docker Deployment (PaaS)

- Dockerfile-based build
- Same git → deploy workflow
- Guarantees identical runtime everywhere

### 3. AWS EC2 – Development Setup (IaaS)

- Fresh Ubuntu t3.micro / t2.micro instance
- Manual SSH access (`.pem` key)
- Python `venv` created directly on server
- Application bound to `0.0.0.0:8000`
- Security Group allows port 8000

### 4. AWS EC2 – Production Hardened Setup (IaaS)

Modern production architecture on a single EC2 instance:
```

Internet
 ↓
AWS Security Group (80, 443 only)
 ↓
 Nginx (port 80 / 443) – public-facing
 ↓
(proxy_pass) 127.0.0.1:8000
 ↓
Gunicorn – manages 4× Uvicorn workers
 ↓
FastAPI application

text

````
Features:

- Gunicorn + Uvicorn workers for concurrency
- systemd service (auto-start, restart on crash)
- Nginx as secure reverse proxy
- App **never** listens on public IP
- Only ports 80/443 open to world

## 🔐 Key Security & Architecture Lessons

- Binding to `0.0.0.0` vs `127.0.0.1`
- Why you should **never** expose application servers directly
- Least-privilege Security Groups
- systemd unit files for reliable background services
- Request flow visibility: Client → Nginx → Gunicorn → FastAPI

## 🚀 Quick Start (Local Development)

```bash
# 1. Clone the repository
git clone https://github.com/supreetbhat/cloud-task.git
cd cloud-task

# 2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate    # Linux / macOS
# or: venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run development server
uvicorn main:app --reload --port 8000
````

Open → [http://localhost:8000](http://localhost:8000/)

## 📁 Important Files

|File|Purpose|
|---|---|
|main.py|FastAPI application|
|requirements.txt|Python dependencies|
|Dockerfile|Container definition|
|render.yaml|Render.com native configuration|
|service.service|systemd unit file example|

## 📌 Next Steps / Possible Improvements

- Add GitHub Actions → Render & ECR deployment
- Infrastructure as Code (Terraform / AWS CDK)
- Enable HTTPS (Let’s Encrypt or AWS ACM)
- Scale horizontally (ALB + Auto Scaling Group)
- Add observability (CloudWatch / Prometheus + Grafana)

Contributions, issues, and suggestions are welcome!

---

Made with ❤️ and many sudo systemctl restart moments Last updated: March 2025
