# scheduler/views.py
from django.shortcuts import render
from django.http import HttpResponse
from .scheduler_logic2 import generate_shift_schedule

def parse_fixed_shifts(fixed_shifts_str_list):
    """
    Chuyển đổi danh sách chuỗi ca cố định thành dạng dictionary.
    Ví dụ: ["(ID1,0,s)", "(ID2,0,c)", "(ID3,0,d)"] -> {0: {'ID1': 's', 'ID2': 'c', 'ID3': 'd'}}
    """
    fixed_shifts = {}
    for entry in fixed_shifts_str_list:
        entry = entry.strip().strip("()")
        if entry:
            emp_id, day, shift = entry.split(",")
            day = int(day)
            if day not in fixed_shifts:
                fixed_shifts[day] = {}
            fixed_shifts[day][emp_id] = shift
    return fixed_shifts

def index(request):
    if request.method == 'POST':
        # Nhận dữ liệu từ biểu mẫu
        year = int(request.POST['year'])
        month = int(request.POST['month'])

        employees = {}
        i = 1
        while f'id{i}' in request.POST and f'name{i}' in request.POST:
            employees[request.POST[f'id{i}']] = request.POST[f'name{i}']
            i += 1

        # Xử lý chuỗi cho ca cố định
        fixed_shifts_str_list = request.POST.getlist('fixed_shift')
        fixed_shifts = parse_fixed_shifts(fixed_shifts_str_list)

        # Tạo lịch trực
        html_result, note_fixed_shifts = generate_shift_schedule(year, month, employees, fixed_shifts)

        return render(request, 'scheduler/result.html', {'result': html_result, 'notes': note_fixed_shifts})

    return render(request, 'scheduler/index.html')
