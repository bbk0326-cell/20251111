import streamlit as st
import pandas as pd
from datetime import date, timedelta
import random

# --- 1. 초기 데이터 및 세션 상태 설정 ---

# 초기 재고 데이터 정의
INITIAL_INVENTORY = {
    "도구ID": [101, 102, 103, 104, 105],
    "도구명": ["비커 (500ml)", "현미경", "메스 실린더 (100ml)", "전자 저울", "삼각 플라스크 (250ml)"],
    "총 재고": [10, 3, 15, 2, 8],
    "대여 중": [0, 0, 0, 0, 0],
}

# 대여 기록 초기화
INITIAL_LOAN_HISTORY = pd.DataFrame({
    "도구ID": pd.Series(dtype='int'),
    "대여자": pd.Series(dtype='str'),
    "대여일": pd.Series(dtype='object'),
    "반납 예정일": pd.Series(dtype='object'),
    "상태": pd.Series(dtype='str') # '대여 중', '반납 완료'
})

def initialize_session():
    """앱 실행 시 세션 상태 초기화 및 데이터 로드"""
    if 'inventory_df' not in st.session_state:
        st.session_state.inventory_df = pd.DataFrame(INITIAL_INVENTORY)
        st.session_state.inventory_df['잔여 개수'] = (
            st.session_state.inventory_df['총 재고'] - st.session_state.inventory_df['대여 중']
        )
    
    if 'loan_history_df' not in st.session_state:
        st.session_state.loan_history_df = INITIAL_LOAN_HISTORY.copy()

# 세션 상태 초기화 함수 실행
initialize_session()
df_inventory = st.session_state.inventory_df
df_history = st.session_state.loan_history_df

# --- 2. Streamlit 앱 UI 설정 ---
st.set_page_config(
    page_title="🧪 실험 도구 도서관",
    layout="wide",
    initial_sidebar_state="auto"
)

st.title("🔬 과학 실험 도구 대여 시스템")
st.markdown("도구의 재고 현황을 확인하고, 대여 및 반납 기록을 관리할 수 있습니다.")
st.markdown("---")

# --- 3. 대여/반납 로직 함수 ---

def loan_equipment(tool_id, borrower_name, due_days=7):
    """도구를 대여하고 재고 및 기록을 업데이트합니다."""
    # 1. 재고 확인 및 업데이트
    tool_idx = df_inventory[df_inventory['도구ID'] == tool_id].index
    if not tool_idx.empty:
        idx = tool_idx[0]
        
        if df_inventory.loc[idx, '잔여 개수'] > 0:
            # 재고 수량 업데이트
            df_inventory.loc[idx, '대여 중'] += 1
            df_inventory.loc[idx, '잔여 개수'] -= 1
            st.session_state.inventory_df = df_inventory # 세션 상태 업데이트

            # 2. 대여 기록 추가
            today = date.today()
            due_date = today + timedelta(days=due_days)
            
            new_record = pd.DataFrame([{
                "도구ID": tool_id,
                "대여자": borrower_name,
                "대여일": today,
                "반납 예정일": due_date,
                "상태": "대여 중"
            }])
            
            st.session_state.loan_history_df = pd.concat(
                [df_history, new_record], 
                ignore_index=True
            )
            st.success(f"✅ **{df_inventory.loc[idx, '도구명']}** 1개가 **{borrower_name}**님께 대여되었습니다. (반납 예정일: {due_date})")
        else:
            st.error(f"❌ **{df_inventory.loc[idx, '도구명']}**의 잔여 개수가 부족합니다.")
    else:
        st.error(f"❌ 도구 ID **{tool_id}**를 찾을 수 없습니다.")

def return_equipment(record_index):
    """도구를 반납 처리하고 재고 및 기록을 업데이트합니다."""
    if record_index in df_history.index and df_history.loc[record_index, '상태'] == '대여 중':
        tool_id = df_history.loc[record_index, '도구ID']
        tool_name = df_inventory[df_inventory['도구ID'] == tool_id]['도구명'].iloc[0]
        borrower = df_history.loc[record_index, '대여자']
        
        # 1. 재고 업데이트
        tool_idx = df_inventory[df_inventory['도구ID'] == tool_id].index[0]
        df_inventory.loc[tool_idx, '대여 중'] -= 1
        df_inventory.loc[tool_idx, '잔여 개수'] += 1
        st.session_state.inventory_df = df_inventory # 세션 상태 업데이트

        # 2. 기록 상태 업데이트
        st.session_state.loan_history_df.loc[record_index, '상태'] = '반납 완료'
        
        st.success(f"✅ **{tool_name}**가 정상적으로 반납 처리되었습니다. ({borrower}님)")
    else:
        st.error("❌ 해당 대여 기록을 찾을 수 없거나 이미 반납된 상태입니다.")

