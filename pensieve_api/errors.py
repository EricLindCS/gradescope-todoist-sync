from requests import Response


class PensieveAPIError(Exception):
    pass


class AuthError(PensieveAPIError):
    pass


class RequestError(PensieveAPIError):
    pass


def check_response(response: Response, error: str):
    if not response.ok:
        raise RequestError(
            "An error occurred in a request to Pensieve servers. Details: "
            + "\n"
            + "Status Code: "
            + str(response.status_code)
            + "\n"
            + "Error: "
            + str(error)
            + "\n"
            "Request: " + str(vars(response.request)) + "\n" + "Response: " + str(response.content)
        )
