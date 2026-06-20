import datetime
import uuid
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable, Any, Union


class Transaction:
    """Represents a single transaction in the banking system."""

    def __init__(self, transaction_type: str, amount: float, description: str = "", timestamp: datetime.datetime = None):
        """
        Initialize a new transaction.

        Args:
            transaction_type: Type of transaction ('deposit', 'withdrawal', 'transfer', 'interest')
            amount: Amount of money involved in the transaction
            description: Additional details about the transaction
            timestamp: When the transaction occurred (defaults to current time)
        """
        self.transaction_id = str(uuid.uuid4())
        self.transaction_type = transaction_type
        self.amount = amount
        self.description = description
        self.timestamp = timestamp if timestamp else datetime.datetime.now()

    def __str__(self) -> str:
        """Return a string representation of the transaction."""
        formatted_time = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        transaction_info = f"{self.transaction_type.capitalize()}: £{self.amount:.2f}"
        if self.description:
            transaction_info += f" | {self.description}"
        return f"{formatted_time} | {transaction_info}"


class InsufficientFundsError(Exception):
    """Exception raised when a withdrawal exceeds the available balance."""
    pass


class InvalidAmountError(Exception):
    """Exception raised when an amount is negative or zero."""
    pass


class MonthlyWithdrawalLimitError(Exception):
    """Exception raised when monthly withdrawal limit is exceeded."""
    pass


class Account(ABC):
    """Abstract base class for all account types."""

    def __init__(self, name: str, initial_balance: float = 0.0):
        """
        Initialize a new account.

        Args:
            name: Account holder's name
            initial_balance: Starting balance (default 0.0)

        Raises:
            InvalidAmountError: If initial balance is negative
        """
        if initial_balance < 0:
            raise InvalidAmountError("Initial balance cannot be negative")

        self._account_number = str(uuid.uuid4())[:8]  # First 8 chars of UUID
        self._name = name
        self._balance = initial_balance
        self._transactions: List[Transaction] = []
        self._created_date = datetime.datetime.now()

        # Record initial deposit if any
        if initial_balance > 0:
            self._transactions.append(Transaction("deposit", initial_balance, "Initial deposit"))

    @property
    def account_number(self) -> str:
        """Get the account number."""
        return self._account_number

    @property
    def name(self) -> str:
        """Get the account holder's name."""
        return self._name

    @property
    def balance(self) -> float:
        """Get the current account balance."""
        return self._balance

    @property
    def created_date(self) -> datetime.datetime:
        """Get the account creation date."""
        return self._created_date

    def deposit(self, amount: float, description: str = "") -> None:
        """
        Deposit money into the account.

        Args:
            amount: Amount to deposit
            description: Optional description of the deposit

        Raises:
            InvalidAmountError: If amount is negative or zero
        """
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive")

        self._balance += amount
        self._transactions.append(Transaction("deposit", amount, description))
        print(f"Deposited £{amount:.2f} successfully")

    def withdraw(self, amount: float, description: str = "") -> None:
        """
        Withdraw money from the account.

        Args:
            amount: Amount to withdraw
            description: Optional description of the withdrawal

        Raises:
            InvalidAmountError: If amount is negative or zero
            InsufficientFundsError: If withdrawal would result in negative balance
        """
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive")

        if amount > self._balance:
            raise InsufficientFundsError(f"Insufficient funds. Current balance: £{self._balance:.2f}")

        self._balance -= amount
        self._transactions.append(Transaction("withdrawal", amount, description))
        print(f"Withdrew £{amount:.2f} successfully")

    def add_transaction_record(self, transaction_type: str, amount: float, description: str = "") -> None:
        """
        Add a transaction record without affecting balance (for transfers).

        Args:
            transaction_type: Type of transaction
            amount: Amount involved
            description: Description of the transaction
        """
        self._transactions.append(Transaction(transaction_type, amount, description))

    def get_transaction_history(self) -> List[Transaction]:
        """Get a list of all transactions for this account."""
        return self._transactions.copy()

    def display_transaction_history(self) -> None:
        """Display all transactions in a formatted manner."""
        if not self._transactions:
            print("No transactions to display")
            return

        print("\n===== Transaction History =====")
        print("Date & Time           | Transaction")
        print("------------------------|-----------------")
        for transaction in self._transactions:
            print(transaction)
        print("===============================\n")

    def get_account_summary(self) -> str:
        """Get a detailed summary of the account."""
        summary = [
            f"Account Type: {self.get_account_type()}",
            f"Account Number: {self._account_number}",
            f"Account Holder: {self._name}",
            f"Current Balance: £{self._balance:.2f}",
            f"Created On: {self._created_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Number of Transactions: {len(self._transactions)}"
        ]
        return "\n".join(summary)

    def __str__(self) -> str:
        """Return a string representation of the account."""
        return f"Account {self._account_number} | {self._name} | Balance: £{self._balance:.2f}"

    @abstractmethod
    def get_account_type(self) -> str:
        """Return the type of account."""
        pass


