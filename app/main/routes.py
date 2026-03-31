from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, \
    MessageForm, AppointmentForm, MedicalRecordForm
from app.models import User, Post, Message, Notification, Appointment, MedicalRecord
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

    form = MedicalRecordForm()
    if form.validate_on_submit():
        record = MedicalRecord(
            diagnosis=form.diagnosis.data,
            prescription=form.prescription.data,
            doctor_advice=form.doctor_advice.data,
            appointment_id=apt.id
        )
        apt.status = 'Completed'
        db.session.add(record)
        db.session.commit()
        flash(_('Đã hoàn tất khám bệnh.'))
        return redirect(url_for('main.doctor_dashboard'))
    return render_template('examine.html', title=_('Khám bệnh'), form=form, apt=apt)