"""RunereumAgent - Advanced blockchain & social media agent API.

A production-ready FastAPI service that creates and manages AI agents with:
- Configurable chain selection (Base, Ethereum, etc.)
- Customizable capabilities (trading, social, content)
- Behavioral patterns
- Social media integrations
- Cross-chain operations
- Brand identity management

Core Features:
- Custom agent personality and behavior
- Multi-chain support
- Social media management
- Content creation and distribution
- Real-time monitoring
- Brand presence management
"""

import os
import time
import uuid
from typing import Dict, List, Optional, Union, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil
from typing import BinaryIO

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl
import uvicorn

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from twitter_langchain import TwitterToolkit, TwitterApiWrapper

# Initialize FastAPI app
app = FastAPI(
    title="RunereumAgent API",
    description="Advanced multi-chain AI agent API",
    version="1.0.0"
)

# Setup static files for agent images
app.mount("/images", StaticFiles(directory="images"), name="images")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class Chain(BaseModel):
    """Supported blockchain networks."""
    id: str
    name: str
    chain_id: int
    testnet: bool = False
    
    class Config:
        schema_extra = {
            "example": {
                "id": "base-sepolia",
                "name": "Base Sepolia",
                "chain_id": 84532,
                "testnet": True
            }
        }

class AgentCapability(str, Enum):
    """Available agent capabilities."""
    TRADING = "trading"
    SOCIAL_MEDIA = "social_media"
    CONTENT_CREATION = "content_creation"
    COMMUNITY_MANAGEMENT = "community_management"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    DEX_OPERATIONS = "dex_operations"
    NFT_MANAGEMENT = "nft_management"
    TOKEN_DEPLOYMENT = "token_deployment"

class AgentBehavior(str, Enum):
    """Agent behavioral patterns."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXPERIMENTAL = "experimental"
    COMMUNITY_FOCUSED = "community_focused"
    ANALYTICAL = "analytical"

class SocialPresence(BaseModel):
    """Social media and web presence configuration."""
    twitter_link: Optional[HttpUrl] = None
    telegram_link: Optional[HttpUrl] = None
    youtube_link: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None

class AgentConfig(BaseModel):
    """Complete agent configuration matching frontend requirements."""
    name: str = Field(..., min_length=3, max_length=50)
    ticker: str = Field(..., min_length=1, max_length=10)
    chain: str
    capabilities: Set[AgentCapability]
    behavior: AgentBehavior
    social_presence: Optional[SocialPresence] = None
    
    class Config:
        schema_extra = {
            "example": {
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
        }

@dataclass
class RunereumConfig:
    """Extended configuration settings for RunereumAgent."""
    
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    base_config: AgentConfig
    model_name: str = "gpt-4o-mini"
    
    # Behavior parameters based on agent_behavior
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0)
    trade_frequency: int = Field(default=300)  # seconds
    social_frequency: int = Field(default=3600)  # seconds
    max_transaction_value: float = Field(default=1.0)  # in ETH
    
    system_prompt: str = ""  # Will be generated based on config
    
    def generate_system_prompt(self) -> str:
        """Generate customized system prompt based on configuration."""
        return f"""You are {self.base_config.name}, a specialized AI agent operating on {self.base_config.chain} with ticker {self.base_config.ticker}.
        
Your core capabilities include:
{self._format_capabilities()}

You operate with a {self.base_config.behavior.value} behavioral pattern, which means:
{self._get_behavior_description()}

