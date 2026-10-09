# UI/UX DESIGN PLAN: Customizable Dropshipping E-Commerce Platform
### Based on PDR v2.0 + TDR v1.0

---

## 1. Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | **Mobile-First, Desktop-Complete** | All storefront screens are designed for 375px viewport first, then scaled up. Admin portal targets 1280px minimum but remains usable at 768px. |
| 2 | **Progressive Disclosure** | Show only what the user needs at each step. Product customization options reveal only after a variant is selected. Admin panels show only the modules the user's role permits. |
| 3 | **Inventory-Honest UI** | Stock status is always visible and always real-time. Out-of-stock items are never hidden — they are shown with a clear label and deprioritised in listings. No dark patterns around scarcity. |
| 4 | **One Primary Action per Screen** | Every page has a single dominant CTA (Add to Cart, Confirm Payment, Approve Change). Secondary actions are visually subordinate. Checkout is a linear funnel — no escape temptations. |
| 5 | **Role-Aware Admin Surfaces** | The admin portal renders only the navigation and features the logged-in user's roles permit. A Shipping Admin never sees the Code Panel. A Review Moderator never sees order financials. The UI enforces the RBAC model visually, not just technically. |

---

## 2. Wireframe Reference

### 2.1 Storefront (Customer-facing) — Top Navigation Pattern
- **Layout:** Fixed top navbar (logo, search bar, cart icon, account icon) + full-width content area + footer
- **Mobile nav:** Hamburger menu slides in from left with category tree + account links
- **Product grid:** 2-col on mobile, 3-col on tablet, 4-col on desktop. Each card shows: product image, name, price, stock badge, rating stars
- **PDP (Product Detail Page):** Image gallery left / product info + customizer right on desktop. Stacked on mobile. Sticky "Add to Cart" bar at bottom on mobile
- **Cart:** Slide-out drawer on desktop; full-page on mobile
- **Checkout:** 3-step stepper: Address → Payment → Confirm. Linear, no sidebars

### 2.2 Admin Portal — Sidebar Navigation Pattern
- **Layout:** Fixed left sidebar (role-filtered nav items, 240px) + top bar (user info, role badge, notifications) + main content area
- **Sidebar behaviour:** Collapsible to icon-only (60px) on smaller screens. Active item highlighted with brand accent
- **Content area:** Card-based dashboards; table-based management screens; detail panels slide in from right (no full-page navigations for detail views)
- **Super Admin distinction:** Super Admin sidebar shows all modules + "Role Management" section at the top. Other roles see only their permitted modules
- **Code Panel:** Full-width diff viewer layout — file tree left, diff content centre, approval controls right

---

## 3. Information Architecture (Sitemap)

### 3.1 Public / Shared (No Login Required)

```
/                           → Homepage (featured products, banners, categories)
/search                     → Search results page (full-text + faceted filters)
/products                   → Product listing page (PLP)
/products/:slug             → Product detail page (PDP) with customizer
/categories/:slug           → Category listing page
/delivery-check             → Delivery availability checker (pincode lookup)
/reviews/:productId         → Public reviews for a product
/auth/login                 → Login page
/auth/register              → Registration page
/auth/forgot-password       → Password reset request
/auth/reset-password        → Password reset confirmation
/auth/mfa-verify            → MFA verification step (post-login for admins)
```

### 3.2 Admin — Super Admin Exclusive

```
/admin                      → Super Admin dashboard (platform overview stats)
/admin/employees            → Employee list (all accounts)
/admin/employees/new        → Create new employee account
/admin/employees/:id        → Employee detail + role assignment (multi-select roles)
/admin/roles                → Roles master list (view only)
/admin/audit-logs           → Immutable audit trail (filterable by actor, action, date)
/admin/system/settings      → Platform-level settings (COD fee, low-stock threshold defaults)
```

### 3.3 Staff / Employee (Role-Filtered)

```
── Product Admin ──
/admin/products             → Product list (paginated, searchable)
/admin/products/new         → Create product + variants + media
/admin/products/:id/edit    → Edit product
/admin/inventory            → Inventory dashboard (all SKUs, stock levels, alert flags)
/admin/inventory/:variantId → Stock detail + threshold adjustment + manual sync trigger
/admin/search-analytics     → Top queries, zero-result queries, CTR report
/admin/search/synonyms      → Synonym dictionary management

── Order Admin ──
/admin/orders               → Order list (filter by status, date, customer)
/admin/orders/:id           → Order detail (items, payment, shipping, timeline)
/admin/refunds              → Refund management queue

── Shipping Admin ──
/admin/shipments            → Shipment list (filter by status, courier)
/admin/shipments/:id        → Shipment detail + courier ID assignment + tracking update

── Review Moderator ──
/admin/reviews              → Review moderation queue (pending → approve/hide/flag)
/admin/reviews/:id          → Review detail with media preview + moderation action

── Notification Admin ──
/admin/notifications        → Campaign list (push, email, SMS)
/admin/notifications/new    → Create campaign (audience, channel, template, schedule)

── Management User ──
/admin/code-panel           → Code change proposal list (pending/approved/rejected)
/admin/code-panel/:id       → Change detail: diff viewer + approve/reject controls
/admin/audit-logs           → Shared with Super Admin (read-only)
```

### 3.4 Customer (Login Required for Cart+)

```
── Account ──
/account                    → Account overview (recent orders, profile summary)
/account/profile            → Edit profile (name, phone)
/account/orders             → Order history list
/account/orders/:id         → Order detail + tracking status timeline
/account/orders/:id/return  → Return request form
/account/orders/:id/review  → Submit review for a delivered product

── Shopping ──
/cart                       → Cart page (items, customizations, inventory check)
/checkout                   → 3-step checkout funnel
/checkout/success           → Order confirmation screen
/checkout/failure           → Payment failure screen + retry CTA
```

---

## 4. Key User Flows

### 4.1 Registration, Login & Password Reset

**Customer Registration:**
```
/auth/register
  → Fill: name, email, phone (optional), password
  → Client: password strength indicator
  → Submit → POST /api/auth/register
  → Success → redirect /account with welcome toast
  → Error (email exists) → inline field error: "An account with this email already exists"
```

**Login (Customer):**
```
/auth/login
  → Fill: email, password
  → Submit → POST /api/auth/login
  → Success → redirect to previous page or /account
  → Error → toast: "Invalid email or password" (no field-specific error — security)
```

**Login (Employee / Admin) — MFA Required:**
```
/auth/login
  → Fill: email, password → POST /api/auth/login
  → Response: requiresMfa: true + tempToken
  → Redirect to /auth/mfa-verify
  → Enter 6-digit TOTP code → POST /api/auth/mfa/verify
  → Success → redirect /admin dashboard
  → Error → "Invalid code. Try again." with countdown for next code
```

**Password Reset:**
```
/auth/forgot-password
  → Enter email → POST /api/auth/password/reset-request
  → Show: "If this email exists, a reset link has been sent" (always, no reveal)
  → Email contains link → /auth/reset-password?token=...
  → Enter new password + confirm → POST /api/auth/password/reset
  → Success → redirect /auth/login with toast "Password updated. Please log in."
```

**MFA Setup (Admin, first login):**
```
/account/security (or /admin/profile)
  → Click "Enable MFA" → POST /api/auth/mfa/setup
  → Display: QR code image + plaintext secret for manual entry
  → Instruction: "Scan with Google Authenticator"
  → Enter 6-digit code → POST /api/auth/mfa/verify
  → Success → toast "MFA enabled" + tick badge on security settings
```

