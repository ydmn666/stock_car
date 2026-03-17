import os

def disable_proxy_env():
    for key in [
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
    ]:
        os.environ.pop(key, None)

    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    os.environ["CURL_CA_BUNDLE"] = ""