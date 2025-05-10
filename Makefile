helm:
	helm repo add bitnami https://charts.bitnami.com/bitnami
	helm repo add grafana https://grafana.github.io/helm-charts
	helm repo add spark-operator https://kubeflow.github.io/spark-operator
	curl -L -H "Accept: application/vnd.github.VERSION.raw" https://api.github.com/repos/AdrienLibert/orderbook/contents/chart.zip\?ref\=clean-repo-for-chart-only-purpose --output chart.zip
	unzip chart.zip -d .

clear_helm:
	helm repo remove bitnami
	helm repo remove prometheus-community

start_kafka:
	helm install bitnami bitnami/kafka --version 31.0.0 -n orderbook --create-namespace -f helm/kafka/values-local.yaml

stop_kafka:
	helm uninstall --ignore-not-found bitnami -n orderbook

build_deps:
	docker build https://github.com/AdrienLibert/orderbook.git#main:src/kafka_init -t local/kafka-init
	docker build https://github.com/AdrienLibert/orderbook.git#main:src/orderbook -t local/orderbook
	docker build https://github.com/AdrienLibert/orderbook.git#main:src/traderpool -t local/traderpool
	docker build --no-cache -t local/spark:3.5.5 -f src/spark/Dockerfile src

start_spark_operator:
	helm install spark-operator spark-operator/spark-operator --namespace spark-operator --create-namespace --wait -f helm/spark_operator/values-local.yaml

stop_spark_operator:
	helm uninstall --ignore-not-found spark-operator -n spark-operator

start: start_kafka start_spark_operator
	helm install my-grafana grafana/grafana -n analytics -f helm/grafana/values-local.yaml
	kubectl apply -f k8s/grafana -n analytics
	helm install orderbook chart/ --namespace orderbook -f helm/orderbook/values-local.yaml
	kubectl create secret generic postgres --from-literal=password=postgres --from-literal=postgres-password=postgres --dry-run -o yaml | kubectl apply -f -
	helm install postgres oci://registry-1.docker.io/bitnamicharts/postgresql -n analytics --create-namespace -f helm/postgres/values-local.yaml
	kubectl apply -f k8s/spark/

stop: stop_kafka stop_spark_operator
	helm uninstall --ignore-not-found my-grafana -n analytics
	kubectl delete --ignore-not-found service grafana-service -n analytics
	helm uninstall --ignore-not-found postgres -n analytics
	helm uninstall orderbook --ignore-not-found orderbook --namespace orderbook
	kubectl delete --ignore-not-found pvc data-postgres-postgresql-0 -n analytics
	kubectl delete sparkapp spark-pi-python -n analytics
	kubectl delete pod spark-pi-python-driver --ignore-not-found -n analytics