# Báo cáo lựa chọn nền tảng triển khai miễn phí cho LiveInspectAI

**Ngày kiểm tra số liệu:** 14/10/2026. Mọi hạn mức có thể thay đổi; cần xem lại trang chính thức trước khi triển khai.

## 0\. Tóm tắt

\[KHUYẾN NGHỊ] Tổ hợp được chọn là **Cloudflare Pages** (frontend) + **Render Free Web Service** ở Singapore (FastAPI, chỉ xử lý REST) + **Cloudflare Workers và Durable Objects** (relay WebSocket truyền frame) + **Neon PostgreSQL** ở Singapore (cơ sở dữ liệu). Tổ hợp này đạt **4,45/5** trong ma trận có trọng số, cao nhất trong 5 tổ hợp được so sánh.

Ba lý do chính:

1. **Cả bốn dịch vụ đều miễn phí lâu dài và không cần thẻ thanh toán.** Không có khoản dùng thử hết hạn hay credit một lần.
2. **Tách luồng frame khỏi backend là điều bắt buộc.** Render Free chỉ còn 5 GB băng thông/tháng; ở 5 FPS, luồng frame sẽ dùng hết hạn mức này sau khoảng 4 giờ. Durable Objects không tính phí băng thông ra và chấp nhận tin nhắn tới 32 MiB, nên phù hợp làm relay.
3. **Neon tự thức dậy khi có truy vấn.** Supabase Free tạm dừng dự án sau 7 ngày không hoạt động và phải khôi phục thủ công; Render Postgres Free hết hạn sau 30 ngày. Neon chỉ ngủ sau 5 phút rảnh và tự chạy lại khi FastAPI gửi truy vấn.

Ba rủi ro lớn nhất và cách xử lý:

|Rủi ro|Cách xử lý|
|-|-|
|Render ngủ sau 15 phút, mất khoảng 1 phút để chạy lại|Gọi `/api/health` 10–15 phút trước buổi demo|
|Hạn mức Durable Objects đếm theo ngày (reset 7:00 sáng giờ Việt Nam)|Gửi frame theo cơ chế chờ kết quả (ACK), giới hạn 5 FPS|
|Mạng phòng bảo vệ không ổn định|Chuẩn bị chế độ chạy LAN/localhost và video demo quay sẵn|

## 1\. Bối cảnh, yêu cầu và giả định tải

### 1.1. Yêu cầu từ README

|Thành phần|Yêu cầu|
|-|-|
|Frontend|React + TypeScript + Vite, build tĩnh; truy cập camera; vẽ mask lên ảnh; xem lịch sử|
|Backend|Python FastAPI (uvicorn), có Dockerfile; REST API cho đăng nhập, phiên kiểm tra, metadata|
|Realtime|WebSocket/WSS để chuyển frame giữa trình duyệt và AI Agent|
|AI Agent|Chạy trên PC Windows có GTX 1660 Ti, kết nối **ra ngoài** (outbound) qua WSS, tự kết nối lại; không mở cổng trên PC|
|Database|PostgreSQL; lưu người dùng, phiên kiểm tra, kết quả; mặc định không lưu ảnh/video|
|Bảo mật|HTTPS/WSS, `JWT\_SECRET`, `AGENT\_SHARED\_SECRET`, `CORS\_ORIGINS`, giới hạn kích thước và tốc độ gửi frame|

### 1.2. Giả định tải

\[GIẢ ĐỊNH] Các số dưới đây chưa đo thực tế; cần đo lại khi có bản chạy thử (xem mục 11).

|Ký hiệu|Ý nghĩa|Thấp|Chuẩn|Cực đại|
|-|-|-|-|-|
|S\_f|Kích thước một frame JPEG 640×480|30 KB|55 KB|80 KB|
|S\_m|Kích thước kết quả (score + mask nén)|5 KB|12,5 KB|20 KB|
|N|Số trình duyệt xem cùng một phiên|1|1|3|
|f|Tốc độ gửi frame (FPS)|2|5|10|
|H|Số giờ chạy mỗi tháng|20|30|40|

Quy ước đơn vị: 1 KB = 1.000 byte, 1 MB = 1.000 KB, 1 GB = 1.000 MB.

## 2\. Nền tảng Frontend

### 2.1. So sánh

|Tiêu chí|Cloudflare Pages|Vercel Hobby|Netlify Free|GitHub Pages|Firebase Hosting (Spark)|
|-|-|-|-|-|-|
|Băng thông|Không giới hạn với tài nguyên tĩnh|100 GB Fast Data Transfer/tháng|Trừ vào 300 credits/tháng, 20 credits/GB (tối đa \~15 GB nếu không deploy)|\~100 GB/tháng (giới hạn mềm)|360 MB/ngày|
|Build/deploy|500 build/tháng|Theo hạn mức Hobby|15 credits mỗi lần deploy production|\~10 build/giờ (giới hạn mềm)|Deploy bằng CLI|
|Cần thẻ|Không|Không|Không|Không|Không|
|Hết hạn|Không|Không|Site bị tạm dừng khi hết credits trong tháng|Không|Không|
|Repo private|Có|Có|Có|Cần GitHub Pro|Không phụ thuộc Git|
|SPA routing|File `\_redirects`|`vercel.json`|File `\_redirects`|Phải dùng mẹo `404.html`|`rewrites` trong `firebase.json`|
|Điều khoản|Cho phép mọi mục đích|Chỉ phi thương mại|Cho phép|Không dành cho kinh doanh|Cho phép|
|Nguồn|\[DỮ KIỆN]|\[DỮ KIỆN]|\[DỮ KIỆN]|\[DỮ KIỆN]|\[CHƯA XÁC MINH]|

Ghi chú về Vercel: từ năm 2026, mỗi dự án Hobby chỉ giữ lại 3 bản deploy production gần nhất, nhưng **bản production hiện tại không bao giờ bị xoá**. Điểm này không ảnh hưởng đến đồ án nên không được tính là nhược điểm.

### 2.2. Đánh giá

* **Netlify:** mỗi lần đẩy code lên nhánh chính tốn 15 credits. Khoảng 20 lần deploy là hết 300 credits của tháng, và site bị tạm dừng. Không hợp với giai đoạn sửa giao diện liên tục.
* **Firebase Hosting:** 360 MB/ngày đủ cho người xem, nhưng là giới hạn theo ngày nên có rủi ro trong ngày demo khi nhiều người tải lại trang.
* **GitHub Pages:** buộc repo phải public (nếu không có GitHub Pro) và không hỗ trợ chuyển hướng SPA chuẩn, nên tải lại trang `/history` sẽ lỗi 404 nếu không dùng mẹo.
* **Vercel Hobby:** dùng tốt, phù hợp điều khoản phi thương mại của đồ án. Là lựa chọn dự phòng hợp lý cho frontend.

\[KHUYẾN NGHỊ] **Chọn Cloudflare Pages.** Băng thông tĩnh không giới hạn, 500 build/tháng, hỗ trợ repo private, có HTTPS tự động. Frontend và relay cùng nằm trên Cloudflare nên quản lý tên miền, biến môi trường và bảo mật ở một chỗ. Nếu sau này muốn gộp, code Vite có thể chuyển sang Workers Static Assets mà không phải sửa.

## 3\. Nền tảng Backend (FastAPI)

### 3.1. So sánh

