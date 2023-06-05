import json
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import sys

response = """\
HTTP/1.1 {status_code} {status_message}
Content-Type: application/json; charset=UTF-8
Content-Length: {content_length}

{payload}
"""

# Dictionary that maintains cache
cache = {}

# Ports of all order services
portsOfOrderServices = []

# Ids of all order services
idsOfOrderServices = []

# Setting a leader node port
leaderNodePort = 0

# Is cache enable
# Cache is enabled by default
cacheFlag = True

# Function to select an order service (up and running) with highest
def leaderElection():
    global idsOfOrderServices
    global portsOfOrderServices

    # Setting a default port number
    leader = 1

    # Iterating from the order service with the highest id
    for index in reversed(range(len(idsOfOrderServices))):
        orders = socket.socket()
        host = "127.0.0.1"
        port = portsOfOrderServices[index]
        try:

            orders.connect((host, port))
            orders.close()
            leader = portsOfOrderServices[index]
            break
        except socket.error as msg:
            print(msg)

    return leader

# Check if the input request is a json request
def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def threaded(c, lockCache, lockLeaderNode):
    global cache
    global leaderNodePort
    global cacheFlag

    # Thread per session model
    while True:
        # Receive Data from client/catalog
        # This request can be a http request from client
        # This request can also be a restock message from catalog
        httpRequest = c.recv(1024)

        # If client/catalog closes their socket, then we break the loop and close the socket
        # This is a thread per session model
        if not httpRequest:
            print('Bye')
            break
        # Checking if it's a http request from client
        # Or a json request from catalog about the restock
        # Or a json request from order service to find out the leaderNode
        if is_json(httpRequest):
            # This is a restock message
            # We need to update cache and remove all items that are restocked
            request = json.loads(httpRequest)

            if request.get('message') == 'Get Leader':
                # Locking since we are accessing shared memory space
                lockLeaderNode.acquire()
                resp = {'leaderNodePort': leaderNodePort}
                c.send(json.dumps(resp).encode('utf-8'))
                lockLeaderNode.release()
                break

            if cacheFlag and (request.get('code') == 1 and request.get('message') == 'Restock') and len(request.get('restockToyList')) > 0:
                # Locking since we are accessing a shared memory space
                lockCache.acquire()
                for toy in request.get('restockToyList'):
                    if toy in cache:
                        del cache[toy]
                lockCache.release()

            # Send a success message to catalog after we remove restocked elements
            c.send('Success'.encode("utf-8"))
        else:

            # We come here if the input message is a http request from client
            # Parsing the http request
            arr = httpRequest.decode().split('\r\n')
            print(arr)

            # Getting all the data we need from the http message
            request = arr[0]
            request_type = request.split(' ')[0]
            parsed = urlparse(request.split(' ')[1])
            request_path = parsed.path
            request_query = parsed.query
            request_body = arr[len(arr) - 1]

            # Getting the dictionary from the raw json the client passes with the post request
            request_body_json = json.loads(request_body.replace('\n', '')) if request_body != '' else {}

            # Getting the dictionary from the url parameters the client passes through the url
            request_query_json = {i.split('=')[0]: i.split('=')[1] if len(i.split('=')) == 2 else None for i in
                                  request_query.split('&')} if request_query != '' else {}

            # Checking is the request is a 'GET' or a 'POST' request
            if request_type != 'GET' and request_type != 'POST':
                payload = json.dumps({"error": {"code": 404, "message": "Invalid Method Call"}})
                c.send(response.format(status_code=404,
                                       status_message="Invalid Method Call",
                                       content_length=len(payload),
                                       payload=payload)
                       .encode("utf-8"))
                continue

            # Checking if the resource name is '/products' or '/orders'
            if request_path != '/products' and request_path != '/orders':
                payload = json.dumps({"error": {"code": 404, "message": "Invalid URL Path"}})
                c.send(response.format(status_code=404,
                                       status_message="Invalid URL Path",
                                       content_length=len(payload),
                                       payload=payload)
                       .encode("utf-8"))
                continue

            # Checking if the resource name is '/products' or '/orders' when it is a 'GET' request
            # Checking if the resource name is '/orders' when it is a 'POST' request
            if (request_type == 'GET' and (request_path != '/products' and request_path != '/orders')) or (request_type == 'POST' and request_path != '/orders'):
                payload = {"error": {"code": 404, "message": "Invalid Resource for this Request type"}}
                c.send(response.format(status_code=404,
                                       status_message="Invalid Resource for this Request type",
                                       content_length=len(payload),
                                       payload=payload)
                       .encode("utf-8"))
                continue
            data = {}
            if request_type == 'GET':
                # Additional check to see the data type of the request_query_json
                if isinstance(request_query_json, str):
                    request_query_json = json.loads(request_query_json)

                # This is the code that processes get a toy details
                if request_path == '/products':

                    # Check if the url has product_name parameter when try to do a 'GET' request
                    if request_query_json.get("product_name") is None:
                        payload = json.dumps({"error": {"code": 404, "message": "{product_name} parameter missing"}})
                        c.send(response.format(status_code=404,
                                               status_message="{product_name} parameter missing",
                                               content_length=len(payload),
                                               payload=payload)
                               .encode("utf-8"))
                        continue
                    else:

                        # If everything is good then proceed to execute the request
                        product_name = request_query_json.get("product_name")

                        # Setting a default value if we need to contact the catalog
                        contactCatalog = True

                        # Check if cache is enabled
                        if cacheFlag:
                            # Locking since we are reading cache (shared memory space)
                            lockCache.acquire()
                            if product_name in cache:

                                # If the toy is in cache, we don't need to contact catalog
                                # Setting the flag
                                contactCatalog = False

                                # Building response message
                                message = {}
                                message["code"] = 1
                                message["name"] = product_name
                                message["price"] = cache[product_name][0]
                                message["quantity"] = cache[product_name][1]
                            lockCache.release()

                        # If cache is disabled or the toy is not in cache, we should contact catalog
                        if contactCatalog:
                            # Form a dictionary with the data we need to communicate with Catalog
                            data["type"] = "get"
                            data["name"] = product_name

                            # Start communication with Catalog
                            catalog = socket.socket()
                            host = "127.0.0.1"
                            port = 9001
                            catalog.connect((host, port))
                            catalog.send(json.dumps(data).encode('utf-8'))
                            message = catalog.recv(1024)
                            catalog.close()

                            message = json.loads(message)

                        # Process the information we received from the catalog and build payload we need to send to the client
                        if message.get("code") == 1:

                            # If we receive a successful response we need to update our cache
                            # Check if cache is enabled
                            if cacheFlag:

                                # Locking since we are accessing cache
                                lockCache.acquire()

                                # Adding a new toy to cache based on the response from catalog
                                cache[message.get("name")] = []
                                cache[message.get("name")].append(message.get("price"))
                                cache[message.get("name")].append(message.get("quantity"))
                                lockCache.release()
                            payload = json.dumps({"data":{"name":message.get("name"),"price":message.get("price"),"quantity":message.get("quantity")}})
                        else:
                            payload = json.dumps({"data": {"code": message.get("code"),
                                                           "message": message.get("message")}})

                        # Format an HTTP message with the payload we built and send to client
                        c.send(response.format(status_code=1,
                                               status_message="Get method success",
                                               content_length=len(payload),
                                               payload=payload)
                               .encode("utf-8"))

                # Check if the request is to get order details of an order number
                if request_path == '/orders':
                    # Check if the url has order_number parameter when try to do a 'GET' request
                    if request_query_json.get("order_number") is None:
                        payload = json.dumps({"error": {"code": 404, "message": "{order_number} parameter missing"}})
                        c.send(response.format(status_code=404,
                                               status_message="{order_number} parameter missing",
                                               content_length=len(payload),
                                               payload=payload)
                               .encode("utf-8"))
                        continue
                    else:
                        # Build a request to the orders service
                        data["type"] = "get"
                        data["order_number"] = request_query_json.get("order_number")

                        # Start communication with Orders Service
                        orders = socket.socket()
                        host = "127.0.0.1"

                        # Locking since we are using leader node port which is a shared memory space
                        lockLeaderNode.acquire()

                        # Setting the port to leader node port
                        port = leaderNodePort
                        try:
                            # Trying to connect to leader node order service
                            orders.connect((host, port))
                        except socket.error as msg:
                            # We come here if the leader node is down
                            # Now we do leader node election and set the global leader node port
                            leaderNodePort = leaderElection()
                            orders.connect((host, port))
                        lockLeaderNode.release()

                        # Send request to the leader node for order details
                        orders.send(json.dumps(data).encode('utf-8'))
                        message = orders.recv(1024)
                        orders.close()

                        message = json.loads(message)

                        # Process the information we received from the leader node and build payload we need to send to the client
                        if message.get("code") == 1:
                            payload = json.dumps({"data": {"order_number": message.get("order_number"), "name": message.get("name"),
                                                           "quantity": message.get("quantity")}})
                        else:
                            payload = json.dumps({"data": {"code": message.get("code"),
                                                           "message": message.get("message")}})

                        # Format a HTTP message with the payload we built and send to client
                        c.send(response.format(status_code=1,
                                               status_message="Get method success",
                                               content_length=len(payload),
                                               payload=payload)
                               .encode("utf-8"))

            # We come here if the request is a POST request
            if request_type == 'POST':

                # Additional check to see the data type of the request_query_json
                if isinstance(request_body_json,str):
                    request_body_json = json.loads(request_body_json)

                # Check if the raw JSON sent by the client has both name and quantity attributes for the 'POST' request
                if request_body_json.get("name") is None or request_body_json.get("quantity") is None:
                    payload = json.dumps({"error": {"code": 404, "message": "name or quantity parameter missing in raw json file"}})
                    c.send(response.format(status_code=404,
                                           status_message="name or quantity parameter missing in raw json file",
                                           content_length=len(payload),
                                           payload=payload)
                            .encode("utf-8"))
                    continue
                else:

                    product_name = request_body_json.get("name")

                    # If everything is good then proceed to execute the request

                    # Form a dictionary with the data we need to communicate with Orders
                    data["type"] = "post"
                    data["name"] = product_name
                    data["quantity"] = request_body_json.get("quantity")

                    # Form a connection with orders and send the request with above dictionary
                    orders = socket.socket()
                    host = "127.0.0.1"

                    # Locking because we are accessing leader node port (shared memory space)
                    lockLeaderNode.acquire()
                    port = leaderNodePort
                    try:
                        # Trying to the leader node order service
                        orders.connect((host, port))
                    except socket.error as msg:
                        # If leader node is down, do the leader election again
                        leaderNodePort = leaderElection()
                        orders.close()

                        # Start a connection with the newly elected leader node
                        orders = socket.socket()
                        orders.connect((host, leaderNodePort))
                    lockLeaderNode.release()

                    # Sending and receiving the data to leader node
                    orders.send(json.dumps(data).encode('utf-8'))
                    resp = orders.recv(1024)
                    orders.close()

                    message = json.loads(resp)

                    # Analyze the response from the orders service and build the payload to the client
                    if message.get("code") == 1:
                        # Check if cache is enabled
                        if cacheFlag:
                            # Locking since we are reading/writing cache which is a shared memory space
                            lockCache.acquire()

                            # If the order is successful we need to remove it from cache
                            if product_name in cache:
                                del cache[product_name]
                            lockCache.release()
                        payload = json.dumps({"data":{"order_number":message.get("order_number")}})
                    else:
                        payload = json.dumps({"data": {"code": message.get("code"),
                                                       "message": message.get("message")}})

                    # Format a HTTP message with the payload we built and send to client
                    print('I am sending: ', payload)
                    c.send(response.format(status_code=1,
                                           status_message="Post method success",
                                           content_length=len(payload),
                                           payload=payload)
                           .encode("utf-8"))

    # Close the socket after coming out of the while loop
    c.close()


