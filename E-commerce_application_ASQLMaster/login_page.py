import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog
import mysql.connector
from customer_home import CustomerHome 
from seller_portal import SellerPortal  
from manager_portal import ManagerPortal
from shared import open_signup_portal  # Use shared function to open the SignUpPortal
from data201 import make_connection
import os


class LoginPage(QDialog):
    def __init__(self):
        super().__init__()

        self.setObjectName("LoginPage")
        self.resize(422, 348)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.setFont(font)
        self.setWindowTitle("Login Portal")

        # Layouts
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.horizontalLayoutLogo = QtWidgets.QHBoxLayout()
        self.formLayout = QtWidgets.QFormLayout()
        self.horizontalLayoutButtons = QtWidgets.QHBoxLayout()
        self.horizontalLayoutBottom = QtWidgets.QHBoxLayout()

        # Logo
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "picture", "logo.png")
        
        self.horizontalSpacerLeftLogo = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutLogo.addItem(self.horizontalSpacerLeftLogo)
        self.label_logo = QtWidgets.QLabel(self)
        self.label_logo.setPixmap(QtGui.QPixmap(logo_path))
        self.label_logo.setScaledContents(True)
        self.label_logo.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayoutLogo.addWidget(self.label_logo)
        self.label_logo.setMinimumSize(132, 132)  # Minimum width and height
        self.label_logo.setMaximumSize(132, 132)  # Maximum height to avoid excessive resizing`


        self.horizontalSpacerRightLogo = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayoutLogo.addItem(self.horizontalSpacerRightLogo)
        self.verticalLayout.addLayout(self.horizontalLayoutLogo)

        # Title
        self.label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setText("Login Portal")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label)

        # Form Fields
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setText("Username:")
        self.lineEdit_username = QtWidgets.QLineEdit(self)
        self.formLayout.addRow(self.label_2, self.lineEdit_username)

        self.label_3 = QtWidgets.QLabel(self)
        self.label_3.setText("Password:")
        self.lineEdit_password = QtWidgets.QLineEdit(self)
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.horizontalLayoutPassword = QtWidgets.QHBoxLayout()
        self.horizontalLayoutPassword.addWidget(self.lineEdit_password)

        self.pushButton_eye = QtWidgets.QPushButton(self)
        self.pushButton_eye.setText("👀")
        self.horizontalLayoutPassword.addWidget(self.pushButton_eye)
        self.formLayout.addRow(self.label_3, self.horizontalLayoutPassword)
        self.verticalLayout.addLayout(self.formLayout)
        self.pushButton_eye.setStyleSheet("border: none; background-color: transparent; font-size: 18px;")
        

        # Login Button
        self.pushButton_login = QtWidgets.QPushButton(self)
        self.pushButton_login.setText("Login")
        self.horizontalLayoutButtons.addWidget(self.pushButton_login)
        self.verticalLayout.addLayout(self.horizontalLayoutButtons)
        self.pushButton_login.setStyleSheet(self._button_style())

        # Bottom Buttons
        self.pushButton_signup = QtWidgets.QPushButton(self)
        self.pushButton_signup.setText("Sign Up")
        self.horizontalLayoutBottom.addWidget(self.pushButton_signup)
        self.verticalLayout.addLayout(self.horizontalLayoutBottom)
        self.pushButton_signup.setStyleSheet(self._button_style())

        # Apply styles programmatically
        self.setStyleSheet("background-color: #F8E7E7;")
        self.lineEdit_username.setStyleSheet("background-color: #FFD6D6; border: 1px solid #FFAAAA; border-radius: 5px;")
        self.lineEdit_password.setStyleSheet("background-color: #FFD6D6; border: 1px solid #FFAAAA; border-radius: 5px;")

        # Connect Buttons
        self.pushButton_login.clicked.connect(self.login)
        self.pushButton_signup.clicked.connect(lambda: open_signup_portal(self))  # Use shared function
        self.pushButton_eye.clicked.connect(self.toggle_password_visibility)

        # Initialize Toggle State
        self.password_visible = False

                # Add validation for UI elements
        if not hasattr(self, 'lineEdit_username') or not hasattr(self, 'pushButton_login'):
            print("Error: UI elements not initialized")
            QMessageBox.critical(self, "Error", "Critical UI components are missing!")
            return

    def _button_style(self):
        """Return the stylesheet for buttons."""
        return "background-color: #FFAAAA; border: 1px solid #D66A6A; border-radius: 5px; padding: 10px 20px; font-size: 16px;"

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_visible:
            self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Password)
            self.pushButton_eye.setText("👀")
        else:
            self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.pushButton_eye.setText("🙈")
        self.password_visible = not self.password_visible

    def login(self):
        """Handle login."""
        username = self.lineEdit_username.text().strip()
        password = self.lineEdit_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        try:
            conn = make_connection(config_file='sqlproject.ini')
            cursor = conn.cursor()

            # Query to check user credentials and retrieve role and customer_id
            query = "SELECT portal, user_name FROM user_portal WHERE user_name = %s AND password = %s"
            cursor.execute(query, (username, password))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:
                portal, customer_id = user
                username_display = username.split('@')[0]
                QMessageBox.information(self, "Login Successful", f"Welcome {portal} {username_display}!")
                self.open_main_window(portal, customer_id)
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Database Error", f"Failed to connect to the database: {err}")
    
    
    def open_main_window(self, portal, username):
        try:
            # Establish the database connection
            self.connection = make_connection(config_file='sqlproject.ini')
            self.cursor = self.connection.cursor()

            if portal == "customer":
                # Query to get the customer_id based on the username (email)
                query = "SELECT customer_id FROM customers WHERE customer_email = %s"
                self.cursor.execute(query, (username,))
                result = self.cursor.fetchone()

                if result:
                    customer_id = result[0]
                    self.customer_home = CustomerHome(customer_id=customer_id)
                    self.customer_home.show()
                else:
                    # If no matching customer is found
                    QMessageBox.warning(self, "Login Error", "Customer not found. Please contact support.")
                    return

            elif portal == "seller":
                self.seller_portal = SellerPortal()
                self.seller_portal.show()

            elif portal == "manager":
                self.manager_portal = ManagerPortal()
                self.manager_portal.show_dialog()

            else:
                QMessageBox.warning(self, "Login Error", "Unknown role. Please contact support.")

            self.close()

        except Exception as e:
            # Handle database connection or query errors
            print(f"Error during query: {e}")
            QMessageBox.warning(self, "Database Error", "An error occurred while fetching data. Please try again later.")
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_portal = LoginPage()
    login_portal.show()
    sys.exit(app.exec_())