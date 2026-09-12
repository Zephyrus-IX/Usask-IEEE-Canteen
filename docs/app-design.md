# App Design

## Core rule summary

1. Every sale must be attached to an active account.
2. Accounts are created by an admin/IEEE exec.
3. IEEE membership discount applies only when membership is marked active and expiry date has not passed.
4. Sales decrease inventory automatically.
5. Restocks increase inventory automatically.
6. Student-balance sales require sufficient available balance.
7. Restock tax rates are configurable and copied into historical records at the time of restock.
8. Business rules should live in shared backend services so both web UI and future CLI/TUI use the same logic.

## MVP screens

```text
New Sale
Accounts
Inventory
Restocks
Reports
Settings
```

## Data model draft

### Account

- user (Django user; NSID is the username)
- must_change_password
- first_name
- last_name
- is_active
- is_ieee_member
- ieee_member_id
- ieee_membership_expires_on
- notes
- created_by
- created_at
- updated_at

Student Numbers are not collected or stored. Account creation and executive-initiated password resets generate a one-time temporary password. The student must replace it at the next sign-in.

### InventoryItem

- name
- quantity_on_hand
- member_price
- non_member_price
- low_stock_threshold
- is_active
- notes
- created_at
- updated_at

### Sale

- account
- handled_by
- payment_method
- total_amount
- status
- created_at

### SaleItem

- sale
- inventory_item
- quantity
- unit_price
- line_total

### BalanceTransaction

- account
- transaction_type: load, purchase, refund, adjustment
- payment_method: cash, card, balance, internal
- amount
- related_sale
- handled_by
- note
- created_at

### RestockEvent

- vendor
- restocked_on
- entered_by
- subtotal
- total_tax
- total_paid
- notes
- created_at

### RestockItem

- restock_event
- inventory_item
- quantity
- line_subtotal
- allocated_tax
- line_total

### TaxRate

- name
- rate_percent
- is_active
- created_at
- updated_at

### RestockTaxLine

- restock_event
- tax_name
- rate_percent
- calculated_amount
- actual_amount
- was_applied

## Interface strategy

The first interface will be a plain functional Django web UI. A CLI/TUI fallback will be added later, sharing the same service functions rather than duplicating business rules.
