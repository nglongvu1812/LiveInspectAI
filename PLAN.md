# PLAN.md — LiveInspectAI

> **Mục đích:** Đây là kế hoạch triển khai chính cho coding agent (Google Antigravity). Hãy biến kế hoạch này thành một ứng dụng MVP hoàn chỉnh, chạy được, có kiểm thử, có tài liệu cài đặt và có thể demo cho một nhóm nhỏ người dùng.
>
> **Quy tắc quan trọng:** “Hoàn chỉnh 100%” nghĩa là hoàn thành toàn bộ phạm vi và tiêu chí nghiệm thu được mô tả trong file này, không có nghĩa mô hình có thể phát hiện lỗi trên mọi loại vật thể hoặc đạt độ chính xác tuyệt đối. Không được tuyên bố tính năng/kiểm thử/deploy đã hoàn thành nếu chưa thực sự chạy và xác minh.

---

## 0. Vai trò của agent và cách làm việc

Bạn là kỹ sư phần mềm chịu trách nhiệm triển khai end-to-end cho LiveInspectAI: nghiên cứu repository hiện tại, thiết kế, viết code, kiểm thử, sửa lỗi, chuẩn bị triển khai và cập nhật tài liệu.

### Quy tắc làm việc bắt buộc

1. **Kiểm tra repository trước khi thay đổi.** Đọc cấu trúc thư mục, README, cấu hình, mã nguồn, Git status và các test hiện có. Nếu repository đã có code, bảo toàn các phần đang hoạt động; không khởi tạo đè hoặc xóa file chỉ vì không giống kế hoạch.
2. Thực hiện theo từng phase trong file này. Một phase chỉ được đánh dấu `[x]` sau khi hoàn thành tiêu chí nghiệm thu và chạy các lệnh kiểm tra liên quan.
3. Không tạo cả ứng dụng bằng một lần sinh code khổng lồ. Chia thành các thay đổi nhỏ, có thể chạy và kiểm tra từng phần.
4. Ưu tiên giải pháp dễ cài trên Windows 11 và dễ trình diễn cho sinh viên. Tránh microservices, Kubernetes, message broker riêng, framework thừa hoặc kiến trúc quá phức tạp nếu chưa có nhu cầu thực tế.
5. Không bịa số liệu, benchmark, kết quả test, đường dẫn, biến môi trường, API hoặc trạng thái triển khai. Khi chưa kiểm chứng, ghi rõ `NOT VERIFIED`.
6. Không chờ người dùng quyết định các chi tiết nhỏ. Chọn mặc định hợp lý, ghi quyết định vào `docs/DECISIONS.md`, tiếp tục triển khai. Chỉ hỏi khi thiếu thông tin hoặc quyền truy cập thật sự chặn công việc (ví dụ secret cloud, thông tin tài khoản hoặc chấp thuận chi phí).
7. Nếu một thư viện có API thay đổi theo phiên bản, kiểm tra tài liệu phù hợp với phiên bản được pin; không trộn ví dụ của nhiều phiên bản. Ưu tiên phiên bản ổn định và tạo lockfile.
8. Không tải dataset lớn, model weights, video hoặc ảnh người dùng lên Git. Không commit `.env`, token, service key, mật khẩu hay dữ liệu cá nhân.
9. Không để frontend có Supabase `service_role` key, agent token, hoặc bất kỳ secret nào. Những giá trị đó chỉ được đọc từ environment phía server/agent.
10. Khi phát hiện lỗi, tìm nguyên nhân và sửa lỗi gốc; không vô hiệu hóa test, bỏ qua exception hoặc trả dữ liệu giả để làm demo trông có vẻ hoạt động.
11. Sau mỗi nhóm thay đổi, báo cáo ngắn: thay đổi nào đã làm, lệnh nào đã chạy, kết quả thực tế, phần nào còn thiếu.
12. Nếu không thể hoàn thành một tích hợp bên ngoài vì thiếu secret/tài khoản/điều kiện mạng, vẫn hoàn thành mã nguồn và mock/test nội bộ phù hợp; ghi chính xác các thao tác thủ công cần thực hiện. Không giả vờ deploy thành công.

### Trình tự ưu tiên

**Ứng dụng chạy được → kết quả model thật → bảo mật cơ bản → test → UX/error states → cloud deployment → tài liệu hoàn chỉnh.** Không làm hiệu ứng giao diện trước khi pipeline inference thật hoạt động.

---

## 1. Tầm nhìn sản phẩm

LiveInspectAI là ứng dụng demo kiểm tra bất thường bề mặt/ngoại quan bằng computer vision. Người dùng mở web app, kết nối webcam hoặc tải ảnh lên, gửi ảnh đến backend; backend chuyển tác vụ qua kết nối WebSocket bảo mật tới AI Agent chạy trên máy Windows của nhóm. Agent dùng model PatchCore đã huấn luyện để trả về điểm bất thường và anomaly heatmap. Web app hiển thị ảnh, lớp phủ heatmap, trạng thái Normal/Anomaly/Uncertain và lưu lịch sử kiểm tra.

### Mục tiêu MVP

- Chạy được end-to-end trên máy phát triển Windows 11.
- Một danh mục MVTec AD được hỗ trợ ban đầu: **`screw`**.
- Huấn luyện và đánh giá PatchCore bằng dữ liệu thật, không dùng response giả làm kết quả AI.
- Dùng ảnh tải lên, chụp webcam một ảnh và chế độ Live Preview có giới hạn FPS.
- AI inference chạy trên PC cục bộ, tận dụng NVIDIA GTX 1660 Ti khi môi trường CUDA/PyTorch tương thích; có đường chạy CPU để debug/fallback.
- Frontend và API có thể triển khai cloud; AI Agent kết nối **đi ra ngoài** bằng WSS, không mở cổng inbound trên máy cá nhân.
- Người dùng đăng nhập, xem lịch sử của chính mình, xem chi tiết kết quả, tải kết quả và xóa lịch sử.
- Có trạng thái Agent online/offline, thông báo lỗi rõ ràng, timeout và reconnect.
- Có test, log an toàn, `.env.example`, hướng dẫn cài đặt/train/deploy/troubleshooting và checklist demo.

### Giới hạn sản phẩm cần công khai

- Model đầu tiên được huấn luyện cho **một danh mục `screw`**, không được quảng cáo là phát hiện lỗi trên mọi vật thể tùy ý.
- PatchCore là anomaly detection: model học ảnh bình thường và tìm vùng khác biệt so với dữ liệu huấn luyện. Kết quả phụ thuộc dataset, ánh sáng, góc chụp, khoảng cách, chất lượng ảnh và ngưỡng phân loại.
- Điểm hiển thị dạng phần trăm chỉ là **điểm bất thường được quy đổi để dễ đọc**, không được gọi là xác suất model đúng nếu chưa hiệu chuẩn xác suất riêng.
- Bản MVP là đồ án/demo nhóm nhỏ, chưa phải hệ thống kiểm định công nghiệp hoặc hệ thống an toàn.

---

## 2. Người dùng và luồng sử dụng chính

### Vai trò

- **Người dùng đã đăng nhập:** chụp/tải ảnh, chạy kiểm tra, xem kết quả và lịch sử của tài khoản mình, tải báo cáo, xóa bản ghi của mình.
- **Chủ máy AI Agent:** chạy Agent trên PC có model; cấu hình endpoint/token qua environment; kiểm tra trạng thái và logs. Đây là thao tác vận hành, không phải quyền truy cập dữ liệu của người khác.
- **Quản trị demo:** cấu hình danh sách người được phép tạo tài khoản hoặc bật/tắt đăng ký nếu nhà cung cấp auth hỗ trợ. Không xây dựng hệ thống phân quyền doanh nghiệp phức tạp trong MVP.

