# LiveInspectAI

**Real-time Visual Anomaly Detection System**

LiveInspectAI là dự án ứng dụng Computer Vision và Deep Learning để phát hiện, phân vùng và trực quan hóa các vùng bất thường trên bề mặt sản phẩm từ hình ảnh hoặc camera trực tiếp.

Dự án hướng đến việc xây dựng một hệ thống kiểm tra lỗi trực quan có thể truy cập qua trình duyệt, phục vụ mục đích học tập, nghiên cứu và trình diễn đồ án.

## 1. Mục tiêu dự án

- Phát hiện các dấu hiệu bất thường trên bề mặt sản phẩm.
- Xác định và hiển thị vùng nghi ngờ có lỗi bằng anomaly map hoặc mask.
- Hỗ trợ kiểm tra hình ảnh và camera trực tiếp.
- Hiển thị điểm bất thường, trạng thái kiểm tra và kết quả trực quan.
- Lưu lịch sử kiểm tra và thông tin kết quả.
- Triển khai giao diện và backend trên cloud, trong khi AI inference chạy trên máy tính cá nhân.

**Lưu ý:** Khả năng phát hiện phụ thuộc vào model, dữ liệu huấn luyện, loại sản phẩm và điều kiện hình ảnh. Dự án không cam kết phát hiện chính xác mọi loại lỗi trên mọi vật thể.

## 2. Công nghệ dự kiến

| Thành phần | Công nghệ |
|---|---|
| Computer Vision | OpenCV, NumPy |
| Deep Learning | PyTorch |
| Anomaly Detection | Anomalib, PatchCore |
| Backend API | Python, FastAPI |
| Frontend | React, TypeScript, Vite |
| Giao tiếp realtime | WebSocket / Secure WebSocket |
| Database | PostgreSQL |
| Database service | Supabase (dự kiến) |
| Frontend hosting | Cloudflare Pages (dự kiến) |
| Model training | Máy tính cá nhân hoặc môi trường phù hợp |
| AI inference | PC sử dụng NVIDIA GTX 1660 Ti |

Các phiên bản thư viện sẽ được lựa chọn và cố định sau khi kiểm tra tính tương thích giữa Python, PyTorch, CUDA và Anomalib.

## 3. Kiến trúc hệ thống

LiveInspectAI sử dụng kiến trúc hybrid deployment:

- **Frontend:** Cung cấp giao diện camera, hiển thị vùng bất thường và xem lịch sử.
- **Backend cloud:** Quản lý API, phiên kiểm tra, xác thực kết nối và lưu metadata.
- **AI Agent local:** Chạy trên máy tính cá nhân, nhận frame được giao, thực hiện inference và trả kết quả.
- **Database:** Lưu thông tin phiên kiểm tra và kết quả.
- **Secure communication:** Sử dụng HTTPS/WSS và cơ chế xác thực giữa các thành phần.

Luồng xử lý dự kiến:

1. Người dùng mở LiveInspectAI trên trình duyệt.
2. Người dùng cấp quyền camera và bắt đầu phiên kiểm tra.
3. Frontend gửi frame đến backend.
4. Backend chuyển frame đến AI Agent đang kết nối.
5. AI Agent chạy model phát hiện bất thường.
6. Kết quả gồm anomaly score và vùng bất thường được gửi về frontend.
7. Giao diện hiển thị mask trên hình ảnh và lưu thông tin kết quả nếu cần.

AI Agent cần đang hoạt động và có kết nối Internet để thực hiện kiểm tra. Nếu máy tính chạy AI ngoại tuyến, chức năng inference từ xa sẽ tạm thời không khả dụng.

## 4. Mô hình AI và dữ liệu

### Mô hình

Dự án dự kiến sử dụng PatchCore thông qua Anomalib làm phương pháp phát hiện bất thường ban đầu.

PatchCore phù hợp với bài toán anomaly detection khi có thể huấn luyện chủ yếu từ hình ảnh sản phẩm bình thường. Mô hình học đặc trưng của dữ liệu bình thường và tạo điểm hoặc bản đồ bất thường cho hình ảnh đầu vào.

### Dataset

Dataset chính dự kiến sử dụng:

- **MVTec AD:** Bộ dữ liệu phát hiện và phân vùng bất thường công nghiệp.
- **Custom dataset:** Hình ảnh sản phẩm do người phát triển tự thu thập để thử nghiệm bổ sung.

Trang chủ MVTec AD: https://www.mvtec.com/research-teaching/datasets/mvtec-ad

Giai đoạn đầu nên tập trung vào một category cụ thể, chẳng hạn `screw`, trước khi mở rộng sang các loại sản phẩm khác.

Dataset dùng để huấn luyện và đánh giá cần được tách biệt hợp lý. Không nên đưa toàn bộ dataset huấn luyện vào image production nếu hệ thống chỉ cần model đã được chuẩn bị.

## 5. Cấu trúc thư mục dự kiến

