# RunereumAgent

A powerful AI agent platform combining blockchain operations, social media management, and autonomous trading capabilities. Built with FastAPI, CDP Agentkit, and LangChain.

## 🌟 Features

### Core Capabilities
- **Multi-Chain Support**: Operates on Base, Base Sepolia, and other EVM-compatible chains
- **Social Media Integration**: Automated Twitter engagement and content creation
- **Trading Strategies**: DCA and Portfolio Rebalancing
- **Real-time Monitoring**: WebSocket-based updates for all agent activities

### Agent Behaviors
- Conservative
- Moderate
- Aggressive
- Experimental
- Community Focused
- Analytical

### Supported Capabilities
- Trading
- Social Media Management
- Content Creation
- Community Management
- Portfolio Management
- DEX Operations
- NFT Management
- Token Deployment

## 🚀 Quick Start

### Prerequisites
```bash
pip install fastapi uvicorn cdp-sdk cdp-agentkit-core cdp-langchain twitter-langchain langchain langchain-openai
```

### Environment Variables
```env
CDP_API_KEY_NAME=your_cdp_key_name
CDP_API_KEY_PRIVATE_KEY=your_cdp_private_key
NETWORK_ID=base-sepolia
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

### Running the Server
```bash
uvicorn main:app --reload
```

## 📚 API Documentation

### Agent Management

#### Create Agent
```http
POST /agents/create
```
```json
{
  "name": "Runekeeper",
  "ticker": "RUNE",
  "chain": "base-sepolia",
  "capabilities": ["trading", "social_media"],
  "behavior": "moderate",
  "social_presence": {
    "twitter_link": "https://twitter.com/runekeeper",
    "website": "https://runekeeper.io"
  }
}
```

#### Get Agent Details
```http
GET /agents/{agent_id}
```

#### Send Message to Agent
```http
POST /agents/{agent_id}/message
```

### Trading Operations

#### Set Trading Strategy
```http
POST /agents/{agent_id}/strategy
```
```json
{
  "strategy_type": "dca",
  "parameters": {
    "max_position_size": "1.0",
    "stop_loss": "0.05",
    "take_profit": "0.1",
    "slippage_tolerance": "0.01",
    "rebalance_threshold": "0.05",
    "dca_interval": 86400,
    "risk_factor": "0.5"
  }
}
```

### Social Media Operations

#### Initialize Social Media
```http
POST /agents/{agent_id}/social/initialize
```

#### Get Social Metrics
```http
GET /agents/{agent_id}/social/metrics
```

## 🔌 WebSocket Integration

Connect to real-time agent updates:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${agent_id}`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

## 🏗 Architecture

### Components

#### RunereumAgent
Core agent implementation managing:
- Blockchain operations
- Social media interactions
- Trading strategies
- Real-time monitoring

#### Trading Strategies
- **DCA Strategy**: Automated dollar-cost averaging
- **Rebalance Strategy**: Portfolio rebalancing based on target allocations

#### Social Media Manager
Handles:
- Twitter engagement
- Content creation
- Mention monitoring
- Engagement metrics

#### Chain Operations
Manages:
- Transaction execution
- Gas optimization
- Chain-specific parameters
- Transaction monitoring

## 💡 Usage Examples

### Creating an Agent with Social Capabilities
```python
import requests

agent_config = {
    "name": "Runekeeper",
    "ticker": "RUNE",
    "chain": "base-sepolia",
    "capabilities": ["trading", "social_media"],
    "behavior": "moderate",
    "social_presence": {
        "twitter_link": "https://twitter.com/runekeeper"
    }
}

response = requests.post(
    "http://localhost:8000/agents/create",
    json=agent_config
)
agent_id = response.json()["agent_id"]
```

### Setting Up Trading Strategy
```python
strategy_config = {
    "strategy_type": "dca",
    "parameters": {
        "max_position_size": "1.0",
        "dca_interval": 86400
    }
}

requests.post(
    f"http://localhost:8000/agents/{agent_id}/strategy",
    json=strategy_config
)
```

## 🔒 Security

- JWT-based authentication
- Rate limiting
- Input validation
- Transaction signing validation

## 📊 Monitoring

Agent activities are monitored through:
- WebSocket real-time updates
- Social media metrics
- Trading performance
- Blockchain transaction status

## 🚧 Current Limitations

- Single chain operation per agent
- Rate limits on social media operations
- Fixed trading strategy parameters
- Basic error recovery mechanisms

## 🛣 Roadmap

- [ ] Multi-chain operations per agent
- [ ] Advanced trading strategies
- [ ] Social media content scheduling
- [ ] Enhanced analytics
- [ ] State persistence
- [ ] Performance monitoring
```

Would you like me to:
1. Add more implementation details to the README
2. Include deployment instructions
3. Add configuration details
4. Include development setup guides
5. Add troubleshooting section

