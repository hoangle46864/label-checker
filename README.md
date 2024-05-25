# Label Checker

`Label Checker` là một ứng dụng được thiết kế để kiểm tra chất lượng nhãn của dữ liệu ảnh, cụ thể là ảnh vi khuẩn E. coli.

## Tính Năng
- **Load Ảnh và Nhãn**: Hỗ trợ định dạng file .tiff cho cả ảnh gốc và nhãn.
- **Duyệt qua Các Đối Tượng**: Cho phép truy cập và xem xét từng label của từng đối tượng một cách dễ dàng.
- **Điều chỉnh Độ Trong Suốt của Nhãn**: Có thể điều chỉnh độ trong suốt của nhãn để phân biệt rõ ràng giữa ảnh gốc và nhãn.
- **Lưu và Tải Tiến Trình Làm Việc**: Cho phép lưu lại tiến trình làm việc và tải lại để tiếp tục công việc khi cần.

## Yêu cầu
Để sử dụng `Label Checker`, bạn cần cài đặt Python và các thư viện được liệt kê trong `requirements.txt`.

## Cách Sử Dụng

### Thao tác bằng nút nhấn trên ứng dụng
![Ảnh ứng dụng](https://i.imgur.com/iRbtl0j.png)

Sử dụng các nút giao diện để thực hiện các chức năng:
- **Load Image**: Tải ảnh và nhãn tương ứng
- **Next Object**: Chuyển đến object tiếp theo
- **Previous Object**: Quay lại object trước đó
- **Yes/No**: Xác nhận hoặc từ chối label
- **Merge**: Gộp ảnh và label (Để kiểm tra có label thiếu hay không)
- **Show/Hide Mask**: Hiển thị hoặc ẩn label
- **Save Progress**: Lưu tiến trình hiện tại
- **Load Progress**: Tải tiến trình đã lưu
- **Thanh trượt**: Trượt tới hoặc lui để tăng hoặc giảm độ trong suốt của label

![Ảnh một tiến trình](https://i.imgur.com/R6mcYlx.png)  
Object có màu **xanh**: Label có chất lượng tốt  
Object có màu **đỏ**: Label có chất lượng kém  
Object có màu **trắng**: Chưa được kiểm tra  
Object **đang kiểm tra**: Object có số thứ tự bên dưới nút `Load Progress`
   

### Thao tác bằng bàn phím
Bên cạnh đó có thể sử dụng các phím tắt sau để thực hiện nhanh các chức năng:
- `A`: Quay lại object trước
- `D`: Chuyển đến object tiếp theo
- `I`: Xác nhận label cho object
- `O`: Từ chối label cho object
- `Q`: Zoom out 
- `E`: Zoom in 
