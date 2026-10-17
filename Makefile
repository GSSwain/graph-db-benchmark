# LDBC FinBench Multi-Engine Benchmark Makefile

.PHONY: help up down restart schema generate-data benchmark report clean verify

help:
	@echo "Available commands:"
	@echo "  make up             - Start local Neo4j and Memcached containers"
	@echo "  make up-all         - Start all containers (Neo4j, Memcached, Neptune, Spanner)"
	@echo "  make down           - Stop all containers"
	@echo "  make verify         - Probe connectivity for all 5 target engines"
	@echo "  make schema         - Apply LDBC FinBench schema and constraints to Neo4j"
	@echo "  make generate-data  - Generate synthetic FinBench data & 100-hop AML trails"
	@echo "  make benchmark      - Run multi-hop benchmark (1 to 100 hops)"
	@echo "  make quickstart     - Run end-to-end quickstart in one command"
	@echo "  make clean          - Clean generated data and reports"

up:
	docker compose up -d neo4j memcached

up-all:
	docker compose --profile all up -d

down:
	docker compose --profile all down

verify:
	./scripts/verify_engines.sh

schema:
	./schemas/neo4j/import.sh

generate-data:
	python3 data-generator/generator.py --preset dev --target neo4j,memcached --export-dir data --deep-hops 100 --chains 10

benchmark:
	python3 test-runner/runner.py --engines neo4j,memcached --hops 1,2,3,4,5,6,7,8,9,10,15,20,30,40,50,75,100 --iterations 10 --output-dir reports

quickstart:
	./scripts/quickstart.sh

clean:
	rm -rf data/* reports/*
	rm -f docs/benchmark_report.html docs/cost_report.html docs/modeling_report.html

cost-estimate:
	python3 scripts/cost_estimator.py --preset all --qps 1000

bench-multilang:
	docker compose run --rm -e SPANNER_EMULATOR_HOST=spanner-emulator:9010 test-runner --engines neo4j-cypher,neo4j-trail,memcached-multiget,memcached-dfs,spanner-sql,neptune-gremlin --hops 1,2,3,4,5,10,20,50,100 --iterations 5 --output-dir reports

