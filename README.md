# 📘 Trang wed sử dụng RSA để xác thực chữ kí số

> Một trang web giới thiệu về xác thực chữ kí số bằng RSA, xây dựng bằng ngôn ngữ Python, HTML, CSS và JavaScript.
## 🚀 Giới thiệu qua chức năng và cách hoạt động của trang wed
> Hệ thống chữ ký số sử dụng Flask, SocketIO và RSA để ký và xác thực tài liệu:
Client (client.html):
Tạo cặp khóa RSA (public/private).
Tải file lên, tạo hash SHA256.
Ký hash bằng khóa riêng, gửi chữ ký, khóa công khai, hash, tên file đến server.
Server (server.html):
Nhận dữ liệu từ client (tên file, hash, chữ ký, khóa công khai).
Xác thực chữ ký bằng khóa công khai, so sánh hash để kiểm tra tính toàn vẹn.
Giao tiếp: SocketIO đảm bảo truyền dữ liệu thời gian thực qua các "room".
Bảo mật: RSA (2048-bit), SHA256, PSS padding.

## 🚀 Demo

👉 [Xem trang web tại đây](https://yourusername.github.io/ten-du-an/)  
(hoặc ghi "Chưa có link nếu bạn chưa deploy")

## 📷 Screenshot

![Screenshot 2025-06-19 132851](https://github.com/user-attachments/assets/131025e9-2b20-4402-8e9f-b8b927cd1609) 

## 📁 Cấu trúc dự án

```bash
.
├── main.py
├── tempalte/
│   └── index.html
│   └── server.html
│   └── client.html
└── README.md
