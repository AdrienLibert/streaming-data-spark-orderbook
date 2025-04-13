# Real-Time OrderBook Analytics

This repository provides a streaming analytics pipeline using Apache Spark, 
powered by an orderbook data generator from [AdrienLibert/orderbook](https://github.com/AdrienLibert/orderbook). 

The orderbook project data generator was developed in collaboration with [@ShikoteiCoding](https://github.com/ShikoteiCoding).

## Installation

### Dependencies

Install the required dependencies with the following commands:

```
make helm
make build_deps
```

### Start Spark

Launch the spark service:

```
make start
```



### Stop Spark

Stop the spark service:

```
make stop
```