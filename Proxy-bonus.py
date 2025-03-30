#!/usr/bin/env python3
# Proxy-bonus.py
# Bonus features implemented:
# 1. Expires header: proxy checks if cached files have expired and re-fetches if needed
# 2. Prefetches embedded resources (href/src) from HTML and stores them in cache (not sent to client)
# 3. Supports URLs with custom ports (hostname:port/path)

import socket
import sys
import os
import argparse
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# 1MB buffer size
BUFFER_SIZE = 1000000

# Parse command line arguments for the proxy hostname and port
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it, and start listening
try:
    # ~~~~ INSERT CODE ~~~~
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~
    print('Created socket')
except Exception as e:
    print('Failed to create socket:', e)
    sys.exit()

try:
    # ~~~~ INSERT CODE ~~~~
    serverSocket.bind((proxyHost, proxyPort))
    # ~~~~ END CODE INSERT ~~~~
    print('Port is bound')
except Exception as e:
    print('Port is already in use:', e)
    sys.exit()

try:
    # ~~~~ INSERT CODE ~~~~
    serverSocket.listen(5)
    # ~~~~ END CODE INSERT ~~~~
    print('Listening to socket')
except Exception as e:
    print('Failed to listen:', e)
    sys.exit()

# ------------------ Bonus 1 Implementation ------------------
# Function to check if the cached response is fresh using the Expires header.
def is_cache_fresh(cache_data):
    header_end = cache_data.find(b"\r\n\r\n")
    if header_end == -1:
        return True  # No header; assume fresh.
    header_text = cache_data[:header_end].decode("utf-8", errors="ignore")
    headers = header_text.split("\r\n")
    for header in headers:
        if header.lower().startswith("expires:"):
            expires_str = header[len("expires:"):].strip()
            try:
                expires_dt = parsedate_to_datetime(expires_str)
                now = datetime.now(timezone.utc)
                if expires_dt < now:
                    print("Cache expired")
                    return False
            except Exception as e:
                print("Error parsing Expires header:", e)
                return True
    return True

# ------------------ Bonus 2 Implementation ------------------
# Function to prefetch resources (found in href and src attributes) from HTML.
def prefetch_resource(full_url, base_host, base_port):
    # Determine if the URL is absolute or relative.
    if full_url.startswith("http://") or full_url.startswith("https://"):
        url_no_protocol = re.sub('^http(s)?://', '', full_url, count=1)
        parts = url_no_protocol.split('/', 1)
        resource_host = parts[0]
        resource_path = '/' + parts[1] if len(parts) > 1 else '/'
        if ":" in resource_host:
            host_parts = resource_host.split(":", 1)
            real_host = host_parts[0]
            resource_port = int(host_parts[1])
        else:
            real_host = resource_host
            resource_port = 80
    else:
        real_host = base_host
        resource_port = base_port
        resource_path = full_url if full_url.startswith("/") else "/" + full_url

    # Create a safe cache path (replace colon with underscore)
    safe_host = real_host if resource_port == 80 else f"{real_host}_{resource_port}"
    cache_location = "./" + safe_host + resource_path
    if cache_location.endswith('/'):
        cache_location += "default"

    # If already cached and fresh, skip prefetching.
    if os.path.isfile(cache_location):
        try:
            with open(cache_location, "rb") as f:
                cache_data = f.read()
                if is_cache_fresh(cache_data):
                    print(f"Prefetch skipped: {cache_location} is fresh")
                    return
        except:
            pass

    print(f"Prefetching: {full_url} -> {cache_location}")
    try:
        originSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin_address = socket.gethostbyname(real_host)
        originSocket.connect((origin_address, resource_port))
        request_line = "GET " + resource_path + " HTTP/1.1"
        host_header = "Host: " + (resource_host if full_url.startswith("http") else base_host)
        connection_header = "Connection: close"
        request = request_line + "\r\n" + host_header + "\r\n" + connection_header + "\r\n\r\n"
        originSocket.sendall(request.encode())
        response = b""
        while True:
            data = originSocket.recv(BUFFER_SIZE)
            if not data:
                break
            response += data
        originSocket.close()
        cache_dir, _ = os.path.split(cache_location)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        with open(cache_location, "wb") as cache_file:
            cache_file.write(response)
        print(f"Prefetched and cached: {cache_location}")
    except Exception as e:
        print(f"Prefetch failed for {full_url}: {e}")

