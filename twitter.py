"""RunereumAgent Twitter integration and social capabilities."""

from typing import Optional, List
from datetime import timedelta
import asyncio
from urllib.parse import urlparse

class SocialMediaManager:
    """Manage social media operations for RunereumAgent."""

    def __init__(self, agent: RunereumAgent):
        self.agent = agent
        self.config = agent.config
        self.setup_social_patterns()
        self.last_post_time = None
        self.engagement_metrics = {
            "posts": 0,
            "replies": 0,
            "mentions": 0
        }

    def setup_social_patterns(self):
        """Configure social media behavior patterns."""
        self.posting_patterns = {
            SocialPattern.PASSIVE: {
                "post_interval": timedelta(hours=24),
                "reply_probability": 0.3,
                "max_daily_posts": 2
            },
            SocialPattern.ACTIVE: {
                "post_interval": timedelta(hours=6),
                "reply_probability": 0.7,
                "max_daily_posts": 8
            },
            SocialPattern.AGGRESSIVE: {
                "post_interval": timedelta(hours=2),
                "reply_probability": 0.9,
                "max_daily_posts": 24
            }
        }
        self.current_pattern = self.posting_patterns[
            self.agent.config.base_config.social_pattern
        ]

    async def initialize_twitter(self):
        """Initialize Twitter components and verify credentials."""
        try:
            # Get account details to verify connectivity
            response = await self.agent.process_message("get account details")
            if response["status"] == "success":
                self.twitter_handle = self._extract_handle(response["message"])
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Twitter: {str(e)}")

    def _extract_handle(self, account_details: str) -> str:
        """Extract Twitter handle from account details response."""
        try:
            data = json.loads(account_details)
            return data["data"]["username"]
        except Exception:
            return None

    async def monitor_mentions(self):
        """Monitor and respond to Twitter mentions."""
        while True:
            try:
                response = await self.agent.process_message("check account mentions")
                if response["status"] == "success":
                    await self._handle_mentions(response["message"])
                
                # Wait based on social pattern
                await asyncio.sleep(self.current_pattern["post_interval"].total_seconds())
            except Exception as e:
                print(f"Error monitoring mentions: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes after error

    async def _handle_mentions(self, mentions_data: str):
        """Process and respond to mentions."""
        try:
            data = json.loads(mentions_data)
            if "data" in data:
                for mention in data["data"]:
                    if random.random() < self.current_pattern["reply_probability"]:
                        await self._generate_and_post_reply(mention)
        except Exception as e:
            print(f"Error handling mentions: {str(e)}")

    async def _generate_and_post_reply(self, mention: dict):
        """Generate and post a contextual reply to a mention."""
        try:
            # Generate appropriate response based on agent's personality
            context = f"""Generate a reply to this tweet: '{mention['text']}'
            Maintain {self.agent.config.base_config.behavior} behavior.
            Focus on {', '.join(self.agent.config.base_config.capabilities)}."""
            
            response = await self.agent.process_message(context)
            
            if response["status"] == "success":
                # Post the reply
                reply_params = {
                    "tweet_id": mention["id"],
                    "tweet_reply": response["message"][:280]  # Twitter character limit
                }
                await self.agent.process_message(f"post tweet reply: {json.dumps(reply_params)}")
                self.engagement_metrics["replies"] += 1

        except Exception as e:
            print(f"Error generating reply: {str(e)}")

    async def create_content(self):
        """Generate and post content based on agent's capabilities and chain activities."""
        while True:
            try:
                if self.can_post():
                    content_type = self._determine_content_type()
                    content = await self._generate_content(content_type)
                    
                    if content:
                        response = await self.agent.process_message(f"post tweet: {content}")
                        if response["status"] == "success":
                            self.last_post_time = datetime.utcnow()
                            self.engagement_metrics["posts"] += 1
                
                await asyncio.sleep(self.current_pattern["post_interval"].total_seconds())
            except Exception as e:
                print(f"Error creating content: {str(e)}")
                await asyncio.sleep(300)

    def can_post(self) -> bool:
        """Check if agent can post based on pattern restrictions."""
        if not self.last_post_time:
            return True
            
        time_since_last = datetime.utcnow() - self.last_post_time
        daily_posts = self.engagement_metrics["posts"]
        
        return (time_since_last >= self.current_pattern["post_interval"] and
                daily_posts < self.current_pattern["max_daily_posts"])

    def _determine_content_type(self) -> str:
        """Determine type of content to post based on agent's capabilities."""
        content_weights = {
            AgentCapability.TRADING: 30,
            AgentCapability.PORTFOLIO_MANAGEMENT: 20,
            AgentCapability.COMMUNITY_MANAGEMENT: 25,
            AgentCapability.CONTENT_CREATION: 25
        }
        
        available_types = [cap for cap in content_weights.keys() 
                         if cap in self.agent.config.base_config.capabilities]
        
        weights = [content_weights[cap] for cap in available_types]
        return random.choices(available_types, weights=weights)[0]

    async def _generate_content(self, content_type: AgentCapability) -> Optional[str]:
        """Generate content based on type and agent's personality."""
        content_prompts = {
            AgentCapability.TRADING: """
                Create a market analysis tweet about recent trading activities on {chain}.
                Include relevant metrics and maintain {behavior} tone.
            """,
            AgentCapability.PORTFOLIO_MANAGEMENT: """
                Share a portfolio update focusing on current positions and strategy on {chain}.
                Maintain {behavior} approach to information sharing.
            """,
            AgentCapability.COMMUNITY_MANAGEMENT: """
                Generate an engaging community-focused tweet about the {chain} ecosystem.
                Reflect {behavior} community management style.
            """,
            AgentCapability.CONTENT_CREATION: """
                Create educational content about {chain} and recent developments.
                Match content to {behavior} communication style.
            """
        }
        
        prompt = content_prompts.get(content_type, "").format(
            chain=self.agent.config.base_config.chain,
            behavior=self.agent.config.base_config.behavior
        )
        
        response = await self.agent.process_message(prompt)
        if response["status"] == "success":
            return response["message"][:280]
        return None

# Add social media endpoints
@app.post("/agents/{agent_id}/social/initialize", response_model=AgentResponse)
async def initialize_social(
    agent_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Initialize agent's social media capabilities."""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    try:
        social_manager = SocialMediaManager(agent)
        if await social_manager.initialize_twitter():
            agent.social_manager = social_manager
            
            # Start social monitoring tasks
            background_tasks.add_task(social_manager.monitor_mentions)
            background_tasks.add_task(social_manager.create_content)
            
            return AgentResponse(
                agent_id=agent_id,
                status="success",
                message="Social media capabilities initialized",
                data={"twitter_handle": social_manager.twitter_handle}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize social media capabilities"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}/social/metrics", response_model=AgentResponse)
async def get_social_metrics(
    agent_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get agent's social media engagement metrics."""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    if hasattr(agent, 'social_manager'):
        return AgentResponse(
            agent_id=agent_id,
            status="success",
            message="Social media metrics retrieved",
            data={
                "metrics": agent.social_manager.engagement_metrics,
                "pattern": agent.config.base_config.social_pattern,
                "last_post": agent.social_manager.last_post_time
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Agent does not have social media capabilities initialized"
        )