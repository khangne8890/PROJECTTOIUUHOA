import streamlit as st
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def main():
    st.set_page_config(page_title="Demo VRPTW", page_icon="⏰", layout="wide")
    
    st.title("⏰ Demo Bài Toán VRPTW (Có khung thời gian)")
    st.markdown("**Đồ án Tối Ưu Hóa** | Sinh viên thực hiện: Mạc Minh Khang, Nguyễn Đăng Khoa, Nguyễn Ngọc Hiểu Minh")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚙️ Thông số hệ thống")
        so_xe = st.slider("Số lượng xe hoạt động:", min_value=1, max_value=4, value=2)
        kho = 0

        time_matrix = [
            [0, 6, 9, 8, 7],
            [6, 0, 8, 3, 2],
            [9, 8, 0, 11, 10],
            [8, 3, 11, 0, 1],
            [7, 2, 10, 1, 0],
        ]
        
        time_windows_goc = [
            (0, 50),   # Node 0 (Kho)
            (7, 12),   # Node 1
            (10, 15),  # Node 2
            (16, 18),  # Node 3
            (10, 13),  # Node 4
        ]

        st.write("**Thời gian yêu cầu của khách hàng (Phút):**")
        df_tw = pd.DataFrame(time_windows_goc, columns=["Mở cửa sớm nhất", "Đóng cửa trễ nhất"], 
                             index=["Kho 0", "Khách 1", "Khách 2", "Khách 3", "Khách 4"])
        
        # SỬ DỤNG st.data_editor để cho phép chỉnh sửa
        edited_tw_df = st.data_editor(df_tw, use_container_width=True)
        
        # Cập nhật lại mảng time_windows từ dữ liệu người dùng gõ vào
        time_windows = [tuple(int(val) for val in row) for row in edited_tw_df.values.tolist()]

        btn_run = st.button("🚀 Bắt đầu giải bài toán", use_container_width=True, type="primary")

    with col2:
        st.subheader("📍 Lịch trình & Thời gian cụ thể")
        if btn_run:
            manager = pywrapcp.RoutingIndexManager(len(time_matrix), so_xe, kho)
            routing = pywrapcp.RoutingModel(manager)

            def time_callback(from_index, to_index):
                a = manager.IndexToNode(from_index)
                b = manager.IndexToNode(to_index)
                return int(time_matrix[a][b])

            transit_callback_idx = routing.RegisterTransitCallback(time_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_idx)

            routing.AddDimension(transit_callback_idx, 30, 30, False, 'Time')
            time_dim = routing.GetDimensionOrDie('Time')

            for idx, (t_start, t_end) in enumerate(time_windows):
                if idx == kho:
                    continue
                node_idx = manager.NodeToIndex(idx)
                time_dim.CumulVar(node_idx).SetRange(t_start, t_end)

            search_params = pywrapcp.DefaultRoutingSearchParameters()
            search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

            solution = routing.SolveWithParameters(search_params)

            if solution:
                st.success(f"✅ Sắp xếp lịch thành công! Tổng thời gian vận hành: **{solution.ObjectiveValue()} phút**")

                for xe in range(so_xe):
                    index = routing.Start(xe)
                    route_str = f"**Lộ trình xe {xe + 1}:**\n\n"

                    while not routing.IsEnd(index):
                        t_var = time_dim.CumulVar(index)
                        node = manager.IndexToNode(index)
                        if node == 0:
                            route_str += f"🏭 Xuất phát từ Kho ➡️ "
                        else:
                            route_str += f"📍 Giao Khách {node} (Lúc {solution.Min(t_var)}p) ➡️ "
                        index = solution.Value(routing.NextVar(index))

                    t_var = time_dim.CumulVar(index)
                    route_str += f"🏠 Quay về Kho (Lúc {solution.Min(t_var)}p)"

                    st.info(route_str)
            else:
                st.error("❌ Không thể xếp lịch! Có khách hàng bị vi phạm Khung thời gian. Vui lòng tăng số xe hoặc nới lỏng thời gian.")

if __name__ == '__main__':
    main()