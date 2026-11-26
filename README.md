# AIOps cho DevOps trong 7 ngày

**Mục tiêu cuối tuần** là tự demo được một quy trình từ Terraform PR đến điều tra sự cố sau deploy. Lộ trình giả định bạn đã quen Git, Docker và CI/CD, có 2–3 giờ mỗi ngày. Một tuần đủ để hoàn thành và giải thích lab này. Kinh nghiệm xử lý sự cố production cần tích lũy qua các ca trực thực tế.

## Roadmap

```text
  TRƯỚC DEPLOY                            SAU DEPLOY
  Terraform PR                            API → backend
       │                                       │
       ▼                                       ▼
  CI kiểm tra và tạo plan                 Metrics → trace → log
       │                                  Prometheus + OpenTelemetry · ngày 1–2
       ▼                                       │
  Tóm tắt plan và lỗi CI                       ▼
  AI review · ngày 5                      Baseline + gom cảnh báo
       │                                  Python + Alertmanager · ngày 3–4
       ▼                                       │
  Deploy → ghi SHA và thời điểm ──────────────►▼
                                        Timeline và tóm tắt cho on-call
                                        Đối chiếu deploy · ngày 6
                                               │
                                               ▼
                                        Diễn tập và đo kết quả · ngày 7
                                               │
                                               ▼
                                        Lab mở rộng · canary release
```

## Lab xuyên suốt

Dùng Docker Compose chạy hai HTTP service `api` và `backend`, Prometheus, Grafana, một trace backend như Jaeger và Alertmanager. Ghi log JSON ra stdout và dùng `docker compose logs` để tra theo `trace_id`. Tạo traffic đều và cấu hình độ trễ của backend qua một biến môi trường. Dùng tài nguyên tích hợp `terraform_data` để tập review plan local. Dùng CI hiện có hoặc chạy cùng các bước bằng script local nếu bạn chưa có runner.

Mỗi ngày dành khoảng **30 phút đọc, 90 phút làm, 30 phút ghi bằng chứng**. Giữ một thư mục kết quả trong lab của bạn để lưu query, mẫu cảnh báo, bảng đánh giá và báo cáo diễn tập.

## Lịch học và tiêu chí tự kiểm tra

[Khởi động playground Ngày 1](day-1/README.md)