### Luồng chuẩn

1. Người dùng mở website HTTPS, đăng nhập.
2. Dashboard hiển thị trạng thái dịch vụ và AI Agent (online/offline/initializing), model đang nạp, số kiểm tra gần đây.
3. Người dùng mở **Inspect**, chọn `Screw — MVTec AD`, sau đó chọn camera hoặc tải ảnh JPEG/PNG/WebP.
4. Người dùng chụp một ảnh hoặc bật Live Preview. Frontend resize/nén bản sao gửi đi, không thay đổi ảnh gốc đang hiển thị.
5. API xác thực người dùng và kiểm tra file, gán `request_id`, đưa yêu cầu vào hàng đợi có giới hạn rồi gửi ảnh qua WSS tới Agent.
6. Agent chạy inference, trả về prediction, raw score, threshold, latency và heatmap thật.
7. Backend kiểm tra response rồi lưu metadata kết quả cho đúng user; nếu lưu ảnh được bật và đã cấu hình storage thì lưu ảnh/heatmap vào bucket riêng tư.
8. Frontend hiển thị kết quả, overlay, giải thích giới hạn, nút chụp lại/tải kết quả/xem lịch sử.
9. Người dùng mở History, lọc và xem chi tiết các lần kiểm tra trước; chỉ thấy dữ liệu của bản thân.
10. Nếu Agent mất kết nối hoặc model lỗi, UI hiển thị lỗi phù hợp, không tự hiển thị kết quả thành công giả.

---

## 3. Kiến trúc mục tiêu

### Thành phần

1. **Frontend:** React + TypeScript + Vite; responsive cho desktop/tablet; dùng HTTPS để trình duyệt cho phép camera.
2. **API backend:** Python + FastAPI; cung cấp REST API, OpenAPI, xác thực, kiểm tra input, hàng đợi inference giới hạn, lưu lịch sử và endpoint WebSocket cho Agent.
3. **Local AI Agent:** Python chạy trên Windows 11, giữ WSS connection đi ra backend, tải model local, nhận ảnh theo yêu cầu và trả kết quả PatchCore.
4. **ML pipeline:** PatchCore dựa trên Anomalib hoặc implementation được kiểm chứng tương đương. Chọn **một** cách triển khai, pin version và không đổi framework giữa chừng nếu không có lý do kỹ thuật.
5. **Auth/Database:** Supabase Auth + PostgreSQL là phương án mặc định nếu cấu hình được. Dùng migrations/schema có kiểm soát và kiểm tra quyền truy cập theo `user_id`.
6. **Object storage:** Supabase Storage bucket private, chỉ bật lưu ảnh nếu đã cấu hình. Mặc định có thể chỉ lưu metadata để giảm rủi ro dữ liệu.
7. **Deployment:** frontend trên Cloudflare Pages hoặc host static tương đương; API trên nền tảng hỗ trợ FastAPI và WebSocket kết nối dài; database/auth/storage trên Supabase. Agent vẫn chạy trên PC nhóm.

### Sơ đồ giao tiếp

```text
Browser (HTTPS)
   | REST: login/session/upload/history
   v
FastAPI cloud service <----> PostgreSQL/Auth/Private Storage
   |
   | WSS outbound persistent connection from Agent
   v
Local AI Agent (Windows 11, GTX 1660 Ti)
   |
   v
PatchCore model + preprocessing + anomaly map
```

### Quy tắc giao tiếp

- Browser **không** kết nối trực tiếp đến IP/port máy AI.
- Agent mở kết nối WSS tới API và xác thực bằng token riêng.
- Mọi tác vụ dùng `request_id`/correlation ID; response phải khớp request tương ứng.
- Một Agent chạy trên một GPU và một model mặc định. MVP có thể xử lý **một tác vụ inference tại một thời điểm**, các yêu cầu khác được xếp hàng có giới hạn.
- Live Preview có throttle, mặc định tối đa 1–2 frame/giây; chỉ giữ một frame đang xử lý, bỏ frame cũ nếu người dùng liên tục tạo frame mới. Không xếp hàng vô hạn.
- Dùng ảnh JPEG nén và giới hạn kích thước/độ phân giải trước khi gửi; vẫn giữ ảnh gốc trong browser nếu người dùng cần tải xuống.
- WSS ping/pong hoặc heartbeat có timeout; Agent reconnect với exponential backoff có jitter.
- Nếu API/Agent mất kết nối, các tác vụ chờ phải kết thúc với lỗi có mã, không bị treo vô thời hạn.
- Backend không giả định Agent luôn online. Readiness của API và readiness của AI là hai trạng thái riêng.

### Mặc định vận hành cần có cấu hình

- `APP_ENV=development|production`
- `API_BASE_URL`
- `FRONTEND_ORIGINS`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (frontend nếu cần)
- `SUPABASE_SERVICE_ROLE_KEY` (backend only)
- các biến JWT/JWKS tương ứng với thiết lập Auth thực tế
- `AGENT_ID`
- `AGENT_TOKEN` (backend và Agent, không phải frontend)
- `AGENT_WS_URL`
- `MODEL_PATH`
- `MODEL_CONFIG_PATH`
- `DATASET_ROOT`
- `MAX_UPLOAD_BYTES`
- `MAX_IMAGE_PIXELS`
- `INFERENCE_TIMEOUT_SECONDS`
- `AGENT_HEARTBEAT_SECONDS`
- `MAX_INFERENCE_QUEUE`
- `SAVE_IMAGES=false` mặc định
- `STORAGE_BUCKET` và retention config nếu bật lưu ảnh

Tạo `.env.example` chỉ chứa ví dụ không bí mật. Kiểm tra biến bắt buộc ngay lúc startup và hiển thị lỗi cấu hình dễ hiểu.

---

## 4. Cấu trúc repository mục tiêu

Giữ cấu trúc hiện tại nếu repository đã có tổ chức hợp lý. Nếu bắt đầu từ repo trống, tạo cấu trúc tương đương:

```text
LiveInspectAI/
├── PLAN.md
├── README.md
├── .gitignore
├── .editorconfig
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── API.md
│   ├── DATASET_AND_MODEL.md
│   ├── WINDOWS_SETUP.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY_AND_PRIVACY.md
│   ├── USER_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   ├── TEST_PLAN.md
│   └── DEMO_CHECKLIST.md
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── features/auth/
│   │   │   ├── features/dashboard/
│   │   │   ├── features/inspect/
│   │   │   ├── features/history/
│   │   │   ├── features/settings/
│   │   │   ├── lib/
│   │   │   ├── services/
│   │   │   ├── types/
│   │   │   └── test/
│   │   ├── public/
│   │   ├── package.json
│   │   ├── .env.example
│   │   └── vite.config.ts
│   ├── api/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   ├── api/v1/
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   ├── db/
│   │   │   ├── storage/
│   │   │   └── agent_gateway/
│   │   ├── migrations/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── agent/
│       ├── liveinspect_agent/
│       │   ├── __main__.py
│       │   ├── config.py
│       │   ├── connection.py
│       │   ├── protocol.py
│       │   ├── inference.py
│       │   ├── model_loader.py
│       │   ├── health.py
│       │   └── logging_config.py
│       ├── tests/
│       ├── environment.yml
│       ├── pyproject.toml
│       └── .env.example
├── ml/
│   ├── configs/
│   ├── scripts/
│   │   ├── check_environment.py
│   │   ├── validate_dataset.py
│   │   ├── train_patchcore.py
│   │   ├── evaluate_model.py
│   │   └── export_model.py
│   ├── src/liveinspect_ml/
│   │   ├── dataset.py
│   │   ├── preprocessing.py
│   │   ├── scoring.py
│   │   ├── postprocessing.py
│   │   └── metrics.py
│   └── tests/
├── scripts/
│   ├── dev_check.ps1
│   ├── smoke_test.py
│   └── generate_demo_data.py
└── .github/workflows/
    └── ci.yml
```

