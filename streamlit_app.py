import streamlit as st
import os
from google import genai
from google.genai import types

# --- 0. GUI & CSS INJECTION ---
def local_css(file_name):
    """Function to read the custom CSS file and inject it into the Streamlit app."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Warning: main.css file not found. Custom styling disabled.")

# --- 1. CONFIGURATION AND INITIALIZATION ---

# Initialize Session State Variables (for score tracking and UI state)
if 'ase_score' not in st.session_state: st.session_state.ase_score = 0
if 'umunna_score' not in st.session_state: st.session_state.umunna_score = 0
if 'advice_given' not in st.session_state: st.session_state.advice_given = False
if 'show_reflection' not in st.session_state: st.session_state.show_reflection = False
if 'challenge_active' not in st.session_state: st.session_state.challenge_active = False
if 'challenge_agent' not in st.session_state: st.session_state.challenge_agent = None
if 'challenge_response' not in st.session_state: st.session_state.challenge_response = ""
if 'show_challenge_result' not in st.session_state: st.session_state.show_challenge_result = False

# Initialize the Gemini Client
try:
    # IMPORTANT: Streamlit Secrets is the free and secure way to store the API Key
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception:
    st.error("Error: GEMINI_API_KEY not found. Please ensure it is configured in Streamlit Secrets.")
    st.stop()


# --- 2. ADVANCED AGENT DEFINITIONS (The Core Training Data) ---

# Yoruba Agent Training: Focus on Ori, Ebo, Ajogun, and Absolving God.
YORUBA_SYSTEM_PROMPT = """
You are the Ifá Priest (Babaláwo), a master diviner of the Yoruba tradition. Your advice is based on the spiritual, pre-chosen destiny (Orí) and the forces of nature (Ajogun).
- **Core Beliefs:** Destiny (Orí) is chosen before birth. Evil is caused by the Ajogun (Death, Disease, Loss, etc.). Success is achieved by consulting Ifá and performing Ebo (ritual offerings) to align your Ori and ward off the Ajogun.
- **Advice Style:** Ritualistic, Conditional, and Metaphorical. Prescribe a small, metaphorical Ebo or ritual action (not a real one) to ensure the person's Ori is favorable.
- **Constraint:** Your response must be 3-4 rich, concise sentences, using terms like Orí, Àṣẹ, Ajogun, and Ebo.
"""

# Igbo Agent Training: Focus on Chí, Umunna, and Ethics.
IGBO_SYSTEM_PROMPT = """
You are the Igbo Elder (Dibia), a respected community leader. Your advice is based on personal will (Chí), communal consensus (Umunna), and moral order (Omenalá).
- **Core Beliefs:** Success is a partnership between the individual's effort and their Chí. Moral responsibility and consequence are tied to one's actions and their impact on the Umunna (community). A person must strive for 'Ime Chí' (aligning with one's Chí). Luck is fleeting; a strong Chí is constant.
- **Advice Style:** Ethical, Communal, and Effort-Based. The advice must focus on moral consequences, consulting the Umunna, and reliance on hard work over chance.
- **Constraint:** Your response must be 3-4 rich, concise sentences, using terms like Chí, Umunna, Omenalá, and Dibia.
"""

# --- 3. CORE LOGIC FUNCTIONS ---

def get_advice(system_prompt, user_scenario):
    """Generates the initial advice."""
    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
    response = client.models.generate_content(
        model='gemini-2.5-flash', contents=f"User's Scenario: {user_scenario}", config=config
    )
    return response.text

def get_reflection(reflector_name, rejected_name, scenario, rejected_advice):
    """Generates the competitive cross-critique."""
    if reflector_name == "Ifá Priest":
        critique_prompt = f"You are the Yoruba Ifá Priest. Critique the Igbo Elder's focus on human effort (Chí) and community (Umunna) as insufficient without spiritual alignment (Orí) for the scenario: '{scenario}'. Be concise (3-4 sentences)."
    else:
        critique_prompt = f"You are the Igbo Elder. Critique the Ifá Priest's focus on Ebo (ritual) and fate (Orí) as morally insufficient without addressing the ethical consequence on the Umunna and personal will (Chí) for the scenario: '{scenario}'. Be concise (3-4 sentences)."
    
    config = types.GenerateContentConfig(temperature=0.8)
    response = client.models.generate_content(
        model='gemini-2.5-flash', contents=critique_prompt, config=config
    )
    return response.text

def get_challenge_response(agent_name, user_challenge, scenario, agent_advice):
    """Generates the agent's logical defense against the user's challenge."""
    challenge_prompt = f"""
    You are the {agent_name}. Defend your original advice based on your religious view.
    - Original Advice: "{agent_advice}"
    - User's Challenge: "{user_challenge}"
    - Defense: Use the core logic of your religion (Ori/Ajogun for Yoruba, or Chí/Umunna for Igbo) to logically rebut the user's argument and reaffirm why your advice is the correct path. (Max 5 sentences)
    """
    config = types.GenerateContentConfig(temperature=0.6)
    response = client.models.generate_content(
        model='gemini-2.5-flash', contents=challenge_prompt, config=config
    )
    return response.text

# --- 4. STREAMLIT UI LAYOUT & INTERACTIVE FLOW ---

st.set_page_config(page_title="Àṣe & Chí Alignment Score", layout="wide", initial_sidebar_state="collapsed")
local_css("styles/main.css") # Inject the custom CSS

st.title(" Yoruba & Igbo Ethical Showdown 🌍")
st.markdown("### Align your $Àṣẹ$ and $Chí$ | Reflection and Debate")

# Sidebar for Scores and Progression
with st.sidebar:
    st.header("Your Alignment Status")
    st.markdown("---")
    st.markdown(f"#### ⚡ Àṣẹ Alignment: **{st.session_state.ase_score}**")
    st.markdown(f"#### 🌿 Umunna Score: **{st.session_state.umunna_score}**")
    st.markdown("---")
    if st.button("Reset Game Scores"):
        st.session_state.ase_score = 0; st.session_state.umunna_score = 0
        st.session_state.advice_given = False; st.session_state.show_reflection = False
        st.session_state.challenge_active = False; st.session_state.show_challenge_result = False
        st.rerun()
        
# --- Primary Logic Flow ---

if not st.session_state.advice_given:
    # 1. SCENARIO INPUT
    st.subheader("1. Enter Your High-Stakes Dilemma")
    scenario = st.text_area(
        "Describe your ethical gamble (e.g., 'Should I quit my stable job to invest everything in a high-risk venture?'):", 
        key="scenario_input", height=150
    )
    
    col_button, col_warn = st.columns([1, 2])
    
    if col_button.button("Consult the Elders"):
        if scenario:
            with st.spinner("The Elders are consulting their sources..."):
                st.session_state.yoruba_advice = get_advice(YORUBA_SYSTEM_PROMPT, scenario)
                st.session_state.igbo_advice = get_advice(IGBO_SYSTEM_PROMPT, scenario)
            
            st.session_state.current_scenario = scenario
            st.session_state.advice_given = True
            st.session_state.show_reflection = False
            st.session_state.challenge_active = False
            st.rerun()
        else:
            col_warn.error("Please enter a scenario.")

elif st.session_state.advice_given and not st.session_state.show_reflection:
    # 2. ADVICE AND REFLECTION TRIGGER
    st.subheader(f"2. Dual Counsel for: *{st.session_state.current_scenario}*")
    
    col_yoruba, col_igbo = st.columns(2)
    
    with col_yoruba:
        st.markdown("#### ⚡ Ifá Priest (Yoruba: $Orí$ & $Àṣẹ$)")
        st.info(st.session_state.yoruba_advice)

    with col_igbo:
        st.markdown("#### 🌿 Igbo Elder ($Chí$ & $Umunna$)")
        st.success(st.session_state.igbo_advice)

    st.markdown("---")
    
    if st.button("Force Elders to **Critique** Each Other's Advice", help="This triggers the mandatory cross-cultural reflection."):
        st.session_state.show_reflection = True
        st.rerun()

elif st.session_state.show_reflection and not st.session_state.challenge_active:
    # 3. CROSS-RELIGION REFLECTION PHASE
    st.subheader("3. Cross-Cultural Reflection & Critique")
    
    col_critique_y, col_critique_i = st.columns(2)
    
    with col_critique_y:
        with st.spinner("Igbo Elder critiques Yoruba..."):
            igbo_critique = get_reflection(
                "Igbo Elder", "Ifá Priest", st.session_state.current_scenario, st.session_state.yoruba_advice
            )
        st.markdown("##### 🌿 Igbo Elder's Dissent:")
        st.error(f"> {igbo_critique}")

    with col_critique_i:
        with st.spinner("Ifá Priest critiques Igbo..."):
            yoruba_critique = get_reflection(
                "Ifá Priest", "Igbo Elder", st.session_state.current_scenario, st.session_state.igbo_advice
            )
        st.markdown("##### ⚡ Ifá Priest's Dissent:")
        st.error(f"> {yoruba_critique}")
        
    st.markdown("---")
    st.subheader("4. The Challenge Arena: Choose Your Path (and Defender)")
    
    col_c_y, col_c_i, col_next = st.columns(3)
    
    if col_c_y.button("CHALLENGE Yoruba Logic", help="Debate the Ifá Priest's reliance on ritual and fate."):
        st.session_state.challenge_active = True
        st.session_state.challenge_agent = "Ifá Priest"
        st.rerun()
        
    if col_c_i.button("CHALLENGE Igbo Logic", help="Debate the Igbo Elder's reliance on community and effort."):
        st.session_state.challenge_active = True
        st.session_state.challenge_agent = "Igbo Elder"
        st.rerun()

    if col_next.button("Accept Advice & Earn Base Points", help="Complete the cycle without a debate."):
        st.session_state.ase_score += 10; st.session_state.umunna_score += 10
        st.info("Points earned for completing the loop! Start a new scenario.")
        st.session_state.advice_given = False; st.session_state.show_reflection = False
        st.session_state.challenge_active = False
        st.rerun()

elif st.session_state.challenge_active:
    # 5. USER CHALLENGE PHASE
    st.subheader(f"5. Arena: Challenge the **{st.session_state.challenge_agent}**")
    
    agent_advice = st.session_state.yoruba_advice if st.session_state.challenge_agent == "Ifá Priest" else st.session_state.igbo_advice
    agent_name = "Ifá Priest (Yoruba)" if st.session_state.challenge_agent == "Ifá Priest" else "Igbo Elder (Igbo)"
        
    st.warning(f"**{agent_name}'s Original Advice:** *{agent_advice}*")
    
    challenge_input = st.text_area(
        "Enter your logical flaw or counter-argument:", 
        key="challenge_text"
    )
    
    if st.button("Submit Logical Challenge"):
        if challenge_input:
            with st.spinner(f"{agent_name} is preparing a formal defense..."):
                defense = get_challenge_response(
                    agent_name, challenge_input, st.session_state.current_scenario, agent_advice
                )
            
            st.session_state.challenge_response = defense
            st.session_state.challenge_input = challenge_input
            st.session_state.show_challenge_result = True
            st.rerun()
        else:
            st.error("Please enter your challenge argument.")

    if st.session_state.get('show_challenge_result'):
        st.markdown("---")
        st.subheader("The Elder's Defense")
        st.info(f"**{agent_name}'s Defense:**")
        st.markdown(f"> *{st.session_state.challenge_response}*")
        
        st.markdown("---")
        st.subheader("Challenge Resolution (Fun Verdict)")
        
        # Scoring logic: rewarding the user for integrating opposing concepts
        user_input_lower = st.session_state.challenge_input.lower()
        success = False
        if st.session_state.challenge_agent == "Ifá Priest" and any(word in user_input_lower for word in ["will", "effort", "free will", "community", "umunna", "ethics"]):
            st.success("Verdict: CHALLENGE SUCCESS! Your argument exposed a weakness in the fate-based model by stressing **human will**.")
            st.session_state.ase_score += 30 
            st.session_state.umunna_score += 10 
            success = True
        elif st.session_state.challenge_agent == "Igbo Elder" and any(word in user_input_lower for word in ["fate", "ritual", "spiritual", "ori", "cosmic", "destiny"]):
            st.success("Verdict: CHALLENGE SUCCESS! Your argument exposed a weakness in the ethics model by stressing **spiritual fate**.")
            st.session_state.umunna_score += 30 
            st.session_state.ase_score += 10 
            success = True
        else:
            st.error("Verdict: CHALLENGE DEFEATED. The Elder successfully defended their doctrine.")
            st.session_state.ase_score += 5; st.session_state.umunna_score += 5

        if st.button("Continue to New Scenario"):
            st.session_state.advice_given = False
            st.session_state.show_reflection = False
            st.session_state.challenge_active = False
            st.session_state.show_challenge_result = False
            st.rerun()