| Ngày | Học và làm | Kết quả cần có |
|---|---|---|
| **1 · Metrics** | Dựng hai service, phát traffic đều. Expose số request, số lỗi và histogram độ trễ. Viết PromQL cho request rate, tỷ lệ 5xx và p95. Tăng độ trễ backend trong vài phút rồi đưa về bình thường. | Dashboard cho thấy p95 tăng và phục hồi. Lưu ba truy vấn và đánh dấu khoảng thời gian bị ảnh hưởng. [PromQL functions](https://prometheus.io/docs/prometheus/latest/querying/functions/) |
| **2 · Traces và logs** | Instrument cả hai service bằng OpenTelemetry. Truyền trace context qua HTTP. Đưa cùng `trace_id` vào log của request. Từ khoảng thời gian trên dashboard, tìm trace chậm rồi mở log tương ứng. | Một trace có span của cả hai service và một dòng log cùng `trace_id`. Chỉ ra span chiếm thời gian và log củng cố nhận định nào. [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) |
| **3 · Phát hiện bất thường** | Xuất chuỗi p95 theo phút. So sánh ngưỡng cố định với rolling median từ các điểm trước đó cộng một biên độ. Ghi giờ bắt đầu và kết thúc từng đợt tăng độ trễ. Dùng một lượt để chỉnh ngưỡng và lượt khác để đánh giá. | Bảng so sánh số đợt cảnh báo giả, số incident bị bỏ sót và độ trễ phát hiện. Gộp các phút cảnh báo liên tiếp thành một đợt để đếm nhất quán. |
| **4 · Gom cảnh báo** | Để cả API và backend phát cảnh báo khi backend chậm. Trong cùng môi trường lab, thử nhóm theo nhãn dependency dùng chung, rồi thử inhibition nếu có cảnh báo gốc đủ rõ. Tạo thêm một lỗi độc lập. | Ghi số thông báo trước và sau. Xác nhận lỗi độc lập vẫn có thông báo riêng và cảnh báo ảnh hưởng xuất hiện khi cảnh báo gốc vắng mặt. [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) |
| **5 · AI review CI và Terraform** | Chạy `terraform fmt -check`, `terraform validate` và `terraform plan -out=tfplan` sau khi init. Từ `terraform show -json tfplan`, xuất danh sách `address` và `change.actions`. Thử một plan replacement bằng `triggers_replace` trên `terraform_data`. Cho AI đọc danh sách hoặc một đoạn log lỗi CI đã lọc để viết nhận xét có trích dẫn. | AI chỉ đúng resource bị thay thế. Khi CI fail, bản tóm tắt chỉ đúng stage và dòng lỗi. CI vẫn lấy kết quả từ exit code và policy. Giữ raw plan, state và log chưa lọc trong môi trường lab. [Terraform JSON format](https://developer.hashicorp.com/terraform/internals/json-format) · [Terraform show](https://developer.hashicorp.com/terraform/cli/commands/show) |
| **6 · Hỗ trợ on-call** | Khi deploy local, lưu `timestamp_utc`, `service`, `environment`, `commit_sha` và liên kết đến CI nếu có. Chọn các deploy cùng service và môi trường trong 15 phút trước alert. Đưa timeline, metric, trace và log đã lọc cho AI tóm tắt. | Một bản tin ghi phạm vi ảnh hưởng, bằng chứng, deploy đáng kiểm tra, giả thuyết và bước kiểm tra tiếp theo. Thử cả trường hợp có deploy gần alert và trường hợp thiếu bằng chứng. |
| **7 · Diễn tập** | Chạy hai lượt. Lượt A deploy một thay đổi làm backend chậm rồi quay về cấu hình tốt. Lượt B gây chậm mà không deploy. Cất nguyên nhân dự kiến vào ghi chú riêng trước khi phân tích. | Hai báo cáo có timeline, bằng chứng và thời gian phát hiện. Lượt A có biểu đồ xác nhận phục hồi. Lượt B kiểm tra AI có giữ nguyên trạng thái chưa xác định khi thiếu bằng chứng về deploy. |

## Mẫu đầu ra của AI

**Review Terraform** gồm resource bị ảnh hưởng, hành động dự kiến và câu hỏi cần reviewer xác minh. Cặp action `delete/create` hoặc `create/delete` là replacement. Khi input chỉ có địa chỉ và action, ghi nguyên nhân replacement là **chưa xác định**. Quyết định apply do người có quyền duyệt.

**Tóm tắt incident** gồm thời điểm bắt đầu, phạm vi ảnh hưởng, link dashboard hoặc trace, log liên quan, deploy gần nhất và bước xác minh. Phân biệt điều quan sát được với giả thuyết. Một deploy gần thời điểm cảnh báo là đầu mối để kiểm tra.

## Tự chấm cuối tuần

- [ ] Từ cảnh báo p95, tìm được trace chậm và log cùng request.
- [ ] Giải thích được vì sao chọn baseline hoặc ngưỡng cố định dựa vào bảng số liệu.
- [ ] Gom được cảnh báo liên quan và vẫn nhận được thông báo của lỗi độc lập.
- [ ] Đối chiếu nhận xét Terraform của AI với danh sách action thực tế, kể cả replacement.
- [ ] Demo được hai lượt incident, xác nhận phục hồi sau rollback và chỉ ra chỗ bản tóm tắt còn thiếu bằng chứng.

## Ứng dụng AI vào các việc DevOps khác

| Công việc | Bài thực hành | Cách kiểm chứng |
|---|---|---|
| **Review pipeline · ngày 5** | Đưa cấu hình CI cho AI để lập bảng job chạy khi mở PR, merge hoặc tạo tag. Tìm trường hợp một thay đổi kích hoạt hai lượt chạy. | Đối chiếu bảng với lịch sử chạy hoặc kích hoạt từng sự kiện trên repo thử nghiệm. |
| **Viết và kiểm thử IaC · ngày 5** | Cho AI đọc module Terraform mẫu rồi đề xuất test cho input hợp lệ, subnet rỗng và tên sai định dạng. | Chạy `terraform validate`, `terraform test` và kiểm tra plan của ca hợp lệ. |
| **Tối ưu build · sau tuần 1** | Đưa thời lượng theo bước cho AI để tìm nút thắt và đề xuất một thay đổi về cache hoặc chạy song song. | So sánh thời lượng nhiều lượt chạy trên cùng commit và runner. Ghi riêng cache hit và cache miss. |
| **Canary release · sau ngày 7** | So sánh p95 và tỷ lệ 5xx giữa bản stable và canary. Nhờ AI tóm tắt endpoint bị ảnh hưởng và dẫn query dùng để kiểm tra. | Dùng rule có ngưỡng và số mẫu tối thiểu để quyết định rollout. Xác nhận bằng lab bên dưới. |
| **FinOps · sau tuần 1** | Dùng bảng chi phí và mức sử dụng mẫu để tìm khoản tăng bất thường hoặc tài nguyên có thể giảm cấu hình. | Đối chiếu với billing, tag và mức tải cao điểm trước khi đề xuất thay đổi. |
| **Runbook và postmortem · ngày 6–7** | Đưa bản tóm tắt incident và runbook của lab cho AI để đề xuất bước kiểm tra, rồi dựng timeline cho postmortem. | Đối chiếu mốc giờ với alert, trace và deploy. Gắn link bằng chứng cho từng nhận định quan trọng. |

### Lab canary release

1. Chạy hai phiên bản backend bằng Docker Compose. Chia traffic thử nghiệm, chẳng hạn 80% stable và 20% canary. Gắn nhãn phiên bản để tách p95, tỷ lệ 5xx và số request theo endpoint.
2. Chọn trước cửa sổ đánh giá, số request tối thiểu cho mỗi phiên bản và ngưỡng chênh lệch p95 hoặc 5xx. Cho pipeline giữ nguyên tỷ lệ traffic khi chưa đủ mẫu.
3. Chạy một lượt cả hai bản đều khỏe và một lượt canary chậm ở `/checkout` nhưng vẫn trả về HTTP 200. Đưa số liệu và query cho AI để nó nêu endpoint, phiên bản, cửa sổ đo và tín hiệu thay đổi.
4. Kiểm tra pipeline cho phép tăng traffic ở lượt khỏe, dừng rollout ở lượt canary chậm và tiếp tục giữ nguyên khi thiếu mẫu. Sau khi đưa traffic về stable ở lượt lỗi, dùng dashboard xác nhận p95 phục hồi.
