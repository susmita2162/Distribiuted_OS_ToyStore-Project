import random
import time
import unittest
import socket
import json

class Testcases(unittest.TestCase):

    #Placing an order for a certain product
    def testUpdate_PositiveCase(self):

        print('Test1')
        s_update = socket.socket()
        host ="0.0.0.0"
        port = 8000
        postJson = {'name': 'Whale', 'quantity': 1 }
        postRequest = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        s_update.connect((host, port))
        s_update.send(postRequest.encode('utf-8'))
        data = s_update.recv(1024).decode('utf-8')
        print('Testing for Placing an order for a certain product', data)
        s_update.close()
    
    #Placing an order for a certain product with a quantity higher than in the toy store
    def testUpdate_NegativeCase(self):
        print('Test2')
        s_update = socket.socket()
        host ="0.0.0.0"
        port = 8000
        postJson = {'name': 'Tux', 'quantity': 50000 }
        postRequest = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        s_update.connect((host, port))
        s_update.send(postRequest.encode('utf-8'))
        data = s_update.recv(1024).decode('utf-8')
        print('Testing for placing an order for a certain product with a quantity higher than in the toy store', data)
        s_update.close()

    # querying the details of an existing product
    def testQuery_ExistingProduct(self):
        print('Test3')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        existing_items = ['Tux', 'Whale', 'Elephant', 'Bird']
        randomItem = random.randint(0, 3)
        getRequest_existing = 'GET /products?product_name=' + existing_items[randomItem] + ' HTTP/1.1\r\n'
        s_get.connect((host, port))
        s_get.send(getRequest_existing.encode('utf-8'))
        resp_Existing = s_get.recv(1024).decode('utf-8')
        print('Testing for Querying the details of an existing product',resp_Existing)
        s_get.close()

    #Querying the details of non-existing product
    def testQuery_NonExistingProduct(self):
        print('Test4')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        # querying the details of non-existing product
        getRequest_Nonexisting ='GET /products?product_name=' + 'Ostrich' + ' HTTP/1.1\r\n'
        s_get.connect((host, port))
        s_get.send(getRequest_Nonexisting.encode('utf-8'))
        resp_Nonexisting = s_get.recv(1024).decode('utf-8')
        print('Testing for Querying the details of non-existing product',resp_Nonexisting)
        s_get.close()

    #testing invalid method call
    def test_InvalidMethod(self):
        print('Test5')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        # testing invalid method call
        existing_items = ['Tux', 'Whale', 'Elephant', 'Bird']
        randomItem = random.randint(0, 3)
        invalidMethod_Request = 'PUT /products?product_name=' + existing_items[randomItem] + ' HTTP/1.1\r\n' 
        s_get.connect((host, port))
        s_get.send(invalidMethod_Request.encode('utf-8'))
        resp_invalidMethod = s_get.recv(1024).decode('utf-8')
        print('Testing Invalid method response',resp_invalidMethod)
        s_get.close()

    #testing  invalid URL path
    def test_InvalidURLPath(self):
        print('Test6')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        # testing invalid method call
        existing_items = ['Tux', 'Whale', 'Elephant', 'Bird']
        randomItem = random.randint(0, 3)
        invalidURL_Request= 'GET /product?product_name=' + existing_items[randomItem] + ' HTTP/1.1\r\n' 
        s_get.connect((host, port))
        s_get.send(invalidURL_Request.encode('utf-8'))
        resp_invalidURL = s_get.recv(1024).decode('utf-8')
        print('Testing Invalid URL Path response',resp_invalidURL)
        s_get.close()

    #testing Invalid Resource for this Request type
    def test_InvalidResource(self):
        print('Test7')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        # testing Invalid Resource for this Request type
        existing_items = ['Tux', 'Whale', 'Elephant', 'Bird']
        randomItem = random.randint(0, 3)
        invalidResource_Request= 'GET /orders?product_name' + existing_items[randomItem] + ' HTTP/1.1\r\n' 
        s_get.connect((host, port))
        s_get.send(invalidResource_Request.encode('utf-8'))
        resp_invalidResource = s_get.recv(1024).decode('utf-8')
        print('Testing Invalid resource response',resp_invalidResource)
        s_get.close()

    #testing {quantity} parameter missing in POST method
    def testPOST_ParamMiss(self):
        
        print('Test8')
        s_update = socket.socket()
        host ="0.0.0.0"
        port = 8000
        postJson = {'name': 'Whale'}
        postRequest = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        s_update.connect((host, port))
        s_update.send(postRequest.encode('utf-8'))
        data = s_update.recv(1024).decode('utf-8')
        print('Testing for missing param in POST method', data)
        s_update.close()

    #testing parameter missing in GET method
    def testQuery_ParamMiss(self):
        print('Test9')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        existing_items = ['Tux', 'Whale', 'Elephant', 'Bird']
        randomItem = random.randint(0, 3)
        getRequest_existing = 'GET /products?' + ' HTTP/1.1\r\n'
        s_get.connect((host, port))
        s_get.send(getRequest_existing.encode('utf-8'))
        resp_Existing = s_get.recv(1024).decode('utf-8')
        print('Testing for missing param in GET method',resp_Existing)
        s_get.close()

    #testing REST API that allows to query existing orders
    def testQuery_ExistingOrders(self):
        print('Test10')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        order_num = str(10)
        
        getRequest_existing_Ord = 'GET /orders?order_number=' + order_num + ' HTTP/1.1\r\n'
        s_get.connect((host, port))
        s_get.send(getRequest_existing_Ord.encode('utf-8'))
        resp_Existing_ord = s_get.recv(1024).decode('utf-8')
        print('Testing for Querying the details of an existing order',resp_Existing_ord)
        s_get.close()

    #testing REST API that allows to query non-existing orders
    def testQuery_NonExistingOrders(self):
        print('Test11')
        s_get = socket.socket()
        host ="0.0.0.0"
        port = 8000
        order_num = str(120000)
        getRequest_NonexistingOrd = 'GET /orders?order_number=' + order_num + ' HTTP/1.1\r\n'
        s_get.connect((host, port))
        s_get.send(getRequest_NonexistingOrd.encode('utf-8'))
        resp_NonExistingOrd = s_get.recv(1024).decode('utf-8')
        print('Testing for Querying the details of a non-existing order',resp_NonExistingOrd)
        s_get.close()

    #testing replication and fault tolerance 

    def testReplication_FaultTolerance(self):
        print('Test12')
        s_update = socket.socket()
        host = "0.0.0.0"
        port = 8000
        postJson = {'name': 'Whale', 'quantity': 1 }
        # all the 3 order services are up and running
        print('Sending post request - 1')
        postRequest1 = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        s_update.connect((host, port))
        s_update.send(postRequest1.encode('utf-8'))
        data1 = s_update.recv(1024).decode('utf-8')
        print('Testing for Placing an order for a certain product when all the 3 services are up', data1)
        # killing the leader order service manually 
        time.sleep(20)
        # now only 2 order services are up and the reelection of leader node happens
        #sending a post request again
        print('Sending post request - 2')
        postRequest2 = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        s_update.send(postRequest2.encode('utf-8'))
        data2 = s_update.recv(1024).decode('utf-8')
        print('Testing for Placing an order for a certain product when 2 services are up', data2)
        # killing the leader order service again manually 
        time.sleep(20)
        # now only 1 order service is up and the reelection of leader node happens
        #sending two post requests again
        postRequest3 = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson) 
        print('Sending post request - 3')
        s_update.send(postRequest3.encode('utf-8'))
        data3 = s_update.recv(1024).decode('utf-8')
        print('Testing for Placing an order for a certain product when only 1 service is up-post once', data3)
        print('Sending post request - 4')
        s_update.send(postRequest3.encode('utf-8'))
        data4 = s_update.recv(1024).decode('utf-8')
        print('Testing for Placing an order for a certain product when only 1 service is up-post twice', data4)
        # now the order number will be order_number+2
        # killing the leader order service3 again manually and running the first service 
        time.sleep(20)
        # now only 1 order service is up and the reelection of leader node happens
        # running third order service and killing the first service 
        #sending a post request again
        print('Sending post request - 5')
        postRequest5 = 'POST /orders HTTP/1.1\r\n' + json.dumps(postJson)     
        s_update.send(postRequest5.encode('utf-8'))
        data5 = s_update.recv(1024).decode('utf-8')
        #check the order nuber now, the orderlog now for this service will be synchronized
        print('Testing for Placing an order for a certain product when only 1 service is up', data5)
        s_update.close()
    

    
if __name__ == '__main__':
    unittest.main()