---

### 4.2 Core Transaction Flow (Browse → Customize → Checkout)

```
STEP 1 — Discovery
  Homepage / Search / Category page
  → Product card shows: image, name, price, stock badge (In Stock / Low Stock / Out of Stock)
  → Click card → /products/:slug (PDP)

STEP 2 — Product Detail & Customization
  PDP loads:
  → GET /api/catalog/products/:id (product data)
  → GET /api/inventory/check/:variantId (real-time stock, shown as badge)
  → Default variant selected → stock badge updates on variant change
  → If OUT_OF_STOCK → "Add to Cart" button disabled + "Out of Stock" label

  Customization panel (if product.customization_rules allows it):
  → Fabric.js canvas renders product base image
  → Controls: text overlay (font, colour, size), image upload, colour picker, size selector
  → Live preview updates on canvas as user types/selects
  → "Save Customization" serialises canvas to customization_json

STEP 3 — Add to Cart
  → Click "Add to Cart"
  → POST /api/cart/items { variant_id, qty, customization_json }
    → Cart Service → POST /api/inventory/reserve { variant_id, qty, session_id }
    → If INSUFFICIENT_STOCK → toast: "Only N items left. Adjust quantity."
    → If OUT_OF_STOCK → toast: "This item is no longer available."
    → If success → cart drawer slides open with item + customization thumbnail
  → Guest: cart stored in Redis by session_id
  → Logged-in: cart linked to user_id

STEP 4 — Cart Review
  /cart page:
  → List items with: product image + customization preview thumbnail, variant, qty adjuster, unit price, subtotal
  → Each item: GET /api/inventory/check/:variantId on page load (refresh stock status)
  → If any item OUT_OF_STOCK → warning banner + that item's qty field disabled
  → "Remove" button → DELETE /api/cart/items/:itemId → releases reservation
  → Show: subtotal, COD fee estimate (if COD), delivery availability widget (pincode input)
  → CTA: "Proceed to Checkout" (disabled if cart empty or any item out of stock)

STEP 5 — Checkout (3-step stepper)

  Step 1 — Address:
  → Enter/select delivery address
  → GET /api/delivery/check?pincode=... → show "Delivery available" or "Not deliverable to this location"
  → If not deliverable → block Step 2

  Step 2 — Payment:
  → Show order summary (items + customizations + shipping estimate)
  → Payment method selector: UPI / Card / Cash on Delivery
  → COD: show COD handling fee (configurable) + note "Pay at delivery"
  → UPI/Card: Razorpay checkout.js opens in modal
  → POST /api/orders/checkout → creates order, validates all reservations still active
  → If reservation expired during browsing → alert "Session expired. Your cart has been refreshed." → refresh cart

  Step 3 — Confirmation:
  → Payment webhook received → order status = CONFIRMED
  → /checkout/success screen:
    - Order number (large, prominent)
    - "Your invoice will be sent to {email} and WhatsApp"
    - Items summary (with customization thumbnails)
    - Estimated delivery date
    - CTA: "Track your order" → /account/orders/:id

STEP 6 — Post-Order
  → Invoice PDF generated (async) → email + WhatsApp delivery
  → Order status visible in /account/orders
  → Order tracking: real-time status timeline (CONFIRMED → PROCESSING → SHIPPED → DELIVERED)
  → After DELIVERED: "Write a Review" CTA appears (only for verified purchase)
```

---

### 4.3 Super Admin — Role Assignment Flow

```
/admin/employees (list page)
  → Table: name, email, account type, current roles (badges), status, actions
  → Search/filter by name or email
  → Click employee row → /admin/employees/:id

/admin/employees/:id (detail page)
  → Left: employee info card (name, email, created date, last login, status)
  → Right: "Assigned Roles" section
    → Current roles listed as removable chips/tags
    → "Add Role" button → opens modal

  Role Assignment Modal:
  → Checkboxes for all 7 roles from roles table
  → Currently assigned roles pre-checked
  → "Save Changes" → POST /api/admin/employees/:userId/roles { role_ids: [...] }
  → On success: modal closes, roles section refreshes, toast "Roles updated"
  → On error (not super_admin): 403 shown as inline error banner (should never happen via UI, but handle defensively)
  → Role change triggers: active JWT blacklisted → employee must log in again
  → Banner shows: "This employee will need to log in again for role changes to take effect"

  Revoke Role:
  → Click X on a role chip → confirm dialog: "Remove 'Order Admin' role from {name}?"
  → Confirm → DELETE /api/admin/employees/:userId/roles/:roleId
  → Role chip removed, activity logged

Create Employee:
  /admin/employees/new
  → Form: name, email, temporary password (auto-generated or manual)
  → POST /api/admin/employees (creates account with no roles)
  → Redirect to /admin/employees/:id to assign roles
  → Note: employee cannot do anything until at least one role is assigned
```

---

## 5. Screen Inventory

### Storefront (Customer-facing)

| # | Screen | Path | Auth |
|---|--------|------|------|
| 1 | Homepage | / | No |
| 2 | Search Results | /search | No |
| 3 | Product Listing Page | /products | No |
| 4 | Product Detail Page + Customizer | /products/:slug | No |
| 5 | Category Listing | /categories/:slug | No |
| 6 | Delivery Checker | /delivery-check | No |
| 7 | Cart Page | /cart | No (guest) |
| 8 | Checkout — Address Step | /checkout | Yes |
| 9 | Checkout — Payment Step | /checkout | Yes |
| 10 | Checkout — Confirmation | /checkout | Yes |
| 11 | Order Success | /checkout/success | Yes |
| 12 | Order Failure + Retry | /checkout/failure | Yes |
| 13 | Account Overview | /account | Yes |
| 14 | Profile Edit | /account/profile | Yes |
| 15 | Order History | /account/orders | Yes |
| 16 | Order Detail + Tracking | /account/orders/:id | Yes |
| 17 | Return Request | /account/orders/:id/return | Yes |
| 18 | Write Review | /account/orders/:id/review | Yes |
| 19 | Login | /auth/login | No |
| 20 | Register | /auth/register | No |
| 21 | Forgot Password | /auth/forgot-password | No |
| 22 | Reset Password | /auth/reset-password | No |
| 23 | MFA Verify | /auth/mfa-verify | Partial |
| 24 | MFA Setup | /account/security/mfa | Yes |

### Admin Portal

| # | Screen | Path | Role |
|---|--------|------|------|
| 25 | Super Admin Dashboard | /admin | super_admin |
| 26 | Employee List | /admin/employees | super_admin |
| 27 | Create Employee | /admin/employees/new | super_admin |
| 28 | Employee Detail + Role Assignment | /admin/employees/:id | super_admin |
| 29 | Roles Master List | /admin/roles | super_admin |
| 30 | Audit Logs Viewer | /admin/audit-logs | super_admin, management_user |
| 31 | System Settings | /admin/system/settings | super_admin |
| 32 | Product List | /admin/products | product_admin |
| 33 | Create Product | /admin/products/new | product_admin |
| 34 | Edit Product + Media | /admin/products/:id/edit | product_admin |
| 35 | Inventory Dashboard | /admin/inventory | product_admin |
| 36 | Inventory SKU Detail | /admin/inventory/:variantId | product_admin |
| 37 | Search Analytics | /admin/search-analytics | product_admin |
| 38 | Synonym Management | /admin/search/synonyms | product_admin |
| 39 | Order List | /admin/orders | order_admin |
| 40 | Order Detail + Actions | /admin/orders/:id | order_admin |
| 41 | Refund Queue | /admin/refunds | order_admin |
| 42 | Shipment List | /admin/shipments | shipping_admin |
| 43 | Shipment Detail + Tracking | /admin/shipments/:id | shipping_admin |
| 44 | Review Moderation Queue | /admin/reviews | review_moderator |
| 45 | Review Detail + Moderation | /admin/reviews/:id | review_moderator |
| 46 | Notification Campaign List | /admin/notifications | notification_admin |
| 47 | Create Notification Campaign | /admin/notifications/new | notification_admin |
| 48 | Code Panel — Change List | /admin/code-panel | management_user |
| 49 | Code Panel — Change Detail / Diff | /admin/code-panel/:id | management_user |

