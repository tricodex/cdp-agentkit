"""RunereumAgent WebSocket and real-time operations implementation."""

from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.agent_subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        """Connect client to agent's WebSocket."""
        await websocket.accept()
        
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        self.active_connections[agent_id].add(websocket)
        
        if websocket not in self.agent_subscriptions:
            self.agent_subscriptions[websocket] = set()
        self.agent_subscriptions[websocket].add(agent_id)

    async def disconnect(self, websocket: WebSocket):
        """Disconnect client and cleanup subscriptions."""
        if websocket in self.agent_subscriptions:
            for agent_id in self.agent_subscriptions[websocket]:
                if agent_id in self.active_connections:
                    self.active_connections[agent_id].remove(websocket)
                    if not self.active_connections[agent_id]:
                        del self.active_connections[agent_id]
            del self.agent_subscriptions[websocket]

    async def broadcast_to_agent(self, agent_id: str, message: dict):
        """Broadcast message to all clients subscribed to an agent."""
        if agent_id in self.active_connections:
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    await self.disconnect(connection)

manager = ConnectionManager()

class AgentStreamManager:
    """Manage real-time agent operations and updates."""
    
    def __init__(self, agent: RunereumAgent):
        self.agent = agent
        self.active_tasks: Set[asyncio.Task] = set()
        self.should_run = True

    async def start_monitoring(self):
        """Start all monitoring tasks based on agent capabilities."""
        if self._has_blockchain_capabilities():
            self.active_tasks.add(asyncio.create_task(self.monitor_blockchain()))
        
        if self._has_social_capabilities():
            self.active_tasks.add(asyncio.create_task(self.monitor_social()))
        
        if AgentCapability.TRADING in self.agent.config.base_config.capabilities:
            self.active_tasks.add(asyncio.create_task(self.monitor_trading()))

    async def stop_monitoring(self):
        """Stop all monitoring tasks."""
        self.should_run = False
        for task in self.active_tasks:
            task.cancel()
        self.active_tasks.clear()

    async def monitor_blockchain(self):
        """Monitor blockchain activities and balances."""
        while self.should_run:
            try:
                # Get wallet details
                wallet_response = await self.agent.process_message("get wallet details")
                if wallet_response["status"] == "success":
                    await manager.broadcast_to_agent(
                        self.agent.config.agent_id,
                        {
                            "type": "wallet_update",
                            "data": wallet_response["message"]
                        }
                    )

                # Get balances
                balance_response = await self.agent.process_message("get balance eth")
                if balance_response["status"] == "success":
                    await manager.broadcast_to_agent(
                        self.agent.config.agent_id,
                        {
                            "type": "balance_update",
                            "data": balance_response["message"]
                        }
                    )
                
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                await manager.broadcast_to_agent(
                    self.agent.config.agent_id,
                    {
                        "type": "error",
                        "data": f"Blockchain monitoring error: {str(e)}"
                    }
                )
                await asyncio.sleep(60)  # Wait longer after error

    async def monitor_social(self):
        """Monitor social media activities."""
        while self.should_run:
            try:
                if hasattr(self.agent, 'twitter_toolkit'):
                    # Check mentions
                    mentions_response = await self.agent.process_message("check account mentions")
                    if mentions_response["status"] == "success":
                        await manager.broadcast_to_agent(
                            self.agent.config.agent_id,
                            {
                                "type": "social_update",
                                "data": mentions_response["message"]
                            }
                        )
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                await manager.broadcast_to_agent(
                    self.agent.config.agent_id,
                    {
                        "type": "error",
                        "data": f"Social monitoring error: {str(e)}"
                    }
                )
                await asyncio.sleep(600)  # Wait longer after error

    async def monitor_trading(self):
        """Monitor and execute trading strategies."""
        while self.should_run:
            try:
                if self.agent.config.base_config.behavior == AgentBehavior.AGGRESSIVE:
                    check_interval = 60  # Check every minute
                else:
                    check_interval = 300  # Check every 5 minutes

                # Analyze trading opportunities
                analysis_response = await self.agent.process_message(
                    "analyze current market conditions and suggest trades"
                )
                
                if analysis_response["status"] == "success":
                    await manager.broadcast_to_agent(
                        self.agent.config.agent_id,
                        {
                            "type": "trading_update",
                            "data": analysis_response["message"]
                        }
                    )

                    # Execute trades if appropriate
                    if "suggested_trade" in analysis_response:
                        trade_response = await self.agent.process_message(
                            f"execute trade: {analysis_response['suggested_trade']}"
                        )
                        await manager.broadcast_to_agent(
                            self.agent.config.agent_id,
                            {
                                "type": "trade_execution",
                                "data": trade_response["message"]
                            }
                        )

                await asyncio.sleep(check_interval)
            except Exception as e:
                await manager.broadcast_to_agent(
                    self.agent.config.agent_id,
                    {
                        "type": "error",
                        "data": f"Trading monitoring error: {str(e)}"
                    }
                )
                await asyncio.sleep(600)  # Wait longer after error

# WebSocket Routes

@app.websocket("/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent updates."""
    if agent_id not in active_agents:
        await websocket.close(code=4004, reason="Agent not found")
        return

    await manager.connect(websocket, agent_id)
    agent = active_agents[agent_id]
    stream_manager = AgentStreamManager(agent)
    
    try:
        await stream_manager.start_monitoring()
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data["type"] == "command":
                    response = await agent.process_message(data["message"])
                    await websocket.send_json({
                        "type": "command_response",
                        "data": response
                    })
                    
            except WebSocketDisconnect:
                await manager.disconnect(websocket)
                await stream_manager.stop_monitoring()
                break
                
    except Exception as e:
        await manager.broadcast_to_agent(
            agent_id,
            {
                "type": "error",
                "data": f"WebSocket error: {str(e)}"
            }
        )
        await manager.disconnect(websocket)
        await stream_manager.stop_monitoring()