Không nhất thiết phải tạo file rỗng cho mọi mục. Chỉ tạo file khi có nội dung/logic thực tế. Tách code theo trách nhiệm, tránh một file vài nghìn dòng.

---

## 5. Phạm vi chức năng bắt buộc

### 5.1 Authentication và quyền dữ liệu

- Đăng nhập/đăng xuất; đăng ký chỉ bật nếu đã quyết định phạm vi demo và cấu hình được provider.
- Khi chưa đăng nhập, chỉ truy cập trang landing/login và endpoint health public đã cho phép.
- Backend xác thực JWT thật trên mọi endpoint dữ liệu. Không tin `user_id` gửi từ frontend.
- Mỗi lịch sử/kết quả thuộc user hiện tại; không cho đổi ID trong URL để xem dữ liệu người khác.
- Có thông báo rõ khi phiên đăng nhập hết hạn.
- Nếu Supabase chưa cấu hình, ứng dụng development phải trả lỗi cấu hình rõ ràng; không tự chuyển sang tài khoản giả trong production.

### 5.2 Dashboard

Hiển thị:
- Trạng thái API.
- Trạng thái Agent: online/offline/connecting/model-loading/error và `last_seen`.
- Tên/category model đang hoạt động.
- Tổng số lần kiểm tra của user và một số kết quả gần đây.
- Hành động chính: `Bắt đầu kiểm tra`, `Lịch sử`, `Hướng dẫn`.
- Thông báo nếu Agent offline hoặc model chưa sẵn sàng.

Không hiển thị số liệu analytics giả hoặc cứng trong code.

### 5.3 Inspection workspace

- Chọn chế độ `Upload ảnh`, `Chụp một ảnh`, `Live Preview`.
- Camera sử dụng `navigator.mediaDevices.getUserMedia`, xin quyền rõ ràng, có nút dừng camera và xử lý trường hợp bị từ chối/không có thiết bị.
- Upload bằng file picker và drag-and-drop; chấp nhận JPEG/PNG/WebP; preview trước khi gửi.
- Hiển thị category model và lời nhắc hiện tại chỉ hỗ trợ `screw`.
- Nút `Kiểm tra`; trạng thái idle/loading/success/error/timeout/agent offline.
- Không tạo tác vụ trùng liên tục do nhấn nút nhiều lần.
- Live Preview mặc định 1 frame/giây (có thể cấu hình đến 2 FPS), có chỉ báo đang xử lý và tự bỏ frame lỗi thời.
- Cho phép dừng live ngay lập tức, giải phóng camera stream và huỷ timer/request nếu có thể.
- Có tùy chọn hiển thị/ẩn heatmap overlay và chỉnh opacity trên canvas; overlay phải dùng heatmap do model trả về.
- So sánh ảnh gốc với ảnh overlay; giữ đúng tỷ lệ/crop. Không vẽ bounding box ngẫu nhiên hoặc heatmap minh họa giả.
- Hiện prediction (`NORMAL`, `ANOMALY`, `UNCERTAIN`), anomaly score, threshold dùng để quyết định, inference latency và thời điểm kiểm tra.
- Hiển thị lưu ý: score không phải xác suất, ánh sáng/góc chụp ảnh ảnh hưởng kết quả.
- Có nút lưu lịch sử (nếu không auto-save) hoặc chỉ báo đã lưu; xử lý trường hợp inference thành công nhưng lưu lịch sử thất bại một cách rõ ràng.
- Tải kết quả JSON/CSV hoặc tải ảnh overlay xuống máy. Export không được bao gồm token/secret.

### 5.4 Kết quả và lịch sử

Một bản ghi kết quả tối thiểu lưu:
- `id`, `user_id`, `session_id` nếu áp dụng.
- `created_at` UTC.
- `model_name`, `model_version`, `category`.
- `prediction`, `anomaly_score_raw`, `display_score` nếu có, `threshold`.
- `inference_ms`, `image_width`, `image_height`.
- `agent_id`/model metadata phù hợp; không lưu token.
- `image_path` và `heatmap_path` nullable nếu bật lưu ảnh.
- error/status fields nếu lưu cả tác vụ thất bại; không nhầm tác vụ fail thành prediction.

Lịch sử phải hỗ trợ:
- Danh sách có pagination, sắp xếp mới nhất trước.
- Lọc theo prediction/category và khoảng thời gian khi phù hợp.
- Trang chi tiết mở được kết quả cụ thể của user hiện tại.
- Xóa bản ghi của user; nếu dùng storage, xóa object liên quan hoặc đánh dấu cleanup rõ ràng.
- Export CSV đúng các bản ghi mà user được quyền xem.
- Empty state/loading/error state.

### 5.5 Trạng thái vận hành

- Health endpoint của API.
- Readiness endpoint thể hiện DB có sẵn không.
- Endpoint/trường trạng thái Agent online, thời gian heartbeat cuối và model sẵn sàng.
- Không tiết lộ stack trace, secret hoặc đường dẫn máy chủ trong response production.
- Logs có correlation/request ID để truy dấu tác vụ.

---

## 6. ML: Dataset, huấn luyện, đánh giá và inference

### 6.1 Dataset

- Dataset mục tiêu: **MVTec Anomaly Detection (MVTec AD)**, category `screw`.
- Người dùng/nhóm phải tự tải từ nguồn phát hành hợp lệ và chấp nhận điều khoản dataset; không scrape không rõ nguồn và không commit ảnh dataset vào Git.
- `DATASET_ROOT` phải được cấu hình. Script cần kiểm tra cấu trúc thư mục và đưa thông báo lỗi dễ hiểu nếu thiếu `train/good`, `test` hoặc ground-truth masks.
- Ghi rõ nguồn tải, điều khoản, cấu trúc mong đợi và lệnh chạy trong `docs/DATASET_AND_MODEL.md`.
- Tạo công cụ kiểm tra dataset, số lượng file theo split, định dạng ảnh, corrupt file, mask và leakage.
- Không tự tải dataset khi agent chạy API/Agent thông thường; chỉ tải khi người phát triển chủ động chạy script.

### 6.2 Đường huấn luyện

1. Kiểm tra Python/PyTorch/CUDA/GPU, bộ nhớ và path dataset.
2. Pin version Python, PyTorch, Anomalib và dependency theo bộ phiên bản tương thích đã xác minh. Lưu lockfile hoặc constraint rõ ràng.
3. Tạo config có thể đọc và chỉnh: category, image size, backbone, batch size nếu framework dùng, accelerator, random seed, output path, dataset root.
4. Huấn luyện PatchCore chỉ bằng ảnh normal thuộc split train.
5. Lưu model weights/checkpoint, cấu hình preprocessing, tên/version model, thông tin môi trường, seed, ngày huấn luyện và checksum nếu khả thi.
6. Không lưu các path tuyệt đối của máy cá nhân làm dependency bắt buộc trong artifacts.
7. Không ghi model weights vào Git; thêm `models/`, checkpoint và output nặng vào `.gitignore`.
8. Có thể chạy inference trên CPU cho kiểm thử; ưu tiên CUDA trên máy GTX 1660 Ti khi `torch.cuda.is_available()` trả về true.
9. Khi CUDA lỗi, in lý do chẩn đoán và cho phép explicit CPU fallback; không tự âm thầm giả vờ đang dùng GPU.