**Total: 49 screens**

---

## 6. Status Badge Convention

| State | Colour | Hex | Used On |
|-------|--------|-----|---------|
| **In Stock** | Green | `#2E7D32` | Product cards, PDP, inventory table |
| **Low Stock** | Amber | `#E65100` | Product cards ("Only N left!"), inventory alerts |
| **Out of Stock** | Red-Grey | `#B0BEC5` | Product cards, PDP (button disabled) |
| **Pre-Order** | Purple | `#6A1B9A` | Product cards, PDP |
| **Order: Pending Payment** | Yellow | `#F9A825` | Order list, order detail timeline |
| **Order: Confirmed** | Teal | `#00796B` | Order list, order detail timeline |
| **Order: Processing** | Blue | `#1565C0` | Order list, order detail timeline |
| **Order: Shipped** | Indigo | `#283593` | Order list, tracking timeline |
| **Order: Delivered** | Green | `#2E7D32` | Order list, tracking timeline |
| **Order: Returned** | Orange | `#E64A19` | Order list, order detail |
| **Order: Cancelled** | Red | `#C62828` | Order list, order detail |
| **Order: Closed** | Grey | `#616161` | Order list, archive view |
| **Payment: Pending** | Yellow | `#F9A825` | Payment column, order detail |
| **Payment: Paid** | Green | `#2E7D32` | Payment column |
| **Payment: Failed** | Red | `#C62828` | Payment column |
| **Payment: COD** | Blue-Grey | `#546E7A` | Payment method badge |
| **Review: Pending** | Yellow | `#F9A825` | Review moderation queue |
| **Review: Approved** | Green | `#2E7D32` | Review moderation queue |
| **Review: Hidden** | Grey | `#757575` | Review moderation queue |
| **Review: Flagged** | Red | `#C62828` | Review moderation queue |
| **Code Change: Draft** | Grey | `#90A4AE` | Code Panel list |
| **Code Change: Pending Approval** | Amber | `#FF8F00` | Code Panel list |
| **Code Change: Approved** | Green | `#2E7D32` | Code Panel list |
| **Code Change: Rejected** | Red | `#C62828` | Code Panel list |
| **Employee: Active** | Green | `#2E7D32` | Employee list |
| **Employee: Inactive** | Grey | `#9E9E9E` | Employee list |

---

## 7. Style Guide Basics

> Framework: **Tailwind CSS** (as specified in TDR stack). Custom theme tokens extend the Tailwind default config.

### Colour Palette

| Token | Hex | Tailwind Class | Usage |
|-------|-----|----------------|-------|
| Brand Primary | `#1A3D6B` | `brand-primary` | Navbar, CTAs, headings |
| Brand Secondary | `#2E6DB4` | `brand-secondary` | Links, active states, highlights |
| Brand Accent | `#4A90C4` | `brand-accent` | Hover states, focus rings |
| Brand Light | `#D6E6F7` | `brand-light` | Backgrounds, chips, info boxes |
| Surface White | `#FFFFFF` | `white` | Cards, modals, main content area |
| Surface Grey | `#F4F6FA` | `surface-grey` | Page background, table alternating rows |
| Text Primary | `#1C2533` | `text-primary` | Body copy, headings |
| Text Secondary | `#616E7C` | `text-secondary` | Labels, captions, helper text |
| Text Disabled | `#A0AEC0` | `text-disabled` | Disabled buttons, empty states |
| Success | `#2E7D32` | `success` | Stock in, confirmed, approved |
| Warning | `#E65100` | `warning` | Low stock, pending, caution |
| Error | `#C62828` | `error` | Out of stock, cancelled, failed |
| Info | `#1565C0` | `info` | Processing, informational banners |

### Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Display / Hero | Inter | 700 Bold | 40–48px |
| H1 Page Title | Inter | 700 Bold | 28–32px |
| H2 Section | Inter | 600 SemiBold | 20–24px |
| H3 Subsection | Inter | 600 SemiBold | 16–18px |
| Body | Inter | 400 Regular | 14–16px |
| Caption / Label | Inter | 400 Regular | 12px |
| Code / Mono (Code Panel) | JetBrains Mono | 400 | 13px |
| Price Display | Inter | 700 Bold | 20–28px |

### Component Tokens

| Component | Border Radius | Shadow |
|-----------|---------------|--------|
| Cards | 8px | `shadow-sm` |
| Modals | 12px | `shadow-xl` |
| Buttons | 6px | `shadow-none` |
| Input fields | 6px | `shadow-sm` on focus |
| Badges / Chips | 999px (pill) | none |
| Drawers | 0 (flush) | `shadow-2xl` left edge |

---

## 8. Accessibility & Responsiveness

### Accessibility Target: WCAG 2.1 Level AA

| Requirement | Implementation |
|-------------|----------------|
| Colour contrast | All text/background pairs meet 4.5:1 ratio minimum (verified against palette above) |
| Focus indicators | 2px solid `brand-accent` ring on all interactive elements (no outline:none without replacement) |
| Keyboard navigation | All flows completable via keyboard only (Tab, Enter, Space, Escape for modals/drawers) |
| Screen reader support | ARIA labels on icon-only buttons, ARIA live regions for stock badge updates and toast notifications |
| Form errors | Error messages associated with fields via `aria-describedby`; never colour-only indicators |
| Images | Alt text required on all product images; decorative images get `alt=""` |
| Focus management | Modal/drawer open: focus trapped inside. Modal close: focus returns to trigger element |
| Customizer canvas | Fabric.js canvas includes `aria-label` describing current customization state; keyboard shortcut list provided |

### Responsive Breakpoints (Tailwind defaults, no custom needed)

| Name | Width | Layout Changes |
|------|-------|----------------|
| `sm` | 640px | 1-col to 2-col product grid; search bar expands |
| `md` | 768px | 2-col to 3-col; cart drawer becomes overlay; admin sidebar collapses to icons |
| `lg` | 1024px | 3-col to 4-col products; PDP switches to side-by-side; admin sidebar expands to full |
| `xl` | 1280px | Max-width container (1200px) centred; admin full layout with right panels |
| `2xl` | 1536px | Dashboard grids switch to 4-column stat cards |

### Rendering Strategy (Next.js 14 App Router)

| Page Type | Strategy | Reason |
|-----------|----------|--------|
| Homepage, Category, PDP | SSR | SEO-critical; product data must be fresh |
| Search Results | SSR | Indexed by search engines; filter params in URL |
| Cart, Checkout, Account | CSR | Personalised; no SEO value; fast client transitions |
| Admin all pages | CSR | Behind auth wall; no SEO needed; rich interactivity |
| Checkout Success | SSR | Order confirmation page (no cache) |

