#!/bin/bash
set -e

if ! minikube status &> /dev/null; then
    minikube start
fi

eval $(minikube docker-env)
docker build -t vectorflow:latest .
helm upgrade --install vectorflow ./helm/vectorflow --wait

kubectl port-forward svc/vectorflow 8000:8000 &
PF_PID=$!

trap "kill $PF_PID 2>/dev/null || true" INT TERM EXIT
wait $PF_PID
