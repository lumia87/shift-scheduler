#Update: 19.6.2024 (chatGPT)

from fpdf import FPDF
from datetime import datetime, timedelta
import pulp
import calendar

def generate_shift_schedule(year, month, employees, fixed_shifts):
    # Tạo danh sách các ngày trong tháng
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    days = [(start_date + timedelta(days=i)).strftime('%d') for i in range((end_date - start_date).days + 1)]

    # Danh sách ca làm việc
    shifts = ['s', 'c', 'd', 'x']  # Sáng, Chiều, Đêm, Nghỉ

    # Ghi chú cho các ngày cố định
    note_fixed_shifts = "*Ghi chú: Ca trực cố định:\n"
    for fixed_date, shift_info in fixed_shifts.items():
        note_fixed_shifts += "  - Ngày {}: {}\n".format(datetime(year, month, fixed_date+1).strftime('%d/%m/%Y'), str(shift_info))
    
    # Số lượng ca sáng, chiều, đêm của từng nhân viên (quá khứ) để cân bằng giữa các nhân viên
    shift_balance = {e: [0, 0, 0] for e in employees}

    # Khởi tạo bài toán tối ưu
    prob = pulp.LpProblem("Employee_Shift_Scheduling", pulp.LpMinimize)

    # Tạo biến quyết định
    shift_vars = pulp.LpVariable.dicts("Shift", (employees.keys(), days, shifts), 0, 1, pulp.LpBinary)

    # Ràng buộc: mỗi ca sáng, chiều, đêm có một người làm
    for day in days:
        for shift in ['s', 'c', 'd']:
            prob += pulp.lpSum(shift_vars[e][day][shift] for e in employees.keys()) == 1

    # Ràng buộc: mỗi nhân viên chỉ làm một ca mỗi ngày
    for e in employees.keys():
        for day in days:
            prob += pulp.lpSum(shift_vars[e][day][shift] for shift in shifts) <= 1

    # Ràng buộc không được đi ca đêm hôm trước sau đó đi ca sáng hôm sau
    for e in employees.keys():
        for i in range(len(days) - 1):
            prob += shift_vars[e][days[i]]['d'] + shift_vars[e][days[i + 1]]['s'] <= 1

    # Ràng buộc một tháng có ít nhất 4 ngày nghỉ
    for e in employees.keys():
        prob += pulp.lpSum(shift_vars[e][day]['x'] for day in days) >= 4

    # Ràng buộc cho ca trực của các ngày cố định
    for fixed_date, shift_info in fixed_shifts.items():
        for e, day_shift in shift_info.items():
            if day_shift in shifts:
                prob += shift_vars[e][days[fixed_date]][day_shift] == 1

    # Tạo các biến để đếm số ca sáng, chiều, đêm cho mỗi nhân viên
    num_shifts = {e: {shift: pulp.lpSum(shift_vars[e][day][shift] for day in days) for shift in ['s', 'c', 'd']} for e in employees.keys()}

    # Tính tổng số ca sáng, chiều, đêm từ shift_balance
    total_shifts_from_balance = {shift: sum(shift_balance[e][i] for e in employees.keys()) for i, shift in enumerate(['s', 'c', 'd'])}

    # Giải bài toán
    prob.solve()

    # Tính tổng số ca sáng, chiều, đêm của mỗi nhân viên từ các biến tối ưu hóa sau khi giải quyết bài toán
    total_shifts_optimized = {shift: sum(pulp.value(num_shifts[e][shift]) for e in employees.keys()) for shift in ['s', 'c', 'd']}

    # Ràng buộc: số lượng ca sáng, chiều, đêm của mỗi nhân viên cộng với shift_balance là gần bằng nhau với độ lệch tối đa là 1
    average_shifts = {shift: (total_shifts_from_balance[shift] + total_shifts_optimized[shift]) / len(employees) for shift in ['s', 'c', 'd']}
    for e in employees.keys():
        for i, shift in enumerate(['s', 'c', 'd']):
            prob += num_shifts[e][shift] + shift_balance[e][i] >= average_shifts[shift] - 1
            prob += num_shifts[e][shift] + shift_balance[e][i] <= average_shifts[shift] + 1

    # Giải lại bài toán với các ràng buộc mới
    prob.solve()

    # In kết quả giải bài toán ra màn hình
    status = pulp.LpStatus[prob.status]
    print(f"Trạng thái giải bài toán: {status}")
    if status == 'Optimal':
        for e in employees.keys():
            num_s = int(pulp.value(num_shifts[e]['s']))
            num_c = int(pulp.value(num_shifts[e]['c']))
            num_d = int(pulp.value(num_shifts[e]['d']))
            print(f"Nhân viên {employees[e]} ({e}): Số ca sáng = {num_s}, Số ca chiều = {num_c}, Số ca đêm = {num_d}")
    else:
        print("Không tìm được giải pháp tối ưu.")

    # Tính tổng số ca sáng, chiều, đêm của mỗi nhân viên
    total_shifts_employee = {e: sum(pulp.value(num_shifts[e][shift]) for shift in ['s', 'c', 'd']) for e in employees.keys()}

    # Tạo bảng kết quả dưới dạng Markdown
    markdown_result = "| STT | MÃ NV | HỌ TÊN | " + " | ".join(days) + " |T.S|T.C|T.Đ| T.Ca |\n"

    for idx, e in enumerate(employees.keys(), start=1):
        row = f"| {idx} | {e} | {employees[e]} | "
        num_s = int(pulp.value(num_shifts[e]['s']))
        num_c = int(pulp.value(num_shifts[e]['c']))
        num_d = int(pulp.value(num_shifts[e]['d']))
        total_shift = total_shifts_employee[e]
        for day in days:
            assigned_shift = 'x'  # Mặc định là ngày nghỉ
            for shift in shifts:
                if pulp.value(shift_vars[e][day][shift]) == 1:
                    assigned_shift = shift.upper()  # Chuyển đổi sang chữ hoa
            row += f"{assigned_shift} | "
        row += f"{num_s} | {num_c} | {num_d} | {total_shift} |\n"
        markdown_result += row

    return markdown_result, note_fixed_shifts