---
---
---

# MASTER PROJECT BLUEPRINT
## Customizable Dropshipping E-Commerce Platform
### Docker + Git Milestone Workflow

---

## 1. Unified Directory Structure (Final State — All Phases)

```
dropp/                                       ← Monorepo root (npm workspaces)
│
├── .github/
│   ├── workflows/
│   │   ├── auth-service.yml                 ← CI: lint → test → build → deploy
│   │   ├── user-service.yml
│   │   ├── catalog-service.yml
│   │   ├── inventory-service.yml
│   │   ├── search-service.yml
│   │   ├── cart-service.yml
│   │   ├── order-service.yml
│   │   ├── payment-service.yml
│   │   ├── invoice-service.yml
│   │   ├── notification-service.yml
│   │   ├── review-service.yml
│   │   ├── shipping-service.yml
│   │   ├── admin-service.yml
│   │   ├── code-panel-service.yml
│   │   ├── delivery-check-service.yml
│   │   ├── storefront.yml
│   │   └── admin-portal.yml
│   └── PULL_REQUEST_TEMPLATE.md
│
├── infrastructure/
│   ├── nginx/
│   │   ├── nginx.conf                       ← API Gateway (all 15 routes)
│   │   └── ssl/                             ← TLS certs (production only)
│   ├── docker/
│   │   ├── Dockerfile.node                  ← Shared Node.js base image
│   │   └── Dockerfile.python                ← Shared Python/FastAPI base image
│   ├── k8s/                                 ← Kubernetes manifests (per service)
│   │   ├── namespace.yml
│   │   ├── auth-service/
│   │   │   ├── deployment.yml
│   │   │   ├── service.yml
│   │   │   └── hpa.yml
│   │   ├── inventory-service/
│   │   ├── search-service/
│   │   └── ... (one folder per service)
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── modules/
│           ├── vpc/
│           ├── eks/
│           ├── rds/
│           ├── elasticache/
│           ├── s3/
│           └── cloudfront/
│
├── docker-compose.yml                       ← Dev: all services + infra
├── docker-compose.override.yml              ← Dev overrides (hot reload volumes)
├── docker-compose.test.yml                  ← Integration test environment
├── .env.example                             ← All env var templates
├── .gitignore
├── package.json                             ← Root npm workspaces config
└── README.md
│
├── packages/
│   └── shared/                              ← @dropp/shared (Node.js 20)
│       ├── package.json
│       ├── src/
│       │   ├── index.js                     ← Barrel export
│       │   ├── logger/index.js              ← Winston logger factory
│       │   ├── errors/index.js              ← Custom error class hierarchy
│       │   ├── middleware/
│       │   │   ├── errorHandler.js
│       │   │   ├── authenticate.js          ← JWT verify + blacklist check
│       │   │   ├── requireRoles.js          ← RBAC factory middleware
│       │   │   └── requestLogger.js         ← Trace ID + HTTP logging
│       │   ├── response/index.js            ← sendSuccess / sendError / sendPaginated
│       │   └── validators/index.js          ← Joi helpers + commonSchemas
│       └── tests/shared.test.js
│
├── services/
│
│   ├── auth-service/                        ← Node.js 20 / Express (port 3001)
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── app.js
│   │   │   ├── server.js
│   │   │   ├── config/index.js
│   │   │   ├── routes/auth.routes.js
│   │   │   ├── controllers/auth.controller.js
│   │   │   ├── services/
│   │   │   │   ├── auth.service.js
│   │   │   │   └── token.service.js
│   │   │   ├── models/user.model.js
│   │   │   ├── middleware/validate.js
│   │   │   └── validators/auth.validators.js
│   │   ├── migrations/
│   │   │   ├── 001_create_users.sql
│   │   │   ├── 002_create_roles.sql
│   │   │   ├── 003_create_user_roles.sql
│   │   │   └── 004_create_audit_logs.sql
│   │   └── tests/
│   │       ├── auth.controller.test.js
│   │       └── auth.service.test.js
│   │
│   ├── user-service/                        ← Node.js 20 / Express (port 3002)
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── app.js
│   │   │   ├── server.js
│   │   │   ├── config/index.js
│   │   │   ├── routes/user.routes.js
│   │   │   ├── controllers/user.controller.js
│   │   │   ├── services/user.service.js
│   │   │   ├── models/user.model.js
│   │   │   ├── middleware/validate.js
│   │   │   └── validators/user.validators.js
│   │   └── tests/user.service.test.js
│   │
│   ├── catalog-service/                     ← Node.js 20 / Express (port 3003)
│   │   ├── package.json
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── app.js / server.js / config/
│   │   │   ├── routes/catalog.routes.js
│   │   │   ├── controllers/
│   │   │   │   ├── product.controller.js
│   │   │   │   └── category.controller.js
│   │   │   ├── services/
│   │   │   │   ├── product.service.js
│   │   │   │   └── media.service.js         ← S3 upload logic
│   │   │   ├── models/
│   │   │   │   ├── product.model.js
│   │   │   │   └── category.model.js
│   │   │   ├── events/
│   │   │   │   └── catalog.publisher.js     ← RabbitMQ event emitter
│   │   │   └── validators/catalog.validators.js
│   │   └── migrations/
│   │       ├── 005_create_categories.sql
│   │       ├── 006_create_products.sql
│   │       ├── 007_create_product_variants.sql
│   │       ├── 008_create_product_media.sql
│   │       └── 009_create_customization_rules.sql
│   │
│   ├── inventory-service/                   ← Python 3.12 / FastAPI (port 3004)
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── app/
│   │   │   ├── main.py                      ← FastAPI app entry point
│   │   │   ├── config.py                    ← Settings (pydantic BaseSettings)
│   │   │   ├── database.py                  ← PostgreSQL + Redis connections
│   │   │   ├── routers/
│   │   │   │   ├── stock.py                 ← Public check endpoints
│   │   │   │   └── admin.py                 ← Admin management endpoints
│   │   │   ├── services/
│   │   │   │   ├── stock_service.py
│   │   │   │   └── reservation_service.py
│   │   │   ├── models/
│   │   │   │   └── inventory.py             ← SQLAlchemy model
│   │   │   ├── schemas/
│   │   │   │   └── inventory.py             ← Pydantic schemas
│   │   │   ├── consumers/
│   │   │   │   └── catalog_consumer.py      ← RabbitMQ event listener
│   │   │   └── jobs/
│   │   │       └── low_stock_alert.py       ← Cron job (APScheduler)
│   │   ├── migrations/
│   │   │   └── 010_create_inventory.sql
│   │   └── tests/
│   │       ├── test_stock_service.py
│   │       └── test_reservation.py
│   │
│   ├── search-service/                      ← Node.js 20 / Express (port 3005)
│   │   ├── package.json / Dockerfile
│   │   ├── src/
│   │   │   ├── app.js / server.js / config/
│   │   │   ├── routes/search.routes.js
│   │   │   ├── controllers/search.controller.js
│   │   │   ├── services/
│   │   │   │   ├── search.service.js        ← Elasticsearch query builder
│   │   │   │   └── analytics.service.js
│   │   │   ├── workers/
│   │   │   │   └── index.sync.worker.js     ← RabbitMQ consumer → ES upsert
│   │   │   └── elasticsearch/
│   │   │       ├── client.js                ← ES connection
│   │   │       └── productIndex.js          ← Index mapping definition
│   │   └── tests/
│   │
│   ├── cart-service/                        ← Node.js 20 / Express (port 3006)
│   │   ├── src/
│   │   │   ├── app.js / server.js / config/
│   │   │   ├── routes/cart.routes.js
│   │   │   ├── controllers/cart.controller.js
│   │   │   ├── services/cart.service.js
│   │   │   └── models/cart.model.js         ← Redis cart operations
│   │   └── migrations/
│   │       └── 011_create_carts.sql
│   │
│   ├── order-service/                       ← Node.js 20 / Express (port 3007)
│   │   ├── src/
│   │   │   ├── routes/order.routes.js
│   │   │   ├── controllers/order.controller.js
│   │   │   ├── services/
│   │   │   │   ├── order.service.js
│   │   │   │   └── stateMachine.js          ← Order FSM
│   │   │   ├── models/order.model.js
│   │   │   └── events/order.publisher.js
│   │   └── migrations/
│   │       ├── 012_create_orders.sql
│   │       └── 013_create_order_items.sql
│   │
│   ├── payment-service/                     ← Node.js 20 / Express (port 3008)
│   │   ├── src/
│   │   │   ├── routes/payment.routes.js
│   │   │   ├── controllers/payment.controller.js
│   │   │   ├── services/
│   │   │   │   ├── payment.service.js
│   │   │   │   └── razorpay.service.js      ← Razorpay API wrapper
│   │   │   └── webhooks/
│   │   │       └── razorpay.webhook.js      ← HMAC-SHA256 signature verify
│   │   └── migrations/
│   │       └── 014_create_payments.sql
│   │
│   ├── invoice-service/                     ← Python 3.12 / FastAPI (port 3009)
│   │   ├── requirements.txt / Dockerfile
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── consumers/
│   │   │   │   └── order_consumer.py        ← Listens to order.confirmed
│   │   │   ├── services/
│   │   │   │   ├── pdf_service.py           ← WeasyPrint PDF generation
│   │   │   │   └── s3_service.py            ← Upload to AWS S3
│   │   │   └── templates/
│   │   │       └── invoice.html             ← Jinja2 HTML invoice template
│   │   └── migrations/
│   │       └── 015_create_invoices.sql
│   │
│   ├── notification-service/                ← Node.js 20 / Express (port 3010)
│   │   ├── src/
│   │   │   ├── consumers/                   ← RabbitMQ listeners
│   │   │   │   ├── order.consumer.js
│   │   │   │   └── inventory.consumer.js
│   │   │   ├── providers/
│   │   │   │   ├── email.provider.js        ← SendGrid
│   │   │   │   ├── whatsapp.provider.js     ← Meta WhatsApp Business API
│   │   │   │   ├── push.provider.js         ← Firebase FCM
│   │   │   │   └── sms.provider.js          ← Twilio
│   │   │   └── services/notification.service.js
│   │   └── migrations/
│   │       └── 016_create_notifications.sql
│   │
│   ├── review-service/                      ← Node.js 20 / Express (port 3011)
│   │   ├── src/
│   │   │   ├── routes/review.routes.js
│   │   │   ├── controllers/review.controller.js
│   │   │   ├── services/review.service.js
│   │   │   └── models/review.model.js
│   │   └── migrations/
│   │       ├── 017_create_reviews.sql
│   │       └── 018_create_review_media.sql
│   │
│   ├── shipping-service/                    ← Node.js 20 / Express (port 3012)
│   │   ├── src/
│   │   │   ├── routes/shipping.routes.js
│   │   │   ├── services/
│   │   │   │   ├── shipping.service.js
│   │   │   │   └── couriers/
│   │   │   │       ├── delhivery.js         ← Delhivery API adapter
│   │   │   │       └── shiprocket.js        ← Shiprocket fallback adapter
│   │   │   └── webhooks/courier.webhook.js
│   │   └── migrations/
│   │       └── 019_create_shipments.sql
│   │
│   ├── admin-service/                       ← Node.js 20 / Express (port 3013)
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── roles.routes.js
│   │   │   │   ├── employee.routes.js
│   │   │   │   └── auditLog.routes.js
│   │   │   ├── controllers/
│   │   │   │   ├── roles.controller.js
│   │   │   │   ├── employee.controller.js
│   │   │   │   └── auditLog.controller.js
│   │   │   └── services/
│   │   │       ├── role.service.js
│   │   │       └── employee.service.js
│   │   └── (shares migrations from auth-service)
│   │
│   ├── code-panel-service/                  ← Node.js 20 / Express (port 3014)
│   │   ├── src/
│   │   │   ├── routes/codePanel.routes.js
│   │   │   ├── controllers/codePanel.controller.js
│   │   │   └── services/codePanel.service.js
│   │   └── migrations/
│   │       └── 020_create_code_changes.sql
│   │
│   └── delivery-check-service/              ← Node.js 20 / Express (port 3015)
│       ├── src/
│       │   ├── routes/delivery.routes.js
│       │   ├── controllers/delivery.controller.js
│       │   └── services/
│       │       └── pincode.service.js       ← India Post / Google Maps API
│       └── tests/
│
└── frontend/
    ├── storefront/                          ← Next.js 14 (port 3000)
    │   ├── package.json / next.config.js
    │   ├── tailwind.config.js               ← Custom theme tokens
    │   ├── app/                             ← App Router
    │   │   ├── layout.tsx                   ← Root layout (navbar, footer)
    │   │   ├── page.tsx                     ← Homepage (SSR)
    │   │   ├── search/page.tsx              ← Search results (SSR)
    │   │   ├── products/
    │   │   │   ├── page.tsx                 ← PLP (SSR)
    │   │   │   └── [slug]/page.tsx          ← PDP + customizer (SSR)
    │   │   ├── categories/[slug]/page.tsx
    │   │   ├── cart/page.tsx                ← Cart (CSR)
    │   │   ├── checkout/
    │   │   │   ├── page.tsx                 ← Checkout funnel (CSR)
    │   │   │   ├── success/page.tsx
    │   │   │   └── failure/page.tsx
    │   │   ├── account/
    │   │   │   ├── page.tsx
    │   │   │   ├── profile/page.tsx
    │   │   │   └── orders/
    │   │   │       ├── page.tsx
    │   │   │       └── [id]/page.tsx
    │   │   └── auth/
    │   │       ├── login/page.tsx
    │   │       ├── register/page.tsx
    │   │       └── ...
    │   ├── components/
    │   │   ├── ui/                          ← Base: Button, Badge, Input, Modal
    │   │   ├── layout/                      ← Navbar, Footer, Breadcrumb
    │   │   ├── product/                     ← ProductCard, ProductGrid, VariantSelector
    │   │   ├── customizer/                  ← Fabric.js canvas wrapper
    │   │   ├── cart/                        ← CartDrawer, CartItem
    │   │   ├── checkout/                    ← AddressForm, PaymentSelector, OrderSummary
    │   │   └── search/                      ← SearchBar, Autocomplete, FilterPanel
    │   ├── lib/
    │   │   ├── api/                         ← API client functions (per service)
    │   │   ├── store/                       ← Zustand stores (cart, auth)
    │   │   └── hooks/                       ← useCart, useInventory, useSearch
    │   └── public/
    │
    └── admin-portal/                        ← Next.js 14 (port 3100)
        ├── package.json / next.config.js
        ├── tailwind.config.js
        ├── app/
        │   ├── layout.tsx                   ← Admin layout (sidebar + topbar)
        │   ├── admin/
        │   │   ├── page.tsx                 ← Super Admin dashboard
        │   │   ├── employees/
        │   │   │   ├── page.tsx
        │   │   │   ├── new/page.tsx
        │   │   │   └── [id]/page.tsx        ← Role assignment screen
        │   │   ├── products/
        │   │   ├── inventory/
        │   │   ├── orders/
        │   │   ├── shipments/
        │   │   ├── reviews/
        │   │   ├── notifications/
        │   │   ├── code-panel/
        │   │   └── audit-logs/
        ├── components/
        │   ├── ui/                          ← Admin UI primitives
        │   ├── layout/                      ← AdminSidebar (role-filtered), Topbar
        │   ├── roles/                       ← RoleAssignmentModal, RoleBadge
        │   ├── inventory/                   ← StockTable, AlertFlag, ThresholdEditor
        │   ├── orders/                      ← OrderTable, StatusTimeline, ActionButtons
        │   ├── code-panel/                  ← DiffViewer, ApprovalButtons
        │   └── shared/                      ← StatusBadge, DataTable, FilterBar
        └── lib/
            ├── api/
            ├── store/
            └── hooks/
```

