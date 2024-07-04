from fpdf import FPDF
from datetime import datetime, timedelta
import os, pulp
import calendar, json

def generate_shift_schedule(year, month, teams, fixed_shifts, max_hours_per_week=40):

    shifts = ['s', 'c', 'd', 'x']  # Sáng, Chiều, Đêm, Nghỉ
    shift_hours = {'s': 7, 'c': 7, 'd': 10, 'x': 0}  # Số giờ làm việc cho mỗi ca
    # max_hours_per_week = 40  # Số giờ làm việc tối đa mỗi tuần

    # Ghi chú cho các ngày cố định
    note_fixed_shifts = "Ghi chú: Ca trực cố định:<br> "
    for fixed_date, shift_info in fixed_shifts.items():
        note_fixed_shifts += "- Ngày {}: {}<br>".format(datetime(year, month, fixed_date).strftime('%d/%m/%Y'), str(shift_info))
    
    # Tạo danh sách các ngày trong tháng mm/yyyy
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    days = [(start_date + timedelta(days=i)).strftime('%d') for i in range((end_date - start_date).days + 1)]

    # Xác định các tuần trong tháng
    weeks = []
    current_week = []
    for day in days:
        date_obj = datetime(year, month, int(day))
        if date_obj.weekday() == 0 and current_week:
            weeks.append(current_week)
            current_week = []
        current_week.append(day)
    if current_week:
        weeks.append(current_week)

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

    # Ràng buộc số giờ làm việc không vượt quá 40 giờ mỗi tuần theo EVN, còn theo luật là 48 giờ.
    for g in range(len(teams)):
        for week in weeks:
            prob += pulp.lpSum(shift_hours[shift] * shift_vars[g][day][shift] for day in week for shift in shifts) <= max_hours_per_week

    # Giải bài toán
    prob.solve()

    # In kết quả giải bài toán ra màn hình
    status = pulp.LpStatus[prob.status]
    
    result = {"year":year, "month":month, "status": pulp.LpStatus[prob.status], "teams": [], "days": days, 'note_fixed_shifts': []}

    if status == 'Optimal':
        for g in range(len(teams)):
            team_info = {
                "members": teams[g],
                "shifts": {"s": int(pulp.value(num_shifts[g]['s'])), "c": int(pulp.value(num_shifts[g]['c'])), "d": int(pulp.value(num_shifts[g]['d']))},
                "total_shift": sum(int(pulp.value(num_shifts[g][shift])) for shift in ['s', 'c', 'd']),
                "days": []
            }
            for day in days:
                assigned_shift = 'x'  # Mặc định là ngày nghỉ
                for shift in shifts:
                    if pulp.value(shift_vars[g][day][shift]) == 1:
                        assigned_shift = shift

                team_info["days"].append({"day": day, "shift": assigned_shift})
            result["teams"].append(team_info)
        result['status'] = "Optimal"
        # Ghi chú cho các ngày cố định
        result['note_fixed_shifts'] = [f"Ngày {datetime(year, month, fixed_date).strftime('%d/%m/%Y')}: {shift_info}" for fixed_date, shift_info in fixed_shifts.items()]
    else:
        result['status'] = "Không tìm được lời giải"
    return json.dumps(result)