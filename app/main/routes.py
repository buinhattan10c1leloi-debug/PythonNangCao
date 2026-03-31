from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
# BỔ SUNG: Thêm OfflineAppointmentForm và PrescriptionForm vào danh sách import
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, \
    MessageForm, AppointmentForm, MedicalRecordForm, OfflineAppointmentForm, PrescriptionForm
# THÊM Medicine vào danh sách models
from app.models import User, Post, Message, Notification, Appointment, MedicalRecord, Medicine
from app.translate import translate
from app.main import bp


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required 
def index():
    return render_template('index.html', title=_('Trang chủ'))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Khám phá'), posts=posts.items, 
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Đã lưu thay đổi.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Sửa hồ sơ'), form=form)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.unread_message_count())
        db.session.commit()
        flash(_('Tin nhắn đã được gửi.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Gửi tin nhắn'), form=form, recipient=recipient)


# ====================================================================
# HỆ THỐNG BỆNH VIỆN - ROUTE CHO BỆNH NHÂN
# ====================================================================

@bp.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    form = AppointmentForm()
    doctors = db.session.scalars(sa.select(User).where(User.role == 'doctor')).all()
    form.doctor.choices = [(d.id, d.username) for d in doctors]

    if form.validate_on_submit():
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()
        apt = Appointment(
            appointment_date=form.date.data,
            appointment_time=time_obj,
            notes=form.notes.data,
            patient_id=current_user.id,
            doctor_id=form.doctor.data,
            status='Pending'
        )
        db.session.add(apt)
        db.session.commit()
        flash(_('Đặt lịch khám thành công! Vui lòng chờ xác nhận.'))
        return redirect(url_for('main.my_appointments'))
    return render_template('book_appointment.html', title=_('Đặt lịch khám'), form=form)


@bp.route('/my_appointments')
@login_required
def my_appointments():
    query = sa.select(Appointment).where(
        Appointment.patient_id == current_user.id
    ).order_by(Appointment.appointment_date.desc())
    appointments = db.session.scalars(query).all()
    return render_template('my_appointments.html', title=_('Lịch hẹn của tôi'), appointments=appointments)


@bp.route('/cancel_appointment/<int:id>', methods=['POST'])
@login_required
def cancel_appointment(id):
    apt = db.session.get(Appointment, id)
    if apt is None or apt.patient_id != current_user.id:
        flash(_('Không tìm thấy lịch hẹn.'))
        return redirect(url_for('main.my_appointments'))
    
    if apt.status == 'Pending':
        apt.status = 'Cancelled'
        db.session.commit()
        flash(_('Đã hủy lịch hẹn thành công.'))
    else:
        flash(_('Không thể hủy lịch hẹn đã được xác nhận.'))
    return redirect(url_for('main.my_appointments'))


@bp.route('/medical_history')
@login_required
def medical_history():
    query = sa.select(MedicalRecord).join(Appointment).where(
        Appointment.patient_id == current_user.id
    ).order_by(MedicalRecord.timestamp.desc())
    records = db.session.scalars(query).all()
    return render_template('medical_history.html', title=_('Lịch sử khám bệnh'), records=records)


# ====================================================================
# HỆ THỐNG BỆNH VIỆN - ROUTE CHO BÁC SĨ
# ====================================================================

@bp.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        flash(_('Bạn không có quyền truy cập.'))
        return redirect(url_for('main.index'))
    query = sa.select(Appointment).where(
        Appointment.doctor_id == current_user.id,
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.appointment_date.asc())
    appointments = db.session.scalars(query).all()
    return render_template('doctor_dashboard.html', title=_('Bảng bác sĩ'), appointments=appointments)


@bp.route('/confirm_appointment/<int:id>', methods=['POST'])
@login_required
def confirm_appointment(id):
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))
    apt = db.session.get(Appointment, id)
    if apt and apt.doctor_id == current_user.id:
        apt.status = 'Confirmed'
        db.session.commit()
        flash(_('Đã xác nhận lịch hẹn.'))
    return redirect(url_for('main.doctor_dashboard'))


