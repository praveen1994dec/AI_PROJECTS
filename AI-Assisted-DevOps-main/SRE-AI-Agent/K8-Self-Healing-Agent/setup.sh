#!/bin/bash
set -e

# ── Prerequisites ──────────────────────────────────────────
for cmd in kind kubectl docker; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "  [FAIL] $cmd not found. Please install it first."
        exit 1
    fi
    echo "  [OK] $cmd"
done
echo ""

# ── Kind cluster ───────────────────────────────────────────
echo "  Creating Kind cluster 'self-healing-cluster'..."
kind delete cluster --name self-healing-cluster 2>/dev/null || true
kind create cluster --name self-healing-cluster --wait 60s
echo "  [OK] Cluster created"
echo ""

# ── Deploy broken apps ────────────────────────────────────
echo "  Deploying intentionally broken apps..."
kubectl apply -f chaos/
echo ""

echo "  Waiting 15s for pods to crash..."
sleep 15

echo ""
echo "  Pod status:"
echo "  ─────────────────────────────────────────"
kubectl get pods --no-headers | while read line; do
    echo "    $line"
done
echo ""

echo "  ================================================"
echo "  Cluster ready! Broken pods deployed."