---

## 2. Git + Docker Workflow

### Branch Strategy

| Branch | Purpose | Rules |
|--------|---------|-------|
| `main` | Production-ready code | Protected. PRs only. Requires 1 approver + all CI checks green. Triggers prod deploy. |
| `staging` | Pre-production integration | Protected. Merge from feature branches. Triggers staging deploy. |
| `feature/P{n}-{short-desc}` | Feature development | Created from `staging`. e.g. `feature/P1-auth-service` |
| `fix/P{n}-{short-desc}` | Bug fixes | Created from `staging` or `main` depending on severity |
| `chore/{desc}` | Infrastructure, config, docs | Non-code changes; still goes through PR |

### Branch Naming Convention

```
feature/P0-monorepo-setup
feature/P1-auth-service
feature/P1-user-service
feature/P2-catalog-service
feature/P2-admin-roles
feature/P3-inventory-service
feature/P3-search-service
feature/P4-cart-checkout
feature/P4-payment-razorpay
feature/P5-invoice-notifications
feature/P5-review-moderation
feature/P5-shipping-tracking
feature/P6-storefront
feature/P6-admin-portal
```

### Docker Testing Workflow (per milestone)

```
For each feature branch before raising a PR:

1. Developer runs:
   docker compose -f docker-compose.yml -f docker-compose.test.yml up --build {service-name}

2. This starts:
   - The service under test (with test env vars)
   - Its real dependencies (postgres, redis, rabbitmq)
   - No mocked infrastructure — full integration test

3. Run tests inside container:
   docker compose exec {service-name} npm test
   (or: docker compose exec {service-name} pytest)

4. All tests must pass before committing.

5. After passing:
   git add .
   git commit -m "P{n}: {descriptive message} ✓ tests passing"
   git push origin feature/P{n}-{desc}
   → Open PR to staging
```

