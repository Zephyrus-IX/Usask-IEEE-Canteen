# MVP Scope

## Included in prototype v1

### Accounts

- Student ID is required
- First and last name are required
- Account status: active/inactive
- IEEE membership status: yes/no
- IEEE member ID when applicable
- IEEE membership expiry date when applicable
- Expired memberships automatically lose discount pricing
- Optional prepaid balance

### Sales

- Public customer sales use the logged-in customer account.
- Staff/superuser accounts can facilitate purchases for any student account.
- No anonymous sales
- No account means no sale
- Sale purchases use student account balance only.
- Cash/card are recorded only when staff load money onto an account.
- Sales do not charge taxes
- Receipts are not required
- Completed sales automatically reduce inventory

### Inventory

- Each product is a separate inventory item
- No category system for MVP
- Member price and non-member price per item
- Current quantity
- Low stock threshold
- Active/inactive flag
- Manual adjustments with reason for theft/damage/count corrections

### Restocks

- Admin/exec manually enters restock receipts
- A restock can contain multiple items
- Taxes are selected per restock from configured tax rates
- Tax amounts are auto-calculated but can be overridden
- Restock tax is allocated proportionally across line items
- Completed restocks automatically increase inventory

### Reports

- Date-filtered dashboard totals
- CSV exports for:
  - sales
  - balance loads
  - restocks
  - inventory
  - accounts

## Deferred until later

- Split payments
- Direct Square Terminal integration
- Receipts
- Sales tax collection
- Public ecommerce storefront
- Polished UI
- Full-screen TUI
