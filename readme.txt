人工智能治理指标口径版本与回算注册中心

运行验收（原有记录夹具，行为保持不变）：
python3 -m indicator_registry run --fixture fixtures/acceptance.json --database /tmp/indicator_registry.sqlite3 --output /tmp/indicator_registry-output

运行版本化验收（定义版本、依赖回算、发布与历史核验）：
python3 -m indicator_registry run --fixture fixtures/versioned_acceptance.json --database /tmp/indicator_registry_versioned.sqlite3 --output /tmp/indicator_registry-versioned
python3 -m indicator_registry run --fixture fixtures/versioned_next.json --database /tmp/indicator_registry_versioned.sqlite3 --output /tmp/indicator_registry-versioned-next

核验（按报告签发时的定义快照核验；--report-id 用于核验已签发的历史报告）：
python3 -m indicator_registry verify --database /tmp/indicator_registry.sqlite3 --output /tmp/indicator_registry-output
python3 -m indicator_registry verify --database /tmp/indicator_registry_versioned.sqlite3 --output /tmp/indicator_registry-versioned --report-id <report_id>

查看已注册的定义版本与报告：
python3 -m indicator_registry versions --database /tmp/indicator_registry_versioned.sqlite3
python3 -m indicator_registry inspect --database /tmp/indicator_registry_versioned.sqlite3

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.definition_signal.test_definition_versions -v
python3 -m unittest tests.definition_signal.test_definition_quality -v

构建检查：
python3 -m compileall -q indicator_registry tests

口径版本与回算约定
--------------------
1. 蓝图/依赖图：记录 payload 中的 definition_id + definition_version 标识一个定义版本；
   depends_on / dependencies / dependency_ids 声明依赖，可用 "gov-a@2" 或
   dependency_versions 固定版本。未声明版本的旧口径夹具走原有流程，发布物不变。
2. 回算顺序：受影响集合 = 变更定义 + 其全部下游依赖闭包；按依赖优先的拓扑序回算。
   未变更的定义若内容哈希、依赖版本和观察窗口均未变化，则复用已注册计算结果（reused）。
3. 观察窗口：每个定义可声明 observation_window_days / observation_window，
   min_observations、source_observations、source_age_days。窗口与所需观测不足、
   依赖未注册、依赖环或依赖环下游，均不发布数字。
4. 不可计算：withheld 条目在 indicator_values.csv 中 value 为空，在
   unavailable.csv 与 definitions.json 中记录 not_computable 原因；报告 status=withheld、
   publishable=false。告警等级为 withheld，绝不使用阈值等级冒充。
5. 定义版本一致性：manifest.json、summary.json、definitions.json、alerts.csv、
   indicator_values.csv、unavailable.csv 均引用同一个 definition_snapshot_hash 与
   version_map；verify 会检查这些引用一致、告警等级与其数值一致、依赖哈希与签发快照一致。
6. 稳定性：同一版本重跑生成逐字节相同的发布物；已签发报告按当时快照核验，
   即使更新版本已发布也仍可通过（verify 同时报告 historical=true）。
7. 依赖来源不足：依赖版本已被新版本取代时，依赖方的版本引用与依赖内容哈希会一并
   更新并重算；固定旧版本但新版本已存在的，会在 messages 中记录
   dependency_pin_stale/dependency_pin_advanced，不会静默沿用旧结果。
