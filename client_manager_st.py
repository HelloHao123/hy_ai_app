import streamlit as st
import pandas as pd
import os
import uuid # 用于生成唯一文件名
import io # 👈 【新增】用于在内存中生成文件，极速导出
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text

# --- 1. 数据库配置和模型定义 ---
DATABASE_URI = "sqlite:///clients.db"

# --- 2. Streamlit Session State 管理 SQLAlchemy 实例 ---
if 'sqlalchemy_engine' not in st.session_state:
    st.session_state['sqlalchemy_engine'] = create_engine(DATABASE_URI)
if 'sqlalchemy_session_factory' not in st.session_state:
    st.session_state['sqlalchemy_session_factory'] = sessionmaker(bind=st.session_state['sqlalchemy_engine'])
if 'sqlalchemy_base' not in st.session_state:
    st.session_state['sqlalchemy_base'] = declarative_base()

engine = st.session_state['sqlalchemy_engine']
Session = st.session_state['sqlalchemy_session_factory']
Base = st.session_state['sqlalchemy_base']


class Client(Base):
    __tablename__ = 'clients'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    no = Column(String(50), unique=True, nullable=False)
    client_name = Column(String(100), nullable=False)
    contact_info = Column(String(200))
    nationality_city = Column(String(100))
    company = Column(String(200), nullable=False)
    product = Column(String(200))
    notes_progress = Column(Text)
    business_card = Column(String(255))
    company_background = Column(Text)

    def __repr__(self):
        return f'<Client {self.id} | {self.client_name} - {self.company}>'

# --- 3. 数据库操作函数 ---
@st.cache_resource
def init_db():
    Base.metadata.create_all(engine)

def get_clients():
    session = Session()
    clients = session.query(Client).all()
    session.close()
    return clients

def add_client_to_db(client_data):
    session = Session()
    new_client = Client(**client_data)
    try:
        session.add(new_client)
        session.commit()
        st.success("客户信息添加成功！")
    except Exception as e:
        session.rollback()
        st.error(f"添加客户信息失败: {e}")
    finally:
        session.close()

# --- 批量导入函数 (优化版) ---
def import_clients_from_df(df_to_import):
    df_to_import.columns = [col.strip() for col in df_to_import.columns]
    
    session = Session()
    imported_count = 0
    skipped_count = 0
    errors = []

    required_cols = ['No.', 'Clients Name', 'Company']
    
    for index, row in df_to_import.iterrows():
        try:
            missing_fields = [col for col in required_cols if col not in df_to_import.columns or pd.isna(row.get(col))]
            if missing_fields:
                errors.append(f"第 {index+2} 行缺少必填项 {missing_fields}，跳过。")
                skipped_count += 1
                continue

            client_no = str(row['No.']).strip()

            existing_client = session.query(Client).filter_by(no=client_no).first()
            if existing_client:
                errors.append(f"客户编号 {client_no} 已存在，跳过第 {index+2} 行。")
                skipped_count += 1
                continue

            client_data = {
                'no': client_no,
                'client_name': row.get('Clients Name', ''),
                'contact_info': row.get('Contact Info', ''),
                'nationality_city': row.get('Nationality/City', ''),
                'company': row.get('Company', ''),
                'product': row.get('Product', ''),
                'notes_progress': row.get('备注/进度', ''),
                'business_card': row.get('名片', ''),
                'company_background': get_company_background(row.get('Company', ''))
            }
            new_client = Client(**client_data)
            session.add(new_client)
            imported_count += 1
        except Exception as e:
            session.rollback()
            errors.append(f"导入第 {index+2} 行时发生异常: {e}")
            skipped_count += 1

    try:
        session.commit()
        return imported_count, skipped_count, errors
    except Exception as e:
        session.rollback()
        errors.insert(0, f"数据库最终提交失败: {e}")
        return imported_count, skipped_count, errors
    finally:
        session.close()

# --- 4. 公司背景调查函数 ---
def get_company_background(company_name):
    if not company_name:
        return ""
    if "腾讯" in company_name:
        return "腾讯公司成立于1998年，主要经营互联网增值服务、金融科技等。"
    elif "华为" in company_name:
        return "华为技术有限公司成立于1987年，是全球领先的ICT解决方案供应商。"
    else:
        return "未找到该公司背景信息 (请集成真实API)"

