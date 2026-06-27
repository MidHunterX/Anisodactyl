from fastapi import Request


@staticmethod
def create_mock_request(query_string: str) -> Request:
    """Helper to create a FastAPI request with specific query params."""
    scope = {"type": "http", "query_string": query_string.encode()}
    return Request(scope)
