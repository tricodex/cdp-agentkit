"""RunereumAgent trading strategies and chain operations."""

from decimal import Decimal
from typing import Optional, Tuple
import asyncio
from enum import auto
from dataclasses import dataclass

class MarketPosition(str, Enum):
    """Market position indicators."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"

@dataclass
class TradingParameters:
    """Trading strategy parameters."""
    max_position_size: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    slippage_tolerance: Decimal
    rebalance_threshold: Decimal
    dca_interval: int  # in seconds
    risk_factor: Decimal

class TradingStrategy:
    """Base class for trading strategies."""
    
    def __init__(self, agent: RunereumAgent, params: TradingParameters):
        self.agent = agent
        self.params = params
        self.position = MarketPosition.NEUTRAL
        self.last_trade_time = None
        self.current_position_size = Decimal('0')

    async def analyze(self) -> Tuple[MarketPosition, Optional[dict]]:
        """Analyze market conditions and return position recommendation."""
        raise NotImplementedError()

    async def execute_trade(self, trade_params: dict) -> bool:
        """Execute a trade based on parameters."""
        raise NotImplementedError()

    async def get_market_data(self) -> dict:
        """Get relevant market data for analysis."""
        try:
            # Get basic market data from CDP toolkit
            balance_response = await self.agent.process_message("get balance eth")
            
            # Additional market data based on chain
            if self.agent.config.base_config.chain == "base-mainnet":
                price_data = await self._get_base_market_data()
            else:
                price_data = await self._get_chain_market_data()
            
            return {
                "balance": balance_response,
                "market_data": price_data
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get market data: {str(e)}")

class DCAStrategy(TradingStrategy):
    """Dollar Cost Averaging strategy implementation."""

    async def analyze(self) -> Tuple[MarketPosition, Optional[dict]]:
        if not self.last_trade_time or \
           (datetime.utcnow() - self.last_trade_time).seconds >= self.params.dca_interval:
            market_data = await self.get_market_data()
            
            # Calculate DCA amount based on available balance
            balance = Decimal(market_data["balance"]["eth"])
            dca_amount = min(
                balance * Decimal('0.1'),  # 10% of available balance
                self.params.max_position_size
            )
            
            if dca_amount > 0:
                return MarketPosition.LONG, {
                    "action": "buy",
                    "amount": str(dca_amount),
                    "asset": "eth"
                }
        
        return MarketPosition.NEUTRAL, None

class RebalanceStrategy(TradingStrategy):
    """Portfolio rebalancing strategy."""

    async def analyze(self) -> Tuple[MarketPosition, Optional[dict]]:
        market_data = await self.get_market_data()
        current_allocation = self._calculate_allocation(market_data)
        
        if self._needs_rebalance(current_allocation):
            return self._get_rebalance_action(current_allocation)
        
        return MarketPosition.NEUTRAL, None

    def _calculate_allocation(self, market_data: dict) -> dict:
        """Calculate current portfolio allocation."""
        total_value = Decimal('0')
        allocations = {}
        
        for asset, balance in market_data["balance"].items():
            value = Decimal(balance) * Decimal(market_data["market_data"][asset]["price"])
            total_value += value
            allocations[asset] = value
        
        # Convert to percentages
        return {
            asset: (value / total_value) if total_value else Decimal('0')
            for asset, value in allocations.items()
        }

    def _needs_rebalance(self, current_allocation: dict) -> bool:
        """Check if portfolio needs rebalancing."""
        target_allocation = {
            "eth": Decimal('0.6'),
            "usdc": Decimal('0.4')
        }
        
        return any(
            abs(current_allocation.get(asset, Decimal('0')) - target)
            > self.params.rebalance_threshold
            for asset, target in target_allocation.items()
        )

class ChainOperations:
    """Chain-specific operations handler."""

    def __init__(self, agent: RunereumAgent):
        self.agent = agent
        self.chain = agent.config.base_config.chain
        self.setup_chain_specifics()

    def setup_chain_specifics(self):
        """Setup chain-specific parameters and configurations."""
        self.chain_config = {
            "base-mainnet": {
                "gas_limit": 500000,
                "priority_fee": 2,  # gwei
                "block_time": 2,  # seconds
                "confirmations": 3
            },
            "base-sepolia": {
                "gas_limit": 800000,
                "priority_fee": 1,
                "block_time": 2,
                "confirmations": 1
            }
        }.get(self.chain, {})

    async def execute_transaction(self, tx_params: dict) -> dict:
        """Execute a transaction with chain-specific optimizations."""
        try:
            # Prepare transaction parameters
            prepared_tx = self._prepare_transaction(tx_params)
            
            # Execute via CDP toolkit
            response = await self.agent.process_message(
                f"execute transaction: {json.dumps(prepared_tx)}"
            )
            
            # Monitor transaction
            if response["status"] == "success":
                tx_hash = self._extract_tx_hash(response)
                return await self._monitor_transaction(tx_hash)
            
            return response
        except Exception as e:
            return {
                "status": "error",
                "message": f"Transaction failed: {str(e)}"
            }

    def _prepare_transaction(self, tx_params: dict) -> dict:
        """Prepare transaction with chain-specific parameters."""
        return {
            **tx_params,
            "gas_limit": self.chain_config["gas_limit"],
            "priority_fee": self.chain_config["priority_fee"],
            "chain": self.chain
        }

    async def _monitor_transaction(self, tx_hash: str) -> dict:
        """Monitor transaction with chain-specific confirmation requirements."""
        required_confirmations = self.chain_config["confirmations"]
        block_time = self.chain_config["block_time"]
        
        confirmations = 0
        while confirmations < required_confirmations:
            await asyncio.sleep(block_time)
            
            # Check transaction status
            status_response = await self.agent.process_message(
                f"check transaction status: {tx_hash}"
            )
            
            if status_response["status"] == "success":
                confirmations = self._get_confirmations(status_response)
            else:
                return status_response
        
        return {
            "status": "success",
            "message": "Transaction confirmed",
            "tx_hash": tx_hash,
            "confirmations": confirmations
        }

# Add trading strategy endpoints
@app.post("/agents/{agent_id}/strategy", response_model=AgentResponse)
async def set_trading_strategy(
    agent_id: str,
    strategy_type: TradingStrategy,
    parameters: TradingParameters,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Set or update agent's trading strategy."""
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    
    try:
        if strategy_type == "dca":
            strategy = DCAStrategy(agent, parameters)
        elif strategy_type == "rebalance":
            strategy = RebalanceStrategy(agent, parameters)
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy type")
        
        agent.trading_strategy = strategy
        
        return AgentResponse(
            agent_id=agent_id,
            status="success",
            message=f"Trading strategy updated to {strategy_type}",
            data={"parameters": parameters.dict()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))