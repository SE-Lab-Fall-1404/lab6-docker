# Microservices Architecture with Docker

A complete RESTful API with CRUD operations, load balancing, and shared PostgreSQL database using Docker Compose.

## Components

| Service | Technology | Port | Replicas |
|---------|------------|------|----------|
| Load Balancer | Nginx | 80 | 1 |
| Backend API | Flask/Python | 5000 | 3 (scalable) |
| Database | PostgreSQL | 5432 | 1 |

## Prerequisites

- Docker
- Docker Compose
- Play with Docker (https://labs.play-with-docker.com)

## Quick Start

```bash
# Clone or create project
mkdir microservices-demo && cd microservices-demo

# Create directory structure
mkdir -p nginx backend

# Build and run
docker-compose up -d --build

# Wait for services to be ready
sleep 10
```

## Verification

### Running Containers
```bash
docker container ls
```
<img width="1497" height="322" alt="image" src="https://github.com/user-attachments/assets/58574813-02bb-47be-892e-a55eaf2a84c1" />


### Docker Images
```bash
docker image ls | grep -E "(backend|nginx|postgres)"
```
<img width="928" height="282" alt="image" src="https://github.com/user-attachments/assets/0b2784ad-2b5e-4522-82d2-a8f76ad4c513" />


## API Testing

### Health Check
```bash
curl http://localhost/health
```
Expected output:
```json
{"status":"healthy","database":"connected","hostname":"backend1"}
```

### Create Item
```bash
curl -X POST http://localhost/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Docker Book", "description": "Master Docker containers"}'
```
<img width="824" height="117" alt="image" src="https://github.com/user-attachments/assets/72a0238b-ab43-4136-b5fd-fce030dc1aae" />


### Get All Items
```bash
curl http://localhost/items
```
<img width="1482" height="97" alt="image" src="https://github.com/user-attachments/assets/82e80c75-38e6-4dec-83aa-e35d2cfb2147" />

### Get Single Item
```bash
curl http://localhost/items/1
```

### Update Item
```bash
curl -X PUT http://localhost/items/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated: Complete Docker guide"}'
```

### Delete Item
```bash
curl -X DELETE http://localhost/items/1
```

## Load Balancing Demo

Send multiple requests to see traffic distribution:
```bash
for i in {1..6}; do
  echo "Request $i:"
  curl -s http://localhost/ | grep hostname
  echo ""
done
```
<img width="1071" height="548" alt="image" src="https://github.com/user-attachments/assets/58e5d9fe-921f-4a99-b4b6-93885a7d77fb" />


## Scaling (Handle Increased Load)

Scale backend instances without code changes:

```bash
# Scale to 5 instances
docker-compose up -d --scale backend=5 --no-recreate

# Update Nginx config
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1000;
}
http {
    upstream backend_servers {
        server backend1:5000;
        server backend2:5000;
        server backend3:5000;
        server backend4:5000;
        server backend5:5000;
    }
    server {
        listen 80;
        location / {
            proxy_pass http://backend_servers;
            proxy_set_header Host $host;
        }
    }
}
EOF

# Restart Nginx
docker-compose restart nginx-lb

# Verify scaling
docker container ls | grep backend
```
<img width="1354" height="191" alt="image" src="https://github.com/user-attachments/assets/a611773f-a7de-42b1-a8da-381fe368572d" />


## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info with hostname |
| GET | `/health` | Health check |
| GET | `/items` | List all items |
| POST | `/items` | Create new item |
| GET | `/items/{id}` | Get item by ID |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |
| POST | `/reset` | Reset database (test only) |

## Project Structure

```
microservices-demo/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── nginx/
    ├── Dockerfile
    └── nginx.conf
```

## Troubleshooting

### Check Logs
```bash
docker logs backend1
docker logs nginx_lb
docker logs postgres_db
```

### Restart Services
```bash
docker-compose restart
```

### Full Cleanup
```bash
docker-compose down -v
docker system prune -f
```

## **Stateless Concept & Our Usage**

### **What is Stateless?**

**Stateless** means each request is independent - the server doesn't remember anything from previous requests. Every request contains all information needed to process it.

**Analogy:** 
- ❌ **Stateful**: Waiter remembers your order from yesterday
- ✅ **Stateless**: You order fresh every time

### **How We Used Stateless in Our Experiment**

**1. Backend APIs are Stateless:**
```python
# Each request works independently
GET /items/1    # No session, no memory of previous calls
POST /items     # Just insert data, don't remember who sent it
```

**2. Load Balancing Works Because of Stateless:**
```nginx
upstream backend_servers {
    server backend1:5000;
    server backend2:5000;  # Any server can handle any request
    server backend3:5000;
}
```
Nginx sends requests randomly to backend1, backend2, or backend3. They all work the same.

**3. Easy Scaling:**
```bash
# Added 2 more servers instantly
docker-compose up -d --scale backend=5
```
No code changes needed because new servers don't need to know past requests.

**4. Fault Tolerance:**
If `backend1` crashes → requests automatically go to `backend2` or `backend3`. User doesn't notice anything!
