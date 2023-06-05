import sys
import time

from client import client

import matplotlib.pyplot as plt

if __name__ == '__main__':

    # Defining default values for buy probability and hostname of the frontend service
    hostName = '127.0.0.1'
    numClients = 5

    # Read command line parameters and override the default values of
    # hostName and probability
    if len(sys.argv) > 1:
        hostName = sys.argv[1]

    latency = {}

    # Ranging the buy probability from 0 to 0.8
    for prob in range(5):

        print('\n------------------------Buy Probability = {prob}-------------------- \n'.format(prob=prob*0.2))
        testClient = client(numClients, prob*0.2, hostName)
        testClient.runClients()
        print('Latency for each client: ', testClient.requestLatencyArray)
        print('Average request latency when clients are run with buy probability: {prob} = '.format(prob=prob*0.2),
              testClient.averageLatency)
        latency[prob*0.2] = testClient.averageLatency
        if prob != 4:
            time.sleep(10)
    print('\n\n')

    print('Latency map for various probabilities: {map}'.format(map=latency))

    # Plotting the graph of latency wrt number of clients
    plt.grid(True)
    plt.plot(*zip(*sorted(latency.items())))
    plt.plot(color='maroon', marker='o')
    plt.xlabel('Probability of buy requests')
    plt.ylabel('Average latency per request - 5 Clients (ms)')
    plt.show()


