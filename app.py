import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'nha_tro_nguyen_duy_secret_key'

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
    {
        'Id': i,
        'SoPhong': f'Phòng {100 + i}',
        'DienTich': 18 if i <= 5 else 22,
        'GiaThue': 1500000 if i <= 5 else 2000000,
        'TrangThai': 'Trong' if i in [1, 3, 5, 7, 9] else 'DaThue',
        'MoTa': 'Phòng khép kín, có gác xép, bình nóng lạnh, kệ bếp nấu ăn, ban công thoáng mát.'
    }
    for i in range(1, 11)
]


def init_auth_and_pricing():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE NOT NULL,
                PasswordHash TEXT NOT NULL,
                Role TEXT NOT NULL DEFAULT 'user'
            )
        """)
        default_users = [
            ('admin', generate_password_hash('123456'), 'admin'),
            ('chutro', generate_password_hash('123456'), 'chutro'),
            ('khach', generate_password_hash('123456'), 'user')
        ]
        for uname, phash, role in default_users:
            cursor.execute("""
                INSERT OR IGNORE INTO Users (Username, PasswordHash, Role)
                VALUES (?, ?, ?)
            """, (uname, phash, role))

        # Cập nhật giá phòng mặc định thành 1.500.000đ (phòng đầu) và 2.000.000đ (các phòng sau)
        cursor.execute("SELECT Id, SoPhong FROM Phong ORDER BY Id ASC")
        rows = cursor.fetchall()
        for idx, r in enumerate(rows):
            gia_moi = 1500000 if idx < 5 else 2000000
            cursor.execute("UPDATE Phong SET GiaThue = ? WHERE Id = ?", (gia_moi, r[0]))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Cảnh báo khởi tạo auth/giá phòng:", e)


init_auth_and_pricing()


def is_manager():
    return session.get('role') in ('admin', 'chutro')


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user'):
            flash('Vui lòng đăng nhập bằng tài khoản chủ trọ hoặc admin!', 'warning')
            return redirect(url_for('index'))
        if not is_manager():
            flash('Chỉ tài khoản chủ trọ hoặc admin mới được vào Quản lý cơ sở!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_auth_info():
    return {
        'current_user': session.get('user'),
        'current_role': session.get('role'),
        'can_manage': is_manager()
    }


def get_coso_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Id, Slug, TenCoSo, DiaChi, KhuVuc, GiaDien, GiaNuoc FROM CoSo WHERE TenCoSo = 'Nhà trọ Nguyễn Duy' LIMIT 1"
        )
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
            cursor.execute(
                "SELECT Id, SoPhong, DienTich, GiaThue, TrangThai, MoTa FROM Phong WHERE CoSoId = ? ORDER BY SoPhong",
                (coso['Id'],)
            )
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


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm = request.form.get('confirm_password', '')

    if not username or not password:
        flash('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!', 'danger')
        return redirect(url_for('index'))

    if password != confirm:
        flash('Mật khẩu nhập lại không khớp!', 'danger')
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Users (Username, PasswordHash, Role) VALUES (?, ?, 'user')",
            (username, generate_password_hash(password))
        )
        conn.commit()
        cursor.close()
        conn.close()

        session['user'] = username
        session['role'] = 'user'
        flash(f'Đăng ký thành công! Chào {username}, bây giờ bạn đã có thể đăng ký phòng.', 'success')
    except sqlite3.IntegrityError:
        flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác!', 'danger')
    except Exception as e:
        flash(f'Lỗi đăng ký: {e}', 'danger')

    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Username, PasswordHash, Role FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user'] = user[0]
            session['role'] = user[2]
            if user[2] in ('admin', 'chutro'):
                flash(f'Đăng nhập chủ trọ ({user[0]}) thành công! Đã mở mục Quản lý cơ sở.', 'success')
            else:
                flash(f'Đăng nhập thành công ({user[0]})! Bạn đã có thể đăng ký phòng.', 'success')
        else:
            flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')
    except Exception as e:
        flash(f'Lỗi đăng nhập: {e}', 'danger')

    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Bạn đã đăng xuất!', 'info')
    return redirect(url_for('index'))


@app.route('/dat-lich', methods=['POST'])
def dat_lich():
    if not session.get('user'):
        flash('Bạn cần đăng nhập tài khoản trước khi đăng ký phòng!', 'warning')
        return redirect(url_for('index'))

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
        print("Ghi nhận đăng ký phòng (chế độ demo):", e)

    flash(f'Đã đăng ký phòng thành công dưới tài khoản {session.get("user")}! Chủ trọ sẽ liên hệ số {sdt}.', 'success')
    return redirect(url_for('index'))


@app.route('/quan-ly')
@manager_required
def quan_ly():
    coso, phongs = get_coso_data()
    return render_template('quan_ly.html', coso=coso, phongs=phongs)


@app.route('/quan-ly/cap-nhat-phong/<int:phong_id>', methods=['POST'])
@manager_required
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
        flash('Đã cập nhật giá và trạng thái phòng!', 'success')
    except Exception as e:
        flash(f'Lỗi cập nhật: {e}', 'danger')
    return redirect(url_for('quan_ly'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)