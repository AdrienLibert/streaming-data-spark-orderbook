from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import from_json, col, current_timestamp

spark = SparkSession \
    .builder \
    .appName("KafkaStreaming") \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5') \
    .getOrCreate()

kafka_options = {
    "kafka.bootstrap.servers": "bitnami-kafka.orderbook.svc.cluster.local:9092",
    "startingOffsets": "latest",
    "subscribe": "trades.topic"
}

df = spark.readStream.format("kafka").options(**kafka_options).load()

json_schema = StructType([
    StructField("trade_id", StringType(), True),
    StructField("order_id", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("price", DoubleType(), True),
    StructField("action", StringType(), True),
    StructField("status", StringType(), True),
    StructField("timestamp", IntegerType(), True)
])

json_df = df.selectExpr("CAST(value AS STRING) AS value")

df_final = json_df.select(from_json(col("value"), json_schema).alias("trades")) \
                  .select("trades.*") \
                  .filter(col("quantity") != 0) \
                  .withColumn("processing_timestamp", current_timestamp())

df_final.writeStream.format("console").outputMode("append").start().awaitTermination()

# Write to console
console_query = trades_df.writeStream \
    .format("console") \
    .outputMode("append") \
    .start()

write_to_postgres = batch_df.write \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://postgres-postgresql.analytics.svc.cluster.local:5432/analytics") \
    .option("user", "postgres") \
    .option("password", "postgres") \
    .option("dbtable", "trades") \
    .option("driver", "org.postgresql.Driver") \
    .mode("append") \
    .save()

# Write to PostgreSQL
postgres_query = trades_df.writeStream \
    .foreachBatch(write_to_postgres) \
    .outputMode("append") \
    .start()

spark.streams.awaitAnyTermination()