# AI Sales Agent SaaS — Customer Onboarding Guide

> Version 1.0 — Enterprise Customer Delivery

---

## Table of Contents

1. [Overview](#1-overview)
2. [Create a Company (Tenant)](#2-create-a-company-tenant)
3. [Create Users](#3-create-users)
4. [Configure Permissions](#4-configure-permissions)
5. [Connect WhatsApp](#5-connect-whatsapp)
6. [Configure AI](#6-configure-ai)
7. [Create Your First Pipeline](#7-create-your-first-pipeline)
8. [Register Your First Customer](#8-register-your-first-customer)
9. [Create Your First Order](#9-create-your-first-order)
10. [View Your First Report](#10-view-your-first-report)
11. [Daily Operations](#11-daily-operations)
12. [Common Tasks](#12-common-tasks)

---

## 1. Overview

The AI Sales Agent SaaS platform consists of three main interfaces:

| Interface | URL | Purpose |
|-----------|-----|---------|
| **Admin Panel** | `https://your-domain.com/admin/login` | Super admin — manage companies, global settings |
| **User Dashboard** | `https://your-domain.com/login` | Sales agents — daily operations |
| **API** | `https://your-domain.com/api/v1` | Programmatic access |

### User roles

| Role | Permissions |
|------|------------|
| `super_admin` | Full system access, manage all companies |
| `owner` | Full company access, manage users and settings |
| `admin` | Manage company data, view reports |
| `sales_agent` | Daily sales operations (CRM, pipeline, orders) |
| `analyst` | Read-only access to reports and dashboards |

---

## 2. Create a Company (Tenant)

**Who:** Super admin  
**Where:** Admin Panel → Tenants

### Steps

1. Log in to the **Admin Panel** at `/admin/login`
   - Default credentials: `admin@your-company.com` / `Admin@2024!`
2. Click **"Tenants"** in the sidebar
3. Click **"Create Company"**
4. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| **Company Name** | Legal business name | "Fashion Store SAC" |
| **Slug** | URL-friendly identifier | `fashion-store` |
| **Plan** | Subscription plan | `enterprise`, `professional`, `starter` |
| **Status** | Account status | `active` |
| **Max Users** | User limit | `10` |
| **Max Storage GB** | Storage limit | `5` |

5. Click **"Save"**

The company is now active. The system will create:
- A company record in the database
- Default notification settings
- Initial audit log entry

---

## 3. Create Users

**Who:** Company owner or admin  
**Where:** User Dashboard → Settings → Users

### Steps

1. Log in to the **User Dashboard** at `/login`
   - Use credentials provided by the super admin
2. Navigate to **Dashboard → Settings → Users**
3. Click **"Invite User"**
4. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| **Email** | User's email address | `juan.perez@email.com` |
| **Full Name** | User's full name | "Juan Pérez" |
| **Role** | Access level (see table above) | `sales_agent` |

5. Click **"Send Invitation"**

The user will receive an email with:
- Login URL
- Temporary password
- Instructions to set up their account

### Bulk user creation

For importing multiple users at once, contact support or use the API:

```bash
curl -X POST https://your-domain.com/api/v1/admin/users/bulk \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {"email": "ana@email.com", "full_name": "Ana López", "rol": "sales_agent"},
      {"email": "carlos@email.com", "full_name": "Carlos Ruiz", "rol": "analyst"}
    ]
  }'
```

---

## 4. Configure Permissions

**Who:** Company owner or admin  
**Where:** User Dashboard → Settings → Roles

### Built-in roles

| Role | CRM | Products | Orders | Pipeline | Reports | Users | WhatsApp | AI |
|------|-----|----------|--------|----------|---------|-------|----------|----|
| Owner | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Sales Agent | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | ✓ |
| Analyst | ✓ | ✓ | ✓ | — | ✓ | — | — | — |

### Custom permissions

To modify what a role can access:

1. Go to **Settings → Roles**
2. Select the role to edit
3. Toggle permissions per module
4. Click **"Save Changes"**

Permissions are enforced at the API level (backend) and UI level (frontend).

---

## 5. Connect WhatsApp

**Who:** Company owner or admin  
**Where:** User Dashboard → WhatsApp

### Prerequisites

- A WhatsApp Business API account (Meta Business Platform)
- A verified Meta Business Manager
- A WhatsApp phone number

### Steps

1. Navigate to **Dashboard → WhatsApp**
2. Click **"Connect WhatsApp"**
3. You'll be redirected to Meta's authorization page
4. Log in with your Meta Business account
5. Select the WhatsApp Business phone number to connect
6. Grant the requested permissions
7. You'll be redirected back to the platform

### Verify connection

After connecting, check the WhatsApp dashboard:
- **Status**: Should show "Connected"
- **Phone Number**: Your connected number
- **Messages**: Recent messages will appear in the conversations panel

### Troubleshooting WhatsApp connection

| Issue | Solution |
|-------|----------|
| "Session expired" | Reconnect via the WhatsApp settings page |
| "Number not registered" | Ensure the number is registered with WhatsApp Business API |
| "Webhook not verified" | The system automatically verifies Meta webhooks; if this fails, contact support |
| "Rate limited" | WhatsApp API has message limits; the system manages this automatically |

---

## 6. Configure AI

**Who:** Company owner or admin  
**Where:** User Dashboard → AI Settings

### Prerequisites

- OpenAI API key configured at the system level (by super admin)
- The company must have an active subscription

### AI Features

| Feature | Description | Default |
|---------|-------------|---------|
| **Sales Insights** | AI analysis of sales patterns, lead scoring | Enabled |
| **Smart Recommendations** | Product recommendations for customers | Enabled |
| **Conversation AI** | AI-assisted replies in chat | Disabled |
| **Auto Replies** | Automatic responses to common queries | Disabled |
| **Sentiment Analysis** | Detect customer sentiment in conversations | Enabled |
| **Intent Detection** | Identify customer purchase intent | Enabled |

### Configuration steps

1. Go to **Dashboard → AI Settings**
2. Configure each AI feature:

   **Sales Insights:**
   - Enable/disable AI-powered insights
   - Set analysis frequency (daily, weekly, real-time)

   **Conversation AI:**
   - Enable AI-suggested replies
   - Enable auto-reply (automatic responses)
   - Set escalation rules (when to transfer to human agent)

3. Click **"Save Configuration"**

### Testing AI features

1. Go to **Dashboard → AI Sales**
2. View the AI Sales Dashboard — should show insights, recommendations, and activity
3. Open a **Conversation** → AI sidebar shows suggested replies and sentiment
4. Create a **Pipeline deal** → AI scores the lead automatically

---

## 7. Create Your First Pipeline

**Who:** Any user with pipeline access  
**Where:** User Dashboard → Pipeline

### Pipeline stages

| Stage | Description | AI Action |
|-------|-------------|-----------|
| **Contacted** | Initial contact made | Auto-scores lead |
| **Interested** | Customer shows interest | Suggests products |
| **Negotiating** | Price and terms discussion | Recommends discounts |
| **Won** | Deal closed | Triggers order creation |
| **Lost** | Deal lost | Logs reason for analysis |

### Steps

1. Go to **Dashboard → Pipeline**
2. Click **"New Deal"**
3. Fill in the form:

| Field | Description | Example |
|-------|-------------|---------|
| **Customer** | Select from existing customers | "María García" |
| **Product** | Select product or custom | "Vestido Floral" |
| **Value** | Deal amount in USD | $150.00 |
| **Notes** | Additional context | "Interested in summer collection" |

4. Click **"Create"**

The deal appears in the **"Contacted"** column. To move a deal:
- **Drag and drop** the card to the next stage
- Or click the deal and use the **"Move to"** dropdown

### Automation rules

You can set automation rules to auto-move deals:
1. Go to **Dashboard → Automation**
2. Click **"New Rule"**
3. Configure:
   - **Trigger**: When a deal stays in a stage for N days
   - **Action**: Move to next stage, send notification, assign to user
4. Enable the rule

---

## 8. Register Your First Customer

**Who:** Any user with CRM access  
**Where:** User Dashboard → Customers

### Steps

1. Go to **Dashboard → Customers**
2. Click **"Create Customer"**
3. Fill in the form:

| Field | Required | Example |
|-------|----------|---------|
| **Full Name** | Yes | "María García López" |
| **Email** | No | `maria@email.com` |
| **Phone** | No | `+51999888777` |
| **Lead Status** | Yes | `new`, `interested`, `negotiating`, `won`, `lost` |
| **Source** | No | `whatsapp`, `instagram`, `facebook`, `web`, `referral` |
| **Tags** | No | `vip`, `wholesale`, `summer-campaign` |
| **Notes** | No | "Met at fashion expo" |

4. Click **"Save"**

The customer now appears in:
- **Customers list** — searchable, filterable
- **Pipeline** — available for deal creation
- **Conversations** — ready for messaging

---

## 9. Create Your First Order

**Who:** Any user with orders access  
**Where:** User Dashboard → Orders

### Steps

1. Go to **Dashboard → Orders**
2. Click **"New Order"**
3. Fill in:

| Field | Description |
|-------|-------------|
| **Customer** | Select from customers |
| **Product** | Select product with variant |
| **Quantity** | Number of units |
| **Delivery Type** | `delivery` or `pickup` |
| **Notes** | Special instructions |

4. Click **"Create Order"**

### Order lifecycle

| Status | Description |
|--------|-------------|
| Pending | Awaiting confirmation |
| Confirmed | Customer confirmed |
| Preparing | Being prepared |
| Shipped | In transit |
| Delivered | Completed |
| Cancelled | Order cancelled |

You can update the status from the **Orders** page by selecting the new status in the dropdown.

---

## 10. View Your First Report

**Who:** Users with reports access  
**Where:** User Dashboard → Reports

### Available reports

| Report | Description |
|--------|-------------|
| **Sales Summary** | Revenue, orders, average order value |
| **Customer Analytics** | Acquisition, retention, churn |
| **Pipeline Analytics** | Deal velocity, conversion rates, win/loss |
| **Product Performance** | Top sellers, inventory turnover |
| **Conversation Analytics** | Volume, response times, sentiment trends |

### Steps

1. Go to **Dashboard → Reports**
2. Select a report type
3. Set the date range (default: last 30 days)
4. View metrics and charts
5. Click **"Export"** to download as CSV or PDF

### Executive Dashboard

The **Executive Dashboard** provides a high-level overview:
- Monthly revenue trends
- Customer acquisition charts
- Pipeline health score
- Top-performing products
- Sales agent performance

Go to **Dashboard → Executive**

---

## 11. Daily Operations

### Morning checklist

1. ✅ Check **Dashboard** for daily metrics
2. ✅ Review **Pipeline** for deals that need attention
3. ✅ Check **Conversations** for unread messages
4. ✅ Review **Alerts** for system notifications
5. ✅ Process any pending **Orders**

### Weekly tasks

- [ ] Review **Reports** for weekly performance
- [ ] Update **Pipeline** deals with latest status
- [ ] Run **Automation** rules for batch processing
- [ ] Check **AI Insights** for recommendations
- [ ] Review **WhatsApp** connection status

### Monthly tasks

- [ ] Generate monthly **Executive Report**
- [ ] Audit user permissions
- [ ] Review AI performance and tuning
- [ ] Clean up stale deals and customers
- [ ] Backup verification

---

## 12. Common Tasks

### Reset user password

1. Admin → Settings → Users
2. Find the user
3. Click **"Reset Password"**
4. The user receives an email with a reset link

### Change company plan

1. **Admin Panel** → Tenants
2. Find the company
3. Click **"Edit"**
4. Change the **Plan** field
5. Save

### Suspend a company

1. **Admin Panel** → Tenants
2. Find the company
3. Click **"Edit"**
4. Change **Status** to `suspended`
5. Save

All users from this company will lose access immediately.

### Export data

| Data | Format | Location |
|------|--------|----------|
| Customer list | CSV | Customers → Export |
| Orders | CSV | Orders → Export |
| Pipeline report | CSV/PDF | Pipeline → Export |
| Sales report | CSV/PDF | Reports → Export |

### Get support

- **Email**: support@ai-sales-agent.com
- **Documentation**: https://docs.ai-sales-agent.com
- **Status Page**: https://status.ai-sales-agent.com

When contacting support, include:
1. Your company name
2. The error message (or screenshot)
3. The timestamp when the issue occurred
4. Any relevant IDs (error ID, order ID, customer ID)
