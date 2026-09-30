# Evidence thực tế

Xem [REPORT.md](../REPORT.md) để tra ảnh, output và diễn giải.

- `cp0/`: baseline trước khi sửa; giữ cả các lần pytest lỗi thư mục tạm.
- `cp1/`: workload, validator 100/100, structured log và PII runtime.
- `cp2/`: API export Langfuse thật, prompt lifecycle và snapshot từng bước.
- `langfuse-ui/`: ảnh trực tiếp từ UI Langfuse, gồm trace list, waterfall/metadata, prompt version và trạng thái trước/sau rollback. Không chụp API Keys.
- Các ảnh `*-api.png` là browser capture của viewer local dựa trên JSON export, không phải screenshot UI Langfuse. Key đã được che trước khi lưu.
- `11-dashboard-overview.*`: dashboard CP2 từ JSONL trước practice.
- `cp3-practice/`: metric → log → trace của tool_fail, recovery; không thay thế challenge chính thức.
- `cp3-official/`: challenge chính thức do học viên cung cấp; workload gốc, metric/log/trace API và recovery. Chỉ lưu hash xác nhận file gốc, không lưu query/seed riêng.
- `cp4-after-cp3/`: tests/validators và scan sau khi bổ sung CP3 chính thức.
- `cp4/`: tests/validators, dashboard cuối, scan và SHA-256 source dùng để đối chiếu với commit.

Ảnh được chụp bằng Playwright/Edge, không dùng image generation hay chỉnh sửa kết quả. File HTML/JSON/TXT đi kèm là nguồn kiểm chứng. Challenge đã thực hiện; ảnh UI Langfuse được lưu riêng trong `langfuse-ui/`.