# --- 5. Streamlit UI 渲染函数 ---
def render_client_manager():
    st.header("👥 客户信息管理")
    init_db()

    tab1, tab2 = st.tabs(["查看所有客户", "添加新客户"])

    with tab1:
        st.subheader("所有客户列表")

        # --- Excel 批量导入功能 ---
        st.markdown("---")
        st.subheader("批量导入客户信息 (Excel)")
        uploaded_excel_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls"], key="excel_uploader")
        
        if uploaded_excel_file is not None:
            if st.button("开始导入", key="start_import_button"):
                try:
                    df_to_import = pd.read_excel(uploaded_excel_file)
                    imported, skipped, errs = import_clients_from_df(df_to_import)
                    
                    st.session_state['import_result'] = {
                        'imported': imported,
                        'skipped': skipped,
                        'errors': errs,
                        'columns': list(df_to_import.columns)
                    }
                    st.rerun() 
                except Exception as e:
                    st.error(f"处理 Excel 文件失败: {e}")

        if 'import_result' in st.session_state:
            res = st.session_state['import_result']
            if res['imported'] > 0:
                st.success(f"✅ 成功导入 {res['imported']} 条客户数据！")
            if res['skipped'] > 0:
                st.warning(f"⚠️ 跳过 {res['skipped']} 条数据。")
                for error in res['errors'][:5]:
                    st.error(error)
            
            if res['imported'] == 0 and res['skipped'] == 0:
                st.info("文件为空，没有数据被导入。")
            elif res['imported'] == 0:
                st.error("❌ 导入失败：没有一条数据成功进入数据库。")
                st.write("💡 **调试信息**：程序在 Excel 中识别到的列名为：")
                st.code(res['columns'])
                st.write("请确保 Excel 表头包含：`No.`, `Clients Name`, `Company` (注意大小写和标点)")
            
            del st.session_state['import_result']

        st.markdown("---")
        # --- Excel 批量导入功能结束 ---

        clients = get_clients()
        if clients:
            data =[]
            for client in clients:
                data_row = {
                    'No.': client.no,
                    '客户姓名': client.client_name,
                    '联系方式': client.contact_info,
                    '国籍/城市': client.nationality_city,
                    '公司': client.company,
                    '产品': client.product,
                    '备注/进度': client.notes_progress,
                    '名片路径/URL': client.business_card,
                    '公司背景': client.company_background
                }
                data.append(data_row)
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

            # 名片预览区域
            st.markdown("---")
            st.subheader("名片预览")
            clients_with_cards = [c for c in clients if c.business_card]
            if clients_with_cards:
                col_count = 5
                cols = st.columns(col_count)
                for i, client in enumerate(clients_with_cards):
                    with cols[i % col_count]:
                        st.caption(client.client_name)
                        try:
                            if client.business_card.startswith(('http://', 'https://')):
                                st.image(client.business_card, width=100)
                            elif os.path.exists(client.business_card):
                                st.image(client.business_card, width=100)
                            else:
                                st.write("文件缺失")
                        except:
                            st.write("加载失败")
            else:
                st.info("没有可供预览的名片。")

            # ================= [导出数据功能 (优化版)] =================
            st.markdown("---")
            st.subheader("📥 数据备份与导出")
            
            col_ex1, col_ex2 = st.columns(2)
            
            # 1. 导出为 Excel 格式（利用 io.BytesIO 在内存中生成）
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='客户列表')
            
            with col_ex1:
                st.download_button(
                    label="📊 下载为 Excel 文件 (.xlsx)",
                    data=buffer.getvalue(),
                    file_name="客户信息备份.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                    key="download_excel_mem"
                )
            
            # 2. 导出为 CSV 格式
            csv_data = df.to_csv(index=False).encode('utf-8-sig')
            with col_ex2:
                st.download_button(
                    label="📑 下载为 CSV 文件 (.csv)",
                    data=csv_data,
                    file_name="客户信息备份.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_csv_mem"
                )
            # =========================================================

        else:
            st.info("目前没有客户信息，请上传 Excel 导入，或切换到 '添加新客户' 选项卡进行添加。")

    with tab2:
        st.subheader("添加新客户")
        with st.form("add_client_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            current_business_card_path = "" 

            with col1:
                no = st.text_input("No.", help="客户唯一编号", key="add_no")
                client_name = st.text_input("客户姓名", key="add_client_name")
                contact_info = st.text_input("联系方式 (电话/邮箱)", key="add_contact_info")
                nationality_city = st.text_input("国籍/城市", key="add_nationality_city")
            with col2:
                company = st.text_input("公司名称", key="add_company")
                if company:
                    company_bg = get_company_background(company)
                    st.text_area("公司背景信息", value=company_bg, height=100, disabled=True, key="company_bg_display")
                else:
                    st.text_area("公司背景信息", value="请输入公司名称以加载背景...", height=100, disabled=True, key="company_bg_placeholder")

                product = st.text_input("产品", key="add_product")
                uploaded_file = st.file_uploader("上传名片图片 (可选)", type=["jpg", "jpeg", "png", "webp"], key="upload_business_card")
                text_input_business_card = st.text_input("或直接输入名片URL/路径 (可选)", key="text_business_card_path")

                if uploaded_file is not None:
                    upload_dir = "uploads/business_cards"
                    os.makedirs(upload_dir, exist_ok=True)
                    file_ext = os.path.splitext(uploaded_file.name)[1]
                    unique_filename = f"{uuid.uuid4()}{file_ext}"
                    full_save_path = os.path.join(upload_dir, unique_filename)
                    with open(full_save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    current_business_card_path = full_save_path
                    st.image(current_business_card_path, width=100)
                elif text_input_business_card:
                    current_business_card_path = text_input_business_card

                notes_progress = st.text_area("备注/进度", key="add_notes_progress")

            submitted = st.form_submit_button("保存客户信息", type="primary", use_container_width=True)
            if submitted:
                if not no or not client_name or not company:
                    st.error("No., 客户姓名和公司名称为必填项！")
                else:
                    client_data = {
                        'no': no,
                        'client_name': client_name,
                        'contact_info': contact_info,
                        'nationality_city': nationality_city,
                        'company': company,
                        'product': product,
                        'notes_progress': notes_progress,
                        'business_card': current_business_card_path,
                        'company_background': get_company_background(company)
                    }
                    add_client_to_db(client_data)
                    st.rerun()