### 6.3 Tiền xử lý phải thống nhất

- Một pipeline preprocessing duy nhất được dùng nhất quán khi evaluate và inference.
- Khóa kích thước input, resize/crop, RGB/BGR, normalize mean/std và interpolation thành model metadata/config.
- Nếu ảnh web bị resize, frontend không dùng một tỉ lệ khác với backend một cách không kiểm soát.
- Lưu lại kích thước gốc và kích thước model input để resize heatmap về đúng hệ tọa độ ảnh gốc.
- Test preprocessing với ảnh test cố định để output có shape/range hợp lệ.

### 6.4 Ngưỡng và đầu ra

Đầu ra inference tối thiểu:

```json
{
  "request_id": "uuid",
  "status": "success",
  "model_name": "patchcore-mvtec-screw",
  "model_version": "version-from-artifact",
  "category": "screw",
  "prediction": "NORMAL | ANOMALY | UNCERTAIN",
  "anomaly_score_raw": 0.0,
  "display_score": 0.0,
  "threshold": 0.0,
  "inference_ms": 0,
  "image_width": 0,
  "image_height": 0,
  "heatmap_png_base64": "..."
}
```

- Đây là schema minh họa; định nghĩa schema Python/TypeScript dùng chung về mặt khái niệm và validate trước khi phản hồi.
- Không lấy số minh họa ở trên làm kết quả cố định.
- `anomaly_score_raw` phải là điểm thật model trả về; ghi cách quy đổi `display_score` trong docs. Không gọi `display_score` là accuracy hoặc xác suất.
- Ngưỡng không được chọn tùy tiện bằng một hằng số không giải thích. Tạo cơ chế calibration và lưu threshold trong metadata.
- Có thể trả `UNCERTAIN` nếu score gần vùng threshold hoặc model status không đủ tin cậy; công khai cách định nghĩa vùng này. Nếu không triển khai vùng uncertainty ở vòng đầu, schema/UI vẫn phải phân biệt `error` với `anomaly`, không biến lỗi thành `ANOMALY`.
- Heatmap phải là đầu ra anomaly map của model, chuyển sang PNG một cách an toàn và có kích thước giới hạn.

### 6.5 Quy trình evaluation

- Có script `evaluate_model.py` chạy lặp lại được và lưu báo cáo JSON/CSV.
- Dùng các ảnh official test chỉ cho đánh giá cuối cùng. Nếu cần threshold calibration, dùng một tập normal calibration tách khỏi train fit, hoặc định nghĩa split validation riêng có tài liệu; tuyệt đối không dùng test holdout để tinh chỉnh threshold.
- Báo cáo tối thiểu: image-level AUROC; precision/recall/F1 tại threshold đã cố định nếu ground truth phù hợp; pixel-level AUROC nếu ground-truth masks và metric implement đúng; confusion matrix; số ảnh/split; latency trung bình, median và p95 trên môi trường đã ghi rõ.
- Ghi seed, model config, phiên bản thư viện, thiết bị, split và command chạy.
- Không hard-code benchmark kỳ vọng thành kết quả thực tế. Có thể đặt mục tiêu nghiên cứu nhưng phải đánh dấu target, không phải cam kết.
- Nếu metric thấp hoặc threshold không tách normal/anomaly tốt, báo cáo đúng thực tế, điều tra preprocessing/data issue và ghi hạn chế; không giấu test fail.

### 6.6 Test ML bắt buộc

- Dataset validator bắt được thiếu file/corrupt file.
- Model loader báo lỗi dễ hiểu khi artifact/metadata thiếu hoặc không tương thích.
- Inference trả ra score hữu hạn (`finite`), heatmap hợp lệ, shape đúng và latency không âm.
- Kiểm tra ảnh normal và ảnh anomaly thực tế của category `screw` trên tập sample. Không ép test khẳng định mọi ảnh anomaly phải phân loại đúng; kiểm tra contract và báo cáo metric riêng.
- Test CPU fallback và CUDA diagnostics (CUDA test có thể skip có giải thích khi runner không có GPU).
- Test không dùng test images để train model.

---

## 7. API backend

### 7.1 API tối thiểu

Dùng prefix `/api/v1`. Tên chính xác có thể được điều chỉnh, nhưng contract trong `docs/API.md` phải nhất quán giữa frontend, backend và Agent.

- `GET /healthz` — API process đang chạy.
- `GET /readyz` — config/database readiness; không được coi Agent offline là API process chết.
- `GET /api/v1/status` — trạng thái dịch vụ và Agent cho user đã xác thực.
- `POST /api/v1/inspections` — tạo inspection/session nếu cần.
- `POST /api/v1/inferences` — gửi một ảnh để inference; xác thực user; validate image; trả result hoặc lỗi có mã.
- `GET /api/v1/inspections` — history có pagination/filter.
- `GET /api/v1/inspections/{inspection_id}` — chi tiết theo quyền user.
- `DELETE /api/v1/inspections/{inspection_id}` — xóa record theo quyền user.
- `GET /api/v1/inspections/export.csv` — export lịch sử theo filter có validate.
- `WS /api/v1/agent/ws` — kết nối riêng cho AI Agent; chỉ cho phép khi auth token hợp lệ.

Agent endpoint không xuất hiện trong UI công khai ngoài trạng thái online/offline; không cung cấp chức năng chạy lệnh remote tùy ý.

### 7.2 Hợp đồng lỗi

Trả JSON lỗi có cấu trúc nhất quán:

```json
{
  "error": {
    "code": "AGENT_OFFLINE",
    "message": "AI Agent hiện không kết nối. Hãy kiểm tra máy đang chạy Agent.",
    "request_id": "uuid"
  }
}
```

Mã lỗi dự kiến: `UNAUTHENTICATED`, `FORBIDDEN`, `INVALID_IMAGE`, `IMAGE_TOO_LARGE`, `IMAGE_DIMENSIONS_UNSUPPORTED`, `AGENT_OFFLINE`, `AGENT_BUSY`, `INFERENCE_TIMEOUT`, `MODEL_NOT_READY`, `INFERENCE_FAILED`, `DATABASE_UNAVAILABLE`, `STORAGE_UNAVAILABLE`, `RATE_LIMITED`, `INTERNAL_ERROR`.

Không trả exception stack trace cho client trong production. Log chi tiết ở server nhưng không log token hoặc raw ảnh.

### 7.3 Hàng đợi và concurrency

- Giới hạn request body, thời gian xử lý, số tác vụ đang chờ và tốc độ request theo user.
- MVP cho phép một inference chạy đồng thời trên Agent; hàng đợi có giới hạn rõ ràng.
- Nếu đầy, trả `AGENT_BUSY`/`RATE_LIMITED` sớm thay vì giữ connection mãi.
- Mỗi yêu cầu có timeout đầu-cuối và correlation ID. Khi browser hủy request, backend cố gắng hủy tác vụ chưa chạy; nếu không thể hủy inference đang chạy thì bỏ response lỗi thời nhưng vẫn giải phóng lock.
- Khi Agent disconnect giữa inference, mọi Future đang chờ phải được resolve bằng lỗi và trạng thái Agent phải cập nhật.
- Không gửi cùng một ảnh liên tục từ Live Preview nếu request trước đang xử lý.

### 7.4 WebSocket protocol

Tạo protocol có version, validate schema và được mô tả trong `docs/API.md`.

Các message logic tối thiểu:

