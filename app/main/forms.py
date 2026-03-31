from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User

# --- FORM ĐĂNG NHẬP ---
class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

# --- FORM ĐĂNG KÝ ---
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
            raise ValidationError(_('Tên đăng nhập này đã có người dùng.'))

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError(_('Email này đã được đăng ký.'))

# --- FORM CHỈNH SỬA HỒ SƠ ---
class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == self.username.data))
            if user is not None:
                raise ValidationError(_('Tên này đã tồn tại.'))

# --- CÁC FORM HỖ TRỢ KHÁC ---
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    """Đã bỏ phần đăng hình ảnh - Chỉ còn nhập nội dung văn bản"""
    post = TextAreaField(_l('Nội dung bài đăng'), validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Đăng bài'))

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        from flask import request
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

# --- FORM ĐẶT LỊCH (BỆNH NHÂN) ---
class AppointmentForm(FlaskForm):
    doctor = SelectField('Chọn Bác sĩ', coerce=int, validators=[DataRequired()])
    date = DateField('Ngày khám', format='%Y-%m-%d', validators=[DataRequired()])
    time = SelectField('Khung giờ', choices=[
        ('08:00', '08:00'), ('09:00', '09:00'), ('10:00', '10:00'),
        ('14:00', '14:00'), ('15:00', '15:00'), ('16:00', '16:00')
    ], validators=[DataRequired()])
    notes = TextAreaField('Ghi chú triệu chứng')
    submit = SubmitField('Xác nhận đặt lịch')

# --- FORM KHÁM BỆNH CŨ ---
class MedicalRecordForm(FlaskForm):
    diagnosis = TextAreaField('Chẩn đoán', validators=[DataRequired()])
    prescription = TextAreaField('Đơn thuốc', validators=[DataRequired()])
    doctor_advice = TextAreaField('Lời khuyên')
    submit = SubmitField('Hoàn tất khám')

# --- CÁC FORM CHO BÁC SĨ & PHÒNG THUỐC (GIỮ NGUYÊN ĐỂ TRÁNH LỖI IMPORT) ---

class OfflineAppointmentForm(FlaskForm):
    """Dùng khi bác sĩ tự tạo lịch hẹn cho bệnh nhân vãng lai"""
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
    medicine_details = TextAreaField(_l('Đơn thuốc chi tiết'), 
                                   validators=[DataRequired()])
    doctor_advice = TextAreaField(_l('Lời khuyên của bác sĩ'))
    estimated_cost = StringField(_l('Ghi chú chi phí (nếu có)'))
    submit = SubmitField(_l('Hoàn tất & Chuyển phòng thuốc'))