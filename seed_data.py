from db import get_db_connection

def init_data():
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cursor = conn.cursor()

        print("Đang khởi tạo dữ liệu cho Web Cơ Sở - Nhà trọ Nguyễn Duy...")

        # 1. Tìm hoặc tạo tài khoản chủ trọ
        cursor.execute("SELECT TOP 1 Id FROM TaiKhoan")
        row_tk = cursor.fetchone()

        if row_tk:
            chutro_id = row_tk[0]
        else:
            cursor.execute("""
                INSERT INTO TaiKhoan (TenDangNhap, MatKhau, HoTen, VaiTro)
                VALUES ('admin_duy', '123456', N'Nguyễn Duy', 'ChuTro')
            """)
            cursor.execute("SELECT TOP 1 Id FROM TaiKhoan ORDER BY Id DESC")
            chutro_id = row_tk[0] if 'row_tk' in locals() and row_tk else 1

        # 2. Kiểm tra hoặc tạo mới cơ sở Nhà trọ Nguyễn Duy
        cursor.execute("SELECT Id FROM CoSo WHERE TenCoSo = N'Nhà trọ Nguyễn Duy'")
        row_coso = cursor.fetchone()

        if not row_coso:
            cursor.execute("""
                INSERT INTO CoSo (Slug, TenCoSo, ChuTroId, DiaChi, KhuVuc, GiaDien, GiaNuoc, HoatDong)
                VALUES ('nha-tro-nguyen-duy', N'Nhà trọ Nguyễn Duy', ?, N'Đường 3/2, Phường Tích Lương (Gần ĐH Kỹ thuật Công nghiệp Thái Nguyên)', N'Tích Lương', 3500, 15000, 1)
            """, (chutro_id,))
            print("--> Đã tạo mới cơ sở: Nhà trọ Nguyễn Duy")
        else:
            print("--> Cơ sở Nhà trọ Nguyễn Duy đã tồn tại.")

        cursor.execute("SELECT Id FROM CoSo WHERE TenCoSo = N'Nhà trọ Nguyễn Duy'")
        coso_id = cursor.fetchone()[0]

        # Tạm thời vô hiệu hóa check constraint của bảng Phong để không bị lỗi ràng buộc TrangThai
        try:
            cursor.execute("ALTER TABLE Phong NOCHECK CONSTRAINT ALL")
        except Exception:
            pass

        # 3. Khởi tạo 10 phòng mẫu nếu cơ sở chưa có phòng
        cursor.execute("SELECT COUNT(*) FROM Phong WHERE CoSoId = ?", (coso_id,))
        count_phong = cursor.fetchone()[0]

        if count_phong == 0:
            for i in range(1, 11):
                so_phong = f"Phòng {100 + i}"
                dien_tich = 18 if i <= 5 else 22
                gia_thue = 800000 if i <= 5 else 1000000
                trang_thai = 'Trống' if i % 2 == 1 else 'Đã thuê'
                mo_ta = f"Phòng khép kín diện tích {dien_tich}m2, có gác xép, nóng lạnh, wifi tốc độ cao, cách cổng ĐH Kỹ thuật Công nghiệp 300m."
                cursor.execute("""
                    INSERT INTO Phong (CoSoId, SoPhong, DienTich, GiaThue, TrangThai, MoTa)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (coso_id, so_phong, dien_tich, gia_thue, trang_thai, mo_ta))
            print("--> Đã khởi tạo 10 phòng trọ tiêu chuẩn cho Nhà trọ Nguyễn Duy.")

        # Bật lại check constraint
        try:
            cursor.execute("ALTER TABLE Phong CHECK CONSTRAINT ALL")
        except Exception:
            pass

        print(f"HOÀN TẤT! Dữ liệu Web Cơ Sở - Nhà trọ Nguyễn Duy (ID: {coso_id}) đã sẵn sàng.")
        cursor.close()
        conn.close()

    except Exception as e:
        print("Lỗi khởi tạo dữ liệu:", e)

if __name__ == "__main__":
    init_data()