- Agent → server: `agent_hello` gồm protocol version, agent ID, agent version, capabilities.
- Server → Agent: `hello_ack` và cấu hình heartbeat/limits tối thiểu không chứa secret.
- Server → Agent: `infer_request` chứa `request_id`, category/model, input metadata; ngay sau đó là payload ảnh theo quy ước đã định.
- Agent → server: `infer_result` chứa cùng `request_id` và output schema; hoặc `infer_error` với code/message an toàn.
- Hai phía: `heartbeat`/`heartbeat_ack` hoặc ping/pong.
- Agent gửi status cập nhật khi model bắt đầu load, ready hoặc gặp lỗi.

Quy ước payload ảnh phải được implement nhất quán. Ưu tiên binary WebSocket message đi cùng metadata JSON; nếu chọn base64 JSON vì độ đơn giản, phải giới hạn kích thước, kiểm tra encoding và ghi rõ overhead. Không trộn hai định dạng ngầm.

Server phải:
- Xác thực trước khi chấp nhận Agent.
- Từ chối protocol version không hỗ trợ.
- Kiểm tra request ID khớp.
- Không cho Agent chọn arbitrary filesystem path, URL nội bộ hoặc command để chạy.
- Quản lý lock/hàng đợi cho kết nối Agent đơn.
- Không cho phép connection mới thay thế Agent hợp lệ mà không có policy; tối thiểu đóng/kết thúc session cũ và ghi log.

Agent phải:
- Không lắng nghe cổng public.
- Validate message và payload trước inference.
- Tải model một lần lúc startup, không reload model theo từng frame.
- Có reconnect exponential backoff với giới hạn tối đa và jitter.
- Dừng gọn khi nhận signal/đóng ứng dụng; không lộ token trong logs.

---

## 8. Database và lưu trữ

### 8.1 Schema logic

Thiết kế migrations rõ ràng. Schema thực tế có thể khác nhưng cần đáp ứng các thực thể:

- `profiles` (chỉ nếu cần dữ liệu ngoài Auth provider): `user_id`, `created_at`, `display_name` tùy chọn.
- `inspections`: `id`, `user_id`, `created_at`, `status`, `category`, `model_name`, `model_version`, `image_width`, `image_height`, `error_code` nullable, `inference_ms` nullable, storage paths nullable.
- Có thể dùng một bảng `inspection_results` riêng nếu thiết kế cần giữ session/result tách biệt. Không tạo bảng trùng trách nhiệm.

Mọi thời gian lưu UTC. Dùng ID UUID hoặc định danh khó đoán. Index các truy vấn history phổ biến (`user_id`, `created_at`) và các filter thực tế.

### 8.2 Quy tắc truy cập

- Mọi query history/detail/delete phải scope theo user đã xác thực.
- Nếu frontend kết nối Supabase trực tiếp để đọc, bật Row Level Security (RLS) và viết policy/test. Nếu chỉ backend truy cập DB bằng service role, backend vẫn bắt buộc filter user trong mọi query; service role không được thay cho authorization logic.
- Service role key chỉ ở backend secret store.
- Không lưu raw image hoặc heatmap mặc định nếu `SAVE_IMAGES=false`.
- Nếu lưu ảnh: private bucket, tên object random, signed URL ngắn hạn, kiểm tra quyền record trước khi tạo signed URL, có cơ chế xóa object và retention policy.
- Dùng migrations/versioning để tạo schema; không yêu cầu thao tác SQL thủ công không được ghi trong docs.

---

## 9. Frontend UX và thiết kế

### Nguyên tắc

- Giao diện sạch, rõ, hiện đại, hướng tới thao tác kiểm tra ảnh chứ không phải dashboard trang trí.
- Ưu tiên desktop vì webcam và đồ án demo; vẫn responsive ở tablet/mobile.
- Dùng các component dùng lại được cho loading, error, empty, badge trạng thái và xác nhận xóa.
- Mọi nút phải thực sự hoạt động hoặc được disable kèm lý do; không tạo nút trang trí.
- Có keyboard focus, nhãn form, tương phản màu, trạng thái không chỉ dựa vào màu sắc.
- Có Việt hóa UI mặc định; tên biến/field/code dùng tiếng Anh. Có thể dùng English labels nếu repo hiện tại đã theo tiếng Anh nhưng phải nhất quán.
- Không dùng animation nặng ảnh hưởng việc cập nhật preview.

### Trang tối thiểu

1. **Landing/Login:** giới thiệu đúng khả năng và hạn chế, đăng nhập, lỗi auth.
2. **Dashboard:** API/Agent/model status, số liệu thật, lối vào Inspect/History.
3. **Inspect:** camera/upload, capture/live preview, ảnh gốc, heatmap overlay, score/prediction, controls.
4. **Result detail:** ảnh, overlay, score và threshold, latency, model version, ngày giờ, ghi chú giới hạn.
5. **History:** pagination, filter, delete, export, empty/error state.
6. **Settings/System:** trạng thái kết nối, version app/model, hướng dẫn vận hành; không hiển thị secret/token.
7. **Not found / authorization expired / service unavailable** states.

### Trạng thái UI cần test

- Camera chưa xin quyền, quyền bị từ chối, không có camera, camera bận.
- Chưa chọn file, file không hợp lệ, file quá lớn, ảnh corrupt.
- Agent online, offline, connecting, model loading, inference busy, timeout.
- Mạng chập chờn khi upload hoặc khi lấy lịch sử.
- Không có dữ liệu, dữ liệu nhiều trang, lịch sử bị xóa.
- Auth hết hạn và database/storage tạm thời không sẵn sàng.
- Heatmap không hợp lệ: hiển thị lỗi kết quả trực quan, không crash UI.

---

## 10. Bảo mật, riêng tư và độ tin cậy

Bắt buộc thực hiện những mục sau trước khi gọi bản demo là hoàn chỉnh:

- HTTPS/WSS trên môi trường deploy; không vô hiệu TLS verification để “sửa” kết nối.
- CORS allowlist theo domain frontend, không dùng wildcard trong production nếu có credentials.
- JWT validation thực sự, kiểm tra chữ ký, issuer/audience và expiry theo thư viện/provider đã chọn.
- Agent token riêng, đủ entropy, chỉ truyền qua secret environment; constant-time comparison nếu tự so token.
- Rotate/revoke được token theo hướng dẫn vận hành; không ghi token trong logs hoặc frontend bundle.
- Validate MIME **và** decode nội dung file, không chỉ tin extension; giới hạn byte, chiều rộng/cao và tổng số pixel; chặn ảnh corrupt và decompression bombs.
- Rate limit theo user/IP phù hợp với demo; giới hạn Live Preview và hàng đợi.
- Authz: mọi record thuộc tài khoản hiện tại; test quyền truy cập chéo tài khoản.
- Không cho phép arbitrary path, URL fetch hoặc command từ client/Agent protocol.
- Không log nội dung ảnh/base64, Authorization header, secret hoặc thông tin nhạy cảm không cần thiết.
- Bảo vệ error messages; verbose trace chỉ ở development.
- Bật RLS nếu dùng truy cập client-side Supabase; viết migration/policy và test.
- Secrets chỉ ở deployment environment variables; `.env` được ignore.
- Có trang/section privacy ngắn giải thích ảnh đi qua cloud API tới máy Agent và có/không lưu trong storage theo cấu hình.
- Xóa dữ liệu theo yêu cầu; nếu không lưu ảnh thì giải thích history lưu metadata thôi.
- Nếu `SAVE_IMAGES=true`, xác định retention và cơ chế cleanup; không để ảnh công khai.
- Kiểm tra dependency bằng công cụ audit phù hợp và ghi các cảnh báo chưa giải quyết.

