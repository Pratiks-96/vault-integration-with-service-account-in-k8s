# vault-integration-with-service-account-in-k8s

Vault (Secret Store)
     │
     │ (Vault Agent Injector)
     ▼
Kubernetes Pod
 ├── Vault Agent Sidecar
 │     └── writes secrets to /vault/secrets/config
 │
 └── Microservice (FastAPI)
       └── reads secret file
       └── displays on web page

helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

helm install vault hashicorp/vault \
  --set "server.dev.enabled=true"

  Step 2: Enable Vault Kubernetes Auth

Exec into vault pod:

kubectl exec -it vault-0 -- sh

Inside pod:

vault auth enable kubernetes

Configure:

vault write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
Step 3: Create Secret in Vault
vault kv put secret/myapp \
   username="pavan" \
   password="devsecops123"

Verify:

vault kv get secret/myapp
Step 4: Create Vault Policy

Create file:

policy.hcl

path "secret/data/myapp" {
  capabilities = ["read"]
}

Apply policy:

vault policy write myapp-policy policy.hcl
Step 5: Create Kubernetes ServiceAccount

serviceaccount.yaml

apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa

Apply:

kubectl apply -f serviceaccount.yaml
Step 6: Create Vault Role
vault write auth/kubernetes/role/myapp-role \
    bound_service_account_names=myapp-sa \
    bound_service_account_namespaces=default \
    policies=myapp-policy \
    ttl=24h
Step 7: Create FastAPI Microservice

app.py

from fastapi import FastAPI
import os

app = FastAPI()

SECRET_FILE = "/vault/secrets/config"

def read_secret():
    try:
        with open(SECRET_FILE, "r") as f:
            return f.read()
    except:
        return "No secret found"

@app.get("/")
def home():
    secret = read_secret()
    return {
        "message": "Vault Secret Values",
        "secret": secret
    }

requirements.txt

fastapi
uvicorn

Dockerfile

FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

Build image:

docker build -t myapp:v1 .
Step 8: Kubernetes Deployment with Vault Injection

deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: vault-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vault-demo
  template:
    metadata:
      labels:
        app: vault-demo
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp-role"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp"
        vault.hashicorp.com/agent-inject-template-config: |
          {{- with secret "secret/data/myapp" -}}
          username={{ .Data.data.username }}
          password={{ .Data.data.password }}
          {{- end }}
    spec:
      serviceAccountName: myapp-sa
      containers:
      - name: app
        image: myapp:v1
        ports:
        - containerPort: 8000

Apply:

kubectl apply -f deployment.yaml
Step 9: Service

service.yaml

apiVersion: v1
kind: Service
metadata:
  name: vault-demo-service
spec:
  selector:
    app: vault-demo
  ports:
    - port: 80
      targetPort: 8000
  type: NodePort

Apply:

kubectl apply -f service.yaml

Access:

http://NODE-IP:NODEPORT

Output:

{
  "message": "Vault Secret Values",
  "secret": "username=pavan password=devsecops123"
}
Step 10: Test Automatic Secret Update

Update Vault secret:

vault kv put secret/myapp \
 username="pavan-new" \
 password="updated123"

Vault Agent automatically updates:

/vault/secrets/config

Microservice instantly reflects new value ✅

No restart needed.

How Automatic Refresh Works

Vault Agent Sidecar:

Vault → Agent → File → Microservice reads → updated automatically
Production Best Practice (Recommended)

Use:

Vault Agent Injector

NOT hardcoded secrets

NOT Kubernetes secrets

Final Folder Structure
project/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── deployment.yaml
├── service.yaml
├── serviceaccount.yaml
├── policy.hcl
Result

You now have:

Vault storing secrets

Kubernetes injecting secrets

Microservice displaying secrets

Automatic secret refresh when Vault updates
