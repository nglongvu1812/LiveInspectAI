# Báo Cáo Nghiên cứu Tập dữ liệu MVTec AD

## 1. Tổng quan (Overview)
**MVTec AD (Anomaly Detection)** là một trong những tập dữ liệu tiêu chuẩn (benchmark dataset) phổ biến nhất dành cho bài toán phát hiện và định vị lỗi bất thường (anomaly detection and localization) theo phương pháp học máy không giám sát (unsupervised learning) trong lĩnh vực kiểm tra chất lượng công nghiệp. 

Tập dữ liệu này cung cấp hơn 5,000 hình ảnh độ phân giải cao, kèm theo nhãn ground-truth ở mức độ điểm ảnh (pixel-accurate) cho các vùng bị lỗi, giúp đánh giá chính xác cả khả năng phân loại và khoanh vùng của các mô hình AI.

## 2. Phân loại Nhóm ảnh: Bình thường và Lỗi
Do tính chất của phương pháp học không giám sát trong phát hiện bất thường, tập dữ liệu được thiết kế với cơ chế phân chia nghiêm ngặt:

*   **Nhóm ảnh Bình thường (Normal / Defect-free):**
    *   Sử dụng toàn bộ cho tập huấn luyện (Training Set). Các mô hình chỉ được phép "nhìn thấy" các sản phẩm hoàn hảo không có lỗi để học ra phân phối chuẩn của dữ liệu.
    *   Một phần cũng được đưa vào tập kiểm thử để đánh giá tỷ lệ dương tính giả (False Positive).
*   **Nhóm ảnh Lỗi (Anomalous / Defective):**
    *   Chỉ xuất hiện trong tập kiểm thử (Test Set).
    *   Mỗi ảnh lỗi đều chứa ít nhất một khuyết tật trên sản phẩm hoặc bề mặt vật liệu. Các lỗi này mô phỏng sát với thực tế môi trường sản xuất.

## 3. Danh mục Dữ liệu (Categories)
Tập dữ liệu bao gồm 15 danh mục khác nhau, được chia làm 2 nhóm chính:

### 3.1. Nhóm Bề mặt (Textures - 5 danh mục)
Bao gồm các vật liệu có cấu trúc hoa văn hoặc bề mặt lặp lại. Các lỗi ở nhóm này thường phá vỡ tính liên tục của cấu trúc.
1.  **Carpet** (Thảm)
2.  **Grid** (Lưới kim loại)
3.  **Leather** (Da)
4.  **Tile** (Gạch men)
5.  **Wood** (Gỗ)

### 3.2. Nhóm Vật thể (Objects - 10 danh mục)
Bao gồm các đồ vật có hình dáng và cấu trúc xác định.
1.  **Bottle** (Chai thủy tinh/nhựa)
2.  **Cable** (Dây cáp điện)
3.  **Capsule** (Viên nang)
4.  **Hazelnut** (Hạt dẻ)
5.  **Metal Nut** (Đai ốc kim loại)
6.  **Pill** (Viên thuốc nén)
7.  **Screw** (Ốc vít)
8.  **Toothbrush** (Bàn chải đánh răng)
9.  **Transistor** (Linh kiện bán dẫn)
10. **Zipper** (Khóa kéo)

## 4. Các nhóm Lỗi phổ biến (Defect Types)
Có tổng cộng khoảng 73 loại lỗi xuất hiện rải rác trong 15 danh mục kể trên. Một số nhóm lỗi điển hình bao gồm:
*   **Biến dạng vật lý:** Vết rách (cut), trầy xước (scratch), nứt (crack), lỗ thủng (hole), uốn cong (bent), móp méo.
*   **Thiếu sót hoặc sai lệch lắp ráp:** Thiếu linh kiện (missing part), dây đứt, đặt sai vị trí (misplaced/shifted), chân linh kiện bị lỗi.
*   **Lỗi ngoại quan/Màu sắc:** Vết dơ (contamination), dính chất lỏng (liquid), sai khác màu sắc (color variant), lỗi in ấn logo/chữ (print).