class CheckingAccount(Account):
    """A checking account with no interest but unlimited transactions."""

    def __init__(self, name: str, initial_balance: float = 0.0):
        """Initialize a new checking account."""
        super().__init__(name, initial_balance)

    def get_account_type(self) -> str:
        """Return the type of account."""
        return "Checking"


class SavingsAccount(Account):
    """A savings account with interest and withdrawal limits."""

    def __init__(self, name: str, initial_balance: float = 0.0, interest_rate: float = 0.01):
        """
        Initialize a new savings account.

        Args:
            name: Account holder's name
            initial_balance: Starting balance
            interest_rate: Annual interest rate (default 1%)
        """
        super().__init__(name, initial_balance)
        self._interest_rate = interest_rate
        self._withdrawal_limit = 3  # Monthly limit
        self._withdrawals_this_month = 0
        self._last_withdrawal_month = datetime.datetime.now().month if initial_balance > 0 else None

    def get_account_type(self) -> str:
        """Return the type of account."""
        return "Savings"

    @property
    def interest_rate(self) -> float:
        """Get the current interest rate."""
        return self._interest_rate

    @property
    def withdrawal_limit(self) -> int:
        """Get the monthly withdrawal limit."""
        return self._withdrawal_limit

    @property
    def withdrawals_remaining(self) -> int:
        """Get the number of withdrawals remaining this month."""
        # Reset if it's a new month
        current_month = datetime.datetime.now().month
        if self._last_withdrawal_month != current_month:
            self._withdrawals_this_month = 0
            self._last_withdrawal_month = current_month

        return self._withdrawal_limit - self._withdrawals_this_month

    def apply_interest(self) -> float:
        """
        Apply monthly interest to the account.

        Returns:
            The amount of interest applied
        """
        interest_amount = self._balance * (self._interest_rate / 12)  # Monthly interest
        if interest_amount > 0:
            self._balance += interest_amount
            self._transactions.append(Transaction("interest", interest_amount, "Monthly interest"))
            print(f"Applied monthly interest: £{interest_amount:.2f}")
        return interest_amount

    def withdraw(self, amount: float, description: str = "") -> None:
        """
        Withdraw money from the account with monthly limits.

        Args:
            amount: Amount to withdraw
            description: Optional description of the withdrawal

        Raises:
            InvalidAmountError: If amount is negative or zero
            InsufficientFundsError: If withdrawal would result in negative balance
            MonthlyWithdrawalLimitError: If monthly withdrawal limit is reached
        """
        current_month = datetime.datetime.now().month

        # Reset withdrawal count if it's a new month
        if self._last_withdrawal_month != current_month:
            self._withdrawals_this_month = 0
            self._last_withdrawal_month = current_month

        # Check withdrawal limit
        if self._withdrawals_this_month >= self._withdrawal_limit:
            raise MonthlyWithdrawalLimitError(f"Monthly withdrawal limit ({self._withdrawal_limit}) reached")

        # Proceed with withdrawal
        super().withdraw(amount, description)
        self._withdrawals_this_month += 1

    def get_account_summary(self) -> str:
        """Get a detailed summary of the savings account."""
        basic_summary = super().get_account_summary()
        savings_details = [
            f"Interest Rate: {self._interest_rate:.2%}",
            f"Monthly Withdrawal Limit: {self._withdrawal_limit}",
            f"Withdrawals Remaining This Month: {self.withdrawals_remaining}"
        ]
        return basic_summary + "\n" + "\n".join(savings_details)


