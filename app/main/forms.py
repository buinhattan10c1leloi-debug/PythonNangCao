from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
import sqlalchemy as sa
from app import db
from app.models import User

class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError(_('Please use a different username.'))

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Submit'))

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

# ====================================================================
# CÁC FORM CHO HỆ THỐNG BỆNH VIỆN
# ====================================================================

class AppointmentForm(FlaskForm):
    doctor = SelectField(_l('Chọn Bác sĩ'), coerce=int, validators=[DataRequired()])
    date = DateField(_l('Ngày khám'), format='%Y-%m-%d', validators=[DataRequired()])
    time = SelectField(_l('Khung giờ'), choices=[
        ('08:00', '08:00'), ('09:00', '09:00'), ('10:00', '10:00'),
        ('14:00', '14:00'), ('15:00', '15:00'), ('16:00', '16:00')
    ], validators=[DataRequired()])
    notes = TextAreaField(_l('Triệu chứng/Ghi chú'), validators=[Length(min=0, max=500)])
    submit = SubmitField(_l('Xác nhận đặt lịch'))

class MedicalRecordForm(FlaskForm):
    diagnosis = TextAreaField(_l('Chẩn đoán bệnh'), validators=[DataRequired()])
    prescription = TextAreaField(_l('Đơn thuốc & Liều dùng'), validators=[DataRequired()])
    doctor_advice = TextAreaField(_l('Lời khuyên bác sĩ'))
    submit = SubmitField(_l('Hoàn tất khám & Lưu hồ sơ'))