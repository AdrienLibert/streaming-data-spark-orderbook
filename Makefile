helm:
	helm repo add bitnami https://charts.bitnami.com/bitnami
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	curl -L -H "Accept: application/vnd.github.VERSION.raw" https://api.github.com/repos/AdrienLibert/orderbook/contents/chart.zip\?ref\=clean-repo-for-chart-only-purpose --output chart.zip
	unzip chart.zip -d .

clear_helm:
	helm repo remove flink-operator-repo
	helm repo remove prometheus-community

start_kafka:
	helm install bitnami bitnami/kafka --version 31.0.0 -n orderbook --create-namespace -f helm/kafka/values-local.yaml

stop_kafka:
	helm uninstall --ignore-not-found bitnami -n orderbook

build_deps: # TODO: change to main branch after orderbook repo is clean
	docker build https://github.com/AdrienLibert/orderbook.git#clean-repo-for-chart-only-purpose:src/kafka_init -t local/kafka-init
	docker build https://github.com/AdrienLibert/orderbook.git#clean-repo-for-chart-only-purpose:src/orderbook -t local/orderbook
	docker build https://github.com/AdrienLibert/orderbook.git#clean-repo-for-chart-only-purpose:src/traderpool -t local/traderpool

start_spark:
	helm install spark-operator spark-operator/spark-operator --namespace spark-operator --create-namespace --wait
	kubectl apply -f k8s/spark/

stop_spark:
	helm uninstall --ignore-not-found spark-operator -n spark-operator

start: start_kafka start_spark
	helm install orderbook chart/ --namespace orderbook -f helm/orderbook/values-local.yaml

stop: stop_kafka stop_spark
	helm uninstall --ignore-not-found orderbook --namespace orderbook