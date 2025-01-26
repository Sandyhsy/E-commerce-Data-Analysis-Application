from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QMenu, QAction, QToolButton, QDialog, QVBoxLayout,
    QHBoxLayout, QSpinBox, QLabel, QFormLayout, QMessageBox, QWidget, QSizePolicy, QHeaderView, QFrame
)
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import uic
import mysql.connector
import sys  # For sys.exit()
from customer_order_history import OrderWindow  # Import OrderWindow
from data201 import make_connection
import os
from shared import open_login_portal
from datetime import datetime, timedelta


class CheckoutWindow(QDialog):
    def __init__(self, total_price, cart_window, main_window, customer_id):
        super().__init__()
        self.setWindowTitle("Checkout")
        self.total_price = total_price
        self.cart_window = cart_window
        self.main_window = main_window

        # Layout for form inputs
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.customer_id = customer_id

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Phone Number:", self.phone_input)

        layout.addLayout(form_layout)

        # Total price label
        self.total_label = QLabel(f"Total Price: ${total_price:.2f}")
        layout.addWidget(self.total_label)

        # Buttons
        button_layout = QHBoxLayout()
        submit_button = QPushButton("Submit")
        submit_button.clicked.connect(self.submit_details)
        button_layout.addWidget(submit_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Automatically shrink to fit content
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.adjustSize()

    def submit_details(self):
        """Validate and process user details."""
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()

        if not name or not address or not email or not phone:
            QMessageBox.warning(self, "Input Error", "All fields must be filled out.")
            return

        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Input Error", "Enter a valid email address.")
            return

        QMessageBox.information(self, "Order Submitted", f"Thank you for your order, {name}!")
        print(f"Order Details:\nName: {name}\nAddress: {address}\nEmail: {email}\nPhone: {phone}")

        self.cart_window.clear_cart()  # Clear the cart
        self.close()

        # Show the main window
        self.main_window.show()

class CartWindow(QDialog):
    def __init__(self, cart_items, customer_id, main_window):
        super().__init__()
        self.cart_items = cart_items
        self.main_window = main_window
        self.customer_id = customer_id

        # Remove default title bar
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Custom title bar
        title_bar = QFrame()
        title_bar.setStyleSheet("background-color: #FFC0CB;")  # Pink background
        title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)

        # Title text
        title_label = QLabel("Cart Items")
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        title_layout.addWidget(title_label)

        # Close button
        close_button = QPushButton("X")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #FF69B4;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 0 5px;
            }
            QPushButton:hover {
                background-color: #FF1493;
            }
        """)
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button, alignment=Qt.AlignRight)

        main_layout.addWidget(title_bar)

        # Rest of the cart window layout
        cart_layout = QVBoxLayout()
        self.setup_cart_layout(cart_layout)
        main_layout.addLayout(cart_layout)

        # Pink theme styles
        self.setStyleSheet("""
        QDialog {
            background-color: #FFE4E1; /* Light pink background */
        }
        QLabel {
            color: #FF69B4; /* Hot pink text */
            font-weight: bold;
        }
        QTableWidget {
            background-color: #FFF0F5; /* Lavender blush for table */
            color: #FF69B4; /* Hot pink text */
            border: 1px solid #FFC0CB; /* Pink border */
        }
        QTableWidget::item {
            color: #FF69B4; /* Hot pink text for items */
        }
        QHeaderView::section {
            background-color: #FFC0CB; /* Pink background for headers */
            color: white; /* White text */
            border: 1px solid #FF69B4; /* Hot pink border */
            font-weight: bold;
            padding: 5px;
            text-align: center;
        }
        QSpinBox {
            background-color: #FFC0CB; /* Pink background for spin boxes */
            border: 1px solid #FF69B4; /* Hot pink border */
            border-radius: 5px;
        }
        QPushButton {
            background-color: #FFC0CB; /* Pink button */
            color: white;
            border: 1px solid #FF69B4; /* Hot pink border */
            border-radius: 5px;
            font-weight: bold;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #FF69B4; /* Darker pink when hovered */
        }
        QPushButton:pressed {
            background-color: #FF1493; /* Even darker pink when pressed */
        }
    """)

    def setup_cart_layout(self, layout):
        """Set up the cart layout."""
        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Product ID", "Category", "Description", "Price", "Quantity", "Delete"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make cells uneditable
        layout.addWidget(self.table)

            # Hide the vertical header (row indices)
        self.table.verticalHeader().setVisible(False)

        # Populate table with cart items
        self.table.setRowCount(len(self.cart_items))
        self.spin_boxes = []
        for row_index, item in enumerate(self.cart_items):
            for col_index, value in enumerate(item[:4]):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

            spin_box = QSpinBox()
            spin_box.setMinimum(1)
            spin_box.setValue(item[4] if len(item) > 4 else 1)
            spin_box.valueChanged.connect(lambda value, r=row_index: self.update_quantity(r, value))
            self.table.setCellWidget(row_index, 4, spin_box)
            self.spin_boxes.append(spin_box)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row_index: self.delete_item(r))
            self.table.setCellWidget(row_index, 5, delete_button)

        # Total price and buttons
        button_layout = QHBoxLayout()
        self.total_label = QLabel()
        self.update_total_price()
        button_layout.addWidget(self.total_label)

        # Check Out button
        check_out_button = QPushButton("Check Out")
        check_out_button.clicked.connect(self.check_out)
        button_layout.addWidget(check_out_button)

        # # Open Bigger Window button
        # open_bigger_window_button = QPushButton("Open Bigger Window")
        # open_bigger_window_button.clicked.connect(self.open_bigger_window)
        # button_layout.addWidget(open_bigger_window_button)

        layout.addLayout(button_layout)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def update_total_price(self):
        
        """Update the total price label."""
        total_price = sum(float(item[3].replace('$', '')) * item[4] for item in self.cart_items)
        self.total_label.setText(f"Total Price: ${total_price:.2f}")
        self.total_label.setStyleSheet("font-size: 16px; color: #FF1493;")  # Dark pink text

    # def open_bigger_window(self):
    #     """Open a bigger window."""
    #     self.bigger_window = BiggerWindow(self.cart_items)
    #     self.bigger_window.show()


    def update_quantity(self, row_index, value):
        if 0 <= row_index < len(self.cart_items):
            self.cart_items[row_index] = (*self.cart_items[row_index][:4], value)
            self.update_total_price()
        else:
            print(f"Error: row_index {row_index} is out of range.")

    def delete_item(self, row_index):
        if row_index < len(self.cart_items):
            del self.cart_items[row_index]
            self.table.removeRow(row_index)
            del self.spin_boxes[row_index]
            self.update_cart_count()
            self.update_total_price()
            print(f"Deleted item at row {row_index}. Updated cart: {self.cart_items}")

    def update_cart_count(self):
        total_items = sum(item[4] for item in self.cart_items)
        self.main_window.cart_count = total_items
        self.main_window.cart_button.setText(f"Cart ({total_items})")
        print(f"Cart updated to {total_items} items.")

    def update_total_price(self):
        try:
            total_price = sum(float(item[3].replace('$', '')) * item[4] for item in self.cart_items)
            self.total_label.setText(f"Total: ${total_price:.2f}")
        except Exception as e:
            print(f"Error updating total price: {e}")

            self.total_label.setText(f"Total Price: ${total_price:.2f}")
            print(f"Updated total price: ${total_price:.2f}")

    def save_changes(self):
        for i, spin_box in enumerate(self.spin_boxes):
            quantity = spin_box.value()
            self.cart_items[i] = (*self.cart_items[i][:4], quantity)

        self.main_window.cart_items = self.cart_items
        self.update_cart_count()
        print(f"Saved updated cart items: {self.cart_items}")
        self.close()

    def get_seller_id(self, product_id):
        """
        Retrieve seller_id for a given product_id.
        Assumes that there is a table linking product_id to seller_id.
        """
        try:
            query = """
                SELECT seller_id FROM product_stock WHERE product_id = %s
            """
            self.cursor.execute(query, (product_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error retrieving seller_id for product_id {product_id}: {e}")
            return None

    def check_out(self):
        self.connection = make_connection(config_file='sqlproject.ini')
        self.cursor = self.connection.cursor()
        print(f"Customer ID passed through: {self.customer_id}")

        try:
            # Get today's date and calculate the shipping limit date
            today = datetime.now()
            shipping_date = today + timedelta(days=7)

            # Retrieve the current maximum order_id and generate a new order_id
            order_id_query = "SELECT MAX(order_id) FROM orders"
            self.cursor.execute(order_id_query)
            max_order_id = self.cursor.fetchone()[0]
            new_order_id = (max_order_id + 1) if max_order_id else 1

            # Insert the order into the orders table
            order_query = """
                INSERT INTO orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, 
                                    order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(order_query, (new_order_id, self.customer_id, 'in progress',
                                            today.strftime('%Y-%m-%d %H:%M:%S'), None, None, None, None))

            # Initialize total_price
            total_price = 0

            # Check if cart is empty
            if not self.cart_items:
                QMessageBox.warning(self, "Empty Cart", "Your cart is empty. Please add items before checking out.")
                return

            # Insert order items
            for item in self.cart_items:
                product_id, category, description, price, quantity = item

                # Calculate total price
                total_price += float(price.replace('$', '')) * quantity

                # Update stock and insert order items
                self.update_stock_quantity(product_id, self.get_stock_quantity(product_id) - quantity)

                seller_id = self.get_seller_id(product_id)
                query = """
                    INSERT INTO order_items (order_id, product_id, seller_id, shipping_limit_date, freight_value, quantity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (new_order_id, product_id, seller_id, shipping_date, 0.0, quantity))

            # Insert payment information
            payment_query = """
                INSERT INTO order_payments (order_id, payment_type, payment_installments, payment_value)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(payment_query, (new_order_id, 'credit_card', 1, total_price))

            # Commit all changes
            self.connection.commit()

            # Clear cart and notify user
            self.clear_cart()
            QMessageBox.information(self, "Order Placed", f"Order {new_order_id} placed successfully!")

            # Refresh the order history in the main window's order window
            if self.main_window.order_window and self.main_window.order_window.isVisible():
                self.main_window.order_window.populate_orders()

        except Exception as e:
            self.connection.rollback()
            print(f"Error during checkout: {e}")
            QMessageBox.critical(self, "Error", f"Failed to place order: {e}")

        finally:
            self.cursor.close()
            self.connection.close()


    def get_stock_quantity(self, product_id):
        """
        Retrieve the available stock quantity for a given product_id.
        """
        try:
            query = """
                SELECT stock FROM product_stock WHERE product_id = %s
            """
            self.cursor.execute(query, (product_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error retrieving stock quantity for product_id {product_id}: {e}")
            return None

    def update_stock_quantity(self, product_id, new_quantity):
        """
        Update the stock quantity for a given product_id after the order is placed.
        """
        try:
            query = """
                UPDATE product_stock
                SET stock = %s
                WHERE product_id = %s
            """
            self.cursor.execute(query, (new_quantity, product_id))
        except Exception as e:
            print(f"Error updating stock quantity for product_id {product_id}: {e}")
            raise

    def clear_cart(self):
        """Clear all items from the cart."""
        self.cart_items.clear()
        self.table.setRowCount(0)  # Clear the table
        self.update_cart_count()
        self.update_total_price()
        print("Cart has been cleared.")

# class BiggerWindow(QMainWindow):
#     """A bigger window for detailed cart view."""
#     def __init__(self, cart_items):
#         super().__init__()
#         self.setWindowTitle("Bigger Cart View")
#         self.resize(800, 600)  # Make the window bigger

#         # Set up layout and table
#         layout = QVBoxLayout()
#         widget = QWidget(self)
#         self.setCentralWidget(widget)
#         widget.setLayout(layout)

#         self.table = QTableWidget()
#         self.table.setColumnCount(6)
#         self.table.setHorizontalHeaderLabels(["Product ID", "Category", "Description", "Price", "Quantity", "Delete"])
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Ensure cells are not editable
#         self.populate_table(cart_items)
#         layout.addWidget(self.table)

#     def populate_table(self, cart_items):
#         """Populate the table with cart items."""
#         self.table.setRowCount(len(cart_items))
#         for row_index, item in enumerate(cart_items):
#             for col_index, value in enumerate(item[:4]):
#                 self.table.setItem(row_index, col_index, QTableWidgetItem(str(value)))

class CustomerHome(QMainWindow):
    def __init__(self, customer_id, parent = None):
        super().__init__(parent)
        uic.loadUi("customer_home.ui", self)
        
        self.customer_id = customer_id
        # Cache data
        self.cached_data = []

        # Load data into cache
        self.load_data()

        self.refresh_order_history()

        # Set default size for the main window
        self.resize(800, 600)
        self.setMinimumSize(QSize(600, 600))

        # Automatically adjust size based on content
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.adjustSize()

        # Access widgets
        self.table_view = self.findChild(QTableWidget, "tableView")
        self.sort_combo = self.findChild(QComboBox, "comboBox")
        self.category_combo = self.findChild(QComboBox, "comboBox_2")
        self.search_bar = self.findChild(QLineEdit, "lineEdit")
        self.search_button = self.findChild(QPushButton, "pushButton")
        self.cart_button = self.findChild(QPushButton, "pushButton_2")
        self.user_button = self.findChild(QToolButton, "toolButton")  # Access the "User" button
        # Access the QLabel for the logo
        self.logo_label = self.findChild(QLabel, "logo_label")  # Replace 'logo_label' with your QLabel's object name
        # Set the logo image
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "picture", "logo.png")
        self.set_logo(logo_path) 
        
        self.toolButton.setPopupMode(QToolButton.DelayedPopup)  # Disable dropdown behavior
        self.toolButton.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # Remove the dropdown arrow

        if not self.user_button:
            raise RuntimeError("The User button (toolButton) was not found in the UI file.")

        self.cart_items = []  # Initialize cart items
        self.cart_count = 0  # Initialize cart count

        # Populate sorting options
        self.sort_combo.addItems(["Price: High to Low", "Price: Low to High"])
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)

        # Populate categories
        self.populate_categories()
        self.category_combo.currentIndexChanged.connect(self.apply_filters)

        # Set up search functionality
        self.search_bar.textChanged.connect(self.apply_filters)  # Dynamically filter as you type

        # Set up user menu
        self.setup_user_menu()

            # Set up the table
        self.setup_table()  # Automatically adjust columns based on content and prevent resizing

        # Set up cart button functionality
        self.cart_button.clicked.connect(self.open_cart_window)

        # Populate the table
        self.populate_table_view(order_by="DESC")  # Default sorting: High to Low
        self.cart_window = None  # Track the cart window
        self.order_window = None  # Track the order window


    def load_data(self):
        """Load data from the database into a local cache."""
        try:
            conn = make_connection(config_file = 'sqlproject.ini')
            cursor = conn.cursor()  

            query = """
                SELECT product_id, product_category, product_description, CONCAT('$', FORMAT(product_price, 2)) AS product_price
                FROM products
            """
            cursor.execute(query)
            self.cached_data = cursor.fetchall()

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            print(f"Database error: {err}")

    def refresh_order_history(self):
        """Refresh the order history in the order window."""
        if hasattr(self, 'order_window') and self.order_window.isVisible():
            self.order_window.populate_orders()
    
    def open_order_history(self):
        try:
            if not hasattr(self, 'order_window') or not self.order_window.isVisible():
                self.order_window = OrderWindow(customer_id=self.customer_id, main_window=self)
            self.order_window.show()
            self.hide()
        except Exception as e:
            print(f"Error opening Order History: {e}")


    
    def setup_table(self):
        """Setup table headers and adjust column sizes."""
        # Disable user resizing of columns
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)  # Fix column size explicitly
        header.setStretchLastSection(False)  # Prevent last column from stretching
            # Hide the vertical header (row indices)
        self.table_view.verticalHeader().setVisible(False)

        # Disable user adjustments for column resizing
        header.setSectionsClickable(False)

        # Set column headers
        self.table_view.setColumnCount(5)
        self.table_view.setHorizontalHeaderLabels(["Product ID", "Category", "Description", "Price", "Add to Cart"])

        # Explicitly set the width of each column
        self.table_view.setColumnWidth(0, 100)  # Product ID
        self.table_view.setColumnWidth(1, 150)  # Category
        self.table_view.setColumnWidth(2, 250)  # Description
        self.table_view.setColumnWidth(3, 100)  # Price
        self.table_view.setColumnWidth(4, 120)  # Add to Cart

    def setup_user_menu(self):
        user_menu = QMenu(self)

        # Create actions
        order_history_action = QAction("Order History", self)
        logout_action = QAction("Log Out", self)

        # Connect actions to methods
        order_history_action.triggered.connect(self.open_order_history)
        logout_action.triggered.connect(self.logout)

        # Add actions to the menu
        user_menu.addAction(order_history_action)
        user_menu.addAction(logout_action)

        # Attach menu to the button and set popup mode
        self.user_button.setMenu(user_menu)
        self.user_button.setPopupMode(QToolButton.InstantPopup)

    def open_order_history(self):
        try:
            self.order_window = OrderWindow(customer_id=self.customer_id, main_window=self)
            self.order_window.show()
            self.hide()
        except Exception as e:
            print(f"Error opening Order History: {e}")

    def logout(self):
        # QApplication.instance().quit()
        open_login_portal(self)

    def populate_categories(self):
        try:
            conn = make_connection(config_file = 'sqlproject.ini')
            cursor = conn.cursor()  

            query = "SELECT DISTINCT product_category FROM products"
            cursor.execute(query)
            categories = cursor.fetchall()

            cursor.close()
            conn.close()

            self.category_combo.addItem("All Categories")
            for category in categories:
                self.category_combo.addItem(category[0])

        except mysql.connector.Error as err:
            print(f"Database error: {err}")

    def populate_table_view(self, order_by="DESC", category=None, search_query=None):
        """Populate the table view using cached data."""
        results = self.cached_data

        # Apply category filter
        if category and category != "All Categories":
            results = [row for row in results if row[1] == category]

        # Apply search query filter
        if search_query:
            search_query = search_query.lower()
            results = [
                row for row in results if
                search_query in str(row[0]).lower() or
                search_query in str(row[1]).lower() or
                search_query in str(row[2]).lower() or
                search_query in str(row[3]).lower()
            ]

        # Sort results
        reverse = order_by == "DESC"
        results.sort(key=lambda x: x[3], reverse=reverse)  # Sort by price

        # Populate the table
        self.table_view.setRowCount(0)
        for row_index, row_data in enumerate(results):
            self.table_view.insertRow(row_index)
            for col_index, value in enumerate(row_data):
                self.table_view.setItem(row_index, col_index, QTableWidgetItem(str(value)))

            add_to_cart_button = QPushButton("+")
            add_to_cart_button.setFixedSize(30, 30)  # Adjust button size
            add_to_cart_button.setToolTip("Add to Cart")  # Tooltip for clarity
            add_to_cart_button.clicked.connect(lambda _, r=row_data: self.add_to_cart(r))
            self.table_view.setCellWidget(row_index, 4, add_to_cart_button)  # Place in the 5th column

    def apply_filters(self):
        """Apply the selected filters and update the table view."""
        selected_sort = self.sort_combo.currentText()
        order_by = "DESC" if "High to Low" in selected_sort else "ASC"

        selected_category = self.category_combo.currentText()
        search_query = self.search_bar.text()

        self.populate_table_view(order_by=order_by, category=selected_category, search_query=search_query)

    def add_to_cart(self, row_data):
        for i, item in enumerate(self.cart_items):
            if item[:4] == row_data:
                self.cart_items[i] = (*item[:4], item[4] + 1)
                print(f"Updated quantity for item: {self.cart_items[i]}")
                break
        else:
            self.cart_items.append((*row_data, 1))
            print(f"Added new item to cart: {row_data}")

        self.cart_count = sum(item[4] for item in self.cart_items)
        self.cart_button.setText(f"({self.cart_count})")
        print(f"Current cart items: {self.cart_items}")
    

    def closeEvent(self, event):
        """Override the close event to close child windows."""
        if self.cart_window and self.cart_window.isVisible():
            self.cart_window.close()
        if self.order_window and self.order_window.isVisible():
            self.order_window.close()
        print("Main window and all child windows closed.")
        event.accept()


    def open_cart_window(self):
        self.cart_window = CartWindow(self.cart_items, self.customer_id, self)
        self.cart_window.show()
    
    def setup_cart_table(self):
        for row_index, item in enumerate(self.cart_items):
            spin_box = QSpinBox()
            spin_box.setValue(item[4])  # 初始化數量
            spin_box.valueChanged.connect(lambda value, r=row_index: self.update_quantity(r, value))
            self.cart_table.setCellWidget(row_index, 4, spin_box) 
 
    def set_logo(self, logo_path):
        """Set the application logo."""
        pixmap = QPixmap(logo_path)  # Load the logo image
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap)  # Set the pixmap on the QLabel
            self.logo_label.setScaledContents(True)  # Ensure the image scales with the QLabel
        else:
            print(f"Error: Logo not found at {logo_path}")



if __name__ == "__main__":
    customer_id = 1
    app = QApplication(sys.argv)
    main_window = CustomerHome(customer_id) # Pass customer_id to CustomerHome
    main_window.show()
    sys.exit(app.exec_())