### Commit Message Format

```
P{milestone}: {verb} {what was done}

Examples:
P1: Add JWT register and login endpoints ✓ tests passing
P2: Add product catalog CRUD with S3 media upload
P3: Implement Elasticsearch index sync worker
P4: Integrate Razorpay webhook with HMAC verification
P5: Add WeasyPrint PDF invoice generation
P6: Build storefront product customizer with Fabric.js
```

### CI/CD Gates (GitHub Actions — per service)

```
PR → staging:
  1. lint (ESLint / Flake8)           ← fails fast
  2. unit tests (Jest / Pytest)       ← coverage gate > 80%
  3. docker build                     ← image must build
  4. integration test                 ← docker-compose test env

Merge to staging:
  5. deploy to staging cluster
  6. smoke tests against staging URL

PR staging → main:
  7. manual approval (required)
  8. security scan (Trivy)

Merge to main:
  9. deploy to production (Helm upgrade)
  10. Slack notification
```

---

## 3. Milestone → Feature → Commit Map (P0 → P6)

### P0 — Foundation: Monorepo, Infrastructure, Shared Package
**Goal:** Every developer can clone the repo, run `docker compose up`, and have a working local environment with all infrastructure ready.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Monorepo root (npm workspaces, .gitignore, README) | `package.json`, `.gitignore`, `README.md` | P0: Init monorepo with npm workspaces |
| 2 | Environment configuration (.env.example) | `.env.example` | P0: Add environment variable templates |
| 3 | Docker Compose (postgres, redis, rabbitmq, nginx) | `docker-compose.yml`, `docker-compose.override.yml` | P0: Add docker-compose dev environment |
| 4 | Nginx API Gateway config | `infrastructure/nginx/nginx.conf` | P0: Add Nginx gateway with all 15 route stubs |
| 5 | Shared Node.js base Dockerfile | `infrastructure/docker/Dockerfile.node` | P0: Add shared Node.js Dockerfile |
| 6 | Shared Python base Dockerfile | `infrastructure/docker/Dockerfile.python` | P0: Add shared Python Dockerfile |
| 7 | @dropp/shared — logger, errors, middleware, response, validators | `packages/shared/src/**` | P0: Add @dropp/shared package with all utilities |
| 8 | @dropp/shared unit tests | `packages/shared/tests/shared.test.js` | P0: Add shared package unit tests ✓ |

**Exit criteria:** `docker compose up` starts postgres, redis, rabbitmq, nginx healthy. `npm test` in packages/shared passes.

---

### P1 — Auth + User Services
**Goal:** Users can register, log in (with MFA for admins), receive JWT tokens, and manage their profiles. The full auth layer is live and tested.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Auth Service — DB migrations (users, roles, user_roles, audit_logs) | `auth-service/migrations/001-004` | P1: Add auth database schema migrations |
| 2 | Auth Service — user model (PostgreSQL queries) | `auth-service/src/models/user.model.js` | P1: Add user model with parameterized queries |
| 3 | Auth Service — token service (JWT RS256, blacklist) | `auth-service/src/services/token.service.js` | P1: Add JWT token service with Redis blacklist |
| 4 | Auth Service — auth business logic | `auth-service/src/services/auth.service.js` | P1: Add auth service (register, login, MFA, logout) |
| 5 | Auth Service — validators, controllers, routes | `auth-service/src/validators/`, `controllers/`, `routes/` | P1: Add auth controllers and routes |
| 6 | Auth Service — app.js, server.js, config, Dockerfile | `auth-service/src/app.js`, `server.js`, `config/`, `Dockerfile` | P1: Add auth service Express app and Docker config |
| 7 | Auth Service — unit tests | `auth-service/tests/**` | P1: Add auth service tests ✓ 80%+ coverage |
| 8 | User Service — user model (profile queries) | `user-service/src/models/user.model.js` | P1: Add user model with profile operations |
| 9 | User Service — user service, controller, routes | `user-service/src/services/`, `controllers/`, `routes/` | P1: Add user service profile management |
| 10 | User Service — app.js, server.js, Dockerfile | `user-service/src/app.js`, `server.js`, `Dockerfile` | P1: Add user service app and Docker config |
| 11 | User Service — unit tests | `user-service/tests/**` | P1: Add user service tests ✓ |
| 12 | Nginx routes for /api/auth + /api/users | `infrastructure/nginx/nginx.conf` | P1: Enable auth and user routes in gateway |

**Exit criteria:** `POST /api/auth/register` → 201. `POST /api/auth/login` → 200 + JWT. `GET /api/users/me` with valid JWT → 200. MFA setup and verify working for admin accounts.