Always maintain professional conduct and prioritize your defined objectives."""

    def _format_capabilities(self) -> str:
        return "\n".join([f"- {cap.value}" for cap in self.base_config.capabilities])

    def _get_behavior_description(self) -> str:
        behavior_descriptions = {
            AgentBehavior.CONSERVATIVE: "Prioritize safety and risk management, focus on stable growth",
            AgentBehavior.MODERATE: "Balance between growth and risk management",
            AgentBehavior.AGGRESSIVE: "Seek high growth opportunities, accept higher risk",
            AgentBehavior.EXPERIMENTAL: "Test new strategies and opportunities, pioneer new approaches",
            AgentBehavior.COMMUNITY_FOCUSED: "Prioritize community engagement and social presence",
            AgentBehavior.ANALYTICAL: "Focus on data-driven decisions and market analysis"
        }
        return behavior_descriptions.get(self.base_config.behavior, "Balanced approach to operations")

class AgentState(BaseModel):
    """Current state of a RunereumAgent."""
    agent_id: str
    config: AgentConfig
    is_active: bool
    last_action: Optional[str]
    last_action_time: Optional[datetime]
    wallet_balance: Optional[dict]
    pending_transactions: List[str]
    image_path: Optional[str]

# State management
active_agents: Dict[str, 'RunereumAgent'] = {}

"""RunereumAgent core implementation and API endpoints."""



class RunereumAgent:
    """Core agent implementation combining blockchain and social capabilities."""

    def __init__(self, config: RunereumConfig):
        """Initialize RunereumAgent with configuration."""
        self.config = config
        self.state = AgentState(
            agent_id=config.agent_id,
            config=config.base_config,
            is_active=False,
            last_action=None,
            last_action_time=None,
            wallet_balance=None,
            pending_transactions=[],
            image_path=None
        )
        self.setup_components()

    def setup_components(self):
        """Initialize core components based on capabilities."""
        # Initialize LLM
        self.llm = ChatOpenAI(model=self.config.model_name)
        self.memory = MemorySaver()
        
        # Setup blockchain components if needed
        if self._has_blockchain_capabilities():
            self.setup_blockchain()
        
        # Setup social components if needed
        if self._has_social_capabilities():
            self.setup_social()
        
        # Initialize agent with combined tools
        self.agent = self.create_agent()
        
        self.logger = self.setup_logging()

    def _has_blockchain_capabilities(self) -> bool:
        """Check if agent has blockchain-related capabilities."""
        blockchain_caps = {
            AgentCapability.TRADING,
            AgentCapability.PORTFOLIO_MANAGEMENT,
            AgentCapability.DEX_OPERATIONS,
            AgentCapability.NFT_MANAGEMENT,
            AgentCapability.TOKEN_DEPLOYMENT
        }
        return bool(blockchain_caps & self.config.base_config.capabilities)

    def _has_social_capabilities(self) -> bool:
        """Check if agent has social media capabilities."""
        social_caps = {
            AgentCapability.SOCIAL_MEDIA,
            AgentCapability.CONTENT_CREATION,
            AgentCapability.COMMUNITY_MANAGEMENT
        }
        return bool(social_caps & self.config.base_config.capabilities)

    def setup_blockchain(self):
        """Initialize blockchain components."""
        try:
            self.cdp_wrapper = CdpAgentkitWrapper(network_id=self.config.base_config.chain)
            self.cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(self.cdp_wrapper)
            self.blockchain_tools = self.cdp_toolkit.get_tools()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize blockchain components: {str(e)}")

    def setup_social(self):
        """Initialize social media components."""
        try:
            self.twitter_wrapper = TwitterApiWrapper()
            self.twitter_toolkit = TwitterToolkit.from_twitter_api_wrapper(self.twitter_wrapper)
            self.social_tools = self.twitter_toolkit.get_tools()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize social components: {str(e)}")

    def create_agent(self):
        """Create the agent with all enabled capabilities."""
        tools = []
        if hasattr(self, 'blockchain_tools'):
            tools.extend(self.blockchain_tools)
        if hasattr(self, 'social_tools'):
            tools.extend(self.social_tools)
        
        return create_react_agent(
            llm=self.llm,
            tools=tools,
            checkpointer=self.memory,
            state_modifier=self.config.generate_system_prompt()
        )

    async def process_message(self, message: str) -> dict:
        """Process a message and return structured response."""
        try:
            config = {"configurable": {"thread_id": f"runereum-{self.config.agent_id}"}}
            
            response = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )
            
            self.state.last_action = message
            self.state.last_action_time = datetime.utcnow()
            
            return {
                "status": "success",
                "message": response["agent"]["messages"][0].content,
                "timestamp": datetime.utcnow(),
                "agent_id": self.config.agent_id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow(),
                "agent_id": self.config.agent_id
            }

# API Routes

@app.post("/agents/create", response_model=AgentResponse)
async def create_agent(
    config: AgentConfig,
    image: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new RunereumAgent instance."""
    try:
        agent_id = str(uuid.uuid4())
        runereum_config = RunereumConfig(agent_id=agent_id, base_config=config)
        
        # Handle agent image if provided
        image_path = None
        if image:
            image_path = f"images/{agent_id}{Path(image.filename).suffix}"
            background_tasks.add_task(save_agent_image, image.file, image_path)
            
        # Create agent instance
        agent = RunereumAgent(runereum_config)
        agent.state.image_path = image_path
        active_agents[agent_id] = agent
        
        return AgentResponse(
            agent_id=agent_id,
            status="success",
            message="Agent created successfully",
            data={
                "config": config.dict(),
                "image_path": image_path
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get agent details by ID."""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = active_agents[agent_id]
    return AgentResponse(
        agent_id=agent_id,
        status="success",
        message="Agent details retrieved",
        data={
            "state": agent.state.dict(),
            "config": agent.config.base_config.dict()
        }
    )

@app.post("/agents/{agent_id}/message", response_model=AgentResponse)
async def send_message(
    agent_id: str,
    message: str,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Send a message to a specific agent."""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    agent = active_agents[agent_id]
    response = await agent.process_message(message)
    
    return AgentResponse(
        agent_id=agent_id,
        status=response["status"],
        message=response["message"],
        data={"timestamp": response["timestamp"]}
    )

async def save_agent_image(file: BinaryIO, path: str):
    """Save uploaded agent image."""
    try:
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
    except Exception as e:
        print(f"Error saving agent image: {str(e)}")
        
