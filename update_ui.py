import os

BASE_DIR = r"d:\online-shop-django-project-main-copy\accounts\templates\accounts"

templates = {
    r"profile\manager_edit_profil.html": """{% extends "dashboard/home/dashboard.html" %}
{% load crispy_forms_tags %}
{% block content %}
<div class="container d-flex justify-content-center mt-5 mb-5">
    <div class="card border-0 shadow-sm rounded-4" style="width: 100%; max-width: 500px;">
        <div class="card-body p-4 p-md-5">
            <div class="text-center mb-4">
                <div class="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 60px; height: 60px;">
                    <i class="bi bi-pencil-square fs-2"></i>
                </div>
                <h4 class="fw-bold text-dark">แก้ไขข้อมูลผู้ใช้งาน</h4>
            </div>
            <form method="post" enctype="multipart/form-data">
                {% csrf_token %}
                {{ form|crispy }}
                
                <div class="d-flex justify-content-between mt-5">
                    <a href="{% url 'accounts:manage_user'%}" class="btn btn-light rounded-pill px-4 fw-medium text-secondary">ย้อนกลับ</a>
                    <button type="submit" class="btn btn-primary rounded-pill px-4 fw-medium shadow-sm" onclick="this.disabled=true; this.innerHTML='<span class=\\'spinner-border spinner-border-sm me-2\\'></span>กำลังบันทึก...'; this.form.submit();">บันทึกข้อมูล</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}""",
    r"management\update_user.html": """{% extends "dashboard/home/dashboard.html" %}
{% block content %}
<div class="container mt-4 mb-5 d-flex justify-content-center">
    <div class="card border-0 shadow-sm rounded-4" style="width: 100%; max-width: 700px;">
        <div class="card-body p-4 p-md-5">
            <div class="text-center mb-4">
                <div class="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 60px; height: 60px;">
                    <i class="bi bi-person-lines-fill fs-2"></i>
                </div>
                <h4 class="fw-bold text-dark">แก้ไขสิทธิ์และข้อมูลสมาชิก</h4>
            </div>

            <form action="" method="POST">
                {% csrf_token %}
                {{ form.non_field_errors }}

                <div class="row g-3 mb-4">
                    <div class="col-md-3">
                        <label class="form-label fw-bold text-secondary small">คำนำหน้า</label>
                        <select name="{{ form.perfix.name }}" required class="form-select border-0 bg-light">
                            {% for value, display_name in form.perfix.field.choices %}
                                <option value="{{ value }}" {% if form.perfix.value == value %}selected{% endif %}>{{ display_name }}</option>
                            {% endfor %}
                        </select>
                        <div class="text-danger small mt-1">{{ form.form.perfix.name.errors }}</div>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label fw-bold text-secondary small">ชื่อ</label>
                        <input type="text" value="{{ my.first_name }}" name="first_name" class="form-control border-0 bg-light" required>
                        <div class="text-danger small mt-1">{{ form.first_name.errors }}</div>
                    </div>
                    <div class="col-md-5">
                        <label class="form-label fw-bold text-secondary small">นามสกุล</label>
                        <input type="text" value="{{ my.last_name }}" name="last_name" class="form-control border-0 bg-light" required>
                        <div class="text-danger small mt-1">{{ form.last_name.errors }}</div>
                    </div>
                </div>

                <div class="mb-4">
                    <label for="id_username" class="form-label fw-bold text-secondary small">Username</label>
                    <input type="text" value="{{ my.username }}" name="username" class="form-control border-0 bg-light" required id="id_username">
                    <div class="text-danger small mt-1">{{ form.username.errors }}</div>
                </div>

                <div class="row g-3 mb-4">
                    <div class="col-md-6">
                        <label class="form-label fw-bold text-secondary small">รหัสผ่านใหม่ (ปล่อยว่างถ้าไม่เปลี่ยน)</label>
                        <input type="password" name="password1" class="form-control border-0 bg-light" placeholder="••••••••">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold text-secondary small">ยืนยันรหัสผ่านใหม่</label>
                        <input type="password" name="password2" class="form-control border-0 bg-light" placeholder="••••••••">
                    </div>
                </div>

                <div class="mb-4">
                    <label for="id_email" class="form-label fw-bold text-secondary small">Email</label>
                    <input type="email" value="{{ my.email }}" name="email" class="form-control border-0 bg-light" required id="id_email">
                    <div class="text-danger small mt-1">{{ form.email.errors }}</div>
                </div>

                <hr class="text-secondary opacity-25 my-4">
                <h6 class="fw-bold text-dark mb-3"><i class="bi bi-shield-lock me-2"></i>กำหนดสิทธิ์การใช้งานระบบ</h6>
                
                <div class="row g-3 mb-4">
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" name="is_general" id="id_is_general" {% if my.is_general %}checked{% endif %}>
                            <label class="form-check-label" for="id_is_general">ผู้ใช้งานทั่วไป</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" name="is_executive" id="id_is_executive" {% if my.is_executive %}checked{% endif %}>
                            <label class="form-check-label" for="id_is_executive">ผู้บริหาร</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" name="is_manager" id="id_is_manager" {% if my.is_manager %}checked{% endif %}>
                            <label class="form-check-label text-primary fw-medium" for="id_is_manager">ผู้มีสิทธิอนุมัติ</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" name="is_warehouse_manager" id="id_is_warehouse_manager" {% if my.is_warehouse_manager %}checked{% endif %}>
                            <label class="form-check-label text-warning fw-medium" for="id_is_warehouse_manager">ผู้จัดการคลัง</label>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" role="switch" name="is_admin" id="id_is_admin" {% if my.is_admin %}checked{% endif %}>
                            <label class="form-check-label text-danger fw-bold" for="id_is_admin">แอดมิน</label>
                        </div>
                    </div>
                </div>

                <div class="d-flex justify-content-center gap-3 mt-5">
                    <a href="{% url 'accounts:manage_user' %}" class="btn btn-light rounded-pill px-5 fw-medium text-secondary shadow-sm">ย้อนกลับ</a>
                    <button type="submit" class="btn btn-primary rounded-pill px-5 fw-medium shadow-sm">บันทึกการแก้ไข</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}""",
    r"management\profile_users.html": """{% extends "dashboard/home/dashboard.html" %}
{% load crispy_forms_tags %}
{% block content %}
<div class="container mt-4 mb-5">
    {% if obj == 1 %}
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white">
                <div class="card-body p-0">
                    <div class="row g-0">
                        <!-- Left Sidebar (Avatar) -->
                        <div class="col-md-4 bg-light border-end d-flex flex-column align-items-center justify-content-center p-5 text-center">
                            <div class="mb-4" style="width: 200px; height: 200px; border-radius: 50%; overflow: hidden; background-color: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: flex; align-items: center; justify-content: center;">
                                {% if user.profile.img.url and user.profile.img.url != "" %}
                                    <img src="{{ user.profile.img.url }}" style="width: 100%; height: 100%; object-fit: cover;" alt="Profile Picture">
                                {% else %}
                                    <i class="bi bi-person-fill text-secondary" style="font-size: 100px;"></i>
                                {% endif %}
                            </div>
                            <h5 class="fw-bold text-dark mb-1">{{ user.get_full_name }}</h5>
                            <p class="text-muted mb-3">@{{ user.username }}</p>
                            
                            <div class="d-inline-flex px-3 py-2 rounded-pill bg-white shadow-sm mb-2 border">
                                {% if line_user_exists %}
                                    <i class="bi bi-line text-success me-2"></i> <span class="fw-medium text-success">เชื่อมต่อ Line แล้ว</span>
                                {% else %}
                                    <i class="bi bi-line text-muted me-2 opacity-50"></i> <span class="text-muted">ยังไม่เชื่อมต่อ Line</span>
                                {% endif %}
                            </div>
                        </div>
                        
                        <!-- Right Side (Info) -->
                        <div class="col-md-8 p-5">
                            
                            <div class="d-flex justify-content-between align-items-center mb-4">
                                <h5 class="fw-bold text-primary mb-0"><i class="bi bi-person-vcard me-2"></i>ข้อมูลผู้ใช้งาน</h5>
                                {% if user.is_general and user.is_manager and user.is_admin %}
                                    <span class="badge bg-success bg-opacity-10 text-success rounded-pill px-3 py-2 border border-success border-opacity-25">สิทธิ์ทั้งหมด</span>
                                {% elif user.is_admin %}
                                    <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill px-3 py-2 border border-danger border-opacity-25">แอดมิน</span>
                                {% else %}
                                    <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill px-3 py-2 border border-primary border-opacity-25">ผู้ใช้งานทั่วไป</span>
                                {% endif %}
                            </div>

                            <div class="row g-4 mb-4">
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">กลุ่มงาน</div>
                                    <div class="text-dark fw-medium">{{ profile.workgroup|default:"-" }}</div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">ตำแหน่ง</div>
                                    <div class="text-dark fw-medium">{{ profile.position|default:"-" }}</div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">อีเมล</div>
                                    <div class="text-dark fw-medium">{{ user.email|default:"-" }}</div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">เบอร์โทรศัพท์</div>
                                    <div class="text-dark fw-medium">{{ profile.phone|default:"-" }}</div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">เพศ</div>
                                    <div class="text-dark fw-medium">{{ profile.gender|default:"-" }}</div>
                                </div>
                            </div>
                            
                            <hr class="text-secondary opacity-25 mb-4">
                            
                            <h6 class="fw-bold text-secondary mb-3"><i class="bi bi-clock-history me-2"></i>ประวัติการเข้าใช้งาน</h6>
                            <div class="row g-4">
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">สร้างบัญชีเมื่อ</div>
                                    <div class="text-dark">{{ user.date_joined|date:"d M Y เวลา H:i น." }}</div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="text-muted small fw-bold text-uppercase tracking-wide mb-1">เข้าสู่ระบบล่าสุด</div>
                                    <div class="text-dark">{{ user.last_login|date:"d M Y เวลา H:i น." }}</div>
                                </div>
                            </div>

                            <div class="mt-5 text-end">
                                <a href="javascript:history.back()" class="btn btn-light rounded-pill px-4 fw-medium text-secondary border shadow-sm">ย้อนกลับ</a>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% else %}
    <div class="d-flex align-items-center justify-content-center mt-5">
        <div class="text-center p-5 bg-white rounded-4 shadow-sm">
            <i class="bi bi-person-x text-muted" style="font-size: 60px;"></i>
            <h5 class="mt-3 text-dark fw-bold">ไม่พบข้อมูล</h5>
            <p class="text-muted">ไม่มีข้อมูลผู้ใช้งานสำหรับ {{ profile }}</p>
            <a href="javascript:history.back()" class="btn btn-light rounded-pill px-4 mt-3">ย้อนกลับ</a>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}"""
}

for rel_path, content in templates.items():
    full_path = os.path.join(BASE_DIR, rel_path)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {full_path}")
