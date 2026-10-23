# 🚀 Practical Implementation of Kubernetes MCP Server with Claude Desktop

> **Manage Kubernetes using Natural Language with Model Context Protocol (MCP)**

Instead of memorizing long `kubectl` commands, you can connect a **Kubernetes MCP (Model Context Protocol) Server** to **Claude Desktop** and interact with your Kubernetes cluster using plain English.

Once configured, Claude can securely communicate with your Kubernetes cluster through your local `kubeconfig`, allowing you to:

* 📦 List Pods
* 📄 View Logs
* 🚀 Check Deployments
* 💾 Monitor Cluster Resources
* 🔍 Troubleshoot Kubernetes Issues
* ⚙️ Inspect Services, ConfigMaps, Secrets, and much more

This guide provides a complete hands-on implementation.

---

# 📌 Architecture

```text
                        User
                         │
        Natural Language Prompt
                         │
                         ▼
                Claude Desktop
                         │
                      MCP client
                         │
               Kubernetes MCP Server
                         │
                  kubeconfig File
                         │
                 Kubernetes Cluster
```

---

# Prerequisites

Before starting, ensure the following are installed on your machine.

| Requirement        | Description                  |
| ------------------ | ---------------------------- |
| Claude Desktop     | Installed on your system     |
| Kubernetes Cluster | Local or Cloud               |
| kubectl            | Configured correctly         |
| kubeconfig         | Points to your cluster       |
| Node.js            | Required for `npx` execution |

---

# Step 1 — Verify Kubernetes Access

Before configuring MCP, verify that your Kubernetes cluster is accessible.

```bash
kubectl cluster-info
```

Expected output:

```text
Kubernetes control plane is running at https://xxxxxxxx
CoreDNS is running at ...
```

Now verify your nodes.

```bash
kubectl get nodes
```

Example:

```text
NAME           STATUS   ROLES           AGE
master-node    Ready    control-plane   20d
worker-node    Ready    <none>          20d
```

If both commands work successfully, your `kubeconfig` is correctly configured.

---

# Step 2 — Locate Claude Desktop Configuration

Claude Desktop stores MCP server definitions inside:

```
claude_desktop_config.json
```

## Open the configuration

Inside Claude Desktop:

```
Settings
      ↓
Developer
      ↓
Edit Config
```

Claude automatically opens the configuration file.

---

# Step 3 — Configure Kubernetes MCP Server

Replace your configuration with:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": [
        "-y",
        "kubernetes-mcp-server@latest"
      ]
    }
  }
}
```

Save the file.

---

# Step 4 — Restart Claude Desktop

Completely close Claude Desktop.

Open it again.

Claude automatically starts every MCP server defined inside:

```
claude_desktop_config.json
```

---

# Step 5 — Verify MCP Connection

Look at the bottom-right corner of Claude Desktop.

You should see an **MCP / Extensions** icon.

Click it.

If everything is configured correctly, you'll see:

```
Connected MCP Servers

✔ kubernetes
```

Congratulations!

Your Kubernetes cluster is now connected.

---

# Step 6 — Start Using Natural Language

Instead of typing long Kubernetes commands, simply ask Claude.

---

## List Pods

Prompt:

```
List all pods in my current namespace.
```
---
<p align="center">
 <img src="/MCP/images/cloudy.png" width="600">
</p>

---
Equivalent command:

```bash
kubectl get pods
```

---

## List All Namespaces

Prompt:

```
Show all namespaces.
```

Equivalent:

```bash
kubectl get namespaces
```

---

# Example Workflow

```
User
   │
   ▼
"Why is my application down?"
   │
   ▼
Claude Desktop
   │
   ▼
Kubernetes MCP Server
   │
   ▼
Reads kubeconfig
   │
   ▼
Calls Kubernetes API
   │
   ▼
Returns:
    • Logs
    • Events
    • Deployment Status
    • Pod Status
    • Recommendations
```

---

# Advantages of Kubernetes MCP

* No need to remember complex `kubectl` commands.
* Natural language interaction with your cluster.
* Faster troubleshooting and root cause analysis.
* Context-aware responses based on your connected cluster.
* Secure access through your existing `kubeconfig`.
* Works with local clusters and managed Kubernetes services (AKS, EKS, GKE, etc.).
* Improves productivity for DevOps, SRE, and Platform Engineering teams.

---