```text
LiveInspectAI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── ai/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── storage/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── ai-agent/
│   ├── agent.py
│   ├── websocket_client.py
│   ├── inference.py
│   ├── reconnect.py
│   ├── config.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── training/
│   ├── configs/
│   ├── scripts/
│   └── notebooks/
├── datasets/
│   └── custom/
├── models/
│   └── patchcore/
├── deploy/
├── scripts/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

Đây là cấu trúc định hướng ban đầu. Một số thư mục hoặc file sẽ được tạo trong quá trình phát triển.

## 6. Yêu cầu hệ thống

### Máy tính chạy AI

- Windows 10/11 hoặc môi trường tương thích với các thư viện AI.
- Python phiên bản tương thích với PyTorch và Anomalib đã chọn.
- GPU NVIDIA GTX 1660 Ti hoặc GPU tương đương được hỗ trợ.
- Driver NVIDIA phù hợp.
- RAM và dung lượng lưu trữ đủ cho model, môi trường Python và dữ liệu.

Có thể thử nghiệm trên CPU khi cần, nhưng hiệu năng realtime có thể thấp hơn.

### Môi trường cloud

- Hosting hỗ trợ triển khai frontend.
- Backend hosting hỗ trợ API và WebSocket phù hợp với kiến trúc.
- PostgreSQL hoặc dịch vụ database tương đương.
- HTTPS/WSS và biến môi trường để cấu hình kết nối bảo mật.

Các gói miễn phí có thể có giới hạn về tài nguyên, thời gian hoạt động và kết nối dài hạn.

## 7. Cài đặt và chạy dự án

Các hướng dẫn sau là quy trình dự kiến; lệnh cụ thể sẽ được cập nhật khi từng thành phần được triển khai.

### 7.1. Clone repository

```bash
git clone <REPOSITORY_URL>
cd LiveInspectAI
```

Thay `<REPOSITORY_URL>` bằng URL repository thực tế.

### 7.2. Cài đặt backend

```bash
cd backend
python -m venv .venv
```

Kích hoạt môi trường trên Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Cài các dependencies sau khi file `requirements.txt` đã được cấu hình:

```bash
pip install -r requirements.txt
```

Khởi động backend trong môi trường phát triển khi ứng dụng đã sẵn sàng:

```bash
uvicorn app.main:app --reload
```

### 7.3. Cài đặt frontend

```bash
cd frontend
npm install
npm run dev
```

### 7.4. Khởi động AI Agent

Sau khi đã cài dependencies, chuẩn bị model và cấu hình kết nối cloud:

```bash
cd ai-agent
python agent.py
```

AI Agent chỉ có thể thực hiện inference khi model và cấu hình cần thiết đã được chuẩn bị.

## 8. Cấu hình môi trường

Các thông tin cấu hình sẽ được cung cấp qua biến môi trường hoặc file cấu hình local.

Ví dụ những biến có thể cần:

```dotenv
APP_ENV=development
DATABASE_URL=
JWT_SECRET=
AGENT_SHARED_SECRET=
MODEL_PATH=models/patchcore/model.ckpt
CORS_ORIGINS=
```

Không commit mật khẩu, token, khóa xác thực hoặc thông tin kết nối database thật vào repository.

## 9. Triển khai cloud

Kiến trúc triển khai dự kiến:

- Frontend: Cloudflare Pages hoặc nền tảng tương đương.
- Backend: dịch vụ hosting hỗ trợ FastAPI và kết nối WebSocket phù hợp.
- Database: PostgreSQL, dự kiến sử dụng Supabase.
- AI inference: chạy trên máy tính cá nhân sử dụng GTX 1660 Ti.
- Giao tiếp: HTTPS/WSS có xác thực.

Chi phí phụ thuộc vào hạn mức miễn phí, băng thông, dung lượng lưu trữ và thời gian hoạt động thực tế của từng dịch vụ.

## 10. Bảo mật và quyền riêng tư

- Chỉ chấp nhận AI Agent đã được xác thực.
- Giới hạn kích thước ảnh và tốc độ gửi frame.
- Không công khai trực tiếp dịch vụ inference trên máy tính cá nhân.
- Không lưu ảnh hoặc video nếu không cần thiết.
- Bảo vệ thông tin tài khoản và dữ liệu kiểm tra.
- Kiểm tra quyền camera trước khi bắt đầu phiên.
- Cấu hình CORS theo các origin được phép.

## 11. Trạng thái phát triển

- [ ] Khởi tạo cấu trúc repository.
- [ ] Chuẩn bị dataset và pipeline training.
- [ ] Chạy thử PatchCore trên ảnh tĩnh.
- [ ] Xây dựng AI Agent local.
- [ ] Xây dựng backend API.
- [ ] Xây dựng giao diện frontend.
- [ ] Tích hợp camera và hiển thị anomaly mask.
- [ ] Tích hợp database và lịch sử kiểm tra.
- [ ] Triển khai frontend/backend lên cloud.
- [ ] Kiểm thử end-to-end qua Internet.
- [ ] Hoàn thiện tài liệu cài đặt và triển khai.

## 12. Giới hạn hiện tại

LiveInspectAI đang trong giai đoạn thiết kế và phát triển. Các công nghệ, thư mục và quy trình triển khai trong tài liệu thể hiện định hướng kiến trúc, không đồng nghĩa với việc mọi chức năng đã hoàn thành.

Khả năng phát hiện lỗi trên vật thể chưa từng xuất hiện trong dữ liệu, khi góc nhìn hoặc điều kiện ánh sáng thay đổi mạnh, cần được đánh giá bằng thực nghiệm. Tracking mask giữa các frame cũng là một vấn đề riêng, không được đảm bảo chỉ bằng PatchCore.

## 13. License

License sẽ được bổ sung sau khi xác định phạm vi sử dụng và kiểm tra điều khoản của các thư viện, model và dataset được sử dụng trong dự án.
