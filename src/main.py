from services.api_service import APIService
from services.request_service import RequestService


def main() -> None:
    request_service = RequestService()
    api_service = APIService(request_service)


if __name__ == "__main__":
    main()