# Main proxy loop
while True:
    print('Waiting for connection...')
    clientSocket = None

    # Accept connection from client
    try:
        # ~~~~ INSERT CODE ~~~~
        clientSocket, addr = serverSocket.accept()
        # ~~~~ END CODE INSERT ~~~~
        print('Received a connection')
    except Exception as e:
        print('Failed to accept connection:', e)
        sys.exit()

    # Get HTTP request from client
    try:
        # ~~~~ INSERT CODE ~~~~
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        # ~~~~ END CODE INSERT ~~~~
        message = message_bytes.decode('utf-8')
        print('Received request:')
        print('< ' + message)
    except Exception as e:
        print("Error receiving request:", e)
        clientSocket.close()
        continue

    requestParts = message.split()
    if len(requestParts) < 3:
        clientSocket.close()
        continue

    method = requestParts[0]
    URI = requestParts[1]
    version = requestParts[2]

    print('Method:\t\t' + method)
    print('URI:\t\t' + URI)
    print('Version:\t' + version)
    print('')

    # Remove http(s):// prefix and '/../' for security
    URI = re.sub('^(/?)http(s)?://', '', URI, count=1)
    URI = URI.replace('/..', '')

    # Split hostname and resource
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/'
    if len(resourceParts) == 2:
        resource = '/' + resourceParts[1]

    # ------------------ Bonus 3 Implementation ------------------
    # Handle hostname with a specified port (e.g., hostname:port)
    if ":" in hostname:
        host_parts = hostname.split(":", 1)
        real_hostname = host_parts[0]
        origin_port = int(host_parts[1])
    else:
        real_hostname = hostname
        origin_port = 80

    # For caching, replace colon with underscore
    safe_hostname = hostname.replace(":", "_")
    cache_location = "./" + safe_hostname + resource
    if cache_location.endswith('/'):
        cache_location += "default"

    print('Requested Resource:\t' + resource)
    print('Cache location:\t\t' + cache_location)

    # Try serving from cache if file exists and is fresh
    try:
        if os.path.isfile(cache_location):
            with open(cache_location, "rb") as cacheFile:
                cache_data = cacheFile.read()
            if not is_cache_fresh(cache_data):
                raise Exception("Cached file expired")
            print('Cache hit! Loading from cache file: ' + cache_location)
            # ~~~~ INSERT CODE ~~~~
            clientSocket.sendall(cache_data)
            # ~~~~ END CODE INSERT ~~~~
        else:
            raise Exception("Cache file does not exist")
    except Exception as e:
        print("Cache miss or expired:", e)
        # Cache miss: get resource from origin server
        try:
            # ~~~~ INSERT CODE ~~~~
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # ~~~~ END CODE INSERT ~~~~
        except Exception as e:
            print("Failed to create origin server socket:", e)
            clientSocket.close()
            continue

        try:
            address = socket.gethostbyname(real_hostname)
            # ~~~~ INSERT CODE ~~~~
            originServerSocket.connect((address, origin_port))
            # ~~~~ END CODE INSERT ~~~~
            print('Connected to origin server:', real_hostname, "on port", origin_port)

            originRequest = "GET " + resource + " HTTP/1.1"
            originHeaders = "Host: " + hostname + "\r\nConnection: close"
            request_to_origin = originRequest + "\r\n" + originHeaders + "\r\n\r\n"
            print('Forwarding request to origin server:')
            for line in request_to_origin.split('\r\n'):
                if line:
                    print('> ' + line)

            originServerSocket.sendall(request_to_origin.encode())
            originResponse = b""
            # ~~~~ INSERT CODE ~~~~
            while True:
                data = originServerSocket.recv(BUFFER_SIZE)
                if not data:
                    break
                originResponse += data
            # ~~~~ END CODE INSERT ~~~~

            # Send origin server response to client
            # ~~~~ INSERT CODE ~~~~
            clientSocket.sendall(originResponse)
            # ~~~~ END CODE INSERT ~~~~

            # Cache the origin server response
            cacheDir, _ = os.path.split(cache_location)
            if not os.path.exists(cacheDir):
                os.makedirs(cacheDir)
            with open(cache_location, 'wb') as cacheFile:
                # ~~~~ INSERT CODE ~~~~
                cacheFile.write(originResponse)
                # ~~~~ END CODE INSERT ~~~~
            print('Cached response from origin server at:', cache_location)

            # Bonus 2: If the response is HTML, prefetch associated resources (href/src)
            header_end = originResponse.find(b"\r\n\r\n")
            if header_end != -1:
                header_text = originResponse[:header_end].decode("utf-8", errors="ignore")
                if "Content-Type:" in header_text and "text/html" in header_text.lower():
                    body = originResponse[header_end+4:].decode("utf-8", errors="ignore")
                    hrefs = re.findall(r'href="([^"]+)"', body)
                    srcs = re.findall(r'src="([^"]+)"', body)
                    resources = set(hrefs + srcs)
                    print("Found resources to prefetch:")
                    for res in resources:
                        print("  -", res)
                        prefetch_resource(res, real_hostname, origin_port)
            originServerSocket.close()
            print('Closed connection to origin server.')
        except Exception as e:
            print('Origin server request failed:', e)

    try:
        clientSocket.shutdown(socket.SHUT_WR)
        clientSocket.close()
        print('Closed client socket.\n')
    except Exception as e:
        print('Failed to close client socket:', e)