def main():
    global portsOfOrderServices
    global idsOfOrderServices
    global leaderNodePort
    global cacheFlag

    # Reading all order service port numbers and their id's from command line
    if len(sys.argv) > 1:
        portsOfOrderServices.append(int(sys.argv[1]))
    if len(sys.argv) > 2:
        idsOfOrderServices.append(int(sys.argv[2]))
    if len(sys.argv) > 3:
        portsOfOrderServices.append(int(sys.argv[3]))
    if len(sys.argv) > 4:
        idsOfOrderServices.append(int(sys.argv[4]))
    if len(sys.argv) > 5:
        portsOfOrderServices.append(int(sys.argv[5]))
    if len(sys.argv) > 6:
        idsOfOrderServices.append(int(sys.argv[6]))

    # This command line parameter is to disable the cache
    if len(sys.argv) > 7:
        disableFlag = sys.argv[7].upper()
        if disableFlag == 'N':
            cacheFlag = False

    # Sorting the ports based on the id's
    # Port with the highest id will at the end of the list
    portsOfOrderServices.sort(key=dict(zip(portsOfOrderServices, idsOfOrderServices)).get)
    idsOfOrderServices.sort()
    print(portsOfOrderServices, idsOfOrderServices)

    # Doing leader node election and setting the global leaderNodePort
    leaderNodePort = leaderElection()
    print('leaderNodePort: ', leaderNodePort)

    host = "127.0.0.1"
    port = 8000

    # Binding the socket to a port and starting the server
    s = socket.socket()
    s.bind((host, port))

    print("socket binded to port", port)
    # put the socket into listening mode
    s.listen(100000)
    print("socket is listening")

    # Create a new lock for cache (shared memory space)
    lockCache = threading.Lock()

    # Create a new lock for leaderNodePort (Shared memory space)
    lockLeaderNode = threading.Lock()

    # Created a threadpool
    executor = ThreadPoolExecutor(max_workers=10)

    # A forever loop that keeps accepting connections
    while True:
        # Establish connection with client
        c, addr = s.accept()
        print("Connected to :", addr[0], ":", addr[1])

        # Assign new thread to process the client/catalog's requests
        executor.submit(threaded, c, lockCache, lockLeaderNode)


if __name__ == "__main__":
    main()