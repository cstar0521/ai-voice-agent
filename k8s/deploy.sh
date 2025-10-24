#!/bin/bash

# Kubernetes Deployment Script for AI Voice Loan Agent
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e

ENVIRONMENT=${1:-staging}
NAMESPACE="voice-agent"

echo "=========================================="
echo "Deploying Voice Agent to $ENVIRONMENT"
echo "=========================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Cannot connect to Kubernetes cluster"
    exit 1
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl apply -f namespace.yaml

# Apply ConfigMap
echo "Applying ConfigMap..."
kubectl apply -f configmap.yaml

# Apply Secrets (WARNING: Update secrets.yaml with actual values first!)
echo "Applying Secrets..."
echo "WARNING: Ensure secrets.yaml contains actual values before deploying!"
read -p "Have you updated secrets.yaml with real values? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled. Please update secrets.yaml first."
    exit 1
fi
kubectl apply -f secrets.yaml

# Deploy MongoDB
echo "Deploying MongoDB..."
kubectl apply -f mongodb-deployment.yaml

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
kubectl wait --for=condition=ready pod -l app=mongo -n $NAMESPACE --timeout=300s

# Deploy Backend
echo "Deploying Backend..."
kubectl apply -f backend-deployment.yaml

# Wait for Backend to be ready
echo "Waiting for Backend to be ready..."
kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=300s

# Deploy Frontend
echo "Deploying Frontend..."
kubectl apply -f frontend-deployment.yaml

# Wait for Frontend to be ready
echo "Waiting for Frontend to be ready..."
kubectl wait --for=condition=ready pod -l app=frontend -n $NAMESPACE --timeout=300s

# Apply Ingress
echo "Applying Ingress..."
kubectl apply -f ingress.yaml

# Apply HPA
echo "Applying Horizontal Pod Autoscaler..."
kubectl apply -f hpa.yaml

# Display deployment status
echo ""
echo "=========================================="
echo "Deployment Status"
echo "=========================================="
kubectl get all -n $NAMESPACE

echo ""
echo "=========================================="
echo "Ingress Information"
echo "=========================================="
kubectl get ingress -n $NAMESPACE

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "To view logs:"
echo "  kubectl logs -f deployment/backend -n $NAMESPACE"
echo "  kubectl logs -f deployment/frontend -n $NAMESPACE"
echo ""
echo "To check pod status:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "To access services locally (port-forward):"
echo "  kubectl port-forward svc/backend-service 8000:8000 -n $NAMESPACE"
echo "  kubectl port-forward svc/frontend-service 3000:3000 -n $NAMESPACE"
