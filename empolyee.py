from datetime import datetime
from utils import is_valid_future_date


class StaffController:
    def __init__(self, database):
        self.database = database

    def employee_exists(self, employee_name):
        return employee_name in self.database.data.get("employees", {})

    def has_manager_privilege(self, employee_name):
        return self.database.data["employees"].get(employee_name, {}).get("is_manager", False)

    def process_request(self, employee_name, action, details):
        employees = self.database.data.get("employees", {})
        if employee_name not in employees:
            return "Employee not found."

        profile = employees[employee_name]

        if action == "check_balance":
            leave_type = details.get("leave_type")
            balance_info = profile.get("leave_balance", {})

            if not leave_type:
                response = ["Your leave balances:"]
                for category, amount in balance_info.items():
                    response.append(f"- {category}: {amount} day(s)")
                return "\n".join(response)

            return f"You have {balance_info.get(leave_type, 0)} {leave_type} leave day(s) remaining."

        elif action == "request_leave":
            leave_type = details.get("leave_type")
            days_requested = details.get("num_days")
            start_date = details.get("start_date")

            if not leave_type:
                return "Specify the leave type."
            if not days_requested:
                return "Mention how many days you want to request."
            if not start_date:
                return "Start date is missing."

            try:
                days_requested = int(days_requested)
                if days_requested <= 0:
                    return "Leave days must be a positive number."
            except Exception:
                return "Invalid number of days entered."

            if not is_valid_future_date(start_date):
                return "Date format should be YYYY-MM-DD."
            if start_date in self.database.data.get("holidays", []):
                return f"{start_date} is a holiday. Pick a different date."

            available = profile.get("leave_balance", {}).get(leave_type, 0)
            if available < days_requested:
                return f"You only have {available} {leave_type} day(s) left."

            profile["leave_balance"][leave_type] -= days_requested

            new_request = {
                "type": leave_type,
                "days": days_requested,
                "start_date": start_date,
                "status": "Pending",
                "requested_on": str(datetime.today().date())
            }

            profile.setdefault("leave_history", []).append(new_request)
            self.database.data["employees"][employee_name] = profile
            self.database.save()
            self.database.log_action(
                f"{employee_name} submitted a leave request for {days_requested} day(s) of {leave_type} starting from {start_date}."
            )
            return f"Leave request submitted for {days_requested} {leave_type} day(s) starting {start_date}. Awaiting approval."

        elif action == "cancel_leave":
            leave_type = details.get("leave_type")
            start_date = details.get("start_date")
            history = profile.get("leave_history", [])

            if not history:
                return "No previous leave records found."
            if not leave_type or not start_date:
                return "Please provide both leave type and start date to cancel."
            if not is_valid_future_date(start_date):
                return "Invalid date format. Use YYYY-MM-DD."

            for record in history:
                if record["type"] == leave_type and record["start_date"] == start_date and record["status"] in ["Pending", "Approved"]:
                    record["status"] = "Cancelled"
                    profile["leave_balance"][leave_type] += record["days"]
                    self.database.data["employees"][employee_name] = profile
                    self.database.save()
                    self.database.log_action(
                        f"{employee_name} cancelled leave for {leave_type} on {start_date}."
                    )
                    return "Leave request cancelled successfully."

            return "Matching leave not found to cancel."

        elif action == "view_history":
            history = profile.get("leave_history", [])
            if not history:
                return "No leave history found."
            return "\n".join([
                f"{entry['type']} leave on {entry['start_date']} for {entry['days']} day(s) - {entry['status']}"
                for entry in history
            ])

        elif action == "approve_leave" and self.has_manager_privilege(employee_name):
            target_name = details.get("employee_name")
            all_employees = self.database.data.get("employees", {})

            if not target_name or target_name not in all_employees:
                return "Target employee not found."

            target_profile = all_employees[target_name]
            pending_requests = [
                entry for entry in target_profile.get("leave_history", [])
                if entry["status"] == "Pending"
            ]

            if not pending_requests:
                return "No pending leaves to approve."

            for req in pending_requests:
                req["status"] = "Approved"

            self.database.save()
            self.database.log_action(
                f"{employee_name} approved all pending leave requests for {target_name}."
            )
            return f"All pending leaves approved for {target_name}."

        return "Command not recognized or unauthorized action."

    def register_employee(self, emp_name, initial_balances, manager_status=False):
        if emp_name in self.database.data.get("employees", {}):
            return "Employee already registered."

        self.database.data["employees"][emp_name] = {
            "leave_balance": initial_balances,
            "is_manager": manager_status,
            "leave_history": []
        }
        self.database.save()
        self.database.log_action(f"New employee added: {emp_name}")
        return f"{emp_name} has been successfully added."

    def update_employee(self, emp_name, new_balances=None, manager_status=None):
        if emp_name not in self.database.data.get("employees", {}):
            return "Employee not found."

        current = self.database.data["employees"][emp_name]

        if new_balances is not None:
            current["leave_balance"] = new_balances
        if manager_status is not None:
            current["is_manager"] = manager_status

        self.database.data["employees"][emp_name] = current
        self.database.save()
        self.database.log_action(f"Employee record updated: {emp_name}")
        return f"{emp_name}'s record has been updated."

    def insert_holiday(self, date_str):
        holidays = self.database.data.get("holidays", [])
        if date_str in holidays:
            return "Holiday already exists."
        holidays.append(date_str)
        self.database.data["holidays"] = holidays
        self.database.save()
        self.database.log_action(f"New holiday added: {date_str}")
        return f"{date_str} marked as a holiday."