|Nền tảng|Hạn mức miễn phí|Cần thẻ / thời hạn|WebSocket|Ngủ / khởi động lại|Region gần VN|Kết luận|
|-|-|-|-|-|-|-|
|**Render Free**|512 MB RAM, 0,1 CPU; 750 giờ/tháng/workspace; 5 GB băng thông ra/tháng|Không cần thẻ; không hết hạn|Có|Ngủ sau 15 phút không có traffic vào (tính cả tin nhắn WebSocket); khoảng 1 phút để chạy lại|Singapore|**Phù hợp có điều kiện**: chỉ dùng cho REST|
|Railway|Dùng thử 30 ngày với 5 USD, sau đó 1 USD credit/tháng|Không cần thẻ|Có|Chạy liên tục sẽ hết 1 USD sau vài ngày|Singapore|Phù hợp có điều kiện: làm dự phòng, chỉ bật khi demo|
|Hugging Face Spaces|CPU Basic 2 vCPU, 16 GB|**Tạo Docker Space cần gói trả phí**|—|Ngủ khi không dùng|—|Không phù hợp|
|Koyeb|—|Người dùng mới phải có phương thức thanh toán và đăng ký gói trả phí|Có|—|—|Không phù hợp|
|Fly.io|Chỉ có dùng thử (2 giờ máy hoặc 7 ngày)|Cần thẻ|Có|—|Singapore, Tokyo|Không phù hợp|
|Google Cloud Run|2 triệu request/tháng và hạn mức vCPU/RAM|Cần tài khoản thanh toán|Có, nhưng bị cắt theo request timeout (tối đa 60 phút)|Scale về 0|Singapore|Phù hợp có điều kiện (cần thẻ)|
|Vercel Functions (Python)|4 giờ Active CPU; 10 GB Fast Origin Transfer|Không cần thẻ; phi thương mại|Beta; đóng sau tối đa 300 giây; trình duyệt và agent có thể rơi vào hai instance khác nhau|Serverless|1 region|Không phù hợp làm relay|
|Oracle Cloud Always Free|Máy ảo luôn bật|Cần thẻ; máy rảnh lâu có thể bị thu hồi|Có, toàn quyền|Không ngủ|Singapore, Tokyo|Phù hợp có điều kiện (cần thẻ, tự quản trị)|
|PythonAnywhere|1 web app, CPU giới hạn theo ngày|Không cần thẻ|Không hỗ trợ trên gói free \[CHƯA XÁC MINH]|—|US/EU|Không phù hợp|

Nguồn: Render, Railway, Hugging Face, Koyeb, Fly.io, Cloud Run, Vercel là \[DỮ KIỆN]. Chi tiết cắt giảm cấu hình Oracle Ampere A1 trong năm 2026 là \[CHƯA XÁC MINH].

### 3.2. Những điểm trên gói free của Render cần biết

\[DỮ KIỆN] theo tài liệu "Deploy for Free" của Render:

* Hết 5 GB băng thông mà **chưa gắn phương thức thanh toán** thì Render **tạm dừng toàn bộ dịch vụ free cho đến hết tháng**, không tính tiền. Đây là lý do không cho frame đi qua Render.
* Hết 750 giờ instance trong tháng thì cũng bị tạm dừng đến đầu tháng sau. Một dịch vụ chạy liên tục 31 ngày dùng 744 giờ, vừa đủ, nên chỉ chạy **một** dịch vụ free.
* Render có thể khởi động lại dịch vụ free bất kỳ lúc nào, và có thể tạm dừng dịch vụ free tạo quá nhiều traffic ra ngoài.
* Hệ thống file là tạm thời, mất khi khởi động lại. Không lưu file trên container.

### 3.3. Lựa chọn

\[KHUYẾN NGHỊ] **Chọn Render Free ở Singapore, nhưng chỉ dùng cho REST API**: đăng nhập, cấp vé kết nối relay, quản lý phiên kiểm tra, ghi kết quả vào PostgreSQL, trả lịch sử. Toàn bộ dữ liệu đi qua Render là JSON nhỏ.

\[GIẢ ĐỊNH] Ước tính băng thông REST: khoảng 300 request/giờ khi demo (ghi kết quả gộp mỗi giây + truy vấn lịch sử), mỗi request khoảng 2 KB, 40 giờ/tháng:

> \*\*300 request/giờ × 2 KB × 40 giờ = 24 MB/tháng\*\*

Chưa đến 1% hạn mức 5 GB.

## 4\. Relay realtime

### 4.1. Công thức tính

Mỗi frame đi qua relay tạo ra:

* **Tin nhắn vào relay:** 1 frame từ trình duyệt + 1 kết quả từ agent = **2 tin nhắn**.
* **Tin nhắn ra từ relay:** 1 frame tới agent + N kết quả tới N trình duyệt = **1 + N tin nhắn**.

Băng thông ra (egress) mỗi frame:

> \*\*E\_frame = S\_f + N × S\_m\*\*

* Chuẩn: 55 + 1 × 12,5 = 67,5 KB
* Cực đại: 80 + 3 × 20 = 140 KB

Băng thông ra mỗi giờ ở tốc độ f:

> \*\*E\_giờ = f × 3.600 × E\_frame\*\*

Số tin nhắn vào relay mỗi giờ:

> \*\*M\_vào = 2 × f × 3.600 = 7.200 × f\*\*

Durable Objects tính tin nhắn WebSocket đi vào theo tỷ lệ 20:1, nên số request bị tính:

> \*\*R\_DO = M\_vào ÷ 20 = 360 × f\*\*

### 4.2. Kết quả

\[GIẢ ĐỊNH] áp dụng công thức trên:

|Chỉ số|2 FPS|5 FPS|10 FPS|
|-|-|-|-|
|Egress mỗi giờ, kịch bản chuẩn|486 MB|1,22 GB|2,43 GB|
|Egress mỗi giờ, kịch bản cực đại|1,01 GB|2,52 GB|5,04 GB|
|Egress mỗi tháng, chuẩn (H = 30)|14,6 GB|36,5 GB|72,9 GB|
|Egress mỗi tháng, cực đại (H = 40)|40,3 GB|100,8 GB|201,6 GB|
|Thời gian dùng hết 5 GB (Render/Supabase), chuẩn|10,3 giờ|4,1 giờ|2,1 giờ|
|Thời gian dùng hết 5 GB, cực đại|5,0 giờ|2,0 giờ|59 phút|
|Tin nhắn vào relay mỗi giờ|14.400|36.000|72.000|
|Request tính phí DO mỗi giờ (20:1)|720|1.800|3.600|
|Số giờ/ngày trước khi chạm 100.000 request DO (20:1)|139 giờ|56 giờ|28 giờ|
|Như trên nếu bị đếm 1:1 (trường hợp xấu nhất)|6,9 giờ|2,8 giờ|1,4 giờ|

Thời lượng tính toán của Durable Objects: một DO hoạt động liên tục tiêu thụ 0,128 GB × 3.600 s = 460,8 GB-s mỗi giờ. Hạn mức 13.000 GB-s/ngày đủ cho:

> \*\*13.000 ÷ 460,8 ≈ 28,2 giờ/ngày\*\*

Nghĩa là thời lượng không bao giờ là giới hạn với một phiên demo.

### 4.3. So sánh các phương án relay

|Tiêu chí|Cloudflare Durable Objects|Supabase Realtime (Broadcast)|Ably Free|Pusher Sandbox|WebRTC P2P|
|-|-|-|-|-|-|
|Hạn mức|100.000 request/ngày; tin nhắn vào tính 20:1; tin nhắn ra không tính|2 triệu tin nhắn/tháng; 100 tin nhắn/giây; 200 kết nối đồng thời|\[CHƯA XÁC MINH]|\[CHƯA XÁC MINH]|Không tốn hạn mức cloud sau khi kết nối|
|Kích thước tin nhắn|Tối đa 32 MiB|Tối đa 256 KB|Nhỏ hơn frame 80 KB \[CHƯA XÁC MINH]|\~10 KB \[CHƯA XÁC MINH]|Phụ thuộc trình duyệt|
|Băng thông|Không tính phí egress|Tính vào 5 GB egress của dự án \[GIẢ ĐỊNH về cách tính]|—|—|Không qua cloud|
|Rủi ro|Hạn mức theo ngày; hai codebase (Python + TypeScript)|Dự án tạm dừng sau 7 ngày không hoạt động|Kích thước tin nhắn|Kích thước tin nhắn|Hay lỗi khi mạng dùng NAT đối xứng (4G, mạng trường) nếu không có TURN; aiortc trên Windows khó cài|

