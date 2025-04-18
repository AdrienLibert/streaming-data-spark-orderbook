from pyspark.sql import SparkSession

spark = SparkSession \
    .builder \
    .appName("KafkaStreaming") \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5') \
    .getOrCreate()

kafka_options = {
    "kafka.bootstrap.servers": "bitnami-kafka.orderbook.svc.cluster.local:9092",
    "startingOffsets": "earliest",
    "subscribe": "trades.topic"
}

df = spark.readStream.format("kafka").options(**kafka_options).load()

print("Starting Kafka Spark reader...")