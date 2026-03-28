# System Architecture - AI Money Mentor

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER LAYER                                  │
│                   React Web Application                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│  │  Landing     │ │  Dashboard   │ │  Results     │               │
│  │  Page        │ │  (Actions)   │ │  Page        │               │
│  └──────────────┘ └──────────────┘ └──────────────┘               │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ REST API (HTTP/JSON)
┌────────────────────────▼─────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│                    Flask Backend (Python)                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ API Routes & Request Handling                                │  │
│  │ - POST /api/users/create                                     │  │
│  │ - POST /api/users/<id>/fire-plan                             │  │
│  │ - POST /api/users/<id>/money-health                          │  │
│  │ - POST /api/chat/<id>                                        │  │
│  │ - POST /api/portfolio-analysis                               │  │
│  │ - POST /api/tax-optimization                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Business Logic Layer                                          │  │
│  │ ┌─────────────────────┐ ┌─────────────────────┐            │  │
│  │ │ Financial Calc      │ │ Agent Orchestration │            │  │
│  │ │ - FIRE roadmap      │ │ - Route to agents   │            │  │
│  │ │ - Health score      │ │ - Context mgmt      │            │  │
│  │ │ - SIP allocation    │ │ - Conversation hist │            │  │
│  │ └─────────────────────┘ └─────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Data Layer                                                    │  │
│  │ - User profiles (in-memory → database)                       │  │
│  │ - Conversation history (session storage)                     │  │
│  │ - Recommendations cache                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────────┘
                         │ API Calls (HTTP)
┌────────────────────────▼─────────────────────────────────────────────┐
│                      AI AGENT LAYER                                  │
│              Claude Anthropic API (claude-3-5-sonnet)                │
│  ┌─────────────────────┐ ┌─────────────────────┐                   │
│  │ Financial Advisor   │ │ Portfolio Analyzer  │                   │
│  │ - FIRE planning     │ │ - XIRR calculation  │                   │
│  │ - General advice    │ │ - Overlap detection │                   │
│  │ - Risk profiling    │ │ - Rebalancing plan  │                   │
│  └─────────────────────┘ └─────────────────────┘                   │
│  ┌─────────────────────┐ ┌─────────────────────┐                   │
│  │ Tax Wizard          │ │ Couple Planner      │                   │
│  │ - Deduction ID      │ │ - Joint optimization│                   │
│  │ - Tax regime comp   │ │ - HRA strategy      │                   │
│  │ - Form 16 analysis  │ │ - SIP splits        │                   │
│  └─────────────────────┘ └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (React.js)

**Pages:**

#### Landing Page
- User onboarding form (8 financial inputs)
- Feature highlights
- Call-to-action button
- Responsive design (mobile-first)

**Key Components:**
- `formData` state (age, income, expenses, etc.)
- `handleInputChange()` → Updates form state
- `createUserProfile()` → POST to `/api/users/create`
- Form validation (numeric inputs)

#### Dashboard
- Quick action buttons (Money Health, FIRE Plan)
- Chat interface (multi-turn conversation)
- Agent selector dropdown (4 agent types)
- Message history with auto-scroll

**Key Components:**
- `chatMessages` state (array of messages)
- `sendChatMessage()` → POST to `/api/chat/<user_id>`
- `calculateMoneyHealth()` → POST to `/api/users/<id>/money-health`
- `calculateFIREPlan()` → POST to `/api/users/<id>/fire-plan`

#### Results Page
- Money Health Score visualization (6 dimensions)
- FIRE Roadmap breakdown
- SIP recommendations cards
- Back button to dashboard

**Key Components:**
- Circular score display with level indicator
- Dimension bars (width = score %)
- Stat cards with rupee formatting

---

### 2. Backend (Flask)

**Core Functions:**

#### `create_user_profile(user_data)`
```python
Input: {age, annual_income, monthly_expenses, ...}
Output: user_id (string)
Action: 
  - Generate unique user ID
  - Store profile in users_db
  - Initialize conversation history
```

#### `calculate_fire_roadmap(user_data)`
```python
Input: {age, income, expenses, existing_investments, ...}
Output: {
  years_to_retirement,
  monthly_savings_needed,
  required_corpus_25x,
  projected_corpus,
  fire_feasible,
  monthly_sip_recommendations
}
Formula:
  - Years = target_age - current_age
  - Monthly savings = (annual_income - annual_expenses) / 12
  - Projected FV = existing * (1.12^years) + monthly * compound_factor
  - Corpus = 25 * annual_expenses
```

