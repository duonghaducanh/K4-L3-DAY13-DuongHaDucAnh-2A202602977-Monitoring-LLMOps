# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

## 1. Thông tin và trạng thái

- Họ tên: Dương Hà Đức Anh (theo tên thư mục; học viên kiểm tra lại dấu).
- MSSV: `2A202602977`; lớp: K4-L3B.
- Project Langfuse: `day13-k4-l3b-2A202602977`, ID `cmunietei0iegad0cr62wi5kf` ([project](https://cloud.langfuse.com/project/cmunietei0iegad0cr62wi5kf)).
- Repository URL: [K4-L3-DAY13-DuongHaDucAnh-2A202602977-Monitoring-LLMOps](https://github.com/duonghaducanh/K4-L3-DAY13-DuongHaDucAnh-2A202602977-Monitoring-LLMOps), do học viên cung cấp. Chưa push thay đổi lần này hoặc nộp LMS.
- Commit SHA: xem `git log -1 --format=%H` ở bản local. Thư mục ban đầu là bản tải về, không có `.git`; đã fetch origin/main từ repository cá nhân để giữ lịch sử gốc, không tạo lịch sử baseline giả.
- Challenge ID: `day13-k4-l3b-monitoring-llmops-v1`; file riêng do học viên cung cấp đã copy nguyên byte vào `config/challenge.json`. Cả file gốc và bản config được gitignore; SHA-256 `f8a1b15bfb62f5c91160cb27665d4efbb9ec89b2f8b6d5ec69e9e874443e0d4f`. Không công bố query/seed riêng.
- Báo cáo tổng hợp dữ liệu đo thực tế bằng AI assistant theo yêu cầu; học viên cần đọc, xác nhận và bổ sung phần tự đánh giá trước khi nộp.

**Trạng thái:** CP0/CP1 đã có evidence; code CP2, trace/prompt và dashboard chạy được. Ảnh trace/prompt hiện là browser capture của viewer dựng từ API export thật, **không phải ảnh UI Langfuse**. Vì rubric yêu cầu ảnh trong project Langfuse, vẫn cần bổ sung ảnh UI. CP3 chính thức đã chạy, có metric/log và waterfall từ API thật, đã kiểm chứng recovery. Ảnh trực tiếp UI Langfuse và bước push/nộp của CP4 vẫn còn thiếu.

## 2. Evidence index

Mỗi checkpoint đã lưu output và chụp ngay trong quá trình làm. Các ảnh không chỉnh sửa giá trị; thông tin key bị che trong dữ liệu trước khi render. HTML và JSON đi kèm giúp đối chiếu. Text output từ PowerShell đã chuyển mã UTF-8, giữ nguyên nội dung để đọc trực tiếp trên GitHub.

| Evidence | Đường dẫn thực tế |
|---|---|
| CP0 baseline log 30/100 | [ảnh](evidence/cp0/baseline.png), [output](evidence/cp0/log-validator.txt) |
| CP0 health / workload | [health](evidence/cp0/health.json), [10 requests](evidence/cp0/load-test.txt) |
| CP0 tests | [22 passed](evidence/cp0/tests.png), [lỗi quyền thư mục tạm ban đầu](evidence/cp0/pytest.txt) |
| CP1 log 100/100 | [ảnh](evidence/cp1/log-validator.png), [workload](evidence/cp1/load-test.txt) |
| Structured log, header, PII | [ảnh runtime](evidence/cp1/pii-runtime.png), [JSON](evidence/cp1/pii-runtime.json) |
| CP2 trace list | [15 trace đủ span tree, API viewer](evidence/06-trace-list-api.png) |
| Waterfall và metadata | [API viewer](evidence/07-trace-waterfall-api.png), [observations export](evidence/cp2/observations.json) |
| Prompt v1/v2 và rollback | [version/trace đối chiếu](evidence/09-10-prompt-rollback-api.png), [JSON](evidence/cp2/prompt-trace-links.json) |
| Ảnh ngay khi promote / rollback | [promote](evidence/cp2/prompt-promoted.png), [rollback](evidence/cp2/prompt-rollback.png) |
| CP2 dashboard có dữ liệu | [ảnh](evidence/11-dashboard-overview.png), [snapshot metrics](evidence/11-dashboard-overview.json) |
| Dashboard bản cuối | [ảnh](evidence/cp4/dashboard-final.png), [metrics](evidence/cp4/dashboard-final.json) |
| CP3 chính thức: tổng hợp metric | [ảnh theo pha và ngưỡng challenge](evidence/cp3-official/12-metric-comparison.png), [run/hashes](evidence/cp3-official/run.json) |
| CP3 chính thức: metric lúc incident | [snapshot ngay sau workload](evidence/cp3-official/incident-dashboard.png), [workload gốc](evidence/cp3-official/incident-workload.txt) |
| CP3 chính thức: log | [ảnh](evidence/cp3-official/13-incident-log.png), [JSON](evidence/cp3-official/13-incident-log.json) |
| CP3 chính thức: trace | [waterfall API](evidence/cp3-official/14-incident-trace.png), [observations thật](evidence/cp3-official/14-incident-trace.json) |
| CP3 cùng query trước/trong/sau | [so sánh span](evidence/cp3-official/15-span-comparison.png), [JSON](evidence/cp3-official/15-span-comparison.json) |
| CP3 recovery | [dashboard](evidence/cp3-official/recovery-dashboard.png), [5 HTTP 200](evidence/cp3-official/recovery-workload.txt) |
| Kiểm tra sau CP3 | [tests](evidence/cp4-after-cp3/01-pytest.txt), [log validator](evidence/cp4-after-cp3/02-log-validator.txt), [dashboard validator](evidence/cp4-after-cp3/03-dashboard-validator.txt), [scan/source manifest](evidence/cp4-after-cp3/security-and-source-manifest.json) |
| CP3 practice metric | [ảnh](evidence/cp3-practice/12-incident-metric.png), [JSON](evidence/cp3-practice/12-incident-metric.json) |
| CP3 practice log | [ảnh](evidence/cp3-practice/13-incident-log.png), [JSON](evidence/cp3-practice/13-incident-log.json) |
| CP3 practice trace | [ảnh API waterfall](evidence/cp3-practice/14-incident-trace.png), [JSON](evidence/cp3-practice/14-incident-trace.json) |
| Recovery | [10 HTTP 200 và health](evidence/cp3-practice/recovery.json), [dashboard](evidence/cp3-practice/after-recovery.png) |
| CP4 tests | [28 passed](evidence/cp4/01-pytest.png), [output](evidence/cp4/01-pytest.txt) |
| CP4 log validator | [100/100](evidence/cp4/02-log-validator.png), [output](evidence/cp4/02-log-validator.txt) |
| CP4 dashboard validator | [6/6](evidence/cp4/03-dashboard-validator.png), [output](evidence/cp4/03-dashboard-validator.txt) |
| Secret/PII scan, hash source | [manifest](evidence/cp4/security-and-source-manifest.json) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline CP0 | Kết quả cuối |
|---|---|---|
| Log validator | 30/100, ID MISSING, thiếu context | 100/100; 110 log records, 47 correlation IDs kể cả control events |
| Dashboard contract | 6/6, chưa có dashboard runtime | 6/6 và dashboard `/dashboard` |
| Pytest | 22 passed sau xử lý lỗi thư mục tạm | 28 passed |
| PII leak theo validator | 0 | 0; kiểm thêm CCCD/thẻ, nested data, exception |
| Traces | root starter chưa có child | ảnh CP2 có 15 trees đủ agent/retrieval/generation |
| Prompt | chưa có managed prompt | v1/v2, promote v2, rollback v1, generation liên kết prompt thật |

Snapshot CP4 trước khi bổ sung challenge (60 phút, **bao gồm 10 request lỗi practice**, không xóa để làm đẹp số liệu): P50 154.00 ms, P95 2434.20 ms, P99 2463.40 ms; TTFT P95 50.00 ms. 45 requests, 10 failures, error rate 22.22%, retrieval success 77.78%. Cost $0.074823, input/output tokens 1271/4734, quality mean 0.846.

## 4. Logging và PII

[Middleware](../app/middleware.py) clear context ở đầu và trong finally, chấp nhận header đúng `req-<8 hex>` hoặc sinh ID mới; trả lại ID và `x-response-time-ms`. Header không hợp lệ được thay bằng ID mới để không mang PII vào metadata. [API](../app/main.py) bind user hash, session, feature, model, env trước `request_received`; dùng thread pool cho agent đồng bộ để workload concurrency không chặn event loop.

[PII processor](../app/logging_config.py) scrub đệ quy cả dictionary/list, event, context và exception sau khi format stack nhưng trước file writer/JSON renderer. [Patterns](../app/pii.py) xử lý email, số điện thoại Việt Nam, CCCD và thẻ 13–19 chữ số; chuỗi dài được match trước điện thoại để không redact một phần thẻ. User ID được SHA-256 rồi lấy 12 hex; đây là pseudonymization, không phải anonymization tuyệt đối.

[Tests bổ sung](../tests/test_logging_privacy.py) kiểm tra ID/context đồng thời, header không hợp lệ, nested PII/exception, CCCD/thẻ. Evidence PII dùng dữ liệu giả, public output chỉ hiển thị input đã che và kết quả kiểm tra bốn giá trị thô không có trong log. Log baseline được lưu local dưới `data/baseline-*.jsonl` (gitignored) trước khi bắt đầu cửa sổ log sạch CP1; không xóa log lỗi practice.

## 5. Tracing và prompt versioning

[Agent](../app/agent.py) là root observation `lab-agent-run`, trace name `day13-agent-request`. [Retrieval](../app/mock_rag.py) là child `retriever`; [LLM](../app/mock_llm.py) là child `generation`. Decorators tắt capture raw input/output; chỉ ghi preview đã scrub. Correlation ID, user hash, session, model được propagate. Generation có managed prompt thật, model, input/output token, cost và completion-start time. Fake LLM mô phỏng TTFT khoảng 50 ms; cost là ước tính theo giá trong code, không phải hóa đơn provider.

| Bước | Label | Version xác nhận từ trace | Correlation ID | Trace ID |
|---|---|---|---|---|
| baseline | baseline | 1 | `req-0a4ba7d9` | `46892bf3e6b8c05ae8103a9afc714260` |
| candidate | candidate | 2 | `req-52b27d42` | `4f911a1d5c7bb175076fd6477732c913` |
| promoted | production | 2 | `req-5c5747c0` | `b67ac8255ba794dbdf40e2df001fd423` |
| rollback | production | 1 | `req-e71f3455` | `4e306145b0ff3d30cc644a1f8ca07e50` |

Các request dùng cùng input `Explain monitoring metrics logs traces`. Script đổi label trên Langfuse, clear SDK cache trước request, đọc lại prompt rồi đối chiếu root metadata/generation từ API. App bình thường cache prompt 60 giây; khi đổi label cần chờ TTL hoặc restart API. Trạng thái kết thúc `production → v1`. FakeLLM chưa diễn giải instruction nên không kết luận v2 tốt hơn; input token tăng do template dài hơn, output token ngẫu nhiên.

10 trace IDs workload riêng, tất cả có `session_id=cp2-workload`:

| Trace ID | Correlation ID |
|---|---|
| `2b0241ea9656074e93dfee52d1d76e8a` | `req-0b0d0965` |
| `97e7e6d6b8ab9ecc29fb1cb3853f4515` | `req-689d0caf` |
| `676c96f3a7356ff08c1554be10ba6c43` | `req-e5badfb1` |
| `11208900e68f5fc93fed15ebf3d24dbe` | `req-ddf985f2` |
| `9330dcb0458a267c1d04200039c94171` | `req-70d46079` |
| `1eb734586f9b61df5d06fa377d79a6ec` | `req-7053965f` |
| `8b41237e4df69009acd1a9b5f5815a8c` | `req-ea307850` |
| `d7fd0039833faff3d025af21a7fa519c` | `req-11eb1dd1` |
| `ee02ea97c342dd76c5ac0bd224c4141f` | `req-7399f188` |
| `0c14e475a8457a60284a36d0ee72c547` | `req-140f8ad3` |

Project ban đầu đặt nhầm tên ở organization; đọc lại API đã xác nhận project tên đúng. API `/traces` trả 410 với organization mới nên exporter dùng [Observations API v2 chính thức](https://langfuse.com/docs/api-and-data-platform/features/public-api), phân trang cursor, nhóm theo traceId và lọc correlation IDs trong log local. Không sử dụng trace của người khác.

## 6. Dashboard, SLO và alerts

[Dashboard code](../app/dashboard.py) đọc JSONL theo UTC 60 phút, auto refresh 30 giây, đúng 6 panel theo [contract](../config/dashboard.yaml): latency P50/P95/P99 và TTFT P95; traffic request/phút; error rate/breakdown và retrieval success; cost/phút và tổng; input/output tokens; mean quality. Không có mẫu hiển thị N/A. Percentile nội suy tuyến tính; tests kiểm tra time filter, denominator cả success/failure và empty window.

Retrieval success lấy cả `response_sent` lẫn `request_failed` có tool outcome, vì chỉ lọc event thất bại sẽ sai mẫu số. Cost panel bản cuối tách đồ thị USD/phút và threshold tổng cửa sổ; ảnh CP2 cũ vẫn giữ như evidence lịch sử. `/metrics` là thống kê trong RAM của một process, còn dashboard JSONL là nguồn chuẩn bền qua restart.

[SLO](../config/slo.yaml): 99.5% requests vừa thành công vừa latency ≤3000 ms trong 28 ngày. Budget = 0.5% × N; N=10,000 cho phép 50 bad requests. Không đếm hai lần một request vừa lỗi vừa chậm. Baseline local nhỏ không chứng minh đạt SLO 28 ngày; giữ 3000 ms làm mục tiêu lab. SLI dùng thời gian agent theo contract; header có thời gian HTTP đầy đủ. Traffic threshold 1 request/phút là guardrail lab, không phải mục tiêu sản lượng thật.

[Ba alert](../config/alert_rules.yaml), [runbook](../docs/alerts.md): HighLatencyP95 >3000 ms; HighRequestErrorRate >2%; LowRetrievalSuccess <90%. Cùng cửa sổ 5 phút, duration 5 phút, tối thiểu 10 mẫu, severity/owner/Slack `#k4-l3b-alerts` đầy đủ. Đây là cấu hình và runbook, **chưa nối Slack hoặc chạy alert evaluator**; không có thông báo được gửi. Mỗi runbook đi từ dashboard → log → trace, mitigation theo nguyên nhân và kiểm tra recovery.

## 7. Điều tra incident

### Challenge chính thức

Đã thực hiện với file chính thức `day13-k4-l3b-monitoring-llmops-v1`. Chạy đúng `python scripts/inject_incident.py` và `python scripts/load_test.py --challenge --concurrency 5`; cùng 5 query/seed gốc cho baseline, incident và recovery. Không sửa file riêng; hash và số lượng request ghi trong [run.json](evidence/cp3-official/run.json).

1. **Metrics:** cửa sổ incident `2026-09-30T03:40:41.383977+00:00` → `2026-09-30T03:40:44.346981+00:00` UTC. P95 2657.00 ms, TTFT P95 50.00 ms; 5/5 HTTP 200, retrieval success 100%. Latency vượt ngưỡng challenge 2000 ms dù không có HTTP error. Snapshot dashboard được lưu trước khi chọn log.
2. **Log:** `response_sent`, correlation ID `req-92e64a82`, latency khoảng 2657 ms. Payload query không đưa vào evidence công khai để giữ kín nội dung challenge.
3. **Trace:** `7105b57d1e3d8f51e2f6d11f7af8eb26`, cùng correlation ID. Root 2658 ms, retrieval **2502 ms** (~94.1% thời gian), generation **156 ms**. Các span không báo ERROR: đây là latency incident.
4. **Root cause:** retrieval bị chậm trong incident, không phải LLM generation hay lỗi HTTP. Sau khi đối chiếu span với [mock_rag.py](../app/mock_rag.py), nhánh inject `rag_slow` mô phỏng chờ 2.5 giây khớp thời gian retrieval đo được.
5. **Fix đã làm:** tắt incident bằng `python scripts/inject_incident.py --disable`, giữ nguyên file challenge. Chạy lại cùng input/concurrency; 5/5 HTTP 200, P95 còn **152.00 ms**, TTFT 50.00 ms; health xác nhận tất cả incident tắt.
6. **Preventive measure:** theo dõi retrieval duration riêng, thêm budget/timeout và integration test latency retrieval; thêm ngưỡng cảnh báo phù hợp nếu yêu cầu là 2000 ms. Rule HighLatencyP95 hiện tại dùng 3000 ms/5 phút nên **không khẳng định đã fire** trong incident ngắn này. Giữ contract/SLO chung 3000 ms nguyên trạng, phân biệt với threshold challenge.

Baseline đầu tiên P95 2390.40 ms cũng cao. Heuristic ban đầu chỉ xét tỷ lệ incident/baseline nên chưa xác định rõ triệu chứng; output ban đầu vẫn giữ trong `run.json`, sau đó đối chiếu threshold challenge và recovery. Đã sửa script để các lần chạy sau xét cả threshold challenge, không chỉ tỷ lệ tăng. Không xóa kết quả baseline chậm.

| Pha, cùng query | Correlation ID | Trace ID | Root ms | Retrieval ms | Generation ms |
|---|---|---|---:|---:|---:|
| baseline | `req-d1f0e3b5` | `99604b4b614dbaf8819683e995fccbee` | 2308 | 1 | 151 |
| incident | `req-92e64a82` | `7105b57d1e3d8f51e2f6d11f7af8eb26` | 2658 | 2502 | 156 |
| recovery | `req-0e0c8379` | `62c1ebafde349b40543f43c239d6c9e9` | 154 | 0 | 152 |

Baseline có **2156 ms ngoài hai child span**, retrieval chỉ 1 ms và generation 151 ms; prompt_source=langfuse, version 1. Theo vị trí code, khoảng chờ này phù hợp với lần resolve/fetch prompt đầu tiên, nhưng **chưa có span riêng đo prompt fetch nên đây là suy luận, không khẳng định nguyên nhân đã được đo trực tiếp**. Incident lại nằm rõ ở retrieval 2502 ms, và sau recovery retrieval về 0 ms ở độ phân giải API. Cả ba request dùng prompt v1. So sánh này tránh quy toàn bộ baseline chậm cho retrieval hoặc nhầm rollback prompt là fix.


### Practice `tool_fail` đã thực hiện

1. Metrics trước tiên: khoảng `2026-09-30T03:14:20.723399+00:00` đến `2026-09-30T03:14:22.509017+00:00`. Cả 10 request workload trả HTTP 500. Dashboard 60 phút có error rate 28.57% và retrieval success 71.43%; mẫu số gồm request trước incident, nên tỷ lệ không phải 100%.
2. Sau snapshot metrics, lọc log trong khoảng trên, chọn `request_failed`, correlation ID `req-eb704ed9`, error `RuntimeError`, `tool_success=false`, detail `Vector store timeout`.
3. Sau đó tra Langfuse: trace `d81fe21e47a87e7b17c0b26025327975` có cùng correlation ID; child `retrieval` ERROR, parent agent ERROR. Không có generation vì request dừng trước bước LLM.
4. Root cause theo evidence: bước retrieval thất bại do vector store timeout được mô phỏng bởi practice. Không suy ra lỗi LLM hoặc prompt.
5. Fix đã làm: tắt `tool_fail` qua API control; chạy lại đúng workload/concurrency=5, 10/10 HTTP 200. Dashboard 60 phút vẫn giữ lỗi lịch sử, không lập tức trở lại 0%.
6. Preventive measure: LowRetrievalSuccess và HighRequestErrorRate với runbook; integration test dependency timeout; khi triển khai thật thêm timeout/circuit breaker và fallback có kiểm soát.

## 8. Giải thích và giới hạn

- Quyết định kỹ thuật: scrub tại logging processor cuối cùng trước serialize để phủ cả context và exception; tắt raw capture trong tracing thay vì dựa vào preview của log.
- Blocker đã xử lý: pytest không ghi được thư mục tạm hệ thống; tạo `.pytest_tmp` trong workspace. Langfuse endpoint cũ 410; chuyển sang observations v2. Prompt cache được clear khi demo rollback để trace phản ánh label mới ngay.
- Luồng điều tra: metric chỉ triệu chứng/khoảng UTC; log chọn request cụ thể; correlation ID nối sang trace; child span chỉ đúng bước lỗi. Không kết luận root cause từ metric đơn lẻ.
- Version prompt giúp biết request dùng cấu hình nào và rollback mà không sửa code. Token/cost giúp phát hiện bloat; SLO/budget biến chất lượng thành ngưỡng vận hành có thể đo.
- Hạn chế: bộ dữ liệu lab nhỏ, fake output/token; quality proxy không phải human evaluation; cost không phải billing; dashboard đọc toàn file phù hợp lab chứ chưa tối ưu lưu lượng production. Regex PII không bao phủ mọi dạng dữ liệu nhạy cảm.
- Học viên tự bổ sung sau khi đọc/demo: điều học được, quyết định có thể bảo vệ trong Q&A. Không tự nhận đã nộp hoặc đã có ảnh UI Langfuse khi mới có API evidence.

## 9. Checklist trước khi nộp

- [x] Source TODO bắt buộc, tests và validators có output/ảnh.
- [x] ≥10 traces, child observations, prompt v1/v2 và rollback thật được xác nhận qua API.
- [x] Dashboard runtime 6 panel có dữ liệu, đơn vị, UTC, ngưỡng; SLO và 3 alert/runbook.
- [x] Evidence lưu theo checkpoint, dùng link tương đối.
- [ ] Chụp trực tiếp UI Langfuse: trace list, waterfall/metadata và prompt versions/labels; không chụp API Keys.
- [x] Chạy challenge chính thức, lưu metric/log/trace API đúng challenge ID và xác nhận recovery. Ảnh UI Langfuse vẫn theo mục riêng ở trên.
- [x] Đã nhận và điền repository URL cá nhân.
- [ ] Đối chiếu commit SHA cuối trên remote; chạy lại checks nếu có thay đổi.
- [ ] Học viên kiểm tra report, xác nhận thông tin và tự đánh giá.
- [ ] Push repo cá nhân và nộp URL/SHA trên LMS/Codelabs.
