# scheduler/views.py
from django.shortcuts import render
from django.http import HttpResponse
from .scheduler_logic3 import generate_shift_schedule

def parse_fixed_shifts(fixed_shifts_str_list):
    """
    Chuyển đổi danh sách chuỗi ca cố định thành dạng dictionary.
    Ví dụ: ["1,g1,s; 1,g2,c; 1,g3,d"] -> {0: {0: 's', 1: 'c', 2: 'd'}}
    """
    fixed_shifts = {}
    fixed_shifts_list=fixed_shifts_str_list[0].split(";")
    for entry in fixed_shifts_list:
        entry = entry.strip()
        if entry:
            day, gr_id, shift = entry.split(",")
            day = int(day)
            gr_id =int(gr_id[1:])
            if shift:  # Chỉ thêm nếu shift không rỗng
                if day not in fixed_shifts:
                    fixed_shifts[day] = {}
                fixed_shifts[day][gr_id] = shift
    return fixed_shifts

def index(request):
    if request.method == 'POST':
        # Nhận dữ liệu từ biểu mẫu
        year = int(request.POST['year'])
        month = int(request.POST['month'])

        teams = []
        i = 1
        while f'team{i}' in request.POST:
            t = request.POST[f'team{i}'].split(",")
            teams.append(t)
            i += 1
  

        # Xử lý chuỗi cho ca cố định
        fixed_shifts_str_list = request.POST.getlist('fixed_shift')
        fixed_shifts = parse_fixed_shifts(fixed_shifts_str_list)

        # Tạo lịch trực
        html_result, note_fixed_shifts = generate_shift_schedule(year, month, teams, fixed_shifts)

        return render(request, 'scheduler/result.html', {
            'result': html_result, 
            'notes': note_fixed_shifts,
            'year': year,
            'month': month
        })

    return render(request, 'scheduler/index.html')
