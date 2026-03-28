"""
AI Money Mentor - ET AI Hackathon 2026
Core Backend Application
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from anthropic import Anthropic

# Initialize Flask and CORS
app = Flask(__name__)
CORS(app)

# Initialize Anthropic client
client = Anthropic()

# In-memory user data storage (replace with database in production)
users_db = {}
conversations = {}

# System prompts for different agents
FINANCIAL_ADVISOR_PROMPT = """You are an AI Financial Advisor for ET Money Mentor. You help users with:
1. FIRE (Financial Independence, Retire Early) Path Planning
2. Money Health Score assessment
3. Life Event Financial Decisions
4. Tax optimization strategies
5. Mutual Fund portfolio analysis

User has provided their financial information. Analyze it comprehensively and provide:
- Clear, actionable recommendations
- Quantified projections (month-by-month roadmap where applicable)
- Risk assessment and mitigation strategies
- Tax-saving opportunities specific to their bracket
- Emergency fund recommendations

Always ask clarifying questions if data is incomplete. Provide step-by-step guidance.
Currency: INR. Be specific with numbers and timelines."""

PORTFOLIO_ANALYZER_PROMPT = """You are a Portfolio Analysis Agent for AI Money Mentor. Analyze mutual fund portfolios:

When given CAMS/KFintech data or portfolio details, provide:
1. Portfolio Reconstruction (asset breakdown)
2. True XIRR calculation guidance
3. Overlap Analysis (duplicate exposures)
4. Expense Ratio Impact Assessment
5. Benchmark Comparison
6. AI-Generated Rebalancing Plan

Be quantitative. Show expense drag impact in rupees/percentages.
Flag concentration risks. Suggest diversification moves.
Consider tax implications of rebalancing (Long-term vs Short-term gains).
Provide actionable rebalancing strategies with priority order."""

TAX_WIZARD_PROMPT = """You are a Tax Optimization Agent for AI Money Mentor. Help users maximize tax efficiency:

When user provides Form 16 or salary details:
1. Identify ALL missed deductions (80C, 80D, 80E, 80G, 24, etc.)
2. Compare Old vs New Tax Regime with their specific numbers
3. Suggest tax-saving investments ranked by:
   - Risk profile match
   - Liquidity needs
   - Return potential
   - Deduction benefit
4. Calculate exact tax savings for each recommendation
5. Provide month-by-month SIP plan for optimal tax efficiency

Always consider HRA claims, NPS contributions, insurance premiums.
Be specific with amounts and deadlines. Show impact on take-home pay."""

COUPLE_PLANNER_PROMPT = """You are a Joint Financial Planning Agent for couples. Optimize finances across both partners:

Given both partners' income/assets/goals:
1. Optimize HRA claims (one vs both claiming)
2. NPS contribution strategy for max tax benefit
3. SIP allocation splits for tax efficiency
4. Joint vs individual insurance optimization
5. Combined net worth tracking & goal prioritization
6. Marital financial agreement recommendations