class Bank:
    """Manages multiple accounts and provides banking operations."""

    def __init__(self, name: str):
        """
        Initialize a new bank.

        Args:
            name: Name of the bank
        """
        self.name = name
        self._accounts: Dict[str, Account] = {}

    def create_account(self, account_type: str, name: str, initial_balance: float = 0.0,
                      interest_rate: float = 0.01) -> Account:
        """
        Create a new account.

        Args:
            account_type: Type of account to create ('checking' or 'savings')
            name: Account holder's name
            initial_balance: Starting balance
            interest_rate: Annual interest rate for savings accounts

        Returns:
            The newly created account

        Raises:
            ValueError: If account type is invalid
        """
        account_type = account_type.lower()

        if account_type == "checking":
            account = CheckingAccount(name, initial_balance)
        elif account_type == "savings":
            account = SavingsAccount(name, initial_balance, interest_rate)
        else:
            raise ValueError("Invalid account type. Choose 'checking' or 'savings'")

        self._accounts[account.account_number] = account
        return account

    def get_account(self, account_number: str) -> Optional[Account]:
        """
        Get an account by its account number.

        Args:
            account_number: Account number to look up

        Returns:
            The account if found, None otherwise
        """
        return self._accounts.get(account_number)

    def get_all_accounts(self) -> List[Account]:
        """Get a list of all accounts in the bank."""
        return list(self._accounts.values())

    def display_all_accounts(self) -> None:
        """Display all accounts in a formatted manner."""
        if not self._accounts:
            print("No accounts to display")
            return

        print(f"\n===== {self.name} Accounts =====")
        print("Account Number | Type     | Name                | Balance")
        print("---------------|----------|---------------------|------------")
        for account in self._accounts.values():
            print(f"{account.account_number} | {account.get_account_type():<8} | {account.name:<20} | £{account.balance:.2f}")
        print("==============================\n")

    def apply_interest_to_savings_accounts(self) -> float:
        """
        Apply interest to all savings accounts.

        Returns:
            Total interest applied
        """
        total_interest = 0.0
        for account in self._accounts.values():
            if isinstance(account, SavingsAccount):
                total_interest += account.apply_interest()
        return total_interest

    def transfer(self, from_account_number: str, to_account_number: str, amount: float) -> bool:
        """
        Transfer money between two accounts.

        Args:
            from_account_number: Account number to transfer from
            to_account_number: Account number to transfer to
            amount: Amount to transfer

        Returns:
            True if transfer was successful, False otherwise

        Raises:
            ValueError: If either account is not found
            InvalidAmountError: If amount is negative or zero
            InsufficientFundsError: If withdrawal would result in negative balance
            MonthlyWithdrawalLimitError: If monthly withdrawal limit is reached (for savings accounts)
        """
        # Check if accounts exist
        from_account = self.get_account(from_account_number)
        to_account = self.get_account(to_account_number)

        if not from_account:
            raise ValueError(f"Source account {from_account_number} not found")

        if not to_account:
            raise ValueError(f"Destination account {to_account_number} not found")

        if from_account_number == to_account_number:
            raise ValueError("Cannot transfer to the same account")

        # Check for valid amount
        if amount <= 0:
            raise InvalidAmountError("Transfer amount must be positive")

        # Check for sufficient funds
        if amount > from_account.balance:
            raise InsufficientFundsError(f"Insufficient funds. Current balance: £{from_account.balance:.2f}")

        # Perform transfer (withdrawal from source, deposit to destination)
        try:
            # For savings account, check withdrawal limits
            if isinstance(from_account, SavingsAccount):
                # This will check withdrawal limits and raise an exception if needed
                from_account.withdraw(amount, f"Transfer to account {to_account_number}")
                # Add deposit to destination
                to_account.deposit(amount, f"Transfer from account {from_account_number}")
            else:
                # For regular accounts, just withdraw and deposit
                from_account.withdraw(amount, f"Transfer to account {to_account_number}")
                to_account.deposit(amount, f"Transfer from account {from_account_number}")

            print(f"Successfully transferred £{amount:.2f} from account {from_account_number} to {to_account_number}")
            return True

        except Exception as e:
            print(f"Transfer failed: {e}")
            return False

    def get_bank_statistics(self) -> dict:
        """Get statistics about the bank and its accounts."""
        total_accounts = len(self._accounts)
        checking_accounts = sum(1 for acc in self._accounts.values() if isinstance(acc, CheckingAccount))
        savings_accounts = sum(1 for acc in self._accounts.values() if isinstance(acc, SavingsAccount))

        total_balance = sum(acc.balance for acc in self._accounts.values())
        checking_balance = sum(acc.balance for acc in self._accounts.values() if isinstance(acc, CheckingAccount))
        savings_balance = sum(acc.balance for acc in self._accounts.values() if isinstance(acc, SavingsAccount))

        return {
            "total_accounts": total_accounts,
            "checking_accounts": checking_accounts,
            "savings_accounts": savings_accounts,
            "total_balance": total_balance,
            "checking_balance": checking_balance,
            "savings_balance": savings_balance
        }

    def display_bank_statistics(self) -> None:
        """Display statistics about the bank."""
        stats = self.get_bank_statistics()

        print(f"\n===== {self.name} Statistics =====")
        print(f"Total accounts: {stats['total_accounts']}")
        print(f"Checking accounts: {stats['checking_accounts']}")
        print(f"Savings accounts: {stats['savings_accounts']}")
        print(f"Total balance across all accounts: £{stats['total_balance']:.2f}")
        print(f"Total balance in checking accounts: £{stats['checking_balance']:.2f}")
        print(f"Total balance in savings accounts: £{stats['savings_balance']:.2f}")
        print("===================================\n")


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_valid_input(prompt: str, validation_func: Callable[[str], Any], error_message: str) -> Any:
    """
    Get validated input from the user.

    Args:
        prompt: The prompt to display to the user
        validation_func: A function that validates the input
        error_message: Message to display if validation fails

    Returns:
        The validated input
    """
    while True:
        user_input = input(prompt)
        try:
            result = validation_func(user_input)
            return result
        except (ValueError, TypeError):
            print(error_message)


