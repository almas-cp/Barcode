import csv
import os
import sys
import subprocess
from datetime import datetime
try:
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image, ImageDraw, ImageFont
    import qrcode
    # Try to import tkinter for GUI display
    try:
        import tkinter as tk
        from tkinter import Label, Button
        from PIL import ImageTk
        HAS_TKINTER = True
    except ImportError:
        HAS_TKINTER = False
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-barcode", "Pillow", "qrcode"])
    import barcode
    from barcode.writer import ImageWriter
    from PIL import Image, ImageDraw, ImageFont
    import qrcode
    # Try to import tkinter after installation
    try:
        import tkinter as tk
        from tkinter import Label, Button
        from PIL import ImageTk
        HAS_TKINTER = True
    except ImportError:
        HAS_TKINTER = False

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

    def generate_label(self, item, output_dir='labels'):
        """Generate a professional barcode label with layout similar to a sticker."""
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Extract item details
        item_id = item['item_id']
        name = item['name']
        category = item['category']
        price = item['unit_price']
        barcode_value = item['barcode']
        
        # Create a blank label (white background)
        label_width = 400
        label_height = 250
        label = Image.new('RGB', (label_width, label_height), color='white')
        
        # Create a drawing context
        draw = ImageDraw.Draw(label)
        
        # Try to load fonts, use default if not available
        try:
            # For Windows
            title_font = ImageFont.truetype("arial.ttf", 16)
            text_font = ImageFont.truetype("arial.ttf", 12)
        except IOError:
            try:
                # For Linux/Mac
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except IOError:
                # Default to loading a PIL font if TrueType fonts are not available
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
        
        # Draw border
        draw.rectangle([(0, 0), (label_width-1, label_height-1)], outline='black', width=2)
        
        # Draw divider lines
        draw.line([(0, 50), (label_width, 50)], fill='black', width=1)  # Horizontal top
        draw.line([(label_width//2, 0), (label_width//2, 50)], fill='black', width=1)  # Vertical top
        draw.line([(0, label_height-50), (label_width, label_height-50)], fill='black', width=1)  # Horizontal bottom
        draw.line([(label_width//2, label_height-50), (label_width//2, label_height)], fill='black', width=1)  # Vertical bottom
        
        # Draw text
        # Top left: Item ID
        draw.text((10, 15), f"Item ID: {item_id}", fill='black', font=title_font)
        # Top right: Category
        draw.text((label_width//2 + 10, 15), f"Category: {category}", fill='black', font=title_font)
        # Bottom left: Item name
        # Truncate name if too long
        name_display = name if len(name) < 25 else name[:22] + "..."
        draw.text((10, label_height-35), f"{name_display}", fill='black', font=title_font)
        # Bottom right: Price
        draw.text((label_width//2 + 10, label_height-35), f"Price: ${price}", fill='black', font=title_font)
        
        # Generate the barcode for embedding
        barcode_file = self.generate_barcode(item)
        barcode_img = Image.open(barcode_file)
        
        # Resize barcode to fit in the label
        barcode_width = label_width - 60
        barcode_height = label_height - 120
        barcode_img = barcode_img.resize((barcode_width, barcode_height))
        
        # Calculate position to center the barcode
        barcode_pos_x = (label_width - barcode_width) // 2
        barcode_pos_y = 60
        
        # Paste the barcode onto the label
        label.paste(barcode_img, (barcode_pos_x, barcode_pos_y))
        
        # Save the complete label with the specified filename format
        # Clean the name to make it file-system friendly (remove characters that might cause issues)
        safe_name = "".join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in name)
        # Limit the name length for the filename
        short_name = safe_name[:20] if len(safe_name) > 20 else safe_name
        # Create filename in format: label_itemid_name_barcode.png
        label_path = f"{output_dir}/label_{item_id}_{short_name}_{barcode_value}.png"
        label.save(label_path)
        
        return label_path
        
    def bulk_generate_labels(self, category_filter=None):
        """Generate barcode labels for multiple items at once."""
        print("\n" + "=" * 60)
        print("BULK LABEL GENERATION")
        print("=" * 60)
        
        if category_filter:
            items_to_process = [item for item in self.items if item['category'].lower() == category_filter.lower()]
            filter_message = f" in category '{category_filter}'"
        else:
            items_to_process = self.items
            filter_message = ""
            
        total_items = len(items_to_process)
        
        if total_items == 0:
            print(f"No items found{filter_message}.")
            return
            
        print(f"Generating labels for {total_items} items{filter_message}...")
        
        # Create output directory
        output_dir = "labels"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Generate labels
        generated_paths = []
        for i, item in enumerate(items_to_process, 1):
            print(f"Processing item {i}/{total_items}: {item['name']} ({item['item_id']})")
            try:
                label_path = self.generate_label(item)
                generated_paths.append(label_path)
                print(f"  ✓ Label created: {os.path.basename(label_path)}")
            except Exception as e:
                print(f"  ✗ Error generating label: {e}")
                
        print("\n" + "=" * 60)
        print(f"Label generation complete: {len(generated_paths)}/{total_items} labels created.")
        print(f"Labels saved in: {os.path.abspath(output_dir)}")
        print("=" * 60)
        
        return generated_paths

    def generate_qr_code(self, item, output_dir='barcodes'):
        """Generate a QR code for an item that contains all its data."""
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Create a data string with all item info
        data = f"ID:{item['item_id']}\nName:{item['name']}\nCategory:{item['category']}\n"
        data += f"Quantity:{item['quantity']}\nPrice:{item['unit_price']}\nBarcode:{item['barcode']}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the image
        qr_path = f"{output_dir}/QR_{item['item_id']}.png"
        img.save(qr_path)
        
        return qr_path

    def display_barcode_ascii(self, item):
        """Display a more realistic ASCII representation of a barcode in the terminal."""
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
        
        # Generate the barcode image for actual scanning
        barcode_path = self.generate_barcode(item)
        
        # Create a better visual representation for terminal display
        width = 50  # Total width of the barcode
        height = 15  # Height of the barcode
        
        # Generate a more standardized barcode pattern
        # Create start/stop patterns and data bars
        pattern = []
        
        # Create a deterministic pattern based on the barcode value
        # Using a simple hash function to create consistent patterns
        hash_value = sum(ord(c) for c in barcode_value)
        
        # Start pattern (always present in real barcodes)
        pattern.append("█ █")
        
        # Generate data bars
        for char in barcode_value:
            digit = int(char) if char.isdigit() else ord(char) % 10
            # Use the digit and hash to create a unique but consistent pattern
            bar_width = 1 + ((digit + hash_value) % 3)
            space_width = 1 + (digit % 2)
            pattern.append("█" * bar_width + " " * space_width)
        
        # End pattern (always present in real barcodes)
        pattern.append("█ █")
        
        # Combine all patterns
        bar_pattern = "".join(pattern)
        
        # Pad to desired width
        padding = (width - len(bar_pattern)) // 2
        padded_pattern = " " * padding + bar_pattern + " " * padding
        
        # Display the barcode
        print("\nBARCODE: " + barcode_value)
        print("┌" + "─" * width + "┐")
        
        # Print barcode value at the top
        value_line = "│" + " " * ((width - len(barcode_value)) // 2) + barcode_value
        value_line += " " * (width - len(value_line) + 1) + "│"
        print(value_line)
        
        # Print the barcode pattern
        for _ in range(height):
            print("│" + padded_pattern + "│")
        
        # Print barcode value at the bottom
        print(value_line)
        print("└" + "─" * width + "┘")
        print("=" * 60)
        
        # Notify user about the actual scannable barcode
        print("\nWANT A SCANNABLE BARCODE? Choose an option:")
        print("1. Open barcode image - Option 7 from main menu")
        print("2. Show GUI barcode - Option 9 from main menu")
        print("3. Display QR code - Option 10 from main menu (works in most terminals)")
        print(f"\nImage saved at: {os.path.abspath(barcode_path)}")

    def display_qr_code_terminal(self, item):
        """Generate and display a scannable QR code in the terminal."""
        # First generate the QR code image
        qr_path = self.generate_qr_code(item)
        
        print(f"\nDisplaying QR code for {item['name']} ({item['item_id']})")
        print("This QR code should be scannable directly from most terminals.")
        print("Use your phone's camera or QR scanner app to scan it.\n")
        
        try:
            # Open the QR code image
            img = Image.open(qr_path)
            # Resize for better terminal display
            img = img.resize((40, 40))
            
            # Convert to ASCII
            width, height = img.size
            aspect_ratio = height/width
            new_width = 80
            new_height = int(aspect_ratio * new_width * 0.55)
            img = img.resize((new_width, new_height))
            
            # Convert to grayscale
            img = img.convert('L')
            
            pixels = list(img.getdata())
            chars = ["  ", "██"]
            
            # Print the QR code
            for i in range(0, len(pixels), new_width):
                print("".join([chars[pixels[i+j]//128] for j in range(new_width)]))
                
            print(f"\nIf the terminal QR code doesn't scan, use the image at: {os.path.abspath(qr_path)}")
            return qr_path
            
        except Exception as e:
            print(f"Error displaying QR code: {e}")
            print(f"You can find the QR code image at: {os.path.abspath(qr_path)}")
            return qr_path

    def display_gui_barcode(self, item):
        """Display the barcode in a GUI window for scanning."""
        if not HAS_TKINTER:
            print("\nTkinter is not available on your system. Cannot display GUI.")
            print("Using alternative method to show the barcode image...")
            return self.show_barcode_image(item)
            
        # Generate barcode image
        barcode_path = self.generate_barcode(item)
        
        # Create GUI window
        root = tk.Tk()
        root.title(f"Scannable Barcode: {item['name']} ({item['item_id']})")
        
        # Set window size
        root.geometry("800x400")
        
        # Add instructions
        Label(root, text=f"Barcode for: {item['name']} ({item['item_id']})", 
              font=("Arial", 16)).pack(pady=10)
        Label(root, text="Point your barcode scanner at the screen to scan", 
              font=("Arial", 12)).pack(pady=5)
        
        # Load and display the barcode image
        try:
            img = Image.open(barcode_path)
            # Resize for better display while maintaining ratio
            basewidth = 600
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img = img.resize((basewidth, hsize), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            Label(root, image=photo).pack(pady=20)
            
            # Add close button
            Button(root, text="Close", command=root.destroy, 
                   font=("Arial", 12)).pack(pady=10)
            
            print(f"\nDisplaying barcode in GUI window - this should be scannable.")
            print("Position your scanner toward your screen to scan it.")
            
            # Start the GUI event loop
            root.mainloop()
            return barcode_path
            
        except Exception as e:
            print(f"Error displaying GUI barcode: {e}")
            print(f"You can find the barcode image at: {os.path.abspath(barcode_path)}")
            return barcode_path

    def print_barcode(self, item):
        """Generate a barcode image and prepare it for printing."""
        # First generate the barcode image
        barcode_path = self.generate_barcode(item)
        
        print(f"\nBarcode for {item['name']} ({item['item_id']}) generated at: {os.path.abspath(barcode_path)}")
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
            print("4. Display Item Details")
            print("5. Generate Barcode Label Sticker")
            print("6. Bulk Generate Barcode Labels")
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
                self.item_details_menu()
            elif choice == '5':
                self.label_generation_menu()
            elif choice == '6':
                self.bulk_label_generation_menu()
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

    def show_barcode_image(self, item):
        """Generate a barcode image and open it in the default image viewer."""
        # First generate the barcode image
        barcode_path = self.generate_barcode(item)
        
        print(f"\nOpening barcode image for {item['name']} ({item['item_id']})...")
        
        # Open the image with the default viewer based on the platform
        try:
            if sys.platform.startswith('win'):
                os.startfile(barcode_path)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', barcode_path], check=True)
            else:  # Linux and other platforms
                subprocess.run(['xdg-open', barcode_path], check=True)
            print(f"Barcode image opened in your default viewer.")
        except Exception as e:
            print(f"Could not open the image automatically: {e}")
            print(f"Please open manually at: {os.path.abspath(barcode_path)}")
        
        return barcode_path

    def show_barcode_image_menu(self):
        """Menu for showing barcode images."""
        item_id = input("\nEnter Item ID to view barcode image: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.show_barcode_image(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")

    def gui_barcode_menu(self):
        """Menu for displaying GUI barcodes."""
        item_id = input("\nEnter Item ID to display GUI barcode: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.display_gui_barcode(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")
        
    def qr_code_menu(self):
        """Menu for displaying QR codes."""
        item_id = input("\nEnter Item ID to display QR code: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                self.display_qr_code_terminal(item)
                return
        
        print(f"\nNo item found with ID: {item_id}")

    def label_generation_menu(self):
        """Menu for generating label stickers."""
        item_id = input("\nEnter Item ID to generate label sticker: ").strip().upper()
        
        for item in self.items:
            if item['item_id'] == item_id:
                label_path = self.generate_label(item)
                print(f"\nLabel sticker generated for {item['name']} ({item['item_id']})")
                print(f"Label saved at: {os.path.abspath(label_path)}")
                
                # Ask if user wants to view the label
                view_label = input("\nDo you want to view the label? (y/n): ").strip().lower()
                if view_label == 'y':
                    try:
                        if sys.platform.startswith('win'):
                            os.startfile(label_path)
                        elif sys.platform.startswith('darwin'):  # macOS
                            subprocess.run(['open', label_path], check=True)
                        else:  # Linux and other platforms
                            subprocess.run(['xdg-open', label_path], check=True)
                    except Exception as e:
                        print(f"Could not open the label: {e}")
                        print(f"Please open manually at: {os.path.abspath(label_path)}")
                return
        
        print(f"\nNo item found with ID: {item_id}")
        
    def bulk_label_generation_menu(self):
        """Menu for bulk generating label stickers."""
        print("\n" + "=" * 60)
        print("BULK LABEL GENERATION")
        print("=" * 60)
        print("1. Generate labels for ALL items")
        print("2. Generate labels for a specific category")
        print("3. Return to main menu")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            self.bulk_generate_labels()
        elif choice == '2':
            # Get list of available categories
            categories = sorted(set(item['category'] for item in self.items))
            
            print("\nAvailable categories:")
            for i, category in enumerate(categories, 1):
                print(f"{i}. {category}")
                
            cat_choice = input("\nEnter category number: ").strip()
            try:
                cat_index = int(cat_choice) - 1
                if 0 <= cat_index < len(categories):
                    self.bulk_generate_labels(categories[cat_index])
                else:
                    print("Invalid category number.")
            except ValueError:
                print("Please enter a valid number.")
        elif choice == '3':
            return
        else:
            print("Invalid choice. Returning to main menu.")


if __name__ == "__main__":
    print("Starting Warehouse Barcode Management System...\n")
    manager = WarehouseManager()
    manager.main_menu() 