#### `calculate_money_health_score(user_data)`
```python
Dimensions & Scoring:
  1. Emergency (20% weight)
     Score = (months_covered / 6) * 100
     
  2. Insurance (20% weight)
     Score = 50 (health ≥ ₹5L) + 50 (life ≥ 10x income)
     
  3. Diversification (20% weight)
     Score = 100 - (|equity% - 60| + |debt% - 30|) / 2
     
  4. Debt Health (15% weight)
     Score = 100 - (debt_ratio * 50)
     Ideal: debt < 1x annual income
     
  5. Tax Efficiency (15% weight)
     Score = 100 - |effective_tax_rate - 17.5| * 2
     
  6. Retirement (10% weight)
     Score = (retirement_savings / required_corpus) * 100

Overall = Σ(dimension_score * weight)
```

#### `chat_with_agent(user_id, message, agent_type)`
```python
Flow:
  1. Fetch conversation history for user
  2. Select system prompt based on agent_type
  3. Add new message to history
  4. Call Claude API with full conversation
  5. Extract response from Claude
  6. Append to conversation history
  7. Return response to user

Context Passed to Claude:
  - System prompt (domain-specific)
  - Full conversation history (multi-turn)
  - User financial data (implicit)
```

**API Endpoints:**

| Method | Endpoint | Purpose | Returns |
|--------|----------|---------|---------|
| POST | `/api/users/create` | Create profile | user_id |
| GET | `/api/users/<id>/profile` | Get profile | user data |
| POST | `/api/users/<id>/fire-plan` | FIRE roadmap | roadmap object |
| POST | `/api/users/<id>/money-health` | Health score | score + dimensions |
| POST | `/api/chat/<id>` | Chat with agent | AI response |
| POST | `/api/portfolio-analysis` | Analyze portfolio | analysis |
| POST | `/api/tax-optimization` | Tax advice | recommendations |
| GET | `/api/health` | Health check | status |

---

### 3. AI Agent Layer (Claude API)

**Agent Prompts:**

#### Financial Advisor Prompt
```
Role: Personal financial advisor
Capabilities:
  - FIRE path planning
  - Goal-based recommendations
  - Risk assessment
  - Budget optimization
  - Investment strategy

Input Format:
  User message + financial profile context
  
Output Format:
  Conversational, actionable advice
  Include specific numbers (in INR)
  Provide step-by-step guidance
```

#### Portfolio Analyzer Prompt
```
Role: Investment portfolio expert
Specialties:
  - XIRR calculations
  - Expense ratio impact (in ₹)
  - Overlap detection
  - Benchmark comparison
  - Rebalancing strategies

Input: Portfolio statement or holdings list
Output:
  1) Portfolio reconstruction (asset breakdown)
  2) XIRR guidance & calculation
  3) Overlap analysis (duplicate funds)
  4) Expense ratio drag
  5) Benchmark comparison
  6) Rebalancing priority list
```

#### Tax Wizard Prompt
```
Role: Tax optimization specialist
Deductions Covered:
  - 80C (₹1.5L limit)
  - 80D (health insurance)
  - 80E (education loan)
  - 80G (donations)
  - Section 24 (mortgage)
  - HRA claims

Input: Form 16 or salary details
Output:
  1) Missed deductions
  2) Old vs New tax regime comparison
  3) Tax-saving investment suggestions
  4) Exact tax savings calculation
  5) Implementation timeline
```

#### Couple Planner Prompt
```
Role: Joint financial planning specialist
Optimization Areas:
  - HRA claim strategy
  - NPS contribution splits
  - SIP allocation for tax efficiency
  - Joint vs individual insurance
  - Goal prioritization

Input: Both partners' financial data
Output:
  1) Optimal HRA claim structure
  2) NPS split strategy
  3) Tax-efficient SIP allocation
  4) Insurance recommendations
  5) Combined net worth strategy
```

---

## Data Flow

### User Registration & Profiling

```
User Input
    ↓
React Form State
    ↓
POST /api/users/create
    ↓
Flask: create_user_profile()
    ↓
Generate user_id + store profile
    ↓
Initialize conversation history
    ↓
Response: {user_id, message}
    ↓
Frontend: Store user_id + navigate to dashboard
```

### Money Health Score Calculation

```
User clicks "Money Health Score"
    ↓
Frontend: Collect form data
    ↓
POST /api/users/<id>/money-health
    ↓
Flask: calculate_money_health_score()
    ↓
Calculate 6 dimension scores
    ↓
Apply weights (emergency 20%, insurance 20%, etc.)
    ↓
Calculate overall score
    ↓
Response: {overall_score, dimension_scores, health_level, top_priority}
    ↓
Frontend: Display score circle + dimension bars
```

