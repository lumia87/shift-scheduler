from fpdf import FPDF
from datetime import datetime, timedelta
import os, pulp
import calendar

def generate_shift_schedule(year, month, teams, fixed_shifts):

    shifts = ['s', 'c', 'd', 'x']  # Sáng, Chiều, Đêm, Nghỉ
    # Ghi chú cho các ngày cố định
    note_fixed_shifts = "Ghi chú: Ca trực cố định:<br> "
    for fixed_date, shift_info in fixed_shifts.items():
        note_fixed_shifts += "- Ngày {}: {}<br>".format(datetime(year, month, fixed_date).strftime('%d/%m/%Y'), str(shift_info))
    

    # Tạo danh sách các ngày trong tháng 7/2024
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    days = [(start_date + timedelta(days=i)).strftime('%d') for i in range((end_date - start_date).days + 1)]

    # Khởi tạo bài toán tối ưu
    prob = pulp.LpProblem("Team_Shift_Scheduling", pulp.LpMinimize)

    # Tạo biến quyết định
    shift_vars = pulp.LpVariable.dicts("Shift", (range(len(teams)), days, shifts), 0, 1, pulp.LpBinary)

    # Biến để theo dõi ca đêm hôm trước
    previous_night_shift = {g: pulp.LpVariable.dicts(f"PreviousNightShift_{g}", days, 0, 1, pulp.LpBinary) for g in range(len(teams))}

    # Ràng buộc: mỗi ca sáng, chiều, đêm có một nhóm làm
    for day in days:
        for shift in ['s', 'c', 'd']:
            prob += pulp.lpSum(shift_vars[g][day][shift] for g in range(len(teams))) == 1

    # Ràng buộc: mỗi nhóm chỉ làm một ca mỗi ngày
    for g in range(len(teams)):
        for day in days:
            prob += pulp.lpSum(shift_vars[g][day][shift] for shift in shifts) <= 1

    # Ràng buộc không được đi ca đêm hôm trước sau đó đi ca sáng hôm sau
    for g in range(len(teams)):
        for i in range(len(days) - 1):
            prob += shift_vars[g][days[i]]['d'] + shift_vars[g][days[i + 1]]['s'] <= 1 + previous_night_shift[g][days[i]]

    # Ràng buộc một tháng có ít nhất 4 ngày nghỉ
    for g in range(len(teams)):
        prob += pulp.lpSum(shift_vars[g][day]['x'] for day in days) >= 4

    # Ràng buộc cho ca trực của các ngày cố định cho các nhóm
    for fixed_date, shift_info in fixed_shifts.items():
        for g, day_shift in shift_info.items():
            if day_shift in shifts:
                prob += shift_vars[g-1][days[fixed_date-1]][day_shift] == 1

    # Ràng buộc: không làm ca sáng sau khi làm ca đêm hôm trước
    for g in range(len(teams)):
        for day in days:
            prob += shift_vars[g][day]['s'] <= 1 - previous_night_shift[g][day]

    # Tạo các biến để đếm số ca sáng, chiều, đêm cho mỗi nhóm
    num_shifts = {g: {shift: pulp.lpSum(shift_vars[g][day][shift] for day in days) for shift in ['s', 'c', 'd']} for g in range(len(teams))}

    # Tính tổng số ca sáng, chiều, đêm của tất cả nhóm
    total_shifts = {shift: pulp.lpSum(num_shifts[g][shift] for g in range(len(teams))) for shift in ['s', 'c', 'd']}

    # Ràng buộc: số lượng ca sáng, chiều, đêm của mỗi nhóm gần bằng nhau
    average_shifts = {shift: total_shifts[shift] / len(teams) for shift in ['s', 'c', 'd']}
    for g in range(len(teams)):
        for shift in ['s', 'c', 'd']:
            prob += num_shifts[g][shift] >= average_shifts[shift] - 1
            prob += num_shifts[g][shift] <= average_shifts[shift] + 1

    # Giải bài toán
    prob.solve()

    # In kết quả giải bài toán ra màn hình
    status = pulp.LpStatus[prob.status]
    print(f"Trạng thái giải bài toán: {status}")
    if status == 'Optimal':
        for g in range(len(teams)):
            num_s = int(pulp.value(num_shifts[g]['s']))
            num_c = int(pulp.value(num_shifts[g]['c']))
            num_d = int(pulp.value(num_shifts[g]['d']))
            team_members = ', '.join(teams[g])
            print(f"Nhóm {g+1} ({team_members}): Số ca sáng = {num_s}, Số ca chiều = {num_c}, Số ca đêm = {num_d}")
    else:
        print("Không tìm được giải pháp tối ưu.")

    # Tính tổng số ca sáng, chiều, đêm của mỗi nhóm
    total_shifts_team = {g: sum(pulp.value(num_shifts[g][shift]) for shift in ['s', 'c', 'd']) for g in range(len(teams))}

    # Tạo bảng kết quả dưới dạng HTML
    html_result = "<table border='1'><tr><th>STT</th><th>Tên</th>" + "".join(f"<th>{day}</th>" for day in days) + "<th>T.S</th><th>T.C</th><th>T.Đ</th><th>Tổng</th></tr>"

    for idx, g in enumerate(range(len(teams)), start=0):
        for i, e in enumerate(range(len(teams[g])),start=1):
            row = f"<tr><td>{4*idx+i}</td><td>{teams[g][e]}</td>"
            num_s = int(pulp.value(num_shifts[g]['s']))
            num_c = int(pulp.value(num_shifts[g]['c']))
            num_d = int(pulp.value(num_shifts[g]['d']))
            total_shift = total_shifts_team[g]
            for day in days:
                assigned_shift = 'X'  # Mặc định là ngày nghỉ
                shift_class = 'shift-x'
                for shift in shifts:
                    if pulp.value(shift_vars[g][day][shift]) == 1:
                        shift_class = f"shift-{shift}"
                        assigned_shift = shift.upper()  # Chuyển đổi sang chữ hoa

                row += f"<td class='{shift_class}'>{assigned_shift}</td>"
            row += f"<td>{num_s}</td><td>{num_c}</td><td>{num_d}</td><td>{total_shift}</td></tr>"
            html_result += row

    html_result += "</table>"

    # Tạo bảng kết quả dưới dạng HTML
    print(html_result)
    return html_result, note_fixed_shifts        