# --- 4. UI 탭 구성 ---
tab1, tab2 = st.tabs(["📊 재고 현황", "📚 대여/반납 기록"])

with tab1:
    st.header("재고 및 잔여 개수 확인")
    st.info("현재 각 도구의 **총 재고**와 **대여 가능한 잔여 개수**를 확인할 수 있습니다.")
    
    # 데이터프레임 표시
    st.dataframe(
        df_inventory.sort_values(by='도구ID'),
        hide_index=True,
        column_config={
            "도구ID": st.column_config.NumberColumn("ID", width="small"),
            "도구명": st.column_config.TextColumn("도구명", width="large"),
            "총 재고": st.column_config.NumberColumn("총 재고", format="%d 개"),
            "대여 중": st.column_config.NumberColumn("대여 중", format="%d 개"),
            "잔여 개수": st.column_config.NumberColumn("잔여 개수 (대여 가능)", format="%d 개"),
        }
    )
    
    st.markdown("---")
    
    st.subheader("새로운 도구 대여 신청")
    with st.form("loan_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            tool_id_list = df_inventory['도구ID'].tolist()
            tool_id_selection = st.selectbox(
                "대여할 도구 (ID)",
                options=tool_id_list,
                format_func=lambda x: f"ID {x} - {df_inventory[df_inventory['도구ID'] == x]['도구명'].iloc[0]}"
            )
        
        with col2:
            borrower_name = st.text_input("대여자 이름/학과", placeholder="예: 김철수, 화학과")
        
        submitted = st.form_submit_button("대여 처리")
        
        if submitted and tool_id_selection and borrower_name:
            loan_equipment(tool_id_selection, borrower_name)

with tab2:
    st.header("대여 및 반납 기록")
    
    # '대여 중'인 기록 필터링
    active_loans = df_history[df_history['상태'] == '대여 중'].sort_values(by='반납 예정일')
    
    st.subheader("🔴 현재 대여 중인 도구 목록")
    if not active_loans.empty:
        
        # 도구명 조인을 위한 임시 병합
        display_active_loans = active_loans.merge(
            df_inventory[['도구ID', '도구명']], 
            on='도구ID', 
            how='left'
        )
        display_active_loans = display_active_loans.rename(columns={'도구명': '도구'})
        
        # 반납 처리 선택을 위한 체크박스
        st.markdown("---")
        st.caption("반납할 기록을 선택하고 아래 '반납 처리' 버튼을 누르세요.")
        
        # 반납 처리 폼
        with st.form("return_form"):
            return_indices = []
            
            # 기록을 테이블로 표시하고 반납 체크박스 추가
            for index, row in display_active_loans.iterrows():
                col_check, col_id, col_name, col_borrower, col_due = st.columns([0.5, 0.5, 2, 1.5, 1.5])
                
                with col_check:
                    if st.checkbox("", key=f"return_check_{index}"):
                        return_indices.append(index)
                
                with col_id:
                    st.text(row['도구ID'])
                with col_name:
                    st.text(row['도구'])
                with col_borrower:
                    st.text(row['대여자'])
                with col_due:
                    st.text(row['반납 예정일'].strftime('%Y-%m-%d'))
                    
            return_submitted = st.form_submit_button("선택 항목 반납 처리")
            
            if return_submitted and return_indices:
                for index in return_indices:
                    return_equipment(index)
                # 반납 후 폼을 다시 로드하여 상태 업데이트
                st.rerun() 
            elif return_submitted and not return_indices:
                st.warning("반납할 항목을 선택해주세요.")

    else:
        st.info("현재 대여 중인 도구가 없습니다.")
        
    st.markdown("---")
    
    st.subheader("📚 전체 대여 기록 (최근 10건)")
    # 모든 기록 표시 (최신순 10건)
    display_all_history = df_history.sort_values(by='대여일', ascending=False).head(10).merge(
        df_inventory[['도구ID', '도구명']], 
        on='도구ID', 
        how='left'
    ).rename(columns={'도구명': '도구'})
    
    st.dataframe(
        display_all_history,
        hide_index=True,
        column_order=["도구ID", "도구", "대여자", "대여일", "반납 예정일", "상태"],
        column_config={
            "도구ID": st.column_config.NumberColumn("ID", width="small"),
            "도구": st.column_config.TextColumn("도구명", width="large"),
            "대여자": st.column_config.TextColumn("대여자", width="medium"),
            "대여일": st.column_config.DateColumn("대여일", format="YYYY-MM-DD"),
            "반납 예정일": st.column_config.DateColumn("반납 예정일", format="YYYY-MM-DD"),
            "상태": st.column_config.TextColumn("상태", width="small"),
        }
    )
