import os
import json


def load_json(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            res = json.load(f)
        if not isinstance(res, dict):
            raise ValueError(
                f"JSON file must contain a dictionary (object): {file_path}"
            )
        return res
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON file: {file_path}")


def verify_password(username: str, password: str) -> bool:
    print("Verifying password...")
    print(f"Given Username: {username}")
    print(f'Given Password: {"*" * len(password)}')
    print("Password verified.")
    return True


def submit_reservation(applicant_information: dict, reservation_details: dict) -> None:
    print("\nApplicant Information:")
    print(f"\tName: {applicant_information['name']}")
    print(f"\tAge: {applicant_information['age']}")
    if "gender" in applicant_information:
        print(f"\tGender: {applicant_information['gender']}")
    print(f"\tContact Information:")
    contact_information: dict[str, str] = applicant_information.get("contact", {})
    print(f"\t\tEmail: {contact_information.get('email', 'N/A')}")
    print(f"\t\tPhone: {contact_information.get('phone', 'N/A')}")
    print("\nReservation Details:")
    print(f"\tDate: {reservation_details['reservation_date']}")
    print(f"\tStart: {reservation_details['reservation_time_start']}")
    print(f"\tEnd: {reservation_details['reservation_time_end']}")
    print(f'\tPurpose: {", ".join(reservation_details['reservation_purpose'])}')
    print(f"\tNotes: {reservation_details.get('notes', 'N/A')}")
    print("Submitting reservation...")
    print("Reservation submitted.")


def main():
    main_config = load_json("demo/config/main.json")
    user_credential = load_json(
        f'demo/config/user_credential/{main_config["user_credential"]}.json'
    )
    if verify_password(
        username=user_credential["username"],
        password=user_credential["password"],
    ):

        applicant_information = load_json(
            f'demo/config/applicant_information/{main_config["applicant_information"]}.json'
        )
        reservation_detail = load_json(
            f'demo/config/reservation_detail/{main_config["reservation_detail"]}.json'
        )
        submit_reservation(applicant_information, reservation_detail)


if __name__ == "__main__":
    main()
