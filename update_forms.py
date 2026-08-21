import os

dirs_to_search = [
    r'd:\online-shop-django-project-main-copy\dashboard\templates\dashboard\home',
    r'd:\online-shop-django-project-main-copy\dashboard\templates\dashboard\reports',
    r'd:\online-shop-django-project-main-copy\dashboard\templates\dashboard\orders_and_stock'
]

for d in dirs_to_search:
    for root, _, files in os.walk(d):
        for file in files:
            if not file.endswith('.html') or 'copy' in file: continue
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            orig = content
            
            # Replace form classes
            content = content.replace('class="row gy-2 gx-3 align-items-center justify-content-end mb-4"', 'class="d-flex flex-wrap gap-2 align-items-center justify-content-end mb-4 w-100"')
            content = content.replace('class="row gy-2 gx-3 align-items-center justify-content-end"', 'class="d-flex flex-wrap gap-2 align-items-center justify-content-end w-100"')
            content = content.replace('class="row gy-2 gx-3 align-items-center mb-4"', 'class="d-flex flex-wrap gap-2 align-items-center mb-4 w-100"')
            
            # Replace selects
            content = content.replace('class="form-select"', 'class="form-select shadow-sm border-0" style="width: auto; border-radius: 20px;"')
            
            # Replace labels
            content = content.replace('class="form-label"', 'class="form-label mb-0 fw-semibold text-secondary"')
            
            # Replace buttons
            content = content.replace('<button type="submit" class="btn btn-primary">ค้นหา</button>', '<button type="submit" class="btn btn-primary shadow-sm rounded-pill px-4 fw-bold" style="background: linear-gradient(135deg, #1a73e8 0%, #1e88e5 100%); border: none;"><i class="bi bi-funnel-fill"></i> ค้นหา</button>')
            
            content = content.replace('class="btn btn-secondary"', 'class="btn btn-light shadow-sm rounded-pill px-4 fw-bold bg-white text-secondary" style="border: none;"')
            
            if orig != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Updated {filepath}')
