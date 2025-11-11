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

# 편의를 위해 DataFrame 변수를 세션 상태에 연결
# *주의: 함수 내에서 수정 시 st.session_state.inventory_df에 다시 할당해야 함*
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

# --- 3. 재고 관리 로직 함수 (추가/수정) ---

def add_new_equipment(name, stock):
    """새로운 도구를 재고 목록에 추가합니다."""
    # 도구 ID 자동 할당 (현재 최대 ID + 1)
    new_id = df_inventory['도구ID'].max() + 1 if not df_inventory.empty else 101
    
    new_data = pd.DataFrame([{
        "도구ID": new_id,
        "도구명": name,
        "총 재고": stock,
        "대여 중": 0,
        "잔여 개수": stock
    }])
    
    # 세션 상태 업데이트
    st.session_state.inventory_df = pd.concat(
        [df_inventory, new_data],
        ignore_index=True
    )
    st.success(f"✅ 새 도구 **ID {new_id} - {name}** (총 재고: {stock}개)가 추가되었습니다.")

def modify_equipment_stock(tool_id, new_total_stock):
    """기존 도구의 총 재고 수량을 수정합니다."""
    tool_idx = df_inventory[df_inventory['도구ID'] == tool_id].index
    
    if not tool_idx.empty:
        idx = tool_idx[0]
        tool_name = df_inventory.loc[idx, '도구명']
        loaned_count = df_inventory.loc[idx, '대여 중']
        
        # 유효성 검사: 새 재고는 현재 대여 중인 개수보다 적을 수 없음
        if new_total_stock < loaned_count:
            st.error(f"❌ 총 재고는 현재 대여 중인 개수({loaned_count}개)보다 적을 수 없습니다.")
            return

        # 업데이트
        df_inventory.loc[idx, '총 재고'] = new_total_stock
        df_inventory.loc[idx, '잔여 개수'] = new_total_stock - loaned_count
        
        # 세션 상태 업데이트
        st.session_state.inventory_df = df_inventory
        
        st.success(f"✅ **{tool_name}**의 총 재고가 **{new_total_stock}개**로 수정되었습니다.")
    else:
        st.error(f"❌ 도구 ID **{tool_id}**를 찾을 수 없습니다.")

# --- 4. 대여/반납 로직 함수 (기존) ---

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
        st.error
