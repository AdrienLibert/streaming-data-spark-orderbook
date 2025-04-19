from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType
from pyspark.sql.functions import from_json, col, current_timestamp, window, first, last, max, min, sum

spark = SparkSession \
    .builder \
    .appName("KafkaStreamingCandlesticks") \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5,org.postgresql:postgresql:42.2.5') \
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
df_trades = json_df.select(from_json(col("value"), json_schema).alias("trades")) \
    .select("trades.*") \
    .filter(col("quantity") != 0) \
    .withColumn("processing_timestamp", current_timestamp()) \
    .withColumn("trade_timestamp", col("timestamp").cast("timestamp")) \
    .withWatermark("trade_timestamp", "10 seconds")

df_candlesticks = df_trades \
    .groupBy(window(col("trade_timestamp"), "10 seconds")) \
    .agg(
    first("price").alias("open"),
    last("price").alias("close"),
    max("price").alias("high"),
    min("price").alias("low"),
    sum("quantity").alias("volume")
) \
    .select(
    col("window.start").alias("timestamp"),
    col("open"),
    col("close"),
    col("high"),
    col("low"),
    col("volume")
)

def write_candlesticks(df, epoch_id):
    try:
        existing_timestamps = spark.read \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres-postgresql.analytics.svc.cluster.local:5432/analytics") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", "candlesticks") \
            .option("user", "postgres") \
            .option("password", "postgres") \
            .load() \
            .select("timestamp")

        df_new = df.join(existing_timestamps, "timestamp", "left_anti")

        df_new.write \
            .mode("append") \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres-postgresql.analytics.svc.cluster.local:5432/analytics") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", "candlesticks") \
            .option("user", "postgres") \
            .option("password", "postgres") \
            .save()
    except Exception as e:
        print(f"Error writing candlestick batch {epoch_id}: {str(e)}")
        raise

query = df_candlesticks.writeStream \
    .foreachBatch(write_candlesticks) \
    .option("checkpointLocation", "/tmp/spark-checkpoint") \
    .trigger(processingTime="10 seconds") \
    .start()

spark.streams.awaitAnyTermination()