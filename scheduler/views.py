# scheduler/views.py
from django.shortcuts import render
from .scheduler_logic3 import generate_shift_schedule
from django.http import JsonResponse
import json

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
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
        teams = [request.POST.get(f'team{i}').split(',') for i in range(1, 7)]
        
        fixed_shifts_input = request.POST.get('fixed_shift')
        fixed_shifts = {}
        for item in fixed_shifts_input.split(';'):
            day, group, shift = item.split(',')
            day = int(day)
            group = int(group[1:])  # Bỏ "g" ở đầu và chuyển đổi sang số
            if day not in fixed_shifts:
                fixed_shifts[day] = {}
            fixed_shifts[day][group] = shift

        # Gọi hàm generate_shift_schedule và trả về JSON
        result_json = generate_shift_schedule(year, month, teams, fixed_shifts)

        # Parse kết quả JSON sang dictionary
        result = json.loads(result_json)

        # Trả về template với dữ liệu JSON
        return render(request, 'scheduler/result.html', {'json_data': result, 'month':month, 'year':year})    

    return render(request, 'scheduler/index.html')