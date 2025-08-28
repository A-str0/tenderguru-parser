from services.api_service import APIService
from services.request_service import RequestService
import requests as rq


def main() -> None:
    request_service = RequestService()
    api_service = APIService(request_service)

    response1: rq.Response = request_service.make_request("https://www.rusprofile.ru/search", {"query" : "1211600002393"})
    res = api_service.parse_webpage_ooo(response1.text)
    print(res)

    print()
    
    response2: rq.Response = request_service.make_request("https://www.rusprofile.ru/search", {"query" : "310547623100434"})
    res = api_service.parse_webpage_ip(response2.text)
    print(res)


if __name__ == "__main__":
    main()