\[GIẢ ĐỊNH] Nếu Supabase đếm cả lượt gửi và lượt nhận (2 + 1 + N = 4 sự kiện mỗi frame khi N = 1), 5 FPS tạo 20 tin nhắn/giây (dưới mức 100/giây) và 72.000 tin nhắn/giờ. 2 triệu tin nhắn/tháng đủ khoảng 28 giờ. Tuy vậy, 5 GB egress sẽ hết trước, sau khoảng 4 giờ.

### 4.4. Ghi chú kỹ thuật về Durable Objects

* **Vị trí đặt DO:** \[DỮ KIỆN] DO không chạy ở mọi điểm hiện diện của Cloudflare. Mặc định nó được tạo ở data center có hỗ trợ DO gần nơi có request đầu tiên, và không đổi vị trí sau đó. Cloudflare có gợi ý vị trí `apac-se` cho Đông Nam Á. Với người dùng ở Thái Nguyên, DO nhiều khả năng nằm ở Singapore hoặc Hong Kong, **không phải Hà Nội**.
* **Độ trễ:** \[GIẢ ĐỊNH] ping Hà Nội–Singapore trung bình khoảng 46 ms (WonderNetwork, đo giữa các máy chủ). Vì trình duyệt và agent cùng ở Thái Nguyên, mỗi frame đi ra relay rồi quay về hai lần: trình duyệt → DO → agent, rồi agent → DO → trình duyệt. Phần mạng tốn khoảng 2 × 46 ≈ 92 ms, chưa kể thời gian suy luận và nén ảnh.
* **Hibernation:** \[DỮ KIỆN] dùng WebSocket Hibernation API để DO không bị tính thời lượng khi không có tin nhắn. Ping/pong của giao thức WebSocket không bị tính phí.
* **Báo cáo đếm 1:1:** \[CHƯA XÁC MINH] có một bài trên diễn đàn Cloudflare Community (10/2026) cho rằng tài khoản free bị chặn trước mốc 100.000 sau khi quy đổi 20:1. Chưa được Cloudflare xác nhận. Báo cáo vẫn tính phương án an toàn: ở 5 FPS, kể cả bị đếm 1:1, vẫn chạy được khoảng 2,8 giờ/ngày.

\[KHUYẾN NGHỊ] **Chọn Cloudflare Durable Objects làm relay**, kèm ba biện pháp:

1. Gửi frame dạng nhị phân (`ArrayBuffer`), không dùng base64 (base64 làm frame to thêm khoảng 33%).
2. Gửi theo cơ chế chờ kết quả: trình duyệt chỉ gửi frame mới khi đã nhận kết quả frame trước, giới hạn tối đa 5 FPS.
3. Nếu cần chạy 10 FPS lâu, gộp nhiều kết quả vào một tin nhắn để giảm số tin nhắn vào.

## 5\. Cơ sở dữ liệu PostgreSQL

### 5.1. So sánh

|Dịch vụ|Dung lượng free|Compute / truy vấn|Cần thẻ / hết hạn|Ngủ và thức dậy|Pooling|Region gần VN|Nguồn|
|-|-|-|-|-|-|-|-|
|**Neon**|**0,5 GB/project**, tối đa 100 project|100 CU-giờ/tháng/project; tự co giãn tới 2 CU|Không cần thẻ; không hết hạn|Ngủ sau 5 phút không có truy vấn, tự thức dậy khi có truy vấn|PgBouncer có sẵn|Singapore|\[DỮ KIỆN]|
|Supabase|500 MB; 2 project|CPU dùng chung|Không cần thẻ|**Tạm dừng sau 7 ngày không hoạt động, phải khôi phục thủ công**; không có backup tự động|Supavisor|Singapore|\[DỮ KIỆN]|
|Prisma Postgres|500 MB|100.000 hoặc 200.000 lượt truy vấn/tháng (hai trang chính thức ghi khác nhau)|Không cần thẻ|Scale về 0|Có|\[CHƯA XÁC MINH]|\[DỮ KIỆN]|
|Render Postgres|1 GB|—|Không cần thẻ, **hết hạn sau 30 ngày**, xoá sau 14 ngày nữa|Không ngủ trong 30 ngày|Không có pooling quản lý|Singapore|\[DỮ KIỆN]|
|Railway Postgres|Trừ vào credit|Chạy liên tục tốn credit|Hết credit thì dừng|—|—|Singapore|\[DỮ KIỆN] về credit|
|Aiven|1 node luôn bật|—|Không cần thẻ|Không ngủ|—|\[CHƯA XÁC MINH]|\[CHƯA XÁC MINH]|
|CockroachDB Basic|Có gói free|Theo Request Units|Không cần thẻ|Scale về 0|—|Singapore|\[CHƯA XÁC MINH]; chỉ tương thích giao thức PostgreSQL, có thể vướng khi chạy migration|
|Xata, Nile|—|—|—|—|—|—|\[CHƯA XÁC MINH]|

### 5.2. Tính toán cho Neon

\[DỮ KIỆN] Free có 100 CU-giờ/tháng/project. Ở mức nhỏ nhất 0,25 CU, thời gian hoạt động tối đa:

> \*\*100 CU-giờ ÷ 0,25 CU = 400 giờ/tháng\*\*

\[GIẢ ĐỊNH] Đồ án chạy 20–40 giờ/tháng (cộng thêm 5 phút trước khi DB ngủ mỗi lần), tiêu thụ khoảng 5–10 CU-giờ, tức 5–10% hạn mức.

\[GIẢ ĐỊNH] Dung lượng: nếu ghi **mọi** frame ở 5 FPS trong 30 giờ thì có 5 × 3.600 × 30 = 540.000 dòng. Với khoảng 300 byte/dòng gồm cả chỉ mục, tổng khoảng 160 MB, vẫn dưới 0,5 GB. Tuy vậy, báo cáo khuyến nghị chỉ ghi **frame bất thường** và **một bản tóm tắt mỗi giây**, để dung lượng chỉ còn vài chục MB và số lần ghi giảm 5 lần.

### 5.3. Lựa chọn

\[KHUYẾN NGHỊ] **Chọn Neon ở Singapore.** Lý do:

* Miễn phí lâu dài, không cần thẻ.
* Tự thức dậy khi có truy vấn, không phải vào dashboard khôi phục như Supabase.
* Không giới hạn số truy vấn như Prisma Postgres, mà tính theo thời gian compute, nên phù hợp cách ghi kết quả liên tục.
* Có PgBouncer và tính năng tạo nhánh database (branching) để thử migration an toàn.

**Lưu ý:** README dự kiến dùng Supabase. Nếu vẫn muốn giữ Supabase, cần một lịch tự động truy vấn nhẹ ít nhất mỗi vài ngày để tránh bị tạm dừng, và tự sao lưu bằng `pg\_dump`.

