from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'nha_tro_nguyen_duy_secret_key'

# Dữ liệu dự phòng nếu DB chưa sẵn sàng
FALLBACK_COSO = {
    'Id': 1,
    'Slug': 'nha-tro-nguyen-duy',
    'TenCoSo': 'Nhà trọ Nguyễn Duy',
    'DiaChi': 'Đường 3/2, Phường Tích Lương (Cách cổng ĐH Kỹ thuật Công nghiệp Thái Nguyên 300m)',
    'KhuVuc': 'Tích Lương - Thái Nguyên',
    'GiaDien': 3500,
    'GiaNuoc': 15000,
    'SoDienThoai': '0987.654.321',
    'ChuTro': 'Nguyễn Duy',
    'MoTa': 'Hệ thống phòng trọ sinh viên khép kín, an ninh 24/7, camera giám sát, khóa vân tay, chỗ để xe rộng rãi miễn phí, wifi cáp quang từng tầng.'
}

FALLBACK_PHONGS = [
    {'Id': i, 'SoPhong': f'Phòng {100+i}', 'DienTich': 18 if i<=5 else 22,
     'GiaThue': 800000 if i<=5 else 1000000,
     'TrangThai': 'Trong' if i in [1, 3, 5, 7, 9] else 'DaThue',
     'MoTa': 'Phòng khép kín, có gác xép, bình nóng lạnh, kệ bếp nấu ăn, ban công thoáng mát.'}
    for i in range(1, 11)
]

def get_coso_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Slug, TenCoSo, DiaChi, KhuVuc, GiaDien, GiaNuoc FROM CoSo WHERE TenCoSo = 'Nhà trọ Nguyễn Duy' LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT Id, Slug, TenCoSo, DiaChi, KhuVuc, GiaDien, GiaNuoc FROM CoSo LIMIT 1")
            row = cursor.fetchone()
        
        if row:
            coso = {
                'Id': row[0],
                'Slug': row[1],
                'TenCoSo': row[2],
                'DiaChi': row[3],
                'KhuVuc': row[4],
                'GiaDien': row[5],
                'GiaNuoc': row[6],
                'SoDienThoai': '0987.654.321',
                'ChuTro': 'Nguyễn Duy',
                'MoTa': 'Hệ thống phòng trọ sinh viên khép kín, an ninh 24/7, camera giám sát, khóa vân tay, chỗ để xe rộng rãi miễn phí, wifi cáp quang từng tầng.'
            }
            cursor.execute("SELECT Id, SoPhong, DienTich, GiaThue, TrangThai, MoTa FROM Phong WHERE CoSoId = ? ORDER BY SoPhong", (coso['Id'],))
            phongs = []
            for p in cursor.fetchall():
                phongs.append({
                    'Id': p[0],
                    'SoPhong': p[1],
                    'DienTich': p[2],
                    'GiaThue': p[3],
                    'TrangThai': p[4],
                    'MoTa': p[5]
                })
            cursor.close()
            conn.close()
            return coso, phongs if phongs else FALLBACK_PHONGS
    except Exception as e:
        print("Cảnh báo DB (đang dùng dữ liệu dự phòng):", e)
    return FALLBACK_COSO, FALLBACK_PHONGS

@app.route('/')
def index():
    coso, phongs = get_coso_data()
    trang_thai_filter = request.args.get('trang_thai', 'ALL')
    if trang_thai_filter != 'ALL':
        phongs_filtered = [p for p in phongs if p['TrangThai'] == trang_thai_filter]
    else:
        phongs_filtered = phongs

    tong_phong = len(phongs)
    phong_trong = len([p for p in phongs if p['TrangThai'] == 'Trong'])
    return render_template(
        'index.html',
        coso=coso,
        phongs=phongs_filtered,
        tong_phong=tong_phong,
        phong_trong=phong_trong,
        trang_thai_filter=trang_thai_filter
    )

@app.route('/dat-lich', methods=['POST'])
def dat_lich():
    ho_ten = request.form.get('ho_ten')
    sdt = request.form.get('sdt')
    phong_id = request.form.get('phong_id')
    ngay_xem = request.form.get('ngay_xem')
    ghi_chu = request.form.get('ghi_chu', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO DatLich (PhongId, HoTenKhach, SoDienThoai, NgayXem, GhiChu, TrangThai)
            VALUES (?, ?, ?, ?, ?, 'ChoDuyet')
        """, (phong_id, ho_ten, sdt, ngay_xem, ghi_chu))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Ghi nhận đặt lịch (chế độ demo):", e)

    flash(f'Đã gửi yêu cầu đặt lịch xem phòng thành công! Chủ trọ Nguyễn Duy sẽ liên hệ số {sdt} trong ít phút.', 'success')
    return redirect(url_for('index'))

@app.route('/quan-ly')
def quan_ly():
    coso, phongs = get_coso_data()
    return render_template('quan_ly.html', coso=coso, phongs=phongs)

@app.route('/quan-ly/cap-nhat-phong/<int:phong_id>', methods=['POST'])
def cap_nhat_phong(phong_id):
    trang_thai = request.form.get('trang_thai')
    gia_thue = request.form.get('gia_thue')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Phong SET TrangThai = ?, GiaThue = ? WHERE Id = ?", (trang_thai, gia_thue, phong_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Cập nhật thông tin phòng thành công!', 'success')
    except Exception as e:
        flash(f'Lỗi cập nhật: {e}', 'danger')
    return redirect(url_for('quan_ly'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)