Đây là sản phẩm demo, không tuyên bố đạt chứng nhận bảo mật hay tuân thủ quy định mà chưa được đánh giá chính thức.

---

## 11. Cấu hình môi trường và cài đặt Windows 11

### 11.1 Tách môi trường

- Frontend: Node LTS tương thích với phiên bản Vite/React được pin; giữ lockfile (`package-lock.json`, `pnpm-lock.yaml` hoặc tương đương), không trộn package managers.
- Backend: Python environment riêng.
- Agent/ML: environment riêng cho PyTorch/Anomalib/CUDA để dependency nặng không ảnh hưởng API.
- Dùng Conda environment cho Agent/ML vì người dùng dự định dùng Anaconda.
- Backend có `pyproject.toml` và lock/constraints.
- Không yêu cầu cài CUDA Toolkit nếu bộ PyTorch wheel đã đóng gói runtime cần thiết; docs phải kiểm tra driver/GPU theo bộ version đã chọn và chỉ hướng dẫn cài phần thật sự cần.

### 11.2 Tài liệu phải cho người mới

`docs/WINDOWS_SETUP.md` phải hướng dẫn theo thứ tự, có lệnh copy/paste:

1. Cài Git, Anaconda/Miniconda và Node LTS.
2. Clone repo và tạo các environment.
3. Copy `.env.example` sang `.env` trong từng component rồi điền local config.
4. Tạo/configure Supabase nếu chạy tính năng cloud/local auth cần DB; giải thích cách chạy ở chế độ local khi chưa có cloud credentials mà không giả lập kết quả AI.
5. Tải MVTec AD và đặt đúng folder.
6. Chạy dataset validator.
7. Cài PyTorch phù hợp; chạy `check_environment.py` để xác nhận GTX 1660 Ti/CUDA. Ghi rõ cách fallback CPU để debug.
8. Train PatchCore và evaluate; chỉ tiếp tục production demo khi model artifacts đã tồn tại.
9. Chạy backend, Agent, frontend trong ba terminal riêng.
10. Test `healthz`, Agent status, login và một inference ảnh thật.
11. Các lỗi thường gặp: CUDA unavailable, driver, port trùng, CORS, auth config, Agent token sai, WSS/TLS, dataset path, model path, camera không hoạt động ngoài HTTPS/localhost.

Mọi command trong tài liệu phải được thử thực tế trong môi trường của agent hoặc được đánh dấu rõ là chưa thể kiểm chứng trên nền tảng hiện tại.

---

## 12. Kế hoạch triển khai theo phase

> Đi đúng thứ tự. Không đánh dấu phase hoàn tất chỉ vì đã tạo file. Chỉ tick sau khi chạy kiểm thử/nghiệm thu tương ứng.

### Phase 0 — Repository reconnaissance và chốt quyết định

- [x] Đọc repository, Git status, README, manifests, source và tests.
- [x] Liệt kê những gì đã có, những gì thiếu, các điểm có nguy cơ phá vỡ code cũ.
- [x] Ghi architecture/technology decisions trong `docs/DECISIONS.md`.
- [x] Xác nhận cách dùng Anomalib/PatchCore và pin bộ version tương thích.
- [x] Chọn protocol Agent↔API, schema result, strategy auth/database/storage.
- [x] Chọn nhà cung cấp cloud có WebSocket phù hợp, xem điều kiện hiện tại từ tài liệu chính thức; ghi limits/free-tier/sleep/cold-start và các khoản có thể phát sinh.
- [x] Không nhúng provider key/credential vào code.

**Nghiệm thu:** Có decision log ngắn có lý do, lựa chọn chính, phương án dự phòng; repository sạch và không có thay đổi phá hoại chưa giải thích.

### Phase 1 — Scaffold và quality gates

- [x] Tạo/củng cố cấu trúc repo và `.gitignore`.
- [x] Tạo Python manifests, frontend package manifest và lockfiles.
- [x] Tạo `.env.example` cho từng app, kiểm tra `.env` bị ignore.
- [x] Cấu hình formatter/linter/type checks: frontend ESLint + TypeScript; Python Ruff và type checking phù hợp.
- [x] Tạo API FastAPI tối thiểu gồm `healthz`, `readyz`, OpenAPI.
- [x] Tạo frontend shell có routing, layout, error boundary và trang trạng thái API.
- [x] Tạo Agent CLI có `--help`, validate config và log startup an toàn.
- [x] Tạo CI GitHub Actions chạy lint/typecheck/test/build; CI không cần secrets cloud.

**Nghiệm thu:** Cài dependency sạch theo docs; frontend build được; backend startup và healthz được; Agent CLI help chạy được; CI xanh.

### Phase 2 — Dataset và model PatchCore thật

- [x] Hoàn thành dataset validator cho category `screw`.
- [x] Xây pipeline train/evaluate/inference theo version framework đã pin.
- [x] Tạo config mẫu và quản lý artifacts bên ngoài Git.
- [x] Thêm threshold calibration không dùng test holdout để tune.
- [x] Thêm export report JSON/CSV và lưu metadata model.
- [x] Viết unit tests preprocessing, model output và report.
- [x] Chạy thật ít nhất một lần training/evaluation trên máy có môi trường phù hợp nếu có thể; lưu log và đường dẫn artifacts, không đưa ảnh/dữ liệu riêng lên repository.
- [x] Đo và ghi latency thực tế cho một tập sample đã định nghĩa.

**Nghiệm thu:** Lệnh train và eval có documented, output artifact/metadata thật, inference sample trả score và heatmap thật, report có phương pháp/split/metrics; test không giả vờ model đã train nếu thiếu checkpoint.

### Phase 3 — Local AI Agent

- [x] Implement config bằng environment/CLI; không hardcode URL hoặc token.
- [x] Implement model loading một lần, startup readiness và health status.
- [x] Implement WSS connect/auth/hello/heartbeat.
- [x] Implement nhận request, decode ảnh an toàn, gọi inference và serialize response.
- [x] Implement correlation IDs, timeouts, reconnect backoff và graceful shutdown.
- [x] Implement error mapping cho model missing, bad image, inference failure, server disconnect.
- [x] Thêm structured logs; redaction token.
- [x] Test protocol bằng fake/test server và test model bằng artifact có sẵn.

**Nghiệm thu:** Agent kết nối server dev thật, báo `ready` sau khi load model, inference một ảnh đi-về đúng request ID; tắt server hoặc sai token thì hiển thị trạng thái lỗi/reconnect rõ ràng.

### Phase 4 — API inference và dữ liệu

- [x] Implement auth middleware/dependency và test JWT validation.
- [x] Tạo DB migrations/schema, indexes và RLS/backend authorization theo kiến trúc đã chọn.
- [x] Implement Agent connection manager và bounded queue.
- [x] Implement upload validation, input limits, rate limits và error schemas.
- [x] Implement endpoint inference, timeout, correlation, save result metadata.
- [x] Implement history/list/detail/delete/export CSV.
- [x] Implement private storage chỉ khi `SAVE_IMAGES=true`; thêm signed URL có authorization nếu cần.
- [x] Viết API tests: valid, invalid image, too large, unauthenticated, cross-user access, agent offline, agent timeout, malformed response, DB fail.
- [x] Xuất OpenAPI và đồng bộ `docs/API.md`.

**Nghiệm thu:** API dùng model Agent thật end-to-end từ curl/test client; mọi error state có mã rõ; history của user A không trả dữ liệu user B; queue có giới hạn; không có secrets trong response/log.

### Phase 5 — Frontend hoàn chỉnh

