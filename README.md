Distributed and Operating Systems

Caching, Replication and Fault Tolerance

## Goals and Learning Outcomes

We have implemented this application to have an understanding about:

* Caching, replication, and consistency.
* Concepts of fault tolerance and high availability.
* Deploying the application on the cloud.

## Lab Description

We have implemented the application with the below requirements:

1.  The toy store application consists of three microservices: a front-end service, a catalog
    service, and an order service.

2.  The front-end service exposes the following REST APIs as they were defined in lab2:

    *   `GET /products/<product_name>`
    *   `POST /orders`

    In addition, the front-end service will provide a new REST API that allows clients to query
    existing orders:

    *   `GET /orders/<order_number>`

        This API returns a JSON reply with a top-level `data` object with the three fields:
        `number`, `name`, and `quantity`. If the order number doesn't exist, a JSON reply with a
        top-level `error` object should be returned. The `error` object should contain two fields:
        `code` and `message`


3.  Each microservice should be able to handle requests concurrently. You can use any concurrency models
    covered in class.

4.  Added some variety to the toy offering by initializing the catalog with at least 10 different
    toys. Each toy should have an initial stock of 100. Also the catalog service will periodically 
    restock the toys that are out of stock. The catalog service should check remaining quantity of
    every toy every 10 seconds, if a toy is out of stock the catalog service will restock it to 100.

5.  The client first queries the front-end service with a random toy. If the returned quantity is
    greater than zero, with probability p it will send an order request (make p an variable that's
    adjustable). You can decide whether the the toy query request and the order request uses the
    same connection. The client will repeat for a number of iterations, and record the the order
    number and order information if a purchase request was successful. Before exiting, the client
    will retrieve the order information of each order that was made using the order query request,
    and check whether the server reply matches the locally stored order information.

## Part 1: Caching

In this part we will add caching to the front-end service to reduce the latency of the toy query
requests. The front-end server start with an empty in-memory cache. Upon receiving a toy query
request, it first checks the in-memory cache to see whether it can be served from the cache. If not,
the request will then be forwarded to the catalog service, and the result returned by the catalog
service will be stored in the cache.

Cache consistency needs to be addressed whenever a toy is purchased or restocked. You should
implement a server-push technique: catalog server sends invalidation requests to the front-end
server after each purchase and restock. The invalidation requests cause the front-end service to
remove the corresponding item from the cache.

## Part 2: Replication

To make sure that our toy store doesn't lose any order information due to crash failures, we want to
replicate the order service. When you start the toy store application, you should first start the
catalog service. Then you start three replicas of the order service, each with a unique id number
and its own database file. There should always be 1 leader node and the rest are follower nodes. 
Front-end service will always try to pick the node with the highest id number as the leader.

When the front-end service starts, it will read the id number and address of each replica of the
order service (this can be done using configuration files/environment variables/command line
parameters). It will ping (here ping means sending a health check request rather than the `ping`
command) the replica with the highest id number to see if it's responsive. If so it will notify all
the replicas that a leader has been selected with the id number, otherwise it will try the replica
with the second highest id number. The process repeats until a leader has been found.

When a purchase request or an order query request, the front-end service only forwards the request
to the leader. In case of a successful purchase (a new order number is generated), the leader node
will propagate the information of the new order to the follower nodes to maintain data consistency.

## Part 3: Fault Tolerance

In this part we will handle failures of the order service. In this we dealt with crash failure 
tolerance rather than Byzantine failure tolerance.

First We want to make sure that when any replica crashes (including the leader), toy purchase
requests and order query requests can still be handled and return the correct result. To achieve
this, when the front-end service finds that the leader node is unresponsive, it will redo the leader
selection algorithm as described in [Part2](#part-2-replication).

We also want to make sure that when a crashed replica is back online, it can synchronize with the
other replicas to retrieve the order information that it has missed during the offline time. When a
replica came back online from a crash, it will look at its database file and get the latest order
number that it has and ask the other replicas what orders it has missed since that order number.

## Part 4: Testing and Evaluation with Deployment on AWS

First, we have written some simple test cases to verify that the code works as expected. We tested both
each individual microservice as well as the whole application. The test cases and test
output are present in a test directory.

Next, we deployed the application on an `m5a.xlarge` instance in the `us-east-1` region on AWS. 
We ran 5 clients on the local machine. Measured the latency seen by each client for different 
type requests. We have changed the probability p of a follow up purchase request from 0 to 80%, 
with an increment of 20%, and recorded the result for each p setting.
Made simple plots showing the values of p on the X-axis and the latency of different types of
request on the y-axis. We did the same experiments but with caching turned off, estimated how much
benefits does caching provide by comparing the results.

Finally, we simulated crash failures by killing a random order service replica while the clients is
running, and then brought it back online after some time. Repeated this experiment several times and
made sure that we test the case when the leader is killed. 

## Code base

 We have kept the source code for both parts separately. Inside the src directory, we
 have a separate folder for each component/microservice, e.g., a `client` folder for client
code, a `front-end` folder for the front-end service, etc.
