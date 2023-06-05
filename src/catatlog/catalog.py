import time
from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import json

def processRequest(c, lock, isRestockThread = False):

    # Check if this thread is solely for restock
    if isRestockThread:
        while 1==1:

            # Comes here every 10 seconds to restock the database
            # Locking since we are reading database which is a shared memory space
            lock.acquire()
            print('\nI am here to Restock')
            isRestock = False
            restockToyList = []
            for toy in data_dict['name']:
                index = data_dict['name'].index(toy)
                if data_dict['quantity'][index] == 0:
                    isRestock = True
                    data_dict['quantity'][index] = 100
                    restockToyList.append(toy)
            print('Did restock happen: ', isRestock)
            if isRestock:
                with open("data/toyStoreData.json", "w") as toyStoreFile:
                    json.dump(data_dict, toyStoreFile)
                toyStoreFile.close()
            lock.release()

            if isRestock:
                resp = {}
                resp['code'] = 1
                resp['message'] = 'Restock'
                resp['restockToyList'] = restockToyList
                print('Toys that are restocked: {restockToyList}\n'.format(restockToyList=restockToyList))

                # Communicating with the frontendservice about the restock information
                frontendservice = socket.socket()
                host = "127.0.0.1"
                port = 8000
                try:

                    # Trying to connect to frontendservice
                    frontendservice.connect((host, port))
                    frontendservice.send(json.dumps(resp).encode('utf-8'))
                    message = frontendservice.recv(1024)
                except socket.error as msg:
                    print('Frontendservice is down to send the restock request')

            # Sleeping for 10seconds
            time.sleep(10)
        frontendservice.close()

    else:
        # Receiving the request either from frontend service or orders service
        data = c.recv(1024)
        data = json.loads(data)

        # Processing request from frontend service
        if (data["type"] == 'get') :

            # Check if the Toy exists in the database
            if data["name"] in data_dict['name']:

                # Building the response dictionary
                resp = {}
                index = data_dict['name'].index(data['name'])
                resp["name"] = (data_dict['name'][index])
                resp["price"] = (data_dict['price'][index])
                resp["code"] = 1

                # Make sure that no thread is reading or writing to the quantity
                # while this thread is reading the quantity
                lock.acquire()
                resp["quantity"] = (data_dict['quantity'][index])
                lock.release()

                print('Response to frontendservice', resp)
                result = json.dumps(resp).encode('utf-8')

                # Send the response back to frontend service
                c.send(result)
            else:
                # Form an error message with 'Product not found'
                resp = {"code": 404, "message": "product not found"}

                print('Response to frontendservice: ', resp)
                result = json.dumps(resp).encode('utf-8')

                # Send the response back to frontend service
                c.send(result)

        if(data["type"] == 'post'):

            # Check if the Toy exists in the database
            if data["name"] in data_dict['name']:

                # Building the response dictionary
                resp = {}
                index = data_dict['name'].index(data['name'])

                # Acquire the lock because all the threads will be accessing
                # modifying the shared resources memory and database
                lock.acquire()
                quantity = (data_dict['quantity'][index])

                # Check if available quantity greater than the requested quantity
                if quantity >= data['quantity']:

                    # Write to the memory
                    data_dict['quantity'][index] -= data['quantity']
                    # Write to the database
                    with open("data/toyStoreData.json", "w") as toyStoreFile:
                        json.dump(data_dict,toyStoreFile)
                    toyStoreFile.close()

                    resp["code"] = 1
                else:

                    # Send an error message with 'Stock Over'
                    resp["code"] = 404
                    resp["message"] = 'Stock Over'
                lock.release()

                print('Response to frontendservice: ', resp)
                result = json.dumps(resp).encode('utf-8')

                # Send the response back to orders service
                c.send(result)
            else:
                # Form an error message with 'Product not found'
                resp = {"code": 404, "message": "product not found"}

                print('Response to frontendservice: ', resp)
                result = json.dumps(resp).encode('utf-8')

                # Send the response back to orders service
                c.send(result)

        c.close()
        print('Request is processed')
def run():

    host = "127.0.0.1"
    port = 9001

    # Bind the socket to the host and port
    s = socket.socket()
    s.bind((host, port))
    print("socket catalog binded to port", port)

    # put the socket into listening mode
    s.listen(100000)
    print("socket catalog is listening")

    # create a threadpool
    executor = ThreadPoolExecutor(max_workers=10)

    # Creating a lock object to pass it to the threads inorder to protect the critical region
    lock = threading.Lock()
    executor.submit(processRequest, None, lock, isRestockThread=True)

    while True:
        # Accept the requests either from frontend or orders services
        c, addr = s.accept()

        print("Connected to :", addr[0], ":", addr[1])

        # Assign a thread to process the request
        executor.submit(processRequest, c, lock)
if __name__ == '__main__':

    # Reads the database and gets it to memory as soon the service is initiated
    datafile = open('data/toyStoreData.json')
    data_dict = json.load(datafile)
    datafile.close()
    run()