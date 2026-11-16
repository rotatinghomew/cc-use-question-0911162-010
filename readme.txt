人工智能治理指标口径版本与回算注册中心

运行验收：
python3 -m indicator_registry run --fixture fixtures/acceptance.json --database /tmp/indicator_registry.sqlite3 --output /tmp/indicator_registry-output

核验：
python3 -m indicator_registry verify --database /tmp/indicator_registry.sqlite3 --output /tmp/indicator_registry-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.definition_signal.test_definition_quality -v

构建检查：
python3 -m compileall -q indicator_registry tests
