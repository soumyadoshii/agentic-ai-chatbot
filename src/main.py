# For user authentication
import os
import streamlit as st
import base64
from trainapp import user_input, get_pdf_text, get_text_chunks, vector_store
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

# Load environment variables
load_dotenv()

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None
    
def load_custom_css():
    try:
        with open("style.css", "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def load_config():
    """Load user configuration from config file"""
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.load(file, SafeLoader)
            return config
    except FileNotFoundError:
        st.error("Config file not found. Please create a config.yaml file.")
        return None

def check_password(username, password, config):
    """Securely check if the provided password matches the hashed password in config"""
    if not config or username not in config['credentials']['usernames']:
        return False, None
    
    user_data = config['credentials']['usernames'][username]
    stored_password_hash = user_data['password']
    
    # Professional-grade password verification
    if check_password_hash(stored_password_hash, password):
        return True, user_data
    return False, None

def is_admin(username, config):
    """Check if the user is an admin"""
    if 'admin_users' in config and username in config['admin_users']:
        return True
    return False

def main():
    st.set_page_config(page_title='Enterprise RAG Assistant', layout="centered")
    
    # First check if the user is authenticated
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.is_admin = False
    
    # Load config file
    config = load_config()
    if not config:
        st.stop()
    
    # If not authenticated, show clean login form
    if not st.session_state.authenticated:
        st.title("Login to Enterprise AI Assistant")
        
        # Centered, single login form (SSO removed)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit_button:
                authenticated, user_info = check_password(username, password, config)
                if authenticated:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.session_state.user_info['username'] = username
                    st.session_state.is_admin = is_admin(username, config)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.write("For Sign-Up - Please contact your system administrator.")
        return
    
    # Once authenticated, proceed with the main application
    st.title("Enterprise RAG Assistant")
    load_custom_css()
    
    # Fixed the hidden folder bug here
    logo_path = "static/Group 4898.png"
    
    # Initialize session states
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = []
    if "user_question" not in st.session_state:
        st.session_state.user_question = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Sidebar Menu
    with st.sidebar:
        logo_b64 = get_image_base64(logo_path)
        if logo_b64:
            st.markdown(f"""
            <div style="background-color: white; padding: 10px; border-radius: 10px; display: inline-block;">
            <img src="data:image/png;base64,{logo_b64}" width="200" height="30">
            </div>""", unsafe_allow_html=True)
        else:
            st.write("Enterprise Assistant")
        
        user_display_name = st.session_state.user_info.get('name', 'User')
        st.write(f"Logged in as: **{user_display_name}**")
        
        if st.session_state.is_admin:
            role = st.radio("Select Role", ("User", "Admin"), horizontal=True)
        else:
            role = "User"
            
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.is_admin = False
            st.rerun()
            
        if role == "User":
            st.markdown("### Starter Questions")
            sample_questions = [
                "Give a detailed summary of the main features.",
                "How does the system handle inventory and tracking?",
                "What are the reporting capabilities of this platform?",
                "Explain the data architecture and security protocols.",
                "What are the primary use cases for a business user?",
            ]
            
            for question in sample_questions:
                if st.button(question, use_container_width=True):
                    st.session_state.messages.append({'role': 'User', 'content': question, 'avatar': '👨🏻‍💻'})
                    response = user_input(question, [])
                    st.session_state.messages.append({'role': 'Assistant', 'content': response, 'avatar': '🤖'})

    # Main Chat Interface
    if role == "User":
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=message.get("avatar")):
                st.markdown(message["content"])

        user_question = st.session_state.user_question or st.chat_input("Ask a question based on the uploaded documents...")
        
        if user_question:
            st.session_state.user_question = ""
            with st.chat_message('User', avatar='👨🏻‍💻'):
                st.markdown(user_question)
                st.session_state.messages.append({'role': 'User', 'content': user_question, 'avatar': '👨🏻‍💻'})

            with st.chat_message('Assistant', avatar='🤖'):
                with st.spinner("Analyzing context..."):
                    response = user_input(user_question, st.session_state.chat_history)
                st.write(response)
                st.session_state.messages.append({'role': 'Assistant', 'content': response, 'avatar': '🤖'})
                
        # Feedback Section
        if st.session_state.messages and st.session_state.messages[-1]["role"] == 'Assistant':
            user_col1, user_col2 = st.columns([1, 15])
            with user_col1:
                feedback_button_neg = st.button('👎🏻')
            with user_col2:
                feedback_button_pos = st.button('👍🏻')

            if (feedback_button_neg or feedback_button_pos) and st.session_state.chat_history:
                generated_answer = st.session_state.chat_history[-1]
                user_question_text = st.session_state.chat_history[-2]
                
                feedback_entry = (
                    f"Question: {user_question_text}\n"
                    f"Answer: {generated_answer}\n"
                    f"Feedback: {'Positive' if feedback_button_pos else 'Negative'}\n"
                    f"{'-'*40}\n"
                )

                with open("feedback.txt", "a" if os.path.exists("feedback.txt") else "w", encoding="utf-8") as file:
                    file.write(feedback_entry)
                st.success("Thank you for your feedback!")

    # Admin Interface
    elif role == "Admin" and st.session_state.is_admin:
        st.header("Admin Dashboard")
        tab1, tab2 = st.tabs(["Document Upload", "User Management"])
        
        with tab1:
            pdf_docs = st.file_uploader('Upload PDFs to train the knowledge base', accept_multiple_files=True, type=['pdf'])
            if st.button('Train Model', type="primary") and pdf_docs:
                with st.spinner('Processing documents and building vector embeddings...'):
                    raw_text = get_pdf_text(pdf_docs)
                    chunks = get_text_chunks(raw_text)
                    vector_store(chunks)
                    st.success('Knowledge base successfully updated!')
        
        with tab2:
            st.subheader("Current Users")
            users_data = []
            for usr, data in config['credentials']['usernames'].items():
                users_data.append({
                    "Username": usr,
                    "Name": data.get('name', ''),
                    "Role": "Admin" if is_admin(usr, config) else "User"
                })
            st.table(users_data)
            
            st.subheader("Add New User")
            with st.form("add_user_form"):
                new_username = st.text_input("Username")
                new_name = st.text_input("Name")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["User", "Admin"])
                
                submit_user = st.form_submit_button("Create User", type="primary")
                
                if submit_user and new_username and new_password:
                    if new_username in config['credentials']['usernames']:
                        st.error(f"Username '{new_username}' already exists!")
                    else:
                        # Security Fix: Hash password before saving
                        config['credentials']['usernames'][new_username] = {
                            'name': new_name,
                            'email': new_email,
                            'password': generate_password_hash(new_password)
                        }
                        
                        if new_role == "Admin" and 'admin_users' in config:
                            config['admin_users'].append(new_username)
                        
                        with open('config.yaml', 'w') as file:
                            yaml.dump(config, file)
                        
                        st.success(f"User '{new_username}' added successfully!")
                        st.rerun()

if __name__ == "__main__":
    main()