### 5.4. Schema tối thiểu

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password\_hash VARCHAR(255) NOT NULL,          -- băm bằng argon2 hoặc bcrypt
    full\_name     VARCHAR(100) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'inspector',
    created\_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE agents (
    id            VARCHAR(64) PRIMARY KEY,        -- dùng làm tên phòng relay
    display\_name  VARCHAR(100) NOT NULL,
    gpu\_name      VARCHAR(100),
    model\_version VARCHAR(100),
    last\_seen\_at  TIMESTAMPTZ,
    created\_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE inspection\_sessions (
    id          UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),
    user\_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent\_id    VARCHAR(64) NOT NULL REFERENCES agents(id),
    model\_name  VARCHAR(100) NOT NULL,
    target\_fps  SMALLINT NOT NULL DEFAULT 5,
    threshold   REAL NOT NULL DEFAULT 0.5,
    status      VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | completed | aborted
    started\_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended\_at    TIMESTAMPTZ,
    summary     JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE inspection\_results (
    id            BIGSERIAL PRIMARY KEY,
    session\_id    UUID NOT NULL REFERENCES inspection\_sessions(id) ON DELETE CASCADE,
    frame\_index   INTEGER NOT NULL,
    anomaly\_score REAL NOT NULL,
    is\_anomalous  BOOLEAN NOT NULL DEFAULT FALSE,
    inference\_ms  INTEGER NOT NULL,
    region\_meta   JSONB NOT NULL DEFAULT '{}'::jsonb,   -- bounding box / RLE, không lưu ảnh gốc
    captured\_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx\_sessions\_user\_started ON inspection\_sessions (user\_id, started\_at DESC);
CREATE INDEX idx\_results\_session\_time  ON inspection\_results (session\_id, captured\_at DESC);
CREATE INDEX idx\_results\_anomalous     ON inspection\_results (session\_id, anomaly\_score)
    WHERE is\_anomalous = TRUE;
```

Quản lý schema bằng **Alembic** (đặt trong `backend/migrations/` như README), không chạy SQL tay trên production.

### 5.5. Kết nối từ FastAPI

Hai điểm cần đúng khi dùng SQLAlchemy async + asyncpg với Neon:

* asyncpg không hiểu tham số `sslmode` trong URL, nên bỏ `?sslmode=require\&channel\_binding=require` khỏi chuỗi Neon cung cấp và truyền `ssl` qua `connect\_args`.
* `statement\_cache\_size` là tham số của asyncpg (đặt trong `connect\_args`), còn `prepared\_statement\_cache\_size` là tham số của SQLAlchemy (đặt trong URL). Đặt nhầm `prepared\_statement\_cache\_size` vào `connect\_args` sẽ làm asyncpg báo lỗi `TypeError` khi kết nối.

```python
import os
from sqlalchemy.ext.asyncio import create\_async\_engine, async\_sessionmaker, AsyncSession

# Ví dụ: postgresql+asyncpg://user:PASSWORD@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/liveinspect?prepared\_statement\_cache\_size=0
DATABASE\_URL = os.environ\["DATABASE\_URL"]

engine = create\_async\_engine(
    DATABASE\_URL,
    pool\_size=5,            # đủ cho container 512 MB
    max\_overflow=5,
    pool\_pre\_ping=True,     # kiểm tra kết nối, đánh thức Neon nếu đang ngủ
    pool\_recycle=240,       # làm mới trước khi Neon ngủ (5 phút)
    connect\_args={
        "ssl": "require",
        "statement\_cache\_size": 0,   # an toàn khi đi qua PgBouncer
        "command\_timeout": 30,
    },
)

SessionLocal = async\_sessionmaker(engine, class\_=AsyncSession, expire\_on\_commit=False)
```

## 6\. Tổ hợp đề xuất

### 6.1. Các tổ hợp được so sánh

|Mã|Frontend|Backend REST|Relay frame|Database|
|-|-|-|-|-|
|**T1**|Cloudflare Pages|Render Free|Cloudflare Durable Objects|Neon|
|T2|Cloudflare Pages|Render Free (gánh cả WebSocket)|Render|Supabase|
|T3|Cloudflare Pages|Render Free|Supabase Realtime|Supabase|
|T4|Vercel Hobby|Vercel Functions (WebSocket beta)|Vercel + Redis pub/sub|Supabase|
|T5|Cloudflare Pages|Oracle Always Free VM (Docker)|Oracle VM|Neon|

### 6.2. Ma trận chấm điểm có trọng số

Thang điểm 1–5 (5 là tốt nhất). Tổng điểm = Σ (trọng số × điểm).

|Tiêu chí|Trọng số|T1|T2|T3|T4|T5|
|-|-|-|-|-|-|-|
|Miễn phí thật (không thẻ, không hết hạn)|20%|5|4|5|4,5|2|
|Hỗ trợ WebSocket/realtime ở 2–10 FPS|20%|5|1,5|2,5|1,5|5|
|Ổn định khi demo (ngủ, tạm dừng, hạn mức)|15%|4|2|2,5|2|3|
|Độ trễ từ Việt Nam|15%|4|4|4|3,5|4|
|Dễ triển khai|10%|3,5|5|4|3,5|2,5|
|Bảo mật|10%|4,5|4,5|4|4,5|3,5|
|Mở rộng / dễ chuyển nền tảng|10%|4,5|4|3,5|3|4,5|
|**Tổng**|**100%**|**4,45**|**3,35**|**3,63**|**3,13**|**3,50**|

Lý do cho những điểm chênh lệch lớn:

* **T1:** độ trễ 4 chứ không phải 5, vì DO nằm ở Singapore/Hong Kong và mỗi frame đi vòng hai lần. Dễ triển khai chỉ 3,5 vì phải viết thêm relay bằng TypeScript bên cạnh FastAPI.
* **T2:** WebSocket 1,5 vì 5 GB băng thông của Render hết sau khoảng 4 giờ ở 5 FPS, rồi toàn bộ dịch vụ bị tạm dừng đến hết tháng.
* **T3:** Supabase Realtime chấp nhận được kích thước frame, nhưng dùng chung 5 GB egress và dự án bị tạm dừng sau 7 ngày.
* **T4:** WebSocket trên Vercel đang beta, đóng sau tối đa 300 giây và cần thêm Redis để nối hai instance.
* **T5:** máy ảo mạnh và giữ WebSocket tốt, nhưng cần thẻ thanh toán và phải tự quản trị TLS, tường lửa, cập nhật hệ điều hành.

### 6.3. Sơ đồ kiến trúc T1

```mermaid
flowchart TB
    subgraph VN\["Thái Nguyên, Việt Nam"]
        B\["Trình duyệt<br/>React + Vite<br/>camera + overlay mask"]
        A\["AI Agent<br/>PC Windows, GTX 1660 Ti<br/>PatchCore"]
    end
    subgraph CF\["Cloudflare"]
        P\["Cloudflare Pages<br/>file tĩnh"]
        W\["Worker<br/>kiểm tra vé + Origin"]
        D\["Durable Object<br/>phòng relay theo agent\_id"]
        W --> D
    end
    subgraph SG\["Singapore"]
        R\["Render Free<br/>FastAPI REST"]
        N\[("Neon PostgreSQL<br/>PgBouncer")]
        R -- "TLS 5432" --> N
    end

    B -- "HTTPS: tải giao diện" --> P
    B -- "WSS: gửi frame, nhận mask" --> W
    A -- "WSS outbound: nhận frame, gửi mask" --> W
    B -- "HTTPS: đăng nhập, tạo phiên, lấy vé" --> R
    A -- "HTTPS: lấy vé, ghi kết quả" --> R
```

Hệ thống chia thành hai mặt phẳng:

* **Mặt phẳng điều khiển (REST, đi qua Render):** đăng nhập, tạo phiên, cấp vé kết nối relay, ghi kết quả, xem lịch sử.
* **Mặt phẳng dữ liệu (WSS, đi qua Cloudflare):** frame JPEG từ trình duyệt tới agent và kết quả theo chiều ngược lại. Không đi qua Render, không lưu vào database.

### 6.4. Luồng xác thực và cấp vé

Trình duyệt **không gắn được header `Authorization`** khi mở WebSocket. Vì vậy hệ thống dùng "vé" ngắn hạn:

* Render ký vé bằng `RELAY\_TICKET\_SECRET` (khoá riêng, dùng chung với Worker, khác `JWT\_SECRET`).
* Vé chứa `room` (agent\_id), `role` (viewer hoặc agent), `exp` (hết hạn sau 60 giây), `jti` (mã ngẫu nhiên).
* Trình duyệt gửi vé qua query string khi mở WSS. Worker kiểm tra chữ ký, thời hạn, và header `Origin` (với viewer).
* Agent lấy vé bằng `AGENT\_SHARED\_SECRET` qua HTTPS, không gửi bí mật này lên relay.

```mermaid
sequenceDiagram
    autonumber
    participant B as Trình duyệt
    participant R as Render FastAPI
    participant W as Cloudflare Worker
    participant D as Durable Object
    participant A as AI Agent

    A->>R: POST /api/agent/ticket
    R-->>A: vé agent (60 giây)
    A->>W: WSS /ws/{agent\_id}?ticket=...
    W->>D: vé hợp lệ, gắn nhãn agent
    B->>R: POST /api/sessions (JWT)
    R-->>B: session\_id + vé viewer
    B->>W: WSS /ws/{agent\_id}?ticket=...
    W->>D: vé + Origin hợp lệ, gắn nhãn viewer
```

### 6.5. Luồng xử lý một frame

```mermaid
sequenceDiagram
    autonumber
    participant B as Trình duyệt
    participant D as Durable Object
    participant A as AI Agent
    participant R as Render FastAPI
    participant N as Neon

    B->>D: frame JPEG (\~50 KB)
    D->>A: chuyển frame
    A->>D: score + mask
    D->>B: chuyển kết quả
    A-->>R: lô kết quả mỗi giây
    R-->>N: INSERT kết quả
```

Diễn giải các bước:

1. Trình duyệt chụp frame, nén JPEG chất lượng 0,7 (khoảng 40–60 KB) và gửi dạng nhị phân. Đây là tin nhắn vào thứ nhất của DO.
2. DO chuyển frame cho agent. Tin nhắn ra không bị tính phí.
3. Agent giải mã, chạy PatchCore trên GPU, gửi lại score và mask. Đây là tin nhắn vào thứ hai.
4. DO chuyển kết quả cho trình duyệt. Trình duyệt vẽ mask rồi mới gửi frame tiếp theo.
5. Mỗi giây, agent gửi một lô kết quả tóm tắt lên Render qua HTTPS.
6. Render ghi lô kết quả vào bảng `inspection\_results` trên Neon.

### 6.6. Bảng các kết nối

|Nguồn → Đích|Chiều mở kết nối|Giao thức|Nội dung|Bảo vệ|
|-|-|-|-|-|
|Trình duyệt → Cloudflare Pages|Trình duyệt mở|HTTPS 443|File giao diện|TLS|
|Trình duyệt → Render|Trình duyệt mở|HTTPS 443|Đăng nhập, tạo phiên, lịch sử|JWT, CORS|
|Trình duyệt → Worker/DO|Trình duyệt mở|WSS 443|Frame, kết quả|Vé 60 giây, kiểm tra Origin|
|AI Agent → Worker/DO|**Agent mở ra ngoài**|WSS 443|Frame, kết quả|Vé 60 giây (lấy bằng `AGENT\_SHARED\_SECRET`)|
|AI Agent → Render|Agent mở ra ngoài|HTTPS 443|Lấy vé, ghi lô kết quả|`AGENT\_SHARED\_SECRET`|
|Render → Neon|Render mở|PostgreSQL/TLS 5432|Đọc ghi dữ liệu|TLS, mật khẩu trong biến môi trường|

PC chạy AI Agent **không mở cổng nào**, không cần cấu hình router, không cần Cloudflare Tunnel.

### 6.7. Phương án dự phòng

\[KHUYẾN NGHỊ] Chuẩn bị theo ba mức, từ nhẹ đến nặng:

1. **Đổi relay sang Supabase Realtime (T3)** nếu Cloudflare gặp sự cố hoặc chạm hạn mức ngày. Chỉ đổi lớp kết nối relay ở frontend và agent; Render và Neon giữ nguyên. Phù hợp chạy ngắn (dưới 2–3 giờ ở 5 FPS).
2. **Chế độ LAN/localhost** khi mạng phòng bảo vệ không ổn định: chạy FastAPI (kèm một endpoint WebSocket relay nội bộ) và frontend ngay trên PC có GPU. Trình duyệt trên cùng PC dùng `localhost`, nên vẫn được quyền camera. Nếu dùng máy khác trong LAN, cần HTTPS (ví dụ chứng chỉ tự tạo bằng `mkcert`), vì trình duyệt chỉ cho truy cập camera trên trang bảo mật.
3. **Video demo quay sẵn** toàn bộ luồng, dùng khi cả hai cách trên đều không chạy được.

```mermaid
flowchart LR
    subgraph PC\["PC có GTX 1660 Ti (không cần Internet)"]
        B2\["Trình duyệt<br/>http://localhost:5173"]
        F2\["FastAPI local<br/>REST + WS relay"]
        A2\["AI Agent"]
        DB2\[("PostgreSQL local<br/>hoặc SQLite")]
    end
    B2 -- "WS localhost" --> F2
    A2 -- "WS localhost" --> F2
    F2 --> DB2
```

## 7\. Lý do lựa chọn

Phần này viết để có thể đưa thẳng vào chương thiết kế hệ thống của báo cáo đồ án.

**Bài toán chính.** LiveInspectAI cần truyền ảnh liên tục từ 2 đến 10 khung hình mỗi giây. Ở mức chuẩn (khung hình 55 KB, kết quả 12,5 KB, 5 FPS), lưu lượng ra khoảng 1,2 GB mỗi giờ, tương đương khoảng 36 GB mỗi tháng nếu chạy 30 giờ. Phần lớn các gói miễn phí năm 2026 giới hạn băng thông ở mức vài GB. Vì vậy, kiến trúc phải đặt luồng ảnh vào nơi không tính phí băng thông, và chỉ để những yêu cầu nhỏ đi qua các dịch vụ có hạn mức thấp.

**Vì sao chọn từng thành phần:**

* **Cloudflare Pages cho frontend:** băng thông tĩnh không giới hạn, 500 lần build/tháng, hỗ trợ repo private. Không gặp rủi ro hết credits như Netlify hay giới hạn 360 MB/ngày như Firebase Hosting.
* **Cloudflare Durable Objects cho relay:** là điểm hẹn WebSocket chung cho trình duyệt và agent. Agent kết nối ra ngoài nên không cần mở cổng trên PC. Tin nhắn tối đa 32 MiB (đủ cho frame 80 KB), không tính phí băng thông ra, hạn mức 100.000 request/ngày với tỷ lệ 20:1 đủ cho hơn 50 giờ/ngày ở 5 FPS.
* **Render Free cho backend REST:** chạy đúng Dockerfile FastAPI có sẵn trong README, ở region Singapore, không cần thẻ. Khi frame đã được tách sang relay, lượng dữ liệu qua Render chỉ khoảng vài chục MB/tháng.
* **Neon cho PostgreSQL:** miễn phí lâu dài, tự thức dậy khi có truy vấn, dùng chuẩn PostgreSQL nên Alembic và SQLAlchemy chạy bình thường.

**Vì sao không chọn các phương án khác:**

* **Gộp WebSocket vào FastAPI trên Render (T2):** 5 GB băng thông hết sau khoảng 4 giờ chạy ở 5 FPS; khi đó Render tạm dừng toàn bộ dịch vụ free đến hết tháng.
* **Supabase làm cả DB và relay (T3):** dùng chung 5 GB egress và tự tạm dừng sau 7 ngày không hoạt động. Phù hợp làm dự phòng, không phù hợp làm chính.
* **Vercel Functions làm WebSocket (T4):** đang beta, kết nối đóng sau tối đa 300 giây, và trình duyệt với agent có thể rơi vào hai instance khác nhau nên phải thêm Redis.
* **Oracle Cloud (T5):** cấu hình mạnh nhất nhưng cần thẻ thanh toán, máy ảo rảnh lâu có thể bị thu hồi, và phải tự quản trị bảo mật.
* **Hugging Face Spaces, Koyeb, Fly.io:** không còn gói miễn phí dùng được cho container mới.

**Những đánh đổi chấp nhận được:**

* Có hai codebase phía server (FastAPI bằng Python, relay bằng TypeScript). Relay chỉ khoảng 100 dòng và không chứa logic nghiệp vụ.
* Lần gọi API đầu tiên sau 15 phút không hoạt động phải chờ Render khởi động khoảng 1 phút; xử lý bằng cách làm nóng trước buổi demo.
* Độ trễ mạng khoảng 90–100 ms mỗi frame do đi vòng qua Singapore/Hong Kong; với 5 FPS (200 ms giữa hai frame) vẫn chấp nhận được.

## 8\. Rủi ro và giảm thiểu

|Rủi ro|Ảnh hưởng|Giảm thiểu|
|-|-|-|
|Render ngủ sau 15 phút|Lần đăng nhập đầu phải chờ khoảng 1 phút|Agent gọi `GET /api/health` khi khởi động; frontend gọi khi mở trang; làm nóng 10–15 phút trước demo. Không ping 24/7 không cần thiết|
|Render tạm dừng khi hết 5 GB hoặc 750 giờ|Mất backend đến hết tháng|Không cho frame qua Render; chỉ chạy một dịch vụ free; theo dõi mục Monthly Included Usage|
|Neon ngủ sau 5 phút|Truy vấn đầu chậm thêm một chút|`pool\_pre\_ping=True`; endpoint `/api/health` chạy `SELECT 1`|
|Hạn mức DO theo ngày, reset 00:00 UTC (7:00 sáng giờ VN)|Không mở được kết nối mới khi chạm hạn mức|Gửi frame chờ kết quả; tối đa 5 FPS; tránh chạy thử dài ngay trước demo trong cùng một ngày UTC|
|Agent mất mạng|Trình duyệt không nhận được kết quả|Agent kết nối lại với thời gian chờ tăng dần 1, 2, 4… tối đa 30 giây; relay báo `agent\_offline` cho trình duyệt|
|Cloudflare cập nhật hệ thống làm ngắt WebSocket|Rớt kết nối vài giây|Cả trình duyệt và agent đều tự kết nối lại; trình duyệt lấy vé mới trước khi kết nối lại|
|Lộ vé trong URL (log)|Người khác dùng lại vé|Vé hết hạn sau 60 giây, có `jti`; DO có thể từ chối `jti` đã dùng|
|Nền tảng đổi chính sách free|Phải chuyển nền tảng|Đóng gói Docker, dùng PostgreSQL chuẩn, tách relay; có sẵn phương án dự phòng ở mục 6.7|

## 9\. Cấu hình mẫu

### 9.1. `wrangler.toml` cho relay

```toml
name = "liveinspect-relay"
main = "src/index.ts"
compatibility\_date = "2026-10-01"

\[\[durable\_objects.bindings]]
name = "ROOMS"
class\_name = "InspectionRoom"

\[\[migrations]]
tag = "v1"
new\_sqlite\_classes = \["InspectionRoom"]   # gói Workers Free chỉ hỗ trợ DO dùng SQLite

\[vars]
ALLOWED\_ORIGINS = "https://liveinspect-ai.pages.dev,http://localhost:5173"
MAX\_FRAME\_BYTES = "102400"                # 100 KB
# RELAY\_TICKET\_SECRET đặt bằng: npx wrangler secret put RELAY\_TICKET\_SECRET
```

### 9.2. Mã relay (`src/index.ts`)

```typescript
import { DurableObject } from "cloudflare:workers";

export interface Env {
  ROOMS: DurableObjectNamespace<InspectionRoom>;
  RELAY\_TICKET\_SECRET: string;
  ALLOWED\_ORIGINS: string;
  MAX\_FRAME\_BYTES: string;
}

type Role = "viewer" | "agent";
interface Ticket { room: string; role: Role; exp: number; jti: string; }

function b64urlToBytes(s: string): Uint8Array {
  const bin = atob(s.replace(/-/g, "+").replace(/\_/g, "/"));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

// Kiểm tra JWT HS256 do FastAPI ký
async function verifyTicket(token: string, secret: string): Promise<Ticket | null> {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const \[h, p, s] = parts;
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, \["verify"],
  );
  const ok = await crypto.subtle.verify(
    "HMAC", key, b64urlToBytes(s), new TextEncoder().encode(`${h}.${p}`),
  );
  if (!ok) return null;
  const claims = JSON.parse(new TextDecoder().decode(b64urlToBytes(p))) as Ticket;
  if (claims.exp < Date.now() / 1000) return null;
  return claims;
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const m = url.pathname.match(/^\\/ws\\/(\[A-Za-z0-9\_-]{3,64})$/);
    if (!m) return new Response("Not found", { status: 404 });
    if (req.headers.get("Upgrade") !== "websocket") {
      return new Response("Expected WebSocket", { status: 426 });
    }

    const ticket = await verifyTicket(url.searchParams.get("ticket") ?? "", env.RELAY\_TICKET\_SECRET);
    if (!ticket || ticket.room !== m\[1]) return new Response("Unauthorized", { status: 401 });

    if (ticket.role === "viewer") {
      const origin = req.headers.get("Origin") ?? "";
      if (!env.ALLOWED\_ORIGINS.split(",").includes(origin)) {
        return new Response("Forbidden origin", { status: 403 });
      }
    }

    // Có thể thêm { locationHint: "apac-se" } nếu muốn ép đặt ở Đông Nam Á
    const stub = env.ROOMS.get(env.ROOMS.idFromName(ticket.room));
    const fwd = new Request(req);
    fwd.headers.set("X-Role", ticket.role);
    return stub.fetch(fwd);
  },
};

export class InspectionRoom extends DurableObject<Env> {
  async fetch(req: Request): Promise<Response> {
    const role = (req.headers.get("X-Role") ?? "viewer") as Role;
    const { 0: client, 1: server } = new WebSocketPair();
    this.ctx.acceptWebSocket(server, \[role]);      // Hibernation API
    server.serializeAttachment({ role });
    if (role === "agent") this.broadcast("viewer", JSON.stringify({ type: "agent\_online" }));
    return new Response(null, { status: 101, webSocket: client });
  }

  async webSocketMessage(ws: WebSocket, msg: ArrayBuffer | string): Promise<void> {
    const { role } = ws.deserializeAttachment() as { role: Role };
    const size = typeof msg === "string" ? msg.length : msg.byteLength;
    if (size > Number(this.env.MAX\_FRAME\_BYTES)) {
      ws.close(1009, "message too large");
      return;
    }
    // viewer gửi frame tới agent; agent gửi kết quả tới mọi viewer
    this.broadcast(role === "viewer" ? "agent" : "viewer", msg);
  }

  async webSocketClose(ws: WebSocket): Promise<void> {
    const { role } = ws.deserializeAttachment() as { role: Role };
    if (role === "agent") this.broadcast("viewer", JSON.stringify({ type: "agent\_offline" }));
    try { ws.close(1000, "closed"); } catch { /\* đã đóng \*/ }
  }

  private broadcast(tag: Role, msg: ArrayBuffer | string): void {
    for (const peer of this.ctx.getWebSockets(tag)) {
      try { peer.send(msg); } catch { /\* bỏ qua kết nối hỏng \*/ }
    }
  }
}
```

### 9.3. FastAPI: cấp vé và health check

```python
import os, time, uuid
import jwt                                   # PyJWT
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

app = FastAPI()
app.add\_middleware(
    CORSMiddleware,
    allow\_origins=os.environ\["CORS\_ORIGINS"].split(","),
    allow\_credentials=True,
    allow\_methods=\["GET", "POST"],
    allow\_headers=\["Authorization", "Content-Type", "X-Agent-Secret"],
)

TICKET\_SECRET = os.environ\["RELAY\_TICKET\_SECRET"]

def issue\_ticket(room: str, role: str, ttl: int = 60) -> str:
    now = int(time.time())
    claims = {"room": room, "role": role, "iat": now, "exp": now + ttl, "jti": uuid.uuid4().hex}
    return jwt.encode(claims, TICKET\_SECRET, algorithm="HS256")

@app.get("/api/health")
async def health():
    async with engine.connect() as conn:      # engine ở mục 5.5
        await conn.execute(text("SELECT 1"))  # đánh thức Neon
    return {"status": "ok"}

@app.post("/api/agent/ticket")
async def agent\_ticket(agent\_id: str, x\_agent\_secret: str = Header(...)):
    if x\_agent\_secret != os.environ\["AGENT\_SHARED\_SECRET"]:
        raise HTTPException(status\_code=401)
    return {"room": agent\_id, "ticket": issue\_ticket(agent\_id, "agent")}

# POST /api/sessions: kiểm tra JWT người dùng, tạo inspection\_session,
# rồi trả {"session\_id": ..., "room": agent\_id, "ticket": issue\_ticket(agent\_id, "viewer")}
```

Trong thực tế nên dùng `hmac.compare\_digest` khi so sánh `AGENT\_SHARED\_SECRET`, và thêm giới hạn tốc độ cho các endpoint đăng nhập, cấp vé.

### 9.4. AI Agent: kết nối ra ngoài và tự kết nối lại

```python
import asyncio, os, random
import httpx, websockets

API = os.environ\["API\_BASE\_URL"]          # https://liveinspect-api.onrender.com
RELAY = os.environ\["RELAY\_WS\_URL"]        # wss://liveinspect-relay.<subdomain>.workers.dev
AGENT\_ID = os.environ\["AGENT\_ID"]
SECRET = os.environ\["AGENT\_SHARED\_SECRET"]

async def run\_forever(infer):              # infer(jpeg\_bytes) -> bytes (score + mask)
    backoff = 1
    while True:
        try:
            async with httpx.AsyncClient(base\_url=API, timeout=90) as http:   # chờ Render thức dậy
                await http.get("/api/health")
                r = await http.post("/api/agent/ticket",
                                    params={"agent\_id": AGENT\_ID},
                                    headers={"X-Agent-Secret": SECRET})
                r.raise\_for\_status()
                ticket = r.json()\["ticket"]
            url = f"{RELAY}/ws/{AGENT\_ID}?ticket={ticket}"
            async with websockets.connect(url, max\_size=256 \* 1024,
                                          ping\_interval=20, ping\_timeout=20) as ws:
                backoff = 1
                async for msg in ws:
                    if isinstance(msg, bytes):                       # frame JPEG
                        result = await asyncio.to\_thread(infer, msg)  # PatchCore trên GPU
                        await ws.send(result)
        except Exception as exc:
            print(f"Mất kết nối: {exc!r}; thử lại sau {backoff}s")
            await asyncio.sleep(backoff + random.random())
            backoff = min(backoff \* 2, 30)
```

### 9.5. Frontend: gửi frame theo cơ chế chờ kết quả

```typescript
const MAX\_FPS = 5;
const MAX\_FRAME\_BYTES = 100 \* 1024;

export function startStreaming(ws: WebSocket, video: HTMLVideoElement,
                               onResult: (data: ArrayBuffer) => void) {
  const canvas = document.createElement("canvas");
  canvas.width = 640; canvas.height = 480;
  const ctx = canvas.getContext("2d")!;
  ws.binaryType = "arraybuffer";

  let inFlight = false;
  let sentAt = 0;

  ws.onmessage = (ev) => {
    if (typeof ev.data === "string") return;   // thông báo trạng thái: agent\_online / agent\_offline
    inFlight = false;
    onResult(ev.data);
  };

  const timer = setInterval(async () => {
    if (ws.readyState !== WebSocket.OPEN) return;
    if (inFlight \&\& performance.now() - sentAt < 2000) return;  // quá 2s coi như mất frame
    ctx.drawImage(video, 0, 0, 640, 480);
    const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", 0.7));
    if (!blob || blob.size > MAX\_FRAME\_BYTES) return;
    inFlight = true;
    sentAt = performance.now();
    ws.send(await blob.arrayBuffer());
  }, 1000 / MAX\_FPS);

  return () => clearInterval(timer);
}
```

### 9.6. Dockerfile backend cho Render

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=10000
CMD \["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='\*'"]
```

`requirements.txt` của backend chỉ cần `fastapi`, `uvicorn\[standard]`, `sqlalchemy\[asyncio]`, `asyncpg`, `alembic`, `pyjwt`, `argon2-cffi`, `httpx`. **Không** đưa PyTorch, Anomalib hay dataset vào image backend, vì model chỉ chạy trên PC.

### 9.7. Biến môi trường theo từng nơi

|Biến|Render (FastAPI)|Cloudflare Worker|Cloudflare Pages|AI Agent (PC)|
|-|-|-|-|-|
|`DATABASE\_URL`|Có||||
|`JWT\_SECRET`|Có||||
|`RELAY\_TICKET\_SECRET`|Có|Có (secret)|||
|`AGENT\_SHARED\_SECRET`|Có|||Có|
|`CORS\_ORIGINS`|Có||||
|`ALLOWED\_ORIGINS`, `MAX\_FRAME\_BYTES`||Có (vars)|||
|`VITE\_API\_BASE\_URL`, `VITE\_WS\_RELAY\_URL`|||Có||
|`API\_BASE\_URL`, `RELAY\_WS\_URL`, `AGENT\_ID`, `MODEL\_PATH`||||Có|

Các biến `VITE\_\*` được nhúng vào file JavaScript công khai, nên **không bao giờ** đặt bí mật vào biến có tiền tố `VITE\_`.

## 10\. Các bước triển khai

1. **Neon:** tạo project PostgreSQL ở Singapore, lấy chuỗi kết nối có `-pooler`, chạy Alembic để tạo 4 bảng.
2. **Cloudflare relay:** cài `wrangler`, tạo Worker theo mục 9.1–9.2, đặt `RELAY\_TICKET\_SECRET` bằng `npx wrangler secret put`, chạy `npx wrangler deploy`.
3. **Render:** tạo Web Service từ repo, chọn Docker, region Singapore, gói Free; khai báo biến môi trường theo mục 9.7; kiểm tra `GET /api/health`.
4. **Cloudflare Pages:** kết nối repo frontend, lệnh build `npm run build`, thư mục `dist`; thêm `public/\_redirects` với dòng `/\* /index.html 200`; khai báo `VITE\_API\_BASE\_URL` và `VITE\_WS\_RELAY\_URL`.
5. **Cập nhật CORS:** thêm tên miền `\*.pages.dev` thật vào `CORS\_ORIGINS` (Render) và `ALLOWED\_ORIGINS` (Worker).
6. **AI Agent:** cài môi trường Python có CUDA trên PC, cấu hình biến môi trường, chạy `python agent.py` và kiểm tra trình duyệt nhận được `agent\_online`.
7. **Kiểm thử toàn luồng:** chạy 30 phút ở 5 FPS, ghi lại độ trễ, số lần kết nối lại, mức dùng băng thông Render và request DO trên dashboard; diễn tập chế độ LAN dự phòng.

## 11\. Việc cần đo và kiểm chứng thêm

|Hạng mục|Cách đo|Mục tiêu tham khảo|
|-|-|-|
|Độ trễ đầu-cuối|Gắn mốc thời gian ở trình duyệt khi gửi và khi nhận kết quả; tính p50 và p95|p95 dưới 400 ms ở 5 FPS \[GIẢ ĐỊNH]|
|Thời gian suy luận PatchCore trên GTX 1660 Ti|Đo trong agent (`inference\_ms`)|Cần đo thực tế|
|Kích thước frame và mask thực tế|DevTools tab Network hoặc log agent|So với giả định ở mục 1.2|
|Vị trí DO thực tế|Đọc header `cf-ray` hoặc log `request.cf.colo`|Singapore hoặc Hong Kong|
|Mức dùng hạn mức|Dashboard Render (Monthly Included Usage), Cloudflare (Durable Objects), Neon (Usage)|Dưới 50% hạn mức trong tháng demo|
|Khả năng tự phục hồi|Rút mạng PC 30 giây, kiểm tra agent tự kết nối lại|Phục hồi dưới 30 giây|
|Bảo mật|Thử kết nối relay không có vé, vé hết hạn, Origin lạ|Đều bị từ chối|

Lưu ý thêm về điều khoản: Vercel Hobby chỉ cho mục đích phi thương mại; dataset MVTec AD theo giấy phép CC BY-NC-SA 4.0 (phi thương mại). Nếu sau này thương mại hóa, phải thay dataset và xem lại gói dịch vụ.

## Phụ lục A. Đính chính so với bản trước

|Nội dung bản trước|Đính chính|
|-|-|
|Neon tăng lên 1 GB/project từ 02/10/2026|Trang giá chính thức vẫn ghi **0,5 GB/project**. Kết luận chọn Neon không đổi|
|DO nối biên tại Hà Nội, độ trễ dưới 30 ms|DO chỉ đặt ở data center có hỗ trợ DO (nhiều khả năng Singapore/Hong Kong); phần mạng mỗi frame khoảng 90–100 ms|
|Tổng điểm T3 (Render all-in-one) = 3,45|Tính lại đúng là 3,55 với điểm cũ; bản này chấm lại toàn bộ (xem mục 6.2)|
|Tổng điểm T4 (Oracle) = 3,68|Tính lại đúng là 3,65 với điểm cũ; bản này chấm lại toàn bộ|
|`prepared\_statement\_cache\_size` đặt trong `connect\_args`|Gây lỗi `TypeError`; chuyển sang tham số URL|
|Trình duyệt xác thực WebSocket bằng JWT trong header|Trình duyệt không gắn được header khi mở WebSocket; thay bằng vé ngắn hạn trong query string, kiểm tra Origin|
|Lỗi đếm 1:1 của Cloudflare ghi là \[DỮ KIỆN]|Đổi thành \[CHƯA XÁC MINH] (chỉ có một bài diễn đàn)|
|Prisma Postgres: 1,01 GB, 200.000 truy vấn|Trang chính thức ghi 500 MB; số truy vấn free là 100.000 hoặc 200.000 tùy trang|
|Vercel giữ 3 bản deploy được tính là nhược điểm|Bản production hiện tại không bao giờ bị xoá; không ảnh hưởng đồ án|
|Dự phòng bằng Vercel + Railway + WebRTC|Thay bằng Supabase Realtime, chế độ LAN và video quay sẵn (ít rủi ro hơn)|
|Thiếu sơ đồ Mermaid, công thức bị mất|Bổ sung 4 sơ đồ và toàn bộ công thức ở mục 4, 5, 6|
|Nguồn chủ yếu là blog tổng hợp|Thay bằng tài liệu chính thức (Phụ lục B)|

## Phụ lục B. Nguồn tham khảo

Trạng thái "Đã đối chiếu" nghĩa là đã kiểm tra trực tiếp trang chính thức hoặc nguồn tin cậy trong khoảng 10/2026.

|Nhà cung cấp|Tài liệu|Trạng thái|
|-|-|-|
|Cloudflare|Durable Objects Pricing: https://developers.cloudflare.com/durable-objects/platform/pricing/|Đã đối chiếu|
|Cloudflare|Durable Objects Data location: https://developers.cloudflare.com/durable-objects/reference/data-location/|Đã đối chiếu|
|Cloudflare|Changelog gợi ý vị trí apac-ne, apac-se: https://developers.cloudflare.com/changelog/post/2026-06-19-apac-ne-apac-se-location-hints/|Đã đối chiếu|
|Cloudflare|Durable Objects Limits: https://developers.cloudflare.com/durable-objects/platform/limits/|Đã đối chiếu|
|Cloudflare|WebSockets với Durable Objects: https://developers.cloudflare.com/durable-objects/best-practices/websockets/|Tham khảo|
|Cloudflare|Pages Limits: https://developers.cloudflare.com/pages/platform/limits/|Đã đối chiếu|
|Cloudflare|Workers Limits: https://developers.cloudflare.com/workers/platform/limits/|Đã đối chiếu|
|Render|Deploy for Free: https://render.com/docs/free|Đã đối chiếu|
|Render|New Workspace Plans: https://render.com/docs/new-workspace-plans|Đã đối chiếu (qua bài tổng hợp trích dẫn)|
|Vercel|Limits: https://vercel.com/docs/limits|Đã đối chiếu|
|Vercel|WebSockets trên Functions: https://vercel.com/docs/functions/websockets|Đã đối chiếu|
|Vercel|Hobby plan: https://vercel.com/docs/plans/hobby|Đã đối chiếu|
|Vercel|Changelog lưu giữ deploy Hobby: https://vercel.com/changelog/hobby-projects-now-retain-fewer-deployments-to-free-up-storage|Đã đối chiếu|
|Netlify|Credit-based pricing plans: https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/|Đã đối chiếu|
|GitHub|GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits|Tham khảo|
|Firebase|Pricing: https://firebase.google.com/pricing|Chưa đối chiếu|
|Hugging Face|Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview|Đã đối chiếu|
|Railway|Free Trial: https://docs.railway.com/pricing/free-trial|Đã đối chiếu|
|Koyeb|Blog "Koyeb is Joining Mistral AI" (02/2026): https://www.koyeb.com/blog|Đã đối chiếu|
|Fly.io|Pricing: https://fly.io/docs/about/pricing/|Tham khảo|
|Google Cloud|Cloud Run WebSockets: https://cloud.google.com/run/docs/triggering/websockets|Đã đối chiếu|
|Oracle|Always Free Resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier\_topic-Always\_Free\_Resources.htm|Tham khảo|
|Neon|Pricing: https://neon.com/pricing|Đã đối chiếu|
|Neon|Kết nối Python: https://neon.com/docs/guides/python|Tham khảo|
|Supabase|Pricing: https://supabase.com/pricing|Đã đối chiếu (qua bài tổng hợp trích dẫn)|
|Supabase|Realtime limits: https://supabase.com/docs/guides/realtime/limits|Đã đối chiếu|
|Supabase|Free project pausing: https://supabase.com/docs/guides/platform/free-project-pausing|Tham khảo|
|Prisma|Pricing: https://www.prisma.io/pricing|Đã đối chiếu|
|Prisma|Plans and quotas: https://www.prisma.io/docs/data-platform/billing/plans-and-quotas|Đã đối chiếu|
|SQLAlchemy|asyncpg dialect: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html|Tham khảo|
|WonderNetwork|Ping Hà Nội–Singapore: https://wondernetwork.com/pings/Hanoi/Singapore|Đã đối chiếu|
|MVTec|MVTec AD: https://www.mvtec.com/research-teaching/datasets/mvtec-ad|Đã đối chiếu|



