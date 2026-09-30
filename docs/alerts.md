# Runbook vận hành

Ba rule trong [alert_rules.yaml](../config/alert_rules.yaml) là định nghĩa; chưa kết nối Slack hoặc bộ evaluator tự động. Owner: `student-2A202602977`; kênh dự kiến: Slack `#k4-l3b-alerts`. Cửa sổ 5 phút cần ít nhất 10 mẫu. Thiếu dữ liệu hiển thị N/A, không coi là healthy. Duration là thời gian điều kiện liên tục đúng.

## Alert 1

`HighLatencyP95` — warning: P95 >3000 ms trên cửa sổ 5 phút, liên tục 5 phút. Người dùng chờ câu trả lời lâu; request chậm tiêu tốn error budget.

1. Mở `/dashboard`, xác nhận P50/P95/P99 và TTFT; ghi khoảng UTC.
2. Lọc `response_sent` trong `data/logs.jsonl` cùng thời gian, lấy `correlation_id` có latency cao.
3. Mở trace cùng ID, so sánh retrieval/generation, prompt version và token.

Mitigation theo evidence: rollback label `production` nếu regression gắn prompt mới; khôi phục retrieval nếu retrieval chậm; giảm concurrency khi saturation. Trong practice, tắt scenario bằng `python scripts/inject_incident.py --scenario rag_slow --disable`. Chạy lại cùng workload; P95 phải về dưới ngưỡng và không tăng error. Theo dõi thêm ít nhất 5 phút.

## Alert 2

`HighRequestErrorRate` — critical: failed/received >2% trên cửa sổ 5 phút, liên tục 5 phút. Người dùng không nhận được câu trả lời; lỗi là bad events của SLO.

1. Xác nhận error rate và breakdown trên dashboard; ghi UTC và số failed/received.
2. Chọn một log `request_failed`, ghi `error_type` và `correlation_id`.
3. Mở trace cùng ID, tìm observation ERROR; đối chiếu release/config vừa thay đổi.

Mitigation: khôi phục dependency hoặc cấu hình đã xác định; rollback release/prompt khi có bằng chứng. Không retry vô hạn. Chạy lại workload, xác nhận HTTP 200 và error rate ≤2%, quan sát 5 phút. Giữ evidence các request lỗi ban đầu.

## Alert 3

`LowRetrievalSuccess` — warning: retrieval success <90% trên cửa sổ 5 phút, liên tục 5 phút. Tính cả `response_sent` và `request_failed` có `tool_name=retrieval`, `tool_success` khác null. Người dùng thiếu context hoặc request thất bại.

1. Xác nhận retrieval success và error breakdown ở panel Errors cùng khoảng UTC.
2. Lọc log có `tool_success=false`, lấy `correlation_id` và đối chiếu request thành công gần đó.
3. Mở trace cùng ID, xem retrieval ERROR/duration; kiểm tra vector store và cấu hình timeout.

Mitigation: khôi phục retrieval; chỉ dùng fallback khi nghiệp vụ cho phép. Trong practice dùng `python scripts/inject_incident.py --scenario tool_fail --disable`. Chạy lại workload, kiểm tra retrieval success ≥90% và không tăng latency/cost; theo dõi 5 phút. Thêm integration test dependency timeout trước khi triển khai thật.