- [x] Hoàn thiện auth screens/route guards.
- [x] Hoàn thiện Dashboard lấy trạng thái từ backend thật.
- [x] Hoàn thiện Inspect upload/file validation/preview/camera capture.
- [x] Hoàn thiện Live Preview throttle, bỏ frame cũ, dừng camera sạch.
- [x] Hoàn thiện render ảnh gốc + heatmap overlay thật + opacity control.
- [x] Hiển thị prediction, score/threshold, latency, model version và limitation copy.
- [x] Hoàn thiện History pagination/filter/detail/delete/export.
- [x] Bổ sung loading/empty/error/offline/timeout/auth-expired states.
- [x] Viết unit/component tests và E2E happy-path bằng mock server cho CI; kiểm tra inference thật riêng ở smoke test local.
- [x] Kiểm tra keyboard/accessibility và responsive.

**Nghiệm thu:** Người dùng có thể đăng nhập, kiểm tra ảnh thật, xem heatmap do model trả về, xem kết quả trong lịch sử, export/xóa; không có CTA hỏng hoặc kết quả AI giả.

### Phase 6 — Cloud deploy và vận hành demo

- [ ] Tạo production Dockerfile cho API; chỉ dùng multi-stage tối ưu nếu có lợi và test được.
- [ ] Cấu hình secrets qua provider dashboard, không commit.
- [ ] Deploy schema/migrations và cấu hình Auth/redirect URLs/RLS/storage.
- [ ] Deploy API ở nền tảng hỗ trợ WebSocket dài hạn; kiểm tra idle/sleep/cold start và giới hạn kết nối.
- [ ] Deploy frontend static với environment variables public tối thiểu.
- [ ] Cấu hình HTTPS, WSS, exact CORS origins, allowed auth redirect URLs.
- [ ] Chạy Agent local trỏ về production WSS; xác nhận online/ready.
- [ ] Chạy smoke test từ trình duyệt bên ngoài mạng nội bộ, upload và webcam qua HTTPS.
- [ ] Kiểm tra Agent restart/reconnect, API restart, user logout/login và offline/error state.
- [ ] Viết `docs/DEPLOYMENT.md` với setup từ đầu, rollback, rotate token, migrate DB, shutdown và ước tính chi phí/giới hạn đã kiểm tra.

**Nghiệm thu:** Có URL thực nếu credential cho phép; deployment verification được ghi rõ (ngày, commit, URL, test đã chạy). Nếu thiếu credential, ghi rõ `DEPLOYMENT BLOCKED BY MISSING CREDENTIALS`, nhưng code/config/docs vẫn hoàn chỉnh và deploy local chạy được.

### Phase 7 — Hardening, báo cáo và demo

- [ ] Chạy toàn bộ linter, typecheck, unit tests, integration tests và frontend production build.
- [ ] Chạy smoke test toàn flow có model thật.
- [ ] Chạy test an toàn file/upload/authz/queue/timeouts/secret scan.
- [ ] Đo performance từ thời điểm upload tới kết quả; report median/p95 và điều kiện đo.
- [ ] Test live preview trên máy thực tế; chọn FPS mặc định phù hợp, không tạo queue vô hạn.
- [ ] Viết README end-to-end đủ cho người chưa biết repo.
- [ ] Hoàn thiện architecture, model/dataset/evaluation, API, setup, deployment, troubleshooting, privacy và demo checklist docs.
- [ ] Chuẩn bị lệnh demo, test images được phép phân phối hoặc hướng dẫn lấy mẫu từ dataset; không đưa dữ liệu bị hạn chế vào repo.
- [ ] Ghi known issues/limitations và kết quả test thật.
- [ ] Kiểm tra `git status`, secret scan, file lớn và xác nhận không commit `.env`, dataset, checkpoint nặng.

**Nghiệm thu cuối:** Tất cả tiêu chí trong mục 15 đều đạt hoặc có mục bị chặn được ghi cụ thể với bằng chứng/lý do, không giả vờ hoàn thành.

---

## 13. Kế hoạch thời gian tham khảo cho nhóm 3 người / 6 tuần

Đây là phân chia công việc, không thay thế thứ tự kỹ thuật trong các phase trên.

### Thành viên A — Main coder

- Tuần 1: repo, kiến trúc, API skeleton, database contract, CI.
- Tuần 2: tích hợp PatchCore/inference contract và API/Agent design.
- Tuần 3: Agent WSS, API inference, queue, save results.
- Tuần 4: frontend inspect/camera/overlay/history integration.
- Tuần 5: auth/security fixes, cloud integration, E2E.
- Tuần 6: bug fixing, performance measurements, docs/demo.

### Thành viên B — Cloud/deployment

- Tuần 1: so sánh nhà cung cấp, khởi tạo Supabase/project env và deployment decisions.
- Tuần 2: database schema, auth, private storage policies nếu dùng.
- Tuần 3: deploy test API/websocket hoặc dựng staging.
- Tuần 4: frontend hosting, TLS/WSS/CORS, environment configuration.
- Tuần 5: production/staging integration, reconnect/monitoring, security checks.
- Tuần 6: deployment guide, rollback/backup/secret rotation checklist, chi phí/giới hạn thực tế.

### Thành viên C — Không chuyên code

- Tuần 1: tìm hiểu MVTec AD, category `screw`, license và yêu cầu tài nguyên; tổng hợp nguồn chính thức.
- Tuần 2: tổ chức bảng test case, quy trình lấy sample, checklist đánh giá.
- Tuần 3: test UX và ghi lỗi có steps-to-reproduce, expected/actual/screenshot.
- Tuần 4: thực hiện test trên các camera/ảnh, kiểm tra hướng dẫn sử dụng.
- Tuần 5: tổng hợp metric và kết quả test thực tế, không chỉnh số liệu.
- Tuần 6: báo cáo, slide, demo script, known limitations và nghiệm thu.

### Điểm kiểm tra hàng tuần

- Cuối tuần 1: skeleton khởi động được và kiến trúc thống nhất.
- Cuối tuần 2: PatchCore infer được sample offline với artifact thật.
- Cuối tuần 3: API ↔ Agent end-to-end chạy trong local dev.
- Cuối tuần 4: frontend gửi ảnh và render heatmap thật.
- Cuối tuần 5: staging/cloud kết nối được với Agent cục bộ.
- Cuối tuần 6: test, docs, báo cáo và demo có thể lặp lại.

Nếu trễ tiến độ, bỏ tính năng phụ như đăng ký tự do, dashboard analytics nâng cao hoặc lưu ảnh lâu dài trước; **không** bỏ kiểm tra quyền, validation ảnh, timeout, test kết quả thật hoặc tài liệu setup.

---

## 14. Chiến lược kiểm thử

### 14.1 Unit tests

- Input image validation: type, bytes, dimensions, corrupt content.
- Preprocessing và resize heatmap.
- Model output schema, finite score, valid PNG heatmap.
- Threshold/calibration/scoring functions.
- API schema validation, error normalization và config validation.
- Agent message schema, request correlation và retry-delay logic.
- Frontend formatting, score labels, overlay canvas utilities và export CSV escaping.

### 14.2 Integration tests

- API nhận upload và trả `AGENT_OFFLINE` khi không có Agent.
- Fake WebSocket Agent trả kết quả đúng request ID; backend save DB result.
- Agent disconnect khi có request; request không treo và queue được dọn.
- Request timeout; response cũ không bị gắn vào ảnh mới.
- Database unavailable; health/readiness đúng và không làm lộ secret.
- User A không đọc/xóa kết quả user B.
- Storage private/signed URL authorization nếu chức năng này được bật.

### 14.3 End-to-end tests

