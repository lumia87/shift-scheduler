#Update: 19.6.2024 (chatGPT)

from fpdf import FPDF
from datetime import datetime, timedelta
import os, pulp
import calendar
def generate_shift_schedule(year, month, employees, fixed_shifts):
    # Tạo danh sách các ngày trong tháng
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    days = [(start_date + timedelta(days=i)).strftime('%d') for i in range((end_date - start_date).days + 1)]

    # Danh sách ca làm việc
    shifts = ['s', 'c', 'd', 'x']  # Sáng, Chiều, Đêm, Nghỉ

    # Ghi chú cho các ngày cố định
    note_fixed_shifts = "*GHI CHÚ: CA TRỰC CỐ ĐỊNH:\n"
    for fixed_date, shift_info in fixed_shifts.items():
        note_fixed_shifts += "  - Ngày {}: {}\n".format(datetime(year, month, fixed_date).strftime('%d/%m/%Y'), str(shift_info))
    
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
                prob += shift_vars[e][days[fixed_date-1]][day_shift] == 1 # fixed_date-1 để chuyển từ 1-based index sang 0-based index cho danh sách days

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

    # Tạo bảng kết quả dưới dạng HTML
    html_result = "<tr><th>STT</th><th>MÃ NV</th><th>HỌ TÊN</th>"
    for day in days:
        html_result += f"<th>{day}</th>"
    html_result += "<th>T.S</th><th>T.C</th><th>T.Đ</th><th>T.Ca</th></tr>"

    for idx, e in enumerate(employees.keys(), start=1):
        row = f"<tr><td>{idx}</td><td>{e}</td><td>{employees[e]}</td>"
        num_s = int(pulp.value(num_shifts[e]['s']))
        num_c = int(pulp.value(num_shifts[e]['c']))
        num_d = int(pulp.value(num_shifts[e]['d']))
        total_shift = total_shifts_employee[e]
        for day in days:
            assigned_shift = 'x'  # Mặc định là ngày nghỉ
            shift_class = 'shift-x'
            for shift in shifts:
                if pulp.value(shift_vars[e][day][shift]) == 1:
                    assigned_shift = shift.upper()  # Chuyển đổi sang chữ hoa
                    shift_class = f"shift-{shift}"
            row += f"<td class='{shift_class}'>{assigned_shift}</td>"
        row += f"<td>{num_s}</td><td>{num_c}</td><td>{num_d}</td><td>{total_shift}</td></tr>"
        html_result += row

    return html_result, note_fixed_shifts
