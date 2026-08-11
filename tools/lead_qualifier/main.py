import requests


def qualify_lead(text):
    text = text.lower()

    hot_words = [
        "urgent",
        "as soon as possible",
        "asap",
        "budget",
        "ready to start",
        "need a developer",
        "hire",
    ]

    warm_words = [
        "website",
        "chatbot",
        "automation",
        "python",
        "api",
        "customer",
        "business",
        "company",
        "interested",
        "comparing options",
    ]

    hot_score = sum(word in text for word in hot_words)
    warm_score = sum(word in text for word in warm_words)

    if hot_score >= 1:
        return "HOT"
    elif warm_score >= 2:
        return "WARM"
    else:
        return "COLD"


def main():
    url = "https://postman-echo.com/post"

    lead = input("Describe the customer request: ")

    payload = {
        "lead": lead
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()
        data = response.json()

        received_lead = data.get("json", {}).get("lead")

        if received_lead:
            status = qualify_lead(received_lead)

            print()
            print("===== LEAD ANALYSIS =====")
            print(f"Request: {received_lead}")
            print(f"Lead status: {status}")
            print("=========================")
        else:
            print("Lead was not found in the server response.")

    except requests.exceptions.Timeout:
        print("Request timed out. Please try again.")

    except requests.exceptions.ConnectionError:
        print("Could not connect to the server.")

    except requests.exceptions.JSONDecodeError:
        print("Server returned invalid JSON.")

    except requests.exceptions.HTTPError as error:
        print(f"HTTP error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")


if __name__ == "__main__":
    main()
