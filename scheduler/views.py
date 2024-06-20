# scheduler/views.py
from django.http import HttpResponse
from .scheduler_logic2 import generate_shift_schedule # Assuming main_function is the entry point of your script

def index(request):
    # Dữ liệu đầu vào
    year = 2024
    month = 7
    employees = {
        'ID1': 'lê văn thông',
        'ID2': 'ngô văn dũng',
        'ID3': 'nguyễn văn đài',
        'ID4': 'trần thiện đức',
        'ID5': 'nguyễn triệu hải'
    }
    fixed_shifts = {
        0: {'ID1': 's', 'ID2': 'c', 'ID3': 'd'},
        15: {'ID1': 'c', 'ID2': 'd'}
    }

    # Tạo lịch trực
    markdown_result, note_fixed_shifts = generate_shift_schedule(year, month, employees, fixed_shifts)

    # Gọi hàm để giải quyết bài toán và tạo dữ liệu kết quả

    result, note = generate_shift_schedule(year, month, employees, fixed_shifts)

    print(f"Đã xuất file")
    return HttpResponse(result)