### Multi-Turn Conversation with AI

```
User types message
    ↓
Frontend: setChatInput()
    ↓
User clicks Send
    ↓
POST /api/chat/<user_id> {message, agent_type}
    ↓
Flask: chat_with_agent()
    ↓
Fetch conversation history
    ↓
Select system prompt by agent_type
    ↓
Build messages array [history + new message]
    ↓
Call Claude API with system prompt + messages
    ↓
Extract response from Claude
    ↓
Append [user message, assistant response] to history
    ↓
Response: {success, response, agent_type}
    ↓
Frontend: Append to chatMessages + scroll to bottom
    ↓
Display AI response
```

---

## Database Schema (Production)

### Users Table
```sql
CREATE TABLE users (
  user_id VARCHAR(50) PRIMARY KEY,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Financial Profile
  age INT,
  annual_income DECIMAL(12,2),
  monthly_expenses DECIMAL(12,2),
  existing_investments DECIMAL(12,2),
  target_retirement_age INT,
  emergency_fund DECIMAL(12,2),
  health_insurance_cover DECIMAL(12,2),
  life_insurance_cover DECIMAL(12,2),
  total_investments DECIMAL(12,2),
  equity_investments DECIMAL(12,2),
  debt_investments DECIMAL(12,2),
  total_debt DECIMAL(12,2),
  tax_paid DECIMAL(12,2),
  taxable_income DECIMAL(12,2),
  retirement_savings DECIMAL(12,2),
  
  INDEX idx_created_at (created_at)
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
  conversation_id VARCHAR(100) PRIMARY KEY,
  user_id VARCHAR(50) FOREIGN KEY REFERENCES users(user_id),
  agent_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  
  INDEX idx_user_agent (user_id, agent_type)
);
```

### Messages Table
```sql
CREATE TABLE messages (
  message_id VARCHAR(100) PRIMARY KEY,
  conversation_id VARCHAR(100) FOREIGN KEY,
  role ENUM('user', 'assistant'),
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  
  INDEX idx_conversation (conversation_id)
);
```

### Recommendations Table
```sql
CREATE TABLE recommendations (
  recommendation_id VARCHAR(100) PRIMARY KEY,
  user_id VARCHAR(50) FOREIGN KEY REFERENCES users(user_id),
  type VARCHAR(50),
  data JSON,
  created_at TIMESTAMP DEFAULT NOW(),
  
  INDEX idx_user_type (user_id, type)
);
```

---

## Error Handling & Guardrails

### Input Validation
```python
- Age: 18-100
- Income: 0-10Cr
- Expenses: 0-income
- Investments: 0-10Cr
- Insurance: 0-1Cr
```

### Financial Constraints
```python
- FIRE feasible check: projected_corpus >= required_corpus
- Emergency fund warn: if < 3 months
- Debt warning: if debt_ratio > 2x income
- Insurance warning: if life < 5x income
```

### API Rate Limiting (Production)
```python
- 100 requests/minute per user
- 1000 requests/hour per IP
- Graceful degradation if Claude API fails
```

---

## Deployment Architecture

### Docker Containerization
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### Docker Compose (Local)
```yaml
services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  
  frontend:
    image: node:16
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    command: npm start
```

### Cloud Deployment
```
AWS EC2:
- Backend: t3.medium (2 vCPU, 4GB RAM)
- RDS: PostgreSQL db.t3.micro
- CloudFront: CDN for React frontend
- Lambda: Async recommendation generation

Scaling:
- Auto-scaling group for backend
- Read replicas for database
- Redis cache for conversation history
```

---

## Security Considerations

1. **API Authentication:**
   - User session tokens (JWT)
   - Rate limiting per user
   - HTTPS only

2. **Data Protection:**
   - Encrypt sensitive data (PII, financial)
   - Secure API keys in environment variables
   - No financial data in logs

3. **Compliance:**
   - GDPR-compliant data deletion
   - Audit trail of recommendations
   - Regulatory disclaimers

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| P99 Response Time | <2s | <1s |
| Uptime | 99.9% | N/A |
| Concurrent Users | 100K | 10 (dev) |
| API Calls/Second | 1000 | N/A |
| Claude API Cost/User | ₹0.5 | ₹0.3 |

---

**Architecture designed for scale, maintainability, and user experience.**