---

### P2 — Catalog + Admin Service + Delivery Check
**Goal:** Product catalog is fully manageable. Super Admin can assign roles to employees. Delivery availability checking works. Admins can log in and see role-appropriate views.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Catalog DB migrations (categories, products, variants, media, customization_rules) | `catalog-service/migrations/005-009` | P2: Add catalog database schema |
| 2 | Catalog — product and category models | `catalog-service/src/models/**` | P2: Add catalog data access layer |
| 3 | Catalog — media service (S3 upload) | `catalog-service/src/services/media.service.js` | P2: Add S3 media upload service |
| 4 | Catalog — product service + CRUD API | `catalog-service/src/services/product.service.js` | P2: Add product catalog CRUD |
| 5 | Catalog — RabbitMQ event publisher | `catalog-service/src/events/catalog.publisher.js` | P2: Add catalog event publisher |
| 6 | Catalog — controllers, routes, validators, Dockerfile | `catalog-service/src/**` | P2: Add catalog service app and Docker |
| 7 | Admin Service — role management (assign/revoke) | `admin-service/src/services/role.service.js` | P2: Add super admin role assignment logic |
| 8 | Admin Service — employee management | `admin-service/src/services/employee.service.js` | P2: Add employee management endpoints |
| 9 | Admin Service — audit log viewer | `admin-service/src/controllers/auditLog.controller.js` | P2: Add audit log query API |
| 10 | Admin Service — app, routes, Dockerfile | `admin-service/src/app.js`, `Dockerfile` | P2: Add admin service app |
| 11 | Delivery Check Service — pincode API | `delivery-check-service/src/**` | P2: Add delivery availability check service |
| 12 | Nginx routes for /api/catalog, /api/admin, /api/delivery | nginx.conf | P2: Enable catalog, admin, delivery routes |

**Exit criteria:** Product CRUD works. Super Admin can assign multiple roles to an employee. Employee JWT reflects new roles on next login. Pincode check returns delivery availability.

---

### P3 — Inventory Service + Search Service
**Goal:** Real-time stock availability works on every product page and in cart. Full-text search with filters and autocomplete is live. Stock and catalog changes sync to search index automatically.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Inventory DB migration | `inventory-service/migrations/010_create_inventory.sql` | P3: Add inventory database schema |
| 2 | Inventory — FastAPI app, config, database connection | `inventory-service/app/main.py`, `config.py`, `database.py` | P3: Add inventory service FastAPI setup |
| 3 | Inventory — stock check and bulk check API | `inventory-service/app/routers/stock.py` | P3: Add stock availability check endpoints |
| 4 | Inventory — reservation service (Redis TTL) | `inventory-service/app/services/reservation_service.py` | P3: Add stock reservation with Redis TTL |
| 5 | Inventory — admin endpoints (adjust, sync) | `inventory-service/app/routers/admin.py` | P3: Add inventory admin management endpoints |
| 6 | Inventory — catalog event consumer | `inventory-service/app/consumers/catalog_consumer.py` | P3: Add RabbitMQ catalog event consumer |
| 7 | Inventory — low-stock alert cron job | `inventory-service/app/jobs/low_stock_alert.py` | P3: Add low-stock alert scheduled job |
| 8 | Inventory — Dockerfile + tests | `inventory-service/Dockerfile`, `tests/` | P3: Add inventory service Docker + tests ✓ |
| 9 | Search Service — Elasticsearch client + index mapping | `search-service/src/elasticsearch/**` | P3: Add Elasticsearch product index configuration |
| 10 | Search Service — sync worker (RabbitMQ → ES) | `search-service/src/workers/index.sync.worker.js` | P3: Add catalog-to-ES sync worker |
| 11 | Search Service — search API (full-text, filters, autocomplete, similar) | `search-service/src/services/search.service.js` | P3: Add product search API with faceted filters |
| 12 | Search Service — analytics (click tracking, reports) | `search-service/src/services/analytics.service.js` | P3: Add search analytics service |
| 13 | Nginx routes for /api/inventory, /api/search | nginx.conf | P3: Enable inventory and search routes |

**Exit criteria:** `GET /api/inventory/check/:variantId` returns `{ available_qty, status, reserved_qty }` in <100ms. `GET /api/search/products?q=shirt&color=blue` returns ranked results. Product update in catalog reflects in search within 5 seconds.

---

### P4 — Cart + Checkout + Orders + Payments
**Goal:** A customer can browse, add to cart (with live stock reservation), check out using UPI/card/COD via Razorpay, and receive an order confirmation. Stock is permanently deducted on successful payment.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Cart DB migration (carts, cart_items) | `cart-service/migrations/011_create_carts.sql` | P4: Add cart database schema |
| 2 | Cart Service — Redis cart model | `cart-service/src/models/cart.model.js` | P4: Add Redis cart storage model |
| 3 | Cart Service — cart service (add, update, remove, merge) | `cart-service/src/services/cart.service.js` | P4: Add cart management with inventory reservation |
| 4 | Cart Service — routes, controllers, Dockerfile | `cart-service/src/**` | P4: Add cart service app |
| 5 | Order DB migrations (orders, order_items) | `order-service/migrations/012-013` | P4: Add order database schema |
| 6 | Order Service — state machine | `order-service/src/services/stateMachine.js` | P4: Add order state machine (8 states) |
| 7 | Order Service — checkout flow | `order-service/src/services/order.service.js` | P4: Add checkout and order creation logic |
| 8 | Order Service — event publisher | `order-service/src/events/order.publisher.js` | P4: Add order event publisher |
| 9 | Order Service — routes, controllers, Dockerfile | `order-service/src/**` | P4: Add order service app |
| 10 | Payment DB migration | `payment-service/migrations/014_create_payments.sql` | P4: Add payment database schema |
| 11 | Payment Service — Razorpay integration | `payment-service/src/services/razorpay.service.js` | P4: Add Razorpay order creation |
| 12 | Payment Service — webhook (HMAC verify) | `payment-service/src/webhooks/razorpay.webhook.js` | P4: Add Razorpay webhook handler with HMAC-SHA256 |
| 13 | Payment Service — COD logic | `payment-service/src/services/payment.service.js` | P4: Add COD payment flow with configurable fee |
| 14 | Payment Service — routes, controllers, Dockerfile | `payment-service/src/**` | P4: Add payment service app |
| 15 | Nginx routes for /api/cart, /api/orders, /api/payments | nginx.conf | P4: Enable cart, order, payment routes |

**Exit criteria:** Full checkout flow works end-to-end. Razorpay test payment succeeds → order CONFIRMED → stock permanently deducted. COD order created immediately with status CONFIRMED. Inventory reservation released on payment failure.

---

