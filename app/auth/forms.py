from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
# Thêm TextAreaField, SelectField, DateField vào đây
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User

# --- CÁC FORM XÁC THỰC (ĐÃ CÓ) ---

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


# --- CÁC FORM BỔ SUNG CHO BÁC SĨ & PHÒNG THUỐC ---

class OfflineAppointmentForm(FlaskForm):
    """Dùng khi bác sĩ tự tạo lịch hẹn cho bệnh nhân vãng lai (không dùng web)"""
    patient_name = StringField(_l('Tên bệnh nhân'), validators=[DataRequired()])
    phone = StringField(_l('Số điện thoại'), validators=[DataRequired()])
    date = DateField(_l('Ngày khám'), format='%Y-%m-%d', validators=[DataRequired()])
    time = SelectField(_l('Khung giờ'), choices=[
        ('08:00', '08:00'), ('09:00', '09:00'), ('10:00', '10:00'),
        ('14:00', '14:00'), ('15:00', '15:00'), ('16:00', '16:00')
    ], validators=[DataRequired()])
    notes = TextAreaField(_l('Triệu chứng ban đầu'), validators=[Length(min=0, max=500)])
    submit = SubmitField(_l('Xác nhận đặt lịch trực tiếp'))

class PrescriptionForm(FlaskForm):
    """Dùng để bác sĩ kê đơn thuốc và đẩy dữ liệu xuống phòng bán thuốc"""
    diagnosis = TextAreaField(_l('Chẩn đoán bệnh'), validators=[DataRequired()])
    # Danh sách thuốc: Tên thuốc - Số lượng - Cách dùng
    medicine_details = TextAreaField(_l('Đơn thuốc chi tiết'), 
                                   render_kw={"placeholder": "Ví dụ:\n1. Paracetamol 500mg - 10 viên (Sáng 1, Tối 1)\n2. Vitamin C - 5 viên (Sáng 1)"},
                                   validators=[DataRequired()])
    doctor_advice = TextAreaField(_l('Lời khuyên của bác sĩ'))
    # Trường ẩn hoặc ghi chú để phòng thuốc tính tiền
    estimated_cost = StringField(_l('Ghi chú chi phí (nếu có)'))
    submit = SubmitField(_l('Hoàn tất & Chuyển phòng thuốc'))