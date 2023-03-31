# NoobCash 
## A humble project about cryptocurrency and blockchain

### Project for the course of distributed systems...

### How to use (only locally)

First configure the appropriate configuration in the src/config.py

- N: number of nodes (also miners)
- CAPACITY: number of transactions needed to mine a block
- MINING_DIFFICULTY: number of zeros for the hash of a block mine to mine

Use the following to see all functionalities:
```python ./src/main.py -h``` 

To generate the experiments located in the transactions folder (transactions.tar.gz)
``python ./src/main.py -tf``
