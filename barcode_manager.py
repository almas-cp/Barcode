import csv
import os
import sys
from datetime import datetime
try:
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-barcode", "Pillow"])
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image

class WarehouseManager:
    def __init__(self, csv_file='items.csv'):
        self.csv_file = csv_file
        self.items = self.load_items()

    def load_items(self):
        """Load items from the CSV file."""
        items = []
        try:
            with open(self.csv_file, 'r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    items.append(row)
            print(f"Loaded {len(items)} items from {self.csv_file}")
            return items
        except FileNotFoundError:
            print(f"Error: CSV file '{self.csv_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            sys.exit(1)

    def generate_barcode(self, item, output_dir='barcodes'):
        """Generate a barcode image for an item."""
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Generate barcode
        barcode_value = item['barcode']
        item_id = item['item_id']
        
        # Use EAN13 for 13-digit barcodes or Code128 for others
        if len(barcode_value) == 12 or len(barcode_value) == 13:
            # EAN13 requires exactly 12 digits (the 13th is calculated)
            if len(barcode_value) == 13:
                barcode_value = barcode_value[:12]
            barcode_class = barcode.get_barcode_class('ean13')
        else:
            barcode_class = barcode.get_barcode_class('code128')

        # Generate and save the barcode
        barcode_filename = f"{output_dir}/{item_id}"
        barcode_image = barcode_class(barcode_value, writer=ImageWriter())
        barcode_path = barcode_image.save(barcode_filename)
        
        return barcode_path

    def display_barcode_ascii(self, item):
        """Display a basic ASCII representation of a barcode in the terminal."""
        barcode_value = item['barcode']
        name = item['name']
        item_id = item['item_id']
        price = item['unit_price']
        category = item['category']
        quantity = item['quantity']
        
        # Print item information
        print("\n" + "=" * 60)
        print(f"ITEM: {name} ({item_id})")
        print(f"CATEGORY: {category}")
        print(f"QUANTITY: {quantity}")
        print(f"PRICE: ${price}")
        
        # Generate a simple ASCII barcode representation
        print("\nBARCODE: " + barcode_value)
        print("┌" + "─" * (len(barcode_value) + 10) + "┐")
        print("│ " + " " * 5 + barcode_value + " " * 5 + " │")
        
        # Generate the barcode pattern (simplified)
        bars = ""
        for char in barcode_value:
            # Each digit gets converted to a pattern of | and spaces
            digit = int(char)
            bar_pattern = "█" * (digit % 5 + 1) + " " * (1 + (digit % 3))
            bars += bar_pattern
        
        # Print the barcode lines
        for _ in range(6):
            print("│ " + bars + " │")
        
        print("│ " + " " * 5 + barcode_value + " " * 5 + " │")
        print("└" + "─" * (len(barcode_value) + 10) + "┘")
        print("=" * 60)

    def print_barcode(self, item):
        """Generate a barcode image and prepare it for printing."""
        # First generate the barcode image
        barcode_path = self.generate_barcode(item)
        
        print(f"\nBarcode for {item['name']} ({item['item_id']}) generated at: {barcode_path}")
        print("To print this barcode:")
        
        if sys.platform.startswith('win'):
            print(f"1. Open the image file at: {os.path.abspath(barcode_path)}")
            print("2. Right-click and select 'Print'")
            print("   OR")
            print(f"   Run this command: Start-Process -FilePath \"{os.path.abspath(barcode_path)}\" -Verb Print")
        else:
            print(f"1. Open the image file at: {os.path.abspath(barcode_path)}")
            print("2. Use your system's print dialog to print it")
            print("   OR")
            print(f"   Run this command: lpr {os.path.abspath(barcode_path)}")
        
        return barcode_path

    def display_item_details(self, item):
        """Display detailed information about an item."""
        print("\n" + "=" * 60)
        print(f"ITEM DETAILS: {item['name']}")
        print("=" * 60)
        for key, value in item.items():
            if key == 'expiry_date' and not value:
                value = 'N/A'
            print(f"{key.upper()}: {value}")
        print("=" * 60)

    def main_menu(self):
        """Display the main menu and handle user input."""
        while True:
            print("\n" + "=" * 60)
            print("WAREHOUSE BARCODE MANAGEMENT SYSTEM")
            print("=" * 60)
            print("1. List All Items")
            print("2. Search Item by ID")
            print("3. Search Item by Name")
            print("4. Generate Barcode for Item")
            print("5. Display Item Details")
            print("6. Print Barcode for Item")
            print("7. Exit")
            print("=" * 60)
            
            choice = input("Enter your choice (1-7): ")
            
            if choice == '1':
                self.list_all_items()
            elif choice == '2':
                self.search_by_id()
            elif choice == '3':
                self.search_by_name()
            elif choice == '4':
                self.barcode_generation_menu()
            elif choice == '5':
                self.item_details_menu()
            elif choice == '6':
                self.print_barcode_menu()
            elif choice == '7':
                print("\nExiting Warehouse Management System. Goodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")

    def list_all_items(self):
        """List all items in the inventory."""
        print("\n" + "=" * 80)
        print(f"{'ITEM ID':<10} {'NAME':<30} {'CATEGORY':<15} {'QUANTITY':<10} {'UNIT PRICE':<10}")
        print("=" * 80)
        
        for item in self.items:
            print(f"{item['item_id']:<10} {item['name'][:28]:<30} {item['category'][:13]:<15} {item['quantity']:<10} ${item['unit_price']:<10}")
        
        print("=" * 80)
        input("\nPress Enter to continue...")

    def search_by_id(self):
        """Search for an item by its ID."""
        item_id = input("\nEnter Item ID: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.display_item_details(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")

    def search_by_name(self):
        """Search for items by name (partial match)."""
        name = input("\nEnter Item Name (or part of it): ").strip().lower()
        
        found_items = []
        for item in self.items:
            if name in item['name'].lower():
                found_items.append(item)
        
        if found_items:
            print("\n" + "=" * 80)
            print(f"Found {len(found_items)} items matching '{name}':")
            print("=" * 80)
            print(f"{'ITEM ID':<10} {'NAME':<30} {'CATEGORY':<15} {'QUANTITY':<10}")
            print("=" * 80)
            
            for item in found_items:
                print(f"{item['item_id']:<10} {item['name'][:28]:<30} {item['category'][:13]:<15} {item['quantity']:<10}")
            
            print("=" * 80)
        else:
            print(f"\nNo items found matching '{name}'")

    def barcode_generation_menu(self):
        """Menu for generating and displaying barcodes."""
        item_id = input("\nEnter Item ID for barcode generation: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.display_barcode_ascii(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")

    def item_details_menu(self):
        """Menu for displaying item details."""
        item_id = input("\nEnter Item ID to view details: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.display_item_details(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")

    def print_barcode_menu(self):
        """Menu for printing barcodes."""
        item_id = input("\nEnter Item ID for barcode printing: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.print_barcode(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")


if __name__ == "__main__":
    print("Starting Warehouse Barcode Management System...\n")
    manager = WarehouseManager()
    manager.main_menu() 