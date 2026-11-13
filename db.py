import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'nhatro.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Giúp truy xuất cột dạng từ điển
    return conn

def init_sqlite_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tạo bảng Tài Khoản
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TaiKhoan (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            TenDangNhap TEXT,
            MatKhau TEXT,
            HoTen TEXT,
            VaiTro TEXT
        )
    ''')
    
    # Tạo bảng Cơ Sở
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CoSo (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Slug TEXT,
            TenCoSo TEXT,
            ChuTroId INTEGER,
            DiaChi TEXT,
            KhuVuc TEXT,
            GiaDien REAL,
            GiaNuoc REAL,
            HoatDong INTEGER
        )
    ''')
    
    # Tạo bảng Phòng
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Phong (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            CoSoId INTEGER,
            SoPhong TEXT,
            DienTich REAL,
            GiaThue REAL,
            TrangThai TEXT,
            MoTa TEXT
        )
    ''')
    
    # Tạo bảng Đặt Lịch
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DatLich (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            PhongId INTEGER,
            HoTenKhach TEXT,
            SoDienThoai TEXT,
            NgayXem TEXT,
            GhiChu TEXT,
            TrangThai TEXT
        )
    ''')
    
    # Kiểm tra xem đã có dữ liệu cơ sở chưa, nếu chưa thì thêm dữ liệu mẫu
    cursor.execute("SELECT COUNT(*) FROM CoSo")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO TaiKhoan (TenDangNhap, MatKhau, HoTen, VaiTro) VALUES ('admin_duy', '123456', 'Nguyễn Duy', 'ChuTro')")
        cursor.execute("""
            INSERT INTO CoSo (Slug, TenCoSo, ChuTroId, DiaChi, KhuVuc, GiaDien, GiaNuoc, HoatDong)
            VALUES ('nha-tro-nguyen-duy', 'Nhà trọ Nguyễn Duy', 1, 'Đường 3/2, Phường Tích Lương (Gần ĐH Kỹ thuật Công nghiệp Thái Nguyên)', 'Tích Lương', 3500, 15000, 1)
        """)
        
        # Thêm 10 phòng mẫu
        for i in range(1, 11):
            so_phong = f"Phòng {100 + i}"
            dien_tich = 18 if i <= 5 else 22
            gia_thue = 800000 if i <= 5 else 1000000
            trang_thai = 'Trong' if i % 2 == 1 else 'DaThue'
            mo_ta = f"Phòng khép kín diện tích {dien_tich}m2, có gác xép, nóng lạnh, wifi tốc độ cao."
            cursor.execute("""
                INSERT INTO Phong (CoSoId, SoPhong, DienTich, GiaThue, TrangThai, MoTa)
                VALUES (1, ?, ?, ?, ?, ?)
            """, (so_phong, dien_tich, gia_thue, trang_thai, mo_ta))
            
    conn.commit()
    cursor.close()
    conn.close()

# Tự động khởi tạo database khi chạy app
init_sqlite_db()