- Login → dashboard → upload valid image → result → history detail.
- Camera permission denied và camera available.
- Agent offline: thông báo chính xác, không có prediction giả.
- Timeout/reconnect.
- Xóa history và export CSV.
- Auth expired.

CI dùng test data nhỏ/mocks, không cần GPU hoặc secret. Có một smoke-test script riêng yêu cầu model artifact thật và Agent đang chạy; tài liệu ghi cách chạy.

### 14.4 Tiêu chí chất lượng

- Không có lint/typecheck/build errors trong cấu hình CI.
- Test bảo mật truy cập chéo user phải pass.
- API không bị treo vô hạn khi Agent offline/disconnect.
- Không có secrets trong Git, frontend bundle hoặc logs.
- Mọi màn hình chính có loading/empty/error states.
- Không báo model inference thành công nếu không nhận response thành công đã validate.

---

## 15. Definition of Done — checklist nghiệm thu ứng dụng

Đánh dấu từng mục dựa trên bằng chứng kiểm chứng được.

### Sản phẩm

- [x] Người dùng đăng nhập và đăng xuất được.
- [x] Trang dashboard hiển thị trạng thái API/Agent/model thật.
- [x] Chọn/tải ảnh hợp lệ và xem preview được.
- [x] Camera có thể bật/tắt và chụp được ảnh trên HTTPS/localhost.
- [x] Live Preview có throttle, không tích lũy queue vô hạn và dừng sạch.
- [x] Model PatchCore thật xử lý được ảnh category `screw`.
- [x] UI hiển thị prediction/score/threshold/latency và heatmap từ model.
- [x] Ảnh overlay đúng kích thước/tỷ lệ và có điều chỉnh opacity.
- [x] History lưu và đọc metadata đúng user.
- [x] Filter/pagination/detail/delete/export hoạt động.
- [x] Agent offline/model missing/invalid image/timeout có thông báo hữu ích.
- [x] Không có chức năng chính nào chỉ là UI giả hoặc mock trong production.

### AI/ML

- [x] Dataset validator chạy được.
- [x] Training/evaluation command có thể lặp lại từ tài liệu.
- [x] Artifact có metadata/version/preprocessing config.
- [x] Evaluation report có metric thật và phương pháp mô tả rõ.
- [x] Threshold được calibration theo quy trình không rò rỉ test holdout.
- [x] Inference hợp lệ có score hữu hạn và heatmap hợp lệ.
- [x] Không có cam kết phát hiện lỗi mọi loại đồ vật.

### Backend, dữ liệu và bảo mật

- [x] Auth được validate ở backend.
- [x] Có test ngăn truy cập chéo user.
- [x] Agent xác thực bằng token và dùng WSS trong cloud.
- [x] Upload được giới hạn và decode an toàn.
- [x] Queue/timeouts/reconnect/disconnect được test.
- [x] Secrets không nằm trong frontend hoặc Git.
- [x] Database schema/migrations và storage policy có tài liệu.
- [x] Privacy behavior và chế độ lưu ảnh được công bố.

### Chất lượng và giao hàng

- [ ] Frontend lint + typecheck + tests + build pass.
- [ ] Backend lint/typecheck/tests pass.
- [ ] Agent/ML tests pass hoặc skip GPU tests có lý do cụ thể.
- [ ] Smoke test local end-to-end với model thật pass.
- [ ] Deployment đã được xác minh hoặc blocker credential được ghi rõ.
- [ ] README, setup, API, model/data, security, deployment và troubleshooting docs hoàn chỉnh.
- [ ] Không commit dataset/checkpoint/secret/log có dữ liệu nhạy cảm.
- [ ] Known limitations và kết quả metric/test không bị giấu.

---

## 16. Các lỗi triển khai thường gặp cần chủ động tránh

- Dùng một `ANOMALY` hard-code hoặc random để demo khi model chưa load.
- Trả score giả hoặc vẽ heatmap ngẫu nhiên.
- Nạp model lại cho mỗi frame khiến live preview rất chậm.
- Gửi frame không throttle khiến backend queue tăng liên tục.
- Không có correlation ID khiến response của frame cũ xuất hiện trên frame mới.
- Dùng API token trong frontend bundle hoặc commit `.env`.
- Chỉ kiểm tra extension file mà không decode nội dung.
- Tin `user_id` từ client mà không xác thực JWT/quyền record.
- Dùng service role key ở frontend hoặc bỏ RLS mà không có authorization tương đương ở backend.
- Expose cổng máy Windows trực tiếp lên Internet thay vì Agent mở WSS outbound.
- Nhầm `display_score=87` với “87% xác suất bị lỗi”.
- Tune threshold bằng chính test holdout rồi báo cáo metric như chưa từng tune.
- Dùng các metrics từ một run khác nhưng ghi như số liệu hiện tại.
- Lưu raw images công khai hoặc không có cách xóa.
- Đưa dataset/checkpoint nặng vào Git làm repo phình to.
- Tuyên bố deployed dù mới chỉ build container hoặc chưa có credentials.
- Bỏ qua test fail bằng cách xóa test, giảm assertion hoặc catch exception rồi trả success.

---

## 17. Báo cáo tiến độ của agent

Sau mỗi phase, cập nhật `PLAN.md` bằng cách tick các checkbox đã nghiệm thu và gửi tóm tắt với cấu trúc:

```text
Phase: <số và tên>
Completed:
- <thay đổi cụ thể>
Verification:
- Command: <lệnh thực tế>
- Result: PASS/FAIL/SKIPPED + output tóm tắt
Artifacts:
- <file/đường dẫn được tạo hoặc cập nhật>
Blockers:
- <vướng mắc thật hoặc None>
Next:
- <phase/task tiếp theo>
```

Chỉ báo `PASS` khi lệnh đã được chạy và exit thành công. `SKIPPED` phải có lý do (ví dụ runner CI không có GPU). `NOT VERIFIED` dùng cho việc chưa có quyền/tài khoản/máy phù hợp.

---

## 18. Chỉ thị bắt đầu ngay cho Antigravity

Bắt đầu thực hiện **Phase 0**, không chỉ giải thích lại kế hoạch. Hãy kiểm tra repository và báo cáo ngắn những gì phát hiện được, rồi lần lượt thực hiện các phase tiếp theo. Tự tạo/cập nhật code, test và docs trong workspace hiện tại.

Trong quá trình thực thi:

- Nếu repository trống, scaffold theo mục 4.
- Nếu repository có sẵn, map code hiện tại vào các phase, giữ những phần tốt và điều chỉnh dần.
- Tạo `docs/DECISIONS.md` trước khi đưa ra lựa chọn kiến trúc ảnh hưởng lớn.
- Ưu tiên vertical slice sớm: **upload ảnh → API → Agent WSS → PatchCore thật → kết quả/heatmap**; sau đó hoàn thiện auth/history/UI/deploy.
- Khi cần secret hoặc tài khoản cloud, tiếp tục mọi phần có thể làm local; chỉ liệt kê chính xác các secret/steps còn thiếu, không dừng toàn dự án.
- Không chỉ tạo skeleton rồi tuyên bố hoàn tất. Hoàn thành từng luồng thực tế, chạy test, sửa lỗi, cuối cùng cung cấp hướng dẫn khởi chạy và demo từ đầu đến cuối.

**Kết quả cuối cần bàn giao:** mã nguồn hoàn chỉnh trong workspace, file cấu hình ví dụ không chứa bí mật, model training/evaluation pipeline, API contract, test suite, tài liệu cài đặt/deploy, và một báo cáo trung thực nêu rõ test đã chạy, metrics thực tế, URL deploy (nếu đã xác minh), hạn chế và bước thủ công còn lại.
