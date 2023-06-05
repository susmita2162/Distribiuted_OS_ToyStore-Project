How to run the code:

Make sure you have python 3.8 installed

If at all you face any issue as 'module not found', please run:

pip3 install <module_name>


Note : Our order services run on these ports - 9000, 9002, 9003

Commands to start our service:

Frontendservice:

With Cache:

cd src/frontendservice/

cd frontendservice.py <port-1> <id-1> <port-2> <id-2> <port-3> <id-3>

Example:

python3 frontendservice.py 9000 1 9002 2 9003 3

[The above command chooses 9003 as leader node because it has the highest id]

Without Cache:

cd src/frontendservice/

cd frontendservice.py <port-1> <id-1> <port-2> <id-2> <port-3> <id-3> n

[Add an additional parameter to indicate to disable cache]

Example:

python3 frontendservice.py 9000 1 9002 2 9003 3 n

[The above command chooses 9003 as leader node because it has the highest id]


Catalog Service:

cd src/catalog.py

python3 catalog.py


Orders1 Service:

cd src/orderservice_9000

python3 orders1.py


Orders2 Service:

cd src/orderservice_9002

python3 orders2.py


Orders3 Service:

cd src/orderservice_9003

python3 orders3.py


Steps to run multiple client interfaces:

cd src/client

Client interface:

python3 client.py 

The above command does the following (No parameters passes -> Use Default parameters):

Starts 5 client threads (100 requests each), connects to host 127.0.0.1, probability (p) for buy requests = 0.75

Passing parameters through command line:

python3 client.py <aws-instance-dns-anme> <num-clients> <buy_prob>

Example:

python3 client.py ec2-3-208-22-7.compute-1.amazonaws.com 3 0.95

The above command creates three client threads (each 100 requests) which connects to ec2-3-208-22-7.compute-1.amazonaws.com and makes buy requests with a probability of 0.95


AggregateLoadTest Interface:

Running aggregateLoadTest.py which gives us the graphs we need for part 4 of the lab:

The clear description of what happens inside this file is given in the design doc.

Default values in this interface:

Host = 127.0.0.1

The below command runs on default host name mentioned above.

python3 aggregateLoadTest.py

Passing host name as command line parameter:

python3 aggregateLoadTest.py <host-name>

python3 aggregateLoadTest.py ec2-3-208-22-7.compute-1.amazonaws.com


Infinite Client interface:

python3 infiniteClient.py 

The above command does the following (No parameters passes -> Use Default parameters):

Starts 5 client threads (runs infinitely), connects to host 127.0.0.1, probability (p) for buy requests = 0.75

Passing parameters through command line:

python3 infiniteClient.py <aws-instance-dns-anme> <num-clients> <buy_prob>

Example:

python3 infiniteClient.py ec2-3-208-22-7.compute-1.amazonaws.com 3 0.95

The above command creates three client threads (runs infinitely) which connects to ec2-3-208-22-7.compute-1.amazonaws.com and makes buy requests with a probability of 0.95


