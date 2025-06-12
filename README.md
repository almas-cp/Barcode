# Warehouse Barcode Management System

A terminal-based barcode management system for warehouse inventory tracking.

## Features

- View complete inventory list
- Search for items by ID or name
- Display detailed item information
- Generate and display barcodes in the terminal
- Save barcodes as image files
- Print barcode labels

## Requirements

- Python 3.6+
- Required packages (automatically installed if missing):
  - python-barcode
  - Pillow (PIL)

## Installation

1. Clone or download this repository
2. Ensure Python 3.6+ is installed
3. Run the script - it will automatically install required dependencies

## Usage

Run the application:

```
python barcode_manager.py
```

The system will automatically load the items from `items.csv` and present a menu with the following options:

1. **List All Items** - Display all inventory items in a table format
2. **Search Item by ID** - Find and display details for a specific item ID
3. **Search Item by Name** - Search for items by name (partial matches supported)
4. **Generate Barcode for Item** - Display an ASCII representation of the barcode in the terminal
5. **Display Item Details** - Show all details for a specific item
6. **Print Barcode for Item** - Generate a barcode image file and provide printing instructions
7. **Exit** - Close the application

## CSV Data Format

The system uses a CSV file (`items.csv`) with the following columns:

- `item_id` - Unique identifier for each item
- `name` - Item name
- `category` - Item category
- `quantity` - Number of items in stock
- `location` - Storage location in warehouse
- `supplier` - Supplier name
- `unit_price` - Price per unit
- `barcode` - Barcode number (EAN-13 or Code128)
- `date_added` - Date the item was added to inventory
- `expiry_date` - Expiration date (if applicable)

## Barcode Printing

When you choose to print a barcode, the system will:

1. Generate and save a barcode image in the `barcodes/` directory
2. Display the path to the saved image
3. Provide instructions on how to print the barcode from your system

## License

This project is open source and available for modification and distribution. 