Calculate exact tax savings from optimal structure.
Consider future life events (kids, home loan, etc.).
Provide quarter-by-quarter implementation plan."""

def create_user_profile(user_data):
    """Create initial user profile"""
    user_id = user_data.get('user_id', 'user_' + str(int(datetime.now().timestamp())))
    profile = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'financial_data': user_data,
        'conversation_history': [],
        'recommendations': [],
        'impact_model': {}
    }
    users_db[user_id] = profile
    conversations[user_id] = []
    return user_id

def calculate_fire_roadmap(user_data):
    """Calculate FIRE path plan"""
    age = user_data.get('age', 0)
    income = user_data.get('annual_income', 0)
    expenses = user_data.get('monthly_expenses', 0) * 12
    existing_investments = user_data.get('existing_investments', 0)
    retirement_age = user_data.get('target_retirement_age', 60)
    
    monthly_savings = (income - expenses) / 12
    years_to_retirement = retirement_age - age
    annual_return = 0.12  # Assume 12% average return
    
    # Calculate required corpus (25x annual expenses)
    required_corpus = expenses * 25
    
    # Project future value
    fv = existing_investments * ((1 + annual_return) ** years_to_retirement)
    fv += monthly_savings * (((1 + annual_return) ** years_to_retirement - 1) / (annual_return / 12))
    
    roadmap = {
        'current_age': age,
        'target_retirement_age': retirement_age,
        'years_to_retirement': years_to_retirement,
        'monthly_savings_needed': monthly_savings,
        'annual_expenses': expenses,
        'required_corpus_25x': required_corpus,
        'projected_corpus': round(fv, 2),
        'fire_feasible': fv >= required_corpus,
        'monthly_sip_recommendations': {
            'equity': round(monthly_savings * 0.70, 2),
            'debt': round(monthly_savings * 0.20, 2),
            'gold': round(monthly_savings * 0.10, 2)
        }
    }
    
    return roadmap

def calculate_money_health_score(user_data):
    """Calculate comprehensive money health score"""
    scores = {}
    weights = {
        'emergency': 0.20,
        'insurance': 0.20,
        'diversification': 0.20,
        'debt': 0.15,
        'tax_efficiency': 0.15,
        'retirement': 0.10
    }
    
    # Emergency Fund Score (0-100)
    monthly_expenses = user_data.get('monthly_expenses', 0)
    emergency_fund = user_data.get('emergency_fund', 0)
    months_covered = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
    scores['emergency'] = min(100, (months_covered / 6) * 100)  # 6 months is ideal
    
    # Insurance Score (0-100)
    health_insurance = user_data.get('health_insurance_cover', 0)
    life_insurance = user_data.get('life_insurance_cover', 0)
    annual_income = user_data.get('annual_income', 1)
    insurance_score = 0
    if health_insurance >= 500000:
        insurance_score += 50
    if life_insurance >= annual_income * 10:
        insurance_score += 50
    scores['insurance'] = min(100, insurance_score)
    
    # Diversification Score (0-100)
    total_investments = user_data.get('total_investments', 1)
    equity_pct = (user_data.get('equity_investments', 0) / total_investments * 100) if total_investments > 0 else 0
    debt_pct = (user_data.get('debt_investments', 0) / total_investments * 100) if total_investments > 0 else 0
    
    # Ideal allocation depends on age, but 60-30-10 (equity-debt-gold) is standard
    diversification_score = 100 - (abs(equity_pct - 60) + abs(debt_pct - 30)) / 2
    scores['diversification'] = max(0, min(100, diversification_score))
    
    # Debt Health Score (0-100)
    total_debt = user_data.get('total_debt', 0)
    debt_ratio = total_debt / annual_income if annual_income > 0 else 0
    # Ideal: debt < 1x annual income
    scores['debt'] = max(0, 100 - (debt_ratio * 50))
    
    # Tax Efficiency Score (0-100)
    tax_paid = user_data.get('tax_paid', 0)
    taxable_income = user_data.get('taxable_income', annual_income * 0.8)
    effective_tax_rate = (tax_paid / annual_income * 100) if annual_income > 0 else 0
    # Benchmark: 15-20% effective rate is good
    scores['tax_efficiency'] = max(0, 100 - (abs(effective_tax_rate - 17.5) * 2))
    
    # Retirement Readiness Score (0-100)
    retirement_savings = user_data.get('retirement_savings', 0)
    years_to_retirement = user_data.get('target_retirement_age', 60) - user_data.get('age', 30)
    required_corpus = user_data.get('monthly_expenses', 0) * 12 * 25
    if years_to_retirement > 0:
        corpus_progress = (retirement_savings / required_corpus) * 100 if required_corpus > 0 else 0
        scores['retirement'] = min(100, corpus_progress)
    else:
        scores['retirement'] = 100
    
    # Calculate weighted overall score
    overall_score = sum(scores[key] * weights[key] for key in scores)
    
    return {
        'overall_score': round(overall_score, 1),
        'dimension_scores': {k: round(v, 1) for k, v in scores.items()},
        'health_level': 'Excellent' if overall_score >= 80 else 'Good' if overall_score >= 60 else 'Fair' if overall_score >= 40 else 'Poor',
        'top_priority': min(scores, key=scores.get)
    }

def chat_with_agent(user_id, message, agent_type='financial_advisor'):
    """Multi-turn conversation with AI agents using Claude API"""
    if user_id not in conversations:
        conversations[user_id] = []
    
    # Select appropriate system prompt
    system_prompts = {
        'financial_advisor': FINANCIAL_ADVISOR_PROMPT,
        'portfolio_analyzer': PORTFOLIO_ANALYZER_PROMPT,
        'tax_wizard': TAX_WIZARD_PROMPT,
        'couple_planner': COUPLE_PLANNER_PROMPT
    }
    
    system_prompt = system_prompts.get(agent_type, FINANCIAL_ADVISOR_PROMPT)
    
    # Add user message to conversation history
    conversations[user_id].append({
        'role': 'user',
        'content': message
    })
    
    # Get response from Claude API
    response = client.messages.create(
        model='claude-3-5-sonnet-20241022',
        max_tokens=1024,
        system=system_prompt,
        messages=conversations[user_id]
    )
    
    assistant_message = response.content[0].text
    
    # Add assistant response to conversation history
    conversations[user_id].append({
        'role': 'assistant',
        'content': assistant_message
    })
    
    return assistant_message

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/users/create', methods=['POST'])
def create_user():
    """Create new user and initialize profile"""
    try:
        data = request.json
        user_id = create_user_profile(data)
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User profile created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/users/<user_id>/fire-plan', methods=['POST'])
def get_fire_plan(user_id):
    """Generate FIRE roadmap"""
    try:
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = request.json
        roadmap = calculate_fire_roadmap(user_data)
        
        users_db[user_id]['recommendations'].append({
            'type': 'FIRE_PLAN',
            'data': roadmap,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'fire_roadmap': roadmap
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/users/<user_id>/money-health', methods=['POST'])
def get_money_health(user_id):
    """Calculate money health score"""
    try:
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = request.json
        health_score = calculate_money_health_score(user_data)
        
        users_db[user_id]['recommendations'].append({
            'type': 'MONEY_HEALTH_SCORE',
            'data': health_score,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'money_health_score': health_score
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/chat/<user_id>', methods=['POST'])
def chat(user_id):
    """Multi-turn conversation with AI agents"""
    try:
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        message = data.get('message')
        agent_type = data.get('agent_type', 'financial_advisor')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        response = chat_with_agent(user_id, message, agent_type)
        
        return jsonify({
            'success': True,
            'response': response,
            'agent_type': agent_type
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/users/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile and recommendations"""
    try:
        if user_id not in users_db:
            return jsonify({'error': 'User not found'}), 404
        
        profile = users_db[user_id]
        return jsonify({
            'success': True,
            'user_id': user_id,
            'created_at': profile['created_at'],
            'financial_data': profile['financial_data'],
            'recommendations_count': len(profile['recommendations']),
            'conversation_length': len(conversations.get(user_id, []))
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/portfolio-analysis', methods=['POST'])
def analyze_portfolio():
    """Analyze mutual fund portfolio"""
    try:
        data = request.json
        portfolio_data = data.get('portfolio')
        
        if not portfolio_data:
            return jsonify({'error': 'Portfolio data required'}), 400
        
        # Initialize analysis with chat agent
        user_id = data.get('user_id', 'temp_user_' + str(int(datetime.now().timestamp())))
        if user_id not in conversations:
            conversations[user_id] = []
        
        portfolio_summary = f"""
        Please analyze this mutual fund portfolio:
        {json.dumps(portfolio_data, indent=2)}
        
        Provide: 1) Portfolio reconstruction 2) XIRR guidance 3) Overlap analysis 
        4) Expense ratio impact 5) Benchmark comparison 6) Rebalancing plan
        """
        
        response = chat_with_agent(user_id, portfolio_summary, 'portfolio_analyzer')
        
        return jsonify({
            'success': True,
            'analysis': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/tax-optimization', methods=['POST'])
def optimize_taxes():
    """Tax optimization based on income"""
    try:
        data = request.json
        income_data = data.get('income_data')
        
        if not income_data:
            return jsonify({'error': 'Income data required'}), 400
        
        user_id = data.get('user_id', 'temp_user_' + str(int(datetime.now().timestamp())))
        if user_id not in conversations:
            conversations[user_id] = []
        
        tax_query = f"""
        User's Financial Details:
        {json.dumps(income_data, indent=2)}
        
        Please provide:
        1) All applicable tax deductions (80C, 80D, 80E, 80G, 24, etc.)
        2) Old vs New tax regime comparison with exact numbers
        3) Tax-saving investment suggestions ranked by risk/return
        4) Exact tax savings projection
        5) Month-by-month implementation plan
        """
        
        response = chat_with_agent(user_id, tax_query, 'tax_wizard')
        
        return jsonify({
            'success': True,
            'recommendations': response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
