import React, { useState, useRef, useEffect } from 'react';
import './styles.css';

const AIMentor = () => {
  const [currentPage, setCurrentPage] = useState('landing');
  const [userId, setUserId] = useState(null);
  const [formData, setFormData] = useState({
    age: '',
    annual_income: '',
    monthly_expenses: '',
    existing_investments: '',
    target_retirement_age: '60',
    emergency_fund: '',
    health_insurance_cover: '',
    life_insurance_cover: '',
    total_investments: '',
    equity_investments: '',
    debt_investments: '',
    total_debt: '',
    tax_paid: '',
    taxable_income: '',
    retirement_savings: ''
  });
  
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [agentType, setAgentType] = useState('financial_advisor');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const createUserProfile = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/users/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (data.success) {
        setUserId(data.user_id);
        setChatMessages([{
          role: 'assistant',
          content: '👋 Welcome to AI Money Mentor! I\'ve analyzed your financial profile. What would you like help with today? I can assist with:\n\n1. FIRE Path Planning\n2. Money Health Score\n3. Tax Optimization\n4. Portfolio Analysis\n5. Life Event Financial Decisions'
        }]);
        setCurrentPage('dashboard');
      }
    } catch (error) {
      alert('Error creating profile: ' + error.message);
    }
    setLoading(false);
  };

  const calculateMoneyHealth = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/users/${userId}/money-health`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (data.success) {
        setResults(data.money_health_score);
        setCurrentPage('results');
      }
    } catch (error) {
      alert('Error calculating score: ' + error.message);
    }
    setLoading(false);
  };

  const calculateFIREPlan = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/users/${userId}/fire-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (data.success) {
        setResults(data.fire_roadmap);
        setCurrentPage('results');
      }
    } catch (error) {
      alert('Error calculating FIRE plan: ' + error.message);
    }
    setLoading(false);
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;

    setLoading(true);
    const newMessage = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, newMessage]);
    setChatInput('');

    try {
      const response = await fetch(`/api/chat/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatInput,
          agent_type: agentType
        })
      });

      const data = await response.json();
      if (data.success) {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response
        }]);
      }
    } catch (error) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Could not get response. ' + error.message
      }]);
    }
    setLoading(false);
  };

  const renderLanding = () => (
    <div className="landing-page">
      <div className="landing-header">
        <h1>🤖 AI Money Mentor</h1>
        <p>Your AI-Powered Personal Finance Guide</p>
        <p className="tagline">95% of Indians don't have a financial plan. We change that.</p>
      </div>

      <div className="features-grid">
        <div className="feature-card">
          <h3>🎯 FIRE Path Planner</h3>
          <p>Complete month-by-month roadmap to Financial Independence</p>
        </div>
        <div className="feature-card">
          <h3>💚 Money Health Score</h3>
          <p>5-minute assessment across 6 financial dimensions</p>
        </div>
        <div className="feature-card">
          <h3>💰 Tax Wizard</h3>
          <p>Identify deductions & compare tax regimes with your numbers</p>
        </div>
        <div className="feature-card">
          <h3>💼 Portfolio X-Ray</h3>
          <p>Deep analysis: XIRR, overlaps, expense drag, rebalancing plan</p>
        </div>
      </div>

      <div className="form-section">
        <h2>Let's Start Your Financial Journey</h2>
        <div className="form-grid">
          <input type="number" name="age" placeholder="Your Age" value={formData.age} onChange={handleInputChange} />
          <input type="number" name="annual_income" placeholder="Annual Income (₹)" value={formData.annual_income} onChange={handleInputChange} />
          <input type="number" name="monthly_expenses" placeholder="Monthly Expenses (₹)" value={formData.monthly_expenses} onChange={handleInputChange} />
          <input type="number" name="existing_investments" placeholder="Existing Investments (₹)" value={formData.existing_investments} onChange={handleInputChange} />
          <input type="number" name="emergency_fund" placeholder="Emergency Fund (₹)" value={formData.emergency_fund} onChange={handleInputChange} />
          <input type="number" name="health_insurance_cover" placeholder="Health Insurance Cover (₹)" value={formData.health_insurance_cover} onChange={handleInputChange} />
          <input type="number" name="life_insurance_cover" placeholder="Life Insurance Cover (₹)" value={formData.life_insurance_cover} onChange={handleInputChange} />
          <input type="number" name="total_debt" placeholder="Total Debt (₹)" value={formData.total_debt} onChange={handleInputChange} />
        </div>
        <button onClick={createUserProfile} disabled={loading} className="cta-button">
          {loading ? 'Creating Profile...' : 'Start Now →'}
        </button>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>Welcome to Your Financial Command Center</h1>
        <div className="quick-actions">
          <button onClick={calculateMoneyHealth} className="action-btn">
            <span className="emoji">💚</span> Money Health Score
          </button>
          <button onClick={calculateFIREPlan} className="action-btn">
            <span className="emoji">🎯</span> FIRE Roadmap
          </button>
        </div>
      </div>

      <div className="chat-interface">
        <div className="chat-header">
          <h2>💬 AI Financial Advisor</h2>
          <select value={agentType} onChange={(e) => setAgentType(e.target.value)} className="agent-selector">
            <option value="financial_advisor">Financial Advisor</option>
            <option value="portfolio_analyzer">Portfolio Analyzer</option>
            <option value="tax_wizard">Tax Wizard</option>
            <option value="couple_planner">Couple Planner</option>
          </select>
        </div>

        <div className="chat-messages">
          {chatMessages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && <div className="message assistant"><div className="typing">Thinking...</div></div>}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-input-area">
          <input
            type="text"
            placeholder="Ask me anything about your finances..."
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
            className="chat-input"
          />
          <button onClick={sendChatMessage} disabled={loading} className="send-btn">
            Send
          </button>
        </div>
      </div>
    </div>
  );

  const renderResults = () => (
    <div className="results-page">
      <button onClick={() => setCurrentPage('dashboard')} className="back-btn">← Back</button>
      
      {results?.overall_score !== undefined ? (
        // Money Health Score
        <div className="results-container">
          <h1>💚 Your Money Health Score</h1>
          
          <div className="score-circle">
            <div className="score-value">{results.overall_score}</div>
            <div className="score-label">/ 100</div>
            <div className="score-level">{results.health_level}</div>
          </div>

          <div className="dimensions-grid">
            <div className="dimension">
              <label>Emergency Preparedness</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.emergency + '%'}}></div>
              </div>
              <span>{results.dimension_scores.emergency}</span>
            </div>
            <div className="dimension">
              <label>Insurance Coverage</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.insurance + '%'}}></div>
              </div>
              <span>{results.dimension_scores.insurance}</span>
            </div>
            <div className="dimension">
              <label>Diversification</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.diversification + '%'}}></div>
              </div>
              <span>{results.dimension_scores.diversification}</span>
            </div>
            <div className="dimension">
              <label>Debt Health</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.debt + '%'}}></div>
              </div>
              <span>{results.dimension_scores.debt}</span>
            </div>
            <div className="dimension">
              <label>Tax Efficiency</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.tax_efficiency + '%'}}></div>
              </div>
              <span>{results.dimension_scores.tax_efficiency}</span>
            </div>
            <div className="dimension">
              <label>Retirement Readiness</label>
              <div className="score-bar">
                <div className="score-fill" style={{width: results.dimension_scores.retirement + '%'}}></div>
              </div>
              <span>{results.dimension_scores.retirement}</span>
            </div>
          </div>

          <div className="recommendation-box">
            <h3>🎯 Top Priority</h3>
            <p>Focus on improving your <strong>{results.top_priority.replace('_', ' ').toUpperCase()}</strong> for maximum impact</p>
          </div>
        </div>
      ) : (
        // FIRE Roadmap
        <div className="results-container">
          <h1>🎯 Your FIRE Roadmap</h1>
          
          <div className="fire-summary">
            <div className="fire-stat">
              <label>Current Age</label>
              <span className="value">{results?.current_age}</span>
            </div>
            <div className="fire-stat">
              <label>Target Retirement</label>
              <span className="value">{results?.target_retirement_age}</span>
            </div>
            <div className="fire-stat">
              <label>Years Left</label>
              <span className="value">{results?.years_to_retirement}</span>
            </div>
            <div className="fire-stat">
              <label>Monthly Savings</label>
              <span className="value">₹{(results?.monthly_savings_needed || 0).toLocaleString('en-IN')}</span>
            </div>
          </div>

          <div className="feasibility-check">
            <h3>{results?.fire_feasible ? '✅' : '⚠️'} FIRE Feasibility</h3>
            <p>Required Corpus (25x expenses): <strong>₹{(results?.required_corpus_25x || 0).toLocaleString('en-IN')}</strong></p>
            <p>Projected Corpus: <strong>₹{(results?.projected_corpus || 0).toLocaleString('en-IN')}</strong></p>
            <p>{results?.fire_feasible ? 
              '✅ Your FIRE goal is achievable!' : 
              '⚠️ You may need to adjust savings or retirement age'}</p>
          </div>

          <div className="sip-recommendations">
            <h3>💰 Recommended Monthly SIP Allocation</h3>
            <div className="sip-grid">
              <div className="sip-card">
                <span>Equity</span>
                <span className="amount">₹{(results?.monthly_sip_recommendations?.equity || 0).toLocaleString('en-IN')}</span>
                <span className="percent">70%</span>
              </div>
              <div className="sip-card">
                <span>Debt</span>
                <span className="amount">₹{(results?.monthly_sip_recommendations?.debt || 0).toLocaleString('en-IN')}</span>
                <span className="percent">20%</span>
              </div>
              <div className="sip-card">
                <span>Gold</span>
                <span className="amount">₹{(results?.monthly_sip_recommendations?.gold || 0).toLocaleString('en-IN')}</span>
                <span className="percent">10%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="app-container">
      {currentPage === 'landing' && renderLanding()}
      {currentPage === 'dashboard' && renderDashboard()}
      {currentPage === 'results' && renderResults()}
    </div>
  );
};

export default AIMentor;