class PDF(FPDF):
    def __init__(self, year, month):
        super().__init__()
        self.add_font('DejaVuSans', '', 'DejaVuSans.ttf')
        self.month = month

        self.start_date = datetime(year, month, 1)
        self.end_date = datetime(year, month, calendar.monthrange(year, month)[1])

        self.days = [(self.start_date + timedelta(days=i)).strftime('%d') for i in range((self.end_date - self.start_date).days + 1)]

    def header(self):
        self.set_font('DejaVuSans', '', 16)
        self.cell(0, 10, f'BẢNG TRỰC CA THÁNG {self.start_date.strftime("%m/%Y")}', new_x="LMARGIN", new_y="NEXT", align='C')

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVuSans', '', 8)
        self.cell(0, 10, 'Trang %s' % self.page_no(), new_x="LMARGIN", new_y="NEXT", align='C')

    def chapter_title(self, title):
        self.set_font('DejaVuSans', '', 8)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align='L')

    def chapter_body(self, body):
        self.set_font('DejaVuSans', '', 8)
        column_width = self.w / (len(self.days) + 12)  # Số cột + 12 (cột ghi chú, STT và Tong so ca)
        employee_column_width = column_width * 2.5  # Độ rộng cho cột tên nhân viên

        cell_height = 12  # Chiều cao của mỗi ô

        date_objects = [(self.start_date + timedelta(days=i)) for i in range((self.end_date - self.start_date).days + 1)]
        day_names = [date.strftime('%A') for date in date_objects]

        for row_index, row in enumerate(body.splitlines()):
            cells = row.split('|')
            cells = [cell.strip() for cell in cells if cell.strip()]
            for i, cell in enumerate(cells):
                if i == 0:
                    self.set_fill_color(255, 255, 255)
                    self.cell(column_width, cell_height, cell, border=1, fill=True, align='C')
                elif i == 1:
                    self.set_fill_color(255, 255, 255)
                    self.cell(column_width, cell_height, cell, border=1, fill=True, align='C')
                elif i == 2:
                    self.set_fill_color(255, 255, 255)
                    self.cell(employee_column_width, cell_height, cell, border=1, fill=True, align='C')
                elif row_index == 0 and i >= 3 and i - 3 < len(day_names):
                    day_name = day_names[i - 3]
                    if day_name in ('Saturday', 'Sunday'):
                        self.set_fill_color(255, 204, 204)
                    else:
                        self.set_fill_color(255, 255, 255)
                    self.cell(column_width, cell_height, cell, border=1, fill=True, align='C')
                else:
                    if 'S' in cell:
                        self.set_fill_color(255, 255, 102)
                    elif 'C' in cell:
                        self.set_fill_color(153, 204, 255)
                    elif 'D' in cell:
                        self.set_fill_color(255, 153, 153)
                    elif 'Tong' in cell:
                        self.set_fill_color(192, 192, 192)
                    else:
                        self.set_fill_color(255, 255, 255)
                    self.cell(column_width, cell_height, cell, border=1, fill=True, align='C')
            self.ln(cell_height)

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
res, note = generate_shift_schedule(year, month, employees, fixed_shifts)

# Tạo và lưu file PDF từ chuỗi Markdown
pdf = PDF(year, month)
pdf.add_page(orientation='L', format='A4')
pdf.chapter_body(res)
pdf.chapter_title(note)

# Tạo tên file PDF dựa trên tháng và năm
pdf_file_path = f"Lich_lam_viec_thang_{month}_{year}.pdf"

pdf.output(pdf_file_path)
print(f"Đã lưu file PDF: {pdf_file_path}")
