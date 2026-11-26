# Playground Ngày 1 · Metrics

Cần chạy được `docker compose` trong distro WSL. Nếu dùng Docker Desktop, bật WSL Integration cho distro đó. Mở terminal WSL và chạy:

```bash
cd /mnt/d/Project/Teach/AIOps-7-ngay/day-1
docker compose up -d --build
docker compose ps
```

- Mở [dashboard Grafana](http://localhost:13000/d/aiops-day-1) để xem request rate, tỷ lệ 5xx và p95.
- Kiểm tra cả hai service báo `UP` trong [Prometheus Targets](http://localhost:19090/targets).
- Xem dữ liệu thô ở [API /metrics](http://localhost:18080/metrics). Mở [queries.promql](queries.promql) và chạy từng truy vấn trong [Prometheus](http://localhost:19090/query).

## Thí nghiệm

1. **Đo lúc bình thường.** Giữ traffic tự động ít nhất hai phút. Ghi request rate của API (khoảng 10 request/giây), tỷ lệ 5xx và p95 của cả hai service.
2. **Làm backend chậm.** Đổi độ trễ từ 20 ms lên 800 ms. Ghi thời điểm, đợi khoảng ba phút và quan sát ba biểu đồ.

   ```bash
   BACKEND_DELAY_MS=800 docker compose up -d --no-deps backend
   date -Iseconds
   ```

   Backend tiếp tục trả HTTP 200 sau khi khởi động. API có thể trả vài lỗi 502 trong lúc Compose tạo lại container.

3. **Khôi phục.** Đưa độ trễ về mặc định, ghi thời điểm và giữ traffic thêm ít nhất hai phút. Lưu ảnh dashboard kèm hai mốc giờ và số liệu của ba giai đoạn. Các truy vấn dùng cửa sổ hai phút, nên p95 có thể mất một lúc mới về mức ban đầu.

   ```bash
   BACKEND_DELAY_MS=20 docker compose up -d --no-deps backend
   date -Iseconds
   ```

4. **Thử tỷ lệ 5xx.** Sau khi p95 ổn định, gửi thêm 20 request cố ý trả HTTP 500. Đợi ít nhất một lần scrape (5 giây) rồi xem biểu đồ 5xx.

   ```bash
   for i in {1..20}; do
     curl -sS -o /dev/null http://localhost:18080/error
   done
   ```

**Tự kiểm tra.** Khi request rate gần như giữ nguyên và 5xx về 0%, hai đường p95 cho bạn biết gì về trải nghiệm người dùng? Đối chiếu với hai mốc thay đổi độ trễ.

## Dừng lab

```bash
docker compose down
```

Prometheus giữ lịch sử trong volume để bạn có thể mở lại và so sánh.
