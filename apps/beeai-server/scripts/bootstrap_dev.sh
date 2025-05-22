#!/bin/bash

NAMESPACE=beeai-local-dev
kubectl create namespace "$NAMESPACE"
telepresence helm install
telepresence connect --namespace "$NAMESPACE"

helm install db oci://registry-1.docker.io/bitnamicharts/postgresql \
  --set auth.postgresPassword=postgres \
  --set auth.database=beeai \
  --namespace "$NAMESPACE" \
  || true

kubectl apply --namespace "$NAMESPACE" -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: beeai-platform-svc
  labels:
    app: fake-beeai-server
spec:
  type: ClusterIP
  selector:
    app: fake-beeai-server
  ports:
    - protocol: TCP
      port: 8333
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: beeai-platform-svc
  labels:
    app: fake-beeai-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fake-beeai-server
  template:
    metadata:
      labels:
        app: fake-beeai-server
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
EOF
ENV AUTH__DISABLE_AUTH=true uv run migrate

telepresence --use ".*${NAMESPACE}.*" intercept beeai-platform-svc --port 8333
