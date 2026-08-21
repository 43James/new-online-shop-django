import os

filepath = r"d:\online-shop-django-project-main-copy\accounts\templates\accounts\management\manage_user.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We will replace the whole table section.
# The table section starts from <div class="table-responsive"> and ends at </table>

new_table = """<div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
    <div class="table-responsive">
        <table class="table table-hover modern-table align-middle text-nowrap mb-0">
            <thead class="table-light text-secondary">
                <tr>
                    <th scope="col" class="text-center" style="width: 50px;">#</th>
                    <th scope="col">ผู้ใช้งาน</th>
                    <th scope="col">กลุ่มงาน</th>
                    <th scope="col">ตำแหน่ง</th>
                    <th scope="col">สถานะ</th>
                    <th scope="col" class="text-center">Line</th>
                    <th scope="col" class="text-center">จัดการ</th>
                </tr>
            </thead>
            <tbody>
                {% for l in my %}
                <tr>
                    <td class="text-center text-muted">{{ forloop.counter0|add:my.start_index }}</td>
                    
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="me-3" style="width: 40px; height: 40px; border-radius: 50%; overflow: hidden; display: flex; align-items: center; justify-content: center; background-color: #f8f9fa;">
                                {% if l.profile.image %}
                                    {{ l.profile.image }}
                                {% else %}
                                    <i class="bi bi-person-circle fs-3 text-secondary"></i>
                                {% endif %}
                            </div>
                            <div>
                                <div class="fw-bold text-dark">{{ l.get_full_name }}</div>
                                <div class="text-muted small">@{{ l.username }} | {{ l.email }}</div>
                            </div>
                        </div>
                    </td>

                    <td><span class="text-secondary">{{ l.profile.workgroup }}</span></td>
                    <td><span class="text-secondary">{{ l.profile.position }}</span></td>
                    
                    <td>
                        {% if l.is_general and l.is_warehouse_manager and l.is_admin %}
                        <span class="badge bg-success bg-opacity-10 text-success rounded-pill px-3">ผู้เข้าถึงสิทธิ์ทั้งหมด</span>
                        {% elif l.is_general and l.is_manager and l.is_warehouse_manager %}
                        <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill px-3">ผู้จัดการคลัง</span>
                        {% elif l.is_general and l.is_manager %}
                        <span class="badge bg-info bg-opacity-10 text-info rounded-pill px-3">ผู้มีสิทธิอนุมัติ</span>
                        {% elif l.is_general and l.is_executive %}
                        <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill px-3">ผู้บริหาร</span>
                        {% elif l.is_manager and l.is_admin %}
                        <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill px-3">แอดมิน</span>
                        {% elif l.is_warehouse_manager and l.is_admin %}
                        <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill px-3">แอดมิน</span>
                        {% elif l.is_general %}
                        <span class="badge bg-success bg-opacity-10 text-success rounded-pill px-3">ผู้ใช้งาน</span>
                        {% elif l.is_executive %}
                        <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill px-3">ผู้บริหาร</span>
                        {% elif l.is_manager %}
                        <span class="badge bg-info bg-opacity-10 text-info rounded-pill px-3">ผู้มีสิทธิอนุมัติ</span>
                        {% elif l.is_admin %}
                        <span class="badge bg-danger bg-opacity-10 text-danger rounded-pill px-3">แอดมิน</span>
                        {% else %}
                        <span class="badge bg-warning bg-opacity-10 text-warning rounded-pill px-3">ไม่มีสถานะ</span>
                        {% endif %}
                    </td>

                    <td class="text-center">
                        {% if l.userline_set.exists %}
                        <i class="bi bi-check-circle-fill text-success fs-5"></i>
                        {% else %}
                        <i class="bi bi-x-circle-fill text-danger fs-5"></i>
                        {% endif %}
                    </td>

                    <td class="text-center">
                        <div class="d-flex justify-content-center gap-2">
                            <a href="{% url 'accounts:profile_users' l.username %}" class="btn btn-sm btn-light text-primary rounded-circle shadow-sm" title="ดูข้อมูล">
                                <i class="bi bi-eye"></i>
                            </a>
                            <a href="{% url 'accounts:manager_edit_profile' l.id %}" class="btn btn-sm btn-light text-warning rounded-circle shadow-sm" title="แก้ไขโปรไฟล์">
                                <i class="bi bi-person-badge"></i>
                            </a>
                            <a href="{% url 'accounts:update_user' l.id %}" class="btn btn-sm btn-light text-info rounded-circle shadow-sm" title="ตั้งค่าสิทธิ์">
                                <i class="bi bi-pencil-square"></i>
                            </a>
                            <button class="btn btn-sm btn-light text-danger rounded-circle shadow-sm" data-bs-toggle="modal" data-bs-target="#exampleModal{{l.id}}" title="ลบผู้ใช้งาน">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>

                        <!-- Modal -->
                        <div class="modal fade" id="exampleModal{{l.id}}" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                            <div class="modal-dialog modal-dialog-centered">
                                <div class="modal-content rounded-4 border-0 shadow">
                                    <div class="modal-header border-0 pb-0">
                                        <h5 class="modal-title fw-bold text-danger" id="exampleModalLabel"><i class="bi bi-exclamation-triangle-fill me-2"></i>ยืนยันการลบ</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                    </div>
                                    <div class="modal-body text-center pt-4 pb-4">
                                        <p class="mb-0 fs-5">ท่านต้องการลบผู้ใช้งาน <strong class="text-dark">{{l.username}}</strong> ใช่หรือไม่?</p>
                                    </div>
                                    <div class="modal-footer border-0 pt-0 justify-content-center gap-2">
                                        <button type="button" class="btn btn-light rounded-pill px-4 fw-medium" data-bs-dismiss="modal">ยกเลิก</button>
                                        <a type="button" href="{% url 'accounts:delete_user' l.id %}" class="btn btn-danger rounded-pill px-4 fw-medium">ยืนยันลบ</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>"""

import re
# Find the start and end of the table
start_idx = content.find('<div class="table-responsive">')
end_idx = content.find('</table>') + len('</table>')

if start_idx != -1 and end_idx != -1:
    # Also include the surrounding <div class="col"> if present to replace it cleanly
    div_col_idx = content.rfind('<div class="col" >', 0, start_idx)
    if div_col_idx != -1:
        start_idx = div_col_idx
    
    new_content = content[:start_idx] + new_table + content[end_idx:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Table successfully updated.")
else:
    print("Could not find table boundaries.")
