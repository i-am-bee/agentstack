from starlette.datastructures import URL


def create_resource_uri(url: URL) -> str:
    return f"{url.scheme}://{url.netloc}/{url.path}".rstrip("/")