def main() -> None:
    """Main function to run the banking application."""
    # Set the bank name
    BANK_NAME = "Universal Banking System"

    clear_screen()
    print(f"\n{'=' * 40}")
    print(f"{BANK_NAME}".center(40))
    print(f"{'=' * 40}\n")

    # Create a bank with the predefined name
    bank = Bank(BANK_NAME)

    while True:
        print("\n=== Main Menu ===")
        print("1. Create a new account")
        print("2. Select an existing account")
        print("3. Display all accounts")
        print("4. Transfer between accounts")
        print("5. Apply interest to all savings accounts")
        print("6. Display bank statistics")
        print("7. Exit")

        choice = get_valid_input("Enter your choice (1-7): ",
                              lambda x: int(x) if 1 <= int(x) <= 7 else ValueError(),
                              "Invalid choice. Please enter a number between 1 and 7.")

        if choice == 1:
            # Create a new account
            clear_screen()
            print("\n=== Create a New Account ===")
            print("1. Checking Account")
            print("2. Savings Account")

            account_type_choice = get_valid_input("Select account type (1-2): ",
                                              lambda x: int(x) if 1 <= int(x) <= 2 else ValueError(),
                                              "Invalid choice. Please enter 1 or 2.")

            account_type = "checking" if account_type_choice == 1 else "savings"
            name = input("Enter account holder's name: ")

            initial_balance = get_valid_input("Enter initial balance: £",
                                         lambda x: float(x) if float(x) >= 0 else ValueError(),
                                         "Invalid amount. Please enter a non-negative number.")

            interest_rate = 0.01  # Default interest rate
            if account_type == "savings":
                interest_rate = get_valid_input("Enter annual interest rate (e.g., 0.01 for 1%): ",
                                           lambda x: float(x) if 0 <= float(x) <= 0.1 else ValueError(),
                                           "Invalid interest rate. Please enter a number between 0 and 0.1.")

            try:
                account = bank.create_account(account_type, name, initial_balance, interest_rate)
                print(f"\nAccount created successfully!")
                print(f"Account Number: {account.account_number}")
                print(f"Account Type: {account.get_account_type()}")
                print(f"Initial Balance: £{account.balance:.2f}")
                if account_type == "savings":
                    print(f"Interest Rate: {interest_rate:.2%}")
                    print(f"Monthly Withdrawal Limit: {account.withdrawal_limit}")
            except Exception as e:
                print(f"Error creating account: {e}")

            input("\nPress Enter to continue...")

        elif choice == 2:
            # Select an existing account
            if not bank.get_all_accounts():
                print("No accounts exist. Please create an account first.")
                continue

            clear_screen()
            bank.display_all_accounts()
            account_number = input("Enter account number to select (or just press Enter to return): ")

            if not account_number:
                continue

            account = bank.get_account(account_number)

            if not account:
                print("Account not found.")
                input("\nPress Enter to continue...")
                continue

            # Account operations submenu
            while True:
                clear_screen()
                print(f"\n=== Account: {account.account_number} ({account.name}) ===")
                print(f"Type: {account.get_account_type()}")
                print(f"Current Balance: £{account.balance:.2f}")

                if isinstance(account, SavingsAccount):
                    print(f"Interest Rate: {account.interest_rate:.2%}")
                    print(f"Withdrawals Remaining This Month: {account.withdrawals_remaining}")

                print("\n1. Deposit")
                print("2. Withdraw")
                print("3. View Transaction History")
                print("4. View Detailed Account Summary")
                print("5. Return to Main Menu")

                account_choice = get_valid_input("Enter your choice (1-5): ",
                                            lambda x: int(x) if 1 <= int(x) <= 5 else ValueError(),
                                            "Invalid choice. Please enter a number between 1 and 5.")

                if account_choice == 1:
                    # Deposit
                    amount = get_valid_input("Enter deposit amount: £",
                                        lambda x: float(x) if float(x) > 0 else ValueError(),
                                        "Invalid amount. Please enter a positive number.")
                    description = input("Enter deposit description (optional): ")
                    try:
                        account.deposit(amount, description)
                    except Exception as e:
                        print(f"Error: {e}")
                    input("\nPress Enter to continue...")

                elif account_choice == 2:
                    # Withdraw
                    amount = get_valid_input("Enter withdrawal amount: £",
                                        lambda x: float(x) if float(x) > 0 else ValueError(),
                                        "Invalid amount. Please enter a positive number.")
                    description = input("Enter withdrawal description (optional): ")
                    try:
                        account.withdraw(amount, description)
                    except Exception as e:
                        print(f"Error: {e}")
                    input("\nPress Enter to continue...")

                elif account_choice == 3:
                    account.display_transaction_history()
                    input("\nPress Enter to continue...")

                elif account_choice == 4:
                    # Display detailed account summary
                    clear_screen()
                    print("\n=== Detailed Account Summary ===")
                    print(account.get_account_summary())
                    input("\nPress Enter to continue...")

                elif account_choice == 5:
                    break

        elif choice == 3:
            clear_screen()
            bank.display_all_accounts()
            input("\nPress Enter to continue...")

        elif choice == 4:
            # Transfer between accounts
            clear_screen()
            if len(bank.get_all_accounts()) < 2:
                print("You need at least two accounts to perform a transfer. Please create more accounts.")
                input("\nPress Enter to continue...")
                continue

            bank.display_all_accounts()

            # Get source account
            from_account_number = input("Enter source account number: ")
            from_account = bank.get_account(from_account_number)
            if not from_account:
                print("Source account not found.")
                input("\nPress Enter to continue...")
                continue

            # Get destination account
            to_account_number = input("Enter destination account number: ")
            to_account = bank.get_account(to_account_number)
            if not to_account:
                print("Destination account not found.")
                input("\nPress Enter to continue...")
                continue

            if from_account_number == to_account_number:
                print("Cannot transfer to the same account.")
                input("\nPress Enter to continue...")
                continue

            # Get transfer amount
            amount = get_valid_input("Enter transfer amount: £",
                                 lambda x: float(x) if float(x) > 0 else ValueError(),
                                 "Invalid amount. Please enter a positive number.")

            try:
                bank.transfer(from_account_number, to_account_number, amount)
            except Exception as e:
                print(f"Transfer error: {e}")

            input("\nPress Enter to continue...")

        elif choice == 5:
            # Apply interest to all savings accounts
            clear_screen()
            total_interest = bank.apply_interest_to_savings_accounts()
            print(f"Interest applied to all savings accounts. Total interest: £{total_interest:.2f}")
            input("\nPress Enter to continue...")

        elif choice == 6:
            # Display bank statistics
            clear_screen()
            bank.display_bank_statistics()
            input("\nPress Enter to continue...")

        elif choice == 7:
            # Exit the application
            print(f"\nThank you for using the {BANK_NAME} Application. Goodbye!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user. Goodbye!")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("The application has been terminated.")