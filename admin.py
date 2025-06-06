from utils import is_valid_future_date


def admin_mode(emp_manager, db):
    def display_menu():
        print("\nAdmin Options:")
        print("1. Register New Employee")
        print("2. Modify Employee Details")
        print("3. Remove Employee")
        print("4. Register Holiday")
        print("5. Review Leave Requests")
        print("6. Exit Admin Mode\n")

    def get_leave_balances(existing=None):
        leave_categories = ["Sick Leave", "Annual Leave", "Maternity Leave"]
        balances = {}
        print("Provide leave balances for each type (press enter to retain current if editing):")
        for leave_type in leave_categories:
            while True:
                prompt_text = f"  {leave_type}"
                if existing:
                    prompt_text += f" (currently: {existing.get(leave_type, 0)})"
                prompt_text += ": "
                user_input = input(prompt_text).strip()

                if user_input == "" and existing is not None:
                    balances[leave_type] = existing.get(leave_type, 0)
                    break

                if user_input == "":
                    print("Input required. Enter a number (use 0 if none).")
                    continue

                try:
                    val = int(user_input)
                    if val < 0:
                        print("Number must be zero or positive.")
                        continue
                    balances[leave_type] = val
                    break
                except ValueError:
                    print("Invalid entry. Please provide a valid integer.")

        return balances

    display_menu()

    while True:
        command = input("Select an option by number: ").strip()

        if command == "1":  # Register New Employee
            emp_name = input("Enter employee's full name: ").strip()
            leave_balances = get_leave_balances()
            manager_status = input(
                "Is this employee a manager? (yes/no): ").strip().lower() == "yes"
            msg = emp_manager.add_employee(
                emp_name, leave_balances, manager_status)
            print(msg)
            db.log_action(
                f"New employee added: {emp_name}, Manager: {manager_status}, Leave: {leave_balances}")

        elif command == "2":  # Modify Employee Details
            employees_list = list(db.data.get("employees", {}).keys())
            if not employees_list:
                print("No employees available to edit.")
                display_menu()
                continue

            print("\nEmployee List:")
            for idx, ename in enumerate(employees_list, 1):
                print(f"{idx}. {ename}")
            print("Type 'quit' to cancel editing.")

            while True:
                selection = input(
                    "Choose employee number to edit or 'quit': ").strip().lower()
                if selection == "quit":
                    break
                if not selection.isdigit() or not (1 <= int(selection) <= len(employees_list)):
                    print("Please enter a valid number or 'quit'.")
                    continue
                emp_to_edit = employees_list[int(selection) - 1]
                break

            if selection == "quit":
                display_menu()
                continue

            current_balances = db.data["employees"][emp_to_edit].get(
                "leave_balance", {})
            print("Update leave balances:")
            new_balances = get_leave_balances(current_balances)

            mgr_input = input(
                "Change manager status? (yes/no/skip): ").strip().lower()
            if mgr_input == "yes":
                new_mgr_status = True
            elif mgr_input == "no":
                new_mgr_status = False
            else:
                new_mgr_status = None

            msg = emp_manager.edit_employee(
                emp_to_edit, new_balances, new_mgr_status)
            print(msg)
            db.log_action(
                f"Employee updated: {emp_to_edit}, Leave: {new_balances}, Manager status: {new_mgr_status}")

        elif command == "3":  # Remove Employee
            employees_list = list(db.data.get("employees", {}).keys())
            if not employees_list:
                print("No employees to remove.")
                display_menu()
                continue

            print("\nEmployees:")
            for idx, ename in enumerate(employees_list, 1):
                print(f"{idx}. {ename}")
            print("Type 'quit' to cancel.")

            while True:
                sel = input(
                    "Select employee number or name to remove or 'quit': ").strip()
                if sel.lower() == "quit":
                    break

                if sel.isdigit():
                    idx = int(sel)
                    if not (1 <= idx <= len(employees_list)):
                        print("Number out of range. Try again.")
                        continue
                    target_emp = employees_list[idx - 1]
                else:
                    if sel not in employees_list:
                        print("Name not found. Try again.")
                        continue
                    target_emp = sel

                confirm = input(
                    f"Confirm deletion of '{target_emp}' and all their data? (yes/no): ").strip().lower()
                if confirm == "yes":
                    db.data["employees"].pop(target_emp, None)
                    db.save()
                    print(f"'{target_emp}' has been removed.")
                    db.log_action(f"Deleted employee: {target_emp}")
                else:
                    print("Deletion aborted.")
                break

            display_menu()

        elif command == "4":  # Register Holiday
            while True:
                holiday_date = input(
                    "Enter holiday date (YYYY-MM-DD): ").strip()
                if not is_valid_future_date(holiday_date):
                    print("Date format invalid. Use YYYY-MM-DD.")
                    continue
                break

            confirm = input(
                f"Add {holiday_date} as a holiday? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Holiday registration cancelled.")
                display_menu()
                continue

            msg = emp_manager.add_holiday(holiday_date)
            print(msg)
            db.log_action(f"Holiday added: {holiday_date}")

        elif command == "5":  # Review Leave Requests
            pending_users = [user for user, data in db.data.get("employees", {}).items()
                             if any(req.get("status") == "Pending" for req in data.get("leave_history", []))]

            if not pending_users:
                print("No pending leave requests at the moment.")
                display_menu()
                continue

            print("\nEmployees with pending requests:")
            for idx, user in enumerate(pending_users, 1):
                print(f"{idx}. {user}")
            print("Type 'quit' to cancel.")

            while True:
                selection = input(
                    "Select employee number to review requests or 'quit': ").strip().lower()
                if selection == "quit":
                    break
                if not selection.isdigit() or not (1 <= int(selection) <= len(pending_users)):
                    print("Invalid input. Please enter a valid number or 'quit'.")
                    continue
                selected_user = pending_users[int(selection) - 1]
                break

            if selection == "quit":
                display_menu()
                continue

            user_data = db.data["employees"][selected_user]
            pending_requests = [req for req in user_data.get(
                "leave_history", []) if req.get("status") == "Pending"]

            for idx, req in enumerate(pending_requests, 1):
                print(
                    f"\nRequest {idx}: {req['days']} day(s) of {req['type']} starting {req['start_date']}")
                while True:
                    decision = input(
                        "Approve or deny? (a/d): ").strip().lower()
                    if decision == "a":
                        req["status"] = "Approved"
                        print("Request approved.")
                        db.log_action(
                            f"Leave approved: {req['days']} days {req['type']} for {selected_user} starting {req['start_date']}")
                        break
                    elif decision == "d":
                        req["status"] = "Denied"
                        user_data["leave_balance"][req["type"]] = user_data["leave_balance"].get(
                            req["type"], 0) + req["days"]
                        print("Request denied; leave balance refunded.")
                        db.log_action(
                            f"Leave denied: {req['days']} days {req['type']} for {selected_user} starting {req['start_date']}")
                        break
                    else:
                        print("Please enter 'a' to approve or 'd' to deny.")

            db.data["employees"][selected_user] = user_data
            db.save()

        elif command == "6":  # Exit Admin Mode
            print("Leaving admin mode...")
            break

        else:
            print("Invalid selection, please try again.")

        # Re-display the menu after each command except exit
        display_menu()
