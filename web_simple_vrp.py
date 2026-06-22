import streamlit as st
import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def main():
    st.set_page_config(page_title="Demo VRP", page_icon="🚛", layout="wide")
    
    st.title("🚛 Demo Bài Toán VRP Cơ Bản")
    st.markdown("**Đồ án Tối Ưu Hóa** | Sinh viên thực hiện: Mạc Minh Khang, Nguyễn Đăng Khoa, Nguyễn Ngọc Hiểu Minh")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚙️ Thông số đầu vào")
        so_xe = st.slider("Chọn số lượng xe giao hàng:", min_value=1, max_value=4, value=2)
        kho_xuat_phat = 0
        
        st.write("**Ma trận khoảng cách (mét):**")
        matrix_khoang_cach_goc = [
            [0, 548, 776, 696, 582],
            [548, 0, 684, 308, 194],
            [776, 684, 0, 992, 878],
            [696, 308, 992, 0, 114],
            [582, 194, 878, 114, 0],
        ]
        df_matrix = pd.DataFrame(matrix_khoang_cach_goc, 
                                 columns=["Kho 0", "Khách 1", "Khách 2", "Khách 3", "Khách 4"],
                                 index=["Kho 0", "Khách 1", "Khách 2", "Khách 3", "Khách 4"])
        
        edited_df = st.data_editor(df_matrix, use_container_width=True)
        matrix_khoang_cach = edited_df.values.tolist()

        btn_run = st.button("🚀 Chạy thuật toán OR-Tools", use_container_width=True, type="primary")

    with col2:
        st.subheader("📍 Kết quả lộ trình")
        if btn_run:
            manager = pywrapcp.RoutingIndexManager(len(matrix_khoang_cach), so_xe, kho_xuat_phat)
            routing = pywrapcp.RoutingModel(manager)

            def distance_callback(from_index, to_index):
                node_a = manager.IndexToNode(from_index)
                node_b = manager.IndexToNode(to_index)
                return int(matrix_khoang_cach[node_a][node_b])

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

            # --- THÊM RÀNG BUỘC: BẮT BUỘC TẤT CẢ CÁC XE ĐỀU PHẢI CÓ CHUYẾN ---
            def count_callback(from_index, to_index):
                return 1 # Mỗi lần di chuyển đếm là 1 chặng
            
            count_callback_idx = routing.RegisterTransitCallback(count_callback)
            routing.AddDimension(count_callback_idx, 0, 100, True, 'Count')
            count_dim = routing.GetDimensionOrDie('Count')
            
            # Ép mỗi xe phải đi ít nhất 2 chặng (Từ Kho -> 1 Khách -> Về Kho)
            for xe in range(so_xe):
                count_dim.CumulVar(routing.End(xe)).SetMin(2)
            # ---------------------------------------------------------------

            search_params = pywrapcp.DefaultRoutingSearchParameters()
            search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

            solution = routing.SolveWithParameters(search_params)

            if solution:
                st.success(f"✅ Đã tìm thấy giải pháp tối ưu! Tổng quãng đường của cả đội: **{solution.ObjectiveValue()} mét**")
                
                for xe in range(so_xe):
                    index = routing.Start(xe)
                    route_str = f"**Xe {xe + 1}:** Kho 0"
                    route_dist = 0

                    while not routing.IsEnd(index):
                        prev_index = index
                        index = solution.Value(routing.NextVar(index))
                        route_dist += routing.GetArcCostForVehicle(prev_index, index, xe)
                        route_str += f" ➡️ Điểm {manager.IndexToNode(index)}"

                    st.info(route_str)
                    st.caption(f"📏 Quãng đường xe {xe + 1} di chuyển: {route_dist} mét")
            else:
                st.error("❌ Không tìm thấy giải pháp. Hãy thử giảm số lượng xe hoặc thay đổi số liệu!")

if __name__ == '__main__':
    main()