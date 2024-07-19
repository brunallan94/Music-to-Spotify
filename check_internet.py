import socket


def check_internet_connection(url="8.8.8.8", port=53, timeout=3) -> bool:
    """
    Check if there is an active internet connection by attempting to connect to a specified URL.

    :param url: The URL to connect to (default is Google's DNS server).
    :param port: The port to connect to (default is 53 for DNS).
    :param timeout: The timeout for the connection attempt in seconds (default is 3 seconds).
    :return: True if the connection is successful, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((url, port))
        return True
    except socket.error as ex:
        print(f"Internet connection check failed: {ex}")
        return False


if __name__ == '__main__':
    check_internet_connection()
