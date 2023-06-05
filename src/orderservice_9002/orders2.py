import csv
from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import json
import linecache as lc

# This stores the last order_number from the csv file
globalOrderNumber = 0


def processRequest(c, lock):
    global globalOrderNumber

    # Receiving the request from frontend service
    data = c.recv(1024)
    if not data:
        # If any service closes its socket after communication, we close our socket here
        c.close()
        return
    data = json.loads(data)

    # This is a request that comes in when one order service asks this service to transfer its data
    if data.get('messageUpdate') == 'Update File':
        # Locking to make sure this order log is not updating while this service is transferring its data
        lock.acquire()
        # We only transfer the data from the order number that a service requests
        from_order_number = data.get('from_order_number')
        lineNumber = from_order_number + 1
        lc.clearcache()
        responseMessage = (lc.getline('data/orderlog2.csv', lineNumber)).strip()
        lineNumber += 1
        if responseMessage != '':
            responseMessage += ':'
            while 1 == 1:
                temp = (lc.getline('data/orderlog2.csv', lineNumber)).strip()
                if temp == '':
                    break
                # Appending all the log data with a ':' seperated string
                responseMessage += temp + ':'
                lineNumber += 1

            # Forming a response message
            responseMessage = responseMessage[:-1]
            responseMessage = responseMessage.encode('utf-8')

            # Breaking the appended string to chunks of 1024 bytes and sending them in a for loop
            responseMessages = [responseMessage[i:i + 1024] for i in range(0, len(responseMessage) - 1, 1024)]
            for message in responseMessages:
                c.send(message)

            c.send('null'.encode('utf-8'))
            response = c.recv(1024)
            if not response:
                c.close()
        else:
            c.send('null'.encode('utf-8'))
            response = c.recv(1024)
            if not response:
                c.close()

        # Releasing the lock for other requests to edit the order log
        lock.release()
        return

    # This is a request that comes in when the leader node sends data to update each order request
    if data.get('messageUpdate') == 'Update Line' and data.get('code') == 1:

        # Locking to make sure that order log is not updated simultaneously by other threads
        lock.acquire()
        # Assigning globalOrderNumber to the latest order number
        globalOrderNumber = data.get('order_number')

        # Adding data to the log
        with open('data/orderlog2.csv', 'a+', newline='') as orderlog:
            header_key = ['order_no', 'Product', 'quantity']
            value = csv.DictWriter(orderlog, fieldnames=header_key)
            value.writerow({'order_no': globalOrderNumber, 'Product': data.get('name'),
                            'quantity': data.get('quantity')})
        orderlog.close()
        c.close()

        # Releasing lock
        lock.release()
        return

    # This is a request that comes in, when this service is a leader node and frontend asks for details of order_number
    if data.get('type') == 'get':
        order_number = int(data.get('order_number'))
        resp = {}

        # Locking since we are trying to read shared memory globalOrderNumber
        lock.acquire()

        # Return error message if order_number does not exist in the log
        if order_number > globalOrderNumber:
            resp['code'] = 404
            resp['message'] = 'Invalid order_number'
        else:

            # Read the order log and return the data in that line
            with open('data/orderlog2.csv') as orderlog:
                line = orderlog.readlines()[order_number]
            line = line.split(',')

            # Building the response
            resp['code'] = 1
            resp['order_number'] = int(line[0])
            resp['name'] = line[1]
            resp['quantity'] = int(line[2])
        lock.release()

    else:
        # We come here when this is a leader node, and it gets an order request
        # Making a connection to the catalog and sending the request we got from the frontend

        print('I am the leader node now. I am ordering')

        # Communicating with Catalog
        catalog = socket.socket()
        host = "127.0.0.1"
        port = 9001
        catalog.connect((host, port))

        print('Message to Catalog: ', data)
        catalog.send(json.dumps(data).encode('utf-8'))
        message = catalog.recv(1024)
        catalog.close()

        # Formatting the message from the catalog as a dictionary
        message = json.loads(message)
        print('Message received from Catalog: ', message)

        # Getting data from the message sent by the frontend service
        name = data.get("name")
        quantity = data.get("quantity")

        # Building the response that needs to be sent to the frontend service
        resp = {}

        # Processing the response based on the reply we heard from catalog
        if message.get("code") == 1:
            resp["code"] = 1

            # Making sure that shared memory variables and files are read and modified
            # by one thread at a time
            lock.acquire()

            # Incrementing globalOrderNumber
            globalOrderNumber += 1

            # Adding data to the log
            with open('data/orderlog2.csv', 'a+', newline='') as orderlog:
                header_key = ['order_no', 'Product', 'quantity']
                value = csv.DictWriter(orderlog, fieldnames=header_key)
                value.writerow({'order_no': globalOrderNumber, 'Product': name,
                                'quantity': quantity})
            orderlog.close()

            resp["order_number"] = globalOrderNumber

            # After the update of the log, this service sends that data to other services to update their logs
            hostOrderService = "127.0.0.1"
            try:
                # Trying to connect to one order service
                orderService = socket.socket()
                port = 9000
                orderService.connect((hostOrderService, port))

                # Sending the message to update one line in its order log
                resp['messageUpdate'] = 'Update Line'
                resp['name'] = name
                resp['quantity'] = quantity
                orderService.send(json.dumps(resp).encode('utf-8'))
                response = orderService.recv(1024)
                if not response:
                    orderService.close()
            except socket.error as msg:

                # Gracefully handle if that order service is down
                orderService.close()
                print('Order Service 9000 is down')
            try:

                # Trying to connect to another order service
                orderService = socket.socket()
                port = 9003
                orderService.connect((hostOrderService, port))

                # Sending the message to update one line in its order log
                resp['messageUpdate'] = 'Update Line'
                resp['name'] = name
                resp['quantity'] = quantity
                orderService.send(json.dumps(resp).encode('utf-8'))
                response = orderService.recv(1024)
                if not response:
                    orderService.close()
            except socket.error as msg:

                # Gracefully handle if that order service is down
                orderService.close()
                print('Order Service 9003 is down')
            lock.release()
        else:

            # If the request failed, send the error code and message
            # to the frontend service
            resp["code"] = message.get("code")
            resp["message"] = message.get("message")

    # Sending the response to frontend service
    print('Sending response to frontend: ', resp)
    c.send(json.dumps(resp).encode('utf-8'))
    c.close()
    print('Request is processed')


def run():
    global globalOrderNumber
    host = "127.0.0.1"

    # Setting a default leader node port
    leaderNodePort = 9000
    pingFrontEnd = {}
    pingFrontEnd['message'] = 'Get Leader'
    frontendservice = socket.socket()
    port = 8000
    try:
        # We ask the frontend service for the leader node and use it to get the data
        # Trying to connect to frontendservice
        frontendservice.connect((host, port))
        frontendservice.send(json.dumps(pingFrontEnd).encode('utf-8'))
        message = frontendservice.recv(1024)
        message = json.loads(message)
        leaderNodePort = message.get("leaderNodePort")
        print('Leader Node Port: ', leaderNodePort)
        frontendservice.close()
    except socket.error as msg:
        print('Frontendservice is down to find the leader node.')

    # Bind the socket to the host and port
    s = socket.socket()

    resp = {}
    hostOrderService = "127.0.0.1"

    # As soon as we start the service, we should get the data from the service that is already running
    try:

        # Trying to connect to one of the order services for data transfer
        orderService = socket.socket()
        port = leaderNodePort
        orderService.connect((hostOrderService, port))

        # Asking for all its data from our last order_number
        resp['messageUpdate'] = 'Update File'
        resp['from_order_number'] = globalOrderNumber + 1

        orderService.send(json.dumps(resp).encode('utf-8'))
        lines = ''

        # Receiving and processing all the 1024 chunks of data
        while 1 == 1:
            response = orderService.recv(1024)
            response = response.decode('utf-8')

            if response == 'null':
                break
            elif response.endswith('null'):
                lines += response[: -4]
                break
            lines += response

        # Updating our log file with the data received
        if lines != '':
            lines = lines.split(':')
            with open('data/orderlog2.csv', 'a+', newline='') as orderlog:
                header_key = ['order_no', 'Product', 'quantity']
                value = csv.DictWriter(orderlog, fieldnames=header_key)

                for line in lines:
                    values = line.split(',')
                    value.writerow({'order_no': int(values[0]), 'Product': values[1],
                                    'quantity': int(values[2])})
                    globalOrderNumber += 1
            orderlog.close()

        # put the socket into listening mode
        s.bind((host, 9002))
        s.listen(100000)
        print("socket order service is listening")
        orderService.close()
    except socket.error as msg:

        # We come here if the leader node order service is down by the time we try to connect.
        # We then try to ask other order service for data
        try:

            # Trying to connect to another order service for data
            orderService = socket.socket()
            if leaderNodePort == 9000:
                port = 9003
            elif leaderNodePort == 9003:
                port = 9000
            else:
                # This means both other order services are down, and we go to the next except block
                port = 1
            orderService.connect((hostOrderService, port))

            # Asking for all its data from our last order_number
            resp['messageUpdate'] = 'Update File'
            resp['from_order_number'] = globalOrderNumber + 1

            orderService.send(json.dumps(resp).encode('utf-8'))
            lines = ''

            # Receiving and processing all the 1024 chunks of data
            while 1 == 1:
                response = orderService.recv(1024)
                response = response.decode('utf-8')

                if response == 'null':
                    break
                elif response.endswith('null'):
                    lines += response[: -4]
                    break
                lines += response

            # Updating our log file with the data received
            if lines != '':
                lines = lines.split(':')
                with open('data/orderlog2.csv', 'a+', newline='') as orderlog:
                    header_key = ['order_no', 'Product', 'quantity']
                    value = csv.DictWriter(orderlog, fieldnames=header_key)

                    for line in lines:
                        values = line.split(',')
                        value.writerow({'order_no': int(values[0]), 'Product': values[1],
                                        'quantity': int(values[2])})
                        globalOrderNumber += 1
                orderlog.close()

            # put the socket into listening mode
            s.bind((host, 9002))
            s.listen(100000)
            print("socket order service is listening")
            orderService.close()
        except socket.error as msg:
            # put the socket into listening mode
            s.bind((host, 9002))
            s.listen(100000)
            print("socket order service is listening")

            # We come here when both the other services are also down
            # That means this is the first order service to start
            print('No other order service is up inorder to sync the data')

    # create a threadpool
    executor = ThreadPoolExecutor(max_workers=10)

    # Creating a lock object to pass it to the threads inorder to protect the critical region
    lock = threading.Lock()

    while True:
        # After updating our log file, now we start accepting requests and enter the thread pool
        # Accept requests from the frontend service
        c, addr = s.accept()
        print("Connected to :", addr[0], ":", addr[1])

        # Assign a thread to process the request
        executor.submit(processRequest, c, lock)


if __name__ == '__main__':

    # Reading the orders log and get last order number
    with open('data/orderlog2.csv', 'r') as f:
        for line in f:
            pass
        last_line = line
    f.close()

    # Initializing globalOrderNumber with the latest order number
    if (last_line.split(',')[0]) == 'order_no':
        globalOrderNumber = 0
    else:
        globalOrderNumber = int(last_line.split(',')[0])
    run()
