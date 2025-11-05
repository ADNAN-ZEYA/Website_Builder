#!/bin/bash

echo "🚀 Deploying Prompt 2 Page to Kubernetes"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found! Please install Kubernetes first."
    exit 1
fi

echo "📦 Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

echo "🔐 Creating secrets..."
kubectl apply -f kubernetes/secrets.yaml -n prompt2page

echo "🔧 Deploying backend..."
kubectl apply -f kubernetes/backend-deployment.yaml -n prompt2page

echo "🎨 Deploying frontend..."
kubectl apply -f kubernetes/frontend-deployment.yaml -n prompt2page

echo "⏳ Waiting for pods to start..."
kubectl rollout status deployment/prompt2page-backend -n prompt2page
kubectl rollout status deployment/prompt2page-frontend -n prompt2page

echo "✅ Deployment complete!"
echo ""
echo "📊 Resources created:"
kubectl get all -n prompt2page

echo ""
echo "🌐 Access the application:"
echo "   kubectl port-forward -n prompt2page svc/prompt2page-frontend 8080:80"
echo "   Then visit: http://localhost:8080"
