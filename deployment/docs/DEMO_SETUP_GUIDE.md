# AI Sales Agent SaaS — Demo Environment Setup Guide v1.0

> Para crear un entorno demo completo para presentaciones comerciales.  
> Versión: 1.0 — Junio 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Quick Setup (Automated)](#3-quick-setup-automated)
4. [Setup Components](#4-setup-components)
5. [Demo Walkthrough](#5-demo-walkthrough)
6. [Resetting the Demo](#6-resetting-the-demo)
7. [Demo Script for Sales Team](#7-demo-script-for-sales-team)

---

## 1. Overview

The demo environment includes:

| Component | Quantity | Details |
|-----------|----------|---------|
| Companies | 1 | "Demo Fashion Store" |
| Users | 3 | 1 admin, 2 sales agents |
| Customers | 100 | With lead scores, tags, conversation history |
| Products | 20 | With variants (sizes, colors) and images |
| Pipeline deals | 50 | In various stages with AI scores |
| Orders | 100 | With different statuses |
| Conversations | 200 | With AI replies, sentiment data |
| Automation rules | 5 | Active rules with tasks |
| Reports | Pre-generated | PDF and Excel for all modules |

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@demo.com` | `Demo2024!` |
| Agent 1 | `agent1@demo.com` | `Demo2024!` |
| Agent 2 | `agent2@demo.com` | `Demo2024!` |

---

## 2. Prerequisites

- Completed installation per `CUSTOMER_INSTALLATION_GUIDE.md`
- Backend and frontend services running
- PostgreSQL accessible
- (Optional) OpenAI API key for AI features demo
- (Optional) WhatsApp Business API for messaging demo

---

## 3. Quick Setup (Automated)

```bash
# Run the demo seed script
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
python scripts/demo_seed.py
```

The script will:

1. Create the "Demo Fashion Store" company
2. Create admin and agent users
3. Generate 100 customers with realistic data
4. Create 20 products with variants (sizes, colors, SKUs)
5. Create 50 pipeline deals across all stages
6. Create 100 orders with items
7. Create 200 conversations with messages
8. Set up 5 automation rules
9. Create inventory items with stock levels
10. Generate sample reports

**Duration**: ~30-60 seconds

---

## 4. Setup Components

### 4.1 Demo Company

**Name**: Demo Fashion Store  
**Slug**: `demo-fashion-store`  
**Plan**: `enterprise`  
**Status**: `active`

To create manually:
```bash
curl -X POST https://demo.app.miempresa.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Demo Fashion Store",
    "company_slug": "demo-fashion-store",
    "email": "admin@demo.com",
    "password": "Demo2024!"
  }'
```

### 4.2 Demo Users

| Name | Email | Role | Permission |
|------|-------|------|------------|
| Admin User | `admin@demo.com` | `admin` | Full access |
| Ana Ventas | `agent1@demo.com` | `sales_agent` | CRM, Pipeline, Orders |
| Carlos Ruiz | `agent2@demo.com` | `analyst` | Reports, Dashboard |

### 4.3 Demo Products

| Product | Category | Price | Variants |
|---------|----------|-------|----------|
| Polo Premium Black | Polos | $49.99 | S/M/L/XL |
| Vestido Floral Verano | Vestidos | $89.99 | S/M/L |
| Camisa Linens Blanca | Camisas | $59.99 | S/M/L/XL |
| Jean Skinny Azul | Jeans | $79.99 | 28-36 |
| Blusa Seda Elegante | Blusas | $69.99 | S/M/L |
| Chaqueta Cuero Negra | Chaquetas | $199.99 | S/M/L |
| Shorts Deportivos | Shorts | $34.99 | S/M/L/XL |
| Suéter Cashmere Gris | Suéteres | $129.99 | S/M/L |
| Falda Plisada Rosa | Faldas | $54.99 | S/M/L |
| Abrigo Lana Azul Marino | Abrigos | $249.99 | S/M/L/XL |

(plus 10 more products)

### 4.4 Pipeline Stages & Deals

| Stage | Deals Count | Total Value |
|-------|-------------|-------------|
| New Lead | 10 | $2,500 |
| Contacted | 10 | $3,200 |
| Qualified | 8 | $4,100 |
| Proposal | 7 | $5,600 |
| Negotiation | 5 | $8,200 |
| Won | 5 (closed) | $12,000 |
| Lost | 5 (closed) | $3,000 |

### 4.5 Automation Rules

| Rule | Trigger | Action | Status |
|------|---------|--------|--------|
| Follow-up after 3 days | Deal in "Contacted" > 3 days | Assign task to agent | Active |
| VIP deal alert | Deal value > $1,000 in "New Lead" | Send notification | Active |
| Stale deal reminder | Deal untouched > 7 days | Escalate to admin | Active |
| Won deal → order | Deal moved to "Won" | Create order automatically | Active |
| Lost deal analysis | Deal moved to "Lost" | Log reason and notify | Active |

### 4.6 Sample Conversations

Demo conversations include:
- WhatsApp-style chat with customer inquiries
- AI-generated replies with sales suggestions
- Sentiment analysis data
- Product recommendations
- Price negotiation examples

### 4.7 Pre-generated Reports

| Report | Format | Content |
|--------|--------|---------|
| Sales Report | PDF, Excel | Revenue, orders, AOV trends |
| Pipeline Report | PDF, Excel | Funnel, conversion rates, velocity |
| CRM Report | PDF, Excel | Customer acquisition, retention |
| Inventory Report | PDF, Excel | Stock levels, top products |
| Executive Dashboard | Web | All KPIs in one view |

---

## 5. Demo Walkthrough

### 5.1 Log in

1. Open `https://demo.app.miempresa.com/login`
2. Enter `admin@demo.com` / `Demo2024!`

### 5.2 Dashboard

The main dashboard shows:
- Today's revenue and orders
- Active pipeline deals
- Recent conversations
- Alerts and notifications

### 5.3 Customers (CRM)

1. Navigate to **Customers**
2. Browse the customer list (100 records, paginated)
3. Search for a customer by name
4. Click a customer to view their profile
5. Review: lead score, tags, conversation history, orders

### 5.4 Pipeline

1. Navigate to **Pipeline**
2. View the Kanban board with all stages
3. Drag a deal from "Contacted" to "Qualified"
4. Click a deal to see AI score breakdown
5. Review pipeline metrics and funnel

### 5.5 Products & Inventory

1. Navigate to **Products**
2. Browse the product catalog
3. Click a product to view variants and stock
4. Navigate to **Inventory** to see stock levels

### 5.6 Orders

1. Navigate to **Orders**
2. View the orders list
3. Filter by status
4. Click an order to view details and items

### 5.7 Conversations & AI Sales

1. Navigate to **Conversations**
2. Open a conversation
3. View AI-suggested replies
4. Review sentiment analysis
5. Navigate to **AI Sales** dashboard for insights

### 5.8 Reports

1. Navigate to **Reports**
2. Generate a **Sales Report (PDF)**
3. Generate a **Pipeline Report (Excel)**
4. View the **Executive Dashboard**

### 5.9 Automation

1. Navigate to **Automation**
2. View active rules
3. Review scheduled tasks
4. Check automation metrics

### 5.10 WhatsApp

1. Navigate to **WhatsApp**
2. View metrics (if connected)
3. Review recent messages

### 5.11 Admin Panel

1. Navigate to `/admin/login`
2. Log in with `admin@demo.com` / `Demo2024!`
3. View company details
4. Review audit log

---

## 6. Resetting the Demo

To reset the demo to its initial state:

```bash
# Option 1: Re-run the seed script (drops and recreates)
cd /opt/ai-sales-agent-saas/backend
source .venv/bin/activate
python scripts/demo_seed.py --force

# Option 2: Manual reset via database
sudo -u postgres psql -d ai_sales_agent_saas
-- This deletes ALL demo data
DELETE FROM empresas WHERE slug = 'demo-fashion-store';
-- Then re-run the seed script
```

### Reset Frequency

| Scenario | Recommendation |
|----------|---------------|
| Daily demos | Reset once per day |
| Weekly demos | Reset on Monday morning |
| Trade show | Reset before each show |
| After testing | Reset immediately |

---

## 7. Demo Script for Sales Team

### Opening (2 minutes)

> "Let me show you how AI Sales Agent SaaS can transform your sales operation. I've prepared a demo environment with real data from a fashion retail company."

### CRM & Customers (3 minutes)

> "Here we have 100 customers with complete profiles. Notice the lead scoring — the AI automatically evaluates each customer's purchase intent. We can segment by tags, source, or any custom field."

### Pipeline (3 minutes)

> "The pipeline is the heart of the system. We track deals through 7 stages. The AI scores each deal and gives us recommendations on what to do next. Watch — I can drag this deal from Contacted to Qualified."

### AI Sales (3 minutes)

> "This is where AI changes everything. When a customer messages us, the AI understands their intent — are they asking about price, ready to buy, or need support? It generates a reply and suggests products. Let me show you a conversation."

### Reporting (2 minutes)

> "Reports are available in PDF and Excel with one click. The Executive Dashboard gives you a complete overview of all KPIs in real time."

### Automation (2 minutes)

> "The Automation Engine handles repetitive tasks. If a deal sits too long, it creates a task. When a deal is won, it automatically creates an order. No manual work needed."

### Closing (1 minute)

> "The entire system can be installed in under 30 minutes. Let me walk you through the installation requirements..."

---

*Documentation v1.0 — AI Sales Agent SaaS Enterprise*