### P5 — Invoices + Notifications + Reviews + Shipping
**Goal:** Customers receive PDF invoices by email and WhatsApp after every order. Order status notifications are sent at each state change. Reviews work for verified buyers. Shipment tracking is live.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Invoice DB migration | `invoice-service/migrations/015_create_invoices.sql` | P5: Add invoice database schema |
| 2 | Invoice — Jinja2 HTML template | `invoice-service/app/templates/invoice.html` | P5: Add Indian GST-format invoice template |
| 3 | Invoice — WeasyPrint PDF generation | `invoice-service/app/services/pdf_service.py` | P5: Add PDF invoice generation |
| 4 | Invoice — S3 upload service | `invoice-service/app/services/s3_service.py` | P5: Add invoice S3 upload |
| 5 | Invoice — order.confirmed consumer | `invoice-service/app/consumers/order_consumer.py` | P5: Add order event consumer for invoice trigger |
| 6 | Invoice — FastAPI app + Dockerfile | `invoice-service/app/main.py`, `Dockerfile` | P5: Add invoice service app |
| 7 | Notification DB migration | `notification-service/migrations/016_create_notifications.sql` | P5: Add notification database schema |
| 8 | Notification — email (SendGrid) | `notification-service/src/providers/email.provider.js` | P5: Add SendGrid email provider |
| 9 | Notification — WhatsApp (Meta API) | `notification-service/src/providers/whatsapp.provider.js` | P5: Add WhatsApp notification provider |
| 10 | Notification — push (Firebase FCM) | `notification-service/src/providers/push.provider.js` | P5: Add FCM push notification provider |
| 11 | Notification — SMS (Twilio) | `notification-service/src/providers/sms.provider.js` | P5: Add Twilio SMS provider |
| 12 | Notification — RabbitMQ consumers + routing | `notification-service/src/consumers/**` | P5: Add notification event routing |
| 13 | Notification — campaign API + Dockerfile | `notification-service/src/**` | P5: Add notification service app |
| 14 | Review DB migrations | `review-service/migrations/017-018` | P5: Add review database schema |
| 15 | Review Service — verified purchase check | `review-service/src/services/review.service.js` | P5: Add review submission with purchase verification |
| 16 | Review Service — moderation API | `review-service/src/services/review.service.js` | P5: Add review moderation (approve/hide/flag) |
| 17 | Review Service — event publisher (rating update) | `review-service/src/events/review.publisher.js` | P5: Add review event publisher for search sync |
| 18 | Shipment DB migration | `shipping-service/migrations/019_create_shipments.sql` | P5: Add shipment database schema |
| 19 | Shipping — Delhivery adapter | `shipping-service/src/services/couriers/delhivery.js` | P5: Add Delhivery courier integration |
| 20 | Shipping — Shiprocket fallback adapter | `shipping-service/src/services/couriers/shiprocket.js` | P5: Add Shiprocket fallback courier |
| 21 | Shipping — tracking webhook + status machine | `shipping-service/src/webhooks/`, `routes/` | P5: Add shipping tracking webhook handler |
| 22 | Nginx routes for /api/invoices, /api/notifications, /api/reviews, /api/shipping | nginx.conf | P5: Enable all P5 service routes |
| 23 | Code Panel DB migration + service stub | `code-panel-service/migrations/`, `src/**` | P5: Add code panel service (proposal + approval API) |

**Exit criteria:** After order CONFIRMED → PDF invoice generated and emailed within 30 seconds. WhatsApp delivery confirmed. Review submitted for delivered order → appears in moderation queue. Shipment tracking status updated from courier webhook.

---

### P6 — Frontend (Storefront + Admin Portal) + QA + Launch
**Goal:** Full customer-facing storefront and admin portal are live. All 49 screens built and connected to real APIs. QA complete. Platform deployed to production.

| # | Feature | Files Affected | Commit |
|---|---------|----------------|--------|
| 1 | Storefront — Next.js 14 setup, Tailwind config, shared layout | `frontend/storefront/**` | P6: Init storefront with layout and routing |
| 2 | Storefront — Homepage, PLP, PDP (SSR) | `app/page.tsx`, `products/[slug]/page.tsx` | P6: Add product browsing screens |
| 3 | Storefront — Product customizer (Fabric.js) | `components/customizer/**` | P6: Add Fabric.js product customization canvas |
| 4 | Storefront — Search bar + autocomplete + results | `components/search/**`, `app/search/page.tsx` | P6: Add search UI with autocomplete |
| 5 | Storefront — Cart drawer + inventory badge | `components/cart/**`, `lib/store/cart.store.ts` | P6: Add cart UI with real-time stock badges |
| 6 | Storefront — Checkout funnel (3 steps) | `app/checkout/**` | P6: Add 3-step checkout with Razorpay modal |
| 7 | Storefront — Account screens (profile, orders, tracking) | `app/account/**` | P6: Add customer account and order tracking |
| 8 | Storefront — Auth screens (login, register, MFA) | `app/auth/**` | P6: Add auth screens with MFA verify step |
| 9 | Storefront — Review submission | `app/account/orders/[id]/review/` | P6: Add verified purchase review screen |
| 10 | Admin Portal — Next.js 14 setup, role-aware sidebar | `frontend/admin-portal/**` | P6: Init admin portal with role-filtered navigation |
| 11 | Admin Portal — Super Admin dashboard + employee management + role assignment | `app/admin/employees/**` | P6: Add Super Admin role assignment UI |
| 12 | Admin Portal — Product management + inventory dashboard | `app/admin/products/**`, `inventory/**` | P6: Add product and inventory admin screens |
| 13 | Admin Portal — Order management + refunds | `app/admin/orders/**` | P6: Add order management admin screens |
| 14 | Admin Portal — Shipment management | `app/admin/shipments/**` | P6: Add shipping admin screens |
| 15 | Admin Portal — Review moderation queue | `app/admin/reviews/**` | P6: Add review moderation UI |
| 16 | Admin Portal — Search analytics + synonym editor | `app/admin/search-analytics/**` | P6: Add search analytics dashboard |
| 17 | Admin Portal — Notification campaigns | `app/admin/notifications/**` | P6: Add notification campaign management |
| 18 | Admin Portal — Code Panel (diff viewer + approval) | `app/admin/code-panel/**` | P6: Add code panel with diff viewer |
| 19 | Admin Portal — Audit log viewer | `app/admin/audit-logs/**` | P6: Add audit log filterable table |
| 20 | End-to-end tests (Playwright) | `tests/e2e/**` | P6: Add E2E tests for critical paths |
| 21 | Load tests (k6) | `tests/load/**` | P6: Add k6 load tests (5000 concurrent users) |
| 22 | Security hardening (OWASP ZAP scan, Trivy) | CI workflows | P6: Fix all security scan findings |
| 23 | Kubernetes manifests (all services) | `infrastructure/k8s/**` | P6: Add Kubernetes deployment manifests |
| 24 | Terraform cloud infrastructure | `infrastructure/terraform/**` | P6: Add Terraform IaC for production cloud |
| 25 | Grafana dashboards + PagerDuty alerts | `infrastructure/monitoring/**` | P6: Add observability dashboards and alerting |
| 26 | Production deploy + smoke tests | GitHub Actions workflows | P6: Production launch ✓ |

**Exit criteria:** All 49 screens live and functional. Core Web Vitals: LCP < 2.5s. Search p95 < 300ms. Inventory check p95 < 100ms. Platform uptime > 99.9%. 0 High/Critical OWASP findings. End-to-end checkout flow works in production.

---

## Summary

| Milestone | Services Built | Key Deliverable |
|-----------|---------------|-----------------|
| **P0** | Shared infra + @dropp/shared | Local dev environment live |
| **P1** | Auth + User | JWT auth + profile management |
| **P2** | Catalog + Admin + Delivery | Product catalog + role assignment |
| **P3** | Inventory + Search | Real-time stock + full-text search |
| **P4** | Cart + Order + Payment | Full checkout funnel + Razorpay |
| **P5** | Invoice + Notification + Review + Shipping | Post-order flows complete |
| **P6** | Storefront + Admin Portal + QA | Production-ready platform live |

**Total screens: 49 | Total services: 15 | Total milestones: 7 (P0–P6)**

