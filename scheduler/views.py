# scheduler/views.py
from django.http import HttpResponse
from .scheduler_logic import generate_shift_schedule # Assuming main_function is the entry point of your script
from .scheduler_logic import PDF

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
    # Tạo và lưu file PDF từ chuỗi Markdown
    pdf = PDF(year, month)
    pdf.add_page(orientation='L', format='A4')
    pdf.chapter_body(result)
    pdf.chapter_title(note)

    # Tạo tên file PDF dựa trên tháng và năm
    pdf_file_path = f"Lich_lam_viec_thang_{month}_{year}.pdf"

    pdf.output(pdf_file_path)
    print(f"Đã lưu file PDF: {pdf_file_path}")
    return HttpResponse(result)