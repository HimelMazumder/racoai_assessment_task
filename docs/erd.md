# Entity Relationship Diagram

## Overview

This ERD covers the five core tables of the e-commerce system: Users, Products, Categories, Orders, OrderItems, and Payments.

## ERD (Mermaid)

```mermaid
erDiagram
    Users {
        int id PK
        string username UK
        string email UK
        string password
        datetime date_joined
    }

    Categories {
        int id PK
        string name
        string slug UK
        int parent_id FK "self-referential, nullable"
    }

    Products {
        int id PK
        string name
        string sku UK
        text description
        decimal price
        int stock
        string status "active / inactive"
        int category_id FK "nullable"
        datetime created_at
        datetime updated_at
    }

    Orders {
        int id PK
        int user_id FK
        decimal total_amount
        string status "pending / paid / cancelled / stock_conflict"
        datetime created_at
        datetime updated_at
    }

    OrderItems {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
        decimal subtotal "auto-calculated: price * quantity"
    }

    Payments {
        int id PK
        int order_id FK
        string provider "stripe / bkash"
        string transaction_id UK
        string status "pending / success / failed"
        json raw_response "nullable"
        datetime created_at
        datetime updated_at
    }

    Users ||--o{ Orders : "places"
    Orders ||--|{ OrderItems : "contains"
    Products ||--o{ OrderItems : "referenced in"
    Categories ||--o{ Products : "categorizes"
    Categories ||--o{ Categories : "parent → child"
    Orders ||--o{ Payments : "paid via"
```

## Table Relationships

| Relationship | Type | Constraint |
|---|---|---|
| Users → Orders | One-to-Many | `CASCADE` (delete user deletes orders) |
| Orders → OrderItems | One-to-Many | `CASCADE` (delete order deletes items) |
| Products → OrderItems | One-to-Many | `PROTECT` (cannot delete product with existing orders) |
| Categories → Products | One-to-Many | `SET_NULL` (delete category sets product.category to NULL) |
| Categories → Categories | Self-referential | `CASCADE` (delete parent deletes children) |
| Orders → Payments | One-to-Many | `CASCADE` (delete order deletes payments) |

## Indexed Fields

| Table | Field | Index Type |
|---|---|---|
| Products | `sku` | Unique Index |
| Categories | `slug` | Unique Index |
| Payments | `transaction_id` | Unique Index |
| Users | `email` | Unique Index |
| Users | `username` | Unique Index |
| Orders | `user_id` | FK Index (auto) |
| OrderItems | `order_id` | FK Index (auto) |
| OrderItems | `product_id` | FK Index (auto) |
| Payments | `order_id` | FK Index (auto) |
| Products | `category_id` | FK Index (auto) |