@bp.route('/examine/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def examine(appointment_id):
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))
    
    apt = db.session.get(Appointment, appointment_id)
    if not apt or apt.doctor_id != current_user.id:
        flash(_('Không tìm thấy lịch hẹn.'))
        return redirect(url_for('main.doctor_dashboard'))

    # Lấy danh sách thuốc để bác sĩ chọn từ mục lục bên trái trang khám
    medicines = db.session.scalars(sa.select(Medicine).order_by(Medicine.name.asc())).all()

    # Sử dụng PrescriptionForm để kê đơn thuốc chuyên sâu
    form = PrescriptionForm()
    if form.validate_on_submit():
        record = MedicalRecord(
            diagnosis=form.diagnosis.data,
            prescription=form.medicine_details.data, 
            doctor_advice=form.doctor_advice.data,
            appointment_id=apt.id
        )
        apt.status = 'Completed'
        db.session.add(record)
        db.session.commit()
        flash(_('Đã hoàn tất khám bệnh và gửi đơn thuốc sang Quầy thuốc.'))
        return redirect(url_for('main.doctor_dashboard'))
    return render_template('examine.html', title=_('Khám bệnh'), form=form, apt=apt, medicines=medicines)

@bp.route('/news', methods=['GET', 'POST'])
@login_required 
def news():
    form = PostForm()
    if current_user.is_authenticated and form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Bài viết của bạn đã được đăng tải thành công!'), 'success')
        return redirect(url_for('main.news'))
    
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts() if current_user.is_authenticated else Post.query.order_by(Post.timestamp.desc()),
                        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('main.news', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.news', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('news.html', title=_('Bản tin Cộng đồng'), form=form,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)

# --- KHU VỰC DÀNH RIÊNG CHO ADMIN ---

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập khu vực Quản trị!', 'error')
        return redirect(url_for('main.index'))
    
    patients = db.session.scalars(sa.select(User).where(User.role == 'patient')).all()
    doctors = db.session.scalars(sa.select(User).where(User.role == 'doctor')).all()
    
    return render_template('admin_dashboard.html', title='Quản trị Hệ thống', patients=patients, doctors=doctors)

@bp.route('/admin/create_doctor', methods=['POST'])
@login_required
def admin_create_doctor():
    if current_user.role != 'admin': return redirect(url_for('main.index'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if db.session.scalar(sa.select(User).where(User.username == username)):
        flash('Tên đăng nhập đã tồn tại!', 'error')
    elif db.session.scalar(sa.select(User).where(User.email == email)):
        flash('Email đã được sử dụng!', 'error')
    else:
        new_doc = User(username=username, email=email, role='doctor')
        new_doc.set_password(password)
        db.session.add(new_doc)
        db.session.commit()
        flash(f'Đã tạo tài khoản Bác sĩ: {username}', 'success')
        
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin': return redirect(url_for('main.index'))
    
    user = db.session.get(User, user_id)
    if user and user.role != 'admin':
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa tài khoản: {user.username}', 'success')
        
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/change_password/<int:user_id>', methods=['POST'])
@login_required
def admin_change_password(user_id):
    if current_user.role != 'admin': return redirect(url_for('main.index'))
    
    user = db.session.get(User, user_id)
    new_password = request.form.get('new_password')
    
    if user and new_password:
        user.set_password(new_password)
        db.session.commit()
        flash(f'Đã cấp lại mật khẩu mới cho: {user.username}', 'success')
        
    return redirect(url_for('main.admin_dashboard'))

# --- TÍNH NĂNG NÂNG CAO CHO BÁC SĨ & PHÒNG THUỐC ---

@bp.route('/doctor/create_offline', methods=['GET', 'POST'])
@login_required
def create_offline():
    if current_user.role != 'doctor':
        flash('Chỉ bác sĩ mới có quyền tạo lịch trực tiếp.', 'error')
        return redirect(url_for('main.index'))
    
    form = OfflineAppointmentForm()
    
    if form.validate_on_submit():
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()
        apt = Appointment(
            appointment_date=form.date.data,
            appointment_time=time_obj,
            notes=f"[KHÁCH TRỰC TIẾP] Tên: {form.patient_name.data} - SĐT: {form.phone.data}\nTriệu chứng: {form.notes.data}",
            doctor_id=current_user.id,
            status='Confirmed' 
        )
        db.session.add(apt)
        db.session.commit()
        flash(f'Đã tạo lịch khám trực tiếp cho bệnh nhân {form.patient_name.data}', 'success')
        return redirect(url_for('main.doctor_dashboard'))
        
    return render_template('create_offline.html', title='Tạo lịch trực tiếp', form=form)

@bp.route('/pharmacy/dashboard')
@login_required
def pharmacy_dashboard():
    query = sa.select(MedicalRecord).order_by(MedicalRecord.timestamp.desc())
    records = db.session.scalars(query).all()
    return render_template('pharmacy_dashboard.html', title='Quầy